"""Сводка за месяц и алерты превышения бюджетов."""

from __future__ import annotations

from pydantic import BaseModel

from app.services.ledger import Ledger


class BudgetStatus(BaseModel):
    category: str
    limit: float
    spent: float
    over: bool


class MonthSummary(BaseModel):
    month: str
    income: float
    expenses: float
    savings: float
    savings_rate: float
    by_category: dict[str, float]
    budgets: list[BudgetStatus]


class Alert(BaseModel):
    category: str
    limit: float
    spent: float
    over_by: float
    message: str


def build_summary(ledger: Ledger, month: str) -> MonthSummary:
    """Посчитать сводку за месяц. Детерминировано."""
    transactions = ledger.list_transactions(month=month)
    income = round(sum(t.amount for t in transactions if t.kind == "income"), 2)
    by_category: dict[str, float] = {}
    for t in transactions:
        if t.kind == "expense":
            by_category[t.category] = round(by_category.get(t.category, 0.0) + t.amount, 2)
    expenses = round(sum(by_category.values()), 2)
    savings = round(income - expenses, 2)
    savings_rate = round(savings / income, 4) if income > 0 else 0.0
    budgets = [
        BudgetStatus(
            category=budget.category,
            limit=budget.monthly_limit,
            spent=by_category.get(budget.category, 0.0),
            over=by_category.get(budget.category, 0.0) > budget.monthly_limit,
        )
        for budget in ledger.list_budgets()
    ]
    return MonthSummary(
        month=month,
        income=income,
        expenses=expenses,
        savings=savings,
        savings_rate=savings_rate,
        by_category=dict(sorted(by_category.items())),
        budgets=budgets,
    )


def build_alerts(ledger: Ledger, month: str) -> list[Alert]:
    """Вернуть превышения лимитов за месяц."""
    summary = build_summary(ledger, month)
    alerts: list[Alert] = []
    for status in summary.budgets:
        if status.over:
            over_by = round(status.spent - status.limit, 2)
            alerts.append(
                Alert(
                    category=status.category,
                    limit=status.limit,
                    spent=status.spent,
                    over_by=over_by,
                    message=f"Превышение по {status.category}: {status.spent:g} > {status.limit:g} (+{over_by:g})",
                )
            )
    return alerts
