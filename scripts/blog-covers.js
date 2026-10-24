// Vẽ ảnh bìa 1200×630 cho bài blog (cũng là ảnh chia sẻ og:image).
// Chạy sau `python3 scripts/blog.py`:  node scripts/blog-covers.js [--all]
// Mặc định chỉ vẽ bài chưa có ảnh bìa; --all vẽ lại tất cả. Cần Playwright + Chromium.
const { chromium } = require("playwright");
const fs = require("fs"), path = require("path");

const ROOT = path.resolve(__dirname, "..");
const posts = JSON.parse(fs.readFileSync(path.join(__dirname, "blog-covers.json"), "utf8"));
const all = process.argv.includes("--all");
const url = p => "file://" + path.join(ROOT, p);
const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const page = p => {
  const logo = /\.(svg|png)$/.test(p.image) && !p.image.includes("/blog/img/");
  const wide = p.image.includes("/blog/img/");
  return `<!doctype html><meta charset="utf-8"><style>
*{margin:0;box-sizing:border-box}
body{width:1200px;height:630px;overflow:hidden;position:relative;background:#0b0b12;font-family:Inter,system-ui,sans-serif;color:#f4f3fb}
.g{position:absolute;border-radius:50%}
.g1{width:900px;height:900px;left:-300px;top:-420px;background:radial-gradient(circle,${p.color}70,transparent 64%)}
.g2{width:760px;height:760px;right:-260px;bottom:-420px;background:radial-gradient(circle,#7b6cf655,transparent 64%)}
.t{position:absolute;left:64px;top:62px;width:${wide ? 560 : 640}px;height:506px;display:flex;flex-direction:column}
.cat{display:inline-flex;align-items:center;gap:10px;align-self:flex-start;height:40px;padding:0 18px;border-radius:99px;font:700 18px/1 Inter;letter-spacing:.02em;color:${p.color};background:${p.color}22}
.cat::before{content:"";width:10px;height:10px;border-radius:50%;background:currentColor}
h1{margin-top:26px;font:800 ${p.title.length > 70 ? 44 : p.title.length > 50 ? 50 : 56}px/1.12 Inter;letter-spacing:-.035em;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}
.by{margin-top:auto;display:flex;align-items:center;gap:14px;font:600 20px/1.2 Inter}
.by img{width:52px;height:52px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 3px #ffffff30}
.by small{display:block;font-weight:500;font-size:16px;color:#b9b5d6;margin-top:3px}
.ph{position:absolute;right:${wide ? -60 : 60}px;top:${wide ? 92 : 70}px;width:${wide ? 600 : 400}px;height:${wide ? 446 : 490}px;padding:12px;border-radius:40px;
  background:linear-gradient(160deg,#ffffff2a,#ffffff0c);box-shadow:inset 0 1px 0 #ffffff55,0 40px 80px -20px #000c;transform:rotate(${wide ? -3 : 3}deg)}
.ph img{width:100%;height:100%;border-radius:30px;object-fit:${logo ? "contain" : "cover"};object-position:${wide ? "left top" : "center"};background:${logo ? "#fff" : "#000"};padding:${logo ? 60 : 0}px}
</style><div class="g g1"></div><div class="g g2"></div>
<div class="t"><span class="cat">${esc(p.category)}</span><h1>${esc(p.title)}</h1>
<div class="by"><img src="${url("assets/avatars/nav.jpg")}"><span>Phạm Việt Hà<small>HAVVKING · Blog</small></span></div></div>
<div class="ph"><img src="${url(p.image)}"></div>`;
};

(async () => {
  const todo = posts.filter(p => all || !fs.existsSync(path.join(ROOT, p.cover)));
  if (!todo.length) return console.log("Ảnh bìa đã đủ.");
  const b = await chromium.launch(), pg = await b.newPage({ viewport: { width: 1200, height: 630 } });
  const tmp = path.join(__dirname, ".cover.html");
  for (const p of todo) {
    fs.writeFileSync(tmp, page(p));
    await pg.goto("file://" + tmp); await pg.waitForLoadState("networkidle"); await pg.waitForTimeout(150);
    await pg.screenshot({ path: path.join(ROOT, p.cover), type: "jpeg", quality: 84 });
    console.log("đã vẽ", p.cover);
  }
  fs.unlinkSync(tmp); await b.close();
})();
