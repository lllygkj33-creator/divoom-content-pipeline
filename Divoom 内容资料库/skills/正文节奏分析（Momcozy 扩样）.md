# Divoom 内容流水线：Momcozy 扩样与正文节奏分析

核对日期：2026-09-29。用途：解释五角色 skills 第二版的正文规则来源；不将竞品事实迁移到 Divoom。

## 样本与方法

- 上轮实例表：74 个 URL，其中 Momcozy 64、KTC 10。此次新增公开可读 Momcozy 正文 35 篇，五栏各 7 篇；合计 99 篇 Momcozy、10 篇 KTC。
- 对 99 篇 Momcozy 的公开正文按主要任务重新分栏；将网站商品推荐、目录、作者、FAQ、免责声明和明显商品卡标题排除在普通 H2 节奏统计之外。Markdown 网页解析不能完美区分表格、列表和散文，因此下表为结构观察值，不是“最佳篇幅”的因果结论。
- “散文段落”统计仅计可识别的 18–180 词文本行；表格行、列表项和嵌入模块不计。H3 下的散文并入父 H2；因此这些数字描述 H2 完成一个判断的总节奏。
- 旧 ZimaSpace ZIP 中，五栏各自 title/outline/draft 共 15 份用于提取路由与栏目身份检查；未沿用其稿件中提前填 meta/URL 的阶段混用。

## 五栏观察值

| 栏目 | Momcozy 篇数 | 普通 H2 节数 | 每 H2 散文段落中位 | 段落词数中位 | 适合迁移的节内推进 |
| --- | ---: | ---: | ---: | ---: | --- |
| 科技与信息 | 20 | 161 | 2 | 38 | 局部答案→机制/变量→可观察后果或边界 |
| 帮助与提示 | 21 | 163 | 3 | 42 | 症状与分流→可逆检查→动作和复测/停止 |
| 产品对比 | 17 | 130 | 3 | 38 | 共用轴→双方事实→场景代价→条件赢家 |
| 购买指南 | 22 | 182 | 3 | 40 | 硬条件→筛选与验证→排除/升级→选择规则 |
| 设置与使用 | 19 | 152 | 3 | 44 | 现场输入→配置/替代→验收→调整或退出 |

## 反推与纠偏

1. H2 应是一次完整的局部判断。新增版给普通 H2 设 2–4 个不同工作的散文段：首段直接给条件性回答，次段解释依据/机制/比较/检查，第三段把它用于标题场景并给可见结果；第四段仅用于独立例外或过渡。短表格导语、严格步骤、安全停用可例外。25–45 词的直答与 35–100 词的普通段落是**编辑阈值**，不是对竞品分布的照抄。
2. H1 限定词决定信息结构。`even after` 要解释上次尝试留下的缺口；`without` 要保持缺失依赖并给替代及有效边界；`vs` 要同一条件同一量纲；`for [role]` 要让角色约束改变判断。只在标题里留词、正文仍是泛文，属于承诺失效。
3. 将 query fan-out 前移至编辑：定义、条件、对比、操作、边界、成本六层先标必答/可选/越界，必答问题映射 H2 和具体段落。GEO 最后只补适合独立 FAQ 的**次级残余**；核心答案缺失必须退稿。
4. 每个 H2 设 `baseline/delta/support/decision` 四格：常规答案、新关系或条件、实体库或可复核方法、对读者动作的影响。缺一格即没有可验证的信息增益；不能把虚构体验、新数字、空泛修饰当增益。
5. 范文有坏样本。部分公开页存在重复 H2、产品卡标题混进文章层级、解释文滑向排障/选购等情况。样本只能提供“段落工作”和结构假设，审核不能照搬其全部模块。需求明确禁用 H3，即使范文广泛使用 H3，编辑也须以独立 H2、加粗行首或表格处理分支。
6. 旧实例表 64 条 Momcozy Summary 中有 55 条公开 schema 值以省略号结束，因此不能从它们推完整 summary 词数；60–90 词是 Divoom 契约目标。

## 第二版 skills 的具体改动

- 内容编辑增加：两篇同路由范文节内标注、六层 fan-out、信息增益四格、五栏各自的 H2 节内链、普通 H2 段落协议及逐节五问自检。
- 审核官增加：独立重建六层必答问题、逐 H2 记录段落数/词数/功能和增益四格，核心缺口不得交给 FAQ。
- GEO 优化师改为**残余覆盖复核**；发现主线缺失就退回审核，只有次级独立问题才补 FAQ。
- SEO 仍在过审稿后插链；HTML 同步重建闸门与最终 20 字段契约不变。

## 新增 35 篇 URL（按文章主任务归类）

### 科技与信息

- https://momcozy.com/blogs/babycare/how-baby-monitors-work-parents-guide
- https://momcozy.com/blogs/babycare/what-does-vox-mean-on-baby-monitor
- https://momcozy.com/blogs/babycare/do-baby-monitors-record-video
- https://momcozy.com/blogs/news/baby-monitor-range-explained
- https://momcozy.com/blogs/babycare/fhss-baby-monitor-guide
- https://momcozy.com/blogs/babycare/baby-monitor-app-phone-connection-guide
- https://momcozy.com/blogs/babycare/the-complete-diaper-pail-and-diaper-disposal-guide

### 帮助与提示

- https://momcozy.com/blogs/babycare/momcozy-sound-machine-troubleshooting-guide
- https://momcozy.com/blogs/babycare/bm08-support-troubleshooting-center
- https://momcozy.com/blogs/babycare/troubleshoot-low-suction-electric-milk-pump
- https://momcozy.com/blogs/babycare/prevent-high-chair-seat-cracks
- https://momcozy.com/blogs/breastfeeding/breast-pump-not-working-solutions-guide
- https://momcozy.com/blogs/babycare/how-to-clean-a-stroller-after-a-beach-or-outdoor-vacation-safe-steps-for-sand-salt-dirt-and-baby-messes
- https://momcozy.com/blogs/babycare/clean-high-chair-tray-attachment-mechanisms

### 产品对比

- https://momcozy.com/blogs/babycare/electric-baby-swing-vs-manual
- https://momcozy.com/blogs/babycare/steel-vs-plastic-diaper-pail
- https://momcozy.com/blogs/babycare/diaper-pail-vs-trash-can
- https://momcozy.com/blogs/babycare/momcozy-high-chair-comparison
- https://momcozy.com/blogs/babycare/baby-swing-comparison-2in1-vs-3d-motion
- https://momcozy.com/blogs/babycare/momcozy-baby-monitor-comparison
- https://momcozy.com/blogs/babycare/sit-and-stand-stroller-vs-traditional-double-which-setup-supports-toddler-independence-best

### 购买指南

- https://momcozy.com/blogs/babycare/how-to-choose-a-stroller-for-frequent-long-distance-family-visits
- https://momcozy.com/blogs/babycare/how-to-choose-a-stroller-for-camping-and-rv-travel-with-a-baby
- https://momcozy.com/blogs/babycare/can-a-compact-travel-stroller-work-for-daily-errands-after-vacation
- https://momcozy.com/blogs/babycare/best-infant-stroller
- https://momcozy.com/blogs/babycare/baby-monitor-night-vision-buying-tips
- https://momcozy.com/blogs/babycare/best-baby-monitor-for-daycare
- https://momcozy.com/blogs/babycare/best-carrier-for-newborn

### 设置与使用

- https://momcozy.com/blogs/babycare/how-to-create-a-safe-sleep-environment-when-space-is-limited
- https://momcozy.com/blogs/babycare/baby-sleep-away-from-home
- https://momcozy.com/blogs/breastfeeding/pumping-at-work-first-day-guide
- https://momcozy.com/blogs/breastfeeding/pumping-at-work-on-a-hybrid-schedule-how-to-adjust-your-routine-between-office-and-home-days
- https://momcozy.com/blogs/breastfeeding/pumping-at-work-in-heat-or-outdoor-conditions-how-to-keep-breast-milk-safe
- https://momcozy.com/blogs/breastfeeding/using-a-wearable-pump-at-work-what-to-expect-in-your-first-week
- https://momcozy.com/blogs/babycare/how-to-plan-a-multi-city-trip-when-your-baby-stroller-needs-change-by-destination

以上是公开页面读取结果；Obsidian 资料库当前的 `正文写作规范.md` 和 `实例/` 原文件未提供，接入时须复核版本与路径。
