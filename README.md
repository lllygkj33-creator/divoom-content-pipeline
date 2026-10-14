# Divoom 内容生产流水线

一套**多 Agent 内容生产流水线**的运行资产与规范库。DSH（DeepSeek Harness）负责把流程跑通；各角色也可以交给 **本地 Codex / 人工**执行——三者可混用，看板上长得一样。

---

## 这是什么

给 divoom.com（英文站）生产 SEO 内容。核心不是"让 AI 写文章"，而是**把一条可复核、可回滚、可观测的流水线跑起来**：

- **角色契约化**：每个角色的职责、输入、产出、边界都写死在 `skills/<角色>/SKILL.md`
- **关键事件级进度**：每个角色有 3–6 个关键事件，逐个上报，看板能看到"卡在哪个 agent 的哪个事件"
- **产物可点击查看**：每个角色必须产出交付文件并登记，随时点开 review
- **审核回环**：审核官不通过 → 定向退回给编辑 → 第 2 轮；最多两轮，仍不达标则交人工裁决

---

## 目录结构

```
divoom/
├── README.md                      本文件
├── Divoom 内容资料库/              ★ 主体
│   ├── 流程契约.md                 五角色链路、字段归属、20 键最终 JSON、硬约束
│   ├── 产品植入规范.md             产品提及的实测依据与四条硬判据
│   ├── 锚文本总规范.md             16 类锚文本 + 词数标准
│   ├── 流水线架构与数据传递.md      架构与数据流说明
│   ├── 画布快照-流水线.md           （已弃用的可视化方案，留档）
│   │
│   ├── skills/                     ★ 角色契约（迁移的核心）
│   │   ├── brief官/SKILL.md
│   │   ├── 产品经理/SKILL.md
│   │   ├── 内容编辑/SKILL.md
│   │   ├── SEO优化师/SKILL.md
│   │   ├── 审核官/SKILL.md
│   │   └── 审核官/{references/,scripts/}
│   │
│   ├── 进度看板/                   ★ 进度可视化 + 命令面板
│   │   ├── index.html              看板页面（卡片 + 关键事件 + 产物 + 回环）
│   │   ├── progress.json           状态契约（agent × 关键事件）
│   │   ├── 上报.py                 ★ 进度上报（各 skill 调用它）
│   │   └── server.py               本地服务（静态 + POST /submit + GET /产物）
│   │
│   ├── 实体库/                     Divoom 实体变量库（14 组 / 567 词）
│   ├── 品牌资料库/                 官方集合/PDP/场景/手册（62 产品 / 16 集合 / 26 手册）
│   ├── <栏目>/                     5 个栏目：科技与信息 / 帮助与提示 / 产品对比 / 购买指南 / 设置与使用
│   │   ├── 标题与大纲规范.md        FX 主表 + H1 公式 + H2 箭头逻辑
│   │   ├── 正文写作规范.md          栏目专属的正文推进规范
│   │   ├── 锚文本规范.md
│   │   └── 实例.base               竞品范文基线（Bases 视图）
│   ├── 发布与链接记录/             已发布文章台账（256 篇，内链唯一来源）+ 待补内链
│   └── work/runs/                  ★ 跑通样例（run-105918 是完整的一次）
│
├── fetch_fc.py                     正文抓取（Firecrawl）
├── fetch_brand.py                  品牌资料抓取（集合/PDP/场景/手册）
├── build_brand_library.py          品牌资料库组装
├── build_published_ledger.py       从官方 sitemap 生成发布台账
├── build_instance_notes.py         竞品实例 → Obsidian 笔记 + Bases
└── analyze_*.py                    语料分析（正文节奏 / 产品提及 / 标题需求）
```

---

## 怎么跑

### 1. 起进度看板

```bash
cd "Divoom 内容资料库/进度看板"
python3 server.py          # → http://127.0.0.1:8899/
```

打开后能看到：总进度条、每个角色的卡片（关键事件 + SVG 状态图标 + 阶段性交付 + **命令面板**）。

### 2. 启动一轮

```bash
cd "Divoom 内容资料库"
RUN="run-$(date +%H%M%S)"
mkdir -p "work/runs/$RUN"
python3 进度看板/上报.py 启动 --标题 "<本轮标题>" --runId "$RUN"
```

### 3. 执行各角色（DSH subagent / Codex / 人工，任选）

每个角色做三件事：

```bash
# ① 读契约
cat "skills/<角色>/SKILL.md"

# ② 干活，产出到 work/runs/<runId>/

# ③ 每个关键事件上报（序号见 进度看板/progress.json）
python3 进度看板/上报.py 事件 --agent "<角色>" --n 1 --状态 处理中
python3 进度看板/上报.py 事件 --agent "<角色>" --n 1 --状态 完成 --备注 "一句话"
python3 进度看板/上报.py 产物 --agent "<角色>" --名 "<产物名>" --路径 "work/runs/<runId>/xx.json" --摘要 "…"
python3 进度看板/上报.py 完成 --agent "<角色>"
```

**看板每张卡片底部的「命令」折叠块会按角色自动生成这些命令，直接复制即可。**

**卡住等人 / 交给 Codex 接手时**：把当前事件上报为 `--状态 等待人工`，卡片转紫、顶部横幅显示「✋ 等待人工接手」；
接手完成后把同一事件改回 `--状态 完成`（不改回，卡片会一直停在紫色）。这就是 DSH / Codex / 人三方交接的点。

### 4. 回环（审核不通过时）

```bash
python3 进度看板/上报.py 回环 --轮次 2 --退回给 "编辑" --原因 "…"
python3 进度看板/上报.py 角度 --agent "编辑" --轮次 2
```

看板会亮黄色回环条，编辑卡显示「↩ 由审核官退回，进入第 2 轮」。

---

## 硬约束（违反即失败）

1. **Divoom 事实只能来自 `实体库/` 与 `品牌资料库/`**；型号名必须与 `品牌资料库/产品/` 的官方命名一致，自创或拼错才是硬伤
2. **内链只能指向 `发布与链接记录/已发布文章.md` 里真实存在的 Divoom URL**；没有就登记 `待补内链.md`，正文绝不留空链
3. **产品植入：一篇最多 1 个产品、1 处提及**；不植入是正常结果
4. **审核官不改稿，GEO 不改编**
5. **回环最多两轮**，不覆盖历史版本
6. **竞品实例（Momcozy / KTC）只作结构参考**，其产品事实、医疗建议、链接不得进稿

---

## 环境依赖

| 项 | 用途 | 必需 |
|---|---|---|
| Python 3.9+ | 看板服务、上报脚本、审核脚本 | ✅ |
| `~/.local/bin/fsearch` | brief官 的外部搜索需求（Firecrawl `/v2/search`） | 仅 brief官 用 |
| `~/.opencli/firecrawl.env` | Firecrawl API key（`FIRECRAWL_API_KEY`） | 仅抓取/搜索用 |

> 看板与上报脚本**零第三方依赖**（纯标准库），拷过去就能跑。
> `fsearch`/`fcrawl` 是本机封装脚本，不在本仓库；没有它时 brief官 会输出 `BLOCKED_SEARCH_DEMAND` 阻断，不会瞎编。

---

## 一次完整运行长什么样

`Divoom 内容资料库/work/runs/run-105918/` 是完整样例（含审核回环）：

```
00-brief.json        Brief 官      → 栏目 科技与信息 / FX F1 / 6 步 H2 链
01b-product-v1.json  产品经理      → 不植入（判据②不过）
01-draft-v1.json     编辑 v1       → 2138 词
02-review-v1.json    审核官 v1     → revise（trust 5.5，有封顶）
01-draft-v2.json     编辑 v2       → 1240 词（开头 162→114，六节全部回落）
03-seo-v2.json       SEO v2        → 5 内链（全 curl 200）+ meta 三件套
02-review-v2.json    审核官 v2     → pass（trust 8.0，caps 空）
final.json           交付          → 恰好 20 键
final.html           交付          → 带链 HTML（由 body_markdown 重建）
```

---

## 迁移到新机器的检查清单

- [ ] `python3 进度看板/server.py` 能起来
- [ ] 打开 `http://127.0.0.1:8899/` 看到 6 张卡片
- [ ] `python3 skills/审核官/scripts/hard_limits.py --selftest` 通过
- [ ] （可选）配置 `~/.opencli/firecrawl.env` 与 `fsearch`，否则 brief官 会阻断
- [ ] 库里**没有**绝对路径依赖（已核验 0 处），可直接使用
