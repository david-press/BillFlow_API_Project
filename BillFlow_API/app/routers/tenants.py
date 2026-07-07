from fastapi import APIRouter , Depends , HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from BillFlow_API.app.dependencies import get_db 
from BillFlow_API.app.models import Tenant
from BillFlow_API.app.models import ApiKey
from BillFlow_API.app.auth import generate_api_key
from BillFlow_API.app.schemas import TenantCreate , TenantOut
from BillFlow_API.app.dependencies import get_current_tenant

router = APIRouter(prefix="/tenants" , tags = ["Tenants"])

# --- Get all tenant

@router.get("/" , response_model=list[TenantOut])
async def get_tenants(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Tenant)
    )
    return result.scalars().all()

@router.post("/api-keys")
async def create_api_key(
    label: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    new_key = ApiKey(tenant_id=tenant.id, key=generate_api_key(), label=label)
    db.add(new_key)
    await db.flush()
    await db.refresh(new_key)
    return {"label": new_key.label, "key": new_key.key}