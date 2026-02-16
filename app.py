import streamlit as st
from groq import Groq
import re
import gspread
from google.oauth2.service_account import Credentials

# --- FUNCIÓN PARA GUARDAR EN GOOGLE SHEETS ---
def guardar_en_excel(fecha, nombre, telefono, motivo):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client_gs = gspread.authorize(creds)
        
        # Abrimos el archivo
        sheet = client_gs.open("Agenda de turnos").sheet1
        
        # Guardamos en el orden de tus columnas: Fecha, Nombre, Teléfono, Motivo
        sheet.append_row([fecha, nombre, telefono, motivo])
        return True
    except Exception as e:
        st.sidebar.error(f"Error de sincronización: {e}")
        return False

# 1. Configuración de la Agenda
turnos_ocupados = ["Lunes 16:00", "Lunes 17:00", "Miércoles 18:30"]

st.set_page_config(page_title="Asistente Legal Saavedra", page_icon="⚖️")
st.title("Asistente Legal Saavedra ⚖️")

# Cliente Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": f"""Eres el Asistente Virtual del Estudio Saavedra en Santa Fe.
            HORARIOS: Lunes a Viernes de 16 a 20 hs.
            TURNOS OCUPADOS: {', '.join(turnos_ocupados)}.
            
            REGLAS:
            1. Pide Nombre, Teléfono y Motivo de consulta.
            2. Solo cuando tengas todos los datos, confirma con la frase: "TURNO CONFIRMADO EXITOSAMENTE".
            3. Sé formal y utiliza español rioplatense."""
        }
    ]

# Mostrar historial
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Lógica del Chat
if prompt := st.chat_input("¿En qué puedo ayudarlo?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages
            )
            full_response = response.choices[0].message.content
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # --- DETECCIÓN DE TURNO CONFIRMADO ---
            if "turno confirmado exitosamente" in full_response.lower():
                st.divider()
                
                nombre_final = "No identificado"
                tel_final = "No proporcionado"
                motivo_final = "Consulta General"
                fecha_final = "A confirmar"
                
                # 1. Analizar historial para extraer datos
                texto_completo = ""
                for m in st.session_state.messages:
                    if m["role"] == "user":
                        content = m["content"].lower()
                        texto_completo += " " + content
                        
                        # Extraer Nombre
                        if "mi nombre es" in content:
                            nombre_final = m["content"].lower().split("nombre es")[-1].strip().split('.')[0].title()
                        elif "soy " in content:
                            nombre_final = m["content"].lower().split("soy")[-1].strip().split('.')[0].title()
                        
                        # Extraer Teléfono (secuencia de números)
                        nums = re.findall(r'\d{8,14}', content)
                        if nums: tel_final = nums[0]

                # 2. Detección Inteligente de Motivo
                temas = {
                    "Divorcio": ["divorcio", "separacion", "conyuge", "casamiento"],
                    "Sucesión": ["sucesion", "herencia", "fallecio", "bienes"],
                    "Accidente": ["accidente", "choque", "seguro", "lesion"],
                    "Laboral": ["despido", "trabajo", "empleo", "sueldo", "art"]
                }
                for tema, palabras in temas.items():
                    if any(p in texto_completo for p in palabras):
                        motivo_final = tema
                        break

                # 3. Extracción y Normalización de Fecha/Hora
                dias = ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes"]
                for dia in dias:
                    if dia in full_response.lower():
                        fecha_final = dia.capitalize()
                        break
                
                # Buscar hora (formato 19:00 o solo 19)
                hora_completa = re.search(r'(\d{1,2}):(\d{2})', full_response)
                hora_simple = re.search(r'las (\d{1,2})', full_response.lower())
                
                if hora_completa:
                    fecha_final += f" a las {hora_completa.group(1)}:{hora_completa.group(2)} hs"
                elif hora_simple:
                    # Normalización: si dice "19", ponemos "19:00"
                    fecha_final += f" a las {hora_simple.group(1)}:00 hs"

                # 4. GUARDADO EN EXCEL (Orden: Fecha, Nombre, Teléfono, Motivo)
                if guardar_en_excel(fecha_final, nombre_final, tel_final, motivo_final):
                    st.toast("✅ Sincronizado con el estudio")

                # 5. Interfaz Visual
                st.success("### ✅ Turno Registrado en Agenda")
                with st.container(border=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**👤 Cliente:** {nombre_final}")
                        st.write(f"**📞 Teléfono:** {tel_final}")
                    with col2:
                        st.write(f"**📅 Cita:** {fecha_final}")
                        st.write(f"**📝 Motivo:** {motivo_final}")
                st.caption("ℹ️ Registro automático - Estudio Jurídico Saavedra.")

        except Exception as e:
            st.error("⚠️ El sistema está experimentando una demora.")
            if len(st.session_state.messages) > 0:
                st.session_state.messages.pop()

