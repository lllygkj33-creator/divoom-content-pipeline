# 配图 prompt 随文章 JSON 交付

本部署已选择 `image_prompt_delivery: html_comments_v1` 与 `image_slot_delivery: visible_alt_v1`。用户仍只给标题、只收一份文章数组 JSON。通用 Banner 由 Liquid 固定输出 `https://cdn.shopify.com/s/files/1/0082/4105/3814/files/DIVOOM-blog-banner.jpg?v=1792205040`，文章 HTML 不再含 Banner 或 Banner prompt，也不从正文第一张图提取。没有必要图位就不强行配图。

## 写作前与写作时

大纲声明两个交付模式；visual_plan 中正文图按出现顺序增加 slot：images_1、images_2。pending 项同时带 aspect_ratio、filename、prompt、alt、title，语义 id 与实际文件名保持对应，不能因为增加编号随意改掉已生成图片的文件名。其他四类也可使用 visual_plan，不要求采用 Technology 专属整套 FX 编辑协议。每个 prompt 要独立可用：说明任务、具体画面、构图、风格、准确标签和不能虚构的内容；不能写“如上文”而不给另一个会话必要上下文。

目标比例和建议文件名是制作要求，不是某个图像 API 保证接受的参数。精确文字和图表需要核对，不能承诺生成器一次产生正确小字、数量、标签和型号外观。设计参照 [OpenAI 图像提示词指南](https://developers.openai.com/api/docs/guides/image-prompting)。

正文阶段用 `workflow.render_image_slot(row)` 在相应图位生成可见编号段和隐藏注释，不能手工夹入危险 HTML 或任意评论：

```html
<p>images_1：Accurate intended image description</p>
<!-- DIVOOM_IMAGE_PROMPT_V1 {"id":"figure-name","role":"explanatory","section":"section-id","aspect_ratio":"16:9","filename":"figure-name.png","prompt":"Self-contained English image brief.","alt":"Accurate intended image description","title":"Short image title"} -->
```

编号段放在绑定正文小节的实际插图位置，xxx 必须是该图片的 alt，不能只写“待补图”。编号段在编辑器和普通网页中可见，便于后台定位；prompt 注释前台不可见。没有素材就不创建 img、不发明 CDN URL。omitted 不发标记或 prompt；ready 使用实际图。即便先补了 images_1，计划里其他图片原有编号仍保留，不把 images_2 改号。

## 给另一个图像会话

用户可以交付整份 JSON，并要求：“只读取 html代码 中 DIVOOM_IMAGE_PROMPT_V1 注释，按 id 逐张使用 prompt 生成图片，目标比例参考 aspect_ratio，并保留 id 与建议 filename 对应关系；不要改写文章或编造测量数据。”也可以只复制其中一个 prompt。此处仅交付提示词，不自动调用图像工具、上传媒体或发布。

图生成后检查画面与文字、数值及 alt 是否一致，必要时修改或重做；上传媒体库获得实际 URL，再将对应 images_N 编号段及紧随的 prompt 注释一起替换为 `<p><img src="真实图片 URL" alt="对应 alt" title="对应 title"></p>`。正文图留在原图位；不要在正文插入通用 Banner。编号是人工换图定位，不会自动从媒体库猜 URL。完成后更新该项 ready/src，重新按大纲→正文→链接→审核封存；旧审核不能覆盖新图片。

## 审核与兼容范围

prompt 和 images_N 定位文字不计编辑正文词数或事实证据，但都纳入正文指纹。pending 图位、可见编号和实际注释一一对应，检查编号、alt、章节及完整 prompt，不能漏发或多发；换成 ready 图片后不留该编号段。普通任意注释仍被禁止；文章 JSON 不增加新的顶层键。

本机解析器把 HTML 作为 bodyHtml 保留；每次交付仍需用实际解析器验证。未经 Shopify 写入后回读，不声称其所有编辑器/保存路径必定永久保留注释。原 JSON 是可靠的 prompt 备份；用户可直接从该文件复制，不必依赖网页显示。隐藏注释不等于保密存储。
