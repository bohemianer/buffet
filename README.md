# 价值投资与商业模式内在价值评估研报引擎 (Buffett Value Investing Skill v8.2)

> 深度融合巴菲特 70 年股东信全集、查理·芒格《穷查理宝典》多学科与逆向思维、段永平商业与投资逻辑、李录《文明、现代化、价值投资与中国》以及艾丽丝·施罗德《滚雪球》。
> 自动调用 Longbridge 经审计财务数据与内置 Python 工具，执行严谨的第一性原理三表穿透、所有者收益精算、现行利率地心引力模型与安全边际定价。

---

## 🌟 核心特性

1. **100% 私有化全资所有权视角（The 100% Private Owner Mindset）**：
   - 假定自掏腰包 100% 全资买下公司并私有化退市，未来 10 年不能交易，每年能从抽屉里稳定抽走多少净现金？
2. **第一性原理财务三表 5 步连续推导**：
   - **第 1 步：资产根基**（固定资产物理寿命 vs 40年折旧剪刀差、重置成本不可复制性、净现金堡垒）
   - **第 2 步：运转与盈利**（毛利率特许权、SG&A 消耗率、GAAP 净利润 5 层来源剥皮表、透视盈余）
   - **第 3 步：现金流转化**（收付实现制机理、净利润现金含量比率、零增量资本扩张力）
   - **第 4 步：维持性消耗扣除**（总 CapEx 拆解：维持性 vs 成长性、资本绞蛔虫测试）
   - **第 5 步：最终所有者落袋与分配**（真实所有者收益 OE 精算、注销式回购复利、自清偿企业价值转移、脱水营运 ROE）
3. **现行利率地心引力与两阶段 DCF 估值引擎**：
   - 真实所有者收益率 vs 10 年期国债无风险收益率（ERP 风险溢价判定）；
   - 宏观锚定增速（$g_1 \le$ 名义 GDP 增速，$g_2 \approx$ 全球实际 GDP 增速）与安全边际买入定价表（7折/6折/5折）。
4. **中国 A 股特有五维风险审查**：
   - 监管政策风险、国资控制结构、A/H 股溢折价、限售解禁减持、会计准则切换。
5. **金融机构专属分析协议**：
   - 保险公司（营运利润 + 浮存金经济价值 + P/EV 估值）；
   - 银行（PPOP 等效所有者收益 + 拨备穿透）。

---

## 📂 项目结构

```
.
├── SKILL.md                               # 主技能指令与报告输出规范 (v8.2)
├── README.md                              # 项目说明文档
├── references/                            # 16 个核心价值投资与财务穿透专题库
│   ├── 01_business_moat_and_franchise.md
│   ├── 02_owners_earnings_and_accounting_adjustments.md
│   ├── 03_capital_allocation_and_retained_earnings_rule.md
│   ├── 04_interest_rate_gravity_and_valuation_models.md
│   ├── 05_balance_sheet_net_cash_and_float_economics.md
│   ├── 06_historical_case_studies_database.md
│   ├── 07_forensic_accounting_and_red_flags.md
│   ├── 08_modern_ai_and_system_lens.md
│   ├── 09_munger_multidisciplinary_and_inversion.md
│   ├── 10_duan_yongping_business_and_investment_logic.md
│   ├── 11_li_lu_civilization_modernization_and_value_investing.md
│   ├── 12_buffett_snowball_and_inner_scorecard.md
│   ├── 13_financial_institutions_special_protocol.md
│   ├── 14_china_astock_risk_factors.md
│   ├── 15_three_statements_forensic_analysis.md
│   └── 16_100_percent_owner_mindset_and_business_mechanics.md
├── scripts/                               # 内置 Python 量化与检索工具
│   ├── owners_earnings.py                 # 所有者收益与 1 美元留存收益计算器
│   ├── buffett_valuation_engine.py        # 利率地心引力与两阶段 DCF 内在价值引擎
│   └── search_corpus.py                   # 大师语料全集原典精准检索工具
└── resources/                             # 70 年致股东信全集与大师经典语料库
    ├── corpus_index.json
    └── master_corpus/
        ├── 巴菲特致股东信精华全集.txt
        ├── 穷查理宝典.txt
        ├── 段永平商业逻辑篇.txt
        ├── 段永平投资逻辑篇.txt
        ├── 文明、现代化、价值投资与中国.txt
        └── 滚雪球：巴菲特和他的财富人生.txt
```

---

## 🚀 触发方式

在对话中输入以下指令即可自动触发：
- `巴菲特分析 [股票代码/名称]`（如 `巴菲特分析 苹果`、`巴菲特分析 600900.SH`、`巴菲特分析 ISRG`）
- `所有者收益 [股票代码]`
- `内在价值评估 [股票代码]`
