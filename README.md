# SourcingPlus Visual Search Backend 🚀

Este es el backend de búsqueda visual para **SourcingPlus**, diseñado bajo una arquitectura limpia y modular en Python utilizando **FastAPI**. 

El microservicio se encarga de recibir sincronizaciones de catálogos de productos, procesar y normalizar imágenes para modelos de Inteligencia Artificial (CLIP), y buscar/sincronizar vectores en un índice vectorial serverless de **Pinecone** para búsquedas visuales en tiempo real.

---

## 🌟 Funcionalidades de Última Generación

Este microservicio incorpora prácticas y características avanzadas que optimizan la latencia, la relevancia de búsqueda y la experiencia en e-commerce y retail sourcing:

1.  **Caché de Embeddings en Memoria (Bypass de Latencia):**
    *   Generar embeddings con modelos de Deep Learning (como CLIP) es costoso a nivel de CPU/GPU. El sistema integra un caché LRU (Least Recently Used) que asocia hashes de imágenes y URLs con sus vectores calculados. Las búsquedas repetidas se resuelven en **menos de 50 ms** sin volver a descargar imágenes ni correr el modelo de IA.
2.  **Filtrado por Umbral de Similitud (`score_threshold`):**
    *   Filtra dinámicamente resultados irrelevantes. Si una imagen no tiene suficiente similitud de diseño con el catálogo, la API rechaza coincidencias débiles (ej. similitud < 75%) reduciendo el ruido en el frontend.
3.  **Filtros de Negocio en Base Vectorial (`in_stock_only`):**
    *   Permite excluir productos sin existencias en tiempo real inyectando filtros lógicos (`inventory > 0`) directamente en la consulta de Pinecone, evitando que los clientes encuentren productos agotados en sus búsquedas visuales.
4.  **Búsqueda Segmentada por Metadatos:**
    *   Permite filtrar búsquedas dentro de categorías específicas, optimizando los tiempos de respuesta y la precisión en catálogos B2B masivos.

---

## 🛠️ Stack Tecnológico
*   **Lenguaje:** Python 3.10+
*   **Framework Web:** FastAPI (con Uvicorn para el servidor ASGI)
*   **Procesamiento de Imágenes:** Pillow (PIL) & NumPy
*   **Modelo de Embeddings (IA):** OpenAI CLIP (`openai/clip-vit-base-patch32` vía Hugging Face Transformers)
*   **Base de Datos Vectorial:** Pinecone Serverless Spec (métrica `cosine`)
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
│   │   └── endpoints.py       # Endpoints REST (salud, sincronización y búsqueda visual)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache.py           # Sistema de Caché LRU de embeddings (Última generación)
│   │   ├── ingestor.py        # Ingestor de imágenes y normalización (Subagent A-1)
│   │   └── vectorizer.py      # Generador de embeddings e indexador Pinecone (Subagent A-2)
│   ├── __init__.py
│   ├── config.py              # Carga de variables de entorno y configuración
│   ├── main.py                # Entrada principal de la aplicación FastAPI
│   └── schemas.py             # Modelos de validación Pydantic
├── tests/
│   ├── test_api.py            # Pruebas integrales de endpoints REST
│   ├── test_ingestor.py       # Pruebas de procesamiento y resizing de imágenes
│   ├── test_vectorizer.py     # Pruebas de embeddings e indexación Pinecone
│   └── test_search.py         # Pruebas para filtros avanzados, umbrales y caché
├── .env.example               # Plantilla de variables de configuración
├── .gitignore                 # Exclusiones de Git para claves y caché
├── requirements.txt           # Dependencias del proyecto
└── README.md                  # Documentación del proyecto
```

---

## 🚀 Comenzando

### 1. Requisitos Previos
Asegúrate de tener instalado Python (versión 3.10 o superior) y Git en tu equipo.

### 2. Clonación e Instalación
Clona el repositorio en tu máquina local y accede al directorio:
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

### 3. Configuración del Entorno
Copia el archivo de ejemplo `.env.example` y renómbralo a `.env`:
```bash
copy .env.example .env
```
Abre el archivo `.env` y configura tus credenciales reales si deseas conectarte a la base de datos real de Pinecone:
```ini
PINECONE_API_KEY=tu-clave-api-de-pinecone
PINECONE_INDEX_NAME=sourcingplus-visual-search
USE_MOCK_EMBEDDINGS=False   # Cambia a True para probar offline sin descargar modelos pesados ni usar claves
```

### 4. Ejecución del Servidor
Inicia el servidor local de desarrollo:
```bash
uvicorn app.main:app --reload
```
Accede a la documentación interactiva Swagger en:
👉 **http://127.0.0.1:8000/docs**

---

## 🔌 Especificación de la API (Endpoints Avanzados)

### A. Sincronización de Catálogo
*   **Ruta:** `POST /api/v1/sync`
*   **Descripción:** Descarga de forma concurrente, normaliza e indexa imágenes en Pinecone mapeando SKU, precio, categoría e inventario.

### B. Búsqueda por Archivo (Snap & Shop)
*   **Ruta:** `POST /api/v1/search/file`
*   **Formato de entrada:** `multipart/form-data`
*   **Parámetros:**
    *   `file` (Archivo de imagen: PNG, JPEG)
    *   `top_k` (Entero, opcional, por defecto 10): Número de coincidencias.
    *   `score_threshold` (Flotante, opcional, por defecto 0.0): Retorna solo productos con similitud superior al valor (ej. `0.75`).
    *   `in_stock_only` (Booleano, opcional, por defecto `false`): Si es `true`, filtra productos con inventario mayor a 0.
    *   `category` (Cadena, opcional): Restringe la búsqueda a una categoría.

### C. Búsqueda por URL (Screenshot / Social commerce)
*   **Ruta:** `POST /api/v1/search/url`
*   **Cuerpo (JSON):**
    ```json
    {
      "image_url": "https://url-de-la-imagen.jpg",
      "top_k": 5,
      "score_threshold": 0.70,
      "in_stock_only": true,
      "category": "Calzado"
    }
    ```

---

## 🧪 Ejecución de Pruebas

El proyecto cuenta con una completa suite de pruebas automatizadas que se ejecutan localmente con:
```bash
python -m pytest -v
```

---

## 🛡️ Integración Continua (CI)

Este proyecto está integrado con **GitHub Actions**. Cada vez que realices un `push` o crees un `Pull Request` hacia la rama `main`, GitHub ejecutará automáticamente la suite de pruebas para verificar que el código no contenga errores ni dependencias rotas antes de integrarse.
