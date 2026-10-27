#!/usr/bin/env python3
"""Báo cho Bing, Yandex, Naver, Seznam (giao thức IndexNow) mọi địa chỉ trong sitemap.xml.
Chạy sau khi trang mới đã lên web:  python3 scripts/indexnow.py
Google không dùng IndexNow: với Google, nộp sitemap trong Google Search Console."""
import json, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "portfolio.vtvcab17.workers.dev"
key = (ROOT / "scripts" / "indexnow-key").read_text().strip()
urls = re.findall(r"<loc>(.*?)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))
body = json.dumps({"host": HOST, "key": key, "keyLocation": f"https://{HOST}/{key}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as r:
    print(f"IndexNow: gửi {len(urls)} địa chỉ, máy chủ trả {r.status} (200/202 là đã nhận)")
