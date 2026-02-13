import streamlit as st
from groq import Groq

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
            
            REGLAS:
            1. Pide Nombre, Teléfono y Motivo.
            2. Al confirmar usa la palabra 'AGENDADA' para finalizar.
            3. Sé breve y muy formal."""
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

    # --- LÓGICA DE FICHA DE REGISTRO (v2.3 Sin PDF, Más Robusta) ---
    pistas = ["agendada", "confirmada", "registrada", "pactada", "agendado"]
    if any(p in full_response.lower() for p in pistas):
        st.divider()
        
        # 1. Extracción de nombre refinada
        nombre_final = "Cliente"
        for m in reversed(st.session_state.messages):
            if m["role"] == "user":
                content = m["content"].lower()
                if "nombre es" in content:
                    # Tomamos lo que sigue a "nombre es"
                    sucio = m["content"].lower().split("nombre es")[-1].strip()
                    # Cortamos si hay un punto, una coma o la palabra "y"
                    limpio = sucio.split('.')[0].split(',')[0].split(' y ')[0]
                    nombre_final = limpio.title()
                    break
        
        # 2. Diseño de la Ficha Profesional
        st.success("### ✅ Registro de Turno Confirmado")
        st.write("Para su seguridad y constancia, aquí tiene los detalles de su cita:")
        
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**👤 Cliente:** \n{nombre_final}")
                st.write("**📍 Ubicación:** \nSan Martín 1234, Santa Fe")
            with col2:
                st.write("**📅 Fecha y Hora:** \nSegún lo acordado")
                st.write("**⚖️ Estado:** \nRegistrado en Agenda")
        
        st.caption("Esta ficha ha sido generada por el sistema de gestión del Estudio Saavedra.")
