"""Dashboard + catalog read endpoints (TEXT-5).

All reads use the service_role client and scope by the caller's shop — no
dependency on the RLS app_metadata.shop_id claim.
"""

from fastapi import APIRouter, Query

from app.auth import CurrentUserDep
from app.services import catalog, dashboard

router = APIRouter()


@router.get("/today")
def dashboard_today(user: CurrentUserDep):
    """The shopkeeper's 'aaj' snapshot: totals, low stock, recent entries."""
    return dashboard.today_snapshot(shop_id=user.shop_id)


@router.get("/products")
def products(user: CurrentUserDep, low_only: bool = Query(False)):
    rows = catalog.list_products(shop_id=user.shop_id)
    if low_only:
        rows = [p for p in rows if (p["stock"] or 0) <= 5]
    return {"products": rows}
