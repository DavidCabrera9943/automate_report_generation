import streamlit as st
import pandas as pd
import altair as alt

def execute_code(code):
    """Ejecuta código Python de manera segura."""
    try:
        local_vars = {'df': st.session_state.dataframe, 'pd': pd, 'alt': alt, 'st': st} # Make pd, alt and st available
        exec(code, {}, local_vars)
        return local_vars.get('response', None) # Use .get to avoid KeyError if 'response' is not set

    except Exception as e:
        return {"error": str(e)}