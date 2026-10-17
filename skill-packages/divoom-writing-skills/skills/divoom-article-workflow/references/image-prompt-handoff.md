# 配图 prompt 随文章 JSON 交付

本部署已选择 `config/site.json` 的 `image_prompt_delivery: html_comments_v1`。用户仍只给标题、只收一份文章数组 JSON。没有待配图时不为了该模式强行安排图片；有图位时，英文 prompt 留在正文的结构化 HTML 注释中。

## 写作前与写作时

大纲增加 `image_prompt_delivery: html_comments_v1`；在既有 `visual_plan` 的 pending 项增加 `aspect_ratio`、`filename`、`prompt`、`alt`、`title`。其他四类可以使用同样的 visual_plan，不要求采用 Technology 专属整套 FX 编辑协议。每个 prompt 要独立可用：说明任务、具体画面、构图、风格、准确标签和不能虚构的内容；不能写“如上文”“照参考图”但不给另一个会话必要上下文。

目标比例和建议文件名是制作要求，不是某个图像 API 保证接受的参数。精确文字和图表需要核对，不能承诺生成器一次产生正确小字、数量、标签和型号外观。设计参照 [OpenAI 图像提示词指南](https://developers.openai.com/api/docs/guides/image-prompting)。

正文阶段用 `workflow.render_image_prompt(row)` 生成注释，放在相应图位，不能手工把危险 HTML 或任意评论夹进去。只有以下保留标记合法：

```html
<!-- DIVOOM_IMAGE_PROMPT_V1 {"id":"figure-name","role":"explanatory","section":"section-id","aspect_ratio":"16:9","filename":"figure-name.png","prompt":"Self-contained English image brief.","alt":"Accurate intended image description","title":"Short image title"} -->
```

banner 图位注释放在文章最前、两个实质开头段之前；正文图注释放在绑定的小节中。注释不会在普通网页中渲染成文字，但能在原 JSON 的 HTML 或保存后的文章源码中复制。没有素材就不创建 img、不发明 CDN URL。omitted 不发 prompt，ready 采用实际图而不重复等待生成的指令。

## 给另一个图像会话

用户可以交付整份 JSON，并要求：“只读取 html代码 中 DIVOOM_IMAGE_PROMPT_V1 注释，按 id 逐张使用 prompt 生成图片，目标比例参考 aspect_ratio，并保留 id 与建议 filename 对应关系；不要改写文章或编造测量数据。”也可以只复制其中一个 prompt。此处仅交付提示词，不自动调用图像工具、上传媒体或发布。

图生成后检查画面与文字、数值及 alt 是否一致，必要时修改或重做；上传到用户媒体库，获得实际 URL，再把原注释替换为真实 img。banner 对应图片用最前面的独占 p，供现有 Liquid 提取；正文图留在原图位。完成后重新按正文→链接→审核封存，旧审核不能覆盖新图片。

## 审核与兼容范围

注释中的 prompt 不计正文词数、摘要或可读文本，但纳入正文指纹；改了 prompt 也要重新审核。每个 pending 图位与实际注释一一对应，检查 id、role、section 和完整内容，不能漏发或多发。普通任意注释仍被禁止；发布 JSON 不增加新的顶层键。

本机解析器把 HTML 作为 bodyHtml 保留；每次交付仍需用实际解析器验证。未经 Shopify 写入后回读，不声称其所有编辑器/保存路径必定永久保留注释。原 JSON 是可靠的 prompt 备份；用户可直接从该文件复制，不必依赖网页显示。隐藏注释不等于保密存储。
