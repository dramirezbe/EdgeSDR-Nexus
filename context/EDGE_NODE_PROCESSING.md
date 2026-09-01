# Contexto De Procesamiento RF

Este documento resume la cadena DSP usada por el motor RF, la arquitectura de
ring buffers, la lógica de buffer con doble consumidor, la ruta de corrección del
pico DC en `functions.py` y el contexto operativo práctico de HackRF.

## Mapa De Fuentes

- `rf/rf.c`: ciclo de vida del motor RF, callback de HackRF, manejo de comandos,
  calibración, bucle principal de PSD e hilo de audio.
- `rf/libs/sdr_HAL.c`: sintonización de HackRF, ganancia, tasa de muestreo,
  amplificador y corrección PPM.
- `rf/libs/ring_buffer.c`: ring buffers FIFO con poco bloqueo usados entre los
  callbacks de libhackrf y los hilos de procesamiento.
- `rf/libs/psd.c`: carga IQ, compensación de desbalance IQ, PSD Welch, PSD PFB,
  dimensionamiento FFT desde RBW, ventanas y conversión a dBm.
- `rf/libs/chan_filter.c`: filtro opcional de canal por frecuencia absoluta en
  dominio FFT.
- `rf/libs/iq_iir_filter.c`: bloqueador DC IQ en streaming y cadena de biquads
  Butterworth para prefiltrado de demodulación de audio.
- `rf/libs/fm_radio.c`: demodulador FM por discriminador de fase y
  acondicionamiento de audio.
- `rf/libs/am_radio_local.c`: demodulador AM por envolvente, decimación CIC,
  normalización de portadora, AGC y acondicionamiento de audio.
- `functions.py`: envoltorio de adquisición y eliminación adaptativa
  post-adquisición del pico DC para arreglos PSD devueltos.
- `utils/dc_spike_removal.py` y `utils/dc_spike_detection.py`: reparación
  adaptativa de bins centrados usada por `functions.py`.

## Flujo RF Extremo A Extremo

1. Un comando JSON se parsea en `parse_config_rf`.
2. `find_params_psd` mapea los ajustes RF y PSD solicitados hacia:
   - `SDR_cfg_t`: tasa de muestreo de HackRF, frecuencia central, ganancias,
     amplificador y PPM.
   - `PsdConfig_t`: longitud FFT, solape, tasa de muestreo y ventana.
   - `RB_cfg_t`: número de bytes IQ crudos necesarios para un bloque de
     procesamiento.
3. `hackrf_apply_cfg` aplica los ajustes de hardware y sintoniza con corrección
   PPM.
4. `hackrf_start_rx` inicia el streaming de libhackrf. Su callback escribe bytes
   IQ crudos en los ring buffers.
5. El hilo principal espera hasta que haya suficientes bytes disponibles en
   `rb`, copia un bloque lineal, convierte IQ entrelazado con signo de 8 bits en
   muestras complejas y luego ejecuta:
   - compensación IQ;
   - filtro opcional de canal en dominio FFT;
   - PSD Welch o PFB;
   - publicación ZMQ de `Pxx`, límites de frecuencia y métricas AM/FM.
6. Cuando el audio AM o FM está habilitado, el callback también clona los mismos
   bytes IQ entrantes en `audio_rb`. El hilo de audio drena este buffer de forma
   independiente, demodula, empaqueta PCM en tramas Opus y envía audio por TCP.

## Formato IQ Crudo

HackRF entrega bytes IQ entrelazados con signo de 8 bits:

```text
I0, Q0, I1, Q1, ...
```

La ruta PSD convierte cada par en:

```text
x[n] = (double)I[n] + j * (double)Q[n]
```

La ruta de audio normaliza cada byte por `128.0` antes de demodular:

```text
x[n] = I[n] / 128.0 + j * Q[n] / 128.0
```

Los valores PSD reportados como dBm son relativos a la escala digital del ADC.
No son potencia RF absoluta salvo que toda la cadena analógica haya sido
calibrada externamente.

## Arquitectura De Ring Buffers

El motor RF usa dos ring buffers independientes:

- `rb`: buffer primario de IQ crudo para adquisición PSD y calibración.
- `audio_rb`: buffer de IQ crudo para el hilo de demodulación de audio.

La implementación está en `rf/libs/ring_buffer.c`.

Propiedades principales:

- El buffer se direcciona por bytes, no por muestras.
- `head` y `tail` son contadores `atomic_size_t` que aumentan de forma monótona.
- Los desplazamientos físicos se calculan con módulo: `head % size` y
  `tail % size`.
- Las copias con wraparound se dividen en dos operaciones `memcpy` contiguas.
- `rb_write` escribe como máximo el espacio libre disponible en ese momento.
- `rb_read` lee como máximo los bytes disponibles en ese momento.
- `rb_available` es `head - tail`.
- `rb_reset` pone en cero la memoria de respaldo y reinicia ambos contadores.
- `rb_free` pone en cero la memoria de respaldo antes de liberarla.

En la práctica, cada buffer sigue un diseño de productor único y consumidor
único. El callback es el productor. El bucle principal de PSD consume `rb`; el
hilo de audio consume `audio_rb`.

Las copias de datos no están protegidas por mutexes de pthread. Las variables
atómicas dan visibilidad productor/consumidor. Los mutexes y variables de
condición sólo se usan como señales de despertar para que los hilos en espera no
hagan espera activa.

Detalle operativo importante: si un ring buffer está lleno, `rb_write` trunca la
escritura al espacio disponible. No bloquea, no sobrescribe muestras antiguas y
no mantiene un contador de overruns. Esto mantiene corto el callback de HackRF,
pero significa que paradas sostenidas del procesamiento pueden descartar nuevos
bytes IQ silenciosamente.

Tamaños actuales:

- `rb` está fijo en `100 * 1024 * 1024` bytes.
- `audio_rb` es `AUDIO_CHUNK_SAMPLES * 2 * 8`, actualmente 262144 bytes.
- Cada bloque de procesamiento de audio es `AUDIO_CHUNK_SAMPLES * 2` bytes,
  actualmente 32768 bytes, o 16384 muestras IQ.
- El tamaño de bloque PSD lo calcula `find_params_psd` como aproximadamente
  `sample_rate / 4` bytes, pero nunca menor que un segmento FFT de pares IQ.

## Lógica De Buffer Con Doble Consumidor

El motor no usa un ring buffer con dos lectores. En su lugar, duplica el flujo
del productor en dos buffers independientes:

```c
rb_write(&rb, transfer->buffer, transfer->valid_length);
if (atomic_load(&audio_enabled)) {
    rb_write(&audio_rb, transfer->buffer, transfer->valid_length);
    pthread_cond_signal(&audio_rb_cond);
}
pthread_cond_signal(&rb_cond);
```

Esto importa porque una FIFO única tiene un solo `tail`. Si PSD y audio
compartieran ese `tail`, el consumidor más rápido le quitaría datos al más
lento. Al clonar los bytes en el productor, cada consumidor tiene su propio
`tail` y su propio ritmo:

- PSD puede esperar bloques grandes con calidad de análisis.
- Audio puede drenar bloques más pequeños con menor latencia.
- Audio se puede deshabilitar en `PSD_MODE` sin perturbar la adquisición PSD.
- En una resintonización o al habilitar audio, `audio_rb` se reinicia para que el
  demodulador no reproduzca IQ viejo de la frecuencia central o tasa de muestreo
  anterior.

El costo es duplicar el ancho de banda de memoria cuando el audio está
habilitado. El callback sigue siendo intencionalmente simple: escribir bytes,
señalar hilos en espera y retornar.

## Selección De Parámetros PSD

`find_params_psd` deriva la longitud FFT a partir del RBW solicitado:

```text
nperseg = 2 ^ ceil(log2(ENBW(window) * Fs / RBW))
```

Luego:

- `nperseg` se limita a un mínimo de 256.
- `noverlap = nperseg * requested_overlap`, con guarda superior de
  `nperseg - 1`.
- Las ventanas soportadas incluyen Hamming, Hann, Rectangular, Blackman, Flat
  Top, Kaiser, Tukey y Bartlett.
- Los factores ENBW se aproximan para dimensionamiento. Por ejemplo, Hamming es
  1.363 y Hann es 1.500.

La PSD resultante es bilateral y queda centrada alrededor de DC después de
`fftshift`, por lo que el eje de frecuencia va desde `-Fs/2` hasta justo antes de
`+Fs/2`. Los límites absolutos de frecuencia publicados usan la frecuencia
central nominal solicitada, no la frecuencia internamente sintonizada con
corrección PPM.

## Compensación IQ

`iq_compensation` se aplica a bloques PSD y de calibración antes del análisis
espectral. Es una corrección IQ ciega, por bloque y de segundo orden:

1. Elimina el offset DC de I y Q de forma independiente:

```text
I <- I - mean(I)
Q <- Q - mean(Q)
```

2. Igualar la potencia de las ramas escalando Q:

```text
gain = sqrt(sum(I^2) / sum(Q^2))
Q <- gain * Q
```

3. Reducir la no ortogonalidad I/Q decorrelacionando Q respecto a I:

```text
rho = sum(I * Q) / sum(I^2)
Q <- Q - rho * I
```

Esto mejora el comportamiento del pico central y el rechazo de imagen. No
corrige desbalance dependiente de la frecuencia y no reemplaza una calibración
basada en tono si se requiere alto rechazo de imagen.

La ruta de audio no ejecuta esta compensación por bloque. En su lugar usa un
bloqueador DC de un polo en streaming y filtrado IIR, lo cual evita
discontinuidades causadas por restar una media distinta en cada bloque de audio.

## Capas De Corrección DC

Hay varias correcciones relacionadas con DC, cada una resolviendo un problema
distinto.

### Eliminación DC IQ En Dominio Temporal

En `iq_compensation`, la media de I y Q se elimina de un bloque PSD/calibración.
Esto ataca fuga de LO y offset del ADC antes de la FFT.

### Bloqueador DC IQ En Streaming

`iq_iir_filter_apply_inplace` puede aplicar un bloqueador DC de primer orden por
separado a I y Q antes del filtro IQ de audio:

```text
y[n] = x[n] - x[n-1] + r * y[n-1]
```

El radio de polo actual es `r = 0.995`. Esto crea un cero en DC mientras mantiene
estado entre bloques.

### Bloqueadores DC De Audio

Los demoduladores FM y AM también usan bloqueadores DC de audio de un polo con
`r = 0.996`. Estos eliminan offsets lentos después de la demodulación:

- FM: después de la de-énfasis y antes del pasa-bajos de audio.
- AM: después de la normalización de envolvente/portadora y antes del pasa-bajos
  de audio.

### Reparación Del Pico DC Post-PSD En `functions.py`

`AcquireDual.get_corrected_data` llama a `_apply_dc_correction_to_acquisition`,
que repara un pico central residual en el arreglo `Pxx` devuelto. Esto no es una
corrección IQ; es limpieza de visualización/datos sobre una PSD ya calculada.

El pipeline:

1. Convierte `Pxx` a un arreglo NumPy.
2. Estima `noise_std_db` a partir de la longitud FFT.
3. Llama a `DCSpikeRemovalPipeline.remove_dc_spike_adaptive_symmetric`.
4. Detecta el semiancho del pico DC centrado usando comportamiento simétrico de
   pendiente y curvatura alrededor del bin central.
5. Detecta baja ocupación espectral cerca del centro y puede ampliar la ventana
   de reparación.
6. Reconstruye la región eliminada con un ajuste lineal o polinomial local.
7. Devuelve:
   - `Pxx` corregido;
   - `Pxx_raw` original;
   - metadatos `dc_correction`, incluyendo segmento reparado, modo de detección,
     modo de reconstrucción y métricas de bajo contenido.

Usa `Pxx_raw` cuando una señal real se encuentra intencionalmente en el centro
exacto y no debería repararse visualmente.

## PSD Welch

`execute_welch_psd` implementa un periodograma promediado estándar:

- Divide IQ en segmentos solapados.
- Aplica la ventana solicitada.
- Ejecuta una FFT con FFTW.
- Acumula magnitud al cuadrado.
- Normaliza por `Fs * window_power * segment_count * nperseg`.
- Aplica `fftshift` para centrar DC en la PSD.
- Convierte a dBm relativos.
- Genera un eje de frecuencia centrado.

Notas de implementación:

- Los planes FFTW y buffers de trabajo se cachean por hilo.
- OpenMP paraleliza el bucle de segmentos.
- Se usa planificación dinámica para reducir desbalance de carga.
- Los coeficientes de ventana se cachean por hilo y se reconstruyen sólo cuando
  es necesario.

Welch es un buen valor por defecto cuando se busca costo de CPU moderado y
reducción de varianza.

## PSD PFB

`execute_pfb_psd` implementa una estimación por banco de filtros polifase:

- `M = nperseg` canales.
- `T = PFB_TAPS_PER_CHANNEL`, actualmente 8 taps por canal.
- La longitud del FIR prototipo es `L = M * T`.
- La ventana prototipo es Kaiser con `beta = 8.6`.
- Cada bloque pliega `T` ramas polifase en `M` entradas FFT.
- Las magnitudes FFT se promedian, desplazan, convierten a dBm y se asignan al
  mismo eje de frecuencia centrado.

La ruta PFB ofrece mejor aislamiento entre bins y mejor rechazo de lóbulos
laterales que Welch, con mayor costo de CPU y memoria.

## Filtro Opcional De Canal En Dominio FFT

`chan_filter_apply_inplace_abs` filtra un rango de frecuencia absoluta solicitado
antes de la PSD:

1. Valida que `[start_freq_hz, end_freq_hz]` esté dentro del span capturado
   `[Fc - Fs/2, Fc + Fs/2]`.
2. Construye o reutiliza planes FFTW y una máscara de frecuencia.
3. Aplica FFT al bloque IQ.
4. Etapa 1: aplana grandes picos fuera de banda limitando su magnitud relativa a
   la mediana OOB.
5. Etapa 2: aplica una máscara de magnitud tipo coseno elevado:
   - ganancia de pasabanda 1.0;
   - piso OOB de `-15 dB`;
   - ancho de transición de `30%` del ancho solicitado.
6. Aplica FFT inversa y normaliza por `1 / N`.

El filtro registra si la banda solicitada es positiva, negativa o cruza DC
(`POSITIVE`, `NEGATIVE`, `CROSS_DC`). Una banda que cruza DC debe tratarse con
cuidado porque la fuga de LO y la corrección DC pueden interactuar con contenido
real en el centro sintonizado.

## Filtro IIR IQ En Streaming

El hilo de audio puede filtrar IQ antes de la demodulación usando
`iq_iir_filter_apply_inplace`.

Actualmente el filtro se comporta como un filtro pasa-bajos de canal, aunque en
el contexto el enum de configuración esté en `BANDPASS_TYPE`. La frecuencia de
corte es la mitad del ancho de banda configurado:

- Ancho de banda AM en `rf.c`: 20 kHz.
- Ancho de banda FM en `audio_stream_ctx.h`: 200 kHz.
- Orden del filtro: 6 por defecto, forzado a par y limitado a 2..12.

Cada biquad se diseña con ecuaciones pasa-bajos RBJ y se ejecuta en Forma Directa
II Transpuesta. I y Q se filtran de forma independiente con estados separados.

## Demodulación FM

`fm_radio_iq_to_pcm` usa un discriminador de fase:

1. Pre-decima IQ por promediado para mantener el discriminador cerca de
   500 kS/s.
2. Calcula la diferencia de fase:

```text
diff = x[n] * conj(x[n-1])
angle = atan2(imag(diff), real(diff))
```

3. Decima hacia la tasa de muestreo Opus/audio, usualmente 48 kHz, promediando
   incrementos de fase.
4. Estima la desviación FM a partir de la fase instantánea:

```text
fi_hz = abs(angle) * demod_fs / (2 * pi)
```

5. Aplica de-énfasis de 75 us.
6. Aplica bloqueador DC de audio.
7. Aplica pasa-bajos de audio de 12 kHz.
8. Aplica ganancia fija y recorta a PCM con signo de 16 bits.

La métrica de salida `fm_dev.dev_ema_hz` se publica como `excursion_hz` en modo
FM.

## Demodulación AM

`am_radio_local_iq_to_pcm` realiza demodulación por envolvente:

1. Calcula la envolvente:

```text
env = sqrt(I^2 + Q^2)
```

2. Decima con una estructura CIC de segundo orden.
3. Actualiza la profundidad de modulación AM desde la envolvente cruda decimada:

```text
depth = (Amax - Amin) / (Amax + Amin)
```

4. Rastrea la media de portadora/envolvente con una EMA lenta.
5. Normaliza la envolvente hacia audio relativo:

```text
val = (env_decimated - mean) / mean
```

6. Aplica bloqueador DC de audio.
7. Aplica pasa-bajos de audio de 5 kHz.
8. Aplica AGC basado en RMS con ataque rápido y liberación lenta.
9. Aplica ganancia final y recorta a PCM con signo de 16 bits.

La métrica de salida `am_depth.depth_ema` se publica como porcentaje `depth` en
modo AM.

## Contexto HackRF

El código está construido alrededor de streaming de recepción HackRF mediante
libhackrf.

Características relevantes de HackRF One:

- SDR half-duplex: puede recibir o transmitir, pero este motor usa RX.
- El rango de sintonización RF suele tratarse como aproximadamente 1 MHz a 6 GHz.
- Las muestras nativas son I de 8 bits y Q de 8 bits.
- La tasa de muestreo máxima práctica es 20 MS/s en este código y sus fixtures de
  prueba.
- El span instantáneo capturado es aproximadamente `sample_rate_hz`.
- No hay AGC de hardware en este motor. La ganancia debe elegirse
  deliberadamente.
- El amplificador RF es una etapa de ganancia frontal, aproximadamente 14 dB
  cuando está habilitado, y puede saturarse fácilmente cerca de señales fuertes.
- La ganancia LNA se representa en el HAL como 0..40 dB en pasos de 8 dB.
- La ganancia VGA se representa como 0..62 dB en pasos de 2 dB.
- La exactitud de frecuencia depende del error PPM del oscilador, temperatura y
  calentamiento.

Consecuencias operativas:

- `sample_rate_hz` define tanto el span DSP como la presión sobre USB/CPU.
- `center_freq_hz +/- sample_rate_hz / 2` es el rango válido de frecuencia
  absoluta para filtrado de canal y límites PSD publicados.
- Emisores locales fuertes pueden saturar el ADC de 8 bits. Más ganancia no
  siempre es mejor.
- Con muestras de 8 bits, muy poca ganancia entierra señales débiles en ruido de
  cuantización; demasiada ganancia recorta picos y eleva productos de
  intermodulación.

## Guía De Balance De Ganancia

Para capturas HackRF, ajusta las ganancias priorizando margen de saturación:

1. Inicia con el amplificador RF apagado, salvo que se sepa que la banda es débil
   y limpia.
2. Usa valores moderados de LNA/VGA, luego aumenta ganancia observando recortes,
   espectros aplanados, elevación súbita del piso de ruido ancho o espurias que
   crecen más rápido que las señales reales.
3. Prefiere suficiente LNA para superar la figura de ruido del receptor y luego
   usa VGA para ubicar la señal digitalizada cómodamente dentro del rango.
4. Reduce ganancia si el piso PSD sube de forma amplia cuando una señal fuerte
   entra en el span.
5. Mantén estables los ajustes de ganancia durante una adquisición si vas a
   comparar niveles PSD en el tiempo.

Como este motor reporta dBm relativos a partir de muestras digitales, los cambios
de ganancia cambian el nivel reportado salvo que se aplique una tabla de
calibración externa.

## Lógica De Calibración PPM

`calibrate_hackrf` estima el error PPM del oscilador usando una estructura tipo
FM de radiodifusión:

1. Captura aproximadamente 0.5 segundos de IQ, con límites de seguridad entre
   262144 y 10000000 muestras IQ.
2. Ejecuta `iq_compensation`.
3. Ejecuta PSD Welch para encontrar candidatos espectrales fuertes.
4. Para cada candidato, mezcla el offset hacia banda base y lo demodula como FM.
5. Busca un piloto estéreo fuerte de 19 kHz en la PSD de audio demodulado.
6. Elige el mejor candidato, favoreciendo evidencia de piloto estéreo y alta
   potencia RF.
7. Mezcla el candidato a banda base, decima por promediado y ejecuta otra PSD
   Welch.
8. Busca el delta de frecuencia que deja más balanceada la potencia de bandas
   laterales simétricas para offsets de 30 kHz a 90 kHz.
9. Convierte el delta a PPM:

```text
ppm = -(best_delta_hz / best_frequency_hz) * 1e6
```

10. Rechaza valores mayores a 80 PPM y suaviza estimaciones repetidas. Saltos
    grandes respecto a la calibración anterior se tratan como outliers.

El PPM final se almacena en estado compartido persistente cuando no es cero. El
HAL luego resintoniza usando:

```text
corrected_freq = target_freq * (1 + ppm / 1e6)
```

Las etiquetas de frecuencia publicadas permanecen nominales para que los
usuarios vean el rango solicitado, no la sintonización corregida internamente.

## Estrategia Práctica De Balance IQ Y DC

Usa juntos los tres alcances de corrección, no como sustitutos intercambiables:

- Para bloques PSD: ejecuta `iq_compensation` antes de la PSD. Reduce DC estático
  I/Q, diferencia de ganancia entre ramas y desbalance de fase de primer orden.
- Para streaming de audio: conserva los bloqueadores DC de un polo con estado.
  Son más adecuados para demodulación continua que restar la media bloque a
  bloque.
- Para productos PSD devueltos: usa la reparación Python del pico DC sólo como
  limpieza residual del bin central.

Ten cuidado cuando la señal real de interés está exactamente en el centro
sintonizado:

- La eliminación DC IQ en dominio temporal puede suprimir sólo el componente de
  frecuencia cero real, pero aun así puede afectar una portadora centrada
  intencionalmente en DC.
- La reparación post-PSD puede reemplazar bins centrales con una estimación
  ajustada. Conserva e inspecciona `Pxx_raw` cuando el contenido del bin central
  importe.
- Si es posible, sintoniza ligeramente fuera del centro exacto de la señal y
  filtra o re-etiqueta digitalmente el span. Esto separa una portadora real de la
  fuga de LO y hace menos ambigua la corrección DC.

Para lograr rechazo de imagen IQ más fuerte que el ofrecido por la compensación
ciega actual, el siguiente paso sería una calibración basada en tono por región
de frecuencia/tasa de muestreo/ganancia, o una corrección ampliamente lineal que
use tanto `x` como `conj(x)`. El código actual usa intencionalmente un estimador
liviano por bloque, rápido y robusto para adquisición PSD rutinaria.
