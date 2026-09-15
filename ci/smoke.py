"""Exercise the package's own binary; no network, no model, no oracle."""
from pathlib import Path
import json, subprocess, tempfile

BIN = Path(__file__).resolve().parents[1] / "gramide_typescript"

def run(*args, code=0):
    p = subprocess.run([str(BIN), *map(str, args)], capture_output=True, text=True, timeout=30)
    assert p.returncode == code, (args, p.returncode, p.stdout, p.stderr)
    return p.stdout

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for ext in ["ts", "mts", "cts"]:
        source = root / ("valid." + ext)
        source.write_text("export interface Shape { area(): number }\nexport class Box<T> implements Shape {\n  constructor(private readonly x: T) {}\n  area(): number { return (this.x as unknown as number) ** 2 }\n}\nexport const make = <T,>(x: T): Box<T> => new Box<T>(x)\ntype Id<T> = T extends infer U ? U : never\n")
        run("check", source)
        out = run("outline", source)
        assert "Shape.area" in out and "Box.constructor" in out and "function make" in out and "type Id" in out, out
        doc = json.loads(run("symbols", source))
        assert doc["lang"] == "typescript" and doc["complete"] is True and doc["symbols"][0]["start_byte"] == 0, doc
        broken = root / ("broken." + ext)
        broken.write_text("export class Box {\n  read(): number { return 1 }\n  broken(: {\n  also(x: string) { return x }\n}\nexport function f(): void {}\n")
        run("check", broken, code=1)
        recovered = run("outline", broken)
        assert "Box.read" in recovered and "Box.also" in recovered and "function f" in recovered, recovered
    tsx = root / "view.tsx"
    tsx.write_text("export function View<T>({ items }: { items: T[] }) {\n  return <ul>{items.map((i) => <li key={String(i)}>{i}</li>)}</ul>\n}\nconst pick = <T,>(a: T) => <Select<T> value={a} />\n")
    run("check", tsx)
    doc = json.loads(run("symbols", tsx))
    assert doc["lang"] == "tsx" and doc["complete"] is True and [s["name"] for s in doc["symbols"] if s["kind"] == "function"] == ["View", "pick"], doc
    assert run("version").splitlines()[0].startswith("gramide_typescript ")
print("CLI smoke passed: .ts .mts .cts .tsx check, outline, symbols and recovered outline")
