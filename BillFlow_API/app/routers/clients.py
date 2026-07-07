from fastapi import APIRouter , Depends , HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from BillFlow_API.app.dependencies import get_db , get_current_tenant , get_current_tenant_flexible
from BillFlow_API.app.models import Client , Tenant
from BillFlow_API.app.schemas import ClientCreate , ClientOut

router = APIRouter(prefix="/clients" , tags = ["Clients"])

# -- Create client --
@router.post("/" , response_model= ClientOut)
async def create_client(
    payload : ClientCreate,
    db : AsyncSession = Depends(get_db),
    tenant : Tenant = Depends(get_current_tenant)
):
    client = Client(
        tenant_id = tenant.id,
        name = payload.name,
        email = payload.email
    )

    db.add(client)
    await db.flush() # writes to the db but doesnt commit yet
    await db.refresh(client)  #loads genetated fields
    return client

# -- Get all Clients
@router.get("/" ,response_model=list[ClientOut])
async def get_clients(
    db : AsyncSession = Depends(get_db),
    tenant : Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Client).where(Client.tenant_id == tenant.id)
    )

    return result.scalars().all()

# -- Get single client
@router.post("/{client_id}" , response_model= ClientOut)
async def get_client(
    client_id : str,
    db : AsyncSession = Depends(get_db),
    tenant : Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.tenant_id == tenant.id
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code= 404 , detail = "Client not found")
    return client

# -- Delete Client
@router.delete("/{client_id}")
async def delete_client(
    client_id : str,
    db : AsyncSession = Depends(get_db),
    tenant : Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.tenant_id == tenant.id
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code= 404 , detail = "Client not found")
    
    await db.delete(client)
    return {"detail" : "client deleted"}

