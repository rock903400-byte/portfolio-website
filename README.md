# Portfolio Website（已遷移）

[![Deploy](https://github.com/rock903400-byte/portfolio-website/actions/workflows/pages.yml/badge.svg)](https://github.com/rock903400-byte/portfolio-website/actions/workflows/pages.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> 本作品集已搬遷至 **https://wind.rock903400.workers.dev/**（備援鏡像：https://rock903400-byte.github.io/wind/）

舊網址 `rock903400-byte.github.io/portfolio-website/` 保留自動轉址到主站，
既有連結不會失效，但不再更新內容。新站請見 [rock903400-byte/wind](https://github.com/rock903400-byte/wind)。

## 這個 repo 現在放什麼

| 位置 | 用途 |
|------|------|
| `index.html` | 舊網址 `…/portfolio-website/` 的轉址頁（自動導向新站） |
| `cu-shengmu-site/` | 聖母社官網（客戶站）。用 `npx wrangler pages deploy cu-shengmu-site --project-name cu-shengmu-site --branch main` 手動部署到 Cloudflare Pages；`pages.yml` 也會把它連同整個 repo 一起發布到 GitHub Pages（`…/portfolio-website/cu-shengmu-site/`） |
| `scripts/keepalive.py`、`scripts/urls.txt`、`.github/workflows/wake.yml` | 每 4 小時用瀏覽器喚醒 `urls.txt` 列出的 Streamlit 展示站（免費方案閒置會休眠） |

其他專案資料夾在本機的同一個目錄下，但都被 `.gitignore` 排除，不在這個 repo 裡。

原本的動態作品集網站（GitHub API 即時渲染、分類篩選、全文搜尋、README 彈窗、深淺色主題、聯絡表單）
仍完整保留在 Git 歷史中，需要時可取回：

```bash
git show 067ef41:index.html > old-index.html
```

## License

MIT
