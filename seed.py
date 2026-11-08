"""Inicializa roles y datos de demostración.

Uso (con el entorno virtual activo y MySQL en marcha):
    flask --app run fab create-admin        # crea el usuario administrador
    python seed.py                          # crea roles y datos de ejemplo
"""
import datetime

from flask_appbuilder.security.sqla.models import PermissionView

from app import app, appbuilder, db
from app.models import Categoria, Cliente, DetalleVenta, Producto, Proveedor, Venta

NOMBRES_VISTAS = {
    "inventario": {"CategoriaConProductos", "ProductoModelView", "ProveedorModelView",
                   "Categorías", "Productos", "Proveedores", "Inventario"},
    "ventas": {"ClienteModelView", "VentaModelView", "DetalleVentaModelView",
               "Clientes", "Ventas"},
    "reportes": {"ReportesView", "Reportes", "Ventas",
             "Inventario y stock bajo", "Más vendidos"},
    "ia": {"AsistenteIAView", "Asistente IA", "Inteligencia Artificial"},
}
SOLO_LECTURA = {"can_list", "can_show", "menu_access", "can_info"}


def _dar(sm, rol, vistas, permiso_ok):
    for pv in db.session.query(PermissionView).all():
        if pv.view_menu.name in vistas and permiso_ok(pv.permission.name):
            sm.add_permission_role(rol, pv)


def crear_roles():
    sm = appbuilder.sm

    # Vendedor: gestiona clientes y ventas (CRUD), consulta inventario, usa reportes e IA
    vendedor = sm.add_role("Vendedor")
    _dar(sm, vendedor, NOMBRES_VISTAS["ventas"], lambda p: not p.startswith("can_delete"))
    _dar(sm, vendedor, NOMBRES_VISTAS["inventario"], lambda p: p in SOLO_LECTURA)
    _dar(sm, vendedor, NOMBRES_VISTAS["reportes"], lambda p: True)
    _dar(sm, vendedor, NOMBRES_VISTAS["ia"], lambda p: True)

    # Almacén: gestiona inventario (CRUD) y reportes; no toca ventas
    almacen = sm.add_role("Almacen")
    _dar(sm, almacen, NOMBRES_VISTAS["inventario"], lambda p: True)
    _dar(sm, almacen, NOMBRES_VISTAS["reportes"], lambda p: True)

    # Consulta: solo lectura
    consulta = sm.add_role("Consulta")
    for clave in ("inventario", "ventas"):
        _dar(sm, consulta, NOMBRES_VISTAS[clave], lambda p: p in SOLO_LECTURA)
    _dar(sm, consulta, NOMBRES_VISTAS["reportes"], lambda p: True)
    print("Roles creados: Vendedor, Almacen, Consulta (+ Admin integrado)")


def crear_datos_demo():
    if db.session.query(Categoria).count():
        print("Ya existen datos; no se insertan los de demostración.")
        return
    cats = [Categoria(nombre=n) for n in ("Bebidas", "Snacks", "Limpieza", "Papelería")]
    provs = [
        Proveedor(nombre="Distribuidora Norte", telefono="3-8521234", email="ventas@norte.bo"),
        Proveedor(nombre="Importadora Amazonía", telefono="3-8525678", email="info@amazonia.bo"),
    ]
    db.session.add_all(cats + provs)
    db.session.flush()

    prods = [
        Producto(codigo="BEB-001", nombre="Agua mineral 600ml", precio=3.50, stock=120, stock_minimo=30, categoria=cats[0], proveedor=provs[0]),
        Producto(codigo="BEB-002", nombre="Refresco cola 2L", precio=12.00, stock=8, stock_minimo=15, categoria=cats[0], proveedor=provs[0]),
        Producto(codigo="SNK-001", nombre="Papas fritas 150g", precio=9.00, stock=40, stock_minimo=20, categoria=cats[1], proveedor=provs[1]),
        Producto(codigo="SNK-002", nombre="Galletas de chocolate", precio=6.50, stock=4, stock_minimo=10, categoria=cats[1], proveedor=provs[1]),
        Producto(codigo="LIM-001", nombre="Detergente 1kg", precio=22.00, stock=25, stock_minimo=10, categoria=cats[2], proveedor=provs[0]),
        Producto(codigo="PAP-001", nombre="Cuaderno 100 hojas", precio=8.00, stock=60, stock_minimo=15, categoria=cats[3], proveedor=provs[1]),
    ]
    clientes = [
        Cliente(nombre="Ana", apellido="Rojas", documento="1234567"),
        Cliente(nombre="Luis", apellido="Mamani", documento="7654321"),
        Cliente(nombre="Marta", apellido="Suárez", documento="1122334"),
    ]
    db.session.add_all(prods + clientes)
    db.session.flush()

    hoy = datetime.datetime.now()
    plan = [
        (clientes[0], 2, "Pagada", [(prods[0], 6), (prods[2], 3)]),
        (clientes[1], 5, "Pagada", [(prods[1], 2), (prods[4], 1)]),
        (clientes[2], 9, "Pendiente", [(prods[5], 4)]),
        (clientes[0], 14, "Anulada", [(prods[3], 2)]),
    ]
    for cliente, dias, estado, items in plan:
        v = Venta(cliente=cliente, estado=estado, fecha=hoy - datetime.timedelta(days=dias))
        db.session.add(v)
        for prod, cant in items:
            db.session.add(DetalleVenta(venta=v, producto=prod, cantidad=cant, precio_unitario=prod.precio))
            if estado != "Anulada":
                prod.stock -= cant  # coherente con la regla de negocio
    db.session.commit()
    print("Datos de demostración insertados.")


if __name__ == "__main__":
    with app.app_context():
        crear_roles()
        crear_datos_demo()
