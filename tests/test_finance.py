"""Unit-тесты журнала и сводки: без сети, детерминированы."""

import pytest

from app.services.ledger import Ledger
from app.services.summary import build_alerts, build_summary


def _seed() -> Ledger:
    book = Ledger()
    book.add_transaction("income", 100000, "salary", "2026-09-01")
    book.add_transaction("expense", 20000, "food", "2026-09-05")
    book.add_transaction("expense", 5000, "transport", "2026-09-06")
    book.add_transaction("expense", 3000, "food", "2026-08-20")
    book.set_budget("food", 15000)
    return book


def test_summary_numbers() -> None:
    summary = build_summary(_seed(), "2026-09")
    assert summary.income == 100000.0
    assert summary.expenses == 25000.0
    assert summary.savings == 75000.0
    assert summary.savings_rate == 0.75
    assert summary.by_category == {"food": 20000.0, "transport": 5000.0}
    assert len(summary.budgets) == 1
    assert summary.budgets[0].over is True


def test_alerts_flag_over_budget() -> None:
    alerts = build_alerts(_seed(), "2026-09")
    assert len(alerts) == 1
    assert alerts[0].category == "food"
    assert alerts[0].over_by == 5000.0


def test_empty_month() -> None:
    summary = build_summary(Ledger(), "2026-09")
    assert summary.income == 0.0
    assert summary.savings_rate == 0.0
    assert build_alerts(Ledger(), "2026-09") == []


def test_validation() -> None:
    book = Ledger()
    with pytest.raises(ValueError):
        book.add_transaction("expense", -5, "food", "2026-09-01")
    with pytest.raises(ValueError):
        book.add_transaction("expense", 5, "food", "2026-13-01")
    with pytest.raises(ValueError):
        book.set_budget("food", 0)
    with pytest.raises(ValueError):
        book.list_transactions(month="oops")
