# -*- coding: utf-8 -*-
"""Same-structure layer-height comparison: 0.28 baseline vs 0.20 vs 0.16.
Keeps 3 walls / 10% gyroid / >=0.8 mm shells (4 layers @0.20, 5 @0.16)."""
import json, os, shutil, subprocess, sys

BASE = r"D:\Work\嵌入式课设\.p2s-integrated-pla-fast-20261104"
CLI = r"C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe"
OUT = r"D:\Work\嵌入式课设\codex_readback\layer_height_tradeoff_20261104"
os.makedirs(OUT, exist_ok=True)

PARTS = {
    "LOWER_H41_B1": ("r3\\LOWER_H41_B1", 0.28, 49278.73828125, 373.94830322265625),
    "UPPER_INTEGRATED": ("r4\\UPPER_INTEGRATED", 0.28, 118706.3515625, 802.9749755859375),
}
LAYERS = [(0.20, 4), (0.16, 5)]

def find_key(obj, key):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                return v
            r = find_key(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_key(v, key)
            if r is not None:
                return r
    return None

rows = []
for part, (rel, base_lh, base_s, base_g) in PARTS.items():
    rows.append({"part": part, "layer_mm": base_lh, "shell_layers": 3,
                 "seconds": base_s, "grams": base_g, "status": "baseline r3/r4"})
    src = os.path.join(BASE, rel)
    for lh, shells in LAYERS:
        dst = os.path.join(BASE, "cmp", f"{part}_L{int(round(lh*100)):02d}")
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        os.makedirs(dst)
        for f in ["process.json", "machine.json", "filament.json", "geometry.3mf"]:
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        p = json.load(open(os.path.join(dst, "process.json"), encoding="utf-8"))
        p["layer_height"] = f"{lh}"
        p["top_shell_layers"] = str(shells)
        p["bottom_shell_layers"] = str(shells)
        p["top_shell_thickness"] = "0.8"
        p["bottom_shell_thickness"] = "0.8"
        p["print_settings_id"] = f"SmartBin PLA Fast cmp {part} {lh}"
        json.dump(p, open(os.path.join(dst, "process.json"), "w", encoding="utf-8"), indent=2)
        cmd = [CLI,
               "--datadir", os.path.join(dst, "isolated-data"),
               "--load-settings", f"{os.path.join(dst,'machine.json')};{os.path.join(dst,'process.json')}",
               "--load-filaments", os.path.join(dst, "filament.json"),
               "--arrange", "0", "--orient", "0", "--slice", "0",
               "--export-3mf", "sliced.3mf", "--outputdir", dst, "--debug", "2",
               os.path.join(dst, "geometry.3mf")]
        r = subprocess.run(cmd, cwd=dst, capture_output=True, text=True, timeout=1800)
        log = r.stdout + "\n" + r.stderr
        open(os.path.join(dst, "slice.log"), "w", encoding="utf-8").write(log)
        res = None
        rj = os.path.join(dst, "result.json")
        if os.path.exists(rj):
            res = json.load(open(rj, encoding="utf-8"))
        s = find_key(res, "total_predication")
        g = find_key(res, "total_used_g")
        warn = find_key(res, "warning_message")
        rows.append({"part": part, "layer_mm": lh, "shell_layers": shells,
                     "seconds": s, "grams": g, "rc": r.returncode,
                     "warning": warn, "status": "sliced"})
        print(part, lh, "rc=", r.returncode, "s=", s, "g=", g, "warn=", warn, flush=True)
        for junk in ("plate_1.gcode", "sliced.3mf", "isolated-data"):
            jp = os.path.join(dst, junk)
            if os.path.isdir(jp):
                shutil.rmtree(jp, ignore_errors=True)
            elif os.path.exists(jp):
                os.remove(jp)

json.dump(rows, open(os.path.join(OUT, "results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("\n== summary ==")
for r in rows:
    if r.get("seconds") is None:
        print(r["part"], r["layer_mm"], "FAILED")
        continue
    print(f"{r['part']:18s} L={r['layer_mm']:.2f} shells={r['shell_layers']} "
          f"{r['seconds']/3600:6.2f} h  {r['grams']:8.2f} g")
print("written:", os.path.join(OUT, "results.json"))
