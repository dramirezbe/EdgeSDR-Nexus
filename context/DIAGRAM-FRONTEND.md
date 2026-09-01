# Flujo general del frontend

Este documento resume, en lenguaje simple, como se recorre el frontend de la plataforma ANE. La idea no es explicar el codigo, sino mostrar que ve y que decide una persona cuando entra a la aplicacion.

## Bloques principales

1. Ingreso a la plataforma
2. Pantalla principal con mapa y estado general
3. Revision de sensores y dispositivos
4. Monitoreo en vivo de una medicion
5. Creacion y consulta de campañas
6. Revision de alertas e incidentes
7. Reportes y resultados de medicion
8. Configuracion administrativa

## Diagrama: recorrido de una persona en la interfaz

```mermaid
flowchart TD
  ENTRY["Abrir la plataforma"]

  subgraph ACCESO["Ingreso"]
    LOGIN["Ingresar<br/>Microsoft Azure o acceso administrativo"]
    VALIDAR["Validar sesion"]
    SESION["Entrar al panel principal"]
    REINTENTAR["Volver a intentar ingreso"]
  end

  subgraph PANEL["Panel principal"]
    INICIO["Inicio<br/>vista general, mapa y estadisticas"]
    MENU["Menu lateral<br/>elige que quiere hacer"]
    DISPOSITIVOS["Revisar dispositivos<br/>ubicacion, estado y antenas"]
    MONITOREO["Monitorear en vivo<br/>medicion inmediata"]
    CAMPANAS["Trabajar con campañas<br/>programar, consultar y analizar"]
    ALERTAS["Revisar alertas<br/>incidentes y eventos"]
    CONFIG["Configurar plataforma<br/>solo administradores"]
    SALIR["Cerrar sesion"]
  end

  subgraph MEDICION["Cuando se monitorea en vivo"]
    SENSOR["Elegir sensor"]
    ANTENA["Elegir antena"]
    PARAMETROS["Definir parametros<br/>rango de frecuencia y tipo de medicion"]
    INICIAR["Iniciar adquisicion"]
    VER_DATOS["Ver datos en vivo<br/>espectro, vista temporal y audio si aplica"]
    DECIDIR["Decidir siguiente paso"]
    DETENER["Detener medicion"]
    GUARDAR_CAMPANA["Crear campaña<br/>con esa configuracion"]
  end

  subgraph RESULTADOS["Cuando se revisan resultados"]
    DATOS_CAMPANA["Ver datos de campaña"]
    REPORTE["Generar o revisar reporte"]
    CONCLUSIONES["Interpretar hallazgos<br/>cumple, alerta o requiere revision"]
  end

  ENTRY --> LOGIN
  LOGIN --> VALIDAR
  VALIDAR -->|sesion valida| SESION
  VALIDAR -->|sesion no valida| REINTENTAR
  REINTENTAR --> LOGIN

  SESION --> INICIO
  INICIO --> MENU
  MENU --> DISPOSITIVOS
  MENU --> MONITOREO
  MENU --> CAMPANAS
  MENU --> ALERTAS
  MENU --> CONFIG
  MENU --> SALIR

  DISPOSITIVOS -->|si se quiere medir un sensor| MONITOREO

  MONITOREO --> SENSOR
  SENSOR --> ANTENA
  ANTENA --> PARAMETROS
  PARAMETROS --> INICIAR
  INICIAR --> VER_DATOS
  VER_DATOS --> DECIDIR
  DECIDIR -->|terminar| DETENER
  DECIDIR -->|convertir en campaña| GUARDAR_CAMPANA
  GUARDAR_CAMPANA --> CAMPANAS

  CAMPANAS --> DATOS_CAMPANA
  DATOS_CAMPANA --> REPORTE
  ALERTAS --> REPORTE
  REPORTE --> CONCLUSIONES

  CONFIG --> DISPOSITIVOS
  CONFIG --> CAMPANAS
  SALIR --> LOGIN

  classDef entry fill:#fff,stroke:#111,stroke-width:2px,color:#000;
  classDef access fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px,color:#000;
  classDef screen fill:#e8f5e9,stroke:#43a047,stroke-width:2px,color:#000;
  classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#000;
  classDef result fill:#f3e8ff,stroke:#8b5cf6,stroke-width:2px,color:#000;

  class ENTRY entry;
  class LOGIN,VALIDAR,SESION,REINTENTAR access;
  class INICIO,MENU,DISPOSITIVOS,MONITOREO,CAMPANAS,ALERTAS,CONFIG,SALIR screen;
  class SENSOR,ANTENA,PARAMETROS,INICIAR,VER_DATOS,DECIDIR,DETENER,GUARDAR_CAMPANA action;
  class DATOS_CAMPANA,REPORTE,CONCLUSIONES result;
```

## Como leer el diagrama

La persona entra, se autentica y llega a una pantalla principal. Desde ahi decide si quiere revisar el estado general, mirar sensores, iniciar una medicion, trabajar con campañas, revisar alertas o administrar la plataforma.

El flujo central del frontend es la medicion: elegir sensor, elegir antena, definir parametros e iniciar adquisicion. Durante la medicion se ven datos en vivo. Luego se puede detener la medicion o usar esa configuracion para crear una campaña.

Las campañas y alertas llevan a resultados. La persona consulta mediciones, genera o revisa reportes y toma conclusiones sobre lo encontrado.

## Pantallas principales

- `Inicio`: vista general con mapa y estadisticas.
- `Dispositivos`: revision de sensores, ubicacion, estado y antenas asociadas.
- `Monitoreo`: configuracion y visualizacion de una medicion en vivo.
- `Campañas`: programacion, consulta y analisis de mediciones planificadas.
- `Alertas`: revision de eventos o incidentes detectados.
- `Configuracion`: administracion de antenas, sensores, usuarios y parametros generales.
- `Audio`: aparece asociado al monitoreo o a un sensor, no como tarea principal separada.

## Referencias del frontend usadas

- Entrada y rutas: `src/main.tsx`
- Sesion y permisos: `src/contexts/AuthContext.tsx`
- Pantalla principal: `src/App.tsx`
- Menu lateral: `src/components/Sidebar.tsx`
- Ingreso: `src/components/Login.tsx`
- Dispositivos: `src/components/MonitoringNetwork.tsx`
- Monitoreo: `src/components/ConfigurationPanel.tsx`, `src/components/AnalysisPanel.tsx`
- Campañas: `src/components/CampaignsList.tsx`, `src/components/CampaignModal.tsx`, `src/components/CampaignDataViewer.tsx`
- Alertas: `src/components/AlertsPanel.tsx`
- Configuracion: `src/components/AntennaManagement.tsx`, `src/components/UserManagement.tsx`
- Audio en vivo: `src/components/WebRTCAudioPlayer.tsx`, `src/pages/AudioPage.tsx`
