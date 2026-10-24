# Portfolio · Phạm Việt Hà

Người sáng lập **Beta**, xây sản phẩm AI. Trang chạy trên Cloudflare Workers (`portfolio.vtvcab17.workers.dev`), có Cloudflare Access: chỉ email được cho phép mới xem được.

| Đường dẫn | Nội dung |
|---|---|
| `site/index.html` | Toàn bộ trang (HTML, CSS, JS trong một tệp, không cần build) |
| `site/assets/` | Ảnh, logo; `du-an.bin` là khu Dự án đã mã hoá bằng mật khẩu |
| `worker.js` | Phục vụ `site/` và chuyển tiếp số liệu Beta Holding qua `/api/bh/` |
| `wrangler.jsonc` | Cấu hình Cloudflare Workers |
| `index-1.html` | Bản portfolio cũ, giữ để đối chiếu (không đưa lên web) |
