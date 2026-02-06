# AIWriteX- 微信公众号AI写作助手 | CrewAI多智能体爆文生成神器

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB)](https://www.python.org/) [![CrewAI](https://img.shields.io/badge/CrewAI-0.102.0+-FF6B6B)](https://pypi.org/project/crewai) [![AIForge](https://img.shields.io/badge/aiforge-0.0.19+-E91E63)](https://pypi.org/project/aiforge-engine) [![PyWebView](https://img.shields.io/badge/PyWebView-4.0.0+-9C27B0)](https://pywebview.flowrl.com/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1+-009688)](https://fastapi.tiangolo.com/) [![GrapesJS](https://img.shields.io/badge/GrapesJS-0.22.13+-4A90E2)](https://grapesjs.com/) [![Monaco Editor](https://img.shields.io/badge/Monaco%20Editor-0.45.0+-4CAF50)](https://microsoft.github.io/monaco-editor/) [![Marked](https://img.shields.io/badge/Marked-11.1.1+-00BCD4)](https://marked.js.org/) [![PyWinGUIBuilder](https://img.shields.io/badge/PyWinGUIBuilder-1.0.0+-FFC107)](https://github.com/iniwap/PyWinGUIBuilder) [![Stars](https://img.shields.io/github/stars/iniwap/AIWriteX?label=收藏)](https://iniwap.github.io/AIWriteX)

**[<u>AIWriteX</u>](https://aiwritex.voidai.cc/) 新一代智能内容创作平台**：一键全自动热点选题 + 实时搜索借鉴 + AI创意生成 + 精美排版 + 微信公众号自动发布，融合 **AI + 全网热点雷达 + 微信文章采集下载 + 深度洗稿与内容挖掘 + 多智能体协作 + 去AI味润色**，让你的文章快人一步、阅读量10w+不是梦！

> **想先看看效果？** 👉 [实例预览](#绝美排版实例预览)  
> **想用商业稳定版？** 👉 [前往官网](https://aiwritex.voidai.cc/)  
> **喜欢这个项目？** ⭐ 点个 Star 支持一下吧！

## 🛡️ 独家黑科技：去AI味/AI对抗检测

还在为文章被判定为"100% AI生成"而苦恼？AIWriteX 内置**深度对抗检测引擎**，不止是简单的同义词替换，而是从**底层逻辑**打破AI生成的概率链条：

- **动态风格拟态**：不再是机械的指令，系统会自动提取参考文章的"用词DNA"，并强制注入到生成文中，实现"灵魂级"的风格复刻。
- **结构粉碎**：AI喜欢写工整的列表和段落？我们**强制打散**。列表扁平化、段落长短交错、逻辑连接词随机消除，彻底破坏AI的"完美秩序"。
- **情感色彩增强**：系统内置**情感微扰模块**，随机注入强烈主观色彩的表达与反问句，拒绝客观中立，让文章充满"人"的偏见与温度。
- **评分反馈进化**：可对每次的对抗评分，以优化后续流程

> 残酷的现实：随着朱雀等检测器持续进化，AI生成的完整长文通过检测会越来越难。建议：AI辅助而非AI生成、人机混合协作，AI写初稿的部分段落，人类大幅修改并补充  
> 实测效果：一般（但目前能见到的，应属全网最强）。**朱雀AI检测过于变态，对抗非一日之功，需做长远计**。  

<img src="De_AI_Flavor.jpg" width="100%">

## 📜 素材文库（您的本地知识库）

**告别素材焦虑，打造专属内容护城河！**

AIWriteX 不仅仅是写作工具，更是你的**私有化内容资产管理系统**。

- **微信文库**：
  - 一键采集任意公众号文章，**图片/内容永久本地存储**，构建私有素材库。
  - 支持 Markdown/HTML 双格式导出，无缝对接其他工具。
- **智能选题**：
  - **“蓝海”挖掘机**：AI 深度分析本地库，基于 `多维智能算法` 推荐高价值选题。
  - **写作导航**：每个选题自动生成 **3 个绝佳切入点** + **参考素材评分**，起号不再难。
- **内容挖掘**：
  - **语义级搜索**：不再只是关键词匹配，AI 帮你找到真正相关的深度素材。
  - **AI 融合洗稿**：选中多篇爆文 → AI 自动**去重、提炼、重组** → 生成一篇逻辑严密、观点犀利的原创底稿。

<img src="preview.jpg" width="100%">
<img src="preview1.jpg" width="100%">
<img src="preview2.jpg" width="100%">
  
## 💎 核心功能一览

- 自动抓取全网热门话题，确保标题/内容紧跟潮流
- CrewAI 多智能体协作：研究员 → 作家 → 审核员 → 设计师，一键生成 + 酷炫排版
- **高时效性**：AIForge 实时搜索 + 文章采集借鉴，杜绝陈旧资讯
- 一键发布微信公众号图文（支持定时任务、批量生成、多账号）
- 可视化软件界面：配置/模板/文章/配图/发布全管理
- 两种模式：**软件模式**（小白一键安装） / **开发模式**（灵活定制）

## 🤖 核心技术亮点

- 多智能体框架：CrewAI 驱动，角色分工明确
- 实时资讯引擎：AIForge 多策略搜索 + 借鉴竞品
- 创意变换引擎：文体转换、时空穿越、角色扮演、无限组合
- 智能排版：自动适配微信/小红书/抖音展示风格（更多平台开发中）
- 去AI味优化：对抗检测 + 自然润色，写出真人风格爆文

## 🔥 重磅功能：全网热点雷达（提前2-6小时抓黑马！）

AIWriteX 独家**流量预测引擎**，基于物理算法 + AI研判，帮你锁定即将爆发的潜力话题：

- 聚合微博/抖音/小红书/热搜数据，一键查看平台热点
- **黑马挖掘**：热度0但12小时内预计暴涨的话题，提前预警
- **趋势预测**：精准预判未来12小时流量走势
- 话题深度分析 → 生成爆点提纲 + 完整写作指导
- 一键接入生成工作流 → 文章爆点拉满、时效性超强

> _本地复杂算法 + 大模型双重验证，拒绝过时内容！_

## 🎨 维度化创意变换系统（突破AI创作边界）

同一素材，瞬间变身多种风格！

**适用场景**：

- 内容创作者：一篇素材 → 公众号/小红书/抖音多版本
- 营销/教育：针对不同人群/视角调整表达
- 脑洞爱好者：李白穿越现代、魔幻现实主义书信体……

> 想象一下：李白用魔幻现实主义书信体，向现代旅行者介绍古代长安 → 这就是 AIWriteX 的无限创意！

---

### 更多功能（配置）

通过 `config.yaml` 和 `aiforge.toml` 配置文件，实现高度个性化的功能（推荐使用界面/软件模式编辑配置），以下是关键配置项说明：

- **`config.yaml` 配置项**

| 配置项                         | 说明                                                                         |
| ------------------------------ | ---------------------------------------------------------------------------- |
| **platforms**                  | 设置各平台热搜话题随机选取权重，控制选用优先级                               |
| **wechat**                     | 支持配置多个微信公众号（自动发布时，**必填**`appid`、`appsecret`、`author`） |
| **wechat.credentials**         | `call_sendall`、`sendall`、`tag_id`用来控制群发情况（仅适用于认证号）        |
| **api**                        | 支持多种大模型平台，**必填**`api_key`                                        |
| **api.api_type**               | 支持多个大模型平台，修改 `api_type` 切换平台，如OpenRouter                   |
| **api.OpenRouter.model_index** | 修改 `model_index` 选择平台内具体模型                                        |
| **api.OpenRouter.model**       | 支持多种模型（如openrouter/deepseek/deepseek-chat-v3-0324:free）             |
| **api.OpenRouter.key_index**   | 修改 `key_index` 切换账号（充分利用免费额度，付费账号无需多个）              |
| **api.OpenRouter.api_key**     | 支持多个 OpenRouter `api_key`                                                |
| **img_api**                    | 图片生成模型，用于公众号封面图                                               |
| **img_api.api_type**           | `ali`（需要填写`api_key`）或`picsum`（随机图片）                             |
| **img_api.picsum**             | 随机图片生成方式，降低生成图片消耗                                           |
| **use_template**               | 是否使用内置模板 ，不使用则AI根据要求直接生成文章HTML                        |
| **template**                   | 指定模板文件名（如 `template1`），为空或不存在时随机选择                     |
| **template_category**          | 模板分类，精确匹配话题类型（如健康养生），需分类下存在指定模板               |
| **use_compress**               | 是否压缩模板上传，降低 token 消耗                                            |
| **aiforge_search_max_results** | AIForge 最大返回搜索结果条数，控制搜索广度                                   |
| **aiforge_search_min_results** | AIForge 最小返回搜索结果条数，越大内容越丰富，但失败率越高                   |
| **min_article_len**            | 生成文章最小字数（默认 1000）                                                |
| **max_article_len**            | 生成文章最大字数（默认 2000）                                                |
| **auto_publish**               | 控制自动发布，勾选（true）自动发布，不勾选(false)需手动发布                  |
| **article_format**             | 生成文章格式（HTML、Markdown、txt）,非HTML时，只生成文章，不用模板           |
| **format_publish**             | 当文章格式为Markdown、txt时（微信不支持，直接发布混乱），格式化发布          |

- **`aiforge.toml` 配置项**

| 配置项                   | 说明                                                          |
| ------------------------ | ------------------------------------------------------------- |
| **default_llm_provider** | 使用模型提供商（默认 OpenRouter），可与 CrewAI 使用的模型不同 |
| **api_key**              | 模型提供商的 API Key（必填）                                  |
| **其他选填**             | 根据需要配置其他参数（选填），具体参考 UI 界面说明            |

> _1、aiforge.toml详细配置信息，参见[AIForge](https://github.com/iniwap/AIForge)项目主页_  
> _2、通过配置管理界面，可以详细了解关键参数的解释说明（建议运行UI界面模式）_  
> _2、⚠️ 微信公众号AppID/AppSecret、大模型提供商的API KEY是必填项，其他均可默认_

## 🚀 快速开始

### 软件模式

1. **请下载使用官方正版**：[点击下载](https://aiwritex.voidai.cc/)
2. 打开软件，进行必须要配置（_微信公众号AppID/AppSecret、大模型提供商的API KEY_）
3. 点击`开始执行`

### 开发模式

1. 克隆仓库：
   - `git clone https://github.com/iniwap/AIWriteX.git`
2. 安装依赖：

```shell
pip install uv
uv venv
uv pip install -r requirements.txt
```

3. 配置 `config.yaml`、`aiforge.toml`（_微信公众号AppID/AppSecret、大模型提供商的API KEY_）
4. 运行：
   - 有UI界面：`python .\main.py` (**推荐**)
   - 无UI界面：`python -m src.ai_write_x.crew_main` （**不支持文章、模板、配图管理**）

## 🔍 问题定位

遇到问题时，请根据运行模式查看日志并提交 [Issues](https://github.com/iniwap/AIWriteX/issues)

### 常见问题

请查看`close`(已关闭)的[Issues](https://github.com/iniwap/AIWriteX/issues?q=is%3Aissue%20state%3Aclosed)，以便了解大家常遇到且已经解决的问题。

## 🔮 微信公众号视觉风格设计预览

以下是精心微调、适配并发布的微信公众号模板，涵盖多个话题分类，欢迎预览！

### **绝美排版实例预览**

| 类别     | 风格分类  | 预览链接                                                      | 示例来源（公众号） |
| -------- | --------- | ------------------------------------------------------------- | ------------------ |
| 经典案例 | 美食文化  | [点击预览](https://mp.weixin.qq.com/s/-RIunPVHAIni4f4zO51Gvg) | AI夜航员           |
| 经典案例 | 涂鸦笔记  | [点击预览](https://mp.weixin.qq.com/s/2_zLwmuY_veug8t7xTxi4w) | AI夜航员           |
| 经典案例 | 漫画照片  | [点击预览](https://mp.weixin.qq.com/s/Z7vaed9yQBnD-Hw9JUXYwg) | AI夜航员           |
| 经典案例 | 风景杂志  | [点击预览](https://mp.weixin.qq.com/s/z1QFrGToSIvBXJxgcP-vNg) | AI夜航员           |
| 经典案例 | 广角摄影  | [点击预览](https://mp.weixin.qq.com/s/kgqcfsP5LZ8zRFv9qe6gDg) | AI夜航员           |
| 经典案例 | 电商样片  | [点击预览](https://mp.weixin.qq.com/s/9eyZMDgb0BTtCaa2_LG8Jg) | AI夜航员           |
| 经典案例 | ins信息流 | [点击预览](https://mp.weixin.qq.com/s/NjXLavDbdUzMEhmS8qk0rw) | AI夜航员           |
| 经典案例 | 视觉杂志  | [点击预览](https://mp.weixin.qq.com/s/Gv0v9SlORXBHdXpcoK1c4w) | AI夜航员           |
| 经典案例 | 旅行摄影  | [点击预览](https://mp.weixin.qq.com/s/kWWZ8DuCdxWaPAh3PQHc-Q) | AI夜航员           |
| 经典案例 | 商业大片  | [点击预览](https://mp.weixin.qq.com/s/KSfXKtNaC0WUgFCT90woQA) | AI夜航员           |

### 内置本地模板列表

- 分类模板

| 类别     | 模板名称 | 预览链接                                                      | 适用话题           |
| -------- | -------- | ------------------------------------------------------------- | ------------------ |
| 科技数码 | t1       | [点击预览](https://mp.weixin.qq.com/s/UCjBHaZ_EZVBdEaSEH-6mQ) | 科技前沿与数码评测 |
| 财经投资 | t1       | [点击预览](https://mp.weixin.qq.com/s/uTfYVXUG3_bjqSZ-uuJKeg) | 投资趋势与财经资讯 |
| 教育学习 | t1       | [点击预览](https://mp.weixin.qq.com/s/DOr7sSBQ2sYSqu4WmlH__g) | 学习方法与教育资讯 |
| 健康养生 | t1       | [点击预览](https://mp.weixin.qq.com/s/ZG6SFUYSZlrxyRw6_GH9yg) | 健康生活小贴士分享 |
| 美食旅行 | t1       | [点击预览](https://mp.weixin.qq.com/s/Lw29haJDk4uKODh7rlBOrw) | 美食推荐与旅行攻略 |
| 时尚生活 | t1       | [点击预览](https://mp.weixin.qq.com/s/ZgeIbl7l0KC1ex9ybrZBRg) | 时尚潮流与生活方式 |
| 职场发展 | t1       | [点击预览](https://mp.weixin.qq.com/s/-jJ-OxCr7BMaaYY68vSecQ) | 职场技能与职业规划 |
| 情感心理 | t1       | [点击预览](https://mp.weixin.qq.com/s/2j-C1tBWkpYIQhhR6tOwSg) | 情感故事与心理洞察 |
| 娱乐八卦 | t1       | [点击预览](https://mp.weixin.qq.com/s/3YeEH2Nvhsw8JqHIV0tftQ) | 最新娱乐圈动态速递 |
| 新闻时事 | t1       | [点击预览](https://mp.weixin.qq.com/s/M_l2LCJjiGmCWRvSm7lYvA) | 全球热点与时事分析 |

### 全自动发文效果预览

利用本地搜索与 AIForge 搜索生成时效性强的微信公众号文章效果预览：

| 类型     | 模板使用情况   | 预览链接                                                      | 说明                                 |
| -------- | -------------- | ------------------------------------------------------------- | ------------------------------------ |
| 自动发文 | 未使用模板     | [点击预览](https://mp.weixin.qq.com/s/KI4yHYrjAt8hd_nUEZP8kA) | AI根据要求生成文章，未使用本地模板   |
| 自动发文 | 使用 template9 | [点击预览](https://mp.weixin.qq.com/s/1XPMUPR09Ipuzm_yXgAvKw) | 使用本地模板 template9，视觉效果优化 |
| 自动发文 | 使用 分类模板  | [点击预览](https://mp.weixin.qq.com/s/Dys7eszxP33k6tonXMO1VA) | 指定分类`健康养生`，完美呈现         |

### 浅色/暗色模式下微信显示的效果对比

| 类型     | 主题模式 | 预览链接                                                      | 说明                                                           |
| -------- | -------- | ------------------------------------------------------------- | -------------------------------------------------------------- |
| 手动发文 | 浅色     | [点击预览](https://mp.weixin.qq.com/s/GOiOxGiym1dgqA77wrrFLw) | 浏览器最佳模板，但在手机上边距显得过大                         |
| 手动发文 | 浅色     | [点击预览](https://mp.weixin.qq.com/s/MFKPQIBdldyC_dxcpooOSw) | 统一调整边距后的效果，手机上看着更紧凑些，但丢失原来设计效果   |
| 手动发文 | 暗色     | [点击预览](https://mp.weixin.qq.com/s/jOWDpRSAw9twSptzZbBODg) | 原版为暗色，发到微信被强转（很难看），反而在浅色模式下正常显示 |

> _1、已适配模板可以比较好的显示在微信公众号上，有兴趣的可以继续微调内置模板（如边距等）_  
> _2、目前仅**尚未适配**下的模板未适配，需要适配才能完美显示（配置**分类随机**可能会随机到未适配模板）_  
> _3、目前模板无法很好的应对暗色模式，这和微信僵硬的处理有关_

## 📌 其他说明

### 关于微信公众号

以下是微信公众号开发及自动发文的问题说明：

- **CSS 限制**：
  - 微信发布文章时会移除 `position: absolute`（但保留 `position: relative`），需使用替代布局实现类似效果
  - 动画支持有限：`animateMotion` 可用，但 `animate` 仅支持透明度变化，需进一步测试（例如，template1 动画部分支持）
  - `<button>` 和 `background: url` 会被自动移除
  - `<linearGradient id="catGradient">` 的 `id` 会被移除，导致动画失效
  - `background: linear-gradient(90deg, #4b6cb7 0%, #ff9a9e 100%); -webkit-background-clip: text; color: transparent;` 手机/电脑主题暗色模式不支持渐变，浅色模式支持
  - 微信暗色模式会自动添加`js_darkmode__`，会导致背景色失效，暗色模式效果均不佳（!important 强制不使用暗色模式无效，会自动移除）
- **暗色/浅色模式**：目前生成更倾向于适用微信浅色模式，暗色模式效果稍差，后续需要找到二者更好的平衡点
- **文章显示问题**：发布的文章（未认证公众号）不会显示在公众号文章列表，但关注者会收到通知（每日3篇）
- **⚠️ 权限回收**：自 2025 年 7 月起，个人主体账号、未认证企业账号及不支持认证的账号将失去发布草稿权限，非认证公众号可能无法自动发文
- **⚠️ 微信公众号 IP 白名单问题**：
  - 微信 API 需将当前 IP 添加至后台白名单
  - 动态 IP 需手动更新白名单，或使用固定 IP 的代理
  - 解决方案：使用云服务器转发请求，或通过阿里云函数计算（免费，需注册阿里云）代理微信 API 请求
- **公众号文章列表显示问题**：
  - 未认证账号：API无法实现显示到公众号列表，只能通过后台操作
  - 认证账号：必须调用群发接口，才能显示到列表。is_to_all（True/False）以及不调用sendAll接口具体情况，请各位自行测试，支持配置这三种情况
  - is_to_all=False,且调用接口时，tag_id（用户标签群组ID）好像是必须填写
  - 关于此的 [官方解释](https://developers.weixin.qq.com/doc/service/guide/product/message/Batch_Sends.html)（愣是看的云里雾里，WDNMD，为什么会有这么逆天的产品）

> **⚠️ 注意**：2025 年 7 月后，非认证账号可能将面临自动化发布限制（只能发布到草稿，需要后台操作发布草稿，发布后会显示到公众号文章列表）。

## 📩 联系我们

如需了解配置详情或扩展、定制功能、商业授权，请联系QQ 522765228

## 📜 许可证 / License

- 👉**最近发现有人偷卖本项目，请认准官方淘宝店[墨智工坊](https://aiforge.taobao.com/)，请尊重知识产权，本项目禁止用于商业用途，仅限个人使用。**

本项目采用 [Apache License 2.0](./LICENSE) 开源，并附带额外使用限制，详见 [NOTICE](./NOTICE) 文件。

```markdown
📜 AIWriteX 附加使用条款  
版本 1.2，2025年7月15日  
版权所有 © 2025 iniwap  
联系邮箱：iniwaper@gmail.com / 522765228@qq.com

本项目在 Apache License 2.0 协议基础上，增加以下补充条款：

---

## 1. 非商业使用

您可以自由地出于非商业目的使用、修改软件，无需授权，前提是保留 LICENSE 和本 NOTICE 文件。

---

## 2. 分发与服务提供限制

未经版权所有人书面授权，禁止以下行为：

- 分发本项目或其衍生作品，包括但不限于复制、共享或通过任何方式传播软件；
- 利用本项目或其衍生作品提供面向第三方的服务，包括但不限于利用软件提供SaaS、API托管等服务。

📩 如需授权，请联系邮箱：iniwaper@gmail.com 或 522765228@qq.com  
非盈利性分发可申请免费授权，商业用途需申请付费授权。

---

## 3. 允许的个人盈利使用

您可以出于个人盈利活动（例如个人项目或自由职业工作）使用软件，无需事先授权，前提是此类使用**不涉及分发或向第三方提供服务**，并保留本文件与 LICENSE。

---

## 4. 署名和版权信息要求

在所有使用场景中，必须保留以下内容：

- LICENSE 文件；
- 本 NOTICE 文件；
- 原始版权声明。

不得删除或更改这些声明，违反将自动终止使用授权。

---

## 5. 终止条款

如发现您违反上述任一条款，您的授权将被立即终止，且可能构成侵权责任。

---

## 6. 法律声明

本条款不构成法律建议。如您不确定是否符合使用条件，请联系版权所有人进一步确认。
```
