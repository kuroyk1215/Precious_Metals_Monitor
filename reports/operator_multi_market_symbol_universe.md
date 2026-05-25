# Operator Multi-Market Symbol Universe

## Scope

- static JP / CN / US symbol universe and unified schema only
- manual-only / research-only / observation-only
- no IBKR, TWS, Gateway, real market data, account read, position read, historical data request, Telegram real send, trading, order, cancel, or rebalance
- no buy/sell points and no automatic trading advice

## Schema Gate

- generated_at=2026-05-25T09:23:29+00:00
- schema_gate_status=MULTI_MARKET_SYMBOL_SCHEMA_READY
- markets_present=CN,JP,US
- jp_symbol_count=6
- cn_symbol_count=6
- us_symbol_count=6
- trading_unit_rules_present=true
- settlement_rules_present=true
- timezone_rules_present=true
- all_trading_disabled=true
- all_observation_enabled=true
- no_account_or_position_read=true
- no_historical_data_request=true
- no_real_telegram_send=true
- diagnostic_reason=JP_CN_US_present_all_symbols_trading_disabled_static_schema_ready

## Market Rules

- JP: JST; 100_share_round_lot; TSE closes at 15:30; closing auction 15:25-15:30
- CN: CST; ordinary_stock_100_share_integer_multiple; A_share_common_stock_and_stock_etf_T+1
- US: ET/JST; IBKR cash account; settled cash; default_whole_share; T+1

## Symbols

| market | symbol | display_name | asset_type | currency | timezone | trading_unit | settlement_rule | enabled_for_observation | enabled_for_trading |
|---|---|---|---|---|---|---|---|---|---|
| JP | 1540.T | 1540.T | gold_etf | JPY | JST | 100_share_round_lot | TSE_close_15:30_JST;closing_auction_15:25-15:30_JST | true | false |
| JP | 1542.T | 1542.T | silver_etf | JPY | JST | 100_share_round_lot | TSE_close_15:30_JST;closing_auction_15:25-15:30_JST | true | false |
| JP | 7203.T | Toyota | large_cap | JPY | JST | 100_share_round_lot | TSE_close_15:30_JST;closing_auction_15:25-15:30_JST | true | false |
| JP | 6758.T | Sony | large_cap | JPY | JST | 100_share_round_lot | TSE_close_15:30_JST;closing_auction_15:25-15:30_JST | true | false |
| JP | 9432.T | NTT | large_cap | JPY | JST | 100_share_round_lot | TSE_close_15:30_JST;closing_auction_15:25-15:30_JST | true | false |
| JP | 8035.T | Tokyo Electron | semiconductor | JPY | JST | 100_share_round_lot | TSE_close_15:30_JST;closing_auction_15:25-15:30_JST | true | false |
| US | GLD | GLD | gold_etf | USD | ET/JST | default_whole_share | IBKR_cash_account;settled_cash;T+1 | true | false |
| US | SLV | SLV | silver_etf | USD | ET/JST | default_whole_share | IBKR_cash_account;settled_cash;T+1 | true | false |
| US | AAPL | AAPL | large_cap | USD | ET/JST | default_whole_share | IBKR_cash_account;settled_cash;T+1 | true | false |
| US | MSFT | MSFT | large_cap | USD | ET/JST | default_whole_share | IBKR_cash_account;settled_cash;T+1 | true | false |
| US | NVDA | NVDA | semiconductor | USD | ET/JST | default_whole_share | IBKR_cash_account;settled_cash;T+1 | true | false |
| US | SPY | SPY | broad_market_etf | USD | ET/JST | default_whole_share | IBKR_cash_account;settled_cash;T+1 | true | false |
| CN | 518880.SH | 518880.SH | gold_etf | CNY | CST | ordinary_stock_100_share_integer_multiple | A_share_common_stock_and_stock_etf_T+1 | true | false |
| CN | 600519.SH | 600519.SH | large_cap | CNY | CST | ordinary_stock_100_share_integer_multiple | A_share_common_stock_and_stock_etf_T+1 | true | false |
| CN | 600276.SH | 600276.SH | pharma | CNY | CST | ordinary_stock_100_share_integer_multiple | A_share_common_stock_and_stock_etf_T+1 | true | false |
| CN | 601138.SH | 601138.SH | manufacturing | CNY | CST | ordinary_stock_100_share_integer_multiple | A_share_common_stock_and_stock_etf_T+1 | true | false |
| CN | 002130.SZ | 002130.SZ | manufacturing | CNY | CST | ordinary_stock_100_share_integer_multiple | A_share_common_stock_and_stock_etf_T+1 | true | false |
| CN | 510300.SH | 510300.SH | broad_market_etf | CNY | CST | ordinary_stock_100_share_integer_multiple | A_share_common_stock_and_stock_etf_T+1 | true | false |

## Safety Assertions

- 1540.T: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;JP rule: JST;100_share_round_lot;TSE_close_15:30;closing_auction_15:25-15:30
- 1542.T: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;JP rule: JST;100_share_round_lot;TSE_close_15:30;closing_auction_15:25-15:30
- 7203.T: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;JP rule: JST;100_share_round_lot;TSE_close_15:30;closing_auction_15:25-15:30
- 6758.T: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;JP rule: JST;100_share_round_lot;TSE_close_15:30;closing_auction_15:25-15:30
- 9432.T: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;JP rule: JST;100_share_round_lot;TSE_close_15:30;closing_auction_15:25-15:30
- 8035.T: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;JP rule: JST;100_share_round_lot;TSE_close_15:30;closing_auction_15:25-15:30
- GLD: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;US rule: ET/JST;IBKR_cash_account;settled_cash;default_whole_share;T+1
- SLV: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;US rule: ET/JST;IBKR_cash_account;settled_cash;default_whole_share;T+1
- AAPL: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;US rule: ET/JST;IBKR_cash_account;settled_cash;default_whole_share;T+1
- MSFT: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;US rule: ET/JST;IBKR_cash_account;settled_cash;default_whole_share;T+1
- NVDA: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;US rule: ET/JST;IBKR_cash_account;settled_cash;default_whole_share;T+1
- SPY: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;US rule: ET/JST;IBKR_cash_account;settled_cash;default_whole_share;T+1
- 518880.SH: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;CN rule: CST;ordinary_stock_100_share_integer_multiple;A_share_common_stock_and_stock_etf_T+1;518880.SH_ibkr_availability_not_assumed_local_market_symbol_only
- 600519.SH: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;CN rule: CST;ordinary_stock_100_share_integer_multiple;A_share_common_stock_and_stock_etf_T+1
- 600276.SH: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;CN rule: CST;ordinary_stock_100_share_integer_multiple;A_share_common_stock_and_stock_etf_T+1
- 601138.SH: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;CN rule: CST;ordinary_stock_100_share_integer_multiple;A_share_common_stock_and_stock_etf_T+1
- 002130.SZ: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;CN rule: CST;ordinary_stock_100_share_integer_multiple;A_share_common_stock_and_stock_etf_T+1
- 510300.SH: enabled_for_trading=false; trading_actions_allowed=false; account_read_allowed=false; position_read_allowed=false; historical_data_request_allowed=false; telegram_real_send_allowed=false; manual_only=true; research_only=true; observation_only=true; diagnostic_reason=static_multi_market_symbol_universe_only;no_ibkr_contract_qualification;no_real_market_data;no_account_or_position_read;no_historical_data_request;no_telegram_real_send;CN rule: CST;ordinary_stock_100_share_integer_multiple;A_share_common_stock_and_stock_etf_T+1
