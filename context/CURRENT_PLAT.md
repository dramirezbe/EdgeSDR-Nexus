# Contexto Actual de la Plataforma regulatory body

Última actualización: 2026-05-21

## Fuentes Leídas

Este resumen usa solo la documentación principal del proyecto:

- `README.md`
- `frontend/DIAGRAM.md`
- `backend/DIAGRAM.md`
- `backend/README.md`
- `backend/API-DOCUMENTATION.md`
- `backend/ENDPOINT_CAMPAIGNS_CAMBIOS.md`
- `backend/EJEMPLOS_CAMPAIGNS_ENDPOINT.md`
- `backend/SIMULADOR_AM_FM.md`
- `backend/MIGRACION_POSTGRESQL.md`

No se usó contenido interno de `workshop-platform/` como fuente, excepto este archivo como destino de edición.

## Visión General

La Plataforma regulatory body es un sistema de sensado y monitoreo espectral. Permite operar sensores RF en campo, recibir mediciones, visualizar datos en vivo, administrar campañas de medición, revisar alertas y generar reportes de cumplimiento.

El flujo general es:

1. Una persona usuaria entra al frontend web.
2. El frontend consulta o ejecuta acciones contra el backend.
3. El backend administra usuarios, sensores, antenas, configuraciones, campañas, datos y reportes.
4. Los sensores RF reciben configuraciones o comandos, y envían estado, ubicación GPS, espectro y audio.
5. El backend guarda información histórica y actualiza el frontend en tiempo real.
6. Para reportes, el backend usa datos guardados, ubicación normativa y postprocesamiento Python.
7. El frontend presenta resultados interpretables, incluyendo hallazgos de cumplimiento.

En una frase: la plataforma conecta personas, sensores RF, backend, base de datos y análisis normativo para convertir mediciones de espectro en monitoreo operativo y reportes.

## Componentes Principales

### Frontend

El frontend es la interfaz web usada por la persona operadora o administradora. Sus responsabilidades visibles son:

- Ingreso a la plataforma mediante Microsoft Azure o acceso administrativo.
- Validación de sesión y permisos antes de entrar al panel principal.
- Pantalla de inicio con vista general, mapa y estadísticas.
- Menú lateral para navegar entre secciones.
- Revisión de dispositivos: sensores, ubicación, estado y antenas asociadas.
- Monitoreo en vivo de mediciones inmediatas.
- Creación, consulta y análisis de campañas.
- Revisión de alertas, incidentes y eventos.
- Configuración administrativa de sensores, antenas, usuarios y parámetros generales.
- Visualización de audio en vivo cuando está asociado a un sensor o monitoreo.

Pantallas principales documentadas:

- `Inicio`: mapa, estado general y estadísticas.
- `Dispositivos`: sensores, ubicaciones, estados y antenas.
- `Monitoreo`: configuración y visualización de una medición en vivo.
- `Campañas`: programación, consulta y análisis de mediciones planificadas.
- `Alertas`: incidentes y eventos detectados.
- `Configuración`: administración de recursos y parámetros.
- `Audio`: asociado al monitoreo o sensor, no como flujo principal independiente.

Referencias de implementación indicadas por la documentación:

- Rutas y entrada: `frontend/src/main.tsx`
- Sesión y permisos: `frontend/src/contexts/AuthContext.tsx`
- Aplicación principal: `frontend/src/App.tsx`
- Menú lateral: `frontend/src/components/Sidebar.tsx`
- Login: `frontend/src/components/Login.tsx`
- Dispositivos: `frontend/src/components/MonitoringNetwork.tsx`
- Monitoreo: `frontend/src/components/ConfigurationPanel.tsx`, `frontend/src/components/AnalysisPanel.tsx`
- Campañas: `frontend/src/components/CampaignsList.tsx`, `frontend/src/components/CampaignModal.tsx`, `frontend/src/components/CampaignDataViewer.tsx`
- Alertas: `frontend/src/components/AlertsPanel.tsx`
- Configuración: `frontend/src/components/AntennaManagement.tsx`, `frontend/src/components/UserManagement.tsx`
- Audio: `frontend/src/components/WebRTCAudioPlayer.tsx`, `frontend/src/pages/AudioPage.tsx`

### Backend

El backend es el centro de coordinación de la plataforma. Recibe solicitudes del frontend, datos desde sensores y peticiones para reportes. También guarda información, emite eventos en tiempo real y coordina servicios externos.

Responsabilidades principales:

- Recibir solicitudes REST desde el frontend.
- Validar usuarios, sesiones y permisos según el diseño documentado.
- Administrar sensores, antenas, usuarios y configuración.
- Coordinar monitoreos inmediatos y campañas programadas.
- Preparar órdenes para sensores: configurar, iniciar o detener.
- Recibir datos de campo: estado, GPS, espectro y audio.
- Guardar información histórica.
- Avisar cambios al frontend en tiempo real mediante WebSocket.
- Detectar alertas operativas.
- Generar reportes usando mediciones, ubicación normativa y postprocesamiento.
- Ejecutar mantenimiento automático, como marcar sensores retrasados u offline, cerrar campañas y detener monitoreos vencidos.

Tecnología documentada:

- Node.js 18+
- TypeScript
- REST API
- WebSocket en `/ws`
- PostgreSQL como base de datos principal documentada.
- Swagger UI para documentación de API.

Referencias de implementación indicadas:

- Servidor: `backend/src/app.ts`
- WebSocket: `backend/src/websocket.ts`
- Audio en vivo: `backend/src/audioServer.ts`
- Base de datos: `backend/src/database/connection.ts`
- Autenticación: `backend/src/routes/auth.ts`, `backend/src/middleware/auth.ts`, `backend/src/middleware/azureAuth.ts`
- Sensores y datos: `backend/src/routes/sensor.ts`, `backend/src/models/Sensor.ts`, `backend/src/models/SensorData.ts`
- Gestión y alertas: `backend/src/routes/management.ts`, `backend/src/models/Antenna.ts`, `backend/src/models/SensorHistoryAlert.ts`
- Campañas: `backend/src/routes/campaign.ts`
- Reportes: `backend/src/routes/reports.ts`
- Configuración: `backend/src/routes/config.ts`

### Sensores RF

Los sensores RF son los equipos de campo que miden el espectro y reportan datos al backend.

Datos que envían:

- Estado del sensor, por ejemplo batería, temperatura, CPU, RAM o calidad de señal.
- Ubicación GPS.
- Datos de espectro radioeléctrico, incluyendo FFT o potencias.
- Audio demodulado AM/FM cuando aplica.

Acciones que pueden recibir o consultar:

- Configuración de escaneo.
- Comando para detener adquisición.
- Configuración activa.
- Campañas o parámetros vigentes.

Los sensores físicos también consultan sus campañas asignadas mediante:

- `GET /api/sensor/{mac}/campaigns`

Este endpoint reemplaza el nombre con error tipográfico `/api/sensor/:mac/campains`, elimina duplicados y devuelve información completa para que el sensor pueda ejecutar mediciones planificadas. Si no se envía filtro de estado, devuelve solo campañas `scheduled`, `active` o `running`.

Campos clave de la respuesta de campañas para sensores:

- `campaign_id`
- `status`
- `center_freq_hz`
- `timeframe.start`
- `timeframe.end`
- `rbw_hz`
- `sample_rate_hz`
- `antenna_port`
- `acquisition_period_s`
- `span`
- `scale`
- `window`
- `overlap`
- `lna_gain`
- `vga_gain`
- `antenna_amp`
- `filter`

Los campos `center_freq_hz`, `timeframe.start` y `timeframe.end` siempre aparecen, pero pueden ser `null`; los sensores deben validarlos antes de ejecutar una campaña.

### Base de Datos

La documentación describe PostgreSQL como base de datos del sistema. La información guardada incluye:

- Usuarios y roles.
- Sensores.
- Antenas.
- Relaciones sensor-antena.
- Configuraciones activas de adquisición.
- Campañas y sensores asignados.
- Estados históricos de sensores.
- Ubicaciones GPS históricas.
- Mediciones de espectro.
- Alertas históricas.
- Resultados o caché de reportes cuando aplica.

Tablas mencionadas explícitamente:

- `sensors`
- `antennas`
- `sensor_antennas`
- `sensor_status`
- `sensor_gps`
- `sensor_data`
- `sensor_configurations`
- `campaigns`

La migración documentada mueve el sistema desde SQLite hacia PostgreSQL con soporte opcional de TimescaleDB. La motivación principal es evitar el límite práctico de SQLite alrededor de 2 GB y mejorar el manejo de datos de series temporales, múltiples conexiones, consultas complejas, compresión y retención automática.

Estado documentado de migración:

- `package.json` actualizado con `pg` y `@types/pg`.
- `connection.ts` reescrito con `pg.Pool`.
- `migrate-postgres.ts` creado para esquemas PostgreSQL.
- Modelos `Sensor`, `Antenna` y `SensorData` actualizados a sintaxis PostgreSQL.
- `campaign.ts` actualizado con cliente PostgreSQL y transacciones.
- `migrate.ts` queda obsoleto para SQLite.
- `seed.ts` queda pendiente de actualización.
- `sensor.ts` queda pendiente de revisión por posibles queries directas.

TimescaleDB es opcional para desarrollo, pero recomendado para producción por hypertables, compresión automática, retención automática y consultas temporales optimizadas.

### Postprocesamiento

El postprocesamiento Python se usa para análisis normativo. Recibe mediciones de campaña desde el backend y devuelve resultados de análisis.

Funciones documentadas:

- Detectar emisiones.
- Medir parámetros de emisiones.
- Evaluar cumplimiento cuando existe información normativa.
- Marcar hallazgos como cumple, fuera de parámetros o sin licencia asociada, según aplique.

### Servicios de Apoyo

Servicios o fuentes externas mencionadas:

- Azure AD para identidad institucional.
- Servicio o datos de ubicación normativa para municipio, departamento y DANE.
- Módulo Python de postprocesamiento para detección de emisiones y cumplimiento.

## Flujo de Usuario en el Frontend

El recorrido principal es:

1. Abrir la plataforma.
2. Ingresar con Microsoft Azure o acceso administrativo.
3. Validar sesión.
4. Entrar al panel principal.
5. Revisar el mapa, estado general y estadísticas.
6. Elegir una tarea desde el menú lateral.

Tareas principales:

- Revisar dispositivos.
- Monitorear en vivo.
- Trabajar con campañas.
- Revisar alertas.
- Generar o revisar reportes.
- Configurar la plataforma si el usuario tiene permisos administrativos.
- Cerrar sesión.

## Flujo de Monitoreo en Vivo

El flujo central de medición inmediata es:

1. Elegir sensor.
2. Elegir antena.
3. Definir parámetros, como rango de frecuencia y tipo de medición.
4. Iniciar adquisición.
5. Ver datos en vivo, incluyendo espectro, vista temporal y audio si aplica.
6. Decidir si se detiene la medición o si se crea una campaña con esa configuración.

El backend prepara la configuración, la envía al sensor, recibe los datos capturados, los guarda y actualiza al frontend en tiempo real.

## Flujo de Campañas

Las campañas permiten programar mediciones planificadas.

Capacidades documentadas:

- Crear, listar, consultar, actualizar y eliminar campañas.
- Definir fecha de inicio y fin.
- Definir horas de operación.
- Definir intervalo de medición.
- Configurar rango de frecuencia, ancho de banda, resolución y preset.
- Asignar sensores.
- Iniciar y detener campañas.
- Consultar datos asociados a una campaña.
- Usar datos de campaña para reportes.

El backend también contempla mantenimiento automático para cerrar campañas y detener monitoreos vencidos.

Flujo específico para sensores físicos:

1. El sensor consulta `GET /api/sensor/{mac}/campaigns`.
2. El backend valida que el sensor exista.
3. Si el sensor no existe, responde `404` con `{"error": "Sensor not found"}`.
4. Si existe pero no tiene campañas asignadas, responde `{"campaigns": []}`.
5. Si hay campañas, devuelve configuración lista para adquisición.
6. El sensor valida `center_freq_hz` y `timeframe`.
7. El sensor ejecuta la medición y luego envía datos por `POST /api/sensor/data`.

El endpoint acepta filtro opcional `status` con valores `scheduled`, `active`, `running`, `completed` o `cancelled`.

## Flujo de Reportes

Los reportes conectan mediciones históricas, ubicación y análisis normativo.

Flujo general:

1. La persona consulta datos de campaña o alertas.
2. Solicita generar o revisar un reporte.
3. El backend recoge mediciones guardadas.
4. El backend valida ubicación normativa.
5. El backend solicita análisis al postprocesamiento Python.
6. El postprocesamiento devuelve emisiones detectadas y evaluación de cumplimiento.
7. El backend entrega un reporte estructurado.
8. El frontend muestra conclusiones interpretables, como cumple, alerta o requiere revisión.

Endpoint documentado:

- `POST /api/reports/compliance/{campaignId}` para generar reporte de cumplimiento normativo.

## Flujo de Alertas

El backend detecta y registra alertas operativas. La documentación menciona:

- Desconexión o retraso de sensores.
- Problemas de recursos.
- Temperatura.
- Logs o eventos operativos.

Las alertas se guardan históricamente y se comunican al frontend para revisión. Desde alertas también se puede llegar a reportes o resultados.

## API REST

La documentación Swagger está disponible cuando el backend está en ejecución:

- Local: `http://localhost:3000/api-docs`
- Producción VPN: `http://172.23.90.25:3000/api-docs`
- Producción pública: `http://rsm.ane.gov.co:3000/api-docs`

Especificación JSON:

- `http://172.23.90.25:3000/api-docs.json`

Categorías de API documentadas:

- `Sensor Data`: datos enviados por sensores físicos.
- `Sensor Query`: consulta de datos históricos.
- `Sensor Control`: configuración y control remoto de sensores.
- `Sensors Management`: CRUD de sensores.
- `Antennas Management`: CRUD de antenas.
- `Campaigns`: gestión de campañas.
- `Reports`: generación de reportes.
- `System`: información general del sistema.

Endpoints de datos del sensor:

- `POST /api/sensor/status`
- `POST /api/sensor/gps`
- `POST /api/sensor/data`
- `POST /api/sensor/audio`

Endpoints de consulta del sensor:

- `GET /api/sensor/{mac}/latest-status`
- `GET /api/sensor/{mac}/latest-gps`
- `GET /api/sensor/{mac}/latest-data`
- `GET /api/sensor/{mac}/data/range`
- `GET /api/sensor/{mac}/configuration`
- `GET /api/sensor/{mac}/campaigns`

Endpoints de control del sensor:

- `POST /api/sensor/{mac}/configure`
- `POST /api/sensor/{mac}/stop`
- `POST /api/sensor/{mac}/configuration`

Endpoints de gestión de sensores:

- `GET /api/sensors`
- `GET /api/sensors/{id}`
- `GET /api/sensors/mac/{mac}`
- `POST /api/sensors`
- `PUT /api/sensors/{id}`
- `DELETE /api/sensors/{id}`
- `GET /api/sensors/{id}/antennas`
- `POST /api/sensors/{id}/antennas`
- `DELETE /api/sensors/{sensorId}/antennas/{antennaId}`

Endpoints de gestión de antenas:

- `GET /api/antennas`
- `GET /api/antennas/{id}`
- `POST /api/antennas`
- `PUT /api/antennas/{id}`
- `DELETE /api/antennas/{id}`

Endpoints de campañas:

- `GET /api/campaigns`
- `GET /api/campaigns/{id}`
- `POST /api/campaigns`
- `PUT /api/campaigns/{id}`
- `DELETE /api/campaigns/{id}`
- `POST /api/campaigns/{id}/start`
- `POST /api/campaigns/{id}/stop`
- `GET /api/campaigns/{id}/data`

Endpoint de sistema:

- `GET /`

Nota de seguridad documentada: `backend/API-DOCUMENTATION.md` dice que actualmente la API no requiere autenticación y que no hay rate limiting configurado. Esto convive con el diseño de frontend/backend que sí contempla ingreso, sesiones, permisos y Azure AD para la experiencia de usuario.

## WebSocket y Tiempo Real

El backend expone WebSocket en:

- Local: `ws://localhost:3000/ws`
- Producción documentada: `ws://172.23.90.25:3000/ws`

Mensajes documentados:

- `sensor_status`: estados de sensores.
- `sensor_gps`: actualizaciones de ubicación.
- `sensor_data`: datos de espectro en tiempo real.
- `sensor_configure`: comandos de configuración.
- `sensor_stop`: comandos de detención.

El frontend usa estos eventos para actualizar mapas, pantallas de monitoreo y vistas recientes sin esperar recarga manual.

## Audio AM/FM y Simulador

La documentación del simulador indica que existe soporte para simular demodulación AM/FM con audio en tiempo real.

Capacidades documentadas:

- Menú interactivo para elegir número de puntos de frecuencia y tipo de demodulación: ninguna, AM o FM.
- Audio simulado como tono sinusoidal de 1 kHz con ruido.
- Sample rate de 48 kHz.
- Paquetes de audio de 500 ms.
- PCM codificado en base64.
- Envío de audio cada 500 ms cuando hay demodulación activa.
- Envío de espectro y métricas cada 2 s.

Endpoints usados por el simulador:

- `POST /api/sensor/data` para espectro y métricas AM/FM.
- `POST /api/sensor/audio` para audio PCM base64.

Métricas AM documentadas:

- `depth.unit = "percent"`
- `peak_to_peak`
- `peak_deviation`
- `rms_deviation`

Métricas FM documentadas:

- `excursion.unit = "hz"`
- `peak_to_peak_hz`
- `peak_deviation_hz`
- `rms_deviation_hz`

Estado documentado del flujo AM/FM:

- El simulador genera audio PCM.
- El backend recibe métricas y audio.
- El backend transmite por WebSocket.
- El frontend tiene `AudioPlayer` funcional.
- El frontend muestra métricas en tiempo real.

## Datos Principales

Entidades centrales:

- Usuario
- Rol o permisos
- Sensor
- Antena
- Relación sensor-antena
- Estado de sensor
- Ubicación GPS
- Medición de espectro
- Audio demodulado
- Configuración de adquisición
- Campaña
- Alerta
- Reporte
- Resultado de cumplimiento

Campos o parámetros frecuentes:

- `mac`
- `lat`
- `lng`
- `timestamp`
- `Pxx`
- `start_freq_hz`
- `end_freq_hz`
- `center_frequency`
- `span`
- `sample_rate_hz`
- `resolution_hz`
- `antenna_port`
- `window`
- `overlap`
- `start_date`
- `end_date`
- `start_time`
- `end_time`
- `interval_seconds`
- `start_freq_mhz`
- `end_freq_mhz`
- `bandwidth_mhz`
- `resolution_khz`
- `preset`

## Operación y Despliegue

Requisitos documentados para backend:

- Node.js 18+
- `npm` o `yarn`

Comandos documentados:

- Instalar dependencias: `npm install`
- Migrar base de datos: `npm run migrate`
- Desarrollo: `npm run dev`
- Producción: `npm run build` y `npm start`

Servidor local:

- HTTP API: `http://localhost:3000`
- WebSocket: `ws://localhost:3000/ws`

Variables de entorno documentadas:

- `PORT=3000`
- `DB_PATH=./data/ane.db`
- `NODE_ENV=development`

Variables documentadas para PostgreSQL:

- `DB_HOST=localhost`
- `DB_PORT=5432`
- `DB_NAME=ane_db`
- `DB_USER=postgres`
- `DB_PASSWORD=<password>`
- `PORT=3000`
- `NODE_ENV=development`

Nota: aunque la documentación técnica describe PostgreSQL como base de datos, también aparece `DB_PATH=./data/ane.db` y una referencia legacy a `backend/data/ane.db`. Esto sugiere que puede existir historia o compatibilidad previa con una base local legacy.

Despliegue recomendado en documentación de migración:

- PostgreSQL 13+.
- TimescaleDB opcional en desarrollo y recomendada en producción.
- Docker Compose con servicio `postgres` usando imagen `timescale/timescaledb:latest-pg14`.
- Backend construido desde `./backend` y conectado a la base por variables `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`.

## Riesgos o Brechas Documentadas

- La API REST está documentada como pública y sin rate limiting actualmente.
- El diseño habla de usuarios, sesiones, permisos y Azure AD, por lo que conviene validar si todos los endpoints sensibles ya están protegidos o si la protección vive solo en la interfaz.
- Hay una posible inconsistencia documental entre PostgreSQL y `DB_PATH=./data/ane.db`.
- La migración PostgreSQL aún documenta tareas pendientes: actualizar `seed.ts`, revisar `sensor.ts`, ejecutar instalación/migraciones/seed y validar endpoints/WebSocket.
- Los diagramas describen audio en vivo, alertas, usuarios, configuración y reportes; conviene verificar que todos esos flujos estén implementados y probados en código.

## Resumen Ejecutivo

La Plataforma regulatory body es una aplicación web con backend TypeScript que coordina sensores RF, datos en tiempo real, históricos, campañas y reportes. El frontend guía a la persona desde autenticación y vista general hasta monitoreo, campañas, alertas, configuración y resultados. El backend centraliza autenticación, gestión de recursos, recepción de datos, WebSocket, persistencia, alertas, campañas y reportes. Los sensores alimentan la plataforma con estado, GPS, espectro y audio. El postprocesamiento Python transforma mediciones de campaña en detecciones y evaluación de cumplimiento normativo.
