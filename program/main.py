import streamlit as st
from groq import Groq
import pandas as pd
import altair as alt
import os
import io
from streamlit.runtime.uploaded_file_manager import UploadedFile
import json

# Configuración inicial
client = Groq()
# MODEL_NAME = "llama-3.3-70b-versatile"
MODEL_NAME = "mixtral-8x7b-32768"
df = None
def get_document_info(document:UploadedFile):
    global df
    """Obtiene información relevante del documento cargado."""
    if document.type == "text/csv":
        df = pd.read_csv(document)
    elif document.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(document._file_urls.upload_url)
    elif document.type == "application/json":
        df = pd.read_json(document._file_urls.upload_url)
    else:
        return {"error": "Tipo de documento no soportado"}

    # Extraer información relevante
    info = {
        "column_names": df.columns.tolist(),
        "max_values": df.max(numeric_only=True).to_dict(),
        "min_values": df.min(numeric_only=True).to_dict(),
        "unique_values": {col: df[col].nunique() for col in df.columns},
        "missing_values": df.isnull().sum().to_dict(),
    }

    return info

def preprocess_document():
    """Preprocesa el documento para facilitar consultas futuras."""
    global df
    if df is None:
        return {"error": "No hay un dataframe cargado para preprocesar"}

    # 1. Obtener tareas de preprocesamiento del LLM
    preprocess_tasks_messages = [
        {"role": "system", "content": """
        Analiza la información del dataframe y define las tareas de preprocesamiento necesarias. 
        Considera:
        - Conversión de fechas a datetime.
        - Identificación de columnas categóricas.
        - Sugerencias para filtrar columnas no numéricas no categóricas.

        Responde con una lista de diccionarios, donde cada diccionario representa una tarea:
        ```json
        [
            {"tarea": "convertir_fecha", "columna": "nombre_columna", "formato": "formato_fecha"},
            {"tarea": "identificar_categorica", "columna": "nombre_columna"},
            {"tarea": "filtrar_no_numerica", "columna": "nombre_columna", "sugerencia": "sugerencia_filtro"}
        ]
        ```
        """},
        {"role": "user", "content": f"""
            Información del DataFrame:
            Columnas: {df.columns.tolist()}
            Tipos: {df.dtypes.to_dict()}
            Primeras filas: {df.head().to_dict()}
        """}
    ]

    tasks_json = query_llm(preprocess_tasks_messages)
    try:
        preprocess_tasks = json.loads(tasks_json)
    except json.JSONDecodeError as e:
        return {"error": f"Error al parsear la respuesta del LLM: {e}"}


    # 2. Ejecutar cada tarea
    for task in preprocess_tasks:
        task_name = task.get("tarea")
        column_name = task.get("columna")

        if not column_name or column_name not in df.columns:
            return {"error": f"Nombre de columna inválido: {column_name}"}

        if task_name == "convertir_fecha":
            date_format = task.get("formato")
            preprocess_code = f"""
            df['{column_name}'] = pd.to_datetime(df['{column_name}'], format='{date_format}')
            """
        elif task_name == "identificar_categorica":
            preprocess_code = f"""
            categorias = df['{column_name}'].unique().tolist()
            # Aquí se podría añadir código para manejar las categorías (e.g., convertir a tipo 'category')
            print(f"Categorías de '{column_name}': {{categorias}}") 
            """
        elif task_name == "filtrar_no_numerica":
            suggestion = task.get("sugerencia")
            preprocess_code = f"""
            # Sugerencia para filtrar '{column_name}': {suggestion}
            # Implementa la lógica de filtrado según la sugerencia
            """  # El usuario deberá implementar la lógica
        else:
            return {"error": f"Tarea de preprocesamiento desconocida: {task_name}"}
        print("^^^^^^^^^^^^^^^^^")
        print(preprocess_code)
        print("^^^^^^^^^^^^^^^^^")
        return
        try:
            exec(preprocess_code, globals())
        except Exception as e:
            return {"error": f"Error al ejecutar la tarea '{task_name}' en la columna '{column_name}': {e}"}

    return {"success": "Preprocesamiento completado"}

def query_llm(messages, model=MODEL_NAME, temperature=0.5, max_tokens=1024):
    # print(messages)
    # a = input("Should make this request:[Y/N]")
    # if a =="N":
    #     return "```python print('Perico')```"
    """Realiza una consulta al modelo LLM usando la API de Groq."""
    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def execute_code(code,previous):
    """Ejecuta código Python de manera segura."""
    try:
        print(code)
        local_vars = {'df': df,**previous}
        exec(code, {}, local_vars)
        local_vars.pop('df', None)  # Eliminar el key 'df' antes de devolverlo
        return local_vars
    except Exception as e:
        return {"error": str(e)}


print("A")
# Interfaz gráfica
st.title("Generador de Reportes Automatizados con LLM")

# Paso 1: Subir documento
document_file = st.file_uploader("Sube tu documento", type=["txt", "csv", "xlsx", "json"])

if document_file:
    with st.spinner("Obteniendo información del documento..."):
        print(document_file)
        #document = document_file.read()
        document_info = get_document_info(document_file)
        st.success("Documento procesado con éxito.")

    with st.spinner("Preprocesando el documento..."):
        preprocess_document()
        st.success("Preprocesamiento completado.")
        
    # Paso 2: Recibir query del usuario
    user_query = st.text_area("Escribe tu consulta:")

    if st.button("Generar Reporte") and user_query:
        with st.spinner("Generando reporte..."):
            # Skeleton of Thought: dividir la consulta en tareas atómicas
            skeleton_messages = [
                {"role": "system", "content": f"""Dada la siguiente consulta del usuario sobre el documento cargado, identifica las tareas atómicas necesarias para responderla.
                 la informacion del documento esta contenida en un dataframe de pandas con la siguiente informacion relevante:
                 {document_info}
                 ANSWER FORMAT:
                 [Un breve analisis del tema y de lo que quiere el usuario]
                 ```action
                    <Accion a realizar en lenguaje natural>
                 ```
                 ```action
                    <Otra accion que siga a la anterior>
                 ```

                 EXAMPLE
                 User Input: Como se comprtaron las ventas de Ron de Diciembre con respecto a las de Noviembre

                 ANSWER:
                    El usuario quiere comparar las ventas de Ron en Diciembre con las de Noviembre. Para ello, necesitamos:
                    ```action
                        Filtrar el dataframe para obtener las ventas de Ron en Diciembre
                    ```
                    ```action
                        Filtrar el dataframe para obtener las ventas de Ron en Noviembre
                    ```
                    ```action
                        Comparar las ventas obtenidas
                    ```

                 """},
                {"role": "user", "content": user_query}
            ]
            skeleton_response = query_llm(skeleton_messages)
            st.write("**Tareas atómicas identificadas:**", skeleton_response)

            # Generar código Python para cada tarea atómica
            atomic_tasks = [action.split("```")[0] for action in skeleton_response.split("```action")[1:]]
            final_results = {}

            for task in atomic_tasks:
                with st.expander(f"Tarea: {task}"):
                    task_messages = [
                        {"role": "system", "content": f"""Genera código Python para resolver la siguiente tarea. teniendo en cuenta que las cosultas se realizaran a un dataframe de pandas
                        llamado df del cual se extrajo la siguiente informacion relevante:
                        {document_info}
                        
                        Hasta Ahora tenomos calculadas las siguientes variables
                        {final_results}

                        ANSWER FORMAT:
                        ```python
                            <codigo python>
                        ```
                        """},
                        {"role": "user", "content": task}
                    ]
                    code_response = query_llm(task_messages)
                    st.write(f"**{task}**\n {code_response}")
                    code_response = code_response.split("```python")[1].split('```')[0].strip()
                    # Ejecutar el código generado
                    result = execute_code(code_response,final_results)

                    if "error" in result:
                        st.error(f"Error al ejecutar la tarea: {task}\n{result['error']}")
                    else:
                        final_results = result

            # Paso 3: Respuesta final
            final_message = [
                {"role": "system", "content": f"Genera una respuesta a la siguiente consulta: {user_query} basada en los siguientes resultados."},
                {"role": "user", "content": str(final_results)}
            ]
            final_response = query_llm(final_message)
            st.write("**Respuesta final:**", final_response)

            # Paso 4: Generar visualizaciones
            if st.checkbox("Generar gráficos/tablas para los resultados"):
                for result in final_results:
                    if isinstance(result, pd.DataFrame):
                        chart = alt.Chart(result).mark_bar().encode(
                            x=result.columns[0],
                            y=result.columns[1]
                        )
                        st.altair_chart(chart, use_container_width=True)

# Nota sobre la API de Groq
st.sidebar.info("Usando el modelo 'llama-3.3-70b-versatile' a través de la API de Groq.")
