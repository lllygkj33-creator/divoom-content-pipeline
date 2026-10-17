---
name: divoom-draft
description: Draft or revise the canonical English HTML body for an existing sealed Divoom outline using its five-type writing rules and claim evidence. This is the writing stage of divoom-article-workflow; it does not insert final links or publish.
---

# 正文阶段

入口是已封存 outline 的 run。共享根 `../divoom-article-workflow/`。读 `references/contract.md`、选中类型完整规范、`references/evidence.md`、`references/product.md` 和 `references/publisher.md`。先运行 `workflow.py status <run>` 确认上游指纹未变。

1. 消解核心证据缺口。不要把“在实体库中出现”当作机制已成立；核对具体主张与型号/场景的适用范围，记录对应原文定位。不能查到的数字删除；删掉导致标题承诺失效时停止并说明。
2. 按类型撰写 `body.html`，从直接回答开始，以既定 H2 推进。两段开头；1200–2200 英文词；无 H1/H3。段落必须新增变量、判据或行动结果，表格/清单/FAQ 只在任务需要时使用。FAQ 在此完成，之后不能绕过审核追加。
   Technology 按 [编辑与配图规划](../divoom-article-workflow/references/editorial-planning.md) 执行：段落职责随问题安排，不给每节套同样四段；区分真正重复和必要限定。场景必须说明改变条件、保持条件和可观察差异；没有新增判断则合并。现有样本有无 FAQ 都不构成所有稿件的配额。
3. 语义 HTML 仅使用共享白名单标签。H2 用大纲 section id；表格含 th scope；图片只在用户有真实素材时添加，alt/title 非空。本部署的通用 Banner 已固定在 Liquid，正文不写 Banner 图片或 Banner prompt，第一张正文图必须留在正文；封面只用于栏目卡片。作者、面包屑、目录、免责声明和底部推荐由模板负责，不写入正文。
   图片仅使用 visual_plan 中 ready 的真实素材，实际查看画面并核对图中数字、标签、外观和 alt。pending 按 [交付契约](../divoom-article-workflow/references/image-prompt-handoff.md) 用 render_image_slot 输出可见的 images_1：alt 编号段及隐藏 prompt，不输出假 img；omitted 不进入 HTML。此阶段不调用生图或上传。图位或论点改变时更新 outline/evidence 并重封存，不在正文定稿后另补未经审查的图。
4. 型号仅在论证必要时出现。额外推广最多一产品一处、不得在开头两段、不得单独开产品 H2，四条判据全过才写；对比文的 A/B 是论证对象。具体型号操作必须核实手册版本；危险动作前给边界，文末声明不能代替就地提示。
5. 正文只建立真实论证，不为未来链接硬加段落。本阶段不插 `<a>`；确有原始资料引用需求时在证据表记录，交链接阶段落入自然锚文本。
6. 生成 `metadata.json`：准确导出键名（不含 html代码）。meta description 与 summary 各≤160 UTF-16 字符；summary 是文章价值摘要而非复制开头。url 为小写英文连字符 slug，meta title 忠实且简洁（建议≤60字符，不冒充解析器硬限）。author 固定 `Divoom Professional Team`。blog/tags 必须与大纲和配置一致。不输出 template，除非用户明确指定已存在的文章模板后缀。
7. 逐项更新 evidence 的 `body_excerpt`，它必须是最终正文可定位的文字；把主张分为 supported/unsupported/overreach，改写删去后两类。运行 `seal <run> draft`。

将唯一 body 路径交回总控。不能生成另一份“SEO 正文”或未经核实的使用体验；只有真做过且可追溯才写 we tested。
