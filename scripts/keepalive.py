#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Streamlit Community Cloud 保活器.

原理: 用真正的瀏覽器 (Playwright + Chromium) 開啟每個 *.streamlit.app,
睡著時會出現 "Yes, get this app back up!" 按鈕, 幫忙點下去並等待 App 容器載入.
單純 requests.get 只會拿到靜態殼 (HTTP 200 但不會醒), 所以一定要走瀏覽器.

URL 來源 (優先順序):
  1. 環境變數 STREAMLIT_APP_URLS (逗號或換行分隔)
  2. 同目錄 urls.txt (忽略空行與 # 註解)

結束碼: 全部 OK/WAKE 回 0, 任一失敗回 1 (讓 Actions 變紅好發現).
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

URLS_FILE = Path(__file__).with_name("urls.txt")
WAKE_BUTTON_NAMES = [
    "Yes, get this app back up!",
    "get this app back up",
]

APP_READY_SELECTORS = [
    "div[data-testid='stAppViewContainer']",
    "section[data-testid='stMain']",
    "section[data-testid='stSidebar']",
    "input",
    "button",
    "canvas",
]


async def is_ready(page) -> bool:
    """App 內容是否已載入. 逐個 frame 檢查 (Cloud 版可能包 iframe)."""
    for frame in page.frames:
        for sel in APP_READY_SELECTORS:
            try:
                if await frame.locator(sel).count() > 0:
                    return True
            except Exception:  # noqa: BLE001
                pass
    try:
        txt = await page.locator("body").inner_text()
        if txt and len(txt.strip()) > 50:
            return True
    except Exception:  # noqa: BLE001
        pass
    return False


def load_urls(urls_file: Path = URLS_FILE) -> list[str]:
    env = os.environ.get("STREAMLIT_APP_URLS", "").strip()
    if env:
        parts = env.replace(",", "\n").splitlines()
        urls = [p.strip() for p in parts if p.strip() and not p.strip().startswith("#")]
        if urls:
            return urls
    if not urls_file.exists():
        return []
    urls: list[str] = []
    for line in urls_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


async def visit(page, url: str, nav_timeout: int = 120_000) -> str:
    """回傳 OK / WAKE / WAKE_FAIL / ERROR."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=nav_timeout)
    except Exception as e:  # noqa: BLE001 - 記錄即可, 繼續下一個
        log(f"  ERROR {url} (goto failed: {type(e).__name__})")
        return "ERROR"
    await page.wait_for_timeout(8000)

    # 1. 找喚醒鈕 (睡著才會出現)
    wake_btn = None
    try:
        btn = page.get_by_role("button", name=WAKE_BUTTON_NAMES[0])
        if await btn.count() > 0:
            wake_btn = btn.first
    except Exception:  # noqa: BLE001
        wake_btn = None
    if wake_btn is None:
        try:
            alt = page.locator("button:has-text('get this app back up')")
            if await alt.count() > 0:
                wake_btn = alt.first
        except Exception:  # noqa: BLE001
            wake_btn = None

    if wake_btn is not None:
        log(f"  WAKE  {url} (sleeping, clicking...)")
        try:
            await wake_btn.click(timeout=30_000)
        except Exception as e:  # noqa: BLE001
            log(f"  WAKE_FAIL {url} (click failed: {type(e).__name__})")
            return "WAKE_FAIL"
        # 冷啟動約 2-5 分鐘 (依賴重的 App 如 pandas+plotly 可能更久), 輪詢等內容出現
        for _ in range(30):  # 30 x 10s = 5min
            await page.wait_for_timeout(10_000)
            if await is_ready(page):
                log(f"  WAKE_OK {url}")
                return "WAKE"
        log(f"  WAKE_FAIL {url} (timeout waiting for app)")
        return "WAKE_FAIL"

    # 2. 沒睡著: 確認內容在即可
    if await is_ready(page):
        log(f"  OK    {url}")
        return "OK"
    # 內容還沒出, 可能是剛 reboot, 再等 30s 看一次
    await page.wait_for_timeout(30_000)
    if await is_ready(page):
        log(f"  OK    {url} (slow boot)")
        return "OK"
    log(f"  ERROR {url} (no wake button, no app content)")
    return "ERROR"


async def main() -> int:
    urls = load_urls()
    if not urls:
        log("No URLs found. Set STREAMLIT_APP_URLS or fill scripts/urls.txt")
        return 1
    log(f"Visiting {len(urls)} URLs...")
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log("playwright not installed. Run: pip install playwright && playwright install chromium")
        return 1

    results: dict[str, int] = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        for url in urls:
            status = await visit(page, url)
            results[status] = results.get(status, 0) + 1
        await browser.close()

    summary = " ".join(f"{k}={v}" for k, v in sorted(results.items()))
    log(f"Done. {summary}")
    failed = results.get("WAKE_FAIL", 0) + results.get("ERROR", 0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
