import streamlit as st
from groq import Groq,APIError
import pandas as pd
import altair as alt
import os
import io
from streamlit.runtime.uploaded_file_manager import UploadedFile
import json
import time

# Configuración inicial
client = Groq()

# Groq Models
groq_models = {
    "llama-3.3-70b-versatile":{
        "name": "LLaMA-3.3-70b-Versatile",
        "tokens": 32768,
        "developer": "Meta",
    },
    "llama3-70b-8192": {
        "name": "LLaMA3-70b-Instruct",
        "tokens": 8192,
        "developer": "Meta",
    },
    "llama3-8b-8192": {
        "name": "LLaMA3-8b-Instruct",
        "tokens": 8192,
        "developer": "Meta",
    },
    "mixtral-8x7b-32768": {
        "name": "Mixtral-8x7b-Instruct-v0.1",
        "tokens": 32768,
        "developer": "Mistral",
    },
    "gemma2-9b-it": {"name": "Gemma2-9b-it", "tokens": 8192, "developer": "Google"},
}

col1, col2 = st.sidebar.columns(2)

with col1:
    groq_model_option = st.selectbox(
        "Choose a Groq model:",
        options=list(groq_models.keys()),
        format_func=lambda x: groq_models[x]["name"],
        index=0,
    )
max_tokens_range = groq_models[groq_model_option]["tokens"]
with col2:
        max_tokens = st.slider(
            "Max Tokens:",
            min_value=512,
            max_value=max_tokens_range,
            value=min(32768, max_tokens_range),
            step=512,
            help=f"Adjust the maximum number of tokens for the model's response. Max for selected model: {max_tokens_range}",
        )
if "selected_groq_model" not in st.session_state or st.session_state.selected_groq_model != groq_model_option:
      st.session_state.selected_groq_model = groq_model_option

if "dataframe" not in st.session_state:
    st.session_state.dataframe = None

debug = st.sidebar.checkbox("Debug", value=False)

if debug:
    main_col, debug_col = st.columns([3, 1]) # Adjust ratios as needed. Main content wider than debug
else:
    main_col, debug_col = st.columns([3, 1]) # If not debug mode, main_col is just st to write to the main area.
    #debug_col = None # debug_col is None when debug is off

def get_document_info(document:UploadedFile):
    """Obtiene información relevante del documento cargado."""
    if document.type == "text/csv":
        st.session_state.dataframe = pd.read_csv(document)
    elif document.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        st.session_state.dataframe = pd.read_excel(document._file_urls.upload_url)
    elif document.type == "application/json":
        st.session_state.dataframe = pd.read_json(document._file_urls.upload_url)
    else:
        return {"error": "Tipo de documento no soportado"}

    # Extraer información relevante
    info = {
        "column_names": st.session_state.dataframe.columns.tolist(),
        "max_values": st.session_state.dataframe.max(numeric_only=True).to_dict(),
        "min_values": st.session_state.dataframe.min(numeric_only=True).to_dict(),
        "unique_values": {col: st.session_state.dataframe[col].nunique() for col in st.session_state.dataframe.columns},
        "missing_values": st.session_state.dataframe.isnull().sum().to_dict(),
        "firsts_rows": st.session_state.dataframe.head().to_dict(),
    }

    if debug:
        with debug_col: # Output to debug column
            with st.expander("Document Info"):
                st.write(info)

    return info

def preprocess_document():
    """Preprocesa el documento para facilitar consultas futuras."""

    if st.session_state.dataframe is None:
        return {"error": "No hay un dataframe cargado para preprocesar"}

    # 1. Obtener tareas de preprocesamiento del LLM
    preprocess_tasks_messages = [
        {"role": "system", "content": """
        Analiza la información del dataframe y define las tareas de preprocesamiento necesarias.
        Considera:
        - Conversión de fechas a datetime.
        - Identificación de columnas categóricas.
        - Sugerencias para filtrar columnas no numéricas no categóricas.

        ```json
        [
            {"tarea": "convertir_fecha", "columna": "nombre_columna"},
            {"tarea": "identificar_categorica", "columna": "nombre_columna"},
            {"tarea": "filtrar", "columna": "nombre_columna", "sugerencia": "sugerencia filtro para la columna, puede ser simplemene eliminar la columna, eliminar filas con datos faltantes o filtrar valores outliers"}
            {"tarea": "pandas","codigo":"codigo pandas para realizar el procesado del dataframe almacenado en df, este se ejecuta para realizar una tarea mas compleja, que no sea convertir_fecha,identificar_categorica,o filtrar"}
        ]
        ```
        Ademas sugiere 3 posibles consultas que un usuario que esta analizando el dataframe pueda hacerse del mismo

        --IMPORTANT--
        ANSWER FORMAT
            <Analisis de que datos tienes y que se deberia hacer>
            ```json
                <json array con las tareas>
            ```
            A continuacion se muestran 3 sugerencias de consultas
            ```sugerencia
            <Sugerencia de una consulta que pueda realizar el usuario sobre los datos del dataframe>
            ```
            ```sugerencia
            <Sugerencia 2 de una consulta>
            ```
            ```sugerencia
            <Sugerencia 3>
            ```

        """},
        {"role": "user", "content": f"""
            Información del DataFrame:
            Columnas: {st.session_state.dataframe.columns.tolist()}
            Tipos: {st.session_state.dataframe.dtypes.to_dict()}
            Primeras filas: {st.session_state.dataframe.head().to_dict()}

            
        """}
    ]

    tasks_json = query_llm(preprocess_tasks_messages)
    print(tasks_json)
    tasks_json = tasks_json.split("```json")[1].split('```')[0]
    if debug:
        with debug_col:
            st.write("Tasks JSON Response:")
            st.code(tasks_json, language='json') # Show json in debug column
    try:
        preprocess_tasks = json.loads(tasks_json)
    except json.JSONDecodeError as e:
        if debug:
            with debug_col:
                st.error(f"Error al parsear la respuesta del LLM: {e}")
        return {"error": f"Error al parsear la respuesta del LLM: {e}"}


    if debug:
        with debug_col: # Output to debug column
            with st.expander("Tareas de Preprocesado"):
                st.write(preprocess_tasks)

    # 2. Ejecutar cada tarea
    for task in preprocess_tasks:
        if debug:
            with debug_col:
                st.write(f"Executing task: {task}")
        task_name = task.get("tarea","pandas")
        column_name = task.get("columna","")


        if task_name == "convertir_fecha":
            preprocess_code = f"""import pandas as pd\ndf['{column_name}'] = pd.to_datetime(df['{column_name}'], errors='coerce')\ndf = df.dropna(subset=['{column_name}'])
            """
        elif task_name == "identificar_categorica":
            preprocess_code = f"""categorias = df['{column_name}'].unique().tolist()\ndf['{column_name}'] = df['{column_name}'].astype('category')\n# Aquí se podría añadir código para manejar las categorías (e.g., convertir a tipo 'category')
             
            """
        elif task_name == "filtrar_no_numerica":
            suggestion = task.get("sugerencia")
            preprocess_code = f"""# Sugerencia para filtrar '{column_name}': {suggestion}\n# Implementa la lógica de filtrado según la sugerencia
            """  # El usuario deberá implementar la lógica
        elif task_name == "pandas":
            preprocess_code = task.get("codigo")
        else:
            if debug:
                with debug_col:
                    st.write( {"error": f"Tarea de preprocesamiento desconocida: {task_name}"})
            print( {"error": f"Tarea de preprocesamiento desconocida: {task_name}"})
            continue # Skip to next task if unknown

        if debug:
            with debug_col:
                st.write("Executing code:")
                st.code(preprocess_code, language='python')


        try:
            if debug:
                with debug_col:
                    st.write("DataFrame before execution:")
                    st.dataframe(st.session_state.dataframe.head())

            # local_vars = {'df': st.session_state.dataframe}
            execute_code(preprocess_code)
            # st.session_state.dataframe = local_vars['df'] # Update dataframe in session state

            if debug:
                with debug_col:
                    st.write("DataFrame after execution:")
                    st.dataframe(st.session_state.dataframe.head())
                    st.success(f"Executed task '{task_name}' on column '{column_name}'")

        except Exception as e:
            error_msg = f"Error al ejecutar la tarea '{task_name}' en la columna '{column_name}': {e}"
            if debug:
                with debug_col:
                    st.error(error_msg)
            print(error_msg)
            return {"error": error_msg}


    return {"success": "Preprocesamiento completado"}

def query_llm(messages, model=st.session_state.selected_groq_model, temperature=0.5, max_tokens=1024):
    """Realiza una consulta al modelo LLM usando la API de Groq, con reintentos."""
    max_retries = 5
    retry_delay_seconds = 60  # 1 minuto

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            if debug: # Asumiendo que 'debug' está definido en tu contexto
                with debug_col: # Asumiendo que 'debug_col' está definido en tu contexto
                    with st.expander(f"LLM Request/Response - Attempt {attempt+1} (Success)"):
                        st.write("**Request Messages:**")
                        st.json(messages)
                        st.write("**Response Content:**")
                        st.write(response.choices[0].message.content)
            return response.choices[0].message.content  # Retorna el contenido si la llamada es exitosa

        except APIError as e:
            if attempt < max_retries - 1: # Intenta de nuevo si no es el último intento
                st.warning(f'Error en llamada a la API de Groq (Intento {attempt+1}/{max_retries}): {e}. Reintentando en {retry_delay_seconds} segundos...')
                time.sleep(retry_delay_seconds)
            else: # Si es el último intento y falla, muestra el error final
                st.error(f'Error en llamada a la API de Groq después de {max_retries} intentos: {e}')
                return None

        except Exception as e: # Captura otros errores inesperados
            st.error(f"Error Inesperado en llamada a la API de Groq (Intento {attempt+1}/{max_retries}): {e}")
            return None

    return None

def execute_code(code, retry_count=0, max_retries=1):
    """Ejecuta código Python de manera segura."""
    try:
        if debug:
            with debug_col:
                st.write("Executing code block:")
                st.code(code, language='python')

        local_vars = {'df': st.session_state.dataframe, 'alt':alt, 'pd':pd, 'st':st} # Include alt and pd in local vars
        exec(code, {}, local_vars)
        return local_vars.pop('response', None)

    except Exception as e:
        if retry_count < max_retries:
            error_message = str(e)
            corrected_code = debug_and_regenerate_code(code, error_message) # Function to regenerate code
            if corrected_code:
                return execute_code(corrected_code, retry_count=retry_count + 1, max_retries=max_retries) # Retry
        error_msg = {"error": str(e)}
        if debug:
            with debug_col:
                st.error(f"Code execution error: {e}")
        return error_msg

def debug_and_regenerate_code(original_code, error_message):
    debug_messages = [
        {"role": "system", "content": "You generated Python code that produced an error. Please debug and regenerate the corrected code. There are a df variable with the dataframe already defined, and libraries pandas as pd and altair as alt are available"},
        {"role": "user", "content": f"Original code:\n```python\n{original_code}\n```\nError message: {error_message}\nCorrected code:"}
    ]
    if debug:
        with debug_col:
            st.write("Debugging code, sending messages to LLM:")
            st.json(debug_messages)
    corrected_code_response = query_llm(debug_messages)
    if corrected_code_response:
        if '```python' in corrected_code_response and '```' in corrected_code_response.split('```python')[1]:
            corrected_code = corrected_code_response.split('```python')[1].split('```')[0]
            if debug:
                with debug_col:
                    st.write("Corrected code from LLM:")
                    st.code(corrected_code, language='python')
            return corrected_code
        else:
            if debug:
                with debug_col:
                    st.warning("LLM provided a response but no code block was found.")
            return None # Could not extract code, or LLM failed to correct
    else:
        if debug:
            with debug_col:
                st.error("LLM failed to provide a corrected code response.")
        return None # LLM failed to correct

# Interfaz gráfica
with main_col: # Place main content in main_col
    st.title("Generador de Reportes Automatizados con LLM")

    # Paso 1: Subir documento
    document_file = st.file_uploader("Sube tu documento", type=["txt", "csv", "xlsx", "json"])


    if document_file:
        if st.session_state.get('document_file') != document_file: # Check if a new file is uploaded
            st.session_state.dataframe = None # Clear old dataframe
            st.session_state.document_info = None # Clear old document info
            st.session_state.document_file = document_file # Update the stored file object

        if st.session_state.dataframe is None: # Only process if no dataframe in state
            with st.spinner("Obteniendo información del documento..."):
                st.session_state.document_info = get_document_info(document_file) # Store in session state
                st.success("Documento cargado con éxito.")

            with st.spinner("Preprocesando el documento..."):
                if preprocess_document().get("error",None):
                    st.error("Error al preprocesar el documento")
                else:
                    st.success("Preprocesamiento completado.")

        # Paso 2: Recibir query del usuario
        user_query = st.text_area("Escribe tu consulta:")

        if st.button("Generar Reporte") and user_query:
            with st.spinner("Generando reporte..."):
                # Armar el esqueleto del reporte
                skeleton_messages = [
                    {"role": "system", "content": f"""Dada la siguiente consulta del usuario sobre el documento cargado, genera un esqueleto detallado para un reporte que pueda responder a la consulta de forma exhaustiva. El esqueleto debe estructurar la información de manera lógica y facilitar la creación de un reporte final completo.

                     DOCUMENT INFORMATION
                     {st.session_state.document_info}

                     ANSWER FORMAT:
                     [Un analisis del tema y de lo que quiere el usuario, de que datos quiere conocer, y que datos extras podrian proporcionarsele para una respuesta mas completa]
                     [Analisis de la consulta, Identificar los puntos clave de la consulta (qué información busca el usuario explícitamente), Identificar posibles ambigüedades o interpretaciones de la consulta, Definir las métricas o datos específicos necesarios para responder a la consulta]
                     <Esturctura del Reporte>
                     ```json
                     [
                        'section': {{
                            'name':[Nombre de la seccion del reporte]
                            'description':[Breve descripcion de la seccion del reporte]
                            'data':[brevemente el tipo de información que se va a incluir (ej: "Datos de ventas del producto A", "Gráfico comparativo", "Conclusiones") Indicar si se requieren visualizaciones (gráficos, tablas), y en caso afirmativo, sugerir tipos apropiados (ej: "Gráfico de barras para comparar ventas", "Tabla con datos numéricos detallados")]
                            'extra_data':[Sugerir información adicional o contextual que pueda enriquecer la respuesta y aportar mayor valor al usuario (datos relevantes que no se solicitaron explícitamente pero podrían ser útiles)]
                        }},
                        {{"section": {{
                            "name": "[Nombre de la siguiente sección]",
                            "description": "[Descripción de la siguiente sección]",
                            "data": "[Tipo de información y visualización]",
                            "extra_data":"[información adicional para esta sección]"
                        }}
                        }},...
                    ]
                    ```

                     EXAMPLE
                     User Input: Comparar las ventas del producto A y B en el último trimestre.

                     ANSWER:

                        ```json
                            [
                                {{
                                    "section": {{
                                        "name": "Introducción",
                                        "description": "Breve contexto del reporte de ventas y mención de la comparación solicitada de los productos A y B. Objetivo del reporte: analizar y comparar el rendimiento de ventas de ambos productos.",
                                        "data": "Contexto general del análisis de ventas",
                                        "extra_data": "Mencionar la relevancia de comparar estos productos para la estrategia de la empresa"
                                    }}
                                }},
                                {{
                                    "section": {{
                                        "name": "Datos de Ventas del Producto A (último trimestre)",
                                        "description": "Presentación detallada de las ventas del Producto A en el último trimestre",
                                        "data": "Datos numéricos de ventas. Sugerencia: Tabla detallada",
                                        "extra_data": "Comparación de ventas de A con trimestres anteriores."
                                    }}
                                }},
                                {{
                                    "section": {{
                                        "name": "Datos de Ventas del Producto B (último trimestre)",
                                        "description": "Presentación detallada de las ventas del Producto B en el último trimestre",
                                        "data": "Datos numéricos de ventas. Sugerencia: Tabla detallada",
                                        "extra_data": "Comparación de ventas de B con trimestres anteriores."
                                    }}
                                }},
                            {{
                                "section": {{
                                        "name": "Gráfico Comparativo de Ventas (A vs B)",
                                        "description": "Comparación visual de las ventas de A y B",
                                        "data": "Gráfico de barras para comparar ventas. Sugerencia: Gráfico de barras",
                                        "extra_data":"Comparación de porcentajes de crecimientos"
                                    }}
                                }},
                                {{
                                "section": {{
                                        "name": "Tabla Comparativa de Ventas (A vs B)",
                                        "description": "Tabla con datos comparativos detallados de A y B",
                                        "data": "Tabla con datos numéricos y porcentajes. Sugerencia: Tabla detallada",
                                        "extra_data": "Datos de ventas por región"
                                    }}
                                }},
                                {{
                                    "section": {{
                                        "name": "Conclusiones y Análisis",
                                        "description": "Análisis de los resultados y conclusiones del reporte",
                                        "data": "Resumen de los hallazgos y conclusiones.",
                                        "extra_data": "Mencionar limitaciones o posibles investigaciones futuras."
                                    }}
                                }}
                            ]
                        ```

                     """},
                    {"role": "user", "content": user_query}
                ]
                skeleton_response = query_llm(skeleton_messages).split('```json')[1].split('```')[0]
                if debug:
                    with debug_col:
                        st.write("**Creado esqueleto del reporte**")
                        with st.expander("Ver esqueleto del reporte"):
                            for section in json.loads(skeleton_response):
                                section_name = section["section"]["name"]
                                section_description = section["section"]["description"]
                                section_data = section["section"]["data"]
                                section_extra_data = section["section"]["extra_data"]
                                st.write(f"**Sección {section_name}**")
                                st.write(f"**Descripción:** {section_description}")
                                st.write(f"**Información:** {section_data}")
                # Paso 3: Generar cada seccion del reporte
                for section in json.loads(skeleton_response):
                    section_name = section["section"]["name"]
                    section_description = section["section"]["description"]
                    section_data = section["section"]["data"]
                    section_extra_data = section["section"]["extra_data"]
                    section_messages = [
                        {"role": "system", "content": f"""Teniendo en cuenta los datos del documento siguiente se te ha pedido que generes una seccion de un reporte.
                        Tu trabajo es solo generar la parte textual de la seccion, para ello necesitas informacion extra, a la cual puedes acceder usando codigo python
                         sobre el siguiente documento, el cual se encuentra en un dataframe de pandas llamado "df".
                        DOCUMENT INFORMATION
                        {st.session_state.document_info}

                        ANSWER GUIDE
                        Los datos que desees recibir al final se deben encontrar en una variable local llamada "response" con una estrucutra de datos adecuada como por ejemplo json.
                        Si deseas recibir varios datos como por ejemplo valor maximo y minimo de una columna de un dataframe, debes incluirlos todos en la variable "response".
                        Ten en cuenta de que solo la informacion que necesitas es solo para la parte textual de la seccion del reporte por lo que si quieres ver por ejemplo como se comportaron
                        las ventas de un año en cuestion, no debes incluir toda la informacion de la base de dato con respecto a las ventas de ese año ya que para el reporte escrito
                        son demasiados datos, solo debes incluir en la respuesta la informacion importante que puedas sacar con codigo python de estas como maximos minimos media, outlier,
                        patrones etc.
                        Solo debes proporcionar un codigo python con todas las instrucciones necesarias para obtener la toda la informacion requerida de una.
                        NO PUEDES MODIFICAR EL DATAFRAME ORIGINAL ALMACENADO EN "df".

                        En caso de que no necesites informacion del dataframe

                        ANSWER FORMAT:
                        <Analisis de que datos necesitas conocer para la seccion>
                        ```python
                            <CODIGO PYTHON>
                        ```
                         """
                        },
                        {
                            "role": "user", "content": f"""
                            Sección: {section_name}
                            Descripción: {section_description}
                            Información: {section_data}
                            Extra Data: {section_extra_data}
                        """}
                    ]

                    section_response = query_llm(section_messages).split('```python')[1].split('```')[0]

                    response = execute_code(section_response)
                    if debug:
                        with debug_col: # Output to debug column
                            st.write(f"**Sección {section_name} - Data Response from Code Execution**")
                    
                    if response:
                        st.write(f"**Sección {section_name}**")
                    
                    else:
                        st.write("No data response generated.")
                        response = ""
                    #Luego de que obtuvimos los datos, generamos la seccion del reporte correspondiente
                    #Pasandole esos datos al modelo y dandole la posibilidad de gnerar codigo altair para mostrar
                    #los datos mas generales a partir del dataframe de pandas
                    generate_chart_messages = [
                        {"role": "system", "content": f"""Teniendo en cuenta los datos del documento siguiente se te ha pedido que generes una o varias graficas o tablas sobre el siguiente documento, el cual se encuentra en un dataframe de pandas llamado "df".
                        DOCUMENT INFORMATION
                        {st.session_state.document_info}

                        ANSWER GUIDE
                        Las graficas o tablas que generes debes ser en codigo altair, libreria que ya esta importada como 'import altair as alt'.
                        Las graficas o tablas que desees recibir al final se deben encontrar en una variable local llamada "response" el cual debe ser una lista de graficas o tablas altair.
                        cada elemento de la lista debe ser un diccionario con la siguiente estructura:
                        {{
                            'name':<nombre_del_grafico>,
                            'description':<breve descripcion de que datos muestra este grafico>,
                            'c':<objeto altair>
                        }}

                        Ten en cuenta de que solo necesitas las graficas especificas para la seccion actual del reporte, las graficas mas generales son para las secciones de conclusiones o alguna que la requiera especificamente.

                        Solo debes proporcionar un codigo python con todas las instrucciones necesarias para obtener todas las graficas requerida de una.
                        NO PUEDES MODIFICAR EL DATAFRAME ORIGINAL ALMACENADO EN "df".

                        En caso de que la seccion no requiera graficas haz que el codigo python devuelva uen response sea una lista vacia

                        ANSWER FORMAT:
                        <Analisis de que graficos o tablas serian ilustrativos en esta seccion>
                        ```python
                            <CODIGO PYTHON>
                        ```
                         """
                        },
                        {
                            "role": "user", "content": f"""
                            Sección: {section_name}
                            Descripción: {section_description}
                            Información: {section_data}
                            Extra Data: {section_extra_data}
                        """}
                    ]

                    charts_response = query_llm(generate_chart_messages).split('```python')[1].split('```')[0]

                    chart_response = execute_code(charts_response)
                    if debug:
                        with debug_col: # Output to debug column
                            st.write(f"**Sección {section_name} - Chart Code Execution Response**")
                            if chart_response and type(chart_response) == list:
                                st.write(chart_response)
                                for c in chart_response:
                                    st.altair_chart(c['c'],use_container_width = True)
                            else:
                                st.write("No Chart Generated")
                    if chart_response and type(chart_response) == list:
                        charts_names = [{'name':item['name'],'description':item['description']} for item in chart_response if chart_response] #Handle case when chart_response is None
                    else:
                        charts_names = "Para esta seccion no cuentas con graficos para mostrar"
                    generate_section_messages = [
                        {"role": "system", "content": f"""Teniendo en cuenta los datos del documento siguiente se te ha pedido que generes una seccion de un reporte.

                        DOCUMENT INFORMATION
                        {st.session_state.document_info}

                        ANSWER GUIDE
                        Para generar el reporte lo mas certero posible se te brindan los siguientes datos:

                        {response}

                        Genera la seccion del reporte con la informacion proporcionada, utiliza esos datos para cumplir con las espectativas del reporte en la seccion actual.

                        Para complementar tu respuesta tienes a tu dispocision los siguientes graficos o tablas
                        {charts_names}

                        Los cuales puedes incluir en tu reporte donde los cosideres oportuno usando la siguiente sintaxis
                        ```chart
                            <chart_name>
                        ```
                        No es necesario mostrar algun o todos los graficos si estos no son relevates para la seccion actual.

                        ANSWER FORMAT:
                        <Texto del reporte>
                        ```chart
                            <nombre del grafico a insertar>
                        ```
                        <Pude seguir el texto del reporte, incluir otro grafico a continuacion o intercalarlos en dependencia de lo que requiera esta seccion del reporte>

                         """
                        },
                        {
                            "role": "user", "content": f"""
                            Sección: {section_name}
                            Descripción: {section_description}
                            Información: {section_data}
                            Extra Data: {section_extra_data}
                        """}
                    ]

                    final_response = query_llm(generate_section_messages)

                    parts = final_response.split("```chart") # Dividimos el string usando ```chart como delimitador


                    st.write(f"**Sección {section_name}**")
                    for i, part in enumerate(parts):
                        if i == 0: # La primera parte siempre es texto antes del primer chart (o todo el texto si no hay charts)
                            if part.strip(): # Verificamos que no este vacio despues de quitar espacios en blanco
                                st.write(part.strip())
                        else: # Las partes siguientes vienen despues de un ```chart
                            chart_block_parts = part.split("```") # Dividimos la parte en subpartes usando ``` como delimitador

                            if len(chart_block_parts) >= 2: # Debe haber al menos 2 partes si hay un bloque chart
                                chart_name = chart_block_parts[0].strip() # El nombre del chart esta antes del primer ``` de cierre
                                if chart_name: # Verificamos que el nombre del chart no este vacio
                                    c = None
                                    if chart_response and type(chart_response) == list:
                                        for item in chart_response:
                                            if item['name']==chart_name:
                                                c = item['c']
                                                break
                                    if c:
                                        st.altair_chart(c) # Mostramos el chart usando el nombre

                                text_after_chart = chart_block_parts[1] if len(chart_block_parts) > 1 else "" # El texto despues del chart, si existe
                                if text_after_chart.strip(): # Verificamos que haya texto despues del chart
                                    st.write(text_after_chart.strip())
