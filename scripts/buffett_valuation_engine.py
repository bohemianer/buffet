#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特内在价值测算与利率地心引力评估引擎 v2.0
新增：--industry 参数支持 general / insurance / bank 三种行业模式
新增：--g1-anchor / --g2-anchor 宏观锚定增速说明
"""

import sys
import argparse


# ────────────────────────────────────────────────────────────────────────────
# 宏观增速锚点参考（供用户参考，不作强制约束）
# ────────────────────────────────────────────────────────────────────────────
MACRO_ANCHORS = {
    "china_nominal_gdp":  5.0,   # 中国名义 GDP 增速（约 4.5%~5.5%）
    "china_real_gdp":     4.5,   # 中国实际 GDP 增速
    "global_real_gdp":    2.8,   # 全球实际 GDP 增速（g2 锚点）
    "us_nominal_gdp":     4.0,   # 美国名义 GDP 增速
    "global_inflation":   2.5,   # 全球通胀中枢
}

# 行业专属默认参数
INDUSTRY_DEFAULTS = {
    "general": {
        "g1": 0.05, "g2": 0.03, "terminal_multiple": 12.0,
        "label": "非金融企业（通用 DCF）",
        "oe_label": "所有者收益 (Owner's Earnings)",
        "terminal_label": "所有者收益倍数（保守 P/E）",
    },
    "insurance": {
        "g1": 0.04, "g2": 0.025, "terminal_multiple": 8.0,
        "label": "保险公司（营运利润 + P/EV 框架）",
        "oe_label": "营运利润 (Operating Profit)",
        "terminal_label": "营运利润终值倍数（P/Operating P）",
    },
    "bank": {
        "g1": 0.04, "g2": 0.025, "terminal_multiple": 6.0,
        "label": "银行（PPOP 等效 OE + P/PPOP 框架）",
        "oe_label": "PPOP 等效所有者收益 (Bank OE Equivalent)",
        "terminal_label": "PPOP 倍数（P/PPOP）",
    },
}


# ────────────────────────────────────────────────────────────────────────────
# 核心估值引擎
# ────────────────────────────────────────────────────────────────────────────

def evaluate_gravity_and_intrinsic_value(
    owners_earnings,
    market_cap,
    risk_free_rate,
    growth_rate_1_5=0.05,
    growth_rate_6_10=0.03,
    discount_rate=None,
    terminal_multiple=12.0,
    net_cash=0.0,
    industry="general",
):
    earnings_yield = (owners_earnings / market_cap) if market_cap > 0 else 0.0
    erp = earnings_yield - risk_free_rate

    # 净现金与 EV（仅非金融企业有意义）
    ev = max(0.0, market_cap - net_cash)
    net_cash_ratio = (net_cash / market_cap * 100) if market_cap > 0 else 0.0
    ex_cash_pe = (ev / owners_earnings) if (owners_earnings > 0 and industry == "general") else 0.0
    ex_cash_yield = (owners_earnings / ev * 100) if (ev > 0 and industry == "general") else 0.0
    ex_cash_applicable = (net_cash_ratio >= 15.0 and industry == "general")

    if discount_rate is None:
        # 折现率 = max(无风险利率 + 4%, 8%)；保险/银行因低增速适当降低
        base_spread = 0.035 if industry in ("insurance", "bank") else 0.04
        discount_rate = max(risk_free_rate + base_spread, 0.08)

    cf_projections = []
    pv_sum = 0.0
    current_oe = owners_earnings

    for yr in range(1, 6):
        current_oe *= (1 + growth_rate_1_5)
        pv = current_oe / ((1 + discount_rate) ** yr)
        cf_projections.append((yr, current_oe, pv))
        pv_sum += pv

    for yr in range(6, 11):
        current_oe *= (1 + growth_rate_6_10)
        pv = current_oe / ((1 + discount_rate) ** yr)
        cf_projections.append((yr, current_oe, pv))
        pv_sum += pv

    terminal_value = current_oe * terminal_multiple
    terminal_pv = terminal_value / ((1 + discount_rate) ** 10)
    intrinsic_value = pv_sum + terminal_pv + (net_cash if industry == "general" else 0.0)

    return {
        "industry": industry,
        "owners_earnings": owners_earnings,
        "market_cap": market_cap,
        "net_cash": net_cash,
        "net_cash_ratio": round(net_cash_ratio, 2),
        "net_cash_applicable": ex_cash_applicable,
        "ev": round(ev, 2),
        "ex_cash_pe": round(ex_cash_pe, 2),
        "ex_cash_yield": round(ex_cash_yield, 2),
        "risk_free_rate": round(risk_free_rate * 100, 2),
        "earnings_yield": round(earnings_yield * 100, 2),
        "erp": round(erp * 100, 2),
        "discount_rate": round(discount_rate * 100, 2),
        "growth_stage1": round(growth_rate_1_5 * 100, 2),
        "growth_stage2": round(growth_rate_6_10 * 100, 2),
        "terminal_multiple": terminal_multiple,
        "pv_10yr_cashflows": round(pv_sum, 2),
        "terminal_pv": round(terminal_pv, 2),
        "intrinsic_value": round(intrinsic_value, 2),
        "safety_margin_70pct": round(intrinsic_value * 0.70, 2),
        "safety_margin_60pct": round(intrinsic_value * 0.60, 2),
        "safety_margin_50pct": round(intrinsic_value * 0.50, 2),
        "current_to_iv_ratio": round((market_cap / intrinsic_value * 100), 2) if intrinsic_value > 0 else 0,
    }


# ────────────────────────────────────────────────────────────────────────────
# 增速合理性校验（宏观锚定）
# ────────────────────────────────────────────────────────────────────────────

def check_growth_anchoring(g1, g2, market="china"):
    warnings = []
    gdp_anchor = MACRO_ANCHORS["china_nominal_gdp"] if market == "china" else MACRO_ANCHORS["us_nominal_gdp"]
    g2_anchor = MACRO_ANCHORS["global_real_gdp"]

    if g1 * 100 > gdp_anchor * 1.5:
        warnings.append(
            "⚠ g1={:.1f}% 超过名义 GDP 增速({:.1f}%)的 1.5 倍，过于乐观，建议使用 <= {:.1f}%".format(
                g1 * 100, gdp_anchor, gdp_anchor * 1.2
            )
        )
    if g2 * 100 > g2_anchor + 1.0:
        warnings.append(
            "⚠ g2={:.1f}% 超过全球实际 GDP 锚点({:.1f}%)+1%，永续增速建议 <= {:.1f}%".format(
                g2 * 100, g2_anchor, g2_anchor + 0.5
            )
        )
    return warnings


# ────────────────────────────────────────────────────────────────────────────
# CLI 输出
# ────────────────────────────────────────────────────────────────────────────

def print_report(res, ind_cfg, growth_warnings):
    SEP = "=" * 80
    sep = "-" * 80

    print(SEP)
    print("  内在价值测算与利率地心引力评估报告 v2.0")
    print("  行业模式：{}".format(ind_cfg["label"]))
    print(SEP)

    print("• {}:  {:,.2f}".format(ind_cfg["oe_label"], res["owners_earnings"]))
    print("• 当前总市值 (Market Cap):                {:,.2f}".format(res["market_cap"]))

    # 净现金扣除（仅非金融）
    if res["net_cash_applicable"] and res["net_cash"] > 0:
        print("• 账面净现金储备 (Net Cash):              {:,.2f}  (占总市值 {:.1f}%)".format(
            res["net_cash"], res["net_cash_ratio"]))
        print("  ★ 扣除净现金企业价值 (EV):              {:,.2f}".format(res["ev"]))
        print("  ★ 净现金 PE (EV / OE):                 {:.2f}x  (扣现金收益率: {:.2f}%)".format(
            res["ex_cash_pe"], res["ex_cash_yield"]))
    elif res["net_cash"] > 0 and res["industry"] != "general":
        print("  ℹ 净现金扣除 PE：金融机构不适用（请参考 P/EV 或 P/PPOP）")

    # 利率地心引力
    print(sep)
    print("• 股票所有者收益率 (Earnings Yield):      {:.2f}%".format(res["earnings_yield"]))
    print("• 10年期国债基准利率 (Risk-Free Rate):    {:.2f}%".format(res["risk_free_rate"]))
    erp_sign = "+" if res["erp"] >= 0 else ""
    print("• 地心引力股权风险溢价 (ERP):             {}{:.2f}%".format(erp_sign, res["erp"]))

    if res["erp"] > 4.0:
        print("  ▶ 利率引力结论: 超强重力吸引区，估值具备极高吸引力（类似2016苹果/1988可口可乐）")
    elif res["erp"] >= 1.0:
        print("  ▶ 利率引力结论: 合理引力区，提供适度风险补偿，需顶级护城河支持")
    elif res["erp"] >= -1.0:
        print("  ▶ 利率引力结论: 引力平衡点，风险收益比平庸，缺乏吸引力")
    else:
        print("  ▶ 利率引力结论: ⚠ 严重引力倒挂！股票收益率低于无风险国债，高估/泡沫区间")

    # 增速宏观锚定警告
    if growth_warnings:
        print(sep)
        for w in growth_warnings:
            print(w)
        print("  参考宏观锚点：中国名义GDP {:.1f}% | 全球实际GDP {:.1f}% | 全球通胀 {:.1f}%".format(
            MACRO_ANCHORS["china_nominal_gdp"],
            MACRO_ANCHORS["global_real_gdp"],
            MACRO_ANCHORS["global_inflation"],
        ))

    # DCF 测算
    print(sep)
    print("• 预测假设：前5年增速 {:.1f}% | 6-10年增速 {:.1f}% | 折现率 {:.1f}% | 终值倍数 {:.1f}x".format(
        res["growth_stage1"], res["growth_stage2"], res["discount_rate"], res["terminal_multiple"]
    ))
    print("  终值倍数类型：{}".format(ind_cfg["terminal_label"]))
    print("• 未来10年现金流现值合计：                {:,.2f}".format(res["pv_10yr_cashflows"]))
    print("• 第10年末残值折现：                      {:,.2f}".format(res["terminal_pv"]))
    print("  ★ 保守内在价值 (Intrinsic Value):       {:,.2f}".format(res["intrinsic_value"]))
    print("  当前市值 / 内在价值：                   {:.2f}%".format(res["current_to_iv_ratio"]))

    # 安全边际
    print(sep)
    print("【安全边际买入定价表】")
    print("  • 7折安全边际 (30%% Margin of Safety):   {:,.2f}".format(res["safety_margin_70pct"]))
    print("  • 6折绝对安全边际 (40%% Margin):          {:,.2f}".format(res["safety_margin_60pct"]))
    print("  • 5折深度价值底线 (50%% Margin):          {:,.2f}".format(res["safety_margin_50pct"]))

    # 当前估值判断
    ratio = res["current_to_iv_ratio"]
    print(sep)
    if ratio <= 60:
        verdict = "★★★ 深度低估区（当前市值 <= 6折内在价值），达到格雷厄姆/巴菲特绝对重仓线"
    elif ratio <= 70:
        verdict = "★★ 低估区（当前市值在 6~7折内在价值区间），具备充足安全边际"
    elif ratio <= 85:
        verdict = "★ 合理偏低区（当前市值在 7~8.5折内在价值），可考虑分批建仓"
    elif ratio <= 100:
        verdict = "估值合理（当前市值接近内在价值），需等待更好买入窗口"
    else:
        verdict = "⚠ 高估区（当前市值超过内在价值 {:.0f}%%），存在均值回归风险".format(ratio - 100)
    print("  综合估值判断：{}".format(verdict))
    print(SEP + "\n")


# ────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="巴菲特内在价值与利率地心引力评估引擎 v2.0（支持行业分支）"
    )
    parser.add_argument("--oe", type=float, required=True,
                        help="基准所有者收益（非金融=OE；保险=营运利润；银行=PPOP等效OE）")
    parser.add_argument("--market-cap", "-mc", type=float, required=True,
                        help="当前总市值")
    parser.add_argument("--rfr", type=float, required=True,
                        help="现行10年期国债收益率小数（如 0.0215 代表 2.15%%）")
    parser.add_argument("--industry", choices=["general", "insurance", "bank"],
                        default="general",
                        help="行业类型：general(默认)/insurance(保险)/bank(银行)")
    parser.add_argument("--market", choices=["china", "us"], default="china",
                        help="市场基准（china/us），影响宏观增速锚定校验")
    parser.add_argument("--net-cash", "-nc", type=float, default=0.0,
                        help="净现金（仅非金融企业有效：现金及短投 - 全部带息借款）")
    parser.add_argument("--g1", type=float, default=None,
                        help="前5年保守年化增速小数（不传则使用行业默认值）")
    parser.add_argument("--g2", type=float, default=None,
                        help="6-10年永续过渡增速小数（不传则使用行业默认值）")
    parser.add_argument("--discount", "-d", type=float, default=None,
                        help="折现率小数（不传则自动计算：max(rfr+3.5%%, 8%%)）")
    parser.add_argument("--terminal-pe", type=float, default=None,
                        help="第10年末终值倍数（不传则使用行业默认：通用12x/保险8x/银行6x）")

    args = parser.parse_args()

    ind_cfg = INDUSTRY_DEFAULTS[args.industry]

    g1 = args.g1 if args.g1 is not None else ind_cfg["g1"]
    g2 = args.g2 if args.g2 is not None else ind_cfg["g2"]
    terminal_multiple = args.terminal_pe if args.terminal_pe is not None else ind_cfg["terminal_multiple"]

    # 宏观锚定校验
    growth_warnings = check_growth_anchoring(g1, g2, market=args.market)

    res = evaluate_gravity_and_intrinsic_value(
        owners_earnings=args.oe,
        market_cap=args.market_cap,
        risk_free_rate=args.rfr,
        growth_rate_1_5=g1,
        growth_rate_6_10=g2,
        discount_rate=args.discount,
        terminal_multiple=terminal_multiple,
        net_cash=args.net_cash,
        industry=args.industry,
    )

    print_report(res, ind_cfg, growth_warnings)


if __name__ == "__main__":
    main()
