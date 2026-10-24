// Portfolio trên Cloudflare Workers: phục vụ thư mục site/ và chuyển tiếp số liệu Beta Holding
// qua /api/bh/ để trang không chứa đường dẫn tới nơi lưu mã nguồn.
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
    return env.ASSETS.fetch(request);
  },
};
