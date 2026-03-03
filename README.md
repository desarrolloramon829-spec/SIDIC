# S.I.D.I.C v2.0

## Sistema de Información Delictual e Inteligencia Criminal

<p align="center">
  <strong>Aplicación de escritorio para procesamiento de datos delictuales y generación de informes estadísticos profesionales</strong>
</p>

---

## Descripción

S.I.D.I.C es una aplicación de escritorio desarrollada en Python para la **Comisaría Amaicha del Valle, Tucumán, Argentina**. Procesa datos geográficos delictuales provenientes de QGIS (shapefiles) y genera informes estadísticos completos en formatos Excel, Word y PDF.

### Características principales

- **Lectura de archivos GIS**: Shapefile (.shp), GeoJSON, KML, GeoPackage y CSV con detección automática de encoding (chardet)
- **Hasta 6 períodos comparativos**: Análisis temporal con modos VS_PRINCIPAL, VS_ANTERIOR y AMBAS
- **12+ tablas estadísticas**: Cuadro de referencia, modalidades, franjas horarias, matrices cruzadas, mencionados, aprehendidos, esclarecimiento
- **Gráficos profesionales**: Barras agrupadas con estilo policial (matplotlib)
- **Exportación múltiple**: Excel (.xlsx), Word (.docx) y PDF nativo (reportlab)
- **Interfaz moderna**: Tema oscuro policial con drag & drop, construida con PyQt6
- **Categorización configurable**: Categorías de delito definidas en JSON, no hardcodeadas
- **Persistencia de proyectos**: Archivos .sidic (SQLite) para guardar/cargar sesiones

### Arquitectura v2

La aplicación fue reconstruida con **Clean Architecture** de 4 capas y patrón **MVVM** para la presentación:

```
sidic/
├── domain/         # Entidades, enums, servicios de dominio, protocolos
├── application/    # DTOs, casos de uso
├── infrastructure/ # Lectores GIS, exportadores, repositorios SQLite
├── presentation/   # ViewModels, Widgets PyQt6, MainWindow, QSS
├── config/         # defaults.json configurable, loader con caché
└── tests/          # 207 tests unitarios (pytest)
```

---

## Requisitos

- **Windows 10/11**
- **Python 3.11+**

---

## Instalación

### Opción 1: pip install (desarrollo)

```bash
git clone https://github.com/developerpoliciatuc-wq/S.I.D.I.C.git
cd S.I.D.I.C
pip install -e ".[dev]"
```

### Opción 2: requirements.txt

```bash
git clone https://github.com/developerpoliciatuc-wq/S.I.D.I.C.git
cd S.I.D.I.C
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Opción 3: install.bat (Windows)

```
install.bat
```

---

## Uso

### Interfaz Gráfica

```bash
# Con entry point instalado
sidic

# O directamente
python -m sidic

# O con script batch
run_sidic.bat
```

### Línea de Comandos

```bash
sidic-cli --input "datos/hechos.shp" \
          --output "reportes/informe.xlsx" \
          --format excel \
          --start-date 2024-01-01 \
          --end-date 2024-01-31 \
          --verbose
```

---

## Reportes Generados

### Tablas incluidas

| Tabla                   | Descripción                                    |
| ----------------------- | ---------------------------------------------- |
| Cuadro de Referencia    | Símbolo, delito, cantidad (ROBOS/HURTOS/Total) |
| Delitos con Modalidades | Tipo de delito y modalidad con cantidades      |
| Días de la Semana       | Distribución por día (Lunes a Domingo)         |
| Franja Horaria          | Distribución por 6 franjas definidas           |
| Movilidad               | Medios de movilidad utilizados                 |
| Armas                   | Armas/medios en robos agravados                |
| Ámbito de Ocurrencia    | Lugar donde ocurrieron los hechos              |
| Matriz Delito × Día     | Tabla cruzada delitos por días                 |
| Matriz Delito × Franja  | Tabla cruzada delitos por franjas              |
| Mencionados             | Lista de "Un tal..." con datos                 |
| Aprehendidos            | Personas detenidas con clasificación           |
| Esclarecimiento         | Índice SI / NO / PARCIAL                       |

### Franjas Horarias

| Franja     | Horario       |
| ---------- | ------------- |
| MADRUGADA  | 00:00 - 04:59 |
| MAÑANA     | 05:00 - 08:59 |
| VESPERTINA | 09:00 - 12:59 |
| SIESTA     | 13:00 - 16:59 |
| TARDE      | 17:00 - 19:59 |
| NOCHE      | 20:00 - 23:59 |

---

## Configuración

La categorización de delitos y el mapeo de campos se configura en `sidic/config/defaults.json`.

Secciones principales:

- **categorias**: mapeo delito → categoría (ROBOS, HURTOS, ESTAFAS, etc.)
- **robo_agravado**: palabras clave que califican un robo como agravado
- **simbolos**: símbolo Unicode, color y relleno por delito para cuadro de referencia
- **field_mappings**: mapeo de nombres de columnas GIS a campos internos
- **chart_config**: colores y estilos de gráficos

---

## Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=sidic --cov-report=html
```

**207 tests unitarios** cubriendo:
- Enums (CategoriaDelito, FranjaHoraria, DiaSemana, TipoEsclarecimiento, etc.)
- Modelos (CrimeRecord, MentionedPerson, Apprehended, PeriodData, ReportData)
- Servicios de dominio (DelitoCategorizer, PeriodFilter, CategoryFilter, StatisticsCalculator, PeriodComparator)
- Infraestructura (parse_utils, FieldMapper)
- DTOs de aplicación

---

## Generar Ejecutable

```bash
pip install pyinstaller
pyinstaller --name "SIDIC" --onefile --windowed -p . sidic/app.py
```

---

## Dependencias principales

| Paquete      | Uso                          |
| ------------ | ---------------------------- |
| PyQt6        | Interfaz gráfica             |
| pandas       | Procesamiento de datos       |
| geopandas    | Lectura de archivos GIS      |
| shapely      | Geometría espacial           |
| fiona        | Backend de lectura GIS       |
| matplotlib   | Generación de gráficos       |
| openpyxl     | Exportación a Excel          |
| python-docx  | Exportación a Word           |
| reportlab    | Generación nativa de PDF     |
| chardet      | Detección de encoding        |

---

## Licencia

MIT License — Ver [LICENSE](LICENSE)

---

**S.I.D.I.C v2.0.0** — Sistema de Información Delictual e Inteligencia Criminal
