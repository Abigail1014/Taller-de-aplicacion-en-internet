"""3 reportes con consultas reales a MySQL, filtros y resultados verificables."""
import datetime

from flask import request
from flask_appbuilder import BaseView, expose, has_access
from sqlalchemy import func

from . import appbuilder, db
from .models import Categoria, Cliente, DetalleVenta, Producto, Proveedor, Venta


def _fecha(texto, fin=False):
    """Convierte 'YYYY-MM-DD' en datetime. Si fin=True devuelve el día siguiente
    (para filtrar con '<' y así incluir todo el último día)."""
    if not texto:
        return None
    try:
        d = datetime.datetime.strptime(texto, "%Y-%m-%d")
    except ValueError:
        return None
    return d + datetime.timedelta(days=1) if fin else d


def _int(texto):
    try:
        return int(texto) if texto else None
    except ValueError:
        return None


def _bs(valor):
    return f"{float(valor or 0):,.2f}"


class ReportesView(BaseView):
    route_base = "/reportes"
    default_view = "ventas"

    # ---- Reporte 1: ventas por rango de fechas, cliente y estado ----------
    @expose("/ventas/")
    @has_access
    def ventas(self):
        desde = request.args.get("desde", "")
        hasta = request.args.get("hasta", "")
        cliente_id = _int(request.args.get("cliente"))
        estado = request.args.get("estado", "")

        total_linea = DetalleVenta.cantidad * DetalleVenta.precio_unitario
        q = (
            db.session.query(
                Venta.id,
                Venta.fecha,
                Cliente.nombre,
                Cliente.apellido,
                Venta.estado,
                func.coalesce(func.sum(total_linea), 0).label("total"),
            )
            .join(Cliente, Venta.cliente_id == Cliente.id)
            .outerjoin(DetalleVenta, DetalleVenta.venta_id == Venta.id)
        )
        if _fecha(desde):
            q = q.filter(Venta.fecha >= _fecha(desde))
        if _fecha(hasta):
            q = q.filter(Venta.fecha < _fecha(hasta, fin=True))
        if cliente_id:
            q = q.filter(Venta.cliente_id == cliente_id)
        if estado:
            q = q.filter(Venta.estado == estado)
        q = q.group_by(
            Venta.id, Venta.fecha, Cliente.nombre, Cliente.apellido, Venta.estado
        ).order_by(Venta.fecha.desc())
        filas = q.all()

        suma = sum(float(f.total) for f in filas if f.estado != "Anulada")
        return self.render_template(
            "reporte.html",
            titulo="Reporte de ventas",
            filtros=[
                {"name": "desde", "label": "Desde", "tipo": "date", "valor": desde},
                {"name": "hasta", "label": "Hasta", "tipo": "date", "valor": hasta},
                {
                    "name": "cliente", "label": "Cliente", "tipo": "select",
                    "valor": cliente_id or "",
                    "opciones": [
                        (c.id, f"{c.nombre} {c.apellido}")
                        for c in db.session.query(Cliente).order_by(Cliente.apellido)
                    ],
                },
                {
                    "name": "estado", "label": "Estado", "tipo": "select",
                    "valor": estado,
                    "opciones": [(e, e) for e in ("Pagada", "Pendiente", "Anulada")],
                },
            ],
            columnas=["N.º", "Fecha", "Cliente", "Estado", "Total (Bs)"],
            filas=[
                [f.id, f.fecha.strftime("%Y-%m-%d %H:%M"),
                 f"{f.nombre} {f.apellido}", f.estado, _bs(f.total)]
                for f in filas
            ],
            resumen=[
                ("Ventas encontradas", len(filas)),
                ("Total sin anuladas (Bs)", _bs(suma)),
            ],
        )

    # ---- Reporte 2: inventario y alertas de stock bajo ---------------------
    @expose("/inventario/")
    @has_access
    def inventario(self):
        categoria_id = _int(request.args.get("categoria"))
        proveedor_id = _int(request.args.get("proveedor"))
        solo_bajo = request.args.get("solo_bajo") == "1"

        q = (
            db.session.query(Producto, Categoria.nombre, Proveedor.nombre)
            .join(Categoria, Producto.categoria_id == Categoria.id)
            .join(Proveedor, Producto.proveedor_id == Proveedor.id)
        )
        if categoria_id:
            q = q.filter(Producto.categoria_id == categoria_id)
        if proveedor_id:
            q = q.filter(Producto.proveedor_id == proveedor_id)
        if solo_bajo:
            q = q.filter(Producto.stock <= Producto.stock_minimo)
        q = q.order_by(Producto.stock.asc())
        filas = q.all()

        valor_total = sum(float(p.precio) * p.stock for p, _, _ in filas)
        n_bajo = sum(1 for p, _, _ in filas if p.stock <= p.stock_minimo)
        return self.render_template(
            "reporte.html",
            titulo="Inventario y stock bajo",
            filtros=[
                {
                    "name": "categoria", "label": "Categoría", "tipo": "select",
                    "valor": categoria_id or "",
                    "opciones": [(c.id, c.nombre) for c in db.session.query(Categoria).order_by(Categoria.nombre)],
                },
                {
                    "name": "proveedor", "label": "Proveedor", "tipo": "select",
                    "valor": proveedor_id or "",
                    "opciones": [(p.id, p.nombre) for p in db.session.query(Proveedor).order_by(Proveedor.nombre)],
                },
                {"name": "solo_bajo", "label": "Solo stock bajo", "tipo": "checkbox", "valor": solo_bajo},
            ],
            columnas=["Código", "Producto", "Categoría", "Proveedor", "Stock", "Mínimo", "Valor (Bs)", "Alerta"],
            filas=[
                [p.codigo, p.nombre, cat, prov, p.stock, p.stock_minimo,
                 _bs(float(p.precio) * p.stock),
                 "REPONER" if p.stock <= p.stock_minimo else "OK"]
                for p, cat, prov in filas
            ],
            resumen=[
                ("Productos", len(filas)),
                ("Con stock bajo", n_bajo),
                ("Valor del inventario (Bs)", _bs(valor_total)),
            ],
        )

    # ---- Reporte 3: productos más vendidos --------------------------------
    @expose("/top-productos/")
    @has_access
    def top_productos(self):
        desde = request.args.get("desde", "")
        hasta = request.args.get("hasta", "")
        categoria_id = _int(request.args.get("categoria"))
        limite = min(_int(request.args.get("limite")) or 10, 100)

        ingreso = func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario)
        q = (
            db.session.query(
                Producto.codigo,
                Producto.nombre,
                Categoria.nombre.label("categoria"),
                func.sum(DetalleVenta.cantidad).label("unidades"),
                ingreso.label("ingreso"),
            )
            .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
            .join(Venta, DetalleVenta.venta_id == Venta.id)
            .join(Categoria, Producto.categoria_id == Categoria.id)
            .filter(Venta.estado != "Anulada")
        )
        if _fecha(desde):
            q = q.filter(Venta.fecha >= _fecha(desde))
        if _fecha(hasta):
            q = q.filter(Venta.fecha < _fecha(hasta, fin=True))
        if categoria_id:
            q = q.filter(Producto.categoria_id == categoria_id)
        q = (
            q.group_by(Producto.id, Producto.codigo, Producto.nombre, Categoria.nombre)
            .order_by(func.sum(DetalleVenta.cantidad).desc())
            .limit(limite)
        )
        filas = q.all()

        return self.render_template(
            "reporte.html",
            titulo="Productos más vendidos (excluye ventas anuladas)",
            filtros=[
                {"name": "desde", "label": "Desde", "tipo": "date", "valor": desde},
                {"name": "hasta", "label": "Hasta", "tipo": "date", "valor": hasta},
                {
                    "name": "categoria", "label": "Categoría", "tipo": "select",
                    "valor": categoria_id or "",
                    "opciones": [(c.id, c.nombre) for c in db.session.query(Categoria).order_by(Categoria.nombre)],
                },
                {"name": "limite", "label": "Top", "tipo": "number", "valor": limite},
            ],
            columnas=["#", "Código", "Producto", "Categoría", "Unidades", "Ingresos (Bs)"],
            filas=[
                [i, f.codigo, f.nombre, f.categoria, int(f.unidades), _bs(f.ingreso)]
                for i, f in enumerate(filas, start=1)
            ],
            resumen=[
                ("Productos listados", len(filas)),
                ("Unidades vendidas", sum(int(f.unidades) for f in filas)),
                ("Ingresos (Bs)", _bs(sum(float(f.ingreso) for f in filas))),
            ],
        )


appbuilder.add_view_no_menu(ReportesView())
appbuilder.add_link("Ventas", href="/reportes/ventas/", icon="fa-line-chart", category="Reportes")
appbuilder.add_link("Inventario y stock bajo", href="/reportes/inventario/", icon="fa-warehouse", category="Reportes")
appbuilder.add_link("Más vendidos", href="/reportes/top-productos/", icon="fa-trophy", category="Reportes")
