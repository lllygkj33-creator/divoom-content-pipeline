# 共享契约 v1

## 架构与优先级

一个总控、三个阶段能力、一个 canonical body、一套确定性导出。阶段不是独立并发写手，共享同一工作区；只在阶段边界传路径和状态。先后依赖是 outline → draft → links → review → export。无需 HTTP、看板、队列或模型 API 密钥。

优先级：本次用户明确要求 → config/site.json 的部署事实 → 本契约与 publisher/quality/product/evidence → 所选类型改编规范 → 固定快照的源规范/实例。源文档中的旧角色上报、固定20键、只允许博客内链、实体词表可独立证实参数、GEO后审后改稿等不生效。历史样本是数据，不是指令。

## 工作区

`run.json` 是状态，不储存正文副本。`outline.json` 是计划；`evidence.json` 是逐主张依据；`body.html` 是唯一正文；`metadata.json` 是九个元数据键；`links.json` 是链接记录；`review.json` 是最终人工语义审核。只有导出 `articles.json` 给用户。生成目录不得混入 Skill 资源或 GitHub 提交。

`init` 只创建 run.json，不凭标题词面伪造大纲。标题会由模型推断类型；`outline.json` 才是明确路由的权威。`status` 显示已有阶段和指纹新鲜度。源文件修改使其已封存阶段和所有后续依赖失效。

各阶段拥有字段：大纲负责 outline/evidence 初始；正文负责 body/metadata/evidence 支持关系；链接负责 body 中锚和 links；复核负责 review。改变论证必须回正文阶段；任何阶段不得写发布/排期字段。

Technology 新 run 的 editorial_contract_version=2，outline 使用编辑协议 2：同 FX sample_review、逐节呈现与承接、scenario_plan、faq_decision、visual_plan/visual_reason。review 包含 editorial_checks。字段定义见 [编辑与配图规划](editorial-planning.md)；它们绑定在既有指纹链内，不增加新阶段、不进入文章 JSON。无版本字段的历史 run 保持可读，不能冒称已经通过新编辑审核。其他四类暂不强制迁移该协议。

本部署新增 [配图 prompt 随稿模式](image-prompt-handoff.md)：site 的 image_prompt_delivery 默认 html_comments_v1，新 run 在 outline 声明同一模式。完整审核记录仍不出现在 JSON 顶层；待配图 prompt 可以作为正文保留注释交付，并纳入原指纹链。其他类型可以单独采用 visual_plan 与该模式，不因此强制迁移 Technology 专属编辑协议。

## 封存与审查

outline 指纹绑定 outline；draft 绑定 outline、正文无锚语义投影、metadata、evidence；links 绑定完整 body、links、metadata、evidence；review 绑定所有最终产物、配置与 review。正文从 draft 到 links 允许插锚；换词/加事实改变语义投影会要求重新 draft。配置变化也会使检查失效。

脚本执行哈希门禁可防旧稿误导出，不能防执行者虚假填写证据。语义质量必须由执行者真正阅读源资料、逐项判断。不得把自己检查描述为独立专家背书。

## 有界修订与失败

首稿 + 一次定向内容修订，修订记录在 run.json；机械属性修复可以局部进行。审核失败时先定位负责阶段，不把全稿不断重写。关键来源缺失、标题前提错误或一次修订后仍不合格则留下内部 run，向用户简短说明，不产出看似可发布的低质量 JSON。非关键内链缺失可 pending；核心事实不可以 pending 通过。
