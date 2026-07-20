# SourcingPlus Visual Search Backend & Dashboard 🚀

Este es el backend de búsqueda visual y panel analítico para **SourcingPlus**, diseñado bajo una arquitectura limpia y modular en Python utilizando **FastAPI** y **SQLAlchemy**.

El microservicio se encarga de recibir sincronizaciones de catálogos de productos, procesar y normalizar imágenes para modelos de Inteligencia Artificial (CLIP), y buscar/sincronizar vectores en un índice vectorial serverless de **Pinecone** para búsquedas visuales en tiempo real. Adicionalmente, cuenta con persistencia de metadatos en una base de datos relacional local (SQLite) y un panel interactivo de analíticas en tiempo real (Frontend en Light Theme corporativo).

---

## 🌟 Funcionalidades de Última Generación

Este microservicio incorpora prácticas y características avanzadas que optimizan la latencia, la relevancia de búsqueda y la experiencia en e-commerce y retail sourcing:

1.  **Interfaz Web Integrada (Fase 8 - Consulting Light Theme):**
    *   Una aplicación web Single-Page (SPA) servida directamente desde el endpoint raíz (`GET /`) de la API. Incorpora una paleta de colores corporativa (azul zafiro, azul marino y gris pizarra) adecuada para perfiles de consultoría. Permite subir fotos por drag-and-drop, aplicar filtros y ver estadísticas de rendimiento.
2.  **Persistencia de Fichas de Producto e Hidratación (Fase 5):**
    *   Los metadatos ricos de los productos (título, descripción detallada, marca, URL de compra) se guardan de forma relacional en una base de datos SQLite integrada. Al realizar la búsqueda visual en Pinecone, el backend recupera los IDs coincidentes e "hidrata" automáticamente los resultados con su ficha completa de la base de datos SQL.
3.  **Búsqueda Híbrida / Multimodal (Fase 6):**
    *   Permite mezclar búsquedas visuales con refinamientos textuales (ej. subir la foto de una zapatilla y escribir "color azul" o "deportivo"). El backend genera embeddings de texto usando el codificador CLIP, mezcla vectorialmente ambos embeddings ponderadamente (`image_weight`) y realiza la búsqueda densa.
4.  **Caché Avanzado Multi-Clave de Embeddings:**
    *   Optimiza la latencia a **menos de 50 ms** almacenando embeddings en memoria (LRU Cache). Adapta las claves para incluir las refinaciones de texto, garantizando que búsquedas de la misma imagen con textos distintos no colisionen.
5.  **Filtros Numéricos y de Metadatos en Base Vectorial:**
    *   Inyección de filtros lógicos en Pinecone para rangos de precio (`min_price`, `max_price`), marcas (`brand`), categorías y stock disponible (`in_stock_only`).
6.  **Telemetría y Analíticas de Consulta en 2do Plano (Fase 7):**
    *   Registro de latencia, aciertos de caché y tendencias de productos de forma asíncrona mediante `BackgroundTasks` de FastAPI, garantizando que el guardado en disco no impacte la respuesta del usuario.

---

## 🛠️ Stack Tecnológico
*   **Lenguaje:** Python 3.10+
*   **Framework Web:** FastAPI (con Uvicorn para el servidor ASGI)
*   **Base de Datos Relacional / ORM:** SQLite & SQLAlchemy
*   **Base de Datos Vectorial:** Pinecone Serverless Spec (métrica `cosine`)
*   **Modelo de Embeddings (IA):** OpenAI CLIP (`openai/clip-vit-base-patch32` vía Hugging Face Transformers)
*   **Procesamiento de Imágenes:** Pillow (PIL) & NumPy
*   **Suite de Pruebas:** Pytest + Pytest-asyncio

---

## 🏗️ Estructura del Proyecto

```text
SourcingPlus-VisualSearch-Backend/
├── .github/
│   └── workflows/
│       └── tests.yml          # Pipeline de Integración Continua (CI) en GitHub Actions
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py       # Endpoints REST (ingesta, búsqueda, analíticas y logging)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache.py           # Sistema de Caché LRU de embeddings (Última generación)
│   │   ├── ingestor.py        # Ingestor de imágenes y normalización
│   │   └── vectorizer.py      # CLIP Vectorizer (visión/texto) y Pinecone Client
│   ├── static/                # Activos Frontend served directly on '/'
│   │   ├── app.js             # Lógica e integración con la API
│   │   ├── index.html         # Maquetación y estructura del Dashboard
│   │   └── style.css          # Estilo corporativo "Consulting Light Theme"
│   ├── __init__.py
│   ├── config.py              # Carga de variables de entorno y configuración
│   ├── database.py            # Inicialización de motor de base de datos relacional ORM
│   ├── main.py                # Entrada principal e inicializador de tablas
│   ├── models.py              # Modelos de tablas SQLite (Product, SearchLog)
│   └── schemas.py             # Modelos de validación Pydantic
├── docs/
│   ├── SOP.md                 # Procedimiento operativo estándar y guía de seguridad
│   ├── implementation_plan.md # Plan de implementación del ciclo de vida
│   ├── task.md                # Checklists de tareas completadas
│   └── walkthrough.md         # Walkthrough y reportes de pruebas ejecutadas
├── tests/
│   ├── test_api.py            # Pruebas integrales de endpoints REST e index.html
│   ├── test_database.py       # Pruebas de conectividad y consultas SQL
│   ├── test_hybrid.py         # Pruebas para filtros de precio, marcas y mezcla CLIP
│   ├── test_ingestor.py       # Pruebas de procesamiento y resizing de imágenes
│   ├── test_search.py         # Pruebas para filtros avanzados, stock y caché
│   └── test_vectorizer.py     # Pruebas de embeddings e indexación Pinecone
├── .env.example               # Plantilla de variables de configuración
├── .gitignore                 # Exclusiones de Git (secrets, db, cachés)
├── requirements.txt           # Dependencias del proyecto
└── README.md                  # Documentación del proyecto
```

---

## 🚀 Comenzando

### 1. Clonación e Instalación
Clona el repositorio y accede al directorio:
```bash
git clone https://github.com/juankgarcia700/SourcingPlus-VisualSearch-Backend.git
cd SourcingPlus-VisualSearch-Backend
```

Crea un entorno virtual e instálalo:
```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual (Windows)
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración del Entorno
Copia el archivo de ejemplo `.env.example` y renómbralo a `.env`:
```bash
copy .env.example .env
```
Abre el archivo `.env` y configura tus credenciales:
```ini
PINECONE_API_KEY=tu-clave-api-de-pinecone
PINECONE_INDEX_NAME=sourcingplus-visual-search
DATABASE_URL=sqlite:///./sourcingplus.db
USE_MOCK_EMBEDDINGS=True   # Cambia a False para descargar modelos CLIP locales reales
```

### 3. Ejecución del Servidor
Inicia el servidor local de desarrollo:
```bash
python -m uvicorn app.main:app --reload
```
Abre en tu navegador la dirección del servidor:
👉 **http://127.0.0.1:8000/** (Carga la aplicación web interactiva del Dashboard)
👉 **http://127.0.0.1:8000/docs** (Carga la interfaz de Swagger)

---

## 🔌 Especificación de la API (Endpoints Principales)

-   `POST /api/v1/sync`: Recibe listado de productos, procesa imágenes y sincroniza Pinecone y SQLite.
-   `POST /api/v1/search/file`: Recibe una foto (Multipart/form-data) y realiza búsquedas de coincidencia visual.
-   `POST /api/v1/search/url`: Recibe la URL de una foto (JSON body) y realiza búsquedas.
-   `GET /api/v1/analytics/stats`: Devuelve estadísticas del Dashboard (latencias, aciertos de caché).
-   `GET /api/v1/analytics/trending`: Devuelve la clasificación de los productos más buscados con éxito en la plataforma.

---

## 🧪 Ejecución de Pruebas
El proyecto cuenta con una completa suite de pruebas automatizadas que se ejecutan localmente con:
```bash
python -m pytest -v
```
Las 20 pruebas unitarias e integrales garantizan que cualquier cambio conserve la compatibilidad e integridad del código.
