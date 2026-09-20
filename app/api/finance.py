"""Эндпоинты учёта, бюджетов, сводки и алертов."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.ledger import Budget, Ledger, Transaction, get_ledger
from app.services.summary import Alert, MonthSummary, build_alerts, build_summary

router = APIRouter()


class TransactionRequest(BaseModel):
    kind: Literal["income", "expense"]
    amount: float = Field(gt=0, le=1_000_000_000)
    category: str = Field(min_length=1, max_length=64)
    date: str = Field(min_length=10, max_length=10)
    note: str = Field(default="", max_length=500)


class BudgetRequest(BaseModel):
    category: str = Field(min_length=1, max_length=64)
    monthly_limit: float = Field(gt=0, le=1_000_000_000)


def get_book() -> Ledger:
    return get_ledger()


@router.post("/transactions", response_model=Transaction)
async def add_transaction(request: TransactionRequest, book: Ledger = Depends(get_book)) -> Transaction:
    try:
        return book.add_transaction(
            kind=request.kind,
            amount=request.amount,
            category=request.category,
            date_value=request.date,
            note=request.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/transactions", response_model=list[Transaction])
async def transactions(
    month: str = "",
    kind: str = "",
    book: Ledger = Depends(get_book),
) -> list[Transaction]:
    try:
        return book.list_transactions(month=month, kind=kind)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/budgets", response_model=Budget)
async def set_budget(request: BudgetRequest, book: Ledger = Depends(get_book)) -> Budget:
    try:
        return book.set_budget(request.category, request.monthly_limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/budgets", response_model=list[Budget])
async def budgets(book: Ledger = Depends(get_book)) -> list[Budget]:
    return book.list_budgets()


@router.get("/summary", response_model=MonthSummary)
async def summary(
    month: str = "",
    book: Ledger = Depends(get_book),
    settings: Settings = Depends(get_settings),
) -> MonthSummary:
    target = month or settings.default_month
    try:
        return build_summary(book, target)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/alerts", response_model=list[Alert])
async def alerts(
    month: str = "",
    book: Ledger = Depends(get_book),
    settings: Settings = Depends(get_settings),
) -> list[Alert]:
    target = month or settings.default_month
    try:
        return build_alerts(book, target)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
