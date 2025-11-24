import pytest

pd = pytest.importorskip("pandas")

from src.backtester import Portfolio


def test_fifo_sell_with_logs():
    p = Portfolio(["FUND"], exit_load_schedule=((365, 100),), stt_sell_bps=10, txn_cost_bps=2)
    p.buy(pd.Timestamp("2023-01-01"), "FUND", 1000, 10)  # 99.8 units after fee
    p.buy(pd.Timestamp("2023-02-01"), "FUND", 1000, 10)
    p.buy(pd.Timestamp("2023-03-01"), "FUND", 1000, 10)

    p.sell(pd.Timestamp("2023-04-01"), "FUND", 150, 12, verbose=True)

    sell_logs = [t for t in p.trade_log if t.action == "SELL"][0].fifo_log
    assert sell_logs is not None
    assert "2023-01-01" in sell_logs[0]
    assert "2023-02-01" in sell_logs[1]

    remaining_units = sum(l.units for l in p.lots["FUND"])
    assert remaining_units < 150

    assert p.trade_log[-1].exit_load > 0
    assert p.trade_log[-1].txn_cost > 0
