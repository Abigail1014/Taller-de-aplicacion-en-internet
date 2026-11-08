# Flujo de Git y GitHub (con evidencias)

Ejecuta estos comandos dentro de la carpeta `tienda_fab`. Reemplaza `TU_USUARIO` por tu usuario de GitHub.

## 1. Repositorio y primer commit

```bash
git init -b main
git config user.name "Tu Nombre"
git config user.email "tu_correo@ejemplo.com"
git add .gitignore .env.example requirements.txt config.py run.py README.md
git commit -m "chore: estructura inicial, configuración y dependencias"
```

En GitHub: **New repository** → nombre `tienda-fab` → sin README (ya existe) → Create.

```bash
git remote add origin https://github.com/TU_USUARIO/tienda-fab.git
git push -u origin main
```

## 2. Ramas por funcionalidad (una rama = una funcionalidad)

Para cada rama: crear → agregar archivos → commit descriptivo → subir → Pull Request → merge.

```bash
# Rama 1: modelos y CRUD
git switch -c feature/modelos-crud
git add app/__init__.py app/models.py app/views.py
git commit -m "feat: agrega 6 modelos relacionados y vistas CRUD con reglas de stock"
git push -u origin feature/modelos-crud

# Rama 2: reportes
git switch main
git switch -c feature/reportes
git add app/reportes.py app/templates/reporte.html
git commit -m "feat: agrega 3 reportes con filtros (ventas, inventario, más vendidos)"
git push -u origin feature/reportes

# Rama 3: inteligencia artificial
git switch main
git switch -c feature/ia-gemini
git add app/ia.py app/asistente.py app/templates/asistente.html
git commit -m "feat: integra Gemini para sugerir reposición y generar descripciones"
git push -u origin feature/ia-gemini

# Rama 4: seguridad y datos de demostración
git switch main
git switch -c feature/seguridad-roles
git add seed.py
git commit -m "feat: crea roles Vendedor, Almacen y Consulta y datos de demostración"
git push -u origin feature/seguridad-roles

# Rama 5: documentación
git switch main
git switch -c docs/documentacion
git add docs/ README.md
git commit -m "docs: agrega README y guía de flujo de Git"
git push -u origin docs/documentacion
```

> Si agregas más commits pequeños dentro de cada rama (por ejemplo, uno por modelo o por reporte), el historial queda más rico. Haz commits frecuentes.

## 3. Integrar con Pull Request (recomendado)

1. En GitHub aparece el botón **Compare & pull request** para cada rama.
2. Título descriptivo, descripción breve de lo que cambia → **Create pull request**.
3. **Merge pull request** → **Confirm merge**.
4. Localmente: `git switch main && git pull`.

Alternativa por consola (merge local):

```bash
git switch main
git merge --no-ff feature/modelos-crud -m "merge: integra modelos y CRUD"
git push origin main
```

`--no-ff` conserva visible la rama en el historial.

## 4. Evidencias para la entrega

```bash
git log --oneline --graph --decorate --all      # historial con ramas (captura de pantalla)
git branch -a                                   # ramas locales y remotas
git remote -v                                   # repositorio remoto
git log --stat --pretty=format:"%h %an %ad %s" --date=short > docs/historial_commits.txt
```

Capturas sugeridas:
- Salida de `git log --oneline --graph --decorate --all`.
- Pestaña **Branches** y **Pull requests** (cerrados/merged) en GitHub.
- Pestaña **Commits** de `main` y la página principal del repositorio final.

## 5. Convención de mensajes de commit

`tipo: descripción en presente` — tipos: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.
