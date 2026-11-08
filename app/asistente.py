"""Asistente de IA: sugiere reposición de stock y genera descripciones de producto."""
import datetime

from flask import flash, request
from flask_appbuilder import BaseView, expose, has_access
from sqlalchemy import func

from . import appbuilder, db
from .ia import IAError, consultar_gemini
from .models import Categoria, DetalleVenta, Producto, Proveedor, Venta


class AsistenteIAView(BaseView):
    route_base = "/asistente"
    default_view = "inicio"

    def _contexto(self, **extra):
        productos = db.session.query(Producto).order_by(Producto.nombre).all()
        return dict(productos=productos, respuesta=None, titulo_respuesta="", **extra)

    @expose("/")
    @has_access
    def inicio(self):
        return self.render_template("asistente.html", **self._contexto())

    @expose("/reposicion/", methods=["POST"])
    @has_access
    def reposicion(self):
        """Envía a la IA el stock bajo y las ventas de los últimos 30 días."""
        desde = datetime.datetime.now() - datetime.timedelta(days=30)
        vendidas = dict(
            db.session.query(DetalleVenta.producto_id, func.sum(DetalleVenta.cantidad))
            .join(Venta, DetalleVenta.venta_id == Venta.id)
            .filter(Venta.fecha >= desde, Venta.estado != "Anulada")
            .group_by(DetalleVenta.producto_id)
            .all()
        )
        bajos = (
            db.session.query(Producto, Proveedor.nombre)
            .join(Proveedor, Producto.proveedor_id == Proveedor.id)
            .filter(Producto.stock <= Producto.stock_minimo)
            .all()
        )
        ctx = self._contexto(titulo_respuesta="Sugerencia de reposición")
        if not bajos:
            ctx["respuesta"] = "No hay productos con stock bajo. No se necesita reponer nada."
            return self.render_template("asistente.html", **ctx)

        lineas = "\n".join(
            f"- {p.nombre} (proveedor: {prov}): stock {p.stock}, mínimo {p.stock_minimo}, "
            f"vendidas últimos 30 días: {int(vendidas.get(p.id, 0))}"
            for p, prov in bajos
        )
        prompt = (
            "Eres un asistente de inventario para una tienda. Con los datos siguientes, "
            "indica para cada producto cuántas unidades conviene pedir y por qué, "
            "ordenando de más a menos urgente. Sé breve y usa español.\n\n" + lineas
        )
        try:
            ctx["respuesta"] = consultar_gemini(prompt)
        except IAError as e:
            flash(str(e), "danger")
        return self.render_template("asistente.html", **ctx)

    @expose("/descripcion/", methods=["POST"])
    @has_access
    def descripcion(self):
        """Genera una descripción comercial y, si se pide, la guarda en el producto."""
        producto = db.session.get(Producto, request.form.get("producto_id", type=int))
        ctx = self._contexto(titulo_respuesta="Descripción generada")
        if not producto:
            flash("Seleccione un producto.", "warning")
            return self.render_template("asistente.html", **ctx)

        categoria = db.session.get(Categoria, producto.categoria_id)
        prompt = (
            "Escribe una descripción comercial atractiva de máximo 40 palabras, en español, "
            f"para el producto '{producto.nombre}' de la categoría '{categoria.nombre}'. "
            "No inventes especificaciones técnicas. Devuelve solo el texto."
        )
        try:
            texto = consultar_gemini(prompt, temperatura=0.7)
        except IAError as e:
            flash(str(e), "danger")
            return self.render_template("asistente.html", **ctx)

        if request.form.get("guardar") == "1":
            producto.descripcion = texto
            db.session.commit()
            flash(f"Descripción guardada en '{producto.nombre}'.", "success")
        ctx["respuesta"] = texto
        return self.render_template("asistente.html", **ctx)


appbuilder.add_view(
    AsistenteIAView, "Asistente IA", icon="fa-magic", category="Inteligencia Artificial"
)
