import streamlit as st
from groq import Groq

st.title("Asistente Legal Inteligente")

# Configura tu API Key aquí (luego la pondremos oculta)
client = Groq(api_key="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")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": """Eres el Asistente Virtual de Élite del Estudio Jurídico Saavedra. 
UBICACIÓN: San Martín 1234, Santa Fe. 
HORARIOS: Lunes a Viernes de 16:00 a 20:00 hs. 

REGLAS DE ORO:
1. NUNCA des montos de dinero, porcentajes de indemnización ni consejos legales. Di: 'Esa es una excelente pregunta para el Dr. Saavedra durante la consulta'.
2. GESTIÓN DE CITAS: Solo ofrece turnos de Lunes a Viernes entre las 16 y las 20 hs. Si el cliente pide otro horario, explica amablemente el horario del estudio.
3. DATOS OBLIGATORIOS: Para confirmar, debes obtener: Nombre, Teléfono y motivo de consulta.
4. IDIOMA: Español rioplatense formal (usted). Gramática perfecta (uso de 'e' e 'i' correctamente).
5. RESPUESTA ANTE EL CONFLICTO: Si el cliente se muestra agresivo, mantén la calma y ofrece agendar la cita para que el profesional lo ayude personalmente.
6. CONCISIÓN: Mantén tus respuestas breves y directas. No te extiendas más de lo necesario."""}]
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("¿En qué podemos ayudarle?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages
        )
        full_response = response.choices[0].message.content
        st.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})





