#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(PROJECT_DIR, "data", "browser_profile")
COOKIES_FILE = os.path.join(PROJECT_DIR, "data", "cookies.json")

async def main():
    if not os.path.exists(COOKIES_FILE):
        print("[-] 未找到 data/cookies.json，请先在本地运行 local_login.py 并将生成的文件放入 data/ 目录。")
        sys.exit(1)
        
    print("[*] 正在读取 cookies.json...")
    with open(COOKIES_FILE, "r", encoding="utf-8") as f:
        cookies = json.load(f)
        
    print("[*] 正在启动无头浏览器以注入凭证...")
    pw = await async_playwright().start()
    
    kwargs = dict(
        headless=True, 
        viewport={"width": 1400, "height": 900}, 
        locale="zh-CN",
        args=["--disable-blink-features=AutomationControlled"]
    )
    
    try:
        context = await pw.chromium.launch_persistent_context(PROFILE_DIR, channel="chrome", **kwargs)
    except Exception:
        context = await pw.chromium.launch_persistent_context(PROFILE_DIR, **kwargs)
        
    await context.add_cookies(cookies)
    
    # 验证是否注入成功
    saved_cookies = await context.cookies()
    if any(c.get("name") == "sessionid" for c in saved_cookies):
        print("[+] 成功将 Cookies 注入到 Linux 服务器的 browser_profile 中！")
        print("[+] 你现在可以正常使用爬虫了。为了安全，建议删除 data/cookies.json 文件。")
    else:
        print("[-] 注入失败，请重试。")
        
    await context.close()
    await pw.stop()

if __name__ == "__main__":
    asyncio.run(main())
