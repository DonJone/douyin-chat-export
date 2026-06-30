"""Test: can we call batch_play_info from page context with arbitrary vids?
No scrolling needed if yes."""
import asyncio
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extractor.web_scraper import WebChatScraper


def some_vids(n=3):
    c = sqlite3.connect("data/chat.db"); c.row_factory = sqlite3.Row
    out = []
    for r in c.execute("SELECT raw_data FROM messages WHERE raw_data LIKE '%tkey%' ORDER BY timestamp DESC LIMIT 50"):
        try:
            ro = json.loads(r[0])
            if ro.get("awe_type") != 0: continue
            cj = json.loads(ro.get("content_json", "{}"))
            tkey = cj.get("video", {}).get("tkey")
            vid = cj.get("video", {}).get("vid")
            if tkey: out.append({"tkey": tkey, "vid": vid})
            if len(out) >= n: break
        except Exception: pass
    return out


async def main():
    vids = some_vids(5)
    print(f"[*] testing with {len(vids)} vids:", flush=True)
    for v in vids: print(f"    tkey={v['tkey']}")

    s = WebChatScraper()
    await s.launch()
    await s.wait_for_login()
    page = s.page

    print("\n[*] open /chat (just to load SDK + cookies + tokens) ...", flush=True)
    await page.goto("https://www.douyin.com/chat", wait_until="commit", timeout=30000)
    await asyncio.sleep(8)

    # === Direct fetch from page context, NO click, NO scroll ===
    print("\n[*] calling batch_play_info via page.fetch with all vids batched ...", flush=True)
    result = await page.evaluate(
        r"""async (vids) => {
            try {
                // Build body
                const body = JSON.stringify({
                    req_infos: vids.map(v => ({ item_id: 0, tos_key: v.tkey, type: 2 })),
                    with_caption: true,
                });
                // Hit the endpoint WITHOUT custom params — let the SDK's URL handling do its thing
                // (cookies + SDK's request interceptor will add msToken/a_bogus)
                const url = '/aweme/v1/web/maya/story/batch_play_info/v1/?device_platform=webapp&aid=6383&channel=channel_pc_web&app_name=douyin_web&pc_client_type=1';
                const resp = await fetch(url, {
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body,
                });
                const text = await resp.text();
                return { status: resp.status, body: text.slice(0, 3000) };
            } catch (e) {
                return { err: String(e) };
            }
        }""", vids,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))

    try: await asyncio.wait_for(s.close(), timeout=10)
    except Exception: pass


if __name__ == "__main__":
    asyncio.run(main())
