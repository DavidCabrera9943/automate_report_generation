import pandas as pd
import io
import groq


def analizar_csv(csv_path):
    """Analiza un CSV y devuelve información sobre sus columnas."""
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return f"Error al leer el CSV: {e}"
        
    column_info = {}
    for col in df.columns:
        column_info[col] = {
            'type': str(df[col].dtype),
            'unique_values': df[col].unique().tolist()[:5] if df[col].nunique() < 20 else "Too Many to show", # Limitar para no sobrecargar el context
            'has_nulls': df[col].isnull().any()
        }
    return df.head(),column_info

a  = analizar_csv("car_prices.csv")
print(a)


prompt_tareas_atomicas = [
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