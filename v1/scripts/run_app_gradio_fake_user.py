#!/usr/bin/env python3
"""Drive the real app_gradio web UI with a fake interview user."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "agents", ROOT / "utils", ROOT / "web_ui", SCRIPTS_DIR):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)
os.chdir(ROOT)

from fake_interview_user import FakeInterviewUser  # noqa: E402
from interview_agent_group import load_config  # noqa: E402
from scenarios.demo_scenarios import get_demo_scenario  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.common.exceptions import TimeoutException  # noqa: E402
from selenium.webdriver import ChromeOptions  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402
from web_ui.app_gradio import create_app  # noqa: E402


def _latest_run_dir() -> Path | None:
    runs_root = ROOT / "data" / "runs"
    if not runs_root.exists():
        return None
    candidates = [p for p in runs_root.iterdir() if p.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _write_run_timing(
    run_dir: Path,
    *,
    scenario: str,
    profile: str,
    start_ts: float,
    end_ts: float,
) -> None:
    elapsed = max(0.0, end_ts - start_ts)
    payload = {
        "scenario": scenario,
        "profile": profile,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start_ts)),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(end_ts)),
        "elapsed_seconds": round(elapsed, 1),
        "elapsed_minutes": round(elapsed / 60.0, 2),
        "elapsed_human": f"{int(elapsed // 3600)}h {(int(elapsed) % 3600) // 60}m {int(elapsed) % 60}s",
    }
    (run_dir / "run_timing.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def find_free_port(start: int = 7860, end: int = 7890) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available in 7860-7890")


class ServerThread(threading.Thread):
    def __init__(self, port: int, cfg_override: dict | None = None):
        super().__init__(daemon=True)
        self.port = port
        self.app = create_app(cfg_override=cfg_override)
        self.server = make_server("127.0.0.1", port, self.app, threaded=True)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def run(self) -> None:
        self.server.serve_forever()

    def stop(self) -> None:
        self.server.shutdown()
        self.ctx.pop()


def build_driver(detach: bool, headless: bool) -> webdriver.Chrome:
    options = ChromeOptions()
    options.add_experimental_option("detach", detach)
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,1400")
    if headless:
        options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)


def last_agent_text(driver: webdriver.Chrome) -> str:
    bubbles = driver.find_elements(By.CSS_SELECTOR, ".message.agent .bubble")
    texts = [b.text.strip() for b in bubbles if b.text.strip()]
    return texts[-1] if texts else ""


def wait_for_opening(driver: webdriver.Chrome, timeout: int = 180) -> str:
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, ".message.agent .bubble")) > 0
    )
    return last_agent_text(driver)


def send_chat_message(driver: webdriver.Chrome, text: str, timeout: int = 240) -> str:
    before_count = len(driver.find_elements(By.CSS_SELECTOR, ".message.agent .bubble"))
    textarea = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, "msgInput")))
    textarea.clear()
    textarea.send_keys(text)
    driver.find_element(By.ID, "sendBtn").click()

    def _agent_replied(d: webdriver.Chrome) -> bool:
        bubbles = d.find_elements(By.CSS_SELECTOR, ".message.agent .bubble")
        loading = d.find_elements(By.ID, "loadingMsg")
        return len(bubbles) > before_count and not loading

    WebDriverWait(driver, timeout).until(_agent_replied)
    return last_agent_text(driver)


def interview_complete(driver: webdriver.Chrome) -> bool:
    try:
        section = driver.find_element(By.ID, "continueSection")
        return section.value_of_css_property("display") != "none"
    except Exception:
        return False


def finish_interview_if_needed(driver: webdriver.Chrome) -> None:
    if interview_complete(driver):
        return
    try:
        finish_btn = driver.find_element(By.ID, "finishBtn")
        if finish_btn.is_displayed():
            finish_btn.click()
            WebDriverWait(driver, 10).until(interview_complete)
    except Exception:
        pass


def start_pipeline(driver: webdriver.Chrome) -> None:
    btn = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, "continueBtn")))
    btn.click()


def wait_for_pipeline_completion(driver: webdriver.Chrome, timeout_seconds: int) -> None:
    end_time = time.time() + timeout_seconds
    last_segment = None
    while time.time() < end_time:
        try:
            segment = driver.find_element(By.ID, "liveSegment").text.strip()
            if segment and segment != last_segment:
                print(f"[pipeline] {segment}", flush=True)
                last_segment = segment

            btn_text = driver.find_element(By.ID, "continueBtn").text.strip()
            if "处理完成" in btn_text:
                return

            scale = driver.find_element(By.ID, "scaleResult")
            if scale.value_of_css_property("display") != "none":
                return
        except Exception:
            pass
        time.sleep(5)
    raise TimeoutException("Pipeline did not finish before timeout")


def choose_fake_reply(turn: int, agent_msg: str, fake: FakeInterviewUser, demo: dict) -> str:
    if turn == 1 and demo.get("opening_user_reply"):
        return str(demo["opening_user_reply"]).strip()
    scripted = demo.get("scripted_replies") or []
    scripted_idx = turn - 2
    if 0 <= scripted_idx < len(scripted):
        return str(scripted[scripted_idx]).strip()
    reply = fake(agent_msg).strip()
    if not reply or "请开始提问" in reply:
        return "请继续围绕这个协作场景提问，我会按真实情况补充关键细节。"
    return reply


def main() -> None:
    parser = argparse.ArgumentParser(description="Drive app_gradio with a fake interview user.")
    parser.add_argument("--scenario", default="musculoskeletal_assembly")
    parser.add_argument("--config", default=None)
    parser.add_argument("--max-turns", type=int, default=12)
    parser.add_argument("--pipeline-timeout", type=int, default=14400)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--no-detach", action="store_true")
    parser.add_argument("--interview-only", action="store_true")
    parser.add_argument("--validation-mode", action="store_true")
    parser.add_argument("--teacher-demo", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    demo = get_demo_scenario(args.scenario)
    profile = "teacher-demo" if args.teacher_demo else ("validation" if args.validation_mode else "full")
    if args.teacher_demo:
        print(f"[teacher-demo] model={cfg.get('model_name')} api_base={cfg.get('api_base')}", flush=True)
    fake_model = "deepseek-v4-flash" if args.teacher_demo else cfg["model_name"]
    fake = FakeInterviewUser(
        api_key=cfg["openai_api_key"],
        model_name=fake_model,
        work_scenario=demo["fake_user_memory"],
    )

    port = find_free_port()
    cfg_override = None
    if args.teacher_demo:
        cfg_override = {"demo_mode": True, "model_name": "deepseek-v4-flash"}
    elif args.validation_mode:
        cfg_override = {"validation_mode": True}
    server = ServerThread(port, cfg_override=cfg_override)
    server.start()
    url = f"http://127.0.0.1:{port}/"
    print(f"[web-ui] {url}", flush=True)
    existing_runs = {
        p.name for p in (ROOT / "data" / "runs").iterdir()
        if (ROOT / "data" / "runs").exists() and p.is_dir()
    }
    start_ts = time.time()

    driver = build_driver(detach=not args.no_detach, headless=args.headless)
    try:
        driver.get(url)
        agent_msg = wait_for_opening(driver)
        print("[interview] opening loaded", flush=True)

        for turn in range(1, args.max_turns + 1):
            if interview_complete(driver):
                break
            user_msg = choose_fake_reply(turn, agent_msg, fake, demo)
            print(f"[interview] turn {turn}: {user_msg[:120]}", flush=True)
            agent_msg = send_chat_message(driver, user_msg)
            if interview_complete(driver):
                break

        finish_interview_if_needed(driver)
        if not interview_complete(driver):
            raise RuntimeError("Interview did not reach the continue stage")

        if args.interview_only:
            print("[interview] finished; stopping before pipeline", flush=True)
            return

        print("[pipeline] starting", flush=True)
        start_pipeline(driver)
        wait_for_pipeline_completion(driver, args.pipeline_timeout)
        print("[pipeline] finished", flush=True)
        end_ts = time.time()
        runs_root = ROOT / "data" / "runs"
        new_runs = [p for p in runs_root.iterdir() if p.is_dir() and p.name not in existing_runs] if runs_root.exists() else []
        run_dir = max(new_runs, key=lambda p: p.stat().st_mtime) if new_runs else _latest_run_dir()
        if run_dir:
            _write_run_timing(
                run_dir,
                scenario=args.scenario,
                profile=profile,
                start_ts=start_ts,
                end_ts=end_ts,
            )
            print(f"[run] saved timing -> {run_dir / 'run_timing.json'}", flush=True)
            print(f"[run] latest complete run -> {run_dir}", flush=True)
    finally:
        server.stop()
        if args.headless or args.no_detach:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
