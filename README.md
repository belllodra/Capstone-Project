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
Hemos obtenido los datos meteorológicos de la web https://meteostat.net/es/place/es/barcelona?s=08181&t=2020-02-01/2025-03-24, donde se pueden descargar. Hemos realizado un preoprocesamiento para obtener las columnas:  tavg  tmin  tmax  prcp  snow  wdir  wspd  wpgt  pres  year  month  day hour y posteriormente hacerles el merge a las del dataset de entrenamiento y al de test. En este momento es cuando se necesita la columna year, que finalmente eliminamos.

# MODELOS PROBADOS

Primeramente hicimos pruebas con el modelo de regresión lineal, los resultados fueron bastante buenos. 
Despues realizamos pruebas con una red neuronal simple, obteniendo peores resultados.
El siguiente modelo sobre el que realizamos pruebas fue XGRADIENT BOSTING, obteniendo los mejores resultados. Nos dectantamos por realizar bastanres pruebas con este.
También probamos otros modelos como random forest o LGBMRegressor, dandonos peores resultados.

