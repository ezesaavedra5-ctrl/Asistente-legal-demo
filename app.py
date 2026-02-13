import streamlit as st
from groq import Groq
import re

# 1. Agenda del Estudio (Editable)
turnos_ocupados = ["Lunes 16:00", "Lunes 17:00", "Miércoles 18:30"]

st.set_page_config(page_title="Asistente Legal Saavedra", page_icon="⚖️")
st.title("Asistente Legal Saavedra ⚖️")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": f"""Eres el Asistente Virtual del Estudio Saavedra. 
            UBICACIÓN: San Martín 1234, Santa Fe.
            HORARIOS: Lunes a Viernes de 16 a 20 hs.
            TURNOS OCUPADOS: {', '.join(turnos_ocupados)}.
            
            REGLAS DE ORO:
            1. NO menciones turnos ocupados de otros días si el cliente pregunta por un día específico.
            2. Si el cliente elige un día, revisa si hay algo ocupado ESE DÍA. Si no, ofrece opciones entre 16 y 20 hs.
            3. Pide Nombre, Teléfono y Motivo.
            4. Solo cuando TODO esté acordado (Nombre, Tel, Motivo y Hora), confirma la cita.
            5. PARA FINALIZAR: Debes usar exactamente la frase "TURNO CONFIRMADO EXITOSAMENTE" para que el sistema cierre el registro. 
            6. Sé formal (español rioplatense) y evita errores gramaticales."""
        }
    ]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("¿En qué puedo ayudarlo?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages
        )
        full_response = response.choices[0].message.content
        st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # --- LÓGICA DE FICHA PROFESIONAL REFINADA ---
    # Ahora usamos una frase larga para que no aparezca antes de tiempo
    if "turno confirmado exitosamente" in full_response.lower():
        st.divider()
        
        nombre_final = "Cliente"
        fecha_final = "A confirmar"
        
        # 1. Extracción de nombre (reforzada)
        for m in reversed(st.session_state.messages):
            if m["role"] == "user":
                content = m["content"].lower()
                if "mi nombre es" in content:
                    nombre_final = m["content"].lower().split("nombre es")[-1].strip().split('.')[0].split(',')[0].split(' y ')[0].title()
                    break
                elif "soy " in content:
                    nombre_final = m["content"].lower().split("soy")[-1].strip().split('.')[0].split(',')[0].title()
                    break

        # 2. Extracción de Fecha y Hora del mensaje de la IA
        dias = ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes"]
        for dia in dias:
            if dia in full_response.lower():
                fecha_final = dia.capitalize()
                break
        
        hora_match = re.search(r'(\d{1,2}:\d{2})', full_response)
        if hora_match:
            fecha_final += f" a las {hora_match.group(1)} hs"

        # 3. Interfaz Visual
        st.success("### ✅ Turno Registrado en Agenda")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**👤 Cliente:** \n{nombre_final}")
                st.write(f"**📅 Cita:** \n{fecha_final}")
            with col2:
                st.write("**📍 Ubicación:** \nSan Martín 1234, Santa Fe")
                st.write("**⚖️ Estado:** \nConfirmado")
        
        st.caption("ℹ️ Este es un registro digital del Estudio Jurídico Saavedra.")
