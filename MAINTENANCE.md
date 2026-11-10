# 官网发布维护注意事项

> 适用目录：`backend_update/official_website`（GitHub Pages 发布目录）
> 原则：**日常发版只改 `index.html`**；另外三个文件是稳定文件，不需要跟版本走。

## 1. 文件职责

| 文件 | 作用 | 什么时候需要改 |
|---|---|---|
| `index.html` | 官网页面 + 全部 SEO 元信息 | 每次发版 |
| `robots.txt` | 爬虫放行规则 + sitemap 地址 | 换域名、调整爬虫策略 |
| `sitemap.xml` | 页面清单 | 新增/删除/重命名页面、换域名 |
| `llms.txt` | 给 AI 的官方事实摘要 | 品牌定位、核心能力、路线图方向大改 |

## 2. 日常发版：只改 index.html

需要同步修改的内容都在 `index.html` 内：

- `<title>`、`description`、`keywords`、OG、Twitter
- JSON-LD 里的 `softwareVersion`、`offers` 价格、`dateModified`
- 页面里的版本号、价格

不需要改：`robots.txt`、`sitemap.xml`、`llms.txt`。

## 3. 什么时候必须改另外三个文件

### 新增 / 删除 / 重命名页面
- 改 `sitemap.xml`：增删对应的 `<loc>`。
- 不要加 `lastmod`，除非确定每次都会维护；旧日期比没有日期更糟。

### 更换域名
- `index.html`：canonical、OG、JSON-LD 里的绝对 URL
- `robots.txt`：`Sitemap:` 行
- `sitemap.xml`：所有 `<loc>`
- `llms.txt`：所有链接
- Pages 仓库：`CNAME`

### 调整爬虫策略
- 只改 `robots.txt`。

### 品牌定位 / 核心能力 / 路线图方向大改
- 改 `llms.txt`。
- 同时检查 `index.html` 的 `featureList`、FAQ、Roadmap 是否一致。

## 4. GitHub Pages 发布检查

- `index.html` 必须在 Pages 发布根目录；`官网.html` 不会被当作首页。
- 自定义域名需要 `CNAME` 文件，内容为 `aiwritex.voidai.cc`；换域名时同步修改。
- `official_website` 当前已包含完整站点：`index.html`、全部公开子页面、`assets/`、`preview.jpg`、`logo.png`、`CNAME` 与三个稳定文件。
- 已放置 `.nojekyll`，GitHub Pages 会按纯静态文件原样提供，不经过 Jekyll 处理。
- 新增公开页面时，记得同时把页面加入 `sitemap.xml`。
- 部署后验证：
  - `https://aiwritex.voidai.cc/`
  - `https://aiwritex.voidai.cc/robots.txt`
  - `https://aiwritex.voidai.cc/sitemap.xml`
  - `https://aiwritex.voidai.cc/llms.txt`
- 首次部署后到百度搜索资源平台、Google Search Console、Bing 站长工具提交 sitemap；以后页面不增删就不用再提交。

## 5. 不要做的事

- 不要把版本号、价格、日期写进 `llms.txt`（会过期，且官网才是权威）。
- 不要给 `sitemap.xml` 加不维护的 `lastmod`。
- 不要把 `robots.txt` 放到子路径后期待它生效（项目页的 `/repo/robots.txt` 不是域名根 robots）。
- 不要在 FAQ 区新增营销问答；FAQ 区保持原有 4 条安装/购买问答，如需调整应同步 FAQPage schema。
- 不要只改 `index.html` 的可见文案，而忘了同一文件里的 JSON-LD / OG。
