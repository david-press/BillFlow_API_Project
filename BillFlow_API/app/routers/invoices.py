from fastapi import APIRouter , Depends , HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select , func
from BillFlow_API.app.dependencies import get_db , get_current_tenant
from BillFlow_API.app.models import Invoice , Client , Tenant , InvoiceStatus
from BillFlow_API.app.schemas import ClientCreate , ClientOut , InvoiceCreate , InvoiceOut , InvoiceUpdate , BillingSummary

router = APIRouter(prefix="/invoices" , tags = ["Invoices"])

#-- Billing summary ----
#this computes aggregations across all invoices for the tenant - no python loops
@router.get("/summary" , response_model=BillingSummary)
async def get_billing_summary(
    db : AsyncSession = Depends(get_db),
    tenant : Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(
            func.count(Invoice.id).label("total_invoices"),
            func.coalesce(func.sum(Invoice.amount) , 0).label("total_amount"),
            func.coalesce(
                func.sum(Invoice.amount).filter(Invoice.status == InvoiceStatus.paid), 0).label("paid_amount"),
            func.coalesce(
                func.sum(Invoice.amount).filter(Invoice.status != InvoiceStatus.paid), 0).label("pending_amount"),    
            ).where(Invoice.tenant_id == tenant.id)
        )
    row = result.one()

    return BillingSummary(
        total_invoices= row.total_invoices,
        total_amount = float(row.total_amount),
        paid_amount = float(row.paid_amount),
        pending_amount = float(row.pending_amount)
    )


# --- Create Invoice ---
@router.post("/" , response_model=InvoiceOut)
async def create_invoice(
    payload : InvoiceCreate , 
    db : AsyncSession = Depends(get_db),
    tenant : Tenant = Depends(get_current_tenant)
):
    #to verify
    result = await db.execute(
        select(Client).where(
            Client.id == payload.client_id,
            Client.tenant_id == tenant.id
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code= 404 , detail = "Client not found")
    
    invoice = Invoice(
        tenant_id = tenant.id,
        client_id = payload.client_id,
        title = payload.title,
        amount = payload.amount,
        due_date = payload.due_date
    )
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    return invoice


# -- Get All invoice -- 
@router.get("/" , response_model=list[InvoiceOut])
async def get_invoices(
    db : AsyncSession = Depends(get_db),
    tenant : Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Invoice).where(Invoice.tenant_id == tenant.id)
    )
    return result.scalars().all()

# -- Update Invoice Status 
@router.patch("/{invoice_id}" , response_model= InvoiceOut)
async def update_invoice_status(
    invoice_id : str,
    payload : InvoiceUpdate,
    db : AsyncSession = Depends(get_db),
    tenant : Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant.id
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code= 404 , detail = "Invoice not found")
    
    invoice.status = payload.status
    await db.flush()
    await db.refresh(invoice)
    return invoice


# --- Delete Invoice ---
@router.delete("/{client_id}")
async def delete_invoice(
    invoice_id : str,
    db : AsyncSession = Depends(get_db),
    tenant : Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant.id
        )
    )

    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code= 404 , detail = "Invoice not found")
    
    await db.delete(invoice)
    return {"detail" : "invoice deleted"}



        