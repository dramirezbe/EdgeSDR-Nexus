# Contexto del Frontend — Plataforma ANE

Este documento consolida el contexto del frontend de la Plataforma ANE como
insumo para redactar el capítulo "Plataforma web en la nube" del informe final.
Toda la información se presenta desde una perspectiva metodológica, de
arquitectura y de decisiones de diseño, sin referencias a archivos de código ni
estructura de directorios.

## Propósito del componente

El frontend es la interfaz web a través de la cual las personas operadoras y
administradoras interactúan con el sistema de monitoreo espectral. Su función
es presentar de forma clara y accionable los datos capturados por los sensores
RF, facilitar la configuración de mediciones, la gestión de campañas, la
revisión de alertas y la consulta de reportes de cumplimiento normativo.

El frontend no es simplemente una capa de presentación: implementa la lógica
de navegación, el flujo de autenticación institucional, la conexión en tiempo
real con el backend, la visualización interactiva de datos científicos y la
experiencia completa de usuario para todas las funciones del sistema.

## Usuarios y roles

La plataforma está dirigida a dos perfiles principales de personas usuarias:

- **Personal técnico / operador**: accede a las funciones de monitoreo en vivo,
  consulta de dispositivos, creación y seguimiento de campañas, revisión de
  alertas y consulta de reportes. Es el perfil de uso cotidiano.

- **Personal administrativo**: además de las funciones del perfil técnico,
  tiene acceso a la configuración de la plataforma: gestión de antenas, gestión
  de sensores, administración de usuarios y parámetros generales del sistema.

El acceso se realiza mediante autenticación institucional a través de
Microsoft Azure AD, utilizando las credenciales corporativas de la ANE. La
plataforma también contempla un mecanismo de acceso administrativo local para
cuentas de servicio. Los roles se asignan en la base de datos y determinan
qué secciones del menú y qué funcionalidades están disponibles para cada
persona.

## Funcionalidades

El frontend organiza sus funcionalidades en pantallas principales accesibles
desde un menú lateral de navegación:

### Inicio (Dashboard)

Vista general al ingresar a la plataforma. Presenta:
- Mapa geográfico con la ubicación de todos los sensores registrados, usando
  marcadores que reflejan el estado operativo de cada dispositivo.
- Resumen de estadísticas del sistema: sensores activos, campañas en curso,
  alertas recientes.
- Punto de partida para navegar a cualquier sección.

### Dispositivos

Pantalla de gestión y monitoreo de la red de sensores:
- Listado de todos los sensores registrados con su estado actual, ubicación y
  antenas asociadas.
- Visualización en mapa de la red de sensores con indicadores de estado por
  colores.
- Acceso al detalle de cada sensor: información técnica, antenas conectadas,
  historial de estado.
- Punto de entrada para iniciar un monitoreo en vivo sobre un sensor específico.

### Monitoreo en vivo

Flujo central de la plataforma para realizar una medición inmediata:
1. Selección del sensor objetivo.
2. Selección de la antena a utilizar (puerto).
3. Definición de parámetros de adquisición: rango de frecuencia (inicio/fin),
   tipo de medición, ganancias, ancho de banda, resolución.
4. Inicio de la adquisición.
5. Visualización en tiempo real de los datos capturados:
   - Espectro de potencia (PSD) en gráfica interactiva.
   - Vista temporal (waterfall) para observar evolución de señales.
   - Audio demodulado AM/FM cuando está habilitado, con reproductor
     integrado y métricas de modulación (profundidad AM, excursión FM).
6. Finalización de la medición, con opción de guardar la configuración como
   nueva campaña.

### Campañas

Gestión de mediciones programadas:
- Listado de todas las campañas con filtros por estado (programada, activa,
  en ejecución, completada, cancelada).
- Creación de nuevas campañas: definición de nombre, fechas de inicio y fin,
  horas de operación, intervalo entre mediciones, parámetros espectrales
  (rango de frecuencia, ancho de banda, resolución, preset) y asignación de
  sensores.
- Visualización de detalle de una campaña: configuración, sensores asignados,
  estado actual.
- Consulta de datos capturados asociados a una campaña.
- Inicio y detención manual de campañas.
- Los datos de campaña son la fuente principal para la generación de reportes
  de cumplimiento normativo.

### Alertas

Revisión de incidentes y eventos detectados por el sistema:
- Listado cronológico de alertas operativas: desconexión de sensores,
  anomalías de temperatura, consumo excesivo de recursos, eventos de sistema.
- Filtro por sensor, tipo de alerta y rango de fechas.
- Vinculación con los datos del sensor para facilitar el diagnóstico.
- Navegación desde alertas hacia reportes cuando la alerta está asociada a una
  campaña.

### Configuración

Panel administrativo para la gestión de recursos del sistema:
- **Gestión de antenas**: CRUD completo del catálogo de antenas, con tipo,
  rango de frecuencia, ganancia y código de inventario.
- **Gestión de usuarios**: administración de cuentas de acceso, roles y
  permisos.
- **Parámetros del sistema**: configuración de valores globales de la
  plataforma.

### Audio

Reproductor de audio demodulado AM/FM, accesible desde el monitoreo en vivo
o desde la vista de un sensor específico. Permite:
- Escuchar en tiempo real la señal demodulada durante un monitoreo activo.
- Visualizar métricas de modulación AM (profundidad pico a pico, desviación
  RMS) y FM (excursión pico a pico, desviación RMS).
- Control de reproducción independiente del panel de espectro.

## Arquitectura técnica

### Pila tecnológica

- **Librería principal**: React 19 con TypeScript
- **Empaquetador**: Vite 5
- **Estilos**: Tailwind CSS 3
- **Enrutamiento**: React Router 7
- **Visualización de datos**: Plotly.js para gráficas de espectro y waterfall;
  Recharts para gráficas estadísticas
- **Mapas**: Leaflet con React-Leaflet para visualización geoespacial
- **Autenticación**: Microsoft Authentication Library (MSAL) para Azure AD
- **Comunicación HTTP**: Axios
- **Íconos**: Lucide React

### Organización de la aplicación

La aplicación sigue una arquitectura basada en componentes con separación
clara de responsabilidades:

**Capa de entrada y enrutamiento**: el punto de entrada configura los
proveedores globales (autenticación MSAL, enrutamiento) y define las rutas
de la aplicación. La autenticación envuelve toda la aplicación, de modo que
cualquier ruta protegida requiere una sesión válida.

**Capa de contexto y estado global**:
- `AuthContext`: gestiona el estado de autenticación, la sesión de la persona
  usuaria, sus permisos y el token de acceso. Provee funciones de login,
  logout y verificación de sesión a toda la aplicación.
- Estado local por componente: cada pantalla gestiona sus propios datos
  mediante hooks de React (useState, useEffect), consultando al backend según
  necesidad.

**Capa de componentes de interfaz**:
- `Login`: pantalla de ingreso con integración Azure AD (botón institucional)
  y acceso administrativo local.
- `Sidebar`: menú lateral de navegación que adapta las opciones visibles
  según el rol de la persona.
- `MonitoringNetwork`: vista de red de sensores con mapa interactivo y
  listado de dispositivos.
- `ConfigurationPanel`: panel de configuración de parámetros para monitoreo
  en vivo.
- `AnalysisPanel`: panel de visualización de espectro, waterfall y métricas
  durante un monitoreo activo.
- `CampaignsList`: listado de campañas con filtros y acciones.
- `CampaignModal`: formulario de creación y edición de campañas, con
  selección de sensores y definición de parámetros.
- `CampaignDataViewer`: visualización de datos capturados en una campaña.
- `AlertsPanel`: listado y revisión de alertas operativas.
- `AntennaManagement`: CRUD del catálogo de antenas con validación de campos.
- `UserManagement`: administración de cuentas de usuario.
- `WebRTCAudioPlayer`: reproductor de audio en vivo con soporte para Opus.

**Capa de servicios**: comunicación con el backend mediante Axios. Los
servicios encapsulan las llamadas HTTP a los diferentes endpoints de la API
(sensores, antenas, campañas, reportes, configuración) y gestionan la
inclusión automática de tokens de autenticación.

**Capa de hooks**: lógica reutilizable extraída en hooks personalizados para
operaciones comunes como consulta de estado de sensores, suscripción a
WebSocket y manejo de datos de espectro.

### Comunicación en tiempo real

El frontend mantiene una conexión WebSocket con el backend para recibir
actualizaciones en tiempo real sin necesidad de recargar la página. Los
eventos recibidos incluyen:

- `sensor_status`: cambios en el estado operativo de los sensores (online,
  offline, recursos).
- `sensor_gps`: actualizaciones de ubicación de los sensores en campo.
- `sensor_data`: datos de espectro capturados durante monitoreos activos.
- `sensor_configure`: confirmación de comandos de configuración enviados.
- `sensor_stop`: confirmación de comandos de detención.

Estos eventos actualizan automáticamente los mapas, las gráficas de espectro
y los indicadores de estado en todas las pantallas relevantes.

## Visualizaciones

### Espectro de potencia (PSD)

La gráfica principal de monitoreo muestra la densidad espectral de potencia
en el rango de frecuencia configurado. Se utiliza Plotly.js para renderizar
gráficas interactivas con las siguientes capacidades:

- Eje X: frecuencia en MHz o Hz.
- Eje Y: potencia en dBm.
- Zoom y desplazamiento interactivos para inspeccionar regiones de interés.
- Actualización en tiempo real durante monitoreos activos, con nuevos datos
  recibidos por WebSocket.
- Superposición de múltiples capturas para comparación temporal.

### Waterfall (espectrograma)

Visualización de la evolución temporal del espectro, donde el eje vertical
representa el tiempo y la intensidad de color representa la potencia. Permite
identificar patrones de transmisión, señales intermitentes y cambios en la
ocupación espectral a lo largo del tiempo.

### Mapa de sensores

Visualización geoespacial usando Leaflet con marcadores interactivos:
- Cada sensor se ubica según sus coordenadas GPS.
- El color del marcador indica el estado operativo (verde: activo, rojo:
  offline, amarillo: advertencia).
- Al hacer clic en un marcador se muestra información del sensor y acceso
  rápido a monitoreo.
- El mapa se actualiza automáticamente cuando los sensores reportan nuevas
  posiciones GPS.

### Métricas de audio

Durante monitoreos con demodulación activa, se muestran en tiempo real:
- AM: profundidad de modulación (porcentaje), valores pico a pico, desviación
  RMS.
- FM: excursión de frecuencia (Hz), valores pico a pico, desviación RMS.

### Estadísticas del sistema

Gráficas de resumen en el panel de inicio usando Recharts para visualizar
tendencias de actividad, ocupación espectral y estado de la red de sensores.

## Seguridad y control de acceso

El frontend implementa la capa de presentación del modelo de seguridad:

**Autenticación con Azure AD**: utiliza la librería MSAL (Microsoft
Authentication Library) para integrar el flujo de login institucional. La
persona usuaria es redirigida al portal de Microsoft para autenticarse con
sus credenciales corporativas. Tras la autenticación exitosa, MSAL gestiona
los tokens de acceso y su renovación automática.

**Protección de rutas**: el enrutador verifica la existencia de una sesión
activa antes de renderizar cualquier ruta protegida. Si no hay sesión, la
persona es redirigida a la pantalla de login.

**Adaptación de interfaz por rol**: el menú lateral y las rutas disponibles
se filtran según el rol asignado a la persona usuaria, ocultando las opciones
de configuración a quienes no tienen permisos administrativos.

**Tokens en comunicación con backend**: los servicios HTTP incluyen
automáticamente el token de acceso en las cabeceras de las solicitudes al
backend, permitiendo que el backend valide la identidad y los permisos en
cada operación.

## Despliegue

El frontend se despliega como una aplicación web estática servida por Nginx:

**Construcción**: Vite genera un conjunto de archivos HTML, JavaScript y CSS
optimizados. Plotly.js se separa en un chunk independiente para mejorar la
carga inicial, ya que es la dependencia de mayor tamaño. Los assets
estáticos se versionan para permitir caché agresiva.

**Servidor web**: Nginx sirve los archivos estáticos y actúa como proxy
inverso hacia el backend para las rutas `/api/` y `/ws` (WebSocket). La
configuración SPA garantiza que todas las rutas de la aplicación que no
corresponden a archivos físicos se redirijan al `index.html`, permitiendo
que React Router maneje la navegación del lado del cliente.

**Contenedor**: la imagen Docker se construye en dos etapas: compilación en
Node.js Alpine y servidor en Nginx Alpine, resultando en una imagen ligera
lista para producción.

**Optimizaciones de entrega**: compresión gzip para contenido textual, caché
de larga duración (1 año) para archivos estáticos con hash en el nombre, y
políticas de caché immutable para assets versionados.

**Configuración de red**: en producción, el frontend se sirve en el puerto 80
a través de Nginx, que enruta al backend en el puerto 3000. Los timeouts del
proxy están extendidos a 3600 segundos para solicitudes a la API que pueden
tomar tiempos prolongados (generación de reportes).

## Decisiones de diseño

### React con TypeScript

Se eligió React por su ecosistema maduro, su modelo de componentes
reutilizables y su capacidad para manejar actualizaciones de interfaz en
tiempo real de forma eficiente. TypeScript se adoptó para agregar tipado
estático, mejorando la detección temprana de errores y la documentación
implícita de las interfaces de datos entre componentes.

### Plotly.js para visualización científica

La visualización de espectro radioeléctrico requiere capacidades gráficas
específicas: gráficos de líneas con miles de puntos, zoom interactivo, ejes
con notación científica y rendimiento adecuado para actualizaciones en tiempo
real. Plotly.js fue seleccionada por su soporte nativo para estas
capacidades, su API declarativa compatible con React y su madurez en el
ámbito científico.

### Vite como empaquetador

La elección de Vite sobre alternativas como Webpack respondió a su velocidad
de compilación en desarrollo (basada en ESM nativo) y su configuración
simplificada. Para un equipo de desarrollo que itera rápidamente sobre la
interfaz, el tiempo de recarga en caliente es un factor significativo de
productividad.

### Tailwind CSS para estilos

Tailwind CSS fue seleccionado por su enfoque de utilidades atómicas, que
permite una iteración rápida sobre el diseño sin mantener archivos CSS
separados. En un proyecto con múltiples pantallas y componentes, este enfoque
reduce la fricción de mantener consistencia visual y facilita la colaboración.

### MSAL para autenticación institucional

La integración con Azure AD mediante MSAL responde al requerimiento
institucional de la ANE de utilizar las credenciales corporativas existentes.
MSAL maneja los flujos OAuth 2.0 / OIDC, la renovación silenciosa de tokens
y la persistencia de sesión, reduciendo la complejidad de implementación en
el frontend.

### Separación de Plotly en un chunk independiente

Plotly.js-dist-min es la dependencia de mayor tamaño en el bundle de
producción (~3 MB). La configuración de Vite la separa en un chunk
independiente, permitiendo que el resto de la aplicación se cargue y sea
interactiva sin esperar a que Plotly termine de descargarse. Esto mejora la
percepción de velocidad en el primer acceso.

## Problemas presentados y ajustes realizados

### Experiencia de carga inicial con dependencias pesadas

- **Problema**: la carga inicial de la aplicación era lenta debido al tamaño
  del bundle que incluía Plotly.js, afectando la primera impresión de las
  personas usuarias.
- **Evidencia**: mediciones de Lighthouse y tiempos de carga reportados por
  personas usuarias.
- **Causa**: Plotly.js se incluía en el bundle principal, bloqueando la
  renderización de la interfaz hasta que toda la librería estuviera
  descargada y parseada.
- **Ajuste**: configuración de división de código (code splitting) en Vite
  para separar Plotly en un chunk independiente cargado bajo demanda. Las
  pantallas que no usan gráficos de espectro (Inicio, Dispositivos, Alertas,
  Configuración) ya no esperan la carga de Plotly.
- **Resultado**: mejora significativa en el tiempo de carga inicial y en la
  puntuación de rendimiento, sin afectar la experiencia en las pantallas de
  monitoreo donde Plotly sí es necesario.

### Problemas de contenido mixto (Mixed Content)

- **Problema**: en el entorno de producción servido por HTTPS, las conexiones
  WebSocket y las solicitudes a la API generaban errores de contenido mixto
  cuando se usaban URLs absolutas con HTTP.
- **Evidencia**: errores en consola del navegador, fallos en la conexión
  WebSocket, datos en tiempo real no actualizándose.
- **Causa**: las URLs del backend estaban configuradas como absolutas en
  lugar de relativas, causando que el navegador bloqueara las solicitudes
  HTTP desde una página servida por HTTPS.
- **Ajuste**: configuración de URLs relativas para API (`/api`) y WebSocket
  (`/ws`) en las variables de entorno de compilación, delegando la resolución
  al proxy inverso Nginx que maneja ambas rutas en el mismo dominio.
- **Resultado**: eliminación de errores de contenido mixto, funcionamiento
  correcto de WebSocket y API en todos los entornos.

### Sincronización de estado entre pestañas

- **Problema**: al tener múltiples pestañas abiertas con la plataforma, el
  estado de autenticación y los datos en tiempo real no se sincronizaban
  entre ellas, generando inconsistencias (sesión cerrada en una pestaña pero
  activa en otra).
- **Evidencia**: reportes de personas usuarias, pruebas con múltiples
  pestañas.
- **Causa**: el estado de sesión y las conexiones WebSocket se gestionaban
  por pestaña sin mecanismo de coordinación entre instancias.
- **Ajuste**: revisión del flujo de autenticación en MSAL para garantizar que
  los eventos de login/logout se propaguen correctamente, y manejo adecuado
  de la renovación de tokens en todas las pestañas activas.
- **Resultado**: comportamiento consistente de la sesión
  independientemente del número de pestañas abiertas.

## Aprendizajes

1. **La división de código es crítica para aplicaciones con dependencias
   científicas**: las librerías de visualización como Plotly pueden dominar el
   tamaño del bundle. Planificar la división de código desde el inicio evita
   tener que resolver problemas de rendimiento cuando la aplicación ya está en
   uso.

2. **Las URLs relativas simplifican el despliegue en múltiples entornos**:
   usar URLs relativas para API y WebSocket permite que la misma compilación
   funcione en desarrollo local, VPN y producción sin reconfiguración,
   eliminando una fuente de errores de configuración.

3. **El manejo de autenticación debe contemplar múltiples pestañas**: en
   aplicaciones web modernas, las personas usuarias frecuentemente abren
   múltiples pestañas. El flujo de autenticación debe sincronizar el estado
   de sesión entre todas ellas, especialmente en los eventos de cierre de
   sesión y expiración de tokens.

4. **Tailwind CSS acelera la iteración de diseño**: en un proyecto con
   múltiples pantallas y componentes, el enfoque de utilidades atómicas reduce
   la fricción de mantener consistencia visual y permite que personas
   desarrolladoras se enfoquen en la funcionalidad sin crear y mantener
   archivos CSS separados.

5. **La elección de React fue acertada para una interfaz con datos en
   tiempo real**: el modelo de componentes y el Virtual DOM de React manejan
   eficientemente las actualizaciones frecuentes de datos provenientes del
   WebSocket, actualizando solo los componentes afectados sin re-renderizar
   toda la página.

## Limitaciones

1. **Tamaño de bundle con Plotly.js**: aunque se separa en un chunk
   independiente, Plotly.js sigue siendo una dependencia pesada (~3 MB) que
   afecta la primera visita a pantallas de monitoreo. No se ha evaluado la
   migración a alternativas más ligeras como ECharts o D3.js para las
   visualizaciones de espectro.

2. **Sin soporte offline**: la aplicación requiere conectividad constante
   con el backend para funcionar. No hay modo offline ni almacenamiento local
   de datos para consulta sin conexión.

3. **Sin diseño responsivo completo**: la interfaz está optimizada para
   pantallas de escritorio, que es el contexto de uso principal (estaciones
   de monitoreo). No se ha priorizado la adaptación a dispositivos móviles.

4. **Dependencia de servicios externos para mapas**: Leaflet carga tiles de
   mapa desde servicios externos (OpenStreetMap por defecto). En un entorno
   de red restringida, esto puede requerir configuración de un servidor de
   tiles local.

5. **Sin pruebas automatizadas de interfaz**: el desarrollo del frontend
   no incluye pruebas unitarias ni de integración automatizadas, dependiendo
   de verificación manual para validar cambios.

6. **Internacionalización no implementada**: la interfaz está en español
   sin soporte para cambio de idioma, lo cual es adecuado para el contexto
   actual pero limita la posibilidad de transferencia a entornos
   internacionales.

## Recomendaciones

1. **Evaluar alternativas a Plotly.js**: analizar si ECharts o una
   implementación con Canvas/WebGL puede ofrecer las mismas capacidades de
   visualización con un tamaño de bundle significativamente menor.

2. **Implementar pruebas automatizadas**: introducir pruebas unitarias con
   Vitest y pruebas de integración con Testing Library para garantizar que
   los cambios no introduzcan regresiones en flujos críticos como
   autenticación, monitoreo en vivo y gestión de campañas.

3. **Caché de datos frecuentes**: implementar una capa de caché local
   (localStorage o IndexedDB) para datos que cambian con poca frecuencia
   (catálogo de antenas, lista de sensores) reduciendo solicitudes
   repetitivas al backend.

4. **Modo offline limitado**: permitir la consulta de datos previamente
   cargados (último estado conocido de sensores, campañas recientes) cuando
   la conectividad con el backend se pierde temporalmente.

5. **Tiles de mapa autohospedados**: configurar un servidor de tiles local
   para eliminar la dependencia de servicios externos de mapas y garantizar
   el funcionamiento en entornos de red restringida.

6. **Monitoreo de rendimiento en el cliente**: integrar herramientas de
   Real User Monitoring (RUM) para detectar problemas de rendimiento
   experimentados por las personas usuarias en producción.

## Repositorio

| Campo | Valor |
|---|---|
| Nombre del software | ANE Frontend |
| Rama | main |
| Función en el sistema | Interfaz web para operación y administración de la plataforma de monitoreo espectral |
| Entradas | Interacciones de la persona usuaria, datos en tiempo real por WebSocket, respuestas de API REST |
| Salidas | Visualizaciones de espectro y mapas, formularios de configuración, reportes, audio en vivo |
| Dependencias | React 19, TypeScript, Vite, Tailwind CSS, Plotly.js, Leaflet, MSAL, Nginx |
| Estado actual | En producción en servidor institucional privado |
