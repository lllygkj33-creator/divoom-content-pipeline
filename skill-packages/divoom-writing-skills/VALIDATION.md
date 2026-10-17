# 验收记录

## 2026-10-17：固定模板 Banner 与可见换图定位

- 通用 Banner 固定在文章 Section，不再提取或移除正文第一张图片；正文生成阶段不再安排 Banner 图片或 prompt。用户未替换线上主题，本次只交付可覆盖的 Liquid 文件。
- 新增 visible_alt_v1：正文待配图位置输出 images_1：alt、images_2：alt 等可见定位段，紧随原结构化 prompt；保留原有语义 id 和图片文件名。换图后应同时移除定位段与其 prompt。定位段不计编辑正文词数或事实证据，且纳入指纹。
- 63 项 Python 回归测试通过。新增检查包括编号/alt 错配、重复编号、非法 Banner 图位、部分图片补好后其余编号不重排、定位文字不能充当事实证据。
- 完整 main-article-editorial.liquid 通过 Shopify 官方 Liquid Section 校验器。复用本机已有的同版 Shopify 校验依赖解决包内缺少依赖的问题；没有修改校验规则。
- 原文章正文、meta 与链接保持不变，另建 run 重封存后导出固定 Banner 版 JSON：3 个正文图位、3 个 prompt、1,455 个编辑正文英文词，原文件名保留。本机实际发布程序解析器识别为 blog_article，publishable=true，issues=[]，bodyHtml 完整保留。没有上传图片、发布文章或写入 Shopify。

## 2026-10-17：JSON 随稿交付配图 prompt

- 本部署默认 `html_comments_v1`：大纲预先规划图位与自包含英文 prompt，正文用保留 HTML 注释交付，最终文章数组的顶层字段不变。没有实际素材时不输出虚构 img 或 CDN URL。
- 58 项 Python 测试通过。其中 8 项新增回归检查覆盖注释转义、可见文本排除、计划与图位对应、prompt 改动导致指纹变化、非法注释及未声明模式拒绝。它们验证机械不变量，不替代内容或图像人工审核。
- 使用已安装的新版四阶段 Skills 实际重写 F1 功率与低音文章，独立新 run 完成大纲→正文→链接→执行模型自检→导出；旧稿保留。新稿 7 个 H2、两组清单、一个观察/推断边界表、无重复 FAQ，含 1 张 banner 和 3 张正文图的待生成 prompt。成稿与运行证据只在本地用户交付目录，不纳入 Skills 包或仓库。
- 对该新版 JSON 调用 `D:/divoom-publisher/src/lib/shopify-json.ts` 的实际解析器：识别为 blog_article，Technology Hub 与 Bluetooth Speakers 保留，publishable=true，issues=[]，bodyHtml 与输入 HTML（去首尾空白后）完全一致，4 个 prompt 注释全部保留。解析器 SHA256 仍为 `e5b81fbfbf18482181ee8492091e59a7cb7db212991fe5552cef06987ccddb43`。使用只读配置/翻译适配和 Custom 上传目标；未启动服务、未改发布程序、未发布。
- package 完整性检查通过，原始 123 份快照未改动。生成图片、上传素材、替换真实 URL 及 Shopify 保存后注释回读尚未执行，不声称已完成这些步骤。

## 2026-10-17：Technology 图文编辑协议 2

- 逐篇读取 F1–F13 对应的 13 个实时页面；另读 1 篇 F14 补充候选，未改写原始候选状态。适配两种正文模板，排除列表/表格单元格和商品卡的段落计数干扰。
- 取得并逐张查看 62 个 OG/正文/商品图资产：正式样本 13 张 OG 图、43 张正文图、4 个商品卡图片节点；补充候选 2 张图。图像二进制及竞品全文只留本次本地研究目录，未放入 package；包中保存 URL、位置、原创注释与正文指纹。
- 50 项 Python 单元测试通过，新增案例绑定、候选状态、条件记录、未就绪素材、图位、编辑审核、计划变动失效、旧 run 兼容及内部字段不泄露到文章出口等机械检查。安装环境回归同时验证本包校验器不扫描无关的其他 Skills。自动测试不证明文风、事实或图片专业性。
- F1 功率文章完成协议 2 的大纲规划演练并封存，加入两个有控制条件的场景和三个 pending 图位；未重写线上文章、未生成图片、未用旧评分冒充新稿质量验收。
- 四个 Skills 使用官方 quick_validate 校验；其 PyYAML 位于临时校验目录，不是运行依赖。validate_package 检查原始 123 份快照的指纹保持完整。
- 原文章 JSON 再次通过本包 publisher 内容格式检查。发布程序和最终 JSON 字段未改变；本次没有重新调用发布程序或 Shopify 写入。
- 人工/模型语义前向题增加 9 个情境，保留“需实际执行者判断”身份，未声称这些语义题已自动端到端通过。

完整案例分析报告见 [Technology 图文审计](reports/technology-editorial-visual-audit-2026-10-17.html)。

## 2026-10-16：初始包

日期：2026-10-16，Asia/Shanghai。

已执行：

- skill-creator 官方 quick_validate.py：四个 Skill 全部通过。官方校验器需要的 PyYAML 只装在工作区临时验证目录，不是包运行依赖。
- validate_package.py：四个 Skill、123份固定资料的 SHA256、当前指令相对引用和JSON解析通过。
- Python unittest：37项测试通过，覆盖字段、UTF-16长度、非法slug、三栏目与品类标签、HTML属性与标签、域名伪装、预览URL、未解析变量、证据缺口、逐主张定位、链接记录、评分门槛、阶段指纹失效、审核后变更、修订预算、导出字节一致性与禁止覆盖内部产物。
- 本机 `D:/divoom-publisher/src/lib/shopify-json.ts` 实际解析器兼容测试：五类字段样本全部识别为blog_article，三个目标blog名称和tags保留，五条均为publishable且issues为空。使用Custom上传目标和只读配置/翻译适配；没有启动应用、没有写发布程序、没有发布。
- 实际解析器快照SHA256：`e5b81fbfbf18482181ee8492091e59a7cb7db212991fe5552cef06987ccddb43`。

范围说明：自动测试样本是短格式fixture，不是五篇完成事实研究的文章；没有声称已做五类模型端到端质量验收。`tests/editorial-evals.json` 提供五类主任务和11个语义边界的后续前向测试集，验收时应实际运行助手，不以字符串匹配代替行为判断。包内统一最终审核是执行模型的自检，不伪装成独立审稿人。

网站部署：本机通用site.config.json仍含示例栏目，测试证明的是现有解析规则能够接受显式Divoom blog字段，不证明线上Blog ID、当前UI手动选择或主题模板已经配置。本包不修改该部署设置，上传时选择实际目标。

源规范保持五类不同结构，原始60个FX和候选状态完整保留。123份资料均还原为原Git blob字节并带manifest，可追溯但不代表实时规格。默认正文1200–2200英文词、两段开头、无H1/H3、至少四个实质H2。导出需要可定位的证据与七维审核；脚本不能自行认定事实正确。
