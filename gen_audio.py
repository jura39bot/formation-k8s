#!/usr/bin/env python3
"""Narration for every lesson step (CKA), natural English female voice."""
import json, pathlib, subprocess
OUT = pathlib.Path("/root/clawd/k8s-cka/audio"); OUT.mkdir(exist_ok=True)
EDGE = "/opt/whisper-venv/bin/edge-tts"; VOICE = "en-US-AriaNeural"
data = json.loads(pathlib.Path("src/data.json").read_text(encoding="utf-8"))
jobs = []
for d in data["domains"]:
    for l in d["lessons"]:
        for i, st in enumerate(l["steps"]):
            jobs.append((f'{l["id"]}_{i}', f'{st["h"]}. {st["p"]}'))
print("clips", len(jobs), flush=True)
ok = 0
for n, (name, txt) in enumerate(jobs, 1):
    dest = OUT / f"{name}.mp3"
    if dest.exists() and dest.stat().st_size > 800:
        ok += 1; continue
    tmp = OUT / f"_{name}.tmp.mp3"
    try:
        subprocess.run([EDGE, "--voice", VOICE, "--rate=-3%", "--text", txt,
                        "--write-media", str(tmp)], check=True, capture_output=True, timeout=90)
        if tmp.stat().st_size > 800:
            tmp.replace(dest); ok += 1
        else:
            tmp.unlink(missing_ok=True)
    except Exception as e:
        tmp.unlink(missing_ok=True); print("ERR", name, e, flush=True)
    if n % 10 == 0: print(f"{n}/{len(jobs)}", flush=True)
print(f"DONE {ok}/{len(jobs)}", flush=True)
