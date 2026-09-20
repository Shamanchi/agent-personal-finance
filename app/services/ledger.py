"""Учёт операций и бюджетов (in-memory, офлайн)."""

from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    id: str
    kind: Literal["income", "expense"]
    amount: float = Field(gt=0)
    category: str
    date: str
    note: str = ""


class Budget(BaseModel):
    category: str
    monthly_limit: float = Field(gt=0)


def _validate_month(value: str) -> str:
    try:
        year, month = value.split("-")
        date(int(year), int(month), 1)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"month must be YYYY-MM, got {value!r}") from exc
    return value


def _validate_date(value: str) -> str:
    try:
        year, month, day = (int(part) for part in value.split("-"))
        date(year, month, day)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"date must be YYYY-MM-DD, got {value!r}") from exc
    return value


class Ledger:
    """Журнал операций и лимитов. Хранится в памяти процесса."""

    def __init__(self) -> None:
        self._transactions: list[Transaction] = []
        self._budgets: dict[str, Budget] = {}

    def add_transaction(
        self,
        kind: Literal["income", "expense"],
        amount: float,
        category: str,
        date_value: str,
        note: str = "",
    ) -> Transaction:
        if amount <= 0:
            raise ValueError("amount must be positive")
        category = category.strip().lower()
        if not category:
            raise ValueError("category must not be empty")
        transaction = Transaction(
            id=str(uuid4()),
            kind=kind,
            amount=round(amount, 2),
            category=category,
            date=_validate_date(date_value),
            note=note,
        )
        self._transactions.append(transaction)
        return transaction

    def list_transactions(self, month: str = "", kind: str = "") -> list[Transaction]:
        result = list(self._transactions)
        if month:
            prefix = _validate_month(month)
            result = [t for t in result if t.date.startswith(prefix)]
        if kind:
            if kind not in ("income", "expense"):
                raise ValueError("kind must be income or expense")
            result = [t for t in result if t.kind == kind]
        return result

    def set_budget(self, category: str, monthly_limit: float) -> Budget:
        if monthly_limit <= 0:
            raise ValueError("monthly_limit must be positive")
        category = category.strip().lower()
        if not category:
            raise ValueError("category must not be empty")
        budget = Budget(category=category, monthly_limit=round(monthly_limit, 2))
        self._budgets[category] = budget
        return budget

    def list_budgets(self) -> list[Budget]:
        return sorted(self._budgets.values(), key=lambda b: b.category)

    def clear(self) -> None:
        self._transactions.clear()
        self._budgets.clear()


_ledger: Ledger | None = None


def get_ledger() -> Ledger:
    global _ledger
    if _ledger is None:
        _ledger = Ledger()
    return _ledger
