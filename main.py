import logging
import sys
from fastapi import FastAPI, APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, constr, ValidationError
from sqlalchemy import Column, Integer, String, Enum as SQLAEnum, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from enum import Enum
from typing import Optional

# Structured JSON logging setup
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'message': record.getMessage(),
            'event': getattr(record, 'event', None),
            'order_id': getattr(record, 'order_id', None),
            'user': getattr(record, 'user', None)
        }
        # Remove None values
        return str({k: v for k, v in log_record.items() if v is not None})

logger = logging.getLogger('uvicorn.access')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.handlers.clear()
logger.addHandler(handler)

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./orders.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OrderStatus(str, Enum):
    created = "created"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_email = Column(String, index=True, nullable=False)
    item = Column(String, nullable=False)
    status = Column(SQLAEnum(OrderStatus), default=OrderStatus.created, nullable=False)

Base.metadata.create_all(bind=engine)

# Pydantic models
class OrderCreate(BaseModel):
    customer_email: EmailStr
    item: constr(min_length=1, max_length=100)

class OrderUpdate(BaseModel):
    status: OrderStatus

class OrderOut(BaseModel):
    id: int
    customer_email: EmailStr
    item: str
    status: OrderStatus
    
    class Config:
        orm_mode = True

# RBAC dependency
def staff_required(request: Request):
    role = request.headers.get("X-User-Role")
    if role != "staff":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff privileges required.")
    return role

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def mock_send_email(email: str, order_id: int, status: str):
    log_data = {
        'event': 'notification_sent',
        'order_id': order_id,
        'email': email,
        'status': status
    }
    logger.info(str(log_data))

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderOut, status_code=201, summary="Create a new order", responses={403:{"description":"Forbidden"},422:{"description":"Validation Error"}})
def create_order(
    order_in: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: str = Depends(staff_required),
):
    order = Order(customer_email=order_in.customer_email, item=order_in.item)
    db.add(order)
    db.commit()
    db.refresh(order)
    logger.info('', extra={'event': 'order_created', 'order_id': order.id, 'user': user})
    return order

@router.put("/{order_id}", response_model=OrderOut, summary="Update order status", responses={404:{"description":"Not Found"},403:{"description":"Forbidden"},422:{"description":"Validation Error"}})
def update_order(
    order_id: int,
    update: OrderUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: str = Depends(staff_required)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    old_status = order.status
    order.status = update.status
    db.add(order)
    db.commit()
    db.refresh(order)
    logger.info('', extra={'event': 'order_updated', 'order_id': order.id, 'user': user})
    background_tasks.add_task(mock_send_email, order.customer_email, order.id, order.status)
    return order

@router.get("/{order_id}", response_model=OrderOut, summary="Get an order", responses={404:{"description":"Not Found"}})
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order

app = FastAPI(title="Order Processing API", version="1.0.0", description="API for e-commerce order management with background notification and RBAC")

# CORS Middleware for completeness
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.exception_handler(HTTPException)
def custom_http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
