"""Résume l'en-tête X-Legenipng-Report lu sur l'entrée standard."""
import json
import sys

r = json.loads(sys.stdin.read())
o = r["output"]
steps = " ".join("{}={}".format(s["step"], s["ms"]) for s in r["steps"])
line = "  -> {}x{} {} {} Ko | {}".format(o["width"], o["height"], o["format"], o["bytes"] // 1024, steps)
if r["notes"]:
    line += " | notes: " + ",".join(n["code"] for n in r["notes"])
print(line, end="")
