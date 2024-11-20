from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, DateTime
from flask_login import UserMixin
from datetime import datetime
from database import db


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(130), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    
    clients: Mapped[list["Client"]] = relationship("Client", back_populates="admin", lazy="dynamic")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="admin", lazy="dynamic")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="admin", lazy="dynamic")
    
    def __repr__(self):
        return f'<Admin {self.admin_name}>'

class Client(db.Model):
    __tablename__ = 'clients'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    street: Mapped[str] = mapped_column(String(250))
    city: Mapped[str] = mapped_column(String(15))
    phone_number: Mapped[str] = mapped_column(String(20))
    
    admin_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('admins.id'), nullable=False)
    admin: Mapped["Admin"] = relationship("Admin", back_populates="clients")
    
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="client", lazy="dynamic")
    
    def __repr__(self):
        return f'<Client {self.name}>'
    


class Order(db.Model):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    product_name: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Pending")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    client_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('clients.id'), nullable=False)
    client: Mapped[Client] = relationship("Client", back_populates="orders")
    
    admin_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('admins.id'), nullable=False)
    admin: Mapped["Admin"] = relationship("Admin", back_populates="orders")

    def __repr__(self):
        return f'<Order {self.id} - {self.status}>'
    


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_number: Mapped[int] = mapped_column(Integer, nullable=False)
    order_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('orders.id'), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    invoice_image: Mapped[str] = mapped_column(String(200), nullable=False)

    order: Mapped["Order"] = relationship('Order', backref="invoices", lazy=True)
    
    admin_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('admins.id'), nullable=False)
    admin: Mapped["Admin"] = relationship("Admin", back_populates="invoices")

    def __repr__(self):
        return f'<Invoice {self.id} for Order {self.order_id}>'
