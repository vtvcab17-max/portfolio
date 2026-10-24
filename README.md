# Portfolio · Phạm Việt Hà

Người sáng lập **Beta**, xây sản phẩm AI. Trang chạy trên GitHub Pages và Cloudflare Workers (`portfolio.vtvcab17.workers.dev`, có thể bật Cloudflare Access).

| Đường dẫn | Nội dung |
|---|---|
| `index.html` | Toàn bộ trang (HTML, CSS, JS trong một tệp, không cần build) |
| `assets/` | Ảnh, logo; `du-an.bin` là khu Dự án đã mã hoá bằng mật khẩu |
| `worker.js` | Phục vụ trang (chép vào `dist/` khi deploy) và chuyển tiếp số liệu Beta Holding qua `/api/bh/` |
| `wrangler.jsonc` | Cấu hình Cloudflare Workers |
| `index-1.html` | Bản portfolio cũ, giữ để đối chiếu (không đưa lên web) |
