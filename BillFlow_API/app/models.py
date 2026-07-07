from sqlalchemy import String, ForeignKey , Numeric , Enum , DateTime , func
from sqlalchemy.orm import Mapped , mapped_column , relationship
from BillFlow_API.app.database import Base
import enum
import uuid

# ---Enums ---
class InvoiceStatus(str , enum.Enum):
    draft = "draft",
    sent = "sent",
    paid = "paid",
    overdue = "overdue"

# --Tenant(the business using Bullflow) ---
class Tenant(Base):
    __tablename__ = "tenants"

    id : Mapped[str] = mapped_column(String , primary_key = True , default = lambda : str(uuid.uuid4()))
    name : Mapped[str] = mapped_column(String(100) , nullable = False)
    email : Mapped[str] = mapped_column(String(225) , unique = True , nullable = False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at : Mapped[DateTime] = mapped_column(DateTime(timezone= True) , server_default= func.now())

    # relationship
    clients : Mapped[list["Client"]] = relationship(back_populates="tenant" , cascade = "all , delete-orphan" , lazy = "selectin")
    invoices : Mapped[list["Invoice"]] = relationship(back_populates="tenant" , cascade = "all , delete-orphan" , lazy = "selectin")
    
class Client(Base):
    __tablename__ = "clients"

    id : Mapped[str] = mapped_column(String , primary_key = True , default = lambda : str(uuid.uuid4()))
    tenant_id : Mapped[str] = mapped_column(String , ForeignKey("tenants.id" , ondelete= "CASCADE") , nullable = False)
    name : Mapped[str] = mapped_column(String(100) , nullable = False)
    email : Mapped[str] = mapped_column(String(225) , unique = True , nullable = False)
    created_at : Mapped[DateTime] = mapped_column(DateTime(timezone= True)  , server_default= func.now())

    #relationship
    tenant : Mapped[list["Tenant"]] = relationship(back_populates="clients" , lazy = "selectin")
    invoices : Mapped[list["Invoice"]] = relationship(back_populates="client" , cascade = "all , delete-orphan" , lazy = "selectin")

# ---Invoice ----
class Invoice(Base):
    __tablename__ = "invoices"

    id : Mapped[str] = mapped_column(String , primary_key = True , default = lambda : str(uuid.uuid4()))
    tenant_id : Mapped[str] = mapped_column(String , ForeignKey("tenants.id" , ondelete= "CASCADE") , nullable = False)
    client_id : Mapped[str] = mapped_column(String , ForeignKey("clients.id" , ondelete= "CASCADE") , nullable = False)
    title : Mapped[str] = mapped_column(String(200) , nullable = False)
    amount : Mapped[float] = mapped_column(Numeric(10 , 2) , nullable = False)
    status : Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus) , default = InvoiceStatus.draft)
    due_date : Mapped[DateTime] = mapped_column(DateTime(timezone= True) , nullable= True)
    created_at : Mapped[DateTime] = mapped_column(DateTime(timezone = True) , server_default= func.now())

    #relationship
    tenant : Mapped[list["Tenant"]] = relationship(back_populates="invoices" , lazy = "selectin")
    client : Mapped[list["Client"]] = relationship(back_populates="invoices" , lazy = "selectin")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tenant: Mapped["Tenant"] = relationship(lazy="selectin")
    
