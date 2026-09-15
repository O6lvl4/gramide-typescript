# gramide-typescript

TypeScript for [gramide](https://github.com/O6lvl4/gramide), as a language
package: the JavaScript package's scanner and grammar with the type syntax
put under its extension points, the rules that say which nodes declare a
name, that grammar compiled to a table, and a binary of its own, so that the
language can be tested against its reference parser, measured and
regenerated without the others. Written in
[Almide](https://github.com/almide/almide).

[日本語](README_ja.md)

```
gramide_typescript check   src/*.ts      exit 0 if it parses, else `file:line:col: unexpected X (expected …)`
gramide_typescript outline app.ts        `L12-40 class Widget`, `  L20-24 method Widget.render`, `L50-61 interface Props`
gramide_typescript symbols app.ts        versioned JSON names, owners, line and byte ranges
gramide_typescript tags    app.ts        definitions and references: a repo map's input
gramide_typescript map .   --budget 1024 --task "fix the retry"
```

The shipped `gramide` command ([gramide-cli](https://github.com/O6lvl4/gramide-cli))
composes this package with the others; `almide install github.com/O6lvl4/gramide-cli`
is how most people get it. This repository is where TypeScript is defined
and where its correctness is checked.

## What it reads

`.ts`, `.mts` and `.cts`, and `.tsx` as a second definition, as TypeScript
5.9: everything
[gramide-javascript](https://github.com/O6lvl4/gramide-javascript) reads,
plus type annotations, generics with constraints, defaults and variance,
interfaces, type aliases, enums, namespaces and ambient modules, `declare`,
`abstract`, accessibility and `readonly` modifiers, parameter properties,
overloads, index signatures, `import type` / `export type`, `import x =
require()`, `export =`, decorators, `as`, `satisfies`, the `!` assertion and
the `<T>x` assertion; and in types, unions, intersections, conditional and
mapped types, `infer`, `keyof` / `typeof` / `unique symbol`, tuples with names
and rests, function and constructor types, template literal types,
`import("m").T` and type predicates. A `.tsx` file is read by the same
grammar with JSX where an expression may stand and without the `<T>x`
assertion, which is what the compiler does; a tag may carry type arguments
(`<Select<string[]> multiple>`).

As in the JavaScript package, the grammar refuses what is not TypeScript and
does not promise to refuse every file the compiler refuses: a file gramide
rejects is broken for the compiler too, which is the direction a syntax
gate must get right and the direction the oracle below checks.

## What was checked

Every `.ts` file under `src/` of the TypeScript compiler at its 5.9.3 tag,
and the `.d.ts` files the compiler ships, through this package and through
the compiler's own parser, with the two answers compared: whether the file
parses, then for every declaration its kind, name, owner, line range and
byte range.

| corpus | files | bytes | result |
|---|---:|---:|---|
| TypeScript 5.9.3 `src/` | 701 | 20.6 MB | all parse; all 48,691 declarations match the reference |
| TypeScript 5.9.3 `lib/*.d.ts` | 102 | 3.7 MB | all parse; all 26,413 declarations match the reference |
| MUI `docs/data/{material,joy}/components/**/*.tsx` at `053c4319` | 538 | 1.0 MB | all parse; all 1,378 declarations match the reference |
| Excalidraw `packages/excalidraw/**/*.tsx` at `a9186480` | 261 | 2.6 MB | all parse; all 2,848 declarations match the reference |

([evidence](docs/evidence/corpus-typescript-src.json),
[evidence](docs/evidence/corpus-typescript-lib-dts.json),
[evidence](docs/evidence/corpus-mui-docs-tsx.json),
[evidence](docs/evidence/corpus-excalidraw-tsx.json).) A declaration
here is everything the JavaScript package lists, plus interfaces, type
aliases, enums and namespaces, method and property signatures, and the
names inside a namespace qualified with it (`ts.Parser.parse`). The batched
`check` over the compiler's `src/` runs at about 340 MB/s on eight cores.

The fixtures CI runs are in [ci/README.md](ci/README.md).

## How it is written

- **`src/lexer.almd`** — the JavaScript scanner told to read `>` one token
  at a time, so `Array<Array<T>>` closes two brackets; the grammar joins the
  shift and comparison operators back without checking that the tokens are
  adjacent. Two further rules the type syntax forces on the scanner live in
  the JavaScript package under the same switch: a `>` after an operand ends
  the operand (`Promise<void>` ends a line the way a name does), and a line
  break before `[key: T]` or `(x: T)` separates the members of an object
  type where JavaScript would read an index or a call.
- **`src/types.almd`** — the type grammar, from a conditional type down to a
  reference.
- **`src/grammar.almd`** — every JavaScript extension point filled, the
  comparison and shift levels rebuilt around the split `>`, and the
  declarations TypeScript adds. `js.with_overrides` puts each rule under the
  JavaScript name it replaces, so the two grammars are one grammar with two
  tables.
- **`src/symbols.almd`** — the JavaScript rules plus interfaces, type
  aliases, enums and namespaces; a namespace qualifies what it holds, an
  ambient module and a global augmentation do not.
- **`src/table.almd`** and **`src/table_tsx.almd`** — generated by `gen-table`
  and `gen-table-tsx`; CI fails if either is stale.

## Checks

`bash ci/check.sh` needs Almide, Node 22 and `cd ci && npm ci` for the
oracle. It runs `almide test`, the table check, the binary's smoke test and
the fixtures.

## License

MIT or Apache-2.0, at your option.
