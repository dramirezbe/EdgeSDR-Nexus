# Contexto del Backend — Plataforma regulatory body

Este documento consolida el contexto del backend de la Plataforma regulatory body como
insumo para redactar el capítulo "Plataforma web en la nube" del informe final.
Toda la información se presenta desde una perspectiva metodológica, de
arquitectura y de decisiones de diseño, sin referencias a archivos de código ni
estructura de directorios.

## Propósito del componente

El backend es el centro de coordinación de la plataforma. Su función principal
es conectar a las personas usuarias (a través del frontend), los sensores RF en
campo, la base de datos y los servicios de postprocesamiento. No es simplemente
una capa de persistencia: orquesta adquisiciones, mantiene estado en tiempo real,
gestiona campañas programadas, detecta alertas operativas y coordina la
generación de reportes de cumplimiento normativo.

Las responsabilidades concretas del backend son:

- Recibir solicitudes REST desde el frontend y desde los sensores RF.
- Validar usuarios, sesiones y permisos según el diseño de acceso.
- Administrar sensores, antenas, usuarios y parámetros de configuración.
- Coordinar monitoreos inmediatos y campañas programadas de medición.
- Preparar y entregar órdenes de configuración a los sensores: configurar,
  iniciar, detener.
- Recibir datos de campo desde los sensores: estado, GPS, espectro
  radioeléctrico (FFT/potencias) y audio demodulado AM/FM.
- Guardar información histórica en base de datos.
- Comunicar cambios al frontend en tiempo real mediante WebSocket.
- Detectar alertas operativas (desconexión, recursos, temperatura).
- Coordinar la generación de reportes normativos integrando mediciones,
  ubicación y postprocesamiento.
- Ejecutar mantenimiento automático: marcar sensores offline, cerrar campañas
  vencidas, detener monitoreos expirados.

## Arquitectura

El backend sigue una arquitectura de servidor monolítico bien modularizado,
construido sobre Node.js con TypeScript. Utiliza Express como framework HTTP,
WebSocket nativo para comunicación en tiempo real, y el cliente pg para
conexión con PostgreSQL. La documentación de la API se genera automáticamente
mediante Swagger/OpenAPI.

### Pila tecnológica

- **Entorno de ejecución**: Node.js 18+
- **Lenguaje**: TypeScript (compilado a JavaScript para producción)
- **Framework HTTP**: Express
- **Comunicación en tiempo real**: WebSocket nativo
- **Base de datos**: PostgreSQL 13+ con extensión opcional TimescaleDB
- **Autenticación**: JSON Web Tokens (JWT) + integración con Microsoft Azure AD
- **Documentación API**: Swagger UI / OpenAPI

### Capas lógicas

El backend está organizado en capas lógicas con responsabilidades separadas:

1. **Capa de entrada HTTP**: recibe solicitudes REST del frontend y de los
   sensores. Expone el servidor en el puerto configurado y aplica middleware
   común: CORS, logging, parsing de JSON con límite ampliado (50 MB) para
   permitir tramas espectrales de alta resolución.

2. **Capa de autenticación y autorización**: valida la identidad de la persona
   usuaria mediante dos mecanismos complementarios. Para acceso institucional se
   integra con Azure AD usando el protocolo OIDC y la librería jose. Para
   acceso programático o administrativo se usan tokens JWT firmados. Los
   middleware de autenticación se aplican selectivamente según la ruta y el
   perfil de acceso requerido.

3. **Capa de rutas y controladores**: organiza la lógica de negocio en módulos
   independientes:
   - Autenticación (login institucional y local, validación de sesión).
   - Gestión de sensores y antenas (CRUD, asignación, desasignación).
   - Recepción de datos de campo (estado, GPS, espectro, audio).
   - Control remoto de sensores (configuración, inicio, detención).
   - Campañas de medición (creación, programación, arranque, parada, consulta).
   - Reportes de cumplimiento normativo.
   - Configuración del sistema.

4. **Capa de modelos y acceso a datos**: abstrae las consultas a la base de
   datos mediante funciones tipadas. Utiliza un pool de conexiones pg.Pool
   para gestionar concurrencia (hasta 20 conexiones simultáneas). Las
   operaciones que modifican múltiples tablas se ejecutan dentro de
   transacciones PostgreSQL.

5. **Capa de comunicación en tiempo real**: mantiene conexiones WebSocket
   activas con los clientes frontend. Transmite eventos de estado de sensores,
   actualizaciones GPS, datos de espectro en tiempo real, comandos de
   configuración y comandos de detención. Un segundo canal WebSocket
   independiente gestiona el streaming de audio demodulado.

6. **Capa de mantenimiento automático**: ejecuta tareas programadas cada 30
   segundos para validar el estado de los sensores. Marca como offline aquellos
   que no han reportado en un tiempo definido. Notifica cambios de estado al
   frontend mediante broadcast WebSocket.

### Flujo de datos principal

1. La persona usuaria interactúa con el frontend.
2. El frontend envía solicitudes HTTP al backend.
3. El backend valida autenticación y permisos.
4. Para mediciones: el backend almacena la configuración solicitada y la deja
   disponible para que el sensor la consulte.
5. El sensor consulta periódicamente su configuración activa y campañas
   asignadas mediante endpoints REST.
6. El sensor ejecuta la medición y envía datos al backend (estado, GPS,
   espectro, audio).
7. El backend guarda los datos en PostgreSQL y los transmite al frontend por
   WebSocket.
8. Para reportes: el backend recopila mediciones históricas, consulta datos de
   ubicación normativa, invoca el servicio de postprocesamiento Python y
   devuelve resultados estructurados al frontend.

## Base de datos

La plataforma utiliza PostgreSQL como sistema de gestión de base de datos
relacional, con soporte opcional para la extensión TimescaleDB que optimiza el
almacenamiento y consulta de datos de series temporales.

### Motivación de la elección

La base de datos inicial del sistema fue SQLite. Esta decisión se revisó cuando
la base de datos comenzó a aproximarse al límite práctico de ~2 GB, lo que
causaba degradación de rendimiento y bloqueos de la aplicación. La migración a
PostgreSQL respondió a varias necesidades simultáneas:

- Eliminar el límite de tamaño de 2 GB.
- Soportar múltiples conexiones simultáneas desde el frontend y los sensores.
- Mejorar el rendimiento de consultas complejas sobre grandes volúmenes de datos
  históricos.
- Habilitar compresión y retención automática de datos antiguos mediante
  TimescaleDB.
- Garantizar transacciones ACID completas en operaciones que afectan múltiples
  tablas.

### Modelo de datos

El esquema de base de datos está organizado en cuatro dominios funcionales:

**Dominio de identidad y acceso**:
- `users`: credenciales, roles y estado de las personas usuarias. Los roles
  documentados incluyen "tecnico" y "admin". Las contraseñas se almacenan con
  hash bcrypt.
- `audit_logs`: registro de acciones con trazabilidad por usuario y marca de
  tiempo.

**Dominio de sensores y configuración**:
- `sensors`: registro maestro de sensores RF con identificador único MAC,
  nombre, ubicación de referencia (lat, lng, alt) y estado administrativo.
- `antennas`: catálogo de antenas con rango de frecuencia, ganancia, tipo e
  inventario.
- `sensor_antennas`: relación muchos-a-muchos entre sensores y antenas, con
  puerto de conexión y estado activo/inactivo.
- `sensor_configurations`: parámetros de adquisición por sensor: frecuencias
  de inicio y fin, resolución, sample rate, ganancias LNA/VGA, tipo de ventana,
  solapamiento, configuración de demodulación AM/FM y filtros de canal.

**Dominio de datos de campo (series temporales)**:
- `sensor_status`: estado operativo del sensor: CPU por núcleo, RAM, disco,
  temperatura, latencia de red, delta de tiempo, logs. Es la tabla de mayor
  volumen y está configurada como hypertable de TimescaleDB particionada por
  `timestamp_ms`.
- `sensor_gps`: ubicación GPS histórica con latitud, longitud y altitud.
- `sensor_data`: datos de espectro radioeléctrico: arreglo de potencias PSD
  (Pxx), frecuencias de inicio y fin, marca de tiempo, ubicación y métricas
  de demodulación AM (profundidad) y FM (excursión). Se asocia opcionalmente
  a una campaña.
- `sensor_history_alert`: registro histórico de alertas operativas por sensor:
  tipo de alerta, descripción y marca de tiempo.

**Dominio de campañas y reportes**:
- `campaigns`: definición de campañas de medición: nombre, estado, fechas,
  horas de operación, intervalo, rango de frecuencia, ancho de banda,
  resolución y preset.
- `campaign_sensors`: relación entre campañas y sensores asignados, con
  restricción de unicidad por par campaña-sensor.
- `compliance_reports_cache`: caché de reportes de cumplimiento normativo en
  formato JSON, uno por campaña.
- `system_configurations`: tabla clave-valor para parámetros globales del
  sistema.

### TimescaleDB

La extensión TimescaleDB se aplica sobre `sensor_status`, la tabla de mayor
crecimiento al recibir actualizaciones periódicas de cada sensor. La
configuración incluye:

- Hypertable particionada por la columna `timestamp_ms` (epoch milliseconds).
- Intervalo de partición configurado según la carga de datos esperada.
- Índices compuestos por MAC y timestamp para optimizar consultas de series
  temporales por sensor.

Otras tablas como `sensor_data` y `sensor_gps` son candidatas futuras para
migración a hypertables, sujeto al volumen de datos acumulado.

## API REST

La interfaz de programación del backend está organizada en ocho categorías
funcionales, documentadas mediante especificación OpenAPI accesible a través de
Swagger UI.

### Categorías de endpoints

1. **Sensor Data** (ingesta de datos desde sensores): endpoints POST para que
   los sensores envíen estado, GPS, datos de espectro y audio demodulado al
   backend. Son los endpoints de mayor tráfico en operación normal.

2. **Sensor Query** (consultas de datos): endpoints GET para que el frontend
   consulte el último estado, última ubicación GPS, últimos datos de espectro,
   datos por rango temporal y configuración activa de un sensor identificado
   por su MAC.

3. **Sensor Control** (control remoto): endpoints POST para enviar comandos
   a los sensores: configurar parámetros de escaneo, detener adquisición,
   guardar configuración activa.

4. **Sensors Management** (gestión de sensores): CRUD completo de sensores,
   consulta por ID o MAC, y gestión de antenas asociadas (asignar, desasignar,
   consultar).

5. **Antennas Management** (gestión de antenas): CRUD completo del catálogo de
   antenas.

6. **Campaigns** (campañas): gestión completa de campañas de medición
   programadas: crear, listar, consultar, actualizar, eliminar, iniciar,
   detener, y consultar datos asociados.

7. **Reports** (reportes): generación de reportes de cumplimiento normativo a
   partir de los datos de una campaña, integrando el servicio de
   postprocesamiento.

8. **System** (sistema): endpoint raíz con información de versión y lista de
   endpoints disponibles.

### WebSocket

El backend mantiene dos canales WebSocket independientes:

- **Canal de datos de sensores** (`/ws`): transmite en tiempo real estados de
  sensores, actualizaciones GPS, datos de espectro, comandos de configuración
  y comandos de detención. Los mensajes siguen un formato tipado que permite
  al frontend actualizar mapas, gráficas y paneles sin recarga manual.

- **Canal de audio** (`/ws/audio/sensor/{id}` y `/ws/audio/listen/{id}`):
  transmite streaming de audio demodulado AM/FM en formato Opus codificado.
  Un sensor publica su audio y los clientes frontend se suscriben para
  escuchar en vivo.

## Seguridad y control de acceso

El modelo de seguridad opera en dos niveles complementarios:

**Autenticación de personas usuarias**: para el acceso desde el frontend web,
el backend se integra con Microsoft Azure AD mediante el protocolo OpenID
Connect. Las personas de la institución inician sesión con sus credenciales
institucionales. El backend valida los tokens emitidos por Azure y mantiene
sesiones mediante JWT propios. También existe un mecanismo de acceso
administrativo local con credenciales almacenadas en la base de datos
(encriptadas con bcrypt) para cuentas de servicio.

**Autorización por roles**: los middleware de autorización verifican el rol
de la persona usuaria antes de permitir operaciones sensibles. La
configuración de la plataforma (gestión de antenas, usuarios, parámetros del
sistema) está restringida a roles administrativos.

**Validación de sensores**: los endpoints de ingesta de datos desde sensores
operan con validación por dirección MAC. Cada sensor se identifica por su
MAC única registrada en el sistema. Los datos de sensores no registrados son
rechazados.

## Despliegue en la nube

La plataforma se despliega en un servidor institucional privado de la regulatory body,
sin acceso público a Internet. El acceso se realiza a través de la red interna
de la entidad.

**Infraestructura de contenedores**: tanto el backend como el frontend se
empaquetan como imágenes Docker independientes. El backend utiliza una
construcción multi-etapa: compilación de TypeScript en una etapa y ejecución
en Node.js Alpine en la etapa final, minimizando el tamaño de la imagen de
producción.

**Base de datos**: PostgreSQL se ejecuta en el mismo entorno de servidor, con
la extensión TimescaleDB habilitada. Se recomienda la imagen oficial
timescale/timescaledb para garantizar compatibilidad.

**Proxy inverso**: Nginx actúa como punto de entrada único, enrutando tráfico
HTTP al frontend (archivos estáticos) y al backend (API REST), y tráfico
WebSocket al backend para comunicación en tiempo real. La configuración
incluye timeouts extendidos (1 hora) para soportar la generación de reportes
de larga duración, compresión gzip y políticas de caché para activos
estáticos.

**Variables de entorno**: la configuración de conexión a base de datos y
puerto del servidor se gestiona mediante variables de entorno, permitiendo
desplegar el mismo artefacto en distintos entornos sin recompilación.

**Direcciones de servicio**:

| Entorno | HTTP API | WebSocket | Swagger |
|---|---|---|---|
| Desarrollo local | `localhost:3000` | `localhost:3000/ws` | `localhost:3000/api-docs` |
| Producción (VPN) | `172.23.90.25:3000` | `172.23.90.25:3000/ws` | `172.23.90.25:3000/api-docs` |
| Producción (externa) | `rsm.ane.gov.co:3000` | `rsm.ane.gov.co:3000/ws` | `rsm.ane.gov.co:3000/api-docs` |

## Decisiones de diseño

### PostgreSQL sobre SQLite

La decisión de migrar de SQLite a PostgreSQL fue la de mayor impacto
arquitectónico. SQLite ofrecía simplicidad operativa —sin servidor de base de
datos separado, todo en un archivo—, pero impuso limitaciones concretas: el
límite práctico de ~2 GB causaba bloqueos en producción, no soportaba
concurrencia de escritura desde múltiples sensores y frontend simultáneamente,
y carecía de tipos nativos para datos geoespaciales y series temporales.

La migración se realizó de forma progresiva: primero se actualizó la capa de
conexión a pg.Pool, luego se reescribieron los modelos de datos a sintaxis
PostgreSQL, se crearon nuevos scripts de migración y finalmente se actualizaron
las rutas. La extensión TimescaleDB se adoptó como optimización opcional para
producción, no como requisito de desarrollo.

### WebSocket para tiempo real en lugar de polling

Se eligió WebSocket como mecanismo de comunicación en tiempo real en lugar de
polling HTTP periódico. Esta decisión se justifica por la naturaleza de los
datos: los sensores transmiten actualizaciones de estado, GPS y espectro de
forma continua durante monitoreos activos. El polling habría generado tráfico
innecesario y latencia en la visualización. WebSocket permite que el backend
notifique proactivamente al frontend solo cuando hay datos nuevos, reduciendo
la carga tanto en el servidor como en el cliente.

### Separación de canales de datos y audio

El audio demodulado se transmite por un canal WebSocket independiente del
canal de datos de sensores. Esta separación responde a dos necesidades:
(1) el audio requiere menor latencia y mayor frecuencia de transmisión que
los datos de espectro, y (2) no todos los monitoreos incluyen demodulación,
por lo que mantener canales separados evita sobrecarga innecesaria cuando
solo se adquiere espectro.

### Timeout extendido para reportes

El servidor HTTP y el proxy inverso están configurados con timeouts de 1 hora
(3600 segundos). Esta decisión responde al hallazgo de que los reportes de
cumplimiento normativo involucran consultas a múltiples tablas, procesamiento
de grandes volúmenes de datos espectrales e invocación al servicio de
postprocesamiento Python, y pueden exceder los timeouts por defecto de 30
segundos.

## Problemas presentados y ajustes realizados

### Límite de capacidad de SQLite

- **Problema**: la base de datos SQLite alcanzaba ~2 GB de datos acumulados,
  causando degradación de rendimiento y bloqueos de la aplicación en producción.
- **Evidencia**: logs de error del servidor, mediciones de tamaño de archivo
  de base de datos.
- **Causa**: SQLite no está diseñado para volúmenes de datos de series
  temporales con múltiples escrituras concurrentes desde varios sensores.
- **Ajuste**: migración completa a PostgreSQL con soporte para TimescaleDB. Se
  reescribió la capa de conexión, los modelos de datos y las rutas con
  consultas directas. Se mantuvo compatibilidad hacia atrás con los formatos
  de datos existentes.
- **Resultado**: eliminación del límite de capacidad, mejora de rendimiento
  en consultas complejas y habilitación de compresión y retención automática
  de datos.

### Endpoint de campañas para sensores

- **Problema**: el endpoint que consulta las campañas asignadas a un sensor
  presentaba resultados duplicados cuando existían múltiples registros de
  asignación, y el nombre del endpoint contenía un error tipográfico que
  causaba confusión en la integración con sensores físicos.
- **Evidencia**: logs de consulta de sensores físicos, pruebas de integración
  con hardware real.
- **Causa**: falta de deduplicación en la consulta SQL de asignación
  sensor-campaña e inconsistencia en la nomenclatura del endpoint.
- **Ajuste**: corrección del nombre del endpoint a la forma canónica,
  incorporación de lógica de deduplicación en la consulta, adición de filtro
  opcional por estado de campaña (scheduled, active, running, completed,
  cancelled) y validación de campos requeridos antes de la entrega.
- **Resultado**: los sensores físicos reciben una lista única de campañas
  asignadas con todos los parámetros necesarios para ejecutar las mediciones
  (frecuencia central, sample rate, ganancias, RBW, solapamiento, ventana,
  puerto de antena, filtros).

### Tiempos de espera en generación de reportes

- **Problema**: la generación de reportes de cumplimiento normativo fallaba
  por timeout cuando el volumen de datos acumulados de campaña era grande,
  especialmente en campañas de varios días con mediciones frecuentes.
- **Evidencia**: errores de timeout en el frontend (HTTP 504) y logs del proxy
  inverso Nginx.
- **Causa**: los timeouts por defecto del servidor HTTP (30 segundos) y de
  Nginx (60 segundos) eran insuficientes para el pipeline completo de
  consulta de datos históricos, invocación al servicio de postprocesamiento
  Python y armado de la respuesta JSON.
- **Ajuste**: configuración de timeouts extendidos a 3600 segundos tanto en
  el servidor Node.js como en el proxy inverso Nginx, con valores consistentes
  para proxy_read_timeout, proxy_connect_timeout y proxy_send_timeout.
- **Resultado**: los reportes se generan exitosamente incluso para campañas
  con grandes volúmenes de datos, eliminando los errores de timeout.

### Validación automática de estado de sensores

- **Problema**: sensores que dejaban de reportar datos permanecían con estado
  "active" en la plataforma, dando una falsa impresión de operatividad y
  dificultando la detección de fallas en campo.
- **Evidencia**: reportes de personas usuarias indicando sensores que
  aparecían activos en el panel pero no entregaban mediciones; inspección de
  estados en base de datos.
- **Causa**: ausencia de un mecanismo automático que verificara la frescura
  del último reporte de cada sensor y actualizara su estado en consecuencia.
- **Ajuste**: implementación de una tarea programada cada 30 segundos que
  consulta la antigüedad del último reporte de cada sensor activo. Los
  sensores que exceden el umbral de inactividad se marcan automáticamente
  como offline. Los cambios de estado se notifican al frontend mediante
  broadcast WebSocket con el tipo de mensaje `sensor_status_changed`.
- **Resultado**: el estado de los sensores en el panel refleja fielmente su
  condición operativa real, permitiendo al personal identificar rápidamente
  equipos que requieren atención.

## Aprendizajes

1. **Dimensionar la persistencia según la carga prevista**: SQLite fue adecuado
   para desarrollo y pruebas iniciales, pero mantener una base de datos sin
   servidor para una carga de producción con múltiples escritores concurrentes
   y grandes volúmenes de series temporales generó un cuello de botella que
   requirió migración. El aprendizaje es evaluar la estrategia de persistencia
   desde el inicio según el perfil de carga esperado, no solo según la
   conveniencia de desarrollo.

2. **La comunicación en tiempo real debe ser push, no pull**: WebSocket
   demostró ser la estrategia correcta para un sistema donde los datos fluyen
   de forma continua desde múltiples fuentes. El patrón de broadcast desde el
   backend evita que el frontend tenga que implementar lógica de polling y
   reduce la carga tanto en la red como en el servidor.

3. **Los timeouts deben calibrarse según la operación más costosa**: los
   valores por defecto de los servidores HTTP no contemplan operaciones de
   análisis que pueden tomar minutos. Identificar la operación de mayor
   duración —los reportes de cumplimiento— y configurar todos los timeouts de
   la cadena (servidor, proxy) en consecuencia evita fallos intermitentes
   difíciles de diagnosticar.

4. **La separación de canales por tipo de dato simplifica el manejo de
   calidades de servicio**: mantener datos de espectro y audio en canales
   WebSocket independientes permite tratar cada flujo con sus propios
   requisitos de latencia, frecuencia de transmisión y formato, sin que un
   tipo de dato afecte la calidad del otro.

5. **El mantenimiento automático del estado evita falsos positivos**: sin la
   tarea de validación periódica de estado de sensores, equipos desconectados
   aparecían como activos. La automatización de esta verificación eliminó un
   problema de confianza en la información mostrada y redujo la carga de
   verificación manual del personal operativo.

## Limitaciones

1. **Base de datos sin réplicas**: la configuración actual de PostgreSQL opera
   en instancia única, sin replicación ni alta disponibilidad. Una falla del
   servidor de base de datos interrumpiría toda la plataforma.

2. **Escalamiento vertical**: el backend está diseñado como un solo proceso
   Node.js. Si bien el pool de conexiones soporta concurrencia moderada, no
   está preparado para escalar horizontalmente a múltiples instancias sin un
   coordinador de WebSocket compartido (como Redis).

3. **Sin balanceo de carga**: el punto único de entrada a través de Nginx no
   contempla múltiples réplicas del backend para distribución de carga en
   escenarios de alta demanda.

4. **Dependencia de conectividad con sensores**: el modelo de operación asume
   que los sensores consultan periódicamente su configuración y campañas. Si
   un sensor pierde conectividad justo en el momento de consulta, puede no
   recibir una campaña programada hasta el siguiente ciclo de polling.

5. **Postprocesamiento externo sin cola de trabajos**: el análisis de
   emisiones y cumplimiento normativo depende de un servicio Python externo
   invocado de forma síncrona. Si este servicio no está disponible, la
   generación de reportes falla sin reintentos automáticos.

6. **Crecimiento de tablas no particionadas**: las tablas `sensor_data` y
   `sensor_gps` aún no están configuradas como hypertables de TimescaleDB. A
   medida que crezcan en volumen, pueden presentar degradación similar a la
   que motivó la migración desde SQLite.

## Repositorio

| Campo | Valor |
|---|---|
| Nombre del software | regulatory body Backend |
| Rama | main |
| Función en el sistema | Coordinación central: API REST, WebSocket, persistencia, gestión de campañas, alertas y reportes |
| Entradas | Solicitudes HTTP (frontend y sensores), datos de espectro, GPS, estado y audio desde sensores |
| Salidas | Respuestas JSON, eventos WebSocket, reportes de cumplimiento normativo |
| Dependencias | Node.js 18+, PostgreSQL 13+, TimescaleDB (opcional), Azure AD, servicio Python de postprocesamiento |
| Estado actual | En producción en servidor institucional privado |
