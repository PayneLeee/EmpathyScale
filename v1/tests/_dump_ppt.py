"""Dump all text from the project PPTX using only the stdlib (no pptx dependency)."""
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(r"D:/Users/zhangy/Downloads/EmpathyScale-main")
PPT = ROOT / "汇报PPT.pptx"
out_path = ROOT / "EmpathyScale-main" / "tests" / "_ppt_dump.txt"

ns = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

with zipfile.ZipFile(str(PPT)) as z:
    names = sorted(z.namelist())
    slide_names = [n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)]
    slide_names.sort(key=lambda n: int(re.search(r"(\d+)", n).group(1)))
    out = []
    for sn in slide_names:
        num = re.search(r"(\d+)", sn).group(1)
        xml = z.read(sn)
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            out.append(f"\n===== SLIDE {num} (parse error) =====")
            continue
        texts = []
        for t in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t"):
            if t.text:
                texts.append(t.text)
        # also capture table cells via <a:t>
        out.append(f"\n===== SLIDE {num} =====")
        if texts:
            out.append("\n".join(texts))
        else:
            out.append("(no extractable text)")
    Path(out_path).write_text("\n".join(out), encoding="utf-8")
    print("WROTE", out_path, "slides=", len(slide_names))
