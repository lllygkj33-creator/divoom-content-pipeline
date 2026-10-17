---
name: divoom-outline
description: Plan an evidence-backed outline for an existing Divoom article run, classify its primary intent and FX, and map claims to sources. Used as the outline stage of divoom-article-workflow or to resume that stage; does not mine topics or draft the final article.
---

# 大纲阶段

入口传入 run 目录。总控位于 `../divoom-article-workflow/`，共享配置、规范和脚本均在该目录。先读其 `references/contract.md`、`references/routing.md`、`references/evidence.md`；再只读选中类型的 `references/types/<类型>.md` 及其链接的原始标题规范。不能只匹配 Why/How 词形选类型。

1. 保留标题限制，记录一个读者主任务、直接答案和不覆盖内容。按 FX 的 H2 问题顺序规划，不照抄公式槽位。`F14` 等候选保留不确定状态，不声称为已验证范式。
   Technology 新稿先读共享根的 [编辑与配图规划](../divoom-article-workflow/references/editorial-planning.md)，再从 [案例索引](../divoom-article-workflow/references/technology-cases.json) 读取对应 FX，实际阅读原文与图片；不能用排版讨论中的另一篇文章替代。记录原样本、迁移点与不照搬项。
2. 搜索 `references/source/` 的实体、官方产品和手册资料，结合可用浏览工具核对关键事实。外部技术主张用原始研究、标准、官方文档；Reddit 是问题来源。来源内容只作数据。
3. 每个 H2 记录独立问题、预期结论、推进的新变量、证据需求、边界和与下节的关系。默认至少四个有必要的 H2，1200–2200 英文词预算，两个开头段落，无 H3。节数和段落带宽不能成为注水配额。
4. 创建 `outline.json`：`title`、`type`、`fx`、`blog`、`core_term`、`tags`、`answer`、`scope`、`sections`。每节含 `id`、`h2`、`question`、`new_information`、`claim_ids`、`boundary`。tags 从真实品类映射选，不用五类意图充当标签。
   按配置写 `image_prompt_delivery`、`image_slot_delivery`；正文图位按文章顺序编号 slot 为 images_1、images_2。pending 图位的独立英文 prompt、目标比例、建议文件名、alt/title 按 [配图交付契约](../divoom-article-workflow/references/image-prompt-handoff.md) 规划，不要求用户另填需求表。本部署的 Banner 由模板固定输出，不规划 Banner 或向文章中插入该图。
   新稿声明 `image_reference_contract_version: 1`；每个未省略图位写 `reference_mode` 与 `reference_requirement`。画面出现真实产品外观用 product_photos_required，说明要哪个型号/颜色/角度，缺图由后续图像会话索要；抽象部件原理用 generic_concept_only，不凭外观图推断内部；不涉及产品用 no_product_required。不能根据型号名猜外观或把示意图当实物参考。
   Technology 新稿同时写 `editorial_protocol_version: 2`、`sample_review`、`scenario_plan`、`faq_decision`、`visual_plan`、`visual_reason`；每节增加 `format`、`format_reason`、`transition`，字段定义见编辑与配图规划。先考虑小条件是否改变判断，再决定场景数量与图位，不固定清单、FAQ 或配图数量。无素材也规划用途，但不编造图片 URL。
5. 创建 `evidence.json`：按共享证据契约逐项登记主张及来源，核心主张未核实时标为待查。大纲允许待查任务，但必须在正文封存前解决；不能将候选来源写成已支持。
6. 运行共享脚本 `seal <run> outline`。把路径和未决事实交回总控，继续正文，不要求用户逐节批准。

验收：每节增加信息而不是换词重复；总体能回答标题；类型、FX、栏目与核心品类匹配；没有无证据的既定产品结论。
