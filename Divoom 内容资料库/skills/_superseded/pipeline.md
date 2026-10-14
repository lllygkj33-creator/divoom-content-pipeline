你是 Divoom 内容流水线的**编排器**。请严格按下面的 script 体执行一次 `workflow` 调用，不要修改逻辑，只把 `args` 里的占位值替换成真实值。

## 调用参数

```
meta = {
  "name": "divoom-content-pipeline",
  "description": "写手 → SEO → GEO 三阶段产出 Divoom 文章，最终落一份 JSON",
  "whenToUse": "为 Divoom 生成一篇新文章（标题/大纲/正文 + SEO + GEO）时",
  "phases": [
    {"title": "写手"},
    {"title": "SEO 优化"},
    {"title": "GEO 优化"},
    {"title": "汇总校验"}
  ]
}
args = {
  "vault": "Divoom 内容资料库",
  "topic": "<在此填入主题需求>",
  "column": "<在此填入栏目：科技与信息|帮助与提示|产品对比|购买指南|设置与使用>"
}
```

## script 体

```js
const { vault, topic, column } = args;
const runId = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const runDir = `${vault}/work/runs/${runId}`;

log(`流水线启动：栏目=${column}，主题=${topic}`);
log(`产出目录：${runDir}`);

const common = `
你在 Divoom 内容流水线里，本次栏目是「${column}」。工作目录就是资料库根目录。
所有路径都相对于资料库根目录，例如 ${vault}/实体库/、${vault}/${column}/。
动手前必须先读你自己的作业手册，并严格按它执行。
`;

// ── 阶段一：写手 ────────────────────────────────────────────────
phase('写手');
const draftPath = `${runDir}/01-draft.md`;
const draft = await agent(`
${common}

1. 先读作业手册：${vault}/skills/写手/SKILL.md
2. 严格按手册：读实体库、读「${column}/标题与大纲规范.md」选一个主 FX、读「${column}/正文写作规范.md」
3. 主题需求：${topic}
4. 产出标题、大纲、完整正文 markdown
5. 把结果写入文件 ${draftPath}（用写文件工具，不要只在回答里输出）
6. 你的回答只写一行：draft written, H1=<你的 H1>

硬约束（违反即失败）：不写锚文本/内链/meta/FAQ；不编造型号名（实体库「产品型号」为空）；
正文里每个 Divoom 事实都必须能在实体库查到。
`, { label: `写手：${topic}`, phase: '写手' });

log(`写手完成：${(draft || '').slice(0, 120)}`);
if (!draft) return { ok: false, failed_stage: '写手' };

// ── 阶段二：SEO 优化师 ──────────────────────────────────────────
phase('SEO 优化');
const seoPath = `${runDir}/02-seo.json`;
const seo = await agent(`
${common}

1. 先读作业手册：${vault}/skills/SEO优化师/SKILL.md
2. 读写手完稿：${draftPath}
3. 读 ${vault}/锚文本总规范.md、${vault}/${column}/锚文本规范.md
4. 读发布台账：${vault}/发布与链接记录/已发布文章.md 与 待补内链.md
5. 输出作业手册里规定的那一个 JSON 对象，并写入文件 ${seoPath}
6. 你的回答只写一行：seo written, internal_links=<条数>, pending=<条数>

硬约束（违反即失败）：内链只能指向已发布台账里真实存在且可访问的 Divoom URL；
台账里没有合适目标就登记到 pending_links，正文里绝不留空链接或编造 URL；
不改正文观点、H2 与段落结构；锚文本以 3–6 词为主。
`, { label: `SEO：${topic}`, phase: 'SEO 优化' });

log(`SEO 完成：${(seo || '').slice(0, 120)}`);
if (!seo) return { ok: false, failed_stage: 'SEO', draft: draftPath };

// ── 阶段三：GEO 优化师 ─────────────────────────────────────────
phase('GEO 优化');
const geoPath = `${runDir}/03-geo.json`;
const geo = await agent(`
${common}

1. 先读作业手册：${vault}/skills/GEO优化师/SKILL.md
2. 读 SEO 产物：${seoPath}（正文在 body_markdown 字段里）
3. 读本栏目实例学 FAQ 深度：${vault}/${column}/实例汇总.md（需要时读 ${vault}/${column}/实例/ 下单篇）
4. 读 ${vault}/${column}/标题与大纲规范.md 确认 H1 承诺了什么
5. 按 query fan-out 六层拆子问题，判定 covered / gap_filled / out_of_scope
6. 输出作业手册里规定的那一个 JSON 对象，写入 ${geoPath}
7. 你的回答只写一行：geo written, has_gaps=<true|false>, faq=<条数>

硬约束（违反即失败）：你不改正文一个字；FAQ 里不得出现竞品事实；
涉及 Divoom 事实必须能在实体库查到；没有真实缺口时 faq 为空并给 closing_paragraph。
`, { label: `GEO：${topic}`, phase: 'GEO 优化' });

log(`GEO 完成：${(geo || '').slice(0, 120)}`);
if (!geo) return { ok: false, failed_stage: 'GEO', draft: draftPath, seo: seoPath };

// ── 阶段四：汇总成最终 JSON ─────────────────────────────────────
phase('汇总校验');
const finalPath = `${runDir}/final.json`;
const final = await agent(`
${common}

把三段产物合成一份最终 JSON，写入 ${finalPath}，并在回答里只输出这份 JSON。

输入文件：
- 写手完稿：${draftPath}
- SEO 产物：${seoPath}
- GEO 产物：${geoPath}

最终 JSON 的字段固定为：
{
  "topic": "${topic}",
  "column": "${column}",
  "fx": "<写手选用的 FX 编号>",
  "title": "<meta title>",
  "meta_description": "<meta description>",
  "summary": "<summary>",
  "slug": "<从 H1 生成的 url slug，小写连字符>",
  "url": "",
  "h1": "<正文 H1>",
  "body_markdown": "<SEO 优化后的完整正文>",
  "faq": [{"question": "...", "answer": "..."}],
  "closing_paragraph": "",
  "internal_links": [{"anchor": "...", "url": "...", "h2": "...", "type": "..."}],
  "external_links": [{"anchor": "...", "url": "...", "why": "..."}],
  "pending_links": [{"anchor_candidate": "...", "topic": "...", "h2": "...", "reason": "..."}],
  "fanout": [{"layer": "...", "question": "...", "verdict": "...", "evidence": "..."}],
  "eeat_notes": ["..."],
  "html": "<body_markdown 转成的 html，含 FAQ 段落>",
  "generated_at": "${runId}"
}

规则：
- url 留空字符串（尚未发布）
- html 必须包含正文与 FAQ；不要包含 <html>/<head>，只给正文片段
- 不新增任何字段，不改字段名
- 写文件之后，你的回答里输出这份 JSON 本身
`, { label: `汇总：${topic}`, phase: '汇总校验' });

if (!final) return { ok: false, failed_stage: '汇总', draft: draftPath, seo: seoPath, geo: geoPath };

log(`最终 JSON 已写入 ${finalPath}`);
return {
  ok: true,
  run_id: runId,
  run_dir: runDir,
  final_json: finalPath,
  stages: { draft: draftPath, seo: seoPath, geo: geoPath }
};
```

## 执行要求

- 只调用一次 `workflow`，把上面的 script 体原样传入（替换 args 占位值）
- 不要自己先写文章；三个阶段的活都由脚本里的 agent 完成
- 跑完后把返回的 `run_dir` 与 `final_json` 路径告诉我，并汇报三个阶段各自的产出
