#!/usr/bin/env python3
import asyncio
import os
import json
from playwright.async_api import async_playwright

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(PROJECT_DIR, "data", "cookies.json")
DOUYIN_URL = "https://www.douyin.com/"

async def main():
    os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
    print("[*] 正在启动本地浏览器，请在弹出的窗口中扫码或输入密码登录...")

    pw = await async_playwright().start()
    
    # Use ephemeral context (no profile dir) so it doesn't get bound to Mac keychain
    context = await pw.chromium.launch_persistent_context(
        "", 
        headless=False,
        channel="chrome",
        viewport={"width": 1280, "height": 800},
        locale="zh-CN",
        args=["--disable-blink-features=AutomationControlled"]
    )
    
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
    page = context.pages[0] if context.pages else await context.new_page()

    try:
        await page.goto(DOUYIN_URL, wait_until="commit", timeout=60000)
    except Exception as e:
        print(f"[!] 页面加载较慢，继续等待登录: {e}")

    print("[*] 等待登录... (登录成功后自动提取凭证并关闭)")
    for _ in range(300):
        try:
            cookies = await context.cookies()
        except Exception:
            await asyncio.sleep(1)
            continue
            
        if any(c.get("name") == "sessionid" for c in cookies):
            print("\n[+] 登录成功！正在提取跨平台纯文本 Cookies...")
            with open(COOKIES_FILE, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            print(f"[+] 提取完成！凭证已保存至: {COOKIES_FILE}")
            break
        await asyncio.sleep(1)
    else:
        print("[-] 登录超时")

    await context.close()
    await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())
