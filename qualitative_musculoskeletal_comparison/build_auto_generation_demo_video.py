"""Render a 16:9 MP4 replay with readable staged scrolling."""
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from build_auto_generation_demo import build_demo_data

PKG_ROOT = Path(__file__).resolve().parent
FONT_DIR = Path("C:/Windows/Fonts")

BG = "#f5f7fb"
CARD = "#ffffff"
TEXT = "#1f2937"
MUTED = "#6b7280"
BLUE = "#0084ff"
GREEN = "#22a35a"
ORANGE = "#f59e0b"
BORDER = "#e5e9f0"
SOFT_BLUE = "#f0f6ff"
SOFT_GREEN = "#f0fdf4"
USER_BLUE = "#0084ff"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        FONT_DIR / ("msyhbd.ttc" if bold else "msyh.ttc"),
        FONT_DIR / ("simhei.ttf" if bold else "simkai.ttf"),
        FONT_DIR / ("arialbd.ttf" if bold else "arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F_TITLE = font(24, True)
F_STAGE = font(22, True)
F_H2 = font(18, True)
F_H3 = font(16, True)
F_BODY = font(15)
F_SMALL = font(13)
F_TINY = font(11)
F_METRIC = font(22, True)


def fit_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> str:
    text = str(text)
    if text_width(draw, text, fnt) <= max_width:
        return text
    out = ""
    for ch in text:
        if text_width(draw, out + ch + "...", fnt) > max_width:
            return out + "..."
        out += ch
    return out


def rounded(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    fill: str,
    outline: str = BORDER,
    radius: int = 14,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(text, font=fnt)


def wrap_text(draw: ImageDraw.ImageDraw, text: Any, fnt: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    lines: List[str] = []
    text = str(text).replace("\r", "").strip()
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            lines.append("")
            continue
        current = ""
        for ch in para:
            trial = current + ch
            if text_width(draw, trial, fnt) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: Any,
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_gap: int = 4,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, fnt, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip("，。；,. ") + "..."
    line_h = int(fnt.size * 1.3)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h + line_gap
    return y


def paragraph_height(draw: ImageDraw.ImageDraw, text: Any, fnt: ImageFont.FreeTypeFont, max_width: int, line_gap: int = 4) -> int:
    return len(wrap_text(draw, text, fnt, max_width)) * (int(fnt.size * 1.3) + line_gap)


def text_units(value: Any) -> int:
    if isinstance(value, dict):
        return sum(text_units(v) for v in value.values())
    if isinstance(value, list):
        return sum(text_units(v) for v in value)
    return len(str(value))


def distribute(weights: List[float], total: float, bounds: List[Tuple[float, float]]) -> List[float]:
    total_weight = sum(weights) or 1
    values = [total * w / total_weight for w in weights]
    fixed = [False] * len(values)
    for _ in range(8):
        changed = False
        for i, value in enumerate(values):
            low, high = bounds[i]
            if value < low:
                values[i] = low
                fixed[i] = True
                changed = True
            elif value > high:
                values[i] = high
                fixed[i] = True
                changed = True
        remaining = total - sum(v for v, f in zip(values, fixed) if f)
        free = [i for i, f in enumerate(fixed) if not f]
        if not changed or not free:
            break
        free_weight = sum(weights[i] for i in free) or 1
        for i in free:
            values[i] = remaining * weights[i] / free_weight
    drift = total - sum(values)
    if values:
        values[-1] += drift
    return values


def build_timeline(data: Dict[str, Any], duration: int) -> Dict[str, Any]:
    chat_weight = text_units(data["conversation"])
    pipeline_weights = [
        text_units(step) + text_units(step_detail_lines(data, i)) * 0.9
        for i, step in enumerate(data["pipeline_steps"])
    ]
    pipeline_weight = sum(pipeline_weights) * 0.85
    result_weight = (text_units(data["scale_sections"]) + text_units(data["metrics"]) * 1.4) * 1.7
    chat_dur, pipeline_dur, result_dur = distribute(
        [chat_weight, pipeline_weight, result_weight],
        float(duration),
        [(22, 30), (30, 36), (22, 28)],
    )
    step_durs = distribute(pipeline_weights, pipeline_dur, [(2.4, 5.8)] * len(pipeline_weights))
    step_starts: List[float] = []
    cursor = chat_dur
    for dur in step_durs:
        step_starts.append(cursor)
        cursor += dur
    return {
        "duration": float(duration),
        "chat": chat_dur,
        "pipeline": pipeline_dur,
        "result": result_dur,
        "pipeline_start": chat_dur,
        "result_start": chat_dur + pipeline_dur,
        "step_durations": step_durs,
        "step_starts": step_starts,
    }


def phase_at(t: float, timeline: Dict[str, Any]) -> Tuple[str, float, float]:
    if t < timeline["pipeline_start"]:
        return "访谈对话回放", t / timeline["chat"], timeline["chat"]
    if t < timeline["result_start"]:
        elapsed = t - timeline["pipeline_start"]
        return "九步骤自动生成", elapsed / timeline["pipeline"], timeline["pipeline"]
    elapsed = t - timeline["result_start"]
    return "最终量表结果", elapsed / timeline["result"], timeline["result"]


def draw_header(draw: ImageDraw.ImageDraw, data: Dict[str, Any], t: float, width: int, timeline: Dict[str, Any]) -> None:
    phase, _, _ = phase_at(t, timeline)
    draw.rectangle((0, 0, width, 72), fill="#ffffff")
    draw.line((0, 72, width, 72), fill=BORDER, width=2)
    draw.text((32, 14), "EmpathyScale 生成过程回放", font=F_TITLE, fill=TEXT)
    draw.text((32, 45), f"16:9 视频 · {phase} · 运行编号 {data['run_id']}", font=F_SMALL, fill=MUTED)
    pill_w = 165
    rounded(draw, (width - pill_w - 32, 18, width - 32, 52), SOFT_BLUE, "#dbeafe", radius=17)
    draw.text((width - pill_w - 12, 27), "80s 分段滚动版", font=F_SMALL, fill=BLUE)
    progress = min(1.0, t / timeline["duration"])
    draw.rectangle((0, 72, width, 78), fill="#e9eef6")
    draw.rectangle((0, 72, int(width * progress), 78), fill=BLUE)


def chat_layout(draw: ImageDraw.ImageDraw, messages: List[Dict[str, Any]], panel_w: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    y = 0
    for msg in messages:
        bubble_w = 760 if msg["type"] == "agent" else 720
        lines = wrap_text(draw, msg["content"], F_BODY, bubble_w - 34)
        height = 28 + len(lines) * 24
        rows.append({"msg": msg, "lines": lines, "width": bubble_w, "height": height, "y": y})
        y += height + 18
    return rows


def draw_chat_scene(
    draw: ImageDraw.ImageDraw,
    data: Dict[str, Any],
    t: float,
    width: int,
    height: int,
    timeline: Dict[str, Any],
) -> None:
    panel = (36, 102, width - 36, height - 32)
    x1, y1, x2, y2 = panel
    rounded(draw, panel, CARD, BORDER, radius=18)
    draw.text((x1 + 28, y1 + 20), "1 · 访谈对话：从场景细节到可测量输入", font=F_STAGE, fill=TEXT)
    draw.text((x1 + 28, y1 + 51), "真实访谈对话回放，滚动展示用户与访谈智能体如何收集场景约束。", font=F_SMALL, fill=MUTED)

    viewport = (x1 + 28, y1 + 88, x2 - 28, y2 - 76)
    vx1, vy1, vx2, vy2 = viewport
    draw.rectangle(viewport, fill="#f8fafc", outline=BORDER)
    rows = chat_layout(draw, data["conversation"], vx2 - vx1)
    total_h = rows[-1]["y"] + rows[-1]["height"] if rows else 0
    max_scroll = max(0, total_h - (vy2 - vy1) + 16)
    scroll = max_scroll * min(1.0, max(0.0, t / timeline["chat"]))

    for row in rows:
        msg = row["msg"]
        by = vy1 + 18 + int(row["y"] - scroll)
        bh = row["height"]
        if by < vy1 + 8 or by + bh > vy2 - 8:
            continue
        is_user = msg["type"] == "user"
        bw = row["width"]
        bx = vx2 - bw - 22 if is_user else vx1 + 22
        fill = USER_BLUE if is_user else "#ffffff"
        outline = USER_BLUE if is_user else BORDER
        rounded(draw, (bx, by, bx + bw, by + bh), fill, outline, radius=16)
        label = "用户" if is_user else "访谈智能体"
        draw.text((bx + 16, by + 8), label, font=F_TINY, fill="#dbeafe" if is_user else BLUE)
        ty = by + 27
        for line in row["lines"]:
            draw.text((bx + 16, ty), line, font=F_BODY, fill="#ffffff" if is_user else TEXT)
            ty += 24

    # Input area.
    input_y = y2 - 58
    draw.line((x1, input_y - 12, x2, input_y - 12), fill=BORDER, width=1)
    rounded(draw, (x1 + 28, input_y, x2 - 130, input_y + 38), "#ffffff", "#d8dee8", radius=9)
    draw.text((x1 + 44, input_y + 11), "对话完成后进入自动处理阶段...", font=F_SMALL, fill=MUTED)
    rounded(draw, (x2 - 112, input_y, x2 - 28, input_y + 38), "#eef2f7", "#eef2f7", radius=9)
    draw.text((x2 - 85, input_y + 10), "发送", font=F_SMALL, fill="#334155")


def step_status(index: int, t: float, timeline: Dict[str, Any]) -> str:
    start = timeline["step_starts"][index]
    done = start + timeline["step_durations"][index] * 0.72
    if t >= done:
        return "done"
    if t >= start:
        return "running"
    return "pending"


def step_detail_lines(data: Dict[str, Any], index: int) -> List[Tuple[str, str]]:
    step = data["pipeline_steps"][index]
    if index == 0:
        return [(label, value) for label, value in data["summary_rows"]]
    if index == 1:
        return [("文献", title) for title in data["paper_titles"][:7]]
    if index in (2, 3):
        return [("候选题项", item) for item in data["initial_items"][:7]]
    if index in (4, 5):
        return [("事件", line) for line in data["feed_lines"][6:11]]
    if index == 6:
        return [("统计筛选", step["result"])] + [("保留题项", item) for sec in data["scale_sections"] for item in sec["items"][:2]]
    if index == 7:
        return data["metrics"] + [("验证说明", step["result"])]
    return [("最终输出", step["result"])] + [("量表维度", sec["dimension"]) for sec in data["scale_sections"]]


def draw_pipeline_scene(
    draw: ImageDraw.ImageDraw,
    data: Dict[str, Any],
    t: float,
    width: int,
    height: int,
    timeline: Dict[str, Any],
) -> None:
    _, local_t, _ = phase_at(t, timeline)
    x1, y1, x2, y2 = (36, 102, width - 36, height - 32)
    rounded(draw, (x1, y1, x2, y2), CARD, BORDER, radius=18)
    draw.text((x1 + 28, y1 + 20), "2 · 九步骤自动处理：逐步生成与验证量表", font=F_STAGE, fill=TEXT)
    draw.text((x1 + 28, y1 + 51), "每个步骤按展示文字量分配时间，右侧展示该步骤的输入、产物或中间结果。", font=F_SMALL, fill=MUTED)

    list_x, list_y, list_w = x1 + 28, y1 + 88, 390
    detail_x, detail_y = list_x + list_w + 26, list_y
    detail_w, detail_h = x2 - detail_x - 28, y2 - detail_y - 22
    current = 0
    for i, start in enumerate(timeline["step_starts"]):
        if t >= start:
            current = i

    for i, step in enumerate(data["pipeline_steps"]):
        sy = list_y + i * 55
        status = step_status(i, t, timeline)
        fill = "#f7fbff" if i == current else "#ffffff"
        border = BLUE if status == "running" else (GREEN if status == "done" else "#cbd5e1")
        rounded(draw, (list_x, sy, list_x + list_w, sy + 45), fill, BORDER, radius=10)
        draw.rectangle((list_x, sy, list_x + 6, sy + 45), fill=border)
        icon = "✓" if status == "done" else ("⟳" if status == "running" else "○")
        draw.text((list_x + 18, sy + 12), icon, font=F_SMALL, fill=border)
        title = fit_text(draw, f"{i + 1}. {step['title']}", F_SMALL, list_w - 58)
        draw.text((list_x + 45, sy + 7), title, font=F_SMALL, fill=TEXT)
        draw.text((list_x + 45, sy + 27), "完成" if status == "done" else ("生成中..." if status == "running" else "等待中"), font=F_TINY, fill=MUTED)

    step = data["pipeline_steps"][current]
    rounded(draw, (detail_x, detail_y, detail_x + detail_w, detail_y + detail_h), SOFT_BLUE, "#dbeafe", radius=16)
    draw.text((detail_x + 22, detail_y + 20), f"当前步骤 {current + 1}: {step['title']}", font=F_H2, fill=TEXT)
    y = draw_wrapped(draw, (detail_x + 22, detail_y + 52), step["detail"], F_BODY, "#374151", detail_w - 44, max_lines=2)
    rounded(draw, (detail_x + 22, y + 8, detail_x + detail_w - 22, y + 58), "#ffffff", BORDER, radius=12)
    draw.text((detail_x + 40, y + 22), "结果", font=F_SMALL, fill=BLUE)
    draw_wrapped(draw, (detail_x + 88, y + 20), step["result"], F_SMALL, TEXT, detail_w - 130, max_lines=2)

    content_y = y + 78
    draw.text((detail_x + 22, content_y), "生成细节", font=F_H3, fill=TEXT)
    content_y += 28
    for label, value in step_detail_lines(data, current)[:8]:
        row_h = 42 + min(42, paragraph_height(draw, value, F_SMALL, detail_w - 170))
        rounded(draw, (detail_x + 22, content_y, detail_x + detail_w - 22, content_y + row_h), "#ffffff", BORDER, radius=10)
        draw.text((detail_x + 40, content_y + 12), fit_text(draw, label, F_TINY, 68), font=F_TINY, fill=MUTED)
        draw_wrapped(draw, (detail_x + 118, content_y + 10), value, F_SMALL, TEXT, detail_w - 165, max_lines=2)
        content_y += row_h + 8
        if content_y > detail_y + detail_h - 50:
            break


def result_rows(draw: ImageDraw.ImageDraw, data: Dict[str, Any], max_width: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    y = 0
    for section in data["scale_sections"]:
        rows.append({"kind": "section", "text": section["dimension"], "y": y, "height": 42})
        y += 48
        for i, item in enumerate(section["items"], 1):
            h = 24 + paragraph_height(draw, item, F_BODY, max_width - 120)
            rows.append({"kind": "item", "idx": i, "text": item, "y": y, "height": h})
            y += h + 10
    return rows


def draw_result_scene(
    draw: ImageDraw.ImageDraw,
    data: Dict[str, Any],
    t: float,
    width: int,
    height: int,
    timeline: Dict[str, Any],
) -> None:
    _, local_t, _ = phase_at(t, timeline)
    x1, y1, x2, y2 = (36, 102, width - 36, height - 32)
    rounded(draw, (x1, y1, x2, y2), CARD, BORDER, radius=18)
    draw.text((x1 + 28, y1 + 20), "3 · 最终结果：10 条场景化共情量表", font=F_STAGE, fill=TEXT)
    draw.text((x1 + 28, y1 + 51), "滚动展示最终筛选后量表，保留每个维度和题项细节。", font=F_SMALL, fill=MUTED)

    mx = x1 + 28
    metric_w = 300
    metric_gap = 18
    for label, value in data["metrics"]:
        rounded(draw, (mx, y1 + 88, mx + metric_w, y1 + 146), SOFT_GREEN, "#cfe8d7", radius=12)
        draw.text((mx + 16, y1 + 99), label, font=F_TINY, fill="#4b6354")
        draw.text((mx + 16, y1 + 118), fit_text(draw, value, F_METRIC, metric_w - 32), font=F_METRIC, fill="#176534")
        mx += metric_w + metric_gap

    viewport = (x1 + 28, y1 + 166, x2 - 28, y2 - 24)
    vx1, vy1, vx2, vy2 = viewport
    draw.rectangle(viewport, fill="#f8fafc", outline=BORDER)
    rows = result_rows(draw, data, vx2 - vx1 - 48)
    total_h = rows[-1]["y"] + rows[-1]["height"] if rows else 0
    max_scroll = max(0, total_h - (vy2 - vy1) + 72)
    scroll = max_scroll * min(1.0, max(0.0, local_t))

    for row in rows:
        ry = vy1 + 18 + int(row["y"] - scroll)
        if ry < vy1 + 8 or ry + row["height"] > vy2 - 8:
            continue
        if row["kind"] == "section":
            rounded(draw, (vx1 + 18, ry, vx2 - 18, ry + 38), SOFT_BLUE, "#dbeafe", radius=10)
            draw.text((vx1 + 34, ry + 9), row["text"], font=F_H3, fill=BLUE)
        else:
            rounded(draw, (vx1 + 18, ry, vx2 - 18, ry + row["height"]), "#ffffff", BORDER, radius=10)
            draw.text((vx1 + 36, ry + 13), f"题项 {row['idx']}", font=F_SMALL, fill=MUTED)
            draw_wrapped(draw, (vx1 + 112, ry + 10), row["text"], F_BODY, TEXT, vx2 - vx1 - 160)


def render_frame(data: Dict[str, Any], t: float, width: int, height: int, timeline: Dict[str, Any] | None = None) -> Image.Image:
    if timeline is None:
        timeline = build_timeline(data, 80)
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw, data, t, width, timeline)
    if t < timeline["pipeline_start"]:
        draw_chat_scene(draw, data, t, width, height, timeline)
    elif t < timeline["result_start"]:
        draw_pipeline_scene(draw, data, t, width, height, timeline)
    else:
        draw_result_scene(draw, data, t, width, height, timeline)
    return img


def render_video(output: Path, width: int, height: int, duration: int, fps: int) -> None:
    data = build_demo_data()
    timeline = build_timeline(data, duration)
    print(
        "Timeline:",
        f"访谈 {timeline['chat']:.1f}s,",
        f"流水线 {timeline['pipeline']:.1f}s,",
        f"结果 {timeline['result']:.1f}s",
    )
    print("Step durations:", ", ".join(f"{d:.1f}s" for d in timeline["step_durations"]))
    n_frames = duration * fps
    output.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(
        output,
        fps=fps,
        codec="libx264",
        quality=8,
        macro_block_size=16,
        ffmpeg_log_level="error",
    ) as writer:
        for frame_idx in range(n_frames):
            t = frame_idx / fps
            frame = render_frame(data, t, width, height, timeline)
            writer.append_data(np.asarray(frame))
            if frame_idx % max(1, fps * 5) == 0:
                print(f"Rendered {frame_idx}/{n_frames} frames")
    print(f"Wrote {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=PKG_ROOT / "output" / "auto_generation_demo_720p_80s.mp4",
    )
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--duration", type=int, default=80)
    parser.add_argument("--fps", type=int, default=4)
    args = parser.parse_args()
    if args.width * 9 != args.height * 16:
        raise SystemExit("width/height must be 16:9")
    render_video(args.output, args.width, args.height, args.duration, args.fps)


if __name__ == "__main__":
    main()
