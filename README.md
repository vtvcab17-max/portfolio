# Portfolio · Phạm Việt Hà

Người sáng lập **Beta**, xây sản phẩm AI. Trang chạy trên GitHub Pages và Cloudflare Workers (`portfolio.vtvcab17.workers.dev`, có thể bật Cloudflare Access).

| Đường dẫn | Nội dung |
|---|---|
| `index.html` | Toàn bộ trang (HTML, CSS, JS trong một tệp, không cần build) |
| `assets/` | Ảnh, logo; `du-an.bin` là khu Dự án đã mã hoá bằng mật khẩu |
| `worker.js` | Phục vụ trang (chép vào `dist/` khi deploy) và chuyển tiếp số liệu Beta Holding qua `/api/bh/` |
| `wrangler.jsonc` | Cấu hình Cloudflare Workers |
| `index-1.html` | Bản portfolio cũ, giữ để đối chiếu (không đưa lên web) |
| `blog-src/` | Bài blog viết bằng Markdown (nguồn, không đưa lên web) |
| `blog/`, `sitemap.xml`, `robots.txt` | Blog đã dựng, sinh bởi `scripts/blog.py` (đừng sửa tay) |
| `scripts/` | `blog.py` dựng blog, `blog-covers.js` vẽ ảnh bìa, `blog_style.css` giao diện blog |

## Viết bài blog

1. Tạo tệp mới trong `blog-src/`, ví dụ `21-ten-bai.md`, chép phần đầu (giữa hai dòng `---`) từ một bài có sẵn rồi sửa:
   `slug` (đường dẫn, không dấu), `title`, `description` (khoảng 150 ký tự), `category` (HAVVKING, Phạm Việt Hà, Sản phẩm, Hướng dẫn),
   `keywords`, `image` (ảnh trong `assets/`, dùng cho ảnh bìa), `date`, `order` (số thứ tự; bài số 1 là bài nổi bật).
2. Viết nội dung bằng Markdown: `## Tiêu đề`, `- danh sách`, `**đậm**`, `[chữ](https://…)`, `![chú thích](assets/…)`, bảng `| … |`.
   Liên kết tới bài khác: `[chữ](post:slug)`. Thẻ đặc biệt (mỗi thẻ một dòng riêng):
   `{{yt ID Tiêu đề}}` nhúng YouTube, `{{post slug}}` thẻ "Đọc thêm", `{{link URL|ảnh|tiêu đề|mô tả}}` thẻ liên kết.
3. Chạy `python3 scripts/blog.py` rồi `node scripts/blog-covers.js` (vẽ ảnh bìa cho bài mới), commit và đẩy lên.

Blog không chấp nhận link GitHub (script báo lỗi nếu có).
