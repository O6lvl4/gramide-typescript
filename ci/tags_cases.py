"""What the TypeScript package reports as references, and what it does not.

`tags` is the repo map's input: definitions to rank, references to rank them
by. A reference is a call of a name or a type mention. Everything this does
not cover is listed at the bottom, as a case with the output it does give, so
that adding it later is a diff here rather than a surprise. The corpora in
docs/evidence/tags-*.json check the same rules against the TypeScript
compiler's parser on real code; this file is the rules, one line each."""
from pathlib import Path
import subprocess, tempfile

BIN = Path(__file__).resolve().parents[1] / "gramide_typescript"

COVERED = [
 ("a call, with or without type arguments, which are type mentions", "f(1)\ng<T>(2)\nnew Map<K, V>()\n", ["ref call f L1", "ref call g L2", "ref type T L2", "ref call Map L3", "ref type K L3", "ref type V L3"]),
 ("a non-null `!` is not there", "x!.add(1)\nthis.f!(2)\n", ["ref call x.add L1", "ref call f L2"]),
 ("an annotation, a return type, a type argument", "function f(x: Foo): Bar<Baz> {}\n", ["def function f L1-1", "ref type Foo L1", "ref type Bar L1", "ref type Baz L1"]),
 ("a qualified name mentions its first segment", "let u: ns.Foo\n", ["def let u L1-1", "ref type ns L1"]),
 ("assertions and `satisfies`", "const a = <Foo>x\nconst b = y as Bar\nconst c = z satisfies Baz\n",
  ["def const a L1-1", "ref type Foo L1", "def const b L2-2", "ref type Bar L2", "def const c L3-3", "ref type Baz L3"]),
 ("a class's bare-name base and its interfaces", "class A extends B implements C, D {}\n", ["def class A L1-1", "ref type B L1", "ref type C L1", "ref type D L1"]),
 ("an interface's bases", "interface I extends J, K {}\n", ["def interface I L1-1", "ref type J L1", "ref type K L1"]),
 ("a type alias's parts, a constraint, a conditional", "type T = Foo | Bar\ntype U<X extends Base> = X extends Foo ? Bar : Baz\n",
  ["def type T L1-1", "ref type Foo L1", "ref type Bar L1", "def type U L2-2", "ref type Base L2", "ref type X L2", "ref type Foo L2", "ref type Bar L2", "ref type Baz L2"]),
 ("`keyof`, an indexed access, a template literal type", "let a: keyof Foo\nlet b: Bar['k']\nlet c: `${Baz}`\n",
  ["def let a L1-1", "ref type Foo L1", "def let b L2-2", "ref type Bar L2", "def let c L3-3", "ref type Baz L3"]),
]

# Each of these is a reference a reader can see and `tags` does not report. None
# is a defect to be fixed quietly: each is a decision, and changing one should
# change this list. The oracle in reference_tags.mjs states the same decisions.
NOT_COVERED = [
 ("a keyword type is not a reference to anything a file declares", "let s: string\nlet o: object\ntype U<S> = intrinsic\n", ["def let s L1-1", "def let o L2-2", "def type U L3-3"]),
 ("`as const` is not a type", "const t = [1] as const\n", ["def const t L1-1"]),
 ("`typeof x` names a value, `import('m').T` a module", "let a: typeof x\nlet b: import('m').T\n", ["def let a L1-1", "def let b L2-2"]),
 ("a base that is an expression is not a name", "class A extends mix(B) {}\n", ["def class A L1-1", "ref call mix L1"]),
 ("a JSX tag names a component, and is not reported; its type arguments are", "const j = <Foo<T> x={g(1)} />\n", ["def const j L1-1", "ref type T L1", "ref call g L1"]),
 ("an import is a reference, and Rust's `use` is not reported either", "import type { X } from 'm'\nimport y = require('n')\n", []),
]

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for label, source, expected in COVERED + NOT_COVERED:
        path = root / ("case.tsx" if "<Foo<T>" in source else "case.ts")
        path.write_text(source)
        result = subprocess.run([str(BIN), "tags", str(path)], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0 and not result.stderr, (label, result.returncode, result.stderr)
        assert result.stdout.split("\n")[:-1] == expected, (label, source, expected, result.stdout)
print(f"TypeScript tags: {len(COVERED)} reported cases and {len(NOT_COVERED)} deliberately unreported ones")
