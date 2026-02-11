import streamlit as st
from groq import Groq

st.title("Asistente Legal Inteligente")

# Configura tu API Key aquí (luego la pondremos oculta)
client = Groq(api_key="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")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "Eres un asistente de un estudio jurídico. Tu meta es filtrar el caso y agendar una cita. No des consejos legales."}]

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

