# Reproducible checks

Run `bash ci/check.sh` from a checkout with Almide and Node installed, or set
`ALMIDE_BIN` to an absolute compiler path. This runs the package's tests,
builds its own binary from `cli/main.almd`, fails if `src/table.almd` or `src/table_tsx.almd` is not
what the grammar compiles to, drives the binary through temporary fixtures,
and compares `symbols` with `ci/reference_ranges.mjs`, an oracle over the
TypeScript compiler's own parser that knows nothing of gramide — on a UTF-8
fixture with generics, an interface with signatures of every kind, a const
enum, ambient modules, a global augmentation, a dotted namespace, an
abstract decorated class with overloads and parameter properties, a mapped
type, a conditional type with `infer`, and `export =`; on five files the
oracle rejects, which gramide must reject too; and on 2,000 generated
generic functions. No model API or credentials are used.

The oracle is `typescript` 5.9.3 from npm, pinned in `ci/package.json`;
`cd ci && npm ci` fetches it, and `check.sh` skips the oracle steps with a
message when it is missing.

`python3 ci/reference_corpus.py /path/to/TypeScript/src docs/evidence/corpus-typescript-src.json`
runs the same comparison over every `.ts`, `.mts` and `.cts` file under a
directory — acceptance both ways, then every declaration's kind, name, owner,
line and byte range — and writes the evidence the README cites.

`python3 ci/reference_tags.py /path/to/src docs/evidence/tags-typescript-src.json`
does the same for `tags`: every `ref call` and `ref type` line against
`ci/reference_tags.mjs`, a second oracle over the compiler's parser that
states the reference rules in its header. `ci/tags_cases.py` is those rules
one line each, with the references deliberately not reported listed beside
the ones that are.

`./gramide_typescript lex-check FILE...` runs the scanner alone, strictly,
and names the files that do not lex.

CI pins Almide to `dff9a458f2e581631bb6537c856a7974036e4153`, Rust to
`1.94.0` and Node to 22. Upgrade these deliberately and rerun the checks
together.
