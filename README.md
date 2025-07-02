# CrewAI微信公众号全自动生成排版发布工具

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![PySimpleGUI](https://img.shields.io/badge/PySimpleGUI-4.60.5+-green) ![CrewAI](https://img.shields.io/badge/CrewAI-0.102.0+-red) ![AIPy](https://img.shields.io/badge/aipyapp-0.1.27+-pink)  ![PyWinGUIBuilder](https://img.shields.io/badge/PyWinGUIBuilder-1.0.0+-yellow) ![Stars](https://img.shields.io/github/stars/iniwap/ai_auto_wxgzh?label=收藏)

基于 CrewAI 、AIPy 的微信公众号自动化工具软件，自动获取抖音、微博等平台热点，融合“搜索+借鉴+AI”，生成**高时效（实时）**、高质量、排版酷炫的文章并发布到微信公众号。👉[高大上文章排版预览](#微信公众号模板效果预览)

**喜欢项目？点个 Star 支持一下吧！🌟**

![界面预览 / Interface Preview](image/preview.jpg)

## 🎯项目背景
为了学习CrewAI，特开发了这个小项目。最后才发现公众号（未认证）限制巨多，有认证微信公众号的可以更好的发挥这个项目的作用。

## 💎基本功能
系统提供以下核心功能，支持自动化、个性化文章生成与发布，适合技术与非技术用户：

- **自动获取热门话题**：从各大平台实时抓取热门话题，确保文章标题/内容紧跟潮流。
- **自动生成与排版**：利用 CrewAI 多角色协作，自动生成文章并完成酷炫排版。
- **自动发布图文**：一键发布图文消息到微信公众号，简化运营流程。
- **💡 实时文章生成**：采用多重搜索策略（本地缓存+在线搜索），拒绝过时内容，确保文章时效性。
- **💡 支持指定话题与参考文章**：允许用户自定义文章话题或提供参考文章，结合 AI 生成高质量内容。
- **UI 可视化管理**：提供直观界面，方便配置管理、文章发布管理和模板管理，操作简单高效。
- **支持两种运行模式**：
  - **开发模式**：适合技术用户，支持灵活定制开发，适配复杂需求。
  - **软件模式**：无需开发环境，安装软件并填写配置即可，适合非技术用户快速上手。

### 个性化功能（配置）

通过 `config.yaml` 和 `aipyapp.toml` 配置文件，系统支持高度个性化的功能定制，推荐使用界面/软件模式编辑配置，操作更友好。以下是关键配置项说明：

- **`config.yaml` 配置项**

| 配置项                     | 说明                                                                         |
|----------------------------|-----------------------------------------------------------------------------|
| **platforms**              | 设置各平台热搜话题随机选取权重，控制选用优先级                                  |
| **wechat**                 | 支持配置多个微信公众号（ 自动发布时，**必填**`appid`、`appsecret`、`author`）   |
| **api**                    | 支持多种大模型平台，**必填**`api_key`                                         |
| **api.api_type**           | 支持多个大模型平台，修改 `api_type` 切换平台，如OpenRouter                     |
| **api.OpenRouter.model_index** | 修改 `model_index` 选择平台内具体模型                                     |
| **api.OpenRouter.model**      | 支持多种模型（如openrouter/deepseek/deepseek-chat-v3-0324:free）           |
| **api.OpenRouter.key_index** | 修改 `key_index` 切换账号（利用免费额度）                                   |
| **api.OpenRouter.api_key** | 支持多个 OpenRouter `api_key`                                               |
| **img_api**                | 图片生成模型，用于公众号封面图                                                |
| **img_api.api_type**       | `ali`（需要填写`api_key`）或`picsum`（随机图片）                             |
| **img_api.picsum**         | 随机图片生成方式，降低生成图片消耗                                            |
| **use_template**           | 是否使用内置模板 ，不使用则AI根据要求直接生成文章HTML                          |
| **template**               | 指定模板文件名（如 `template1`），为空或不存在时随机选择                        |
| **template_category**      | 模板分类，精确匹配话题类型（如健康养生），需分类下存在指定模板                   |
| **need_auditor**           | 是否启用质量审核 agent/task，关闭可降低 token 消耗（默认关闭）                |
| **use_compress**           | 是否压缩模板上传，降低 token 消耗                                            |
| **use_search_service**     | 启用本地缓存代码优先的搜索扩展，首次成功率较低，后续效率高（默认关闭）           |
| **aipy_search_max_results**| AIPy 最大返回搜索结果条数，控制搜索广度                                      |
| **aipy_search_min_results**| AIPy 最小返回搜索结果条数，越大内容越丰富，但失败率越高                       |
| **min_article_len**        | 生成文章最小字数（默认 1000）                                               |
| **max_article_len**        | 生成文章最大字数（默认 2000）                                               |
| **auto_publish**           | 控制自动发布，勾选（true）自动发布，不勾选(false)需手动发布                   |

- **`aipyapp.toml` 配置项**

| 配置项                     | 说明                                                                 |
|----------------------------|----------------------------------------------------------------------|
| **default_llm_provider**   | 使用模型提供商（默认 openrouter），可与 CrewAI 使用的模型不同。         |
| **api_key**                | 模型提供商的 API Key，必填。                                          |
| **其他选填**               | 根据需要配置其他参数，具体参考 UI 界面说明。                          |

*1、通过配置管理界面，可以详细了解关键参数的解释说明（建议运行UI界面模式）*
*2、Claude 3.7 生成的模板可免费通过 Poe 平台生成，放置到 `knowledge/` 对应分类文件夹*
*3、微信公众号AppID/AppSecret、CrewAI和AIPy使用的大模型提供商的API KEY是必填项，其他可默认*

## 🚀 快速开始
### 开发模式
1. 克隆仓库：
    - `git clone https://github.com/iniwap/ai_auto_wxgzh.git`
2. 安装依赖：
   - `pip install -r requirements.txt`
   - `pip install PySimpleGUI-4.60.5-py3-none-any.whl`
4. 配置 `config.yaml`、`aipyapp.toml`（*微信公众号AppID/AppSecret、CrewAI和AIPy使用的大模型提供商的API KEY*）
5. 运行：
    - 有UI界面：`python .\main.py -d` (**推荐**)
    - 无UI界面：`python -m src.ai_auto_wxgzh.crew_main` （**不支持文章、模板管理**）

### 软件模式
1. 请从网盘下载`微信公众号AI工具_云盘版_Setup.exe` 👇，并安装
    - [移动云盘 提取码:1sgp](https://caiyun.139.com/w/i/2nQQRmAhg7Ffl)
    - [Microsoft OneDrive](https://1drv.ms/u/c/c831e3cc9be11110/Eaip7dg-hKBNqJRWQ_suJwgBh5naslCIumQy-2sC2D8KYQ?e=N4Oi5Z)
    - [Google Drive](https://drive.google.com/file/d/1NlY5jV8adIbpFv5_eWyk40kvzhku_eL0/view?usp=sharing)
2. 打开软件，进行必须要配置（*微信公众号AppID/AppSecret、CrewAI和AIPy使用的大模型提供商的API KEY*）
3. 点击`开始执行`

## 🔍问题定位
### 开发模式
1. 界面模式执行：**查看logs目录下的文件**，如`UI_2025-05-20.log`，提交issue
2. 无UI界面模式：**查看命令行输出**，复制提交issue
- 不同的CrewAI版本日志输出差别比较大，可临时更换下CrewAI版本：
```shell
pip  uninstall crewai
pip  install crewai==0.102.0
```
*此版本会输出过程日志，仍看不出问题的，可将日志提交Issue*  
- 恢复到最新版本：
```shell
pip  uninstall crewai
pip  install crewai
```
### 软件模式
请选择`文件->日志->UI_2025-05-20.log（选择当天的日志）`，点击打开、复制、提交Issue

### AIPy相关问题
1. 搜索分两种模式：缓存和非缓存模式，前者仅使用AIPy（缓存成功搜索代码，初次缓慢），后者同时使用本地搜索+AIPy（成功率更高）
2. 不是所有话题搜索引擎都能搜索到，如果失败属于正常现象，任务会继续执行的；
3. 搜索代码生成过程中可能会有错误，请忽略（有自动纠错机制，后续运行会修复），不影响整体运行；
4. 生成搜索代码有随机性，由于采用了缓存机制，多运行几次，搜索效果会提升；
5. 由于搜索引擎的限制以及人工验证的存在，会出现搜索不到结果的情况，请忽略，不影响整体运行。


⚠️**免费的OpenRouter有可能服务不正常，无法正确运行（这种情况只能等用的人少的时候再试）；一个账号首次执行成功率比较高，后续执行使用模板时候可能被截断。**
*这应该跟其最近修改了付费策略有关系，免费的终究是没那么好用。*

## 🔮微信公众号模板效果预览

以下是精心微调并发布的微信公众号模板，涵盖多个主题，欢迎体验！

### 内置本地模板列表

- 分类模板

| 类别       | 模板名称 | 预览链接                     | 描述                     |
|------------|----------|------------------------------|--------------------------|
| 健康养生   | t1       | [预览](https://mp.weixin.qq.com/s/ZG6SFUYSZlrxyRw6_GH9yg) | 健康生活小贴士分享       |
| 娱乐八卦   | t1       | [预览](https://mp.weixin.qq.com/s/3YeEH2Nvhsw8JqHIV0tftQ) | 最新娱乐圈动态速递       |
| 情感心理   | t1       | [预览](https://mp.weixin.qq.com/s/2j-C1tBWkpYIQhhR6tOwSg) | 情感故事与心理洞察       |
| 教育学习   | t1       | [预览](https://mp.weixin.qq.com/s/DOr7sSBQ2sYSqu4WmlH__g) | 学习方法与教育资讯       |
| 科技数码   | t1       | [预览](https://mp.weixin.qq.com/s/UCjBHaZ_EZVBdEaSEH-6mQ) | 科技前沿与数码评测       |

- 其他模板

| 模板名称   | 预览链接                     | 描述                     |
|------------|------------------------------|--------------------------|
| template1  | [预览](https://mp.weixin.qq.com/s/9MoMFXgY7ieEMW0kqBqfvQ) | 通用模板，无风格限定     |
| template2  | [预览](https://mp.weixin.qq.com/s/0vCNvgbHfilSS77wKzM6Dg) | 通用模板，无风格限定     |
| template3  | [预览](https://mp.weixin.qq.com/s/ygroULs7dx5Q54FkR8P0uA) | 通用模板，无风格限定     |
| template4  | [预览](https://mp.weixin.qq.com/s/-SexfJ1yUcgNDtWay3eLnA) | 通用模板，无风格限定     |
| template5  | [预览](https://mp.weixin.qq.com/s/pDPkktE_5KnkQkJ1x2-y9Q) | 通用模板，无风格限定     |
| template6  | [预览](https://mp.weixin.qq.com/s/7F_Qdho-hzxeVV6NrsPmhQ) | 通用模板，无风格限定     |
| template7  | [预览](https://mp.weixin.qq.com/s/ug7NseZDziDMWBVwe3s1pw) | 通用模板，无风格限定     |
| template8  | [预览](https://mp.weixin.qq.com/s/uDjKVrWop4XNrM-csQ-IKw) | 通用模板，无风格限定     |
| template9  | [预览](https://mp.weixin.qq.com/s/EVhL67x8w35IuNnoxI1IEA) | 通用模板，无风格限定     |
| template10 | [预览](https://mp.weixin.qq.com/s/pDN5rgCgz0CbA8Q92CugYw) | 通用模板，无风格限定     |

### 全自动发文效果预览

全自动发文系统利用本地搜索与 AIPy 技术生成时效性强的文章内容，并随机选择上述模板进行填充和发布。

| 类型           | 模板使用情况 | 预览链接                     | 描述                           |
|----------------|--------------|------------------------------|--------------------------------|
| 自动发文       | 未使用模板   | [预览](https://mp.weixin.qq.com/s/KI4yHYrjAt8hd_nUEZP8kA) | AI根据要求生成文章，未使用本地模板        |
| 自动发文       | 使用 template9 | [预览](https://mp.weixin.qq.com/s/1XPMUPR09Ipuzm_yXgAvKw) | 使用本地模板 template9，视觉效果优化   |

*有兴趣的可以继续微调（如边距等），上面的模板可以比较好的显示在微信公众号上了。执行代码时，自动随机选择模板，生成的文章会自动选取填充上面的模板发布文章。*

 ## 📢后续计划
 - **适配分类模板**
- 增加功能，使输出效果更好
- 优化模板，减少token消耗（持续）
- 优化处理，减少不必要的token消耗（持续）
- 增加容错，提升成功率（持续）

## 📌其他说明
### 关于微信公众号
~~由于不熟悉微信公众号开发，哪位知道如何正确的使用“position: absolute;”，麻烦提一个issue 或者PR给我。
这个很必要，因为生成的模板都使用了，浏览器显示正常，但是发布到微信公众号，就变成了垂直排列，无法作为背景。整体效果差太多了。~~

经过分析，发现以下问题：
- 发布文章后，微信会自动移除position: absolute（position: relative好像不会移除） ，必须通过其他方式实现
- 微信公众号支持animateMotion，不支持animate（经测试只支持透明度变化动画，也不全是模板1的动画没问题，这个需要继续测试）
- 调整好的模板，效果虽然不能完全和原来的相比，但是总体还不错（有背景装饰、有动画）
- 不支持button，会被自动移除
- 会自动移除 background: url
- `<linearGradient id="catGradient">`，此类动画，id会被自动移除，动画会失效
- 最近发现发布的文章不会显示到公众号文章列表，但是有时会收到消息通知（关注者），之前完全没通知（每天大概3-5篇的，后续不会有通知）
-**【噩耗】：注：2025年7月起，个人主体账号、企业主体未认证账号及不支持认证的账号将被回收发布草稿的调用权限，这就意味着非认证公众号没法自动发文了。（垄断真该死啊！）**
- **微信API访问IP白名单问题，这个有点恶心，只能使用的时候把当前IP添加进去；如果有代理直接开代理吧，使用那个固定IP即可（如果是固定的话）**
- **如果有云服务器，做个转发就行了；还可以使用阿里云函数计算代理微信API请求，免费的，但需要注册阿里云**
### 关于软件模式
- 为了支持软件模式，让大家更简单的体验项目，调试花费了很长时间(CrewAI使用大量资源，一个个试探出来的)，给个star支持下吧~
- 家庭网络IP可能不固定，通过API发微信公众号，需要将IP添加进微信公众号后台白名单（没有固定IP只能变化时添加，有代理的使用代理的固定IP即可）
- **不需要软件模式（UI）代码（运行于服务器），删除gui以及main代码，直接无UI模式运行即可**
- 抓紧体验吧~更多功能开发中...
