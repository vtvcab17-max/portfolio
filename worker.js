// Portfolio trên Cloudflare Workers: phục vụ thư mục site/ và chuyển tiếp số liệu Beta Holding
// qua /api/bh/ để trang không chứa đường dẫn tới nơi lưu mã nguồn; ghi IP mỗi lượt tải ảnh bằng cấp.
const SRC = "https://raw.githubusercontent.com/vtvcab17-max/beta-holding/";
const ALLOWED = /^(main|paperclip-chay)\/data\/[\w.-]+\.json$/;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/bh/")) {
      const path = url.pathname.slice("/api/bh/".length);
      if (!ALLOWED.test(path)) return new Response("Không tìm thấy", { status: 404 });
      const r = await fetch(SRC + path, { cf: { cacheTtl: 60, cacheEverything: true } });
      return new Response(r.ok ? r.body : "null", {
        status: r.ok ? 200 : 404,
        headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=60" },
      });
    }
    if (url.pathname === "/assets/edu/creds.bin") {
      // Ảnh bằng cấp đã mã hoá: ghi lại mỗi lượt tải (xem trong Cloudflare: Workers → portfolio → Logs).
      console.log(JSON.stringify({
        su_kien: "tai_anh_bang_cap",
        ip: request.headers.get("CF-Connecting-IP"),
        quoc_gia: request.cf && request.cf.country,
        thanh_pho: request.cf && request.cf.city,
        trinh_duyet: request.headers.get("User-Agent"),
        trang_gui: request.headers.get("Referer"),
        luc: new Date().toISOString(),
      }));
      const r = await env.ASSETS.fetch(request);
      const h = new Headers(r.headers);
      h.set("cache-control", "private, no-store");
      return new Response(r.body, { status: r.status, headers: h });
    }
    return env.ASSETS.fetch(request);
  },
};
