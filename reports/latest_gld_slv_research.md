# GLD/SLV Core Research Loop

## 安全边界

- scope: GLD / SLV only
- 不新增市场，不新增股票池
- 不自动下单
- 不读取账户持仓、账户资金或任何账户敏感字段
- 输出仅用于研究、日志、数据质量闸门和测试

## 一致预期

- 黄金与白银 ETF 的核心驱动仍是美元实际利率、美元指数、通胀预期、避险需求与 ETF 资金流。
- GLD 更偏黄金 beta 与宏观避险，SLV 波动更高且受工业需求与金银比扰动更明显。
- 若报价非 real_time，所有计划必须降级；no_price 明确为不交易，等待有效报价。

## 实时数据

- generated_jst: 2026-06-03T20:41:37+09:00
- generated_et: 2026-06-03T07:41:37-04:00
- supported_data_delay_flag: real_time, delayed, frozen, no_price, source_conflict
- supported_confidence: high, medium, low
- GLD: price=N/A; source=phase444_446_operator_chain; data_delay_flag=no_price; confidence=low; action_allowed=false; signal=不交易，等待有效报价
- SLV: price=N/A; source=phase444_446_operator_chain; data_delay_flag=no_price; confidence=low; action_allowed=false; signal=不交易，等待有效报价

## 既有认知

- 研究框架保留为人工执行前的观察清单，不形成自动化执行指令。
- GLD/SLV 只在有效报价、低冲突、人工复核通过后进入下一步计划。

## 短期策略：1-5 个交易日

- real_time: 可使用正常人工研究计划，关注回撤买点、反弹减仓点与失效位。
- delayed: 仅观察或低置信计划，等待开盘/报价刷新后复核。
- frozen/source_conflict/no_price: 不行动化，仅记录风险与等待条件。

## 中期策略：2-8 周

- 以实际利率趋势、DXY方向、ETF流入流出与金银比为主线。
- 若 SLV 相对 GLD 强弱出现异常，优先复核白银工业需求与流动性风险。

## 长期策略：3-12 个月

- GLD 关注降息路径、央行购金、美元信用与避险周期。
- SLV 关注工业周期、库存、太阳能/电子需求与黄金白银相对估值。

## 今日买点

- GLD: 等待有效报价；不交易，等待有效报价
- SLV: 等待有效报价；不交易，等待有效报价

## 今日卖点

- GLD: 等待有效报价；若风险事件反转或报价降级则暂停计划
- SLV: 等待有效报价；若风险事件反转或报价降级则暂停计划

## 止损/失效位

- GLD: 等待有效报价；若 data_delay_flag=no_price 且 action_allowed=false，按降级规则执行
- SLV: 等待有效报价；若 data_delay_flag=no_price 且 action_allowed=false，按降级规则执行

## IBKR 现金账户约束

- 现金账户只按 settled cash 做人工复核；不得假设可用未结算资金。
- GFV / freeriding 风险：避免用未结算卖出资金再次买入并在结算前卖出。
- 本报告不读取账户资金、持仓、position 或 account 字段。

## ET / JST 时间窗口

- ET: 美股盘前、常规交易时段、盘后分别记录；关键计划以常规时段有效报价为准。
- JST: 次日清晨复盘 ET 收盘数据，盘中如仅有延迟/冻结数据则保持观察。

## 风险与退出触发

- 报价变为 no_price、frozen 或 source_conflict 时退出行动化计划。
- 实际利率急升、DXY突破、ETF资金大幅流出、地缘风险快速降温会触发防守复核。
- SLV 额外关注工业金属回落、流动性恶化与金银比快速反转。

## 一致性对账单

- GLD: data_delay_flag=no_price; confidence=low; action_allowed=false; result=不交易，等待有效报价; notes=real_marketdata_connection_or_request_not_confirmed
- SLV: data_delay_flag=no_price; confidence=low; action_allowed=false; result=不交易，等待有效报价; notes=real_marketdata_connection_or_request_not_confirmed
