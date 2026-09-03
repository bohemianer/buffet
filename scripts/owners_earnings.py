#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特所有者收益 & 1美元法则计算器（v2.0）
新增：--industry 参数，金融机构（保险/银行）自动切换专属分析框架
"""

import sys
import argparse


# ────────────────────────────────────────────────────────────────────────────
# 通用所有者收益（适用于非金融企业）
# ────────────────────────────────────────────────────────────────────────────

def calculate_owners_earnings(net_income, depreciation_amortization, maintenance_capex, delta_working_capital=0.0):
    oe = net_income + depreciation_amortization - maintenance_capex - delta_working_capital
    oe_to_ni_ratio = (oe / net_income * 100) if net_income != 0 else 0.0
    return {
        "net_income": net_income,
        "da": depreciation_amortization,
        "maintenance_capex": maintenance_capex,
        "delta_working_capital": delta_working_capital,
        "owners_earnings": oe,
        "oe_to_ni_ratio": round(oe_to_ni_ratio, 2)
    }


# ────────────────────────────────────────────────────────────────────────────
# 保险公司专属：营运利润所有者收益（Operating OE）
# ────────────────────────────────────────────────────────────────────────────

def calculate_insurance_operating_profit(
    gaap_net_income,
    investment_volatility_adj,   # 短期投资波动（浮盈/浮亏）需剔除
    discount_rate_adj,            # 折现率变动对准备金的影响
    one_time_items,               # 一次性非日常损益
    float_size,                   # 浮存金规模（保险准备金+未赚保费）
    float_cost_pct,               # 浮存金成本率（综合成本率-100%，若<0则为负成本）
    target_investment_return_pct, # 资产端目标投资回报率
    combined_ratio_pct=None,      # 综合成本率（可选，用于自动计算浮存金成本）
):
    """
    保险公司营运利润与浮存金经济价值测算
    参考：巴菲特1995/1998/2004年致股东信保险浮存金分析框架
    """
    # 1. 营运利润（剔除短期市场波动）
    operating_profit = gaap_net_income - investment_volatility_adj - discount_rate_adj - one_time_items

    # 2. 浮存金成本（若传入综合成本率则自动计算）
    if combined_ratio_pct is not None:
        float_cost_pct = max(0.0, (combined_ratio_pct - 100.0) / 100.0)

    # 3. 浮存金经济价值贡献
    float_economic_value = float_size * (target_investment_return_pct / 100.0 - float_cost_pct)

    # 4. 营运利润含金量比率
    op_to_gaap_ratio = (operating_profit / gaap_net_income * 100) if gaap_net_income != 0 else 0.0

    return {
        "gaap_net_income": gaap_net_income,
        "investment_volatility_adj": investment_volatility_adj,
        "discount_rate_adj": discount_rate_adj,
        "one_time_items": one_time_items,
        "operating_profit": operating_profit,
        "op_to_gaap_ratio": round(op_to_gaap_ratio, 2),
        "float_size": float_size,
        "float_cost_pct": round(float_cost_pct * 100, 2) if combined_ratio_pct is None else round((combined_ratio_pct - 100.0), 2),
        "target_investment_return_pct": target_investment_return_pct,
        "float_economic_value": round(float_economic_value, 2),
    }


# ────────────────────────────────────────────────────────────────────────────
# 银行专属：PPOP法等效所有者收益
# ────────────────────────────────────────────────────────────────────────────

def calculate_bank_ppop_earnings(
    net_income,
    credit_provision,            # 当期信用减值损失（拨备）
    normalized_credit_cost_pct,  # 正常化信用损失率（占贷款余额的 %）
    total_loans,                 # 贷款总余额
    cet1_ratio_pct,              # 当前核心一级资本充足率(%)
    target_cet1_ratio_pct=12.0,  # 目标最低 CET1 比率(%)
    rwa_growth_pct=5.0,          # 风险加权资产预期增速(%)
    total_rwa=0.0,               # 风险加权资产总额
):
    """
    银行所有者收益等效值：PPOP法
    参考：巴菲特2007年致股东信金融机构风险分析框架
    """
    # 1. 拨备前营业利润（PPOP）= 净利润 + 当期拨备
    ppop = net_income + credit_provision

    # 2. 正常化信用损失（用长周期平均信用成本率代替单年拨备）
    normalized_credit_loss = total_loans * (normalized_credit_cost_pct / 100.0)

    # 3. 维持资本充足率所需留存利润（若当前 CET1 低于目标，需留存更多）
    capital_buffer_needed = 0.0
    if total_rwa > 0 and cet1_ratio_pct < target_cet1_ratio_pct + rwa_growth_pct * 0.12:
        required_add_capital = total_rwa * rwa_growth_pct / 100.0 * (target_cet1_ratio_pct / 100.0)
        capital_buffer_needed = max(0.0, required_add_capital)

    # 4. 银行版等效所有者收益
    bank_oe_equivalent = ppop - normalized_credit_loss - capital_buffer_needed

    ppop_to_ni_ratio = (ppop / net_income * 100) if net_income != 0 else 0.0
    oe_to_ni_ratio = (bank_oe_equivalent / net_income * 100) if net_income != 0 else 0.0

    return {
        "net_income": net_income,
        "credit_provision": credit_provision,
        "ppop": round(ppop, 2),
        "ppop_to_ni_ratio": round(ppop_to_ni_ratio, 2),
        "normalized_credit_loss": round(normalized_credit_loss, 2),
        "normalized_credit_cost_pct": normalized_credit_cost_pct,
        "capital_buffer_needed": round(capital_buffer_needed, 2),
        "bank_oe_equivalent": round(bank_oe_equivalent, 2),
        "oe_to_ni_ratio": round(oe_to_ni_ratio, 2),
    }


# ────────────────────────────────────────────────────────────────────────────
# 1美元留存收益测试（支持多时点均值，修正牛熊市扭曲）
# ────────────────────────────────────────────────────────────────────────────

def one_dollar_rule_test(start_market_cap, end_market_cap, retained_earnings_sum,
                          start_cap_avg=None, end_cap_avg=None):
    """
    巴菲特1美元留存收益法则
    start_cap_avg / end_cap_avg：若传入，使用3年均值市值代替单一时点，修正牛熊市扭曲
    """
    effective_start = start_cap_avg if start_cap_avg is not None else start_market_cap
    effective_end = end_cap_avg if end_cap_avg is not None else end_market_cap
    using_avg = (start_cap_avg is not None or end_cap_avg is not None)

    market_cap_created = effective_end - effective_start
    if retained_earnings_sum <= 0:
        ratio = None
    else:
        ratio = market_cap_created / retained_earnings_sum

    passed = (ratio is not None and ratio >= 1.0)
    return {
        "start_market_cap": start_market_cap,
        "end_market_cap": end_market_cap,
        "effective_start_cap": effective_start,
        "effective_end_cap": effective_end,
        "using_avg_adjustment": using_avg,
        "market_cap_created": round(market_cap_created, 2),
        "retained_earnings_sum": round(retained_earnings_sum, 2),
        "dollar_value_created_per_retained_dollar": round(ratio, 2) if ratio is not None else "N/A",
        "test_passed": passed
    }


# ────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="巴菲特所有者收益与1美元法则计算器 v2.0（支持金融机构专属模式）"
    )
    subparsers = parser.add_subparsers(dest="command")

    # ── 子命令 1：通用所有者收益 ──
    calc_parser = subparsers.add_parser("calc", help="计算非金融企业所有者收益")
    calc_parser.add_argument("--net-income", "-ni", type=float, required=True, help="GAAP报告净利润")
    calc_parser.add_argument("--da", "-d", type=float, required=True, help="折旧与摊销 (D&A)")
    calc_parser.add_argument("--maintenance-capex", "-mc", type=float, required=True, help="年均维护性资本开支")
    calc_parser.add_argument("--delta-wc", "-wc", type=float, default=0.0, help="新增营运资金需求（可选）")

    # ── 子命令 2：保险公司专属 ──
    ins_parser = subparsers.add_parser("insurance", help="保险公司：营运利润 + 浮存金经济价值测算")
    ins_parser.add_argument("--gaap-ni", type=float, required=True, help="GAAP归母净利润")
    ins_parser.add_argument("--inv-vol-adj", type=float, default=0.0, help="需剔除的短期投资浮盈/浮亏（正值=浮盈需剔除）")
    ins_parser.add_argument("--discount-adj", type=float, default=0.0, help="折现率变动对准备金影响")
    ins_parser.add_argument("--one-time", type=float, default=0.0, help="一次性非日常损益")
    ins_parser.add_argument("--float-size", type=float, required=True, help="浮存金规模（保险准备金总额）")
    ins_parser.add_argument("--combined-ratio", type=float, default=None, help="综合成本率%%（如98.5），优先用于计算浮存金成本")
    ins_parser.add_argument("--float-cost", type=float, default=0.02, help="浮存金成本率小数（若不传combined-ratio则用此值，如0.02=2%%）")
    ins_parser.add_argument("--inv-return", type=float, default=5.0, help="资产端目标投资回报率%%（如5.0=5%%）")

    # ── 子命令 3：银行专属 ──
    bank_parser = subparsers.add_parser("bank", help="银行：PPOP法等效所有者收益测算")
    bank_parser.add_argument("--net-income", "-ni", type=float, required=True, help="GAAP归母净利润")
    bank_parser.add_argument("--provision", type=float, required=True, help="当期信用减值损失（拨备）")
    bank_parser.add_argument("--norm-cost", type=float, default=0.8, help="正常化信用损失率%%（历史长周期均值，如0.8=0.8%%）")
    bank_parser.add_argument("--total-loans", type=float, required=True, help="贷款总余额")
    bank_parser.add_argument("--cet1", type=float, default=12.0, help="当前核心一级资本充足率%%")
    bank_parser.add_argument("--target-cet1", type=float, default=12.0, help="目标最低CET1%%")
    bank_parser.add_argument("--rwa", type=float, default=0.0, help="风险加权资产总额（传入后计算资本留存需求）")
    bank_parser.add_argument("--rwa-growth", type=float, default=5.0, help="RWA预期增速%%")

    # ── 子命令 4：1美元测试（含牛熊市均值修正）──
    test_parser = subparsers.add_parser("one-dollar", help="5-10年1美元留存收益测试（支持均值市值修正）")
    test_parser.add_argument("--start-cap", type=float, required=True, help="期初总市值（单一时点）")
    test_parser.add_argument("--end-cap", type=float, required=True, help="期末总市值（单一时点）")
    test_parser.add_argument("--retained-sum", type=float, required=True, help="期间累计留存未分配利润")
    test_parser.add_argument("--start-cap-avg", type=float, default=None, help="（可选）期初3年均值市值，用于修正牛熊市扭曲")
    test_parser.add_argument("--end-cap-avg", type=float, default=None, help="（可选）期末3年均值市值，用于修正牛熊市扭曲")

    args = parser.parse_args()

    # ── 通用 OE ──
    if args.command == "calc":
        res = calculate_owners_earnings(args.net_income, args.da, args.maintenance_capex, args.delta_wc)
        print("=" * 60)
        print("  所有者收益（Owner's Earnings）核算结果")
        print("  适用范围：非金融企业（消费/工业/科技/地产）")
        print("=" * 60)
        print("GAAP 报告净利润 (a):       {:>20,.2f}".format(res["net_income"]))
        print("折旧与摊销加回 (b):        {:>20,.2f}".format(res["da"]))
        print("维护性资本支出 (c):       -{:>20,.2f}".format(res["maintenance_capex"]))
        if res["delta_working_capital"] != 0:
            print("新增营运资金需求 (d):     -{:>20,.2f}".format(res["delta_working_capital"]))
        print("-" * 60)
        print("★ 真实所有者收益:          {:>20,.2f}".format(res["owners_earnings"]))
        print("  含金量比率 (OE/净利润):  {:>19.2f}%".format(res["oe_to_ni_ratio"]))
        print("=" * 60 + "\n")

    # ── 保险专属 ──
    elif args.command == "insurance":
        float_cost = args.float_cost if args.combined_ratio is None else max(0.0, (args.combined_ratio - 100.0) / 100.0)
        res = calculate_insurance_operating_profit(
            gaap_net_income=args.gaap_ni,
            investment_volatility_adj=args.inv_vol_adj,
            discount_rate_adj=args.discount_adj,
            one_time_items=args.one_time,
            float_size=args.float_size,
            float_cost_pct=float_cost,
            target_investment_return_pct=args.inv_return,
            combined_ratio_pct=args.combined_ratio,
        )
        print("=" * 60)
        print("  保险公司营运利润 & 浮存金经济价值测算")
        print("  (Insurance Operating Profit & Float Economics)")
        print("  ⚠ 保险公司禁用通用 OE 公式，请使用本专属框架")
        print("=" * 60)
        print("GAAP归母净利润:            {:>20,.2f}".format(res["gaap_net_income"]))
        print("(-) 短期投资波动剔除:     -{:>20,.2f}".format(res["investment_volatility_adj"]))
        print("(-) 折现率变动调整:       -{:>20,.2f}".format(res["discount_rate_adj"]))
        print("(-) 一次性非日常项目:     -{:>20,.2f}".format(res["one_time_items"]))
        print("-" * 60)
        print("★ 营运利润 (Operating):    {:>20,.2f}".format(res["operating_profit"]))
        print("  营运/GAAP比率:          {:>19.2f}%".format(res["op_to_gaap_ratio"]))
        print("-" * 60)
        print("浮存金规模:                {:>20,.2f}".format(res["float_size"]))
        if args.combined_ratio is not None:
            print("综合成本率:              {:>19.1f}%%".format(args.combined_ratio))
        print("浮存金成本率:            {:>19.2f}%%".format(res["float_cost_pct"]))
        print("资产端目标回报率:        {:>19.2f}%%".format(res["target_investment_return_pct"]))
        print("★ 浮存金经济价值贡献:      {:>20,.2f}".format(res["float_economic_value"]))
        print("  (= 浮存金 x (投资回报率 - 浮存金成本率))")
        print("=" * 60 + "\n")

    # ── 银行专属 ──
    elif args.command == "bank":
        res = calculate_bank_ppop_earnings(
            net_income=args.net_income,
            credit_provision=args.provision,
            normalized_credit_cost_pct=args.norm_cost,
            total_loans=args.total_loans,
            cet1_ratio_pct=args.cet1,
            target_cet1_ratio_pct=args.target_cet1,
            rwa_growth_pct=args.rwa_growth,
            total_rwa=args.rwa,
        )
        print("=" * 60)
        print("  银行所有者收益等效值（PPOP法）")
        print("  (Bank OE Equivalent via PPOP Method)")
        print("  ⚠ 银行禁用通用 OE 公式，请使用本专属框架")
        print("=" * 60)
        print("GAAP归母净利润:            {:>20,.2f}".format(res["net_income"]))
        print("(+) 当期信用减值拨备:     +{:>20,.2f}".format(res["credit_provision"]))
        print("-" * 60)
        print("  拨备前营业利润(PPOP):    {:>20,.2f}".format(res["ppop"]))
        print("  PPOP/净利润比率:        {:>19.2f}%%".format(res["ppop_to_ni_ratio"]))
        print("-" * 60)
        print("(-) 正常化信用损失:       -{:>20,.2f}".format(res["normalized_credit_loss"]))
        print("    (贷款余额 x {:.2f}%% 长周期成本率)".format(res["normalized_credit_cost_pct"]))
        if res["capital_buffer_needed"] > 0:
            print("(-) 维持CET1所需留存:    -{:>20,.2f}".format(res["capital_buffer_needed"]))
        print("-" * 60)
        print("★ 银行等效所有者收益:      {:>20,.2f}".format(res["bank_oe_equivalent"]))
        print("  OE等效/净利润比率:      {:>19.2f}%%".format(res["oe_to_ni_ratio"]))
        print("=" * 60 + "\n")

    # ── 1美元测试 ──
    elif args.command == "one-dollar":
        res = one_dollar_rule_test(
            args.start_cap, args.end_cap, args.retained_sum,
            args.start_cap_avg, args.end_cap_avg
        )
        print("=" * 60)
        print("  1美元留存收益再投资效率检验")
        print("  (One-Dollar Retained Earnings Test)")
        if res["using_avg_adjustment"]:
            print("  ✓ 已启用3年均值修正，消除牛熊市时点扭曲")
        print("=" * 60)
        print("期初市值（单一时点）:      {:>20,.2f}".format(res["start_market_cap"]))
        print("期末市值（单一时点）:      {:>20,.2f}".format(res["end_market_cap"]))
        if res["using_avg_adjustment"]:
            print("期初均值市值（修正）:      {:>20,.2f}".format(res["effective_start_cap"]))
            print("期末均值市值（修正）:      {:>20,.2f}".format(res["effective_end_cap"]))
        print("创造的净市值增长:          {:>20,.2f}".format(res["market_cap_created"]))
        print("累计留存未分配利润:        {:>20,.2f}".format(res["retained_earnings_sum"]))
        print("-" * 60)
        ratio_display = res["dollar_value_created_per_retained_dollar"]
        print("每1元留存利润创造的市值:   {:>19}".format(
            "{:.2f}".format(ratio_display) if isinstance(ratio_display, float) else ratio_display
        ))
        status = "✅ 达标 (>= 1.00, 管理层有效配置资本)" if res["test_passed"] else "❌ 未达标 (< 1.00, 资本配置效率低下)"
        print("检验结论: {}".format(status))
        if not res["test_passed"] and isinstance(ratio_display, float) and ratio_display < 0:
            print("  ⚠ 比率为负，当前估值反映市场对企业未来的悲观预期")
            print("    建议检查：护城河是否受损？管理层是否在低效配置资本？")
        print("=" * 60 + "\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
