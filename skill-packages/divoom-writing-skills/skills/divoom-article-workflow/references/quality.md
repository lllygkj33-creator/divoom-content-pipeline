# 最终质量门禁

最终审核发生在正文、FAQ、链接、meta 全部完成后。导出再核对指纹，任何改动使旧 review 无效。机械检查不能代替来源审读，反过来高自评分也不能盖过格式错误。

## 保留的七维

experience（具体真实情境与可观察结果，禁止虚构实测）；expertise（机制闭合、正确同轴）；authoritativeness（原始事实与主张可追溯，词库不充当证据）；trustworthiness（范围、风险、品牌视角透明）；hcu（答案前置、便于使用、无注水）；infogain（变量区分和判断框架的增量）；ymyl（相关风险的就地边界，不塞无关警告）。详细原基线见 [审核维度](source/audit-dimensions.md)，其中旧脚本“只要命中必须压分”的泛词规则由下述语义门禁取代。

保留 aggregate_eeat = 前四维平均≥8，七维最低≥7、零硬伤。评分0–10，每维至少一条具体理由与正文位置，不为通过凑分。experience 通过具体且有依据的可观察情境评价，不要求给没有做过的第一手实验编经历。

## 需要降级/阻止通过的判断

- 机制/参数与官方事实冲突、自创型号：硬伤，专业性/权威性上限5，不能通过。
- 同轴不足却判赢家：专业性上限7；精确主张无依据：可靠性上限6.5；多项关键数字无来源：权威性上限7。
- 敏感动作缺对应位置边界：可靠性和风险维度上限5.5；破坏或泄露风险指令无前置提示：风险维度<5。
- 明显广告无品牌视角、依赖营销话术得出核心结论：可靠性/增益上限7。
- 长铺垫、无关链接、过密内链：hcu上限7.5；选择文章无场景判据：hcu上限8。必须读上下文，不以一个关键词自动免除全篇风险。

`review.json`：

```json
{
  "decision": "pass",
  "reviewer": "executing-model-self-review",
  "scores": {"experience":8,"expertise":8,"authoritativeness":8,"trustworthiness":8,"hcu":8,"infogain":8,"ymyl":8},
  "rationales": {"experience":"具体位置及依据","expertise":"具体位置及依据","authoritativeness":"具体位置及依据","trustworthiness":"具体位置及依据","hcu":"具体位置及依据","infogain":"具体位置及依据","ymyl":"具体位置及依据"},
  "hard_issues": [],
  "claim_coverage": {"complete":true,"reason":"逐项核对哪些段落中的定量、因果、型号与风险主张；无遗漏"},
  "checks": {"title_promise":true,"type_logic":true,"facts":true,"scope":true,"product_policy":true,"links":true,"metadata":true,"risk_boundaries":true,"no_duplication":true},
  "revision_notes": []
}
```

上例只描述字段，不是可复制的已通过审核。必须对真实稿件逐项写理由；检查不适用时仍记录为何满足边界。若失败，decision=revise/blocked，hard_issues 明确问题；不得导出。读完后执行 seal review 和 export；不再执行审后 GEO 补写。
