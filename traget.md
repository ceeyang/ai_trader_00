# 多币种动态平衡量化交易系统 (PRD)

## 1. 项目概况 (Project Overview)
* **策略名称**: 高倍现货模拟策略 (Index-style Leveraged Long)
* **核心逻辑**: 通过持有一篮子（20个）优质山寨币，利用低倍实际杠杆（有效杠杆 2x）放大收益，并结合动态再平衡（Dynamic Rebalancing）进行高频波动收割。
* **目标环境**: Python 3.9+, CCXT 库, Binance 期货 API。

## 2. 交易参数设置 (Trading Parameters)
| 参数名称 | 参数值 | 说明 |
| :--- | :--- | :--- |
| **初始本金 (Equity)** | 200 USDT | 用于策略验证的初始保证金 |
| **币种数量 (N)** | 20 | 选定的山寨币数量 |
| **目标持仓价值 (Target Value)** | 20 USDT | 每个币种的名义价值 |
| **名义杠杆 (Leverage)** | 5x | 交易所下单时设置的杠杆倍数 |
| **实际杠杆 (Effective Leverage)** | 2x | (20 * 20) / 200，账户整体抗风险倍数 |
| **平衡阈值 (Threshold)** | 5% | 仓位偏离目标价值 5% 时触发再平衡 |
| **扫描周期 (Scan Interval)** | 5 min | 检查仓位价值并执行收割/补仓的频率 |

以上参数都可以动态配置

## 3. 核心功能模块 (Functional Modules)

### M1：市场自动扫描器 (Market Scanner)
* **任务**: 自动维护交易名单。
* **逻辑**: 
    1.  调用 `tradingview-screener` 获取 Binance 合约交易量 Top 50 的币种。
    2.  按板块分类（AI, MEME, L1/L2, RWA, DeFi），每个板块限制最大占比（如不超过 20%）。
    3.  剔除资金费率异常（年化 > 100%）或流动性极差的币种。

### M2：执行引擎 (Execution Engine)
* **任务**: 下单与保证金管理。
* **逻辑**:
    1.  统一设置为 `全仓模式 (Cross Margin)`。
    2.  下单前自动校验 `set_leverage(5)`。
    3.  计算下单量：`Quantity = TargetValue / CurrentPrice`。

### M3：动态收割/再平衡逻辑 (The Rebalancer)
* **逻辑流程**: 
    * **高抛 (Profit-Taking)**: 当单币价值 > `TargetValue * (1 + 5%)`，卖出超额部分。
    * **低吸 (Re-buying)**: 当单币价值 < `TargetValue * (1 - 5%)`，买入缺失部分。
    * **自动收网**: 这种方式能在不爆仓的情况下，把横盘震荡变成 U 本金收益。

### M4：风险控制 (Risk Management)
* **硬性止损**: 账户总 Equity 回撤超过 30% 时，系统自动一键清仓并停止运行。
* **异常监控**: 如果 API 返回余额不足，或单币价差过大（滑点保护），立即中止该笔交易。
* **资金费率**: 每 8 小时检查一次。若累计支付费率超过利润，触发告警。

## 4. 数据报表要求 (Data & Reporting)
* **实时 Dashboard**: 显示当前总资产、可用余额、各币种浮盈。
* **周报导出**: 
    * 各币种“贡献度” (Net Profit per Coin)。
    * 总资金费率损耗 (Total Funding Fees)。
    * 策略胜率与交易频次。

## 5. 开发任务清单 (Developer Tasks)
- [ ] 初始化 CCXT 交易所连接，配置 API Key。
- [ ] 编写 `get_top_symbols()` 扫描函数。
- [ ] 编写核心 `rebalance()` 函数循环检查持仓。
- [ ] 实现 Telegram Bot 消息推送功能（每 4 小时发送一次收益快报）。
- [ ] 编写 `CSV` 记录器，记录每一笔 Rebalance 的利润，用于生成周报。

---
**备注**: 开发时请务必使用测试网 (Testnet) 进行首轮验证。