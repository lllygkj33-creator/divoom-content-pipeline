# 发布程序内容契约

依据用户说明及 2026-10-16 本机 `D:/divoom-publisher/src/lib/shopify-json.ts` 实读。发布程序不属于本包，不修改，不调用其发布 API。隐藏/无排期由用户程序的其他部分控制，不向内容 JSON 注入 published/published_at/schedule 等字段。

唯一默认输出是非空数组，即使只有一篇。每项精确使用：

```json
{
  "blog title": "完整英文标题",
  "url": "lowercase-english-slug",
  "meta title": "忠实且简洁的SEO标题",
  "meta description": "不超过160个UTF-16字符",
  "summary": "不超过160个UTF-16字符",
  "author": "Divoom Professional Team",
  "tags": ["真实品类标签"],
  "blog": "Technology Hub",
  "html代码": "受约束的完整正文HTML"
}
```

`url` 是 handle，不是完整 URL，也不是 /blogs/...。正则 `^[a-z0-9]+(-[a-z0-9]+)*$`。所有字段非空；tags 是不重复的品类数组。若有明确且已核实的用户要求，可额外带 template、reviewer、related_products；不得猜 template 后缀。默认不带 optional 字段。

## HTML

- 禁止 H1（模板负责）以及本包正文风格禁止 H3。两个实质开头段落，至少四个有内容 H2；原解析器可用 `[[related_products_1]]` 绕过 H2 检查，本包默认不使用该捷径，不虚构商品。
- img：src 为真实 HTTP(S) 或根相对路径，非空 alt/title。没有图片就不放，不放假封面/占位图片。通用 Banner 已固定在模板，正文不含 Banner；第一张正文图不提取、不删除，封面只用于栏目卡片。
- a：非空 href/title。第三方 HTTP(S) 必须 `target="_blank" rel="noopener noreferrer nofollow"`，内部路径无需新窗口。协议相对路径 `//evil.example` 不能当作站内。禁止 javascript/data、变量 URL、草稿预览、未解析标记。
- 不嵌 script/style/iframe/form，不放事件属性、不改变主题字体/CSS。允许 p、article、div、span、h2、ul、ol、li、strong、em、b、i、blockquote、table/thead/tbody/tfoot/tr/th/td、caption、figure/figcaption、img、a、br、hr、code、pre、sup、sub、s、del。所有非 void 标签正确闭合，H2 非空，id 唯一。
- `html代码` 不重复 H1/作者/目录/免责声明/Editor's Recommendation；固定模块由 Liquid 模板输出。用户此前的 `<span>product_card</span>` 只在明确要求且 custom.product_card 已有值时使用，不能默认生成。
- 配置的 `html_comments_v1` 模式只允许 [结构化配图注释](image-prompt-handoff.md)。prompt 在原图位随 html代码 交付，前台不渲染；配套 `visible_alt_v1` 输出可见 `<p>images_1：图片 alt</p>` 供后台替换。编号、alt 和位置必须与计划对应，定位段不用于正文词数或事实证据；不新加 JSON 顶层键。未知任意注释依然非法。没有真实 URL 就不输出 img；实际 Shopify 保存后注释是否保留需回读核实，原 JSON 保留完整备份。

## 部署路由差异

显式 `blog` 优先于 class 推断，但上传界面手动选择的 blog 可覆盖 JSON。默认用中性 `<article class="divoom-editorial-article">`，不冒充尚未登记的栏目 class。精确栏目名取 config/site.json。

本机公开模板配置仍有 Example Blog A 等示例栏目、自家域 example-store.test；不能把这些样本名称/域名写进 Divoom 稿件。本包使用 Divoom 真实博客名称与根相对内链。实际上传须选择允许自选 Blog 的目标，或已映射的 Divoom 栏目；内容契约通过不代表部署配置已同步。

单对象页面 schema、社区来源、Discord、VS 等不在默认工作流。不要因为给定示例包含它们而输出 Page、published:true 或 community_source。
