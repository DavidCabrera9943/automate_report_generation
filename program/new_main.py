import streamlit as st
import pandas as pd
import altair as alt
import os
import io
from config import groq_models
from data_processing import get_document_info, preprocess_document
from report_generation import generate_report_skeleton, generate_section_data, generate_section_charts, generate_report_section_text
from llm_api import query_llm
import json

# Sidebar setup
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


# Main app
st.title("Generador de Reportes Automatizados con LLM")

# Paso 1: Subir documento
document_file = st.file_uploader("Sube tu documento", type=["csv", "xlsx", "json"])


if document_file:
    with st.spinner("Obteniendo información del documento..."):
        document_info = get_document_info(document_file)
        if "error" in document_info:
            st.error(document_info["error"])
        else:
            st.success("Documento cargado con éxito.")

            with st.spinner("Preprocesando el documento..."):
                preprocess_result = preprocess_document(query_llm) # Pass query_llm here
                if "error" in preprocess_result:
                    st.error(preprocess_result["error"])
                else:
                    st.success("Preprocesamiento completado.")

            # Paso 2: Recibir query del usuario
            user_query = st.text_area("Escribe tu consulta:")

            if st.button("Generar Reporte") and user_query:
                with st.spinner("Generando reporte..."):
                    # Paso 3: Generar esqueleto del reporte
                    skeleton_response = generate_report_skeleton(document_info, user_query)
                    if debug:
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

                    # Paso 4: Generar cada sección del reporte
                    report_sections_text = {}
                    report_sections_charts = {}

                    for section in json.loads(skeleton_response):
                        section_name = section["section"]["name"]
                        section_description = section["section"]["description"]
                        section_data = section["section"]["data"]
                        section_extra_data = section["section"]["extra_data"]

                        with st.spinner(f"Generando datos para la sección: {section_name}"):
                            response = generate_section_data(document_info, section_name, section_description, section_data, section_extra_data)
                            report_sections_text[section_name] = response
                            if debug:
                                if response:
                                    st.write(f"**Sección {section_name} - Data Response**")
                                    st.write(response)
                                else:
                                    st.write(f"**Sección {section_name} - Data Response**")
                                    st.write("No se ha generado ninguna respuesta de datos.")

                        with st.spinner(f"Generando gráficos para la sección: {section_name}"):
                            chart_response = generate_section_charts(document_info, section_name, section_description, section_data, section_extra_data)
                            report_sections_charts[section_name] = chart_response

                            if debug:
                                if chart_response:
                                    st.write(f"**Sección {section_name} - Charts Code Response**")
                                    st.write(chart_response)
                                    for c in chart_response:
                                        st.altair_chart(c['c'],use_container_width = True)
                                else:
                                    st.write(f"**Sección {section_name} - Charts Code Response**")
                                    st.write("No Chart Generated")

                        charts_names = [{'name':item['name'],'descripcion':item['descripcion']} if item else {} for item in (chart_response if chart_response else [])] #Handle None chart_response

                        with st.spinner(f"Generando texto final para la sección: {section_name}"):
                            final_response = generate_report_section_text(document_info, section_name, section_description, section_data, section_extra_data, response, charts_names)

                            st.write(f"**Sección {section_name}**")
                            parts = final_response.split("```chart") # Dividimos el string usando ```chart como delimitador

                            for i, part in enumerate(parts):
                                if i == 0: # La primera parte siempre es texto antes del primer chart (o todo el texto si no hay charts)
                                    if part.strip(): # Verificamos que no este vacio despues de quitar espacios en blanco
                                        st.write(part.strip())
                                else: # Las partes siguientes vienen despues de un ```chart
                                    chart_block_parts = part.split("```") # Dividimos la parte en subpartes usando ``` como delimitador

                                    if len(chart_block_parts) >= 2: # Debe haber al menos 2 partes si hay un bloque chart
                                        chart_name = chart_block_parts[0].strip() # El nombre del chart esta antes del primer ``` de cierre
                                        chart_obj = None
                                        if report_sections_charts.get(section_name): # Check charts exist for this section
                                            for chart_item in report_sections_charts[section_name]:
                                                if chart_item['name'] == chart_name:
                                                    chart_obj = chart_item['c']
                                                    break
                                        if chart_obj is not None:
                                            st.altair_chart(chart_obj, use_container_width=True) # Display chart if found

                                        text_after_chart = chart_block_parts[1] if len(chart_block_parts) > 1 else "" # El texto despues del chart, si existe
                                        if text_after_chart.strip(): # Verificamos que haya texto despues del chart
                                            st.write(text_after_chart.strip())