import gradio as gr
import joblib
import pandas as pd
import numpy as np
import re
import requests
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Cargar modelo y dataset
model = joblib.load("modelo_docks.pkl")
df_stations = pd.read_csv("Informacio_Estacions_Bicing_2025.csv")
geolocator = Nominatim(user_agent="bicing-agent")

from groq import Groq

client = Groq(api_key="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")

# LLM: llama-3.3-70b-versatile
def preguntar_al_usuario(pregunta):
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Eres un asistente de Bicing. Tu tarea es hacer una preguntal usuario y esperar su respuesta. No saludes a menos que te lo pida"},
            {"role": "user", "content": f"Pregunta al usuario lo siguiente, puedes modificar el tono para hacerlo mas amigable y añadir ayudas adicionales sobre como introducir los datos: '{pregunta}'"}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        max_completion_tokens=512,
        top_p=1,
        stream=False,
    )
    return response.choices[0].message.content.strip()

# Estaciones más cercanas
def get_nearest_stations(ubicacion, top_n=10):
    loc = geolocator.geocode(f"{ubicacion}, Barcelona, Spain")
    if not loc:
        return pd.DataFrame()

    user_coord = (loc.latitude, loc.longitude)
    df_stations["distancia"] = df_stations.apply(
        lambda row: geodesic(user_coord, (row["lat"], row["lon"])).meters,
        axis=1
    )
    return df_stations.nsmallest(top_n, "distancia")[["station_id", "address", "lat", "lon"]]

# Tiempo (Open-Meteo)
def get_weather_forecast(lat, lon, year, month, day, hour):
    fecha = f"{year}-{month:02d}-{day:02d}"
    hora_str = f"{hour:02d}:00"

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&timezone=Europe%2FMadrid"
        f"&start_date={fecha}&end_date={fecha}"
    )

    r = requests.get(url)
    if r.status_code != 200:
        return None, None

    data = r.json()
    horas = data["hourly"]["time"]
    temperaturas = data["hourly"]["temperature_2m"]
    precipitaciones = data["hourly"]["precipitation"]

    for i, h in enumerate(horas):
        if h.endswith(hora_str):
            return temperaturas[i], precipitaciones[i]

    return None, None

# Predicción con el modelo
def predict_disponibilidad(context):
    estaciones_cercanas = get_nearest_stations(context["ubicacion"])
    if estaciones_cercanas.empty:
        return {"error": "No se encontraron estaciones cercanas."}

    resultados = []

    for _, row in estaciones_cercanas.iterrows():
        temp, precip = get_weather_forecast(
            row["lat"], row["lon"], 2025,
            context["month"], context["day"], context["hour"]
        )
        if temp is None:
            continue

        X = np.array([[
            row["station_id"],
            context["month"],
            context["day"],
            context["hour"],
            context["ctx_value"], context["ctx_value"], context["ctx_value"], context["ctx_value"],
            temp,
            precip
        ]])
        pred = model.predict(X)[0]

        resultados.append({
            "station_id": row["station_id"],
            "address": row["address"],
            "pred_pct": float(pred),
            "temperature": round(temp, 1),
            "precip": round(precip, 1)
        })

    if not resultados:
        return {"error": "No se pudieron calcular predicciones meteorológicas."}

    resultados_ordenados = sorted(resultados, key=lambda x: x["pred_pct"], reverse=True)
    return {
        "target_pct": context["target_pct"],
        "candidatas": resultados_ordenados
    }

# Preguntas al usuario
preguntas = [
    ("ubicacion", "INTRODUCE SALUDO y la pregunta ¿Dónde te gustaría coger la bici? (zona o dirección en Barcelona)"),
    ("month", "¿En qué mes planeas cogerla? (número 1-12)"),
    ("day", "¿Qué día del mes?"),
    ("hour", "¿A qué hora la necesitas? (0-23)?"),
    ("target_pct", "¿Qué porcentaje mínimo de bicicletas esperas encontrar disponibles? (0 a 100%)")
]

# Flujo de conversación
def chat(user_input, chat_history, current_step, user_context):
    key, _ = preguntas[current_step]

    if key in ["month", "day", "hour", "target_pct"]:
        match = re.search(r"\d+(\.\d+)?", user_input)
        if match:
            value = float(match.group())
            user_context[key] = value / 100 if key == "target_pct" else int(value)
        else:
            chat_history.append(("user", user_input))
            chat_history.append(("assistant", "Introduce un número válido."))
            return chat_history, current_step, user_context
    else:
        user_context[key] = user_input.strip()

    chat_history.append(("user", user_input))
    current_step += 1

    if current_step < len(preguntas):
        siguiente_pregunta = preguntar_al_usuario(preguntas[current_step][1])
        chat_history.append(("assistant", siguiente_pregunta))
    else:
        resultado = predict_disponibilidad(user_context)
        if "error" in resultado:
            chat_history.append(("assistant", resultado["error"] + " Reiniciando conversación..."))
            user_context = {
                "ubicacion": None,
                "month": None,
                "day": None,
                "hour": None,
                "target_pct": None,
                "temperature": None,
                "lluvia": None
            }
            current_step = 0
            chat_history.append(("assistant", preguntar_al_usuario(preguntas[0][1])))
            return chat_history, current_step, user_context
        else:
            clima = resultado["candidatas"][0]

            # 🧾 Resumen del contexto
            fecha_str = f"{user_context['day']:02d}/{user_context['month']:02d}/2025"
            hora_str = f"{user_context['hour']:02d}:00h"
            resumen_contexto = (
                f"📍 *Ubicación*: {user_context['ubicacion']}\n"
                f"🗓️ *Día*: {fecha_str}\n"
                f"🕒 *Hora*: {hora_str}\n"
                f"🎯 *Porcentaje mínimo deseado de bicis*: {int(user_context['target_pct'] * 100)}%"
            )

            # 📈 Predicción meteorológica
            resumen_meteo = (
                f"🌡️ *Temperatura esperada*: {clima['temperature']}°C\n"
                f"☔ *Precipitación esperada*: {clima['precip']} mm"
            )

            # 🚲 Disponibilidad de estaciones

            candidatas = resultado["candidatas"]
            hay_suficientes = any(r["pred_pct"] >= resultado["target_pct"] for r in candidatas)

            # 🚲 Disponibilidad de estaciones
            msg_estaciones = "🚲 *Estaciones más cercanas ordenadas por disponibilidad:*\n"
            for r in candidatas:
                emoji = "✅" if r["pred_pct"] >= resultado["target_pct"] else "⚠️"
                msg_estaciones += (
                    f"{emoji} '{r['address']}' (ID {r['station_id']}): "
                    f"{round(r['pred_pct']*100)}% disponibilidad\n"
                )

            if not hay_suficientes:
                msg_estaciones += (
                    "\n⚠️ *Aviso:* ninguna estación cercana alcanza el porcentaje mínimo deseado "
                    f"de {int(resultado['target_pct'] * 100)}%. Puedes intentar con otro horario o ubicación."
                )

            for r in resultado["candidatas"]:
                emoji = "✅" if r["pred_pct"] >= resultado["target_pct"] else "⚠️"
                msg_estaciones += (
                    f"{emoji} '{r['address']}' (ID {r['station_id']}): "
                    f"{round(r['pred_pct']*100)}% disponibilidad\n"
                )

            # Construir mensaje completo
            mensaje_final = f"{resumen_contexto}\n\n{resumen_meteo}\n\n{msg_estaciones}"
            chat_history.append(("assistant", mensaje_final.strip()))

            # 🧠 Resumen generado por LLM
            resumen_llm = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un asistente experto en movilidad urbana. Resume al usuario de forma clara y amigable "
                            "si podrá encontrar bicis disponibles. se breve."
                        )
                    },
                    {"role": "user", "content": mensaje_final.strip()}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.5,
                max_completion_tokens=256
            ).choices[0].message.content.strip()

            # Añadir texto fijo al final del resumen
            resumen_llm += "\n\nSi quieres hacer otra consulta, dime una nueva ubicación o escribe 'reiniciar'."

            chat_history.append(("assistant", resumen_llm))

    return chat_history, current_step, user_context


# Interfaz Gradio
with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    txt = gr.Textbox(placeholder="Escribe tu respuesta...", label="Tu mensaje")

    # Nuevo input para ctx histórico
    ctx_selector = gr.Dropdown(
        choices=["alto", "medio", "bajo"],
        value="medio",
        label="Nivel de ocupación histórica (ctx)"
    )

    state_chat = gr.State([])
    state_step = gr.State(0)
    state_context = gr.State({
        "ubicacion": None,
        "month": None,
        "day": None,
        "hour": None,
        "target_pct": None,
        "ctx_value": 0.5,  # valor por defecto
        "temperature": None,
        "lluvia": None
    })

    def user_submit(message, chat_history, current_step, user_context, ctx_selector_value):
        # Mapear valor textual a número
        ctx_map = {"alto": 0.9, "medio": 0.5, "bajo": 0.1}
        user_context["ctx_value"] = ctx_map.get(ctx_selector_value, 0.5)
        return chat(message, chat_history, current_step, user_context)

    txt.submit(
        user_submit,
        inputs=[txt, state_chat, state_step, state_context, ctx_selector],
        outputs=[chatbot, state_step, state_context]
    )

    # Primer mensaje
    primer_pregunta = preguntar_al_usuario(preguntas[0][1])
    state_chat.value = [("assistant", primer_pregunta)]
    chatbot.value = state_chat.value

demo.launch()
