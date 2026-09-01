# Contexto De Procesamiento De Plataforma

Este documento resume el servicio de postprocesamiento ubicado en
`postprocesamiento/`. Cubre el flujo actual de producción usado por
`process_input`, la API Flask, el modelo de trama espectral, el detector con
piso de ruido por escalones, el cruce con licencias, los reportes de
cumplimiento, el enriquecimiento RNI y la pila histórica de análisis espectral
que aún permanece en el código.

## Mapa De Fuentes

- `postprocesamiento/server_flask.py`: servicio Flask, parseo de solicitudes,
  ejecución por lotes, valores por defecto desde entorno, registros y rutas HTTP.
- `postprocesamiento/main.py`: envoltorio CLI alrededor de
  `src.processor.process_input`.
- `postprocesamiento/step1_test_payload.py`: prueba rápida para convertir un JSON
  de medición en `SpectrumFrame`.
- `postprocesamiento/step2_test_router.py`: router CLI de prueba más antiguo,
  similar a `main.py`, pero sin los argumentos de tolerancia más recientes.
- `postprocesamiento/src/processor.py`: capa principal de orquestación. Normaliza
  la entrada, aplica corrección opcional de ganancia, ejecuta el detector actual,
  enruta el modo de salida, cruza licencias, evalúa cumplimiento y añade campos
  RNI.
- `postprocesamiento/src/payload_parser.py`: parser tolerante desde JSON de trama
  hacia `SpectrumFrame`.
- `postprocesamiento/src/spectrum_frame.py`: contenedor en memoria para el
  espectro, con amplitudes, eje de frecuencia, ancho de bin, normalización y
  conversión de dBm a W.
- `postprocesamiento/src/power_utils.py`: ayuda robusta para integración de
  potencia de canal y compatibilidad con integración trapezoidal.
- `postprocesamiento/src/calibration_io.py`: lector robusto de CSV de licencias,
  normalización, conversión de unidades, índices cacheados por DANE/frecuencia y
  selección de la licencia que mejor coincide.
- `postprocesamiento/src/simple_detector.py`: detector configurable por regiones
  con presets. Está disponible mediante `get_detector_run`, pero no es el
  detector usado por la ruta actual de `process_input`.
- `postprocesamiento/src/spectral_analysis.py`: rutinas históricas y
  especializadas de análisis espectral: selección de umbral, detección de picos
  de banda angosta, heurísticas UHF/TDT para Colombia, OBW, ancho de banda a
  x dB, potencia de canal, SNR, MER y BER.
- `postprocesamiento/src/utils/signal_processing.py`: suavizado
  Savitzky-Golay, estimación de tendencia local y detección de mínimos locales.
- `postprocesamiento/src/utils/noise_floor.py`: estimación de piso de ruido a
  partir de valores PSD usando una lógica tipo histograma.
- `postprocesamiento/src/utils/channel_detection.py`: extracción de regiones
  contiguas, unión, filtrado, detección por umbral escalar y detección por
  umbral variable.
- `postprocesamiento/src/utils/region_analysis.py`: expansión adaptativa de
  regiones, construcción de piso de ruido local por escalones y separación final
  de regiones anchas por valles internos.
- `postprocesamiento/src/utils/io_visualization.py`: lector de JSON PSD y ayuda
  de visualización con Matplotlib para inspección fuera de línea.
- `postprocesamiento/Dockerfile`: imagen de contenedor para el servicio
  Flask/Gunicorn.
- `postprocesamiento/requirements.txt`: Flask, Gunicorn, NumPy, Pandas, SciPy y
  Matplotlib.
- `postprocesamiento/consolidado_bbdd_asignación.csv`: base de datos de
  licencias por defecto que se copia dentro de la imagen Docker.

## Puntos De Entrada En Ejecución

El endpoint principal del servicio es `POST /analyze` en `server_flask.py`.

Formas aceptadas de solicitud:

- Solicitud con envoltorio:

```json
{
  "frame": { "Pxx": [], "start_freq_hz": 0, "end_freq_hz": 0 },
  "cumplimiento": 1,
  "dane": "11001",
  "danes": ["11001", "17001"],
  "picos": [92.86, 95.9],
  "umbral_db": 3,
  "delta_fc_khz": 100,
  "delta_bw_khz": 10
}
```

- Solicitud con trama cruda: todo el cuerpo se interpreta como `frame` y los
  metadatos se leen desde los parámetros de consulta.
- Solicitud con `json_path`: se acepta únicamente cuando `ANE_ALLOW_JSON_PATH` o
  `--allow-json-path` lo habilita. Por seguridad está desactivado por defecto en
  producción.

Otras rutas:

- `GET /health`: devuelve `{"ok": true}`.
- `POST /analyze_batch`: procesa muchos envoltorios de trama con un
  `ThreadPoolExecutor` y conserva el orden de los resultados.

Valores por defecto del servidor:

- `ANE_LIC_CSV`: CSV de licencias por defecto.
- `ANE_CORR_CSV`: CSV de corrección de ganancia por defecto.
- `ANE_ALLOW_JSON_PATH`: permite cargar rutas del servidor sólo cuando tiene un
  valor verdadero.
- `ANE_VERBOSE_LOGS`: controla los registros del servicio Flask.
- `ANE_VERBOSE_PROCESSOR`: controla los registros del procesador y por defecto
  está habilitado.

La imagen Docker expone el puerto `8000`, revisa `/health` y ejecuta:

```text
gunicorn --workers 4 --threads 2 --worker-class gthread --bind 0.0.0.0:8000 --timeout 3600 server_flask:app
```

## Modelo De Entrada

`payload_parser.frame_from_payload` acepta un diccionario con:

- Alias para PSD/amplitudes: `Pxx`, `pxx`, `PSD`, `psd`, `amplitudes_dbm`,
  `amplitudes`.
- Alias para frecuencia inicial: `start_freq_hz`, `f_start_hz`, `start_hz`,
  `f_start`, `start_freq`.
- Alias para frecuencia final: `end_freq_hz`, `f_stop_hz`, `stop_hz`, `f_stop`,
  `end_freq`, `stop_freq`.

El parser exige al menos 4 puntos PSD. Luego `SpectrumFrame` construye un eje de
frecuencia lineal desde inicio hasta fin cuando no se entrega un eje explícito:

```text
freq_hz = linspace(f_start_hz, f_stop_hz, len(Pxx))
bin_hz = (freq_hz[-1] - freq_hz[0]) / (N - 1)
```

El código suele tratar las amplitudes como dBm o dBm/Hz según la métrica:

- La salida del detector actual usa valores tipo pico de región sobre la traza
  suavizada.
- Las rutinas históricas de potencia integran como si las amplitudes fueran PSD
  en dBm/Hz.
- El enriquecimiento RNI interpreta `power_dbm` o `p_medida_dBm` como potencia
  total para una conversión idealizada de intensidad de campo.

Esta diferencia importa al comparar valores numéricos de potencia entre la ruta
actual y las rutas históricas.

## Enrutamiento De Modos

`processor.route_mode` asigna la solicitud a uno de tres modos:

- `peaks`: se usa cuando `picos` no está vacío. Los picos solicitados se revisan
  contra las emisiones detectadas.
- `compliance`: se usa cuando no hay `picos` y `cumplimiento == 1`. El cruce con
  CSV de licencias es obligatorio.
- `all_emissions`: se usa cuando no hay `picos` y `cumplimiento == 0`. Detecta y
  reporta emisiones sin comparación de licencias.

Tanto la CLI como Flask normalizan `picos` desde lista, cadena JSON tipo lista o
cadena CSV. `pico_to_hz` interpreta valores con `abs(p) < 1e6` como MHz y los
demás como Hz.

Los filtros DANE se normalizan desde `dane`, `danes` o `municipio` numérico. Una
solicitud multi-DANE tiene prioridad sobre un único `dane`.

## Flujo Actual De Procesamiento Extremo A Extremo

La ruta actual de producción es `src.processor.process_input`.

1. Normaliza la entrada con `unpack_input`.
2. Selecciona el modo con `route_mode`.
3. Normaliza tolerancias de frecuencia y ancho de banda:
   - `delta_fc_khz` por defecto es `100`, que internamente se convierte a
     `0.1 MHz`.
   - `delta_bw_khz` por defecto es `10`.
4. Construye metadatos base de salida: modo, `cumplimiento`, `picos`, timestamp
   y MAC opcionales, y si la corrección está habilitada.
5. Convierte el JSON de trama a `SpectrumFrame`.
6. Aplica corrección opcional de ganancia con `apply_gain_correction`.
7. Construye argumentos de detector con `_build_processing_args`.
8. Ejecuta `_run_new_detector_on_frame`.
9. Define `umbral` en la salida como la mediana del vector final de umbral por
   escalones.
10. Formatea la respuesta según el modo.
11. Añade campos RNI con `_enrich_output_with_rni`.

Detalle importante de la ruta actual: `process_input` ya no usa
`detect_peak_bins`, `measure_emission_parameters` ni el flujo especializado TDT
histórico para la respuesta normal del endpoint. Esas rutinas siguen en el
repositorio y en `_process_input_reference_legacy`, pero el endpoint activo usa
el detector con piso de ruido por escalones descrito abajo.

## Corrección De Ganancia

`apply_gain_correction` lee un CSV de corrección e interpola los errores sobre el
eje de frecuencia de la trama.

Columnas esperadas:

```text
Frecuencia (MHz)
Error (dB)
```

Procesamiento:

```text
freq_corr_axis_hz = CSV["Frecuencia (MHz)"] * 1e6
gain_corr_values_db = CSV["Error (dB)"]
correction_interpolated = interp(frame.freq_hz, freq_corr_axis_hz, gain_corr_values_db)
corrected_amplitudes = frame.amplitudes_dbm + correction_interpolated
```

Los arreglos de corrección se cachean con `lru_cache(maxsize=8)` y se invalidan
por `mtime` del archivo.

## Pipeline Del Detector Actual

El detector actual está implementado en `_run_new_detector_on_frame` dentro de
`processor.py` y usa ayudas de `src/utils`.

Parámetros por defecto de `_build_processing_args`:

- Ancho de bin para histograma de piso de ruido: `nf_delta_db = 0.5`.
- Percentil inicial de ruido: `nf_percentile = 1.0`.
- Mínimo de puntos tras filtrar ruido: `nf_min_points = 4`.
- Margen de detección sobre piso de ruido: `delta_above_nf_db = 3.0` por
  defecto, o `umbral_db` cuando se entrega.
- Separación máxima para unir regiones: `15 kHz`.
- Ancho mínimo de región: `15 kHz`.
- Percentil de refinamiento local: `60`.
- Factor de expansión local de respaldo: `1.15`.
- Límite de razón de altura para refinamiento: `0.55`.
- Ventana de tendencia adaptativa: `9` bins.
- Ancho mínimo para separación final: `1 MHz`.
- Razones de valle para separación final: lateral `0.01`, centro `0.15`.
- Proporciones por sección para separación final: izquierda `15%`, centro `60%`,
  derecha `15%`.
- Caída mínima en hombros del valle: `1.5 dB`.
- Distancia mínima entre valles: `100 kHz`.
- Margen mínimo al borde: `50 kHz`.

Etapas del detector:

1. Construye arreglos desde `SpectrumFrame`.
2. Suaviza `Pxx` con Savitzky-Golay mediante `smooth_psd`.
   - El tamaño de ventana depende de la longitud de la trama:
     - `>4096`: 20
     - `1024..4096`: 16
     - `>=512`: 10
     - en otro caso: 7
3. Estima el piso de ruido global con `detect_noise_floor_from_psd`.
4. Detecta regiones iniciales con `detect_channels_from_psd` usando un umbral
   escalar:

```text
global_threshold = global_noise_floor + delta_above_nf_db
mask = Pxx_smooth >= global_threshold
```

5. Construye un vector de piso de ruido con `build_step_noise_floor`.
6. Detecta regiones finales con `detect_channels_from_variable_threshold`.
7. Divide regiones anchas por valles internos usando
   `split_wide_regions_by_internal_valleys`.
8. Emite una fila por región final con:
   - `nearest_bin` / `peak_idx`
   - `measure_L`, `measure_R`
   - `fc_hz`, `fc_mhz`
   - `bw_hz`, `bw_khz`
   - `power_dbm`

En el detector actual, `power_dbm` es `_region_power_dbm`, es decir, el valor
máximo de la PSD suavizada dentro de la región detectada. No es la potencia
integrada de canal usada por la ruta histórica `channel_power_dbm_uniform_bins`.

## Lógica Del Piso De Ruido Por Escalones

`build_step_noise_floor` empieza con un vector plano en el piso de ruido global y
luego aplica pisos de ruido locales alrededor de regiones candidatas cuando el
refinamiento es confiable.

Para cada región inicial:

1. `expand_region_adaptively` escanea los lados izquierdo y derecho de la región.
2. `find_adaptive_expansion_bins` usa tendencias lineales locales cortas y
   largas para detener la expansión cuando detecta una tendencia ascendente
   confirmada lejos del piso local.
3. Si la expansión adaptativa falla, el código cae a una expansión simétrica
   usando `refine_expansion_factor`.
4. El candidato de piso de ruido local se estima dentro del intervalo expandido.
5. El candidato de umbral local es:

```text
local_threshold = local_noise_floor + delta_above_nf_db
```

6. El refinamiento se acepta sólo cuando el umbral queda suficientemente bajo
   dentro de la altura de la región original:

```text
local_threshold - segment_min < refine_height_ratio_limit * segment_height
```

7. Los pisos locales aceptados se aplican sobre el intervalo expandido.
8. Los solapes usan por defecto la política `"max"`, que conserva el piso de
   ruido más alto en intervalos superpuestos.

Cuando `debug=True`, `process_input` devuelve:

- `vector_piso_ruido`: vector final de piso de ruido por escalones.
- `vector_umbral_dinamico`: vector final de umbral dinámico.

## Separación Final De Regiones

`split_wide_regions_by_internal_valleys` inspecciona regiones anchas detectadas
y las divide cuando los valles internos son creíbles.

Para una región:

1. Ignora regiones más estrechas que `split_min_bw_hz`.
2. Encuentra mínimos locales dentro de la región suavizada.
3. Rechaza candidatos de valle cercanos a los bordes.
4. Evalúa cada valle por:
   - zona de posición del valle: izquierda, centro o derecha;
   - razón adaptativa de altura para esa zona;
   - caídas en ambos hombros;
   - separación mínima frente a otros valles.
5. Deduplica valles cercanos conservando el más profundo.
6. Sólo divide si ambos lados resultantes cumplen el ancho mínimo.

El objetivo es evitar que una región amplia y congestionada se reporte como una
sola emisión cuando la PSD contiene separaciones internas significativas.

## Modos De Salida Actuales

### all_emissions

Devuelve todas las regiones detectadas:

```text
nearest_bin
status = "emision"
fc_hz, fc_mhz
bw_hz, bw_khz
power_dbm
rni, rni_v_m, ocupacion_pct
```

El CSV de licencias se ignora intencionalmente en este modo cuando no se entregan
`picos`, porque la solicitud se interpreta como detección/medición y no como
cumplimiento.

### peaks

Para cada pico solicitado:

1. Convierte el valor solicitado a Hz.
2. Elige la fila detectada más cercana por `fc_hz`.
3. Usa un margen de coincidencia:

```text
margin_hz = min(0.30 * abs(requested_hz), 100000)
```

4. Si no hay una fila detectada dentro del margen, reporta `status = "ruido"` y
   `reason = "no_hay_emision_cercana"`.
5. Si la amplitud del pico detectado está por debajo del umbral final por
   escalones en su bin, reporta `status = "ruido"` y `reason = "por_umbral"`.
6. En otro caso reporta `status = "emision"` con frecuencia medida, ancho de
   banda y potencia.
7. Si se suministran licencias, añade una comparación de licencia o
   `comparaciones_por_dane`.

### compliance

Requiere un CSV de licencias. Cuando se usa un CSV de licencias, se exige filtro
por DANE o municipio heredado para evitar coincidencias falsas entre municipios
no relacionados.

Procesamiento:

1. Parte de las filas detectadas.
2. Las convierte en emisiones base:
   - FC medida en MHz;
   - BW medido en kHz;
   - potencia medida en dBm;
   - límites internos de bins.
3. Aplica un filtro previo de potencia relativa:

```text
COMPLIANCE_MIN_RELATIVE_POWER_RATIO = 0.01
threshold_db = max_power_dbm + 10 * log10(0.01) = max_power_dbm - 20 dB
```

Los candidatos más de 20 dB por debajo del candidato más fuerte se ignoran antes
del cruce con licencias.

4. Cruza cada emisión restante contra la base de licencias.
5. Evalúa:
   - `Cumple_FC`: la frecuencia central medida debe estar dentro de
     `delta_fc_khz`.
   - `Cumple_BW`: si el BW medido es menor que el nominal, cumple; si es mayor,
     sólo falla cuando el exceso supera `delta_bw_khz`.
   - `Cumple_P`: la potencia medida debe ser menor o igual que la potencia
     nominal.
   - `Licencia`: `"SI"` cuando existe coincidencia por frecuencia,
     independientemente del cumplimiento de BW o potencia.

Para solicitudes multi-DANE, la salida incluye:

- `results_by_dane`: tabla independiente por DANE.
- `results`: alias de compatibilidad para el primer DANE.
- `num_emissions`: número de emisiones medidas antes de expandir por DANE.

## Cruce Con CSV De Licencias

`calibration_io.comparar_parametros` es el comparador de licencias.

Columnas de licencia requeridas:

```text
frecuencia
ancho_de_banda
unidad_ancho_de_banda
potencia
unidad_potencia
```

Y al menos una de:

```text
codigo_dane
municipio
```

La lectura del CSV es robusta frente a:

- separadores de punto y coma o coma;
- codificación UTF-8 o Latin-1;
- BOM en nombres de columnas;
- formatos con coma decimal como `88,9`;
- separadores de miles como `1.234,56`;
- valores DANE representados como `11001.0`;
- unidades de ancho de banda en Hz, kHz, MHz y GHz;
- unidades de potencia en dBm, dBW, W, kW, mW, uW y variantes mayores.

Los datos preparados de licencias se cachean por ruta absoluta y `mtime`. Cuando
hay índice por DANE disponible, el comparador construye:

- un índice agrupado por prefijo DANE normalizado de 5 dígitos;
- arreglos de frecuencia ordenados por DANE;
- arreglos precalculados de ancho de banda nominal y potencia nominal.

Coincidencia rápida para un DANE de 5 dígitos:

1. Búsqueda binaria de filas candidatas dentro de
   `f_medida +/- tolerancia_freq`.
2. Puntaje de candidatos:

```text
score = abs(delta_frequency_mhz) + 1e-3 * abs(delta_bandwidth_khz)
```

3. Selección del menor puntaje, con desempate determinista por orden de fila de
   origen.

La ruta de respaldo escanea y ordena un `DataFrame` filtrado con la misma idea de
puntaje.

Campos devueltos por la comparación:

```text
Licencia
fc_nominal_MHz
bw_nominal_kHz
p_nominal_dBm
delta_f_MHz
delta_bw_kHz
delta_p_dB
```

## Enriquecimiento RNI Y Ocupación

`_enrich_output_with_rni` modifica las filas de resultado después del
procesamiento específico de cada modo.

Lee potencia desde:

- `p_medida_dBm` en filas de cumplimiento;
- en otro caso, `power_dbm`.

Lee frecuencia desde:

- `fc_hz`;
- en otro caso, `fc_medida_MHz` o `fc_mhz`.

La conversión de intensidad de campo asume un modelo idealizado de espacio libre
basado en la lógica de `dbm_EMC.pdf`:

```text
eta0 = 377 ohm
ganancia de antena = 6 dBi
lambda = c / f
P[W] = 10 ** ((P_dBm - 30) / 10)
E[V/m] = sqrt(eta0 * P[W] * 4*pi / (G * lambda^2))
E[dBµV/m] = 20*log10(E[V/m]) + 120
```

Campos de salida:

- `rni`: campo eléctrico estimado en dBµV/m.
- `rni_v_m`: campo eléctrico estimado en V/m.
- `ocupacion_pct`: porcentaje relativo a `162.7 dBµV/m`.

Es una estimación normalizada; no sustituye un modelo calibrado de EIRP ni una
medición de sitio.

## Pila Histórica De Análisis Espectral

El código conserva una pila histórica y especializada de detección y medición.
Es contexto importante para mantenimiento, pero no es la ruta normal actual de
Flask salvo que el código llame explícitamente a `_process_input_reference_legacy`,
`get_detector_run` o funciones relacionadas.

Funciones históricas principales:

- `detect_peak_bins`: combina detección Colombia broadband/TDT con detección de
  picos residuales de banda angosta.
- `analyze_colombia_broadband_segments`: detecta emisiones anchas tipo UHF/TDT
  en el rango colombiano de 470 a 698 MHz.
- `measure_emission_parameters`: reporta FC, ancho a x dB, OBW, potencia de
  canal y SNR.
- `estimate_ber_in_band_mqam`: estima MER/BER para canales TDT plausibles.
- `channel_power_dbm_uniform_bins`: integra bins PSD en unidades lineales.
- `simple_detector.detect_emissions`: detector alternativo configurable con
  presets `general`, `fm_dense`, `high_res` y `uhf_tv`.

### Heurísticas TDT/Banda Ancha

La ruta TDT trata 470 a 698 MHz como la banda UHF/DVB-T2 de Colombia y considera
candidatas de banda ancha las capturas con al menos 4 MHz de span y al menos
1 MHz de solape con esa banda.

La lógica especial incluye:

- estimación robusta de ruido por percentiles bajos y bordes;
- candidatos de umbral por Otsu, valle de histograma, percentil y bordes;
- puntuación de umbrales según ocupación esperada de banda ancha, ancho,
  segmentación y concentración de energía;
- centros nominales de raster TDT de 6 MHz desde 473 MHz hasta 695 MHz;
- validación de canales TDT completos y parciales;
- protección contra falsos positivos de banda angosta cerca de bordes de canales
  anchos aceptados;
- límites OBW 99% dentro de segmentos aceptados.

Esta ruta es más específica del dominio que el detector genérico actual por
escalones.

### Métricas Históricas De Medición

La medición histórica asume que los valores PSD son compatibles con integración:

- `measure_bandwidth_xdb`: encuentra el ancho en `peak - x_db` usando suavizado
  ligero y cruces de umbral interpolados.
- `measure_obw`: integra `W/Hz` lineales sobre frecuencia y encuentra el ancho de
  banda ocupado que contiene un porcentaje objetivo, normalmente 99%.
- `measure_channel_power`: integra una ventana de canal en unidades lineales y
  devuelve dBm totales.
- `compute_snr`: resta el ruido mediano al nivel del bin pico.
- `estimate_ber_in_band_mqam`: para TDT plausible, estima relación
  portadora-ruido, MER y BER M-QAM desde estadísticas derivadas de la PSD.

El detector actual por escalones no usa directamente estas métricas integradas.

## Pila Del Detector Simple

`simple_detector.py` implementa otro detector configurable:

1. Suaviza la traza.
2. Estima ruido global por percentil bajo.
3. Construye un umbral escalar.
4. Estima una línea base local por percentil móvil.
5. Construye máscaras residuales de semilla y crecimiento.
6. Rellena huecos pequeños.
7. Forma componentes sembrados.
8. Filtra por ancho mínimo, razón de soporte y prominencia de pico.
9. Opcionalmente rescata rasgos anchos lentos.

Presets:

- `general`: detector de propósito amplio.
- `fm_dense`: manejo más laxo de huecos y prominencia para regiones densas tipo
  FM.
- `high_res`: ancho mínimo y ventana local más pequeños.
- `uhf_tv`: ancho mínimo más grande, ventanas locales mayores y ajustes de
  rescate lento para rasgos UHF anchos.

Este detector se puede invocar con `get_detector_run(detector_name="simple")`,
pero el `process_input` actual usa `_run_new_detector_on_frame`.

## Notas Operativas

- El detector activo del endpoint es genérico y basado en umbral por escalones.
  Actualmente no aplica la ruta especializada Colombia TDT de `spectral_analysis`.
- `umbral_db` es un desplazamiento en dB sobre el piso de ruido detectado. En la
  ruta actual, el campo de respuesta `umbral` es la mediana del vector final de
  umbral dinámico, no necesariamente un único umbral usado en todos los bins.
- `debug=True` puede devolver los vectores completos de piso de ruido y umbral.
  Esto puede ser grande para tramas de alta resolución.
- En modo `all_emissions`, el cruce de licencias se desactiva intencionalmente
  cuando no se solicitan picos.
- En modo `compliance`, se rechaza el cruce sin DANE o municipio cuando se
  entrega un CSV de licencias.
- El `power_dbm` actual del detector por escalones es un nivel pico de región
  tomado del espectro suavizado. El RNI derivado debe tratarse como aproximado
  salvo que se restaure una semántica de potencia calibrada o se sustituya por
  potencia integrada.
- La corrección de ganancia y la preparación del CSV de licencias usan cachés
  basados en `mtime`. Actualizar un CSV en disco invalida el caché sólo cuando
  cambia su `mtime`.
- El modo por lotes de Flask usa hilos. Parte del trabajo NumPy/SciPy puede
  liberar el GIL, pero el parseo Pandas y los bucles Python pueden seguir siendo
  cuellos de botella.
- La imagen Docker incrusta `consolidado_bbdd_asignación.csv` como base de
  licencias por defecto en `/opt/ane-realtime/data/licencias.csv`.

## Guía Práctica De Mantenimiento

Al cambiar comportamiento de detección, primero conviene decidir qué ruta se va
a modificar:

- Comportamiento actual del servicio: editar `_run_new_detector_on_frame`,
  `utils/*` y las ramas actuales de `process_input`.
- Comportamiento histórico/TDT: editar `spectral_analysis.py`,
  `_process_input_reference_legacy` o `get_detector_run`.
- Cruce con licencias: editar `calibration_io.py` y `_match_licencia`.
- Comportamiento de entrada HTTP: editar `server_flask.py`.

Para trabajos de cumplimiento, mantener explícitas las unidades:

- la frecuencia medida se reporta en MHz para comparación de licencias;
- el ancho de banda medido se reporta en kHz para comparación de licencias;
- el ancho de banda nominal se normaliza a kHz;
- la potencia nominal se normaliza a dBm;
- la tolerancia de frecuencia se almacena internamente en MHz después de
  recibirse en kHz.

Para reportes sensibles a potencia, verificar qué métrica se pretende usar:

- nivel pico del detector actual;
- potencia integrada en ancho a x dB;
- potencia integrada en OBW;
- nivel promedio broadband/TDT;
- intensidad de campo calibrada externamente.

Estas métricas no son intercambiables, y el código actual contiene más de una
ruta semántica para `power_dbm`.
