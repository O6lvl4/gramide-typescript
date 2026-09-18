#!/usr/bin/env python3
"""What a broken file costs to read: N brackets deleted from one file, or N
typed at the start of a word, at random, then `outline` (gramide, over its
recovered parse) and the tree-sitter harness (`--recover`) timed on it, each
the best of three runs, with how many outline lines gramide still lists
against the intact file's count. Every count at or above the number of
places a break can go takes all of them.

    python3 bench/recovery_cost.py --gramide BIN --tree-sitter HARNESS \\
        [--kinds 'delete ),delete },insert (,insert {'] \\
        [--counts 0,1,10,100,1000,10000,1000000] [--seed 3] [--out JSON] FILE
"""
import json, os, random, re, subprocess, sys, tempfile, time

def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name); v = sys.argv[i + 1]; del sys.argv[i:i + 2]; return v
    return default

gramide = arg("--gramide"); harness = arg("--tree-sitter"); out = arg("--out")
kinds = arg("--kinds", "delete ),delete },insert (,insert {").split(",")
counts = [int(x) for x in arg("--counts", "0,1,10,100,1000,10000,1000000").split(",")]; seed = int(arg("--seed", "3"))
if not (gramide and harness) or len(sys.argv) != 2: print(__doc__); sys.exit(2)
path = sys.argv[1]; text = open(path, encoding="utf-8", errors="surrogateescape").read()
word_starts = [m.start() for m in re.finditer(r"(?<![A-Za-z0-9_])[A-Za-z_]", text)]

def broken(kind, n):
    verb, ch = kind.split(" ")
    spots = [i for i, c in enumerate(text) if c == ch] if verb == "delete" else word_starts
    n = min(n, len(spots))
    picked = set(random.Random(seed).sample(spots, n)) if n else set()
    if verb == "delete": return n, "".join(c for i, c in enumerate(text) if i not in picked)
    return n, "".join((ch if i in picked else "") + c for i, c in enumerate(text))

def best_of(cmd, runs=3):
    best = None; r = None
    for _ in range(runs):
        t0 = time.perf_counter(); r = subprocess.run(cmd, capture_output=True, text=True); dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    return best, r

report = {"file": os.path.basename(path), "bytes": len(text.encode("utf-8", "surrogateescape")), "seed": seed, "kinds": {}}
for kind in kinds:
    rows = []; done = set()
    for want in counts:
        n, src = broken(kind, want)
        if n in done: continue
        done.add(n)
        with tempfile.NamedTemporaryFile("w", suffix=os.path.splitext(path)[1], delete=False, encoding="utf-8", errors="surrogateescape") as f:
            f.write(src); tmp = f.name
        try:
            g_s, g = best_of([gramide, "outline", tmp]); t_s, _ = best_of([harness, "--recover", "function_declaration,class_declaration,method_definition", tmp])
        finally:
            os.unlink(tmp)
        lines = len([l for l in g.stdout.splitlines() if l.lstrip().startswith("L")])
        rows.append({"breaks": n, "gramide_seconds": round(g_s, 3), "tree_sitter_seconds": round(t_s, 3), "gramide_outline_lines": lines})
        print(f"{kind:9} {n:7}: gramide {g_s:.3f} s ({lines} lines), tree-sitter {t_s:.3f} s", flush=True)
    report["kinds"][kind] = rows
report["intact_lines"] = next((r["gramide_outline_lines"] for rows in report["kinds"].values() for r in rows if r["breaks"] == 0), None)
if out:
    with open(out, "w") as f: json.dump(report, f, indent=1)
