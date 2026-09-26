# PROMETHEUS — Misión 04 · Coevaluación

Aplicación Streamlit para la coevaluación de la Misión 04 — Protocolo de Oxigenación.

## Funcionalidad

- Acceso mediante ID institucional.
- Identificación automática del equipo mediante `estudiantes.csv`.
- El alumno declara dentro de la aplicación el rol que desempeñó.
- Evaluación de compañeros, excluyendo al propio alumno.
- Cinco criterios ponderados:
  - Cumplimiento del rol — 20 %
  - Identificación y razonamiento anatómico — 20 %
  - Integración espacial y representación — 20 %
  - Aplicación a Ingeniería Biomédica — 20 %
  - Colaboración, integración y calidad — 20 %
- Evidencia concreta y sugerencia de mejora.
- Registro persistente mediante GitHub Contents API.
- Generación de comprobante PDF después de un envío exitoso.
- El comprobante no contiene las calificaciones dadas a los compañeros.

## Estructura de estudiantes.csv

```csv
id,nombre_completo,mision04
123456,Nombre del alumno,1
123457,Otro alumno,1
123458,Otro alumno,2
```

No es necesario registrar el rol en `estudiantes.csv`; cada alumno lo selecciona en la aplicación.

## Streamlit Secrets

En Streamlit Community Cloud → Settings → Secrets:

```toml
GITHUB_TOKEN = "TU_TOKEN"
GITHUB_REPO = "TU_USUARIO/TU_REPOSITORIO_MISION04"
GITHUB_BRANCH = "main"
```

El token nunca debe aparecer en `app.py`, `estudiantes.csv` ni en el repositorio.

## Carpetas generadas en GitHub

```text
respuestas/
    mision04_ID.json

comprobantes/
    mision04_ID.pdf
```

Cada alumno tiene un registro asociado a su ID. Si vuelve a enviar la coevaluación, se actualiza su registro en lugar de crear múltiples archivos.

## Flujo

Alumno → ID → equipo → rol declarado → coevaluación → GitHub → comprobante PDF.

## Despliegue

En Streamlit Community Cloud:

- Repository: repositorio de Misión 04
- Branch: `main`
- Main file: `app.py`


## Archivos generados en GitHub

```text
results.csv
respuestas/mision04_ID.json
comprobantes/mision04_ID.pdf
```

`results.csv` se crea con la primera coevaluación y se actualiza con cada envío. El JSON individual se conserva como respaldo detallado.
