// Independent range oracle using the TypeScript compiler's parser, not
// gramide's tree. One JSON object per input path, one per line:
//   {"path", "accepted", "symbols": [{"kind", "name", "owner", "start", "end", "start_byte", "end_byte"}]}
// `accepted` is whether the parser reported no syntax error. The symbols are
// what gramide's `symbols` should say about the file, in the same words:
// functions and function bindings, classes, interfaces, type aliases, enums
// and namespaces, methods and method signatures named with the nearest
// enclosing class, interface, type alias or binding, fields and property
// signatures, and the bindings declared at the top of a file or a namespace.
// A declaration inside a namespace is named with it (`ts.Parser.parse`).
import ts from "typescript";
import fs from "node:fs";

function byteTable(text) {
  const table = new Uint32Array(text.length + 1);
  let bytes = 0;
  for (let i = 0; i < text.length; i++) {
    table[i] = bytes;
    const c = text.charCodeAt(i);
    if (c < 0x80) bytes += 1;
    else if (c < 0x800) bytes += 2;
    else if (c >= 0xd800 && c <= 0xdbff) { bytes += 4; i++; table[i] = bytes; }
    else bytes += 3;
  }
  table[text.length] = bytes;
  return table;
}

function scriptKind(path) {
  if (path.endsWith(".tsx")) return ts.ScriptKind.TSX;
  if (path.endsWith(".ts") || path.endsWith(".mts") || path.endsWith(".cts")) return ts.ScriptKind.TS;
  return ts.ScriptKind.JS;
}

// gramide joins a computed name from its tokens, without the whitespace
function joinedTokens(text) {
  const scanner = ts.createScanner(ts.ScriptTarget.Latest, true, ts.LanguageVariant.Standard, text);
  let out = "";
  while (scanner.scan() !== ts.SyntaxKind.EndOfFileToken) out += scanner.getTokenText();
  return out;
}

function nameText(node) {
  if (!node) return "";
  if (ts.isIdentifier(node) || ts.isPrivateIdentifier(node)) return node.text;
  if (ts.isStringLiteral(node) || ts.isNumericLiteral(node)) return node.getText();
  if (ts.isComputedPropertyName(node)) return joinedTokens(node.getText());
  return "";
}

const isMethodLike = (n) => ts.isMethodDeclaration(n) || ts.isAccessor(n) || ts.isConstructorDeclaration(n) || ts.isMethodSignature(n);

// A method is owned by the nearest class, interface, type alias, binding or
// word-named property above it; a method's body holds no methods, while a
// plain function or arrow between the two is transparent.
function ownerAbove(node) {
  for (let p = node.parent; p; p = p.parent) {
    if ((ts.isClassDeclaration(p) || ts.isInterfaceDeclaration(p) || ts.isTypeAliasDeclaration(p)) && p.name) return p.name.text;
    if (ts.isVariableDeclaration(p) && ts.isIdentifier(p.name)) return p.name.text;
    if (ts.isPropertyAssignment(p) && ts.isIdentifier(p.name)) return p.name.text;
    if (isMethodLike(p)) return "";
    if (ts.isModuleDeclaration(p)) return "";
  }
  return "";
}

// `namespace A.B {}` is one declaration named A.B; its body is the innermost's
function moduleChain(node) {
  const names = [];
  let m = node;
  while (ts.isModuleDeclaration(m)) {
    names.push(ts.isStringLiteral(m.name) ? m.name.getText() : m.name.text);
    if (m.body && ts.isModuleDeclaration(m.body)) m = m.body; else break;
  }
  return { name: names.join("."), body: m.body };
}

function symbolsOf(sf, text) {
  const table = byteTable(text);
  const out = [];
  const lineOf = (pos) => sf.getLineAndCharacterOfPosition(pos).line + 1;
  // where a declaration's last token ends: a trailing comment is the next
  // token's leading trivia to the compiler and no token at all to gramide,
  // and a closing `;` or `,` belongs to the statement or the list
  function tokenEnd(node) {
    const kids = node.getChildren(sf);
    if (kids.length === 0) return node.getEnd();
    for (let i = kids.length - 1; i >= 0; i--) {
      const k = kids[i];
      if (k.kind === ts.SyntaxKind.SemicolonToken || k.kind === ts.SyntaxKind.CommaToken) continue;
      return tokenEnd(k);
    }
    return node.getEnd();
  }
  const push = (kind, name, owner, startPos, endPos) => {
    let end = endPos;
    while (end > startPos && /[\s;,]/.test(text[end - 1])) end--;
    out.push({ kind, name, owner, start: lineOf(startPos), end: lineOf(end - 1), start_byte: table[startPos], end_byte: table[end] });
  };
  const isFunctionInit = (init) => init && (ts.isArrowFunction(init) || ts.isFunctionExpression(init));
  // `top`: at the top of a file or a namespace body, where bindings are listed
  // `ns`: the namespace prefix every name inside carries
  function visit(node, top, ns) {
    const q = (name) => (ns ? ns + "." + name : name);
    let nextTop = false;
    let nextNs = ns;
    if (ts.isFunctionDeclaration(node) && node.name) push("function", q(node.name.text), "", node.getStart(sf), tokenEnd(node));
    else if (ts.isClassDeclaration(node) && node.name) push("class", q(node.name.text), "", node.getStart(sf), tokenEnd(node));
    else if (ts.isInterfaceDeclaration(node)) push("interface", q(node.name.text), "", node.getStart(sf), tokenEnd(node));
    else if (ts.isTypeAliasDeclaration(node)) push("type", q(node.name.text), "", node.getStart(sf), tokenEnd(node));
    else if (ts.isEnumDeclaration(node)) push("enum", q(node.name.text), "", node.getStart(sf), tokenEnd(node));
    else if (ts.isModuleDeclaration(node)) {
      const chain = moduleChain(node);
      push("namespace", q(chain.name), "", node.getStart(sf), tokenEnd(node));
      if (chain.body) visit(chain.body, true, ts.isStringLiteral(node.name) || node.flags & ts.NodeFlags.GlobalAugmentation ? ns : q(chain.name));
      return;
    }
    else if (isMethodLike(node)) {
      const own = ownerAbove(node);
      const name = ts.isConstructorDeclaration(node) ? "constructor" : nameText(node.name);
      const inObjectOrClass = ts.isClassLike(node.parent) || ts.isObjectLiteralExpression(node.parent) || ts.isInterfaceDeclaration(node.parent) || ts.isTypeLiteralNode(node.parent);
      if (name && inObjectOrClass) push("method", q(own ? own + "." + name : name), own, node.getStart(sf), tokenEnd(node));
    }
    else if ((ts.isPropertyDeclaration(node) || ts.isPropertySignature(node)) && nameText(node.name)) push("field", q(nameText(node.name)), "", node.getStart(sf), tokenEnd(node));
    else if (ts.isVariableStatement(node) && top) {
      const flags = ts.getCombinedNodeFlags(node.declarationList);
      const word = flags & ts.NodeFlags.Const ? "const" : flags & ts.NodeFlags.Let ? "let" : flags & ts.NodeFlags.Using ? "using" : flags & ts.NodeFlags.AwaitUsing ? "using" : "var";
      const stmtStart = node.getStart(sf);
      for (const d of node.declarationList.declarations) {
        if (!ts.isIdentifier(d.name)) continue;
        push(isFunctionInit(d.initializer) ? "function" : word, q(d.name.text), "", stmtStart, tokenEnd(d));
      }
    }
    nextTop = ts.isSourceFile(node) || ts.isModuleBlock(node) || (top && (ts.isExportDeclaration(node) || ts.isExportAssignment(node) || ts.isVariableStatement(node)));
    ts.forEachChild(node, (child) => visit(child, nextTop, nextNs));
  }
  visit(sf, true, "");
  return out;
}

for (const path of process.argv.slice(2)) {
  const text = fs.readFileSync(path, "utf8");
  const sf = ts.createSourceFile(path, text, ts.ScriptTarget.Latest, true, scriptKind(path));
  const accepted = sf.parseDiagnostics.length === 0;
  const row = { path, accepted, symbols: accepted ? symbolsOf(sf, text) : [] };
  process.stdout.write(JSON.stringify(row) + "\n");
}
