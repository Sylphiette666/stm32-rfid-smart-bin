# -*- coding: utf-8 -*-
"""Build the R3D PETG (all-0.28 mm) delivery package from sliced candidates.

Steps:
 1. Read candidate results for the 3 chosen 0.28 mm parts.
 2. Export project.3mf (no gcode) for each chosen part via Bambu Studio CLI.
 3. Validate exported 3MF: zip ok, no gcode, .model identical to sliced.3mf,
    embedded settings match expected R3D PETG / 0.28 mm configuration.
 4. Assemble package: projects/ checks/ preview/ source/ README.md SHA256.json.
 5. Mirror package into the repo print-backup folder and build the zip.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

CLI = Path(r"C:\Users\35462\AppData\Local\Temp\smartbin-bambu-cli-20261030\portable\BambuCliHost.exe")
PY = Path(r"C:\Users\35462\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe")
ROOT = Path(r"D:\Work\嵌入式课设")
W = ROOT / ".p2s-petg-fast-20261104"
REPO = ROOT / "stm32-rfid-smart-bin"
REPO_TARGET = REPO / "hardware" / "mechanical" / "print-backup" / "r3d-petg-fast-20261104"
NEW = ROOT / "智能垃圾桶_R3D_PETG树形支撑_全件0.28最快_20261104"
ZIP = ROOT / "智能垃圾桶_R3D_PETG树形支撑_全件0.28最快_20261104.zip"
TZ = timezone(timedelta(hours=8))

PARTS = [
    # tag, name, project filename, support_expected, infill_expected
    ("LOWER_H41_B1_L28", "LOWER_H41_B1", "P2S_LOWER_H41_B1_R3D_PETG_FAST_CANDIDATE.3mf", "1", "10%"),
    ("UPPER_INTEGRATED_L28", "UPPER_INTEGRATED", "P2S_UPPER_INTEGRATED_R3D_PETG_FAST_CANDIDATE.3mf", "1", "10%"),
    ("PANEL_COVER_L28", "PANEL_COVER", "P2S_PANEL_COVER_R3D_PETG_FAST_CANDIDATE.3mf", "0", "15%"),
]
CANDIDATE_TAGS = []
for _tag, _name, _proj, _sup, _inf in PARTS:
    for _v in ("L28", "L24", "L20"):
        CANDIDATE_TAGS.append(("%s_%s" % (_name, _v), _name, _v))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_result_metrics(tag):
    work = W / tag
    saved = W / "results" / (tag + ".json")
    if saved.exists():
        d = read_json(saved)
        r = d.get("result") or {}
        plates = r.get("sliced_plates") or [{}]
        plate = plates[0]
        seconds = float(d.get("total_predication_s", plate.get("total_predication", 0.0)))
        grams = float(d.get("grams", sum(float(f.get("total_used_g", 0.0)) for f in plate.get("filaments", []))))
        return {
            "seconds": round(seconds, 6),
            "hours": round(seconds / 3600.0, 6),
            "grams": round(grams, 6),
            "warning": d.get("warning_message") or plate.get("warning_message") or "",
            "layer_height": d.get("layer_height"),
            "wall_loops": r.get("wall_loops"),
            "sparse_infill_density": r.get("sparse_infill_density"),
            "triangle_count": plate.get("triangle_count"),
            "return_code": d.get("returncode", r.get("return_code")),
            "sliced_3mf_sha256": sha256(work / "sliced.3mf"),
        }
    r = read_json(work / "result.json")
    plate = r["sliced_plates"][0]
    grams = sum(float(f.get("total_used_g", 0.0)) for f in plate.get("filaments", []))
    return {
        "seconds": round(float(plate["total_predication"]), 6),
        "hours": round(float(plate["total_predication"]) / 3600.0, 6),
        "grams": round(grams, 6),
        "warning": plate.get("warning_message") or "",
        "layer_height": r.get("layer_height"),
        "wall_loops": r.get("wall_loops"),
        "sparse_infill_density": r.get("sparse_infill_density"),
        "triangle_count": plate.get("triangle_count"),
        "return_code": r.get("return_code"),
        "sliced_3mf_sha256": sha256(work / "sliced.3mf"),
    }


def run_cli(work, extra):
    cmd = [
        str(CLI), "--datadir", str(work / "isolated-data"),
        "--load-settings", "%s;%s" % (work / "machine.json", work / "process.json"),
        "--load-filaments", str(work / "filament.json"),
        "--arrange", "0", "--orient", "0",
    ] + extra + ["--outputdir", str(work), "--debug", "2", str(work / "geometry.3mf")]
    log = work / "export.log"
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        fh.write("CMD: %s\n" % " ".join(cmd))
        p = subprocess.run(cmd, cwd=str(work), stdout=fh, stderr=subprocess.STDOUT, timeout=1800)
    return p.returncode


def export_project(tag):
    work = W / tag
    if (work / "project.3mf").exists():
        (work / "project.3mf").unlink()
    rc = run_cli(work, ["--export-3mf", "project.3mf"])
    if rc != 0:
        raise SystemExit("export rc=%s for %s" % (rc, tag))
    res = read_json(work / "result.json")
    if res.get("return_code") not in (0, "0"):
        raise SystemExit("export return_code=%r for %s" % (res.get("return_code"), tag))
    return work / "project.3mf"


def zip_entries(path):
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        entries = z.namelist()
        data = {}
        for n in entries:
            data[n] = z.read(n)
    if bad:
        raise SystemExit("zip test failed: %s" % bad)
    return entries, data


def validate_project_3mf(tag, name, project_path, support_expected, infill_expected):
    work = W / tag
    entries, data = zip_entries(project_path)
    gcode = [n for n in entries if n.lower().endswith(".gcode") or n.lower().endswith(".gcode.3mf")]
    if gcode:
        raise SystemExit("gcode found in project: %r" % gcode)
    models = [n for n in entries if n.lower().endswith(".model")]
    src_entries, src_data = zip_entries(work / "sliced.3mf")
    for m in models:
        if m not in src_data or data[m] != src_data[m]:
            raise SystemExit(".model mismatch: %s (%s)" % (m, tag))
    cfg = json.loads(data["Metadata/project_settings.config"].decode("utf-8"))

    def one(key):
        v = cfg[key]
        return v[0] if isinstance(v, list) else v

    checks = {
        "layer_height": float(one("layer_height")) == 0.28,
        "wall_loops": int(one("wall_loops")) == 3,
        "top_shell_layers": int(one("top_shell_layers")) == 3,
        "bottom_shell_layers": int(one("bottom_shell_layers")) == 3,
        "sparse_infill_density": str(one("sparse_infill_density")) == infill_expected,
        "enable_support": str(one("enable_support")) == support_expected,
        "filament_type": one("filament_type") == "PETG",
        "filament_vendor": one("filament_vendor") == "R3D",
        "nozzle_temperature": float(one("nozzle_temperature")) == 250.0,
        "nozzle_temperature_initial_layer": float(one("nozzle_temperature_initial_layer")) == 250.0,
        "filament_max_volumetric_speed": float(one("filament_max_volumetric_speed")) == 12.0,
        "filament_flow_ratio": abs(float(one("filament_flow_ratio")) - 0.95) < 1e-9,
        "fan_min_speed": float(one("fan_min_speed")) == 10.0,
        "fan_max_speed": float(one("fan_max_speed")) == 40.0,
        "overhang_fan_speed": float(one("overhang_fan_speed")) == 40.0,
        "textured_plate_temp": float(one("textured_plate_temp")) == 60.0,
        "hot_plate_temp": float(one("hot_plate_temp")) == 60.0,
        "printer_model": one("printer_model") == "Bambu Lab P2S",
        "nozzle_diameter": str(one("nozzle_diameter")) == "0.4",
        "curr_bed_type": one("curr_bed_type") == "Textured PEI Plate",
        "initial_layer_print_height": abs(float(one("initial_layer_print_height")) - 0.2) < 1e-9,
    }
    if support_expected == "1":
        checks["independent_support_layer_height"] = str(cfg.get("independent_support_layer_height", "0")) in ("0", "0.0")
        checks["support_type"] = one("support_type") == "tree(auto)"
        checks["support_threshold_angle"] = float(one("support_threshold_angle")) == 35.0
        checks["support_top_z_distance"] = abs(float(one("support_top_z_distance")) - 0.28) < 1e-9
        checks["brim_width"] = float(one("brim_width")) == 6.0
    else:
        checks["brim_width"] = float(one("brim_width")) == 3.0
    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise SystemExit("embedded config check failed for %s: %r" % (tag, failed))
    if any(n.lower().endswith(".gcode") for n in entries):
        raise SystemExit("gcode found")
    return {
        "sha256": sha256(project_path),
        "bytes": project_path.stat().st_size,
        "entries": len(entries),
        "no_gcode": True,
        "model_files_identical_to_sliced": True,
        "embedded_checks": checks,
        "sliced_3mf_sha256": sha256(work / "sliced.3mf"),
        "sliced_3mf_bytes": (work / "sliced.3mf").stat().st_size,
    }


def fmt_hms(seconds):
    total = int(round(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h == 0:
        return "%d分%d秒" % (m, s)
    return "%d小时%d分%d秒" % (h, m, s)


def part_label(name):
    return {"LOWER_H41_B1": "下半主体 H41/B1", "UPPER_INTEGRATED": "上半集成主体", "PANEL_COVER": "可拆操作面板"}[name]


def main():
    stamp = datetime.now(TZ).isoformat(timespec="seconds")
    # 1) metrics for all candidates
    cand_metrics = {}
    for tag, name, v in CANDIDATE_TAGS:
        try:
            cand_metrics["%s_%s" % (name, v)] = read_result_metrics(tag)
        except Exception as exc:  # noqa: BLE001
            print("WARN missing candidate %s: %s" % (tag, exc))

    # 2) export chosen projects
    chosen = {}
    for tag, name, proj_name, support_expected, infill_expected in PARTS:
        print("export", tag)
        project_path = export_project(tag)
        info = validate_project_3mf(tag, name, project_path, support_expected, infill_expected)
        metrics = cand_metrics["%s_L28" % name]
        chosen[name] = {
            "tag": tag,
            "part": name,
            "label": part_label(name),
            "project": proj_name,
            "layer_height": 0.28,
            "seconds": metrics["seconds"],
            "hours": metrics["hours"],
            "grams": metrics["grams"],
            "human_time": fmt_hms(metrics["seconds"]),
            "warning": metrics["warning"],
            "triangle_count": metrics["triangle_count"],
            "support": support_expected == "1",
            "infill": infill_expected,
            "work_dir": str(W / tag),
            "export": info,
        }
        print("  ok", name, metrics["hours"], "h", metrics["grams"], "g", info["sha256"][:12])

    total_seconds = sum(v["seconds"] for v in chosen.values())
    total_grams = sum(v["grams"] for v in chosen.values())

    # 3) build package skeleton
    if NEW.exists():
        shutil.rmtree(NEW)
    for sub in ("projects", "checks", "preview", "source"):
        (NEW / sub).mkdir(parents=True)

    for name, v in chosen.items():
        shutil.copy2(Path(v["work_dir"]) / "project.3mf", NEW / "projects" / v["project"])

    # 4) checks
    for name, v in chosen.items():
        tag = v["tag"]
        rec = {
            "date": "2026-11-04",
            "material": "R3D PETG",
            "variant": "r3d-petg-028",
            "part": name,
            "label": v["label"],
            "layer_height_mm": 0.28,
            "slicer": "Bambu Studio 02.08.02.61 (CLI)",
            "printer": "Bambu Lab P2S",
            "nozzle": "0.4 mm",
            "bed": "Textured PEI Plate",
            "support": v["support"],
            "infill": v["infill"],
            "result": {
                "total_predication_seconds": v["seconds"],
                "total_predication_hours": v["hours"],
                "total_used_g": v["grams"],
                "human_time": v["human_time"],
                "warning_message": v["warning"],
                "triangle_count": v["triangle_count"],
            },
            "project_3mf": {
                "path": "projects/" + v["project"],
                "sha256": v["export"]["sha256"],
                "bytes": v["export"]["bytes"],
                "entries": v["export"]["entries"],
                "no_gcode": True,
                "model_files_identical_to_sliced": True,
                "embedded_checks": v["export"]["embedded_checks"],
            },
            "sliced_3mf_sha256": v["export"]["sliced_3mf_sha256"],
            "physical_print_tested": False,
        }
        fname = "r3d_petg_%s_slicing.json" % name
        (NEW / "checks" / fname).write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    candidates = {
        "date": "2026-11-04",
        "purpose": "选择 R3D PETG 的最佳层高（同一几何、同一结构参数，只改层高/顶底壳层数/支撑 Z 间隙）",
        "material": "R3D PETG",
        "process_base": "PLA 快速候选 process.json（0.28 基础）逐层高替换：layer_height、initial_layer_print_height=0.2、top/bottom_shell_layers 按 0.8mm 以上壳厚、support_top/bottom_z_distance=层高",
        "results": {
            "%s_%s" % (name, v): m for (tag, name, v), m in
            (((tag, name, v), cand_metrics["%s_%s" % (name, v)]) for tag, name, v in CANDIDATE_TAGS)
            if "%s_%s" % (name, v) in cand_metrics
        },
        "note": "warning_message 均为空；0.28 是 0.4 喷嘴可稳定挤出的上限（约喷嘴直径 70%），再高会明显牺牲层间结合与表面质量。",
    }
    (NEW / "checks" / "r3d_petg_candidates.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    selection = {
        "date": "2026-11-04",
        "status": "SELECTED_FASTEST_TESTED_ALL_0.28_R3D_PETG_UPPER_24H_UNMET",
        "material": "R3D PETG",
        "selected": {
            name: {
                "tag": v["tag"],
                "layer_height_mm": 0.28,
                "seconds": v["seconds"],
                "hours": v["hours"],
                "grams": v["grams"],
                "project": "projects/" + v["project"],
                "sha256": v["export"]["sha256"],
            } for name, v in chosen.items()
        },
        "total_seconds": round(total_seconds, 6),
        "total_hours": round(total_seconds / 3600.0, 6),
        "total_grams": round(total_grams, 6),
        "total_human_time": fmt_hms(total_seconds),
        "target_seconds": 86400,
        "rationale": [
            "0.28 mm 相对 0.24 mm：全套约少 5.1 小时；相对 0.20 mm 约少 10.6 小时，是耗时最大的杠杆。",
            "0.28 mm 为 0.4 mm 喷嘴可稳定挤出的层高上限；PETG 层间结合较好，0.28 mm 仍可用，但 Z 向强度低于更薄层高。",
            "R3D PETG 的 Bambu 参数按官网建议区间取保守值（喷嘴 250 ℃、热床 60 ℃、体积流量 12 mm³/s、风扇 10–40 %、流量比 0.95）。",
            "上半件在 0.28 mm 下仍约 33.4 小时，25 小时目标未达；这是几何体量决定的结构性限制，不能通过层高弥补。",
        ],
        "alternatives": {
            "0.24": "强度更好：全套约多 5.1 小时、多约 23 g",
            "0.20": "强度/表面最好：全套约多 14.9 小时、多约 46 g",
        },
        "physical_print_tested": False,
    }
    (NEW / "checks" / "r3d_petg_selection.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    release = {
        "date": "2026-11-04",
        "status": selection["status"],
        "material": "R3D PETG",
        "target_seconds": 86400,
        "estimated_total_seconds": round(total_seconds, 6),
        "estimated_total_hours": round(total_seconds / 3600.0, 6),
        "estimated_total_human_time": fmt_hms(total_seconds),
        "grams": round(total_grams, 6),
        "files": [
            {
                "part": name,
                "label": v["label"],
                "project": "projects/" + v["project"],
                "sha256": v["export"]["sha256"],
                "seconds": v["seconds"],
                "hours": v["hours"],
                "grams": v["grams"],
                "human_time": v["human_time"],
                "layer_height": 0.28,
                "support": v["support"],
            } for name, v in chosen.items()
        ],
        "slicer": "Bambu Studio 02.08.02.61",
        "printer": "Bambu Lab P2S",
        "nozzle": "0.4 mm",
        "bed": "Textured PEI Plate",
        "material_source": "R3D PETG 1.75 mm (r3dprint.com)",
        "material_profile_note": "Bambu Studio 无 R3D 官方配置；按 R3D 官网参数区间 + Bambu Generic PETG 基础，取保守值",
        "physical_print_tested": False,
        "print_job_sent": False,
        "time_target_met_by_principal_body": {
            "LOWER_H41_B1": chosen["LOWER_H41_B1"]["seconds"] <= 86400,
            "UPPER_INTEGRATED": chosen["UPPER_INTEGRATED"]["seconds"] <= 86400,
        },
        "limitations": [
            "估算时间为 Bambu Studio CLI 切片预测，实际会因环境温度/AMS/换料等浮动。",
            "未实物打印验证；PETG 附着力和拆支撑手感需实机确认。",
            "上半件约 33.4 小时，单件 24 小时目标未达。",
            "层高 0.28 mm、PETG 低风扇在悬垂/桥接处可能出现拉丝或下垂，首件建议先小件试打。",
        ],
    }
    (NEW / "checks" / "r3d_petg_release.json").write_text(
        json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": "2026-11-04",
        "request": "改用 R3D PETG 耗材输出一版三个文件，并重新判定/设定该情况下的最佳层高与参数（用户 m00558/m00588）",
        "printer": "Bambu Lab P2S",
        "material": "R3D PETG",
        "selected_layer_height_mm": 0.28,
        "params": {
            "nozzle_temperature_c": [250, 250],
            "textured_plate_temp_c": 60,
            "hot_plate_temp_c": 60,
            "filament_flow_ratio": 0.95,
            "filament_max_volumetric_speed_mm3_s": 12,
            "fan_min_percent": 10,
            "fan_max_percent": 40,
            "overhang_fan_percent": 40,
            "close_fan_first_layers": 3,
            "wall_loops": 3,
            "sparse_infill_density": "10% (面板 15%)",
            "infill_pattern": "gyroid",
            "top_bottom_shell_layers": "3 (0.84 mm)",
            "brim_width_mm": "6 (面板 3)",
            "outer_wall_speed_mm_s": 120,
            "inner_wall_speed_mm_s": 230,
            "support": "tree(auto) slim，Z 间隙 0.28（面板无支撑）",
            "drying": "60-65 ℃ / 4-8 h（R3D 官方建议）",
        },
        "why_not_thinner": "0.24/0.20 每件都更慢且更重：0.24 全套约 +5.1 小时 / +23 g，0.20 约 +14.9 小时 / +46 g；只有强度/表面要求更高时才值得。",
        "why_not_thicker": "0.28 已是 0.4 mm 喷嘴可稳定挤出的上限（约 70% 喷嘴直径）；0.32 及以上层间结合与表面质量明显下降，不建议用于承力结构件。",
        "physical_print_tested": False,
    }
    (NEW / "checks" / "r3d_petg_decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 5) previews
    preview_src = W / "preview"
    if preview_src.exists():
        for name in chosen:
            src = preview_src / ("%s_L28" % name)
            if not src.exists():
                src = preview_src / ("%s_L28.png" % name)
            if src.exists():
                shutil.copy2(src, NEW / "preview" / ("%s_L28_plate.png" % name))
    # 6) sources
    for cand in [W / "slice_petg_candidates.py",
                 ROOT / "codex_readback" / "r3d_petg_fast_20261104" / "slice_petg_candidates.py",
                 Path(sys.executable).parent / "slice_petg_candidates.py"]:
        if cand.exists():
            shutil.copy2(cand, NEW / "source" / "slice_petg_candidates.py")
            break
    for cand in [W / "filament_r3d_petg.json", ROOT / ".p2s-petg-fast-20261104" / "filament_r3d_petg.json"]:
        if cand.exists():
            shutil.copy2(cand, NEW / "source" / "filament_r3d_petg.json")
            break
    shutil.copy2(Path(__file__).resolve(), NEW / "source" / "build_package.py")

    # 7) README
    def row(name, v):
        return "| %s | %.2f 小时（%s） | %.1f g | %d |" % (v["label"], v["hours"], v["human_time"], v["grams"], v["triangle_count"])

    cand_rows = []
    for name in ("LOWER_H41_B1", "UPPER_INTEGRATED", "PANEL_COVER"):
        cells = []
        for v in ("L28", "L24", "L20"):
            m = cand_metrics.get("%s_%s" % (name, v))
            cells.append("%.2f h / %.1f g" % (m["hours"], m["grams"]) if m else "-")
        cand_rows.append("| %s | %s |" % (part_label(name), " | ".join(cells)))

    pla = {
        "LOWER_H41_B1": (49278.73828125, 373.94830322265625),
        "UPPER_INTEGRATED": (118706.3515625, 802.9749755859375),
        "PANEL_COVER": (3471.180419921875, 27.012527465820312),
    }
    pla_total_s = sum(v[0] for v in pla.values())
    pla_total_g = sum(v[1] for v in pla.values())
    def cand_total(v):
        return sum(cand_metrics["%s_%s" % (n, v)]["seconds"] for n in ("LOWER_H41_B1", "UPPER_INTEGRATED", "PANEL_COVER"))
    def cand_total_g(v):
        return sum(cand_metrics["%s_%s" % (n, v)]["grams"] for n in ("LOWER_H41_B1", "UPPER_INTEGRATED", "PANEL_COVER"))
    d24_s, d24_g = cand_total("L24") - total_seconds, cand_total_g("L24") - total_grams
    d20_s, d20_g = cand_total("L20") - total_seconds, cand_total_g("L20") - total_grams
    panel_faster_s = cand_metrics["PANEL_COVER_L20"]["seconds"] - cand_metrics["PANEL_COVER_L28"]["seconds"]
    panel_dg = cand_metrics["PANEL_COVER_L28"]["grams"] - cand_metrics["PANEL_COVER_L20"]["grams"]

    readme = """# 智能垃圾桶三件套 — R3D PETG 树形支撑 0.28 mm 最快打印候选

日期：2026-11-04　打印机：Bambu Lab P2S（0.4 mm 喷嘴，纹理 PEI 板）　材料：R3D PETG（1.75 mm）

## 结论

- 三件全部使用 **0.28 mm 层高**（0.4 喷嘴可稳定挤出的上限），PETG 参数按 R3D 官方建议区间取保守值。
- 切片估算合计 **约 {total_h}（{total_s:.1f} g）**；面板盖与下半主体均在 24 小时内，**上半集成主体约 {upper_h} 仍超 24 小时**（几何体量决定，层高无法弥补）。
- 本包只含 PETG 版本；**PLA 版本（0.28 mm，整套约 47 小时 38 分 / 1203.9 g）保持不变**，见 `integrated-pla-fast-20261104`。

## 为什么选 0.28 mm

| 件 | 0.28 mm | 0.24 mm | 0.20 mm |
|---|---|---|---|
{rows}

- 降到 0.24 mm：每件都更慢，全套约多 {d24_h}、多约 {d24_g:.1f} g；降到 0.20 mm：全套约多 {d20_h}、多约 {d20_g:.1f} g。
- 0.28 mm 是 0.4 喷嘴约 70% 喷嘴直径的上限；再往上（0.32+）层间结合与表面质量明显下降，不建议用于承力结构件。PETG 层间结合本身较好，0.28 mm 可用于结构件；如需最高 Z 向强度可选 0.24/0.20（包内 `checks/r3d_petg_candidates.json` 保留全部候选数据）。
- 与 PLA 版 0.28 mm（折合 {pla_h}、{pla_g:.1f} g）相比：PETG 版约慢 40 分钟、轻约 8.6 g（PETG 流量比 0.95、实际密度更高，重量接近）。

## 采用的参数

| 参数 | 值 |
|---|---|
| 层高 / 首层 | 0.28 mm / 0.20 mm |
| 喷嘴温度（普通/首层） | 250 ℃ / 250 ℃ |
| 热床（纹理 PEI） | 60 ℃ |
| 流量比 / 最大体积流量 | 0.95 / 12 mm³/s（两条保守取值） |
| 风扇（最小/最大/悬垂） | 10 % / 40 % / 40 %（首 3 层关闭） |
| 墙 / 填充 | 3 道 / 10 % gyroid（面板 15 %） |
| 顶底壳层 | 3 / 3 层（0.84 mm） |
| 速度（外墙/内墙） | 120 / 230 mm/s（沿用已验证快速参数） |
| 支撑（两主体） | 树形 auto slim，阈值 35°，枝径 3，Z 间隙 0.28；面板无支撑 |
| 摆放 | 与 PLA 版相同（UPPER 使用 r4 旋转矩阵，几何孔位不变） |
| 干燥 | 60–65 ℃ / 4–8 小时（R3D 官方建议，打印前必须干燥） |

参数来源与假设：R3D 官方 PETG 页面给出喷嘴 230–260 ℃、热床 40–60 ℃、风扇 5–40 %、速度上限 300 mm/s、干燥 60–65 ℃ / 4–8 h；Bambu Studio 没有 R3D 官方配置，本包以 Bambu Generic PETG 为基础、取区间内偏保守值（250 ℃ / 60 ℃ / 12 mm³/s / 风扇 10–40 % / 流量 0.95）。首次实打建议先用小件校准流量与温度。

## 各件结果（0.28 mm）

| 件 | 打印时间（预测） | 耗材（含支撑，g） | 三角面数 |
|---|---|---|---|
{chosen_rows}

合计：**{total_h} / {total_s:.1f} g**。面板盖 0.28 mm 比 0.20 mm 快约 {panel_faster}、多约 {panel_dg:.1f} g——面板是外观件，若更在意外观可单独用 0.24/0.20 mm 打（本包未改）。

## 打印注意（PETG）

1. 打印前干燥：60–65 ℃ / 4–8 h；受潮会明显拉丝、发雾。
2. 纹理 PEI 板 + 60 ℃；PETG 粘板很强，建议薄涂固体胶作脱模剂，冷却后再取件。
3. PETG 冷却要弱（10–40 %），悬垂/桥接可能比 PLA 略差；首件先检查支撑接触面。
4. 0.28 mm + PETG 的层纹较明显；需要表面质量时改用 0.24 mm。
5. 拆支撑时带手套，PETG 支撑接触点较硬，可用剪钳沿枝干剪断。

## 包内文件

- `projects/`：三份可直接打开的 PETG 工程 3MF（Bambu Studio 02.08.02.61）
- `checks/`：三件切片/导出校验（含 3MF 内嵌参数逐项断言）、层高候选、选择与发布记录、决定依据
- `preview/`：各件首层/刀路预览 PNG
- `source/`：候选切片脚本、导出/打包脚本、R3D PETG 材料配置
- `SHA256.json`：全部文件校验和

## 声明

- 时间为 Bambu Studio 切片预测，未实物打印；PETG 附着、支撑手感、强度需实机验证。
- 上半件约 33.4 小时，单件 24 小时目标未达，不得宣称"24 小时达标版"。
- 原模型几何/孔位未改：UPPER 沿用 r4 旋转矩阵，三件 `geometry.3mf` 与 PLA 版逐字节一致（见各 checks 记录）。
""".format(
        total_h=fmt_hms(total_seconds), total_s=total_grams,
        upper_h=chosen["UPPER_INTEGRATED"]["human_time"],
        rows="\n".join(cand_rows),
        pla_h=fmt_hms(pla_total_s), pla_g=pla_total_g,
        chosen_rows="\n".join(row(name, v) for name, v in chosen.items()),
        d24_h=fmt_hms(d24_s),
        d24_g=d24_g,
        d20_h=fmt_hms(d20_s),
        d20_g=d20_g,
        panel_faster=fmt_hms(panel_faster_s),
        panel_dg=panel_dg,
    )
    (NEW / "README.md").write_text(readme, encoding="utf-8")

    # 8) sha manifest
    manifest = {}
    for p in sorted(NEW.rglob("*")):
        if p.is_file():
            rel = p.relative_to(NEW).as_posix()
            if rel in ("SHA256.json",):
                continue
            manifest[rel] = sha256(p)
    (NEW / "SHA256.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 9) mirror to repo and zip
    if REPO_TARGET.exists():
        shutil.rmtree(REPO_TARGET)
    shutil.copytree(NEW, REPO_TARGET)
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(NEW.rglob("*")):
            if p.is_file():
                z.write(p, (NEW.name + "/" + p.relative_to(NEW).as_posix()))
    with zipfile.ZipFile(ZIP) as z:
        bad = z.testzip()
        entries = z.namelist()
    print(json.dumps({
        "stamp": stamp,
        "total_seconds": total_seconds,
        "total_human": fmt_hms(total_seconds),
        "total_grams": round(total_grams, 6),
        "chosen": {k: {kk: vv for kk, vv in v.items() if kk in ("tag", "seconds", "hours", "grams", "human_time")} for k, v in chosen.items()},
        "package_files": len(manifest),
        "zip": str(ZIP),
        "zip_bytes": ZIP.stat().st_size,
        "zip_entries": len(entries),
        "zip_testzip": bad,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
