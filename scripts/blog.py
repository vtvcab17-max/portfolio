#!/usr/bin/env python3
"""Dựng blog tĩnh cho portfolio: blog-src/*.md → blog/, sitemap.xml, robots.txt.

Viết bài mới: tạo một tệp .md trong blog-src/ (xem phần đầu các bài có sẵn), rồi chạy
    python3 scripts/blog.py          # dựng HTML
    node scripts/blog-covers.js      # vẽ ảnh bìa cho bài mới (cần Playwright)
Không cần thư viện ngoài. Đường dẫn trong trang đều là tương đối nên chạy được cả trên
GitHub Pages (/portfolio/) lẫn Cloudflare Workers.
"""
import html, json, math, re, unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "blog-src", ROOT / "blog"
BASE = "https://portfolio.vtvcab17.workers.dev"
AUTHOR = "Phạm Việt Hà"
SAME_AS = [
    "https://www.youtube.com/@havvkingofficial",
    "https://open.spotify.com/artist/2ytqsqgD4mLZ0qkOlQnsmn",
    "https://soundcloud.com/ph-m-h-329852250",
    "https://www.tiktok.com/@havvking",
    "https://www.tiktok.com/@havv_king",
    "https://www.tiktok.com/@medialabotary",
    "https://www.instagram.com/havvking_/",
    "https://www.youtube.com/@newsreviewer11",
]
CATS = {  # tên chuyên mục → màu
    "HAVVKING": "#ff4fb0",
    "Phạm Việt Hà": "#8b7dff",
    "Sản phẩm": "#14c9c9",
    "Hướng dẫn": "#ffb340",
}
SOCIAL = [
    ("YouTube", "https://www.youtube.com/@havvkingofficial"),
    ("Spotify", "https://open.spotify.com/artist/2ytqsqgD4mLZ0qkOlQnsmn"),
    ("SoundCloud", "https://soundcloud.com/ph-m-h-329852250"),
    ("TikTok", "https://www.tiktok.com/@havvking"),
    ("Instagram", "https://www.instagram.com/havvking_/"),
]
ICONS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <symbol id="i-arrow" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M7 17 17 7M9 7h8v8"/></symbol>
  <symbol id="i-play" viewBox="0 0 24 24"><path fill="currentColor" d="M8 5.5v13a1 1 0 0 0 1.5.86l11-6.5a1 1 0 0 0 0-1.72l-11-6.5A1 1 0 0 0 8 5.5Z"/></symbol>
  <symbol id="i-clock" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></g></symbol>
  <symbol id="i-cal" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3.5" y="5" width="17" height="15" rx="3"/><path d="M8 3v4M16 3v4M3.5 10h17"/></g></symbol>
  <symbol id="i-search" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></g></symbol>
</svg>"""


def slugify(t):
    t = t.replace("đ", "d").replace("Đ", "D")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def esc(t):
    return html.escape(t, quote=True)


def fmt_date(d):
    y, m, dd = d.split("-")
    return f"{int(dd)} tháng {int(m)}, {y}"


# ---------------- đọc bài ----------------
def load():
    posts = []
    for f in sorted(SRC.glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
        if not m:
            raise SystemExit(f"{f.name}: thiếu phần đầu ---")
        meta = {}
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        for k in ("slug", "title", "description", "category", "image", "date", "order"):
            if not meta.get(k):
                raise SystemExit(f"{f.name}: thiếu '{k}'")
        if meta["category"] not in CATS:
            raise SystemExit(f"{f.name}: chuyên mục lạ '{meta['category']}'")
        if not (ROOT / meta["image"]).exists():
            raise SystemExit(f"{f.name}: không có ảnh {meta['image']}")
        meta["order"] = int(meta["order"])
        meta["body"] = m.group(2)
        meta["keywords"] = [k.strip() for k in meta.get("keywords", "").split(",") if k.strip()]
        meta["cover"] = f"assets/blog/{meta['slug']}.jpg"
        posts.append(meta)
    slugs = [p["slug"] for p in posts]
    if len(set(slugs)) != len(slugs):
        raise SystemExit("trùng slug")
    return sorted(posts, key=lambda p: p["order"])


# ---------------- markdown rút gọn ----------------
class MD:
    def __init__(self, rel, bylug, src):
        self.rel, self.bylug, self.src, self.toc = rel, bylug, src, []

    def url(self, u):
        if u.startswith("post:"):
            s = u[5:]
            if s not in self.bylug:
                raise SystemExit(f"{self.src}: liên kết tới bài không có '{s}'")
            return f"{self.rel}blog/{s}/"
        if u.startswith("home:"):
            return f"{self.rel}{u[5:]}"
        if u.startswith("assets/"):
            if not (ROOT / u).exists():
                raise SystemExit(f"{self.src}: không có tệp {u}")
            return self.rel + u
        if "github" in u.lower():
            raise SystemExit(f"{self.src}: không đưa link GitHub lên blog ({u})")
        return u

    def inline(self, t):
        codes = []
        t = re.sub(r"`([^`]+)`", lambda m: codes.append(m.group(1)) or f"\x00{len(codes)-1}\x00", t)
        t = esc(t)

        def link(m):
            txt, u = m.group(1), html.unescape(m.group(2))
            href = self.url(u)
            ext = href.startswith("http")
            return f'<a href="{esc(href)}"' + (' target="_blank" rel="noopener"' if ext else "") + f">{txt}</a>"

        t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
        return re.sub("\x00(\\d+)\x00", lambda m: f"<code>{esc(codes[int(m.group(1))])}</code>", t)

    def block(self, b):
        b = b.strip("\n")
        first = b.split("\n", 1)[0]
        if b.startswith("```"):
            code = "\n".join(b.split("\n")[1:-1])
            return f"<pre><code>{esc(code)}</code></pre>"
        if m := re.fullmatch(r"(#{2,3}) (.+)", first):
            lvl, txt = len(m.group(1)), m.group(2)
            hid = slugify(txt)
            if lvl == 2:
                self.toc.append((hid, txt))
            return f'<h{lvl} id="{hid}">{self.inline(txt)}</h{lvl}>'
        if m := re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]+)\)", b):
            alt, src = m.group(1), self.url(m.group(2))
            return (f'<figure class="reveal"><div class="fr glass"><img src="{esc(src)}" alt="{esc(alt)}" loading="lazy"></div>'
                    f"<figcaption>{self.inline(alt)}</figcaption></figure>")
        if m := re.fullmatch(r"\{\{yt (\S+) (.+)\}\}", b):
            vid, title = m.group(1), m.group(2)
            return (f'<figure class="reveal"><button class="yt" data-id="{esc(vid)}" aria-label="Phát video: {esc(title)}">'
                    f'<img src="https://i.ytimg.com/vi/{esc(vid)}/hqdefault.jpg" alt="" loading="lazy">'
                    f'<span class="play"><svg><use href="#i-play"/></svg></span></button><figcaption>{self.inline(title)}</figcaption></figure>')
        if m := re.fullmatch(r"\{\{post (\S+)\}\}", b):
            p = self.bylug.get(m.group(1))
            if not p:
                raise SystemExit(f"{self.src}: không có bài '{m.group(1)}'")
            return (f'<a class="callout glass reveal" href="{self.rel}blog/{p["slug"]}/"><img src="{self.rel}{p["cover"]}" alt="" loading="lazy">'
                    f'<span><small>Đọc thêm</small><b>{esc(p["title"])}</b></span></a>')
        if m := re.fullmatch(r"\{\{link (.+?)\|(.+?)\|(.+?)\|(.+?)\}\}", b):
            u, img, t, d = m.groups()
            href = self.url(u)
            ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
            return (f'<a class="callout glass reveal" href="{esc(href)}"{ext}><img src="{esc(self.url(img))}" alt="" loading="lazy">'
                    f"<span><b>{esc(t)}</b><small>{esc(d)}</small></span></a>")
        lines = b.split("\n")
        if all(re.match(r"[-*] ", l) for l in lines):
            return "<ul>" + "".join(f"<li>{self.inline(l[2:])}</li>" for l in lines) + "</ul>"
        if all(re.match(r"\d+\. ", l) for l in lines):
            items = [self.inline(re.sub(r"^\d+\. ", "", l)) for l in lines]
            return "<ol>" + "".join(f"<li>{i}</li>" for i in items) + "</ol>"
        if all(l.startswith(">") for l in lines):
            return "<blockquote>" + self.inline(" ".join(l.lstrip("> ") for l in lines)) + "</blockquote>"
        if all(l.startswith("|") for l in lines) and len(lines) >= 2:
            rows = [[c.strip() for c in l.strip("|").split("|")] for l in lines if not re.fullmatch(r"\|[\s:|-]+\|", l)]
            th = "".join(f"<th>{self.inline(c)}</th>" for c in rows[0])
            tb = "".join("<tr>" + "".join(f"<td>{self.inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            return f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>'
        return f"<p>{self.inline(' '.join(lines))}</p>"

    def render(self, text):
        blocks, cur, fence = [], [], False
        for line in text.split("\n"):
            if line.startswith("```"):
                fence = not fence
                cur.append(line)
                if not fence:
                    blocks.append("\n".join(cur)); cur = []
                continue
            if not fence and not line.strip():
                if cur:
                    blocks.append("\n".join(cur)); cur = []
                continue
            cur.append(line)
        if cur:
            blocks.append("\n".join(cur))
        return "\n".join(self.block(b) for b in blocks)


def words(text):
    return len(re.findall(r"\w+", re.sub(r"\{\{.*?\}\}|\(.*?\)", " ", text)))


# ---------------- khung trang ----------------
def head(rel, title, desc, canon, image, extra="", jsonld=()):
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>\n' for j in jsonld)
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{AUTHOR}">
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="#07070c" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#eef0f8" media="(prefers-color-scheme: light)">
<meta property="og:site_name" content="Phạm Việt Hà · HAVVKING">
<meta property="og:locale" content="vi_VN">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{BASE}/{image}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
{extra}<link rel="icon" href="{rel}assets/brand/beta.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{rel}assets/blog.css">
{ld}</head>
<body>
<div class="wall" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div><div class="grain" aria-hidden="true"></div>
<div class="progress" aria-hidden="true"></div>
{ICONS}
<nav class="bnav glass" aria-label="Điều hướng">
  <a class="me" href="{rel}"><img src="{rel}assets/avatars/nav.jpg" alt=""><span>{AUTHOR}</span></a>
  <a class="l" href="{rel}">Trang chủ</a>
  <a class="l on" href="{rel}blog/">Blog</a>
  <a class="l" href="{rel}#am-nhac">Âm nhạc</a>
</nav>
"""


def foot(rel):
    year = date.today().year
    return f"""<footer class="bfoot"><div class="wrap">
  <span>© {year} {AUTHOR} · HAVVKING</span>
  <span><a href="{rel}">Portfolio</a> · <a href="{rel}blog/">Blog</a> · <a href="{rel}#lien-he">Liên hệ</a></span>
</div></footer>
<div class="lbx" aria-hidden="true"><img alt=""></div>
<script src="{rel}assets/blog.js" defer></script>
</body>
</html>
"""


def person():
    return {"@type": "Person", "name": AUTHOR, "alternateName": "HAVVKING", "url": BASE + "/",
            "image": BASE + "/assets/avatars/hero.jpg", "sameAs": SAME_AS}


def card(p, rel, extra_cls=""):
    c = CATS[p["category"]]
    return (f'<a class="post glass reveal{extra_cls}" href="{rel}blog/{p["slug"]}/" data-cat="{esc(p["category"])}" '
            f'data-q="{esc(slugify(p["title"] + " " + p["description"] + " " + " ".join(p["keywords"])))}">'
            f'<div class="ph"><img src="{rel}{p["cover"]}" alt="{esc(p["title"])}" loading="lazy" width="1200" height="630"></div>'
            f'<span class="cat" style="--c:{c}">{esc(p["category"])}</span>'
            f'<h3>{esc(p["title"])}</h3><p>{esc(p["description"])}</p>'
            f'<div class="m">{p["mins"]} phút đọc</div></a>')


def build_post(p, posts, bylug):
    rel = "../../"
    md = MD(rel, bylug, p["slug"])
    body = md.render(p["body"])
    canon = f"{BASE}/blog/{p['slug']}/"
    c = CATS[p["category"]]
    toc = "".join(f'<li><a href="#{h}">{esc(t)}</a></li>' for h, t in md.toc)
    same = [q for q in posts if q["category"] == p["category"] and q is not p]
    other = [q for q in posts if q["category"] != p["category"]]
    k = p["order"]
    same.sort(key=lambda q: abs(q["order"] - k))
    related = (same[:2] + other[(k * 3) % len(other):][:1] + other[:1])[:3]
    ld = [{
        "@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "description": p["description"],
        "image": [f"{BASE}/{p['cover']}"], "datePublished": p["date"], "dateModified": p.get("updated", p["date"]),
        "inLanguage": "vi", "keywords": p["keywords"], "wordCount": p["words"],
        "author": person(), "publisher": person(),
        "mainEntityOfPage": {"@type": "WebPage", "@id": canon},
        "isPartOf": {"@type": "Blog", "name": "Blog Phạm Việt Hà · HAVVKING", "@id": f"{BASE}/blog/"},
    }, {
        "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": canon}]}]
    extra = (f'<meta property="og:type" content="article">\n<meta property="article:published_time" content="{p["date"]}">\n'
             f'<meta property="article:author" content="{AUTHOR}">\n<meta property="article:section" content="{esc(p["category"])}">\n'
             + "".join(f'<meta property="article:tag" content="{esc(k)}">\n' for k in p["keywords"]))
    if p["keywords"]:
        extra += f'<meta name="keywords" content="{esc(", ".join(p["keywords"]))}">\n'
    soc = "".join(f'<a class="chip glass magnet" href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in SOCIAL)
    title_tag = p.get("seo_title") or p["title"]
    out = head(rel, title_tag, p["description"], canon, p["cover"], extra, ld)
    out += f"""<main>
<header class="wrap ahead">
  <ol class="crumb"><li><a href="{rel}">Trang chủ</a></li><li><a href="{rel}blog/">Blog</a></li><li><a href="{rel}blog/#{slugify(p['category'])}">{esc(p['category'])}</a></li></ol>
  <h1>{esc(p['title'])}</h1>
  <p class="lead">{esc(p['description'])}</p>
  <div class="ameta">
    <a class="by" href="{rel}"><img src="{rel}assets/avatars/nav.jpg" alt="">{AUTHOR}</a>
    <span class="cat" style="--c:{c}">{esc(p['category'])}</span>
    <span><svg class="ic" style="width:16px;height:16px"><use href="#i-cal"/></svg><time datetime="{p['date']}">{fmt_date(p['date'])}</time></span>
    <span><svg class="ic" style="width:16px;height:16px"><use href="#i-clock"/></svg>{p['mins']} phút đọc</span>
  </div>
</header>
<div class="wrap" style="max-width:1100px"><div class="cover glass tilt"><img src="{rel}{p['cover']}" alt="{esc(p['title'])}" width="1200" height="630" fetchpriority="high"></div></div>
<div class="wrap alayout">
  <article>
    <details class="toc-m glass"><summary>Mục lục</summary><nav class="toc"><ol>{toc}</ol></nav></details>
    <div class="prose">
{body}
    </div>
    <aside class="author glass reveal">
      <img src="{rel}assets/avatars/hero.jpg" alt="{AUTHOR}" loading="lazy">
      <div><h4>{AUTHOR} · HAVVKING</h4>
      <p>Người sáng lập Beta, xây các sản phẩm AI Bravin, Antifact, Micron, Micow và Beta HQ. Cử nhân Trí tuệ nhân tạo (ĐH FPT), đang học Kỹ sư phần mềm (PTIT). Làm nhạc dưới nghệ danh HAVVKING.</p>
      <div class="soc">{soc}<a class="chip glass magnet" href="{rel}">Portfolio</a></div></div>
    </aside>
  </article>
  <aside class="toc-side glass"><h4>Trong bài này</h4><nav class="toc"><ol>{toc}</ol></nav></aside>
</div>
<section class="wrap related"><h2>Đọc tiếp</h2><div class="posts">{''.join(card(q, rel) for q in related)}</div></section>
</main>
"""
    out += foot(rel)
    d = OUT / p["slug"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(out, encoding="utf-8")


def build_index(posts):
    rel = "../"
    canon = f"{BASE}/blog/"
    feat, rest = posts[0], posts[1:]
    cats = ["Tất cả"] + list(CATS)
    btns = "".join(f'<button type="button" data-f="{esc(c)}" id="{slugify(c)}" aria-pressed="{str(i == 0).lower()}">{esc(c)}</button>'
                   for i, c in enumerate(cats))
    desc = "Blog của Phạm Việt Hà (HAVVKING): âm nhạc HAVVKING, hành trình của Phạm Việt Hà, hệ sinh thái Beta và hướng dẫn dùng các sản phẩm AI Bravin, Antifact, Micron, Micow."
    ld = [{"@context": "https://schema.org", "@type": "Blog", "name": "Blog Phạm Việt Hà · HAVVKING", "url": canon,
           "description": desc, "inLanguage": "vi", "author": person(),
           "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": f"{BASE}/blog/{p['slug']}/",
                         "datePublished": p["date"], "image": f"{BASE}/{p['cover']}"} for p in posts]}]
    out = head(rel, "Blog Phạm Việt Hà · HAVVKING: âm nhạc, sản phẩm AI và hành trình", desc, canon,
               feat["cover"], '<meta property="og:type" content="website">\n', ld)
    c = CATS[feat["category"]]
    out += f"""<main>
<header class="wrap bhero reveal">
  <span class="eyebrow glass">Blog</span>
  <h1>Ghi chép của <span class="grad nosplit">Phạm Việt Hà</span> và HAVVKING.</h1>
  <p class="lead">Âm nhạc của HAVVKING, hành trình từ thiết kế, truyền thông đến sản phẩm AI, và cách mình xây hệ sinh thái Beta: Bravin, Antifact, Micron, Micow, Beta HQ.</p>
  <a class="who" href="{rel}"><span class="av"><img src="{rel}assets/avatars/nav.jpg" alt=""><img src="{rel}assets/music/avatar.jpg" alt=""></span>
    <span><b>{AUTHOR}</b><small>nghệ danh HAVVKING · {len(posts)} bài viết</small></span></a>
</header>
<div class="wrap">
  <a class="feat glass reveal" href="{rel}blog/{feat['slug']}/">
    <div class="ph"><img src="{rel}{feat['cover']}" alt="{esc(feat['title'])}" width="1200" height="630" fetchpriority="high"></div>
    <div class="tx"><span class="cat" style="--c:{c}">Nổi bật · {esc(feat['category'])}</span><h2>{esc(feat['title'])}</h2><p>{esc(feat['description'])}</p>
    <span class="btn tint go magnet">Đọc bài <svg><use href="#i-arrow"/></svg></span></div>
  </a>
  <div class="filters glass reveal" role="group" aria-label="Lọc theo chuyên mục"><span class="pill" aria-hidden="true"></span>{btns}</div>
  <label class="search glass reveal"><svg class="ic"><use href="#i-search"/></svg><input type="search" placeholder="Tìm bài: havvking, micow, bravin…" aria-label="Tìm bài viết"></label>
  <div class="posts">{''.join(card(p, rel) for p in rest)}</div>
  <p class="empty">Chưa có bài nào khớp. Thử từ khác nhé.</p>
</div>
</main>
"""
    out += foot(rel)
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(out, encoding="utf-8")


def build_home_teaser(posts):
    """Chèn 3 bài nổi bật vào trang chủ, giữa hai dấu <!-- blog:start --> và <!-- blog:end -->."""
    f = ROOT / "index.html"
    s = f.read_text(encoding="utf-8")
    a, b = "<!-- blog:start -->", "<!-- blog:end -->"
    if a not in s:
        return
    pick = posts[:3]
    cards = "".join(
        f'<a class="bcard glass reveal" href="blog/{p["slug"]}/"><div class="ph"><img src="{p["cover"]}" alt="{esc(p["title"])}" loading="lazy" width="1200" height="630"></div>'
        f'<span class="cat" style="--c:{CATS[p["category"]]}">{esc(p["category"])}</span><h3>{esc(p["title"])}</h3><p>{esc(p["description"])}</p></a>'
        for p in pick)
    s = s[: s.index(a) + len(a)] + "\n<div class=\"bcards\">" + cards + "</div>\n" + s[s.index(b):]
    f.write_text(s, encoding="utf-8")


def build_sitemap(posts):
    today = date.today().isoformat()
    urls = [(BASE + "/", today, "1.0"), (BASE + "/blog/", today, "0.9")]
    urls += [(f"{BASE}/blog/{p['slug']}/", p.get("updated", p["date"]), "0.8") for p in posts]
    x = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod><priority>{pr}</priority></url>" for u, d, pr in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{x}</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")


def main():
    posts = load()
    bylug = {p["slug"]: p for p in posts}
    for p in posts:
        p["words"] = words(p["body"])
        p["mins"] = max(1, math.ceil(p["words"] / 220))
    base = (ROOT / "index.html").read_text(encoding="utf-8")
    a = base.index("/* ============ Liquid Glass: token ============ */")
    b = base.index("/* ============ Thanh điều hướng nổi ============ */")
    (ROOT / "assets" / "blog.css").write_text(
        "/* Tự sinh bởi scripts/blog.py: token lấy từ index.html + scripts/blog_style.css. Đừng sửa tay. */\n"
        + base[a:b] + (ROOT / "scripts" / "blog_style.css").read_text(encoding="utf-8"), encoding="utf-8")
    build_index(posts)
    for p in posts:
        build_post(p, posts, bylug)
    build_home_teaser(posts)
    build_sitemap(posts)
    (ROOT / "scripts" / "blog-covers.json").write_text(json.dumps(
        [{k: p[k] for k in ("slug", "title", "category", "image", "cover")} | {"color": CATS[p["category"]]} for p in posts],
        ensure_ascii=False, indent=1), encoding="utf-8")
    missing = [p["cover"] for p in posts if not (ROOT / p["cover"]).exists()]
    print(f"Đã dựng {len(posts)} bài, {sum(p['words'] for p in posts)} từ.")
    if missing:
        print("Thiếu ảnh bìa, chạy: node scripts/blog-covers.js →", ", ".join(missing))


if __name__ == "__main__":
    main()
