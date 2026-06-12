from fastapi import Depends , HTTPException , Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Tenant

#--- Dependency 1 : Database Session ----
#Every route that touches the db gets a fresh Session
#injected - and its guaranted to close after request

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ---- Dependency 2 : Current Tenant
#simulate auth via a header for now.
#in production this would decode a JWT token
#here the get_current_tenant depends on get_db()

async def get_current_tenant(
        x_tenant_id : str = Header(..., description="Tenant ID header"),
        db : AsyncSession = Depends(get_db)
) -> Tenant:
    result = await db.execute(
        select(Tenant).where(Tenant.id == x_tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404 , detail = "Tenant not found")
    return tenant