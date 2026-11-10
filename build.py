#!/usr/bin/env python3
"""Build index.html from src/template.html + src/data.json."""
import json, pathlib, datetime

root = pathlib.Path(__file__).parent
tpl = (root / "src/template.html").read_text(encoding="utf-8")
data = json.loads((root / "src/data.json").read_text(encoding="utf-8"))
build = datetime.datetime.now().strftime("%Y%m%d.%H%M")
html = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))).replace("__BUILD__", build)
(root / "index.html").write_text(html, encoding="utf-8")
lessons = sum(len(d["lessons"]) for d in data["domains"])
steps = sum(len(l["steps"]) for d in data["domains"] for l in d["lessons"])
qs = sum(len(v) for v in data["questions"].values())
print(f"index.html {len(html)} bytes — {len(data['domains'])} domains, {lessons} lessons, {steps} steps, {qs} questions, {len(data['cheatsheets'])} sheets, {len(data['tips'])} tips — {build}")
