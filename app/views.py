"""Vistas CRUD (Flask-AppBuilder) con reglas de negocio."""
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from sqlalchemy import inspect

from . import appbuilder, db
from .models import Categoria, Cliente, DetalleVenta, Producto, Proveedor, Venta


class SinHijosMixin:
    """Regla de negocio: no se puede eliminar un registro con dependientes."""

    relacion_hijos = None
    mensaje_hijos = "El registro tiene datos relacionados y no se puede eliminar."

    def pre_delete(self, item):
        if self.relacion_hijos and getattr(item, self.relacion_hijos):
            raise Exception(self.mensaje_hijos)


def _valor_anterior(item, atributo):
    """Valor que tenía el atributo antes de la edición actual."""
    hist = inspect(item).attrs[atributo].history
    return hist.deleted[0] if hist.deleted else getattr(item, atributo)


# ---------------------------------------------------------------- Catálogos
class CategoriaModelView(SinHijosMixin, ModelView):
    datamodel = SQLAInterface(Categoria)
    list_columns = ["nombre", "descripcion"]
    search_columns = ["nombre"]
    relacion_hijos = "productos"
    mensaje_hijos = "No se puede eliminar: la categoría tiene productos."
    label_columns = {"nombre": "Nombre", "descripcion": "Descripción"}


class ProveedorModelView(SinHijosMixin, ModelView):
    datamodel = SQLAInterface(Proveedor)
    list_columns = ["nombre", "telefono", "email"]
    search_columns = ["nombre", "email"]
    relacion_hijos = "productos"
    mensaje_hijos = "No se puede eliminar: el proveedor tiene productos."
    label_columns = {
        "nombre": "Nombre",
        "telefono": "Teléfono",
        "email": "Correo",
        "direccion": "Dirección",
    }


class ProductoModelView(SinHijosMixin, ModelView):
    datamodel = SQLAInterface(Producto)
    list_columns = ["codigo", "nombre", "categoria", "proveedor", "precio", "stock"]
    search_columns = ["codigo", "nombre", "categoria", "proveedor", "stock"]
    add_columns = [
        "codigo", "nombre", "descripcion", "categoria", "proveedor",
        "precio", "stock", "stock_minimo",
    ]
    edit_columns = add_columns
    show_columns = add_columns
    base_order = ("nombre", "asc")
    relacion_hijos = "detalles"
    mensaje_hijos = "No se puede eliminar: el producto tiene ventas registradas."
    label_columns = {
        "codigo": "Código",
        "nombre": "Nombre",
        "descripcion": "Descripción",
        "categoria": "Categoría",
        "proveedor": "Proveedor",
        "precio": "Precio (Bs)",
        "stock": "Stock",
        "stock_minimo": "Stock mínimo",
    }

    def pre_add(self, item):
        self._validar(item)

    def pre_update(self, item):
        self._validar(item)

    @staticmethod
    def _validar(item):
        if item.precio is None or item.precio < 0:
            raise Exception("El precio no puede ser negativo.")
        if item.stock is None or item.stock < 0:
            raise Exception("El stock no puede ser negativo.")


class CategoriaConProductos(CategoriaModelView):
    related_views = [ProductoModelView]


class ClienteModelView(SinHijosMixin, ModelView):
    datamodel = SQLAInterface(Cliente)
    list_columns = ["nombre", "apellido", "documento", "telefono", "email"]
    search_columns = ["nombre", "apellido", "documento"]
    relacion_hijos = "ventas"
    mensaje_hijos = "No se puede eliminar: el cliente tiene ventas."
    label_columns = {
        "nombre": "Nombre",
        "apellido": "Apellido",
        "documento": "CI / NIT",
        "telefono": "Teléfono",
        "email": "Correo",
    }


# ------------------------------------------------------------------- Ventas
class DetalleVentaModelView(ModelView):
    datamodel = SQLAInterface(DetalleVenta)
    list_columns = ["venta", "producto", "cantidad", "precio_unitario", "subtotal"]
    add_columns = ["venta", "producto", "cantidad"]
    edit_columns = ["cantidad"]  # el producto no se cambia: se elimina y se vuelve a cargar
    show_columns = ["venta", "producto", "cantidad", "precio_unitario", "subtotal"]
    label_columns = {
        "venta": "Venta",
        "producto": "Producto",
        "cantidad": "Cantidad",
        "precio_unitario": "Precio unitario (Bs)",
        "subtotal": "Subtotal (Bs)",
    }

    def pre_add(self, item):
        if item.venta.estado == "Anulada":
            raise Exception("No se pueden agregar ítems a una venta anulada.")
        if not item.cantidad or item.cantidad <= 0:
            raise Exception("La cantidad debe ser mayor que cero.")
        producto = item.producto
        if item.cantidad > producto.stock:
            raise Exception(
                f"Stock insuficiente de '{producto.nombre}': disponible {producto.stock}."
            )
        item.precio_unitario = producto.precio  # congela el precio al momento de vender
        producto.stock -= item.cantidad

    def pre_update(self, item):
        if item.venta.estado == "Anulada":
            raise Exception("No se puede editar un ítem de una venta anulada.")
        if not item.cantidad or item.cantidad <= 0:
            raise Exception("La cantidad debe ser mayor que cero.")
        delta = item.cantidad - _valor_anterior(item, "cantidad")
        if delta > item.producto.stock:
            raise Exception(
                f"Stock insuficiente de '{item.producto.nombre}': "
                f"disponible {item.producto.stock}."
            )
        item.producto.stock -= delta

    def pre_delete(self, item):
        if item.venta.estado != "Anulada":  # si estaba anulada, el stock ya se devolvió
            item.producto.stock += item.cantidad


class VentaModelView(ModelView):
    datamodel = SQLAInterface(Venta)
    related_views = [DetalleVentaModelView]
    list_columns = ["id", "fecha", "cliente", "estado", "total"]
    add_columns = ["cliente", "fecha", "estado", "observacion"]
    edit_columns = ["cliente", "estado", "observacion"]
    show_columns = ["id", "fecha", "cliente", "estado", "observacion", "total"]
    search_columns = ["cliente", "fecha", "estado"]
    base_order = ("fecha", "desc")
    label_columns = {
        "id": "N.º",
        "fecha": "Fecha",
        "cliente": "Cliente",
        "estado": "Estado",
        "observacion": "Observación",
        "total": "Total (Bs)",
    }

    def pre_update(self, item):
        anterior = _valor_anterior(item, "estado")
        if anterior != "Anulada" and item.estado == "Anulada":
            for d in item.detalles:  # anular devuelve el stock
                d.producto.stock += d.cantidad
        elif anterior == "Anulada" and item.estado != "Anulada":
            raise Exception("Una venta anulada no puede reactivarse.")

    def pre_delete(self, item):
        if item.detalles:
            raise Exception("Elimine primero los ítems de la venta (o anúlela).")


db.create_all()  # crea las tablas si no existen

appbuilder.add_view(
    CategoriaConProductos, "Categorías", icon="fa-folder", category="Inventario"
)
appbuilder.add_view(ProductoModelView, "Productos", icon="fa-cube", category="Inventario")
appbuilder.add_view(ProveedorModelView, "Proveedores", icon="fa-truck", category="Inventario")
appbuilder.add_view(ClienteModelView, "Clientes", icon="fa-users", category="Ventas")
appbuilder.add_view(VentaModelView, "Ventas", icon="fa-shopping-cart", category="Ventas")
appbuilder.add_view_no_menu(DetalleVentaModelView)
