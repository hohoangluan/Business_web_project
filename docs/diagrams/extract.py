"""Tách mọi block ```mermaid trong các file .md báo cáo -> docs/diagrams/src/<base>-NN.mmd"""
import re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = pathlib.Path(__file__).resolve().parent / "src"
SRC.mkdir(exist_ok=True)

FILES = [
    "class_diagram.md", "activity_diagrams.md", "use_cases.md",
    "data_flow_diagram.md", "code_flow.md", "deployment_architecture.md",
    "how_it_works.md", "sequence_diagrams.md", "state_diagrams.md",
]

PAT = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
total = 0
for fn in FILES:
    p = ROOT / fn
    if not p.exists():
        print("MISS", fn); continue
    text = p.read_text(encoding="utf-8")
    blocks = PAT.findall(text)
    base = fn.replace(".md", "").replace("_", "-")
    for i, b in enumerate(blocks, 1):
        out = SRC / f"{base}-{i:02d}.mmd"
        out.write_text(b.rstrip() + "\n", encoding="utf-8")
        total += 1
    print(f"{fn}: {len(blocks)} blocks")
print("TOTAL", total)
