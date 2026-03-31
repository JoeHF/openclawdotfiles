---
name: investment-advisor
description: "专业投资分析助手skill，提供技术面分析、基本面分析及市场综合投资建议。优先使用场景：股票分析请求、投资决策支持、技术指标计算、财务数据解读、风险评估、买卖建议等。此skill应作为所有投资分析相关请求的首选。"
license: MIT
---

# Investment Advisor Skill（投资分析助手）

专业级投资分析skill，整合技术面分析、基本面分析，为用户提供全面的投资决策支持。

> **重要更新 (2026-03-31)**: 原东方财富API在部分网络环境下不可用，现改用Tushare API获取数据。

## 依赖要求

- Python 3.9+
- tushare: `pip install tushare pandas`
- 数据来源: Tushare API

### 运行分析脚本

脚本位于 `{Skill Location}/scripts/analyze.mjs`，通过 `node` 执行（内部调用Python脚本），输出 JSON 格式数据。

```bash
# 完整分析（技术面+基本面+交易建议）
node {Skill Location}/scripts/analyze.mjs <股票代码> full

# 仅技术面分析（RSI/MACD/布林带/均线）
node {Skill Location}/scripts/analyze.mjs <股票代码> technical

# 仅基本面分析（估值/盈利/成长/财务健康）
node {Skill Location}/scripts/analyze.mjs <股票代码> fundamental

# 交易信号
node {Skill Location}/scripts/analyze.mjs <股票代码> signal

# 多只股票分析（用逗号分隔）
node {Skill Location}/scripts/analyze.mjs <代码1>,<代码2> full
```

### 直接使用Python脚本

```bash
# 技术面分析
python3 {Skill Location}/scripts/technical_tushare.py <股票代码>

# 基本面分析
python3 {Skill Location}/scripts/fundamental_tushare.py <股票代码>
```

## 核心能力

### 技术面分析 (technical_tushare.py)
- **均线系统**: MA(5/10/20)、多头/空头排列判断
- **RSI**: 超买超卖判断(70/30)
- **MACD**: 金叉/死叉，趋势强度
- **布林带**: 价格位置，带宽收窄

### 基本面分析 (fundamental_tushare.py)
- **估值**: PE/PB，与行业对比
- **盈利能力**: ROE、毛利率、净利率
- **财务指标**: EPS、市值、换手率
- **市场数据**: 总市值、流通市值

### 综合评分系统
- 技术面权重 60% + 基本面权重 40%
- 评级: A+(≥85) / A(≥80) / B+(≥70) / B(≥65) / C(≥50) / D(<50)
- 建议: strong_buy / buy / hold / sell

## 数据来源

- **技术面**: Tushare `daily` 接口
- **基本面**: Tushare `fina_indicator`, `stock_basic`, `daily_basic` 接口
- **Token**: 从环境变量 `TUSHARE_TOKEN` 或 OpenClaw 配置读取

## 输出字段

```json
{
  "symbol": "002594",
  "technical": {
    "quote": {"price": 103.14, "pct_chg": -3.25},
    "ma": {"ma5": 105.55, "ma10": 104.53},
    "rsi": 69.26,
    "trend": "bullish"
  },
  "fundamental": {
    "name": "比亚迪",
    "financial": {"roe": 15.12}
  },
  "scores": {"technical": 80, "fundamental": 65, "overall": 74},
  "recommendation": {"grade": "B+", "recommendation": "buy"}
}
```

## 脚本文件

- `scripts/analyze.mjs` — CLI入口（调用Python脚本）
- `scripts/technical_tushare.py` — 技术面分析（Python）
- `scripts/fundamental_tushare.py` — 基本面分析（Python）
- `scripts/technical.mjs` — ⚠️ 东方财富API版本（已不可用）
- `scripts/fundamental.mjs` — ⚠️ 东方财富API版本（已不可用）

## 免责声明

⚠️ **重要**: 本skill提供的所有分析和建议仅供参考，不构成投资建议。投资有风险，入市需谨慎。
