"""Structured ranges against the TypeScript compiler's parser, on fixtures;
no model calls. The corpus-wide run is ci/reference_corpus.py."""
from pathlib import Path
import json, subprocess, tempfile
HERE = Path(__file__).resolve().parent
BIN = HERE.parent / "gramide_typescript"
COMPARED = ["kind", "name", "owner", "start", "end", "start_byte", "end_byte"]

def oracle(paths):
    p = subprocess.run(["node", str(HERE / "reference_ranges.mjs"), *map(str, paths)], capture_output=True, text=True, cwd=HERE, check=True)
    return {json.loads(l)["path"]: json.loads(l) for l in p.stdout.splitlines()}

def symbols(path):
    p = subprocess.run([str(BIN), "symbols", str(path)], capture_output=True, text=True, check=True)
    d = json.loads(p.stdout); assert d["schema_version"] == 1 and d["complete"] is True
    return [{k: s[k] for k in COMPARED} for s in d["symbols"]]

FIXTURE = '''// 日本語 before declarations tests UTF-8 byte offsets.
import type { Reader } from "./io"
import fs = require("node:fs")
export type Handler<T extends object = {}> = (event: T, ...rest: unknown[]) => void | Promise<void>
export interface Widget<T> extends Base, Other<T> {
  readonly id: string
  size?: number
  [key: string]: unknown
  render<U>(this: Widget<T>, into: U): asserts into is Element
  get value(): T
  new (x: number): Widget<T>
}
export const enum Color { Red = 1, Green, "Blue" = 1 << 2 }
declare module "legacy" { export function old(): void }
declare global { interface Window { app: App } }
export namespace ns.inner { export const x: readonly string[] = []; export class C { m(): void {} } }
@sealed
export abstract class Base<in out T = string> implements Widget<T> {
  declare readonly kind: "base"
  private static count = 0
  protected abstract render(): void
  render(into?: unknown): void
  render(into?: unknown): void { this.count! }
  constructor(public name: string, private readonly opts: { a?: number } = {}) { super() }
  accessor state: Map<string, Array<T>> = new Map<string, Array<T>>()
  static { Base.count = 1 }
}
export function isWidget(x: unknown): x is Widget<any> { return (x as Widget<any>).id !== undefined }
export default function main<T,>(arg: T): T { return <T>arg satisfies T }
export declare const version: string
let value = a >> b >>> c >= d, mapped: { -readonly [K in keyof T as `get${K & string}`]-?: T[K] }
type Cond<T> = T extends [infer H extends string, ...infer R] ? H : never
const handlers = { onClick(): void {}, get value() { return 1 } }
export = main
'''

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    fixture = root / "ranges.ts"; fixture.write_text(FIXTURE)
    expected = oracle([fixture])[str(fixture)]
    assert expected["accepted"], "the fixture must parse for the oracle"
    actual = symbols(fixture)
    want = [{k: s[k] for k in COMPARED} for s in expected["symbols"]]
    assert actual == want, "\n".join(f"{a}\n{b}" for a, b in zip(actual, want) if a != b) or (len(actual), len(want), actual[len(want):], want[len(actual):])
    raw = fixture.read_bytes()
    for s in json.loads(subprocess.check_output([str(BIN), "symbols", str(fixture)], text=True))["symbols"]:
        assert raw[s["start_byte"]:s["end_byte"]].strip()
    total = len(want)
    broken = root / "broken.ts"
    for source in ["function f(x: ): void {}\n", "interface I { a: string\n b: }\n", "let x: Map<string = 1\n", "class A { m(: void {} }\n", "type T = \n"]:
        broken.write_text(source)
        assert not oracle([broken])[str(broken)]["accepted"], source
        p = subprocess.run([str(BIN), "symbols", str(broken)], capture_output=True, text=True)
        assert p.returncode != 0 and not p.stdout, (source, p.returncode, p.stdout)
    large = root / "many.ts"
    large.write_text("".join(f"export function F{i}<T>(x: T): T {{ return x }}\n" for i in range(2000)))
    actual = symbols(large)
    assert actual == [{k: s[k] for k in COMPARED} for s in oracle([large])[str(large)]["symbols"]] and len(actual) == 2000
print(f"Structured ranges passed: TypeScript parser oracle on UTF-8, generics, interfaces, enums, namespaces, overloads, {total} fixture declarations, 5 rejections and 2,000 functions")
