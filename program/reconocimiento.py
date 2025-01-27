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