"""Modelo de datos: 6 tablas relacionadas mediante claves foráneas.

Categoria 1──N Producto N──1 Proveedor
Cliente   1──N Venta    1──N DetalleVenta N──1 Producto
"""
import datetime

from flask_appbuilder import Model
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

ESTADOS_VENTA = ("Pagada", "Pendiente", "Anulada")


class Categoria(Model):
    __tablename__ = "categoria"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(80), unique=True, nullable=False)
    descripcion = Column(String(255))

    def __repr__(self):
        return self.nombre


class Proveedor(Model):
    __tablename__ = "proveedor"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), unique=True, nullable=False)
    telefono = Column(String(30))
    email = Column(String(120))
    direccion = Column(String(255))

    def __repr__(self):
        return self.nombre


class Producto(Model):
    __tablename__ = "producto"
    __table_args__ = (
        CheckConstraint("precio >= 0", name="ck_producto_precio"),
        CheckConstraint("stock >= 0", name="ck_producto_stock"),
    )

    id = Column(Integer, primary_key=True)
    codigo = Column(String(30), unique=True, nullable=False)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(Text)
    precio = Column(Numeric(10, 2), nullable=False, default=0)
    stock = Column(Integer, nullable=False, default=0)
    stock_minimo = Column(Integer, nullable=False, default=5)
    categoria_id = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    categoria = relationship("Categoria", backref="productos")
    proveedor_id = Column(Integer, ForeignKey("proveedor.id"), nullable=False)
    proveedor = relationship("Proveedor", backref="productos")

    def __repr__(self):
        return f"{self.codigo} - {self.nombre}"


class Cliente(Model):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(80), nullable=False)
    apellido = Column(String(80), nullable=False)
    documento = Column(String(30), unique=True, nullable=False)  # CI / NIT
    telefono = Column(String(30))
    email = Column(String(120))

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def __repr__(self):
        return self.nombre_completo()


class Venta(Model):
    __tablename__ = "venta"

    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, nullable=False, default=datetime.datetime.now)
    estado = Column(
        Enum(*ESTADOS_VENTA, name="estado_venta"), nullable=False, default="Pagada"
    )
    observacion = Column(String(255))
    cliente_id = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    cliente = relationship("Cliente", backref="ventas")

    def total(self):
        return sum(
            (d.cantidad * d.precio_unitario for d in self.detalles), start=0
        )

    def __repr__(self):
        return f"Venta #{self.id}"


class DetalleVenta(Model):
    __tablename__ = "detalle_venta"
    __table_args__ = (CheckConstraint("cantidad > 0", name="ck_detalle_cantidad"),)

    id = Column(Integer, primary_key=True)
    venta_id = Column(Integer, ForeignKey("venta.id"), nullable=False)
    venta = relationship("Venta", backref="detalles")
    producto_id = Column(Integer, ForeignKey("producto.id"), nullable=False)
    producto = relationship("Producto", backref="detalles")
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False, default=0)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __repr__(self):
        return f"{self.cantidad} x {self.producto}"
