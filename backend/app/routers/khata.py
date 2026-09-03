"""Khata / ledger read endpoints (TEXT-5). service_role, shop-scoped."""

from typing import Literal

from fastapi import APIRouter, Query

from app.auth import CurrentUserDep
from app.services import khata as khata_svc
from app.services import ledger as ledger_svc

router = APIRouter()


@router.get("/customers")
def customers(user: CurrentUserDep):
    return {"customers": khata_svc.list_customers(shop_id=user.shop_id)}


@router.get("/ledger")
def ledger(
    user: CurrentUserDep,
    filter: Literal["all", "sale", "udhaar", "kharcha"] = "all",
    limit: int = Query(100, ge=1, le=300),
):
    return {"transactions": ledger_svc.transactions(shop_id=user.shop_id, filter=filter, limit=limit)}
