# Standard Operating Procedure (SOP) & Security Guidelines

Este documento establece los procedimientos operativos estándar, las directrices de seguridad y las reglas de integridad del código del proyecto **SourcingPlus Visual Search Backend**.

---

## 1. Control de Privilegios y Acceso al Código Fuente

Para garantizar la integridad y seguridad del código del proyecto, se establecen las siguientes reglas de protección y control de acceso:

### 1.1 Privilegios del Repositorio en GitHub
- **Propietario y Único Editor Autorizado**: El usuario **`juankgarcia700`** es el único titular de los derechos de edición y autoría del repositorio.
- **Configuración de Rama Protegida (`main`)**:
  - Se debe habilitar la regla de **Branch Protection** en GitHub para la rama `main`.
  - **Restricción de Push**: Deshabilitar el acceso de escritura directa a cualquier usuario que no sea `juankgarcia700`.
  - **Prohibir Force Push**: Queda estrictamente deshabilitada la opción `Allow force pushes` para evitar la sobreescritura accidental del historial de commits.
  - **Prohibir Deletion**: Queda deshabilitada la opción `Allow deletions` de la rama `main`.

### 1.2 Firmas e Identidad del Desarrollador (Anti-Fugas Corporativas)
Para evitar dejar firmas o trazas vinculadas a cuentas de correo corporativas en la laptop de trabajo, cualquier commit debe configurarse localmente con las credenciales personales de GitHub del usuario:
```bash
# Configuración exclusiva para este repositorio
git config user.name "juankgarcia700"
git config user.email "juankgarcia700@users.noreply.github.com"
```
*Procedimiento Obligatorio*: Al finalizar cada sesión de desarrollo en equipos corporativos locales, se debe borrar físicamente la carpeta del proyecto para asegurar que no queden copias locales persistentes fuera del almacenamiento seguro en la nube.

---

## 2. Gestión de Secretos y Seguridad de Variables de Entorno

### 2.1 Protección de Llaves de API (Pinecone / OpenAI)
- Queda **estrictamente prohibido** escribir llaves de API (`PINECONE_API_KEY`, `OPENAI_API_KEY`) directamente en el código fuente.
- Todas las variables se deben cargar dinámicamente desde el archivo de entorno seguro `.env` a través de Pydantic Settings (`app/config.py`).
- El archivo `.env` está registrado en `.gitignore` para evitar que sea subido a GitHub por error.

### 2.2 Exclusión de Archivos Locales y Bases de Datos
- Las bases de datos locales creadas durante la ejecución (como `sourcingplus.db`) se consideran temporales y locales. Están excluidas del repositorio mediante la regla `*.db` en el archivo `.gitignore`.
- Las cachés de ejecución y pruebas (`.pytest_cache/`, `__pycache__/`) están igualmente ignoradas para mantener limpio el repositorio.

---

## 3. Integridad y Calidad del Código (Control de Cambios)

Cualquier adición o modificación al código del backend debe cumplir estrictamente con los siguientes pasos de control de calidad:

### 3.1 Suite de Pruebas Automatizadas
Antes de realizar cualquier `git commit` y subir cambios a la nube, es mandatorio ejecutar la suite de pruebas unitarias en el entorno de desarrollo local o Codespaces:
```bash
python -m pytest -v
```
El pipeline de Integración Continua (CI) en **GitHub Actions** (`.github/workflows/tests.yml`) bloqueará cualquier Pull Request que contenga pruebas fallidas.

### 3.2 Estructura del Código y Modularidad
El código se organiza siguiendo el principio de separación de responsabilidades:
1. **`app/schemas.py`**: Cualquier cambio en las APIs debe documentarse primero aquí actualizando los modelos Pydantic de entrada y salida.
2. **`app/models.py`**: Cualquier cambio en la persistencia física (SQLite) debe agregarse en forma de columnas o nuevas tablas ORM.
3. **`app/services/`**: Contiene la lógica pura del negocio (CLIP, Pinecone, descargas, caché). No debe manejar respuestas HTTP directamente.
4. **`app/api/endpoints.py`**: Maneja las rutas HTTP, inyecta sesiones de base de datos (`db: Session`) y delega la ejecución de lógica a los servicios.

---

## 4. Auditoría de Calidad del Proyecto

| Elemento de Control | Estado | Detalle |
| :--- | :---: | :--- |
| **Protección de Secretos** | **APROBADO** | Sin llaves hardcodeadas. Configurado en `.env` protegido por `.gitignore`. |
| **Integridad Git** | **APROBADO** | commits limpios bajo el seudónimo `juankgarcia700` y correo de no-reply de GitHub. |
| **Base de Datos SQLite** | **APROBADO** | Archivos de base de datos física excluidos (`*.db`) de Git. |
| **Cobertura de Pruebas** | **APROBADO** | 20/20 pruebas exitosas verificando ingesta, caché, base de datos, filtros e hibridación. |
| **Latencia de API** | **APROBADO** | Latencia de búsqueda < 50ms gracias al caché LRU y tareas en segundo plano. |
| **Seguridad de Datos** | **APROBADO** | Entrada de datos sanitizada con Pydantic v2 y control estricto de tipos de entrada. |
