#!/usr/bin/env python3
"""What a heavily broken file costs to read: N `)` deleted at random from one
file, then `outline` (gramide, over its recovered parse) and the tree-sitter
harness (`--recover`) timed on it, each the best of three runs, with how many
outline lines gramide still lists against the intact file's count.

    python3 bench/recovery_cost.py --gramide BIN --tree-sitter HARNESS [--counts 0,50,100,200,500] [--seed 3] [--out JSON] FILE
"""
import json, os, random, subprocess, sys, tempfile, time

def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name); v = sys.argv[i + 1]; del sys.argv[i:i + 2]; return v
    return default

gramide = arg("--gramide"); harness = arg("--tree-sitter"); out = arg("--out")
counts = [int(x) for x in arg("--counts", "0,50,100,200,500").split(",")]; seed = int(arg("--seed", "3"))
if not (gramide and harness) or len(sys.argv) != 2: print(__doc__); sys.exit(2)
path = sys.argv[1]; text = open(path, encoding="utf-8", errors="surrogateescape").read()
parens = [i for i, c in enumerate(text) if c == ")"]

def best_of(cmd, runs=3):
    best = None
    for _ in range(runs):
        t0 = time.perf_counter(); r = subprocess.run(cmd, capture_output=True, text=True); dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    return best, r

rows = []
for n in counts:
    rng = random.Random(seed); gone = set(rng.sample(parens, n)) if n else set()
    broken = "".join(c for i, c in enumerate(text) if i not in gone)
    with tempfile.NamedTemporaryFile("w", suffix=os.path.splitext(path)[1], delete=False, encoding="utf-8", errors="surrogateescape") as f:
        f.write(broken); tmp = f.name
    try:
        g_s, g = best_of([gramide, "outline", tmp]); t_s, _ = best_of([harness, "--recover", "function_declaration,class_declaration,method_definition", tmp])
    finally:
        os.unlink(tmp)
    lines = len([l for l in g.stdout.splitlines() if l.lstrip().startswith("L")])
    rows.append({"parens_deleted": n, "gramide_seconds": round(g_s, 3), "tree_sitter_seconds": round(t_s, 3), "gramide_outline_lines": lines})
    print(f"{n:5} parens deleted: gramide {g_s:.2f} s ({lines} lines), tree-sitter {t_s:.2f} s")
report = {"file": os.path.basename(path), "bytes": len(text.encode("utf-8", "surrogateescape")), "seed": seed, "rows": rows, "intact_lines": rows[0]["gramide_outline_lines"] if rows and rows[0]["parens_deleted"] == 0 else None}
if out:
    with open(out, "w") as f: json.dump(report, f, indent=1)
