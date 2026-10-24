/* Blog: hiện dần, thanh tiến độ đọc, lọc + tìm bài, mục lục, video YouTube, phóng ảnh, nghiêng 3D */
(() => {
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }), { threshold: .12, rootMargin: "0px 0px -6% 0px" });
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));

  // thanh tiến độ: trang bài viết đo theo phần nội dung, trang danh sách đo cả trang
  const bar = document.querySelector(".progress"), prose = document.querySelector(".prose");
  const onScroll = () => {
    let k;
    if (prose) { const r = prose.getBoundingClientRect(); k = (innerHeight * .4 - r.top) / r.height; }
    else k = scrollY / (document.documentElement.scrollHeight - innerHeight);
    bar.style.transform = `scaleX(${Math.min(1, Math.max(0, k))})`;
  };
  addEventListener("scroll", onScroll, { passive: true }); onScroll();

  // đốm sáng trên kính chạy theo con trỏ
  document.addEventListener("pointermove", e => {
    const g = e.target.closest && e.target.closest(".glass"); if (!g) return;
    const r = g.getBoundingClientRect();
    g.style.setProperty("--mx", e.clientX - r.left + "px"); g.style.setProperty("--my", e.clientY - r.top + "px");
  });

  // nút hút nhẹ theo con trỏ, ảnh bìa nghiêng 3D
  if (!still && matchMedia("(pointer:fine)").matches) {
    document.querySelectorAll(".magnet").forEach(m => {
      m.addEventListener("pointermove", e => { const r = m.getBoundingClientRect();
        m.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * .18}px,${(e.clientY - r.top - r.height / 2) * .25}px)`; });
      m.addEventListener("pointerleave", () => m.style.transform = "");
    });
    document.querySelectorAll(".tilt").forEach(t => {
      t.addEventListener("pointermove", e => { const r = t.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
        t.style.transform = `perspective(1200px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg)`; });
      t.addEventListener("pointerleave", () => t.style.transform = "");
    });
  }

  // lọc theo chuyên mục + tìm kiếm
  const filters = document.querySelector(".filters");
  if (filters) {
    const pill = filters.querySelector(".pill"), btns = [...filters.querySelectorAll("button")];
    const posts = [...document.querySelectorAll(".posts .post")], q = document.querySelector(".search input"), empty = document.querySelector(".empty");
    const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "d").toLowerCase().replace(/[^a-z0-9]+/g, "-");
    let cat = "Tất cả";
    const place = b => { pill.style.left = b.offsetLeft + "px"; pill.style.width = b.offsetWidth + "px"; };
    const apply = () => {
      const words = norm(q.value).split("-").filter(Boolean); let n = 0;
      posts.forEach((p, i) => {
        const ok = (cat === "Tất cả" || p.dataset.cat === cat) && words.every(w => p.dataset.q.includes(w));
        const was = !p.classList.contains("hide");
        p.classList.toggle("hide", !ok);
        if (ok) { n++; if (!was) { p.classList.remove("pop"); void p.offsetWidth; p.style.animationDelay = (n * 40) + "ms"; p.classList.add("pop", "in"); } }
      });
      empty.style.display = n ? "none" : "block";
    };
    btns.forEach(b => b.addEventListener("click", () => {
      btns.forEach(x => x.setAttribute("aria-pressed", x === b)); place(b); cat = b.dataset.f;
      posts.forEach(p => p.classList.add("hide")); apply();
      history.replaceState(null, "", b.id === "tat-ca" ? location.pathname : "#" + b.id);
    }));
    q.addEventListener("input", apply);
    const start = btns.find(b => "#" + b.id === location.hash) || btns[0];
    requestAnimationFrame(() => { start.click(); });
    addEventListener("resize", () => place(btns.find(b => b.getAttribute("aria-pressed") === "true")));
  }

  // mục lục: tô mục đang đọc (tiêu đề gần nhất đã cuộn qua 30% màn hình)
  const links = [...document.querySelectorAll(".toc a")];
  if (links.length) {
    const heads = [...new Set(links.map(a => a.getAttribute("href").slice(1)))].map(id => document.getElementById(id)).filter(Boolean);
    const mark = () => {
      let cur = null;
      heads.forEach(h => { if (h.getBoundingClientRect().top < innerHeight * .3) cur = h.id; });
      links.forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#" + cur));
    };
    addEventListener("scroll", mark, { passive: true }); mark();
    links.forEach(a => a.addEventListener("click", () => { const d = a.closest("details"); if (d) d.open = false; }));
  }

  // YouTube chỉ tải khi bấm (trang nhẹ, không theo dõi người đọc trước khi họ muốn xem)
  document.querySelectorAll(".yt").forEach(b => b.addEventListener("click", () => {
    const f = document.createElement("iframe");
    f.src = `https://www.youtube-nocookie.com/embed/${b.dataset.id}?autoplay=1&rel=0`;
    f.allow = "autoplay; encrypted-media; picture-in-picture"; f.allowFullscreen = true; f.title = b.getAttribute("aria-label");
    b.replaceChildren(f);
  }, { once: true }));

  // phóng ảnh trong bài
  const lbx = document.querySelector(".lbx");
  document.querySelectorAll(".prose figure img").forEach(img => img.addEventListener("click", () => {
    lbx.querySelector("img").src = img.currentSrc || img.src; lbx.querySelector("img").alt = img.alt; lbx.classList.add("on");
  }));
  lbx.addEventListener("click", () => lbx.classList.remove("on"));
  addEventListener("keydown", e => { if (e.key === "Escape") lbx.classList.remove("on"); });
})();
