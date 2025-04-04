# Capstone-Project

# CREACIÓN DEL DATASET DE ENTRENAMIENTO
Para este apartado hemos realizado una función denominada transform_bike_data_dask, que recibe como parametro la lista de los csv. Hemos decidido utilizar Dask, como se nos sugirió en clase. La función realiza los siguientes pasos: 
- Conversión de timestamps (last_updated) y extracción de hora.
- Cálculo del número total de docks por estación (total_docks).
- Cálculo del porcentaje de disponibilidad de docks.
- Cálculo de contexto temporal (ctx-0 a ctx-4) usando shift para obtener las columnas ctx-0 a ctx-4, siendo ctx-0 la y.
Además añadimos la columna year que utilizaremos más tarde.

# PREPROCESAMIENTO
Hemos considerado eliminar los valores NAs directamente asi como tomar los datos desde 2021. Estas consideraciones han sido tomadas debido a pruebas realizadas del rendimiento del modelo.

# DATOS EXTERIORES AÑADIDOS
Hemos obtenido los datos meteorológicos de la API de Open-Meteo, donde se pueden descargar el historico de datos meteorológicos por latitud, longitud por horas. Hemos realizado un preoprocesamiento de los csv que se generan y posteriormente hacemos el merge a las del dataset de entrenamiento y al de test. En este momento es cuando se necesita la columna year, que finalmente eliminamos. Obteniendo las columnas: station_id | month |	day	| hour |	ctx-4	| ctx-3	| ctx-2	| ctx-1 |	temperature_2m (°C)	| precipitation (mm)

# MODELOS PROBADOS
Primeramente hicimos pruebas con el modelo de regresión lineal, los resultados fueron bastante buenos. 
Despues realizamos pruebas con una red neuronal simple, obteniendo peores resultados.
El siguiente modelo sobre el que realizamos pruebas fue  XGBRegressor, obteniendo los mejores resultados.
También probamos otros modelos como random forest o LGBMRegressor, dandonos peores resultados.
El modelo final ha sido el XGBRegressor(n_estimators=400, learning_rate=0.05, max_depth=12)

# VISUALIZACIÓN DE LOS DATOS
La visualización de los datos se encuentra disponible en el siguiente enlace: https://huggingface.co/spaces/adriansanz/bicis. Para hacer la visualización se ha utilizado utilizado la librería Gradio. Los pasos a realizar son los siguientes:
- Se importan librerías, se carga el modelo que mejor ha funcionado (XGBRegressor) y un dataset (Informacio_Estacions_Bicing_2025.csv) con información de las estaciones de Bicing en Barcelona.
- Hemos definido una función llamada get_station_location que a partir del station_id devuelve los valores de latitud y longitud (para situarlo en el mapa) y la dirección proporcionada como argumento de entrada (para mostrar la dirección de las estaciones disponibles).
- Hemos definido una función llamada filter_map que a partir de unos parámetros de entrada (coincidentes con los propios parámetros del modelo y la disponibilidad mínima) y predice la disponibilidad de bicis en todas las estaciones usando el modelo cargado.
- El valor de entrada de la disponibilidad es utilizado para filtrar todos aquellos outputs con una disponibilidad mayor a la deseada por el usuario.
- Se buscan las coordenadas de cada estación (llamando a la función get_station_location) y se eliminan aquellas sin datos de ubicación.
- Se usa plotly para mostrar las estaciones disponibles en un mapa interactivo con Scattermapbox.
- Se crea una UI con gr.Blocks que permite a los usuarios ajustar filtros y visualizar resultados.
- Como filtros principales seleccionamos el día, mes, hora y disponibilidad mínima.
- Como filtros avanzados encontramos la disponibilidad en las 4 horas previas, y 2 variables meteorológicas (temperatura y precipitación).
- El botoón "Filtrar estacions" activa filter_map, actualizando el mapa con estaciones disponibles.

# Caso de estudio 1: Fiestas de barrio
Para hacer un análisis de cómo la demanda de Bicing cambiaba dependiendo de si había fiestas en el barrio, primero hemos agrupado las estaciones de Bicing (station_id) según el barrio de Barcelona en el que se encuentran. Luego, hemos creado una variable dummy: 1 si había fiestas en el barrio ese día, mes y año, y 0 en caso contrario. Esta información sobre las fiestas se ha tenido que recopilar manualmente, ya que no existe una base de datos a nivel Barcelona. Finalmente, hemos analizado cómo cambiaba la demanda de bicicletas si había fiestas de barrio o no, utilizando una media general, pero también observando si, dentro de los meses en los que había fiestas, la demanda variaba considerablemente. Los resultados para 2023, el año con más normalidad en términos de movilidad y fiestas, sugieren que, en general, las fiestas de barrio no afectan a la demanda de bicicletas. Sin embargo, en algunos barrios sí se observó un cambio significativo, aunque para la mayoría no fue así. Barrios como Sant Gervasi - Galvany, Les Corts y La Sagrera muestran los mayores aumentos en disponibilidad. Mientras otros barrios como La Verneda i la Pau, Sant Martí de Provençals y La Vila Olímpica del Poblenou, muestran una reducción en la disponibilidad de docks durante las fiestas de barrio. Por lo tanto, a pesar de haber analizado esta nueva variable, no se ha añadido a ningún modelo de predicción para los datos de 2024.

# Caso de estudio 2: Agente conversacional
Hemos decidido crear un agente conversacional para recomendar estaciones de Bicing, ya que permite una interacción natural, guía al usuario paso a paso. Hemos decidido automatizar la consulta de predicción meteorológica y de obtención de que estaciónes estan cerca de la ubicación que se solicita, siendo útil para mejorar la experiencia de planificación de trayectos en bici.
El agente conversacional guía al usuario preguntando ubicación, fecha, hora y porcentaje deseado de bicis disponibles. Luego:
-Busca las 10 estaciones más cercanas respecto a la ubicación que se ha solicitado, para ello usa Nominatim, que es un servicio de geocodificación que forma parte de OpenStreetMap, permite convertir una dirección textual en coordenadas geográficas (lat, lon)
-Obtiene la predicción meteorológica (temperatura y precipitación) con la API de Open-Meteo.
-Usa el modelo generado anteriormente para predecir disponibilidad de bicis.
-Muestra al usuario las estaciones ordenadas por disponibilidad prevista.
Hemos utilizado el LLM llama-3.3-70b-versatile, que genera las preguntas y gestiona el flujo de conversación de forma contextual e inteligente.
Para la interfaz grafica hemos usado gradio.
Enlace: https://huggingface.co/spaces/adriansanz/bicing_agent



https://github.com/user-attachments/assets/a6104a35-7c8c-43b9-b3ac-99548ba3cad9

