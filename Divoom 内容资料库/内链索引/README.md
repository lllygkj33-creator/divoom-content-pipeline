---
文件类型: 内链索引
来源: build_link_index.py（从 品牌资料库/ + 发布与链接记录/ 生成）
---

# 内链索引

给 **agent** 用的机器可读索引。加内链时读这里，不要再去啃 `实例汇总.md`（那是竞品正文，几十万字）。

## 三个文件

| 文件 | 条数 | 用途 |
| --- | --- | --- |
| `博客.json` | 256 | Divoom 已发布文章 —— **内链的主要目标** |
| `产品.json` | 62 | 产品 PDP —— 只在需要植入产品时用 |
| `页面.json` | 21 | 16 个集合 + 5 个场景页 —— 类目级内链目标 |

体量：共约 105 KB。只做内链时**只需要读 `博客.json`（55 KB）**。

## 拉取

索引在**私有仓库**里，和整条流水线同一个 repo：

```bash
git clone git@github.com:lllygkj33-creator/divoom-content-pipeline.git
```

CI / 云端 agent 没有 SSH key 时，用只读细粒度 token：

```bash
git clone https://<token>@github.com/lllygkj33-creator/divoom-content-pipeline.git
```

只想拿索引、不想克隆整个仓库：

```bash
curl -H "Authorization: Bearer <token>" \
     -H "Accept: application/vnd.github.raw" \
     https://api.github.com/repos/lllygkj33-creator/divoom-content-pipeline/contents/Divoom%20%E5%86%85%E5%AE%B9%E8%B5%84%E6%96%99%E5%BA%93/%E5%86%85%E9%93%BE%E7%B4%A2%E5%BC%95/%E5%8D%9A%E5%AE%A2.json
```

## 字段

**`博客.json`** — 内链目标
```json
{"编号": "D001", "标题": "9 Surprising Benefits of Using a Digital Photo Frame",
 "URL": "https://divoom.com/blogs/about-divoom-2/9-surprising-benefits-...",
 "官方栏目": "about-divoom-2"}
```
> `标题` 由 URL slug 推导，**未逐页核对 H1**；`官方栏目` 是 Divoom 官方博客分类，**不是**本库的五栏目分类法。

**`产品.json`** — 产品 PDP
```json
{"名称": "Divoom Pixoo 16x16 Pixel Art LED Display for Gaming Room Decor",
 "短名": "Pixoo", "分类": "像素显示屏",
 "URL": "https://divoom.com/products/...", "在售": true,
 "锚文本候选": ["…官方名…", "…去品牌前缀…"],
 "类目锚文本": "pixel art display",
 "话题": ["…官方标签…"], "所属集合": ["pixel-display"]}
```

⚠️ `锚文本候选` 里混了两类，**不能一视同仁**：
- 等于 `类目锚文本` 的那条（如 `pixel art display`）→ 指向**集合页**，是 2–4 词的通用类目词；
- 其余 → 指向**该产品 PDP**，用 3–6 词官方产品名。

**`页面.json`** — 类目级目标
```json
{"类型": "集合", "名称": "pixel-display", "用途": "品类",
 "URL": "https://divoom.com/collections/pixel-display",
 "产品数": 8, "锚文本候选": ["Pixel Display"]}
```

⚠️ `用途: "促销"` 的 **9 个集合**（`all` / `*-sale` / `christmas-gift` / `new-product` / `featured-products` / `kol-*`）是季节性页面，**不要**在常规文章里当内链目标。只有 7 个 `品类` 集合可以。
> `ponytail:` 促销/品类的判定是句柄关键词启发式（见 `build_link_index.py` 的 `PROMO`）。漏判就往那个元组里加词。

## 加内链时的硬约束

1. **只链 `博客.json` 里真实存在且 `已发布` 的 URL**，不臆造路径。
2. **锚文本只能取 `锚文本候选` 里的词**，不得自创。最终取舍按 `锚文本总规范.md`：
   集合页 → 2–4 词通用类目词；PDP → 3–6 词官方产品名。
3. 内链密度 ≤ 1.5 条 / 100 词（`hard_limits.py` 会卡，超了封顶 7.5）。

## 重新生成

站点结构变了（上新品、发新文章）就重跑：

```bash
python3 build_link_index.py             # 生成 + 自检
python3 build_link_index.py --selftest  # 只校验，不重写
```

自检会挡住：条数不对（256/62/21）、URL 非官方域、URL 重复、**锚文本含虚词或发明词**。
