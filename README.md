# Capstone-Project


LINK GRADIO: https://huggingface.co/spaces/adriansanz/bicis/blob/main/app.py


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
Hemos obtenido los datos meteorológicos de la API de open-meteo, donde se pueden descargar el historico de datos meteorológicos por latitud, longitud por horas. Hemos realizado un preoprocesamiento de los csv que se generan y posteriormente hacemos el merge a las del dataset de entrenamiento y al de test. En este momento es cuando se necesita la columna year, que finalmente eliminamos. Obteniendo las columnas: station_id | month |	day	| hour |	ctx-4	| ctx-3	| ctx-2	| ctx-1 |	temperature_2m (°C)	| precipitation (mm)

# MODELOS PROBADOS

Primeramente hicimos pruebas con el modelo de regresión lineal, los resultados fueron bastante buenos. 
Despues realizamos pruebas con una red neuronal simple, obteniendo peores resultados.
El siguiente modelo sobre el que realizamos pruebas fue XGRADIENT BOSTING, obteniendo los mejores resultados.
También probamos otros modelos como random forest o LGBMRegressor, dandonos peores resultados.

# AMPLIACIÓN 1: Fiestas de barrio

Para hacer un análisis de cómo la demanda de Bicing cambiaba dependiendo de si había fiestas en el barrio, primero hemos agrupado las estaciones de Bicing (station_id) según el barrio de Barcelona en el que se encuentran. Luego, hemos creado una variable dummy: 1 si había fiestas en el barrio ese día, mes y año, y 0 en caso contrario. Esta información sobre las fiestas se ha tenido que recopilar manualmente, ya que no existe una base de datos a nivel Barcelona. Finalmente, hemos analizado cómo cambiaba la demanda de bicicletas si había fiestas de barrio o no, utilizando una media general, pero también observando si, dentro de los meses en los que había fiestas, la demanda variaba considerablemente. Los resultados para 2023, el año con más normalidad en términos de movilidad y fiestas, sugieren que, en general, las fiestas de barrio no afectan a la demanda de bicicletas. Sin embargo, en algunos barrios sí se observó un cambio significativo, aunque para la mayoría no fue así. Por lo tanto, a pesar de haber analizado esta nueva variable, no se ha añadido a ningún modelo de predicción para los datos de 2024.

# AMPLIACIÓN 2: Agente conversacional


