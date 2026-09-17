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
| Excalidraw `packages/excalidraw/**/*.ts` at `a9186480` | 187 | 3.1 MB | all parse; all 3,264 declarations match the reference |

The same files through `tags`, with every reference compared against a second
oracle over the compiler's parser ([rules](ci/reference_tags.mjs)):

| corpus | references | result |
|---|---:|---|
| TypeScript 5.9.3 `src/` | 175,408 | all match ([evidence](docs/evidence/tags-typescript-src.json)) |
| TypeScript 5.9.3 `lib/*.d.ts` | 27,369 | all match ([evidence](docs/evidence/tags-typescript-lib-dts.json)) |
| MUI docs `.tsx` | 2,932 | all match ([evidence](docs/evidence/tags-mui-docs-tsx.json)) |
| Excalidraw `.tsx` | 29,074 | all match ([evidence](docs/evidence/tags-excalidraw-tsx.json)) |
| Excalidraw `.ts` | 12,175 | all match ([evidence](docs/evidence/tags-excalidraw-ts.json)) |

A reference is a call of a name (`f(…)`, `a.b(…)`, `new Map<K, V>(…)`, an
applied decorator; a non-null `!` is not there) or a type mention: an
annotation, a type argument, `as` / `satisfies` / `<T>x`, `keyof T`, an
`implements` or `extends` clause, a qualified name by its first segment.
What is deliberately not one (keyword types, `as const`, `typeof x`, JSX tag
names, imports) is listed in [ci/tags_cases.py](ci/tags_cases.py).

([evidence](docs/evidence/corpus-typescript-src.json),
[evidence](docs/evidence/corpus-typescript-lib-dts.json),
[evidence](docs/evidence/corpus-mui-docs-tsx.json),
[evidence](docs/evidence/corpus-excalidraw-tsx.json),
[evidence](docs/evidence/corpus-excalidraw-ts.json).) A declaration
here is everything the JavaScript package lists, plus interfaces, type
aliases, enums and namespaces, method and property signatures, and the
names inside a namespace qualified with it (`ts.Parser.parse`). The batched
`check` over the compiler's `src/` runs at about 340 MB/s on eight cores.

The fixtures CI runs are in [ci/README.md](ci/README.md).

## Against tree-sitter

tree-sitter-typescript at `75b3874` on the tree-sitter runtime at `1b8407d`,
through [bench/tree_sitter_ranges.c](bench/tree_sitter_ranges.c): a fresh
process per file, the parse verdict and then the declaration listing, both
tools alternating, the minimum of three runs kept
([evidence](docs/evidence/tree-sitter-typescript-src.json), method in
[bench/tree_sitter.py](bench/tree_sitter.py)).

| TypeScript 5.9.3 `src/`, 701 files, 20.6 MB | gramide | tree-sitter |
|---|---:|---:|
| parse verdict, sum over the files | 1.676 s | 1.837 s |
| declaration listing, sum over the files | 1.986 s | 2.054 s |
| the 16 files of 200 KB or more (7.9 MB), verdict | 0.151 s | 0.305 s |
| those 16 files, listing | 0.277 s | 0.398 s |
| `compiler/checker.ts` (3.1 MB), verdict | 47 ms | 101 ms |
| an empty file (the process floor) | 1.75 ms | 1.37 ms |

Ahead by a tenth on the sum, which is mostly process floors, and by 2× on
the files where parsing is the cost. The floor is 0.28 ms above the C
harness, 0.15 ms of it Rust's standard runtime starting, and is paid once
per process, so it is left as it is
([where it goes](https://github.com/O6lvl4/gramide-javascript/blob/main/docs/evidence/process-floor.json)). tree-sitter reports a syntax error on
four of these files (`compiler/types.ts`, `compiler/transformers/utilities.ts`,
`services/exportInfoMap.ts`, `lib/es2015.symbol.wellknown.d.ts`) that the
compiler and this package accept. gramide's listing carries more (fields,
bindings, namespaces, owners on every method: 48,691 rows to 19,300), so the
listing rows compare more work against less.

The same on `.tsx`, against tree-sitter's tsx grammar
([evidence](docs/evidence/tree-sitter-mui-docs-tsx.json),
[evidence](docs/evidence/tree-sitter-excalidraw-tsx.json)):

| corpus | gramide | tree-sitter |
|---|---:|---:|
| MUI docs `.tsx`, 538 files, 1.0 MB: verdict, sum | 1.054 s | 0.910 s |
| MUI docs `.tsx`: listing, sum | 1.101 s | 0.930 s |
| Excalidraw `.tsx`, 261 files, 2.6 MB: verdict, sum | 0.552 s | 0.544 s |
| Excalidraw `.tsx`: listing, sum | 0.610 s | 0.584 s |
| `components/App.tsx` (465 KB), verdict | 9.9 ms | 20.1 ms |
| `components/App.tsx`, listing | 16.6 ms | 25.8 ms |

The MUI demos average 2 KB, so that sum is the process floor; App.tsx shows
the parse. tree-sitter's tsx grammar reports a syntax error on two Excalidraw
test files the compiler and this package accept.

### One keystroke

An editor does not parse the file again on every keystroke; it hands the
parser the edit. gramide keeps a parsed file as its recover items — here,
every top-level declaration and every statement or class member inside
braces — and re-reads the smallest one an edit touched
([how](https://github.com/O6lvl4/gramide/blob/main/docs/incremental.md)).
The same 1,000 edits, in-process, for gramide's `reparse-bench` and for
tree-sitter's `ts_tree_edit` + reparse through the same C harness (each a
letter typed or deleted six letters into a word of thirteen or more, so
the file stays what it was syntactically); every fiftieth result checked
against a whole parse ([evidence](docs/evidence/incremental-typescript-src.json),
[evidence](docs/evidence/incremental-excalidraw-tsx.json)):

| median over 1,000 edits | gramide | tree-sitter | a whole parse |
|---|---:|---:|---:|
| `compiler/parser.ts` (540 KB) | 17 µs | 119 µs | 8.9 ms |
| `compiler/checker.ts` (3.1 MB, one function of 2.9 MB) | 78 µs | 561 µs | 54 ms |
| Excalidraw `components/App.tsx` (465 KB) | 15 µs | 221 µs | 9.3 ms |

`checker.ts` is where a whole parse per keystroke is out of the question
and where tree-sitter's reparse is slowest; the deepest item holding the
edit is one statement, and that is all gramide reads.

What comes out is the whole parse: ten random edits in each file of three
corpora, every one checked token for token and node for node against a
whole parse of the same text ([evidence](docs/evidence/incremental-corpus-typescript-src.json),
[evidence](docs/evidence/incremental-corpus-mui-docs-tsx.json),
[evidence](docs/evidence/incremental-corpus-excalidraw-ts.json)):

| corpus | files | edits | differences | read as a whole file |
|---|---:|---:|---:|---:|
| TypeScript 5.9.3 `src/` | 643 | 6,430 | 0 | 0 |
| MUI docs `.tsx` | 489 | 4,890 | 0 | 0 |
| Excalidraw `.ts` | 178 | 1,780 | 0 | 0 |

With an unmatched `{` typed every tenth edit, so that the file stops
parsing and the check runs against the recovering parse, still no
difference; 654, 460 and 160 of those edits read the whole file — the
breaking ones, the windows inside the damage, and a JSX text a brace
cannot lex ([evidence](docs/evidence/incremental-corpus-typescript-src-breaking.json),
[evidence](docs/evidence/incremental-corpus-mui-docs-tsx-breaking.json),
[evidence](docs/evidence/incremental-corpus-excalidraw-ts-breaking.json)).
`ci/incremental_check.py` runs these; `reparse --edit START:OLD_END:NEW_END --new FILE`
is the one-edit command.

### A broken file

An editor's file is broken more often than not. `bench/recovery.py` breaks every
file of the corpus in four ways, one at a time — a `{` typed at the start of a
word, a `}` deleted, a `)` deleted, a `(` typed — and compares what each tool
still lists (gramide's `outline`, which reads the recovered parse; tree-sitter's
tree through the same harness, `--recover`) with its own listing of the whole
file, by kind, name and start line. A declaration whose lines hold the break is
expected to go; a break is *clean* when nothing else is lost and nothing new
appears ([evidence](docs/evidence/recovery-typescript-src.json), [how it recovers](https://github.com/O6lvl4/gramide/blob/main/docs/recovery.md)):

| TypeScript `src/`: 697 files, 2,588 breaks | gramide | tree-sitter |
|---|---:|---:|
| declarations kept, all breaks | 97.3% | 99.0% |
| clean breaks (nothing lost beyond the break, nothing invented) | 91.5% | 94.6% |
| clean breaks, `insert {` | 94.0% | 96.4% |
| clean breaks, `delete }` | 84.3% | 86.7% |
| clean breaks, `delete )` | 91.3% | 98.8% |
| clean breaks, `insert (` | 95.4% | 96.1% |

tree-sitter is ahead, mostly on a `)` deleted inside a member's head: the
member fails, the skip resumes inside it, and the method's `}` then closes the
class, so every later member reads as statements.

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
