import pandas as pd
from streamlit.runtime.uploaded_file_manager import UploadedFile
import streamlit as st
import json

def get_document_info(document: UploadedFile):
    """Obtiene información relevante del documento cargado."""
    if document.type == "text/csv":
        st.session_state.dataframe = pd.read_csv(document)
    elif document.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        st.session_state.dataframe = pd.read_excel(document)
    elif document.type == "application/json":
        try:
            st.session_state.dataframe = pd.read_json(document)
        except ValueError: # Handle potential JSONDecodeError explicitly
            try:
                # Attempt to read line by line if it's a newline-delimited JSON
                lines = document.read().decode('utf-8').strip().split('\n')
                data = [json.loads(line) for line in lines if line] # Filter out empty lines
                st.session_state.dataframe = pd.DataFrame(data)
            except Exception as e_json_lines:
                return {"error": f"Error reading JSON document: {e_json_lines}. Ensure it is valid JSON or newline-delimited JSON."}


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

    return info

def preprocess_document(query_llm):
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
            Columnas: {st.session_state.dataframe.columns.tolist()}
            Tipos: {st.session_state.dataframe.dtypes.to_dict()}
            Primeras filas: {st.session_state.dataframe.head().to_dict()}
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

        if not column_name or column_name not in st.session_state.dataframe.columns:
            return {"error": f"Nombre de columna inválido: {column_name}"}

        if task_name == "convertir_fecha":
            date_format = task.get("formato")
            preprocess_code = f"""
            st.session_state.dataframe['{column_name}'] = pd.to_datetime(st.session_state.dataframe['{column_name}'], format='{date_format}')
            """
        elif task_name == "identificar_categorica":
            preprocess_code = f"""
            categorias = st.session_state.dataframe['{column_name}'].unique().tolist()
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

        try:
            exec(preprocess_code, globals()) # Consider security implications of exec
        except Exception as e:
            return {"error": f"Error al ejecutar la tarea '{task_name}' en la columna '{column_name}': {e}"}

    return {"success": "Preprocesamiento completado"}