from fastapi import APIRouter , Depends , HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db 
from app.models import Tenant
from app.schemas import TenantCreate , TenantOut

router = APIRouter(prefix="/tenants" , tags = ["Tenants"])

# -- create Tenant
@router.post("/" , response_model= TenantOut)
async def create_tenant(
    payload : TenantCreate,
    db : AsyncSession = Depends(get_db)
):
    # check email
    result = await db.execute(
        select(Tenant).where(Tenant.email == payload.email)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code= 404 , detail = "Email already registered")
    tenant = Tenant(
        name = payload.name,
        email = payload.email
    )
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return tenant

# --- Get all tenant

@router.get("/" , response_model=list[TenantOut])
async def get_tenants(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Tenant)
    )
    return result.scalars().all()