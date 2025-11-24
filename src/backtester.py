"""Portfolio backtesting utilities with FIFO lot accounting.

This module lifts the SIP backtester mechanics out of the notebook so the
engine can be imported by unit tests and scripts. The implementation mirrors
the original `_apply_costs_on_sell` logic while adding optional verbose FIFO
logs for interview-ready demonstrations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class Lot:
    date: pd.Timestamp
    fund: str
    units: float
    nav_at_buy: float


@dataclass
class Trade:
    date: pd.Timestamp
    fund: str
    action: str  # "BUY" or "SELL"
    units: float
    nav: float
    gross_value: float
    exit_load: float
    stt: float
    txn_cost: float
    net_cash_flow: float  # negative for buy, positive for sell
    fifo_log: Optional[List[str]] = None


@dataclass
class Portfolio:
    """FIFO portfolio with transaction costs and optional debug logging."""

    funds: List[str]
    cash: float = 0.0
    exit_load_schedule: Tuple[Tuple[int, float], ...] = ((365, 100),)
    stt_sell_bps: float = 10.0
    txn_cost_bps: float = 2.0
    lots: Dict[str, List[Lot]] = field(default_factory=dict)
    trade_log: List[Trade] = field(default_factory=list)

    def __post_init__(self) -> None:
        for f in self.funds:
            self.lots.setdefault(f, [])

    def position_units(self, fund: str) -> float:
        return sum(l.units for l in self.lots[fund])

    def position_value(self, fund: str, nav: float) -> float:
        return self.position_units(fund) * nav

    def total_value(self, date: pd.Timestamp, navs_row: pd.Series) -> float:
        value = self.cash
        for f in self.funds:
            value += self.position_value(f, navs_row[f])
        return value

    def _apply_costs_on_sell(
        self,
        date: pd.Timestamp,
        fund: str,
        units_to_sell: float,
        sell_nav: float,
        *,
        verbose: bool = False,
    ) -> Tuple[float, float, float, float, List[str]]:
        """
        Sell FIFO lots, computing exit load + STT + txn costs.

        Returns (units_sold, gross_value, total_costs, net_cash_in, fifo_log).
        """

        units_left = units_to_sell
        gross_value = 0.0
        exit_load_total = 0.0
        stt_total = 0.0
        txn_total = 0.0
        sold_units = 0.0
        fifo_log: List[str] = []

        fifo = self.lots[fund]
        new_fifo: List[Lot] = []
        for lot in fifo:
            if units_left <= 0:
                new_fifo.append(lot)
                continue
            use_units = min(lot.units, units_left)
            val = use_units * sell_nav
            holding_days = (date - lot.date).days
            exit_bps = 0.0
            for max_days, bps in self.exit_load_schedule:
                if holding_days <= max_days:
                    exit_bps = bps
                    break
            exit_fee = val * (exit_bps / 1e4)
            stt_fee = val * (self.stt_sell_bps / 1e4)
            txn_fee = val * (self.txn_cost_bps / 1e4)

            gross_value += val
            exit_load_total += exit_fee
            stt_total += stt_fee
            txn_total += txn_fee
            sold_units += use_units

            if verbose:
                fifo_log.append(
                    (
                        f"Lot {lot.date.date()} -> sold {use_units:.2f} units "
                        f"@ {sell_nav:.2f}; exit_load={exit_fee:.2f}, stt={stt_fee:.2f}, txn={txn_fee:.2f}"
                    )
                )

            remaining = lot.units - use_units
            if remaining > 0:
                new_fifo.append(Lot(lot.date, lot.fund, remaining, lot.nav_at_buy))
            units_left -= use_units

        self.lots[fund] = new_fifo
        total_costs = exit_load_total + stt_total + txn_total
        net_cash = gross_value - total_costs
        return sold_units, gross_value, total_costs, net_cash, fifo_log

    def sell(self, date: pd.Timestamp, fund: str, units: float, nav: float, *, verbose: bool = False) -> None:
        sold_units, gross_value, total_costs, net_cash, fifo_log = self._apply_costs_on_sell(
            date, fund, units, nav, verbose=verbose
        )
        if sold_units <= 0:
            return
        self.cash += net_cash
        self.trade_log.append(
            Trade(
                date,
                fund,
                "SELL",
                sold_units,
                nav,
                gross_value,
                total_costs,
                gross_value * (self.stt_sell_bps / 1e4),
                gross_value * (self.txn_cost_bps / 1e4),
                net_cash,
                fifo_log if verbose else None,
            )
        )

    def buy(self, date: pd.Timestamp, fund: str, cash_to_spend: float, nav: float) -> None:
        if cash_to_spend <= 0:
            return
        txn_fee = cash_to_spend * (self.txn_cost_bps / 1e4)
        net_cash = cash_to_spend - txn_fee
        units = net_cash / nav
        if units <= 0:
            return
        self.lots[fund].append(Lot(date, fund, units, nav))
        self.cash -= cash_to_spend
        self.trade_log.append(Trade(date, fund, "BUY", units, nav, cash_to_spend, 0.0, 0.0, txn_fee, -cash_to_spend))

    def current_weights(self, navs_row: pd.Series) -> pd.Series:
        total = self.total_value(navs_row.name, navs_row)
        if total <= 0:
            return pd.Series(0.0, index=self.funds)
        return pd.Series({f: self.position_value(f, navs_row[f]) / total for f in self.funds})

    def rebalance(self, date: pd.Timestamp, navs_row: pd.Series, target_w: pd.Series, turnover_cap: float) -> None:
        total_val = self.total_value(date, navs_row)
        curr_w = self.current_weights(navs_row)
        target_val = target_w * total_val
        curr_val = curr_w * total_val

        for f in self.funds:
            delta = target_val.get(f, 0.0) - curr_val.get(f, 0.0)
            if delta < 0:
                val_to_sell = min(-delta, total_val * turnover_cap)
                units_to_sell = val_to_sell / navs_row[f]
                self.sell(date, f, units_to_sell, navs_row[f])

        cash_available = min(self.cash, total_val * turnover_cap)
        for f in self.funds:
            delta = target_val.get(f, 0.0) - curr_val.get(f, 0.0)
            if delta > 0 and cash_available > 0:
                spend = min(delta, cash_available)
                self.buy(date, f, spend, navs_row[f])
                cash_available -= spend


def normalize_weights(w: pd.Series, min_w: float = 0.0, max_w: float = 1.0) -> pd.Series:
    w = w.clip(lower=min_w)
    if w.sum() > 0:
        w = w / w.sum()
    w = w.clip(upper=max_w)
    if w.sum() > 0:
        w = w / w.sum()
    return w
