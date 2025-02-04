# Generación Automática de Reportes a partir de Consultas en Lenguaje Natural sobre Bases de Conocimiento.

## Descripción del Proyecto

Este repositorio contiene el código fuente desarrollado como parte de la tesis de diploma titulada "Generación Automática de Reportes a partir de Consultas en Lenguaje Natural sobre Bases de Conocimiento". El proyecto implementa una aplicación web interactiva, construida con Streamlit, que permite a los usuarios generar reportes automatizados a partir de documentos cargados y consultas en lenguaje natural.

La aplicación utiliza Modelos de Lenguaje Grandes (LLMs) a través de la API de Groq para interpretar las consultas de los usuarios, extraer información relevante de los documentos (CSV, Excel, JSON, TXT), preprocesar los datos, generar el esqueleto del reporte, generar código Python para obtener y procesar datos, crear visualizaciones con Altair, y finalmente, componer secciones de reporte coherentes y detalladas.

## Características Principales

*   **Soporte para múltiples formatos de documentos:**  Carga de archivos CSV, Excel (.xlsx), JSON y TXT.
*   **Preprocesamiento inteligente de documentos:** Utilización de LLMs para sugerir y ejecutar tareas de preprocesamiento de datos, incluyendo conversión de fechas, identificación de columnas categóricas, filtrado y más.
*   **Generación de reportes automatizada:**  Respuesta a consultas en lenguaje natural con reportes estructurados en secciones, utilizando la técnica "Skeleton-of-Thought" para mejorar la coherencia y organización.
*   **Visualizaciones de datos interactivas:**  Inclusión de gráficos y tablas generados con Altair en los reportes para una mejor comprensión de los datos.
*   **Selección de modelos LLM de Groq:**  Soporte para varios modelos de lenguaje de Groq, permitiendo experimentar con diferentes capacidades y rendimientos.
*   **Ajuste de tokens máximos:**  Control sobre el número máximo de tokens generados por el modelo LLM para optimizar el uso de recursos y la longitud de las respuestas.
*   **Modo Debug:**  Opción para activar un modo de depuración que muestra información detallada sobre el proceso, incluyendo las solicitudes y respuestas de la API de Groq, el código Python generado y ejecutado, y los DataFrames intermedios.

## Empezando

Sigue estos pasos para ejecutar la aplicación localmente:

### Prerrequisitos

*   **Python 3.8 o superior** instalado en tu sistema.
*   **pip** instalado (normalmente incluido con Python).
*   **Clave de API de Groq:** Necesitarás una clave de API de Groq para utilizar los modelos LLM. Puedes obtener una en [https://console.groq.com/](https://console.groq.com/).  Asegúrate de configurar la variable de entorno `GROQ_API_KEY` con tu clave API.

### Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/DavidCabrera9943/automate_report_generation.git
    cd automate_report_generation
    ```

2.  **Crea un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Linux/macOS
    venv\Scripts\activate  # En Windows
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

### Ejecución de la Aplicación

1.  **Asegúrate de tener configurada tu clave API de Groq como variable de entorno `GROQ_API_KEY`.**

2.  **Ejecuta la aplicación Streamlit:**
    ```bash
    streamlit run main.py
    ```

3.  **Abre la aplicación en tu navegador:**  Streamlit debería abrir automáticamente la aplicación en tu navegador web. Si no, puedes acceder a ella manualmente a través de la URL que se muestra en la terminal (normalmente `http://localhost:8501`).

## Uso

1.  **Carga tu documento:**  Utiliza el cargador de archivos en la barra lateral para subir tu documento en formato CSV, Excel, JSON o TXT.
2.  **Espera el procesamiento:** La aplicación procesará el documento, extraerá información relevante y realizará un preprocesamiento inicial. Verás mensajes de éxito o error en la interfaz.
3.  **Escribe tu consulta:**  En el área de texto principal, introduce tu consulta en lenguaje natural sobre los datos de tu documento. Por ejemplo: "¿Cuáles son las ventas totales por categoría de producto en 2023?".
4.  **Genera el reporte:** Haz clic en el botón "Generar Reporte". La aplicación utilizará el modelo LLM seleccionado para generar un reporte basado en tu consulta y los datos del documento.
5.  **Revisa el reporte:** El reporte se mostrará en la columna principal, incluyendo texto, datos y visualizaciones.
6.  **Modo Debug (opcional):**  Activa la casilla de verificación "Debug" en la barra lateral para habilitar el modo de depuración. Esto mostrará información adicional en una columna lateral derecha, útil para entender el proceso y depurar posibles problemas.
7.  **Selección de Modelo y Tokens:**  Utiliza los selectores y sliders en la barra lateral para elegir el modelo de Groq a utilizar y ajustar el número máximo de tokens para las respuestas del modelo.

## Tecnologías Utilizadas

*   **Python:** Lenguaje de programación principal.
*   **Streamlit:** Framework para crear aplicaciones web interactivas de ciencia de datos.
*   **Groq API:** API para acceder a modelos de lenguaje grandes de alto rendimiento.
*   **Pandas:** Librería para manipulación y análisis de datos.
*   **Altair:** Librería para visualización de datos en Python, basada en Vega-Lite.

## Información de la Tesis

Este proyecto fue desarrollado como parte de la tesis de diploma:

*   **Título:** Generación Automática de Reportes a partir de Consultas en Lenguaje Natural sobre Bases de Conocimiento.
*   **Autor:** David Cabrera García
*   **Tutores:** DrC. Alejandro Piad Morffis
*   **Universidad:** Universidad de La Habana, Facultad de Matemática y Computación
*   **Fecha:** 4 de febrero de 2025

## Licencia

Este proyecto está bajo la licencia [MIT License](LICENSE).

## Contacto

David Cabrera García - [https://github.com/DavidCabrera9943](https://github.com/DavidCabrera9943)

---
