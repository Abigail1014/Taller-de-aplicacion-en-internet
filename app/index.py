"""Portada de inicio de ELY: vitrina de la tienda + resumen para el personal."""
from flask_appbuilder import IndexView, expose
from flask_login import current_user

# Colores suaves para las tarjetas de producto (uno por categoría)
COLORES = ["#FFE8D6", "#E3F2FF", "#E8F7E4", "#FFF3C4", "#F3E5FF", "#FFE0E6"]
# Emoji por categoría; las que no estén aquí usan 📦
EMOJIS = {"Bebidas": "🥤", "Snacks": "🍿", "Limpieza": "🧴", "Papelería": "✏️"}


class ElyIndexView(IndexView):
    index_template = "ely_inicio.html"

    @expose("/")
    def index(self):
        # Importes dentro del método para evitar importaciones circulares
        from sqlalchemy import func

        from . import db
        from .models import Categoria, Cliente, DetalleVenta, Producto, Venta

        s = db.session
        cats = s.query(Categoria).order_by(Categoria.nombre).all()
        color_de = {c.id: COLORES[i % len(COLORES)] for i, c in enumerate(cats)}
        categorias = [{"nombre": c.nombre, "emoji": EMOJIS.get(c.nombre, "📦")} for c in cats]

        productos = []
        for p in s.query(Producto).order_by(Producto.nombre).limit(40).all():
            if p.stock <= 0:
                estado = "agotado"
            elif p.stock <= p.stock_minimo:
                estado = "ultimas"
            else:
                estado = "ok"
            productos.append({
                "nombre": p.nombre,
                "precio": f"{float(p.precio):,.2f}",
                "categoria": p.categoria.nombre,
                "emoji": EMOJIS.get(p.categoria.nombre, "📦"),
                "color": color_de.get(p.categoria_id, COLORES[0]),
                "estado": estado,
            })

        stats = None
        if current_user.is_authenticated:
            total = (
                s.query(func.coalesce(func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario), 0))
                .join(Venta, DetalleVenta.venta_id == Venta.id)
                .filter(Venta.estado != "Anulada")
                .scalar()
            )
            stats = {
                "productos": s.query(Producto).count(),
                "bajo": s.query(Producto).filter(Producto.stock <= Producto.stock_minimo).count(),
                "clientes": s.query(Cliente).count(),
                "ventas": s.query(Venta).filter(Venta.estado != "Anulada").count(),
                "total": f"{float(total):,.2f}",
            }
        return self.render_template(
            self.index_template,
            appbuilder=self.appbuilder,
            categorias=categorias,
            productos=productos,
            stats=stats,
        )