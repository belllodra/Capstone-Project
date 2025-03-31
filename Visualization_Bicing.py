import gradio as gr
import plotly.graph_objects as go
import pandas as pd
import random


import joblib

simple_model = joblib.load('modelo_docks.pkl')
df_stations = pd.read_csv('Informacio_Estacions_Bicing_2025.csv')



def get_station_location(station_id, df):
    row = df[df['station_id'] == station_id]
    if not row.empty:
        latitude = row.iloc[0]['lat']
        longitude = row.iloc[0]['lon']
        address = row.iloc[0]['address']
        return latitude, longitude, address
    return None, None, None  # Return None if the station_id is not found

def filter_map(min_availability, selected_day, selected_month, selected_hour,
               ctx4, ctx3, ctx2, ctx1, tavg, prcp):
    """Filter stations based on availability, weather conditions, and display them on a map."""

    df = df_stations[['station_id']].copy()
    df['day'] = selected_day
    df['month'] = selected_month
    df['hour'] = selected_hour
    df['ctx-4'] = ctx4
    df['ctx-3'] = ctx3
    df['ctx-2'] = ctx2
    df['ctx-1'] = ctx1
    df['temperature_2m (°C)'] = tavg
    df['precipitation (mm)'] = prcp
   

    # Predict availability using the updated model
    df['availability'] = simple_model.predict(df[['station_id', 'month', 'day', 'hour',
                                              'ctx-4', 'ctx-3', 'ctx-2', 'ctx-1',
                                              'temperature_2m (°C)', 'precipitation (mm)']])


    # Filter stations based on availability
    filtered_df = df[df['availability'] > min_availability].copy()

    # Fetch latitude, longitude, and address dynamically
    filtered_df[['latitude', 'longitude', 'address']] = pd.DataFrame(
        filtered_df['station_id'].apply(lambda sid: get_station_location(sid, df_stations)).tolist(),
        index=filtered_df.index
    )

    # Remove rows where location is missing
    filtered_df = filtered_df.dropna(subset=['latitude', 'longitude'])

    # Format the hover text with HTML line breaks
    hover_texts = [
        f"<b>🚲 Station {id}</b><br>"
        f"🔵 <b>Availability:</b> {avail:.2f}<br>"
        f"🏠 <b>Address:</b> {addr}"
        for id, avail, addr in zip(filtered_df['station_id'], filtered_df['availability'], filtered_df['address'])
    ]

    fig = go.Figure(go.Scattermapbox(
        lat=filtered_df['latitude'],
        lon=filtered_df['longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(size=8, color='blue'),
        text=hover_texts,
        hoverinfo="text"
    ))

    fig.update_layout(
        mapbox_style="open-street-map",
        hovermode='closest',
        mapbox=dict(
            center=dict(lat=41.38, lon=2.17),
            zoom=13
        )
    )
    return fig

# Gradio UI with updated weather variable names
with gr.Blocks(css="body {background-color: #070708; font-family: 'Segoe UI', sans-serif;}") as demo:
    gr.Markdown("### 🗺️ **Bike Availability Map**", elem_id="title")
    gr.Markdown("Ajusta els filtres per veure les estacions amb disponibilitat predita sobre un mapa interactiu.")

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("#### 📅 Filtres Principals")
            min_availability = gr.Slider(0, 1, value=0.2, label="🔵 Mínim de disponibilitat", interactive=True)
            selected_day = gr.Slider(1, 31, value=1, step=1, label="📅 Dia", interactive=True)
            selected_month = gr.Slider(1, 12, value=6, step=1, label="🗓️ Mes", interactive=True)
            selected_hour = gr.Slider(0, 23, value=12, step=1, label="⏰ Hora", interactive=True)

        with gr.Column(scale=1):
            with gr.Accordion("⚙️ Filtres Avançats", open=False):
                selected_ctx4 = gr.Number(value=0.49, label="ctx-4", interactive=True)
                selected_ctx3 = gr.Number(value=0.38, label="ctx-3", interactive=True)
                selected_ctx2 = gr.Number(value=0.32, label="ctx-2", interactive=True)
                selected_ctx1 = gr.Number(value=0.31, label="ctx-1", interactive=True)

            with gr.Accordion("🌦️ Condicions Meteo", open=False):
                tavg = gr.Number(value=20.0, label="🌡️ Temperatura Mitjana (°C)", interactive=True)
                prcp = gr.Number(value=0.0, label="🌧️ Precipitació (mm)", interactive=True)

    btn = gr.Button("🔍 Filtrar estacions", size="lg")

    gr.Markdown("---")
    gr.Markdown("### 🌍 Resultats sobre el mapa")
    map_plot = gr.Plot()

    btn.click(
        filter_map,
        inputs=[min_availability, selected_day, selected_month, selected_hour,
                selected_ctx4, selected_ctx3, selected_ctx2, selected_ctx1,
                tavg, prcp],
        outputs=map_plot
    )

if __name__ == "__main__":
    demo.launch(share=True)