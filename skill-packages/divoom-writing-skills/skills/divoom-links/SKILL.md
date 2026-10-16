---
name: divoom-links
description: Insert and verify contextual internal and primary-source external links in an existing Divoom draft, maintaining a link ledger and claim scope. This is the links stage of divoom-article-workflow; it does not publish or rewrite the article's purpose.
---

# 链接阶段

入口是已封存 draft 的 run。读共享根 `../divoom-article-workflow/references/links.md`、`references/publisher.md`、所选类型锚文本规范与 `references/quality.md`。运行共享 `workflow.py status <run>` 验证上游。

1. 在已存在、确需延伸或证据的句子中选位置。内链检索随包博客/产品/品类索引；排除促销集合、隐藏/草稿/预览 URL、自链和无关落地页。来源库是候选池，不代表今天已验证。
2. 实际读取目标正文，核对锚文本描述的任务、目标主张和时效。未知/403/无法读取不能写 checked；寻找可验证替代，否则删去链接，非关键内链机会登记 pending。
3. 外链优先原始权威来源。能打开只证明可达，不能证明因果、数字或型号适用；逐项核对支持关系。Momcozy/KTC 示例链接不能进入成稿。一般原理外链不得替品牌补参数。
4. 插入 `<a href="真实URL" title="目标内容的自然说明">自然锚文本</a>`。第三方链接加 `target="_blank" rel="noopener noreferrer nofollow"`。站内优先真实根相对路径；自家域名按配置边界判断，不按字符串包含匹配。不要生成模板变量 URL。
5. 写 `links.json` 数组。每项含 `href`（与 HTML 一致）、`kind`（internal/external/pending）、`anchor`、`section`、`purpose`、`checked_at`、`verification`（verified/unverified）、`source_locator`（实际读取位置）。pending 使用空 href、不能留在 HTML；verified 仅代表已检查目标内容，事实仍由 evidence 表逐项审视。
6. 只改必要锚文本。若为了补链改变了结论、数字、FAQ 或正文结构，更新 evidence 并回正文阶段重新封存，不能跳过上游重审。仅插锚不改变论证时可直接 `seal <run> links`；该动作把最终链接 HTML 纳入新指纹。
7. 按 quality 规范审核最终稿，写 review.json；由总控完成 review 封存和 export。不要以“链接数量达标”代替语义质量。
