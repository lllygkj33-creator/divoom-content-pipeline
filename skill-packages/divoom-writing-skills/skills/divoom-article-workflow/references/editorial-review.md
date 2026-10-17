# 编辑审核：按同 FX 样本判断，不为过分数补模块

Technology 协议 2 的 `review.json` 增加 `editorial_checks`。每项记录 `decision`（pass / revise）、`section`（intro / whole-article / 正文实际 section id）、`reason`。最终通过需七项全部 pass，理由必须结合当前稿件；示例或测试 fixture 不是已完成审核。

| key | 实际判断 |
|---|---|
| sample_alignment | 是否绑定本 FX 原始对应案例；F14 候选是否保持不确定身份；有没有把样式参考当成内容范式 |
| paragraph_progression | 每段是否新增解释、条件、信号或边界；相邻段同义重复在哪里；不按字数或段数机械评分 |
| condition_integrity | 条件改变是否真的改变结论、观察或限制；是否给出保持不变的条件；有没有虚构阈值 |
| scenario_value | 场景是否提供不同判断而非换地点；不需要多场景时理由是否成立 |
| format_fit | 列表是否承载并列项，编号是否确有顺序，表格是否同轴；没有列表不自动失败 |
| visual_alignment | 图是否回答所在位置的问题，画面/alt/标签是否一致，数字和外观有据；缺图时是否诚实省略且正文自足 |
| faq_choice | 问答是否解决未回答的问题；省略是否合理；没有 FAQ 不自动扣分 |

不新增一套强制 100 分门槛；七维质量门禁仍在 [quality](quality.md)。先指出具体失效，再决定 pass/revise。不要因上次给过高分而维护旧判断，也不要因为补了列表或 FAQ 自动提高分数。

html_comments_v1 模式还需检查每份待配图 prompt 是否独立可用、与图位论点一致、没有虚构测量/型号细节。prompt 不是已完成图片，不声称看过未生成的图；标记、字段和正文所在小节由脚本检查。生成后的真实图片仍需再次审核。

## 同轴前后对照

比较修改前后时，固定标题、FX、案例、事实证据和评价标准。先分别指出可定位的问题，再比较问题是否减少。仅改变审核基准时，说明原评分不可直接比较；不能把“改用正确案例后分数上涨”宣传成正文质量提升。

## 可借鉴的项目，不增加运行依赖

- [Promptfoo rubric](https://www.promptfoo.dev/docs/configuration/expected-outputs/model-graded/llm-rubric/)：借鉴固定案例、明确判据和理由记录；它支持自定义模型评分，但不是现成的专业编辑标准。
- [DeepEval G-Eval](https://deepeval.com/docs/metrics-llm-evals)：借鉴把自然语言判据拆为具体检查；评价者仍可能偏差，不能把分数当事实。
- [STORM](https://github.com/stanford-oval/storm)：借鉴先研究、再规划大纲、再填充文章的分工；不是本项目的文风或配图规范。

本包保留四个 Skill 与一次有依据的内容修订，不安装上述框架、不新增模型 API key、自动多 Agent 或服务。语义回归题在包根 `tests/editorial-evals.json`；它们需要真实执行者判断，不能冒充已自动通过。
