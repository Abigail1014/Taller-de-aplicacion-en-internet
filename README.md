# Tienda – Inventario y Ventas

Aplicación web con **Flask-AppBuilder**, **Python** y **MySQL**: gestión de productos, clientes y ventas, con asistente de IA (Google Gemini, capa gratuita) y reportes.

## Cumplimiento de requisitos

| Requisito | Dónde está |
|---|---|
| 6 tablas relacionadas | `app/models.py`: Categoria, Proveedor, Producto, Cliente, Venta, DetalleVenta |
| CRUD | `app/views.py` (listar, crear, consultar, editar, eliminar) |
| Reglas de negocio | Stock se descuenta al vender, se devuelve al anular/eliminar; no se elimina con datos dependientes; precio congelado en la venta |
| IA gratuita | `app/ia.py` + `app/asistente.py` (Gemini API): sugiere reposición y genera descripciones |
| 3 reportes con filtros | `app/reportes.py`: ventas, inventario/stock bajo, más vendidos |
| Autenticación y permisos | Login de FAB (`AUTH_DB`), sin registro público, roles `Admin`, `Vendedor`, `Almacen`, `Consulta` (`seed.py`) |
| Git/GitHub | `docs/GIT_FLUJO.md` |

## Modelo de datos

```
Categoria 1──N Producto N──1 Proveedor
Cliente   1──N Venta 1──N DetalleVenta N──1 Producto
```

## Instalación

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # edita usuario/clave de MySQL y GEMINI_API_KEY
```

Crear la base de datos en MySQL:

```sql
CREATE DATABASE tienda_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Inicializar y ejecutar:

```bash
flask --app run fab create-admin   # crea el usuario administrador
python seed.py                     # roles y datos de demostración
python run.py                      # http://127.0.0.1:8080
```

Las tablas se crean automáticamente al iniciar la aplicación.

## IA (gratuita)

1. Crea una API key gratis en <https://aistudio.google.com/apikey>.
2. Pégala en `.env` como `GEMINI_API_KEY`.
3. Si Google cambia el nombre del modelo, ajusta `GEMINI_MODEL` en `.env` (revisa la lista vigente en AI Studio).

Menú **Inteligencia Artificial → Asistente IA**.

## Cómo verificar los reportes

Con los datos de `seed.py` puedes comprobar a mano los resultados, por ejemplo con MySQL:

```sql
SELECT v.id, SUM(d.cantidad * d.precio_unitario) AS total
FROM venta v JOIN detalle_venta d ON d.venta_id = v.id
GROUP BY v.id;
```

El resultado debe coincidir con el reporte **Ventas**.
