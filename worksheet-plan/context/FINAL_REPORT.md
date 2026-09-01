# README — Informe Final del Sistema

## 1. Propósito del repositorio

Este repositorio contiene la estructura base para construir el **informe final del sistema** mediante capítulos escritos por diferentes autores.

El documento final debe funcionar como:

- Memoria técnica del sistema.
- Documento de integración de módulos.
- Registro de decisiones de diseño.
- Registro de problemas, ajustes y aprendizajes.
- Instrumento de transferencia de conocimiento.
- Base para que otros puedan comprender, mantener, reproducir o continuar el desarrollo.

La escritura del informe se organizará de forma modular:

```text
main.tex                 Archivo maestro. Solo debe modificarlo el integrador.
README.md                Guía oficial de escritura, formato y procedimiento.
section/                 Carpeta con un archivo .tex por capítulo.
section/img/             Carpeta de imágenes y evidencias gráficas.
```

Cada autor editará **únicamente el archivo `.tex` de su capítulo asignado**.  
El archivo `main.tex` se encargará de ensamblar todos los capítulos.

---

## 2. Regla principal de trabajo

El informe final no debe ser una suma de textos aislados. Cada capítulo debe explicar:

1. Qué función cumple el tema dentro del sistema.
2. Cómo fue diseñado, implementado, estructurado o evaluado.
3. Qué entradas, salidas, interfaces o dependencias tiene.
4. Qué decisiones técnicas se tomaron.
5. Qué problemas se presentaron.
6. Cómo se decidió qué ajuste o cambio aplicar.
7. Qué evidencia demuestra el funcionamiento o avance.
8. Qué aprendizajes prácticos quedan para transferir conocimiento.
9. Qué limitaciones existen.
10. Qué recomendaciones se proponen.

La idea central es documentar:

```text
Problema observado → Evidencia → Causa probable → Decisión → Ajuste → Resultado → Aprendizaje
```

---

## 3. Archivos y responsabilidades

### 3.1 Archivos que NO deben editar todos los autores

| Archivo | Responsable | Uso |
|---|---|---|
| `main.tex` | Integrador | Ensambla el informe, define formato y carga capítulos |
| `README.md` | Integrador | Define reglas de trabajo, escritura y entrega |

### 3.2 Archivos que sí edita cada autor

Cada autor edita únicamente el archivo de su capítulo dentro de `section/`.

Ejemplo:

```text
section/5_SDR-acquisition.tex
```

Cada autor debe evitar modificar:

- `main.tex`
- `README.md`
- capítulos de otros autores
- carpetas de imágenes de otros capítulos

---

## 4. Estructura recomendada del repositorio

```text
/
├── README.md
├── main.tex
└── section/
    ├── 1_introduction.tex
    ├── 2_requirements-restrictions.tex
    ├── 3_general_design_system.tex
    ├── 4_HW.tex
    ├── 5_SDR-acquisition.tex
    ├── 6_Platform_cloud.tex
    ├── 7_Spectral-localization_cloud.tex
    ├── 8_Test_protocols_edge-cloud.tex
    ├── 9_System_integration.tex
    ├── 10_General_conclusions.tex
    ├── 11_Recommendations.tex
    ├── 12_References.tex
    ├── A_IA-collaboration-technique.tex
    ├── B_Additional_diagrams.tex
    ├── C_Relevant_code_fragments.tex
    ├── D_Manuals_guides.tex
    ├── E_Test_results.tex
    └── img/
        ├── cap01_introduction/
        ├── cap02_requirements/
        ├── cap03_design/
        ├── cap04_hw/
        ├── cap05_sdr/
        ├── cap06_cloud_platform/
        ├── cap07_spectral_localization/
        ├── cap08_tests/
        ├── cap09_integration/
        └── annexes/
```

---

## 5. Distribución sugerida de capítulos

| Archivo | Capítulo | Responsable sugerido |
|---|---|---|
| `section/1_introduction.tex` | Introducción general | Integrador |
| `section/2_requirements-restrictions.tex` | Análisis de requerimientos, restricciones y uso | Autor de requerimientos |
| `section/3_general_design_system.tex` | Diseño general del sistema | Autor de arquitectura |
| `section/4_HW.tex` | Hardware | Autor de hardware |
| `section/5_SDR-acquisition.tex` | SDR: adquisición y preprocesamiento en borde | Autor SDR/borde |
| `section/6_Platform_cloud.tex` | Plataforma web en la nube | Autor plataforma web |
| `section/7_Spectral-localization_cloud.tex` | Análisis espectral y localización en la nube | Autor análisis cloud |
| `section/8_Test_protocols_edge-cloud.tex` | Protocolos de prueba en nube y borde | Autor de pruebas |
| `section/9_System_integration.tex` | Integración general del sistema | Integrador técnico |
| `section/10_General_conclusions.tex` | Conclusiones generales | Integrador |
| `section/11_Recommendations.tex` | Recomendaciones | Integrador |
| `section/12_References.tex` | Referencias | Integrador con insumos de todos |
| `section/A_IA-collaboration-technique.tex` | Técnica de desarrollo en grupo usando agentes IA | Autor anexo IA |
| `section/B_Additional_diagrams.tex` | Diagramas adicionales | Integrador |
| `section/C_Relevant_code_fragments.tex` | Fragmentos conceptuales o referencias a código | Integrador |
| `section/D_Manuals_guides.tex` | Manuales o guías de uso | Integrador / autor operativo |
| `section/E_Test_results.tex` | Resultados de pruebas | Autor de pruebas / integrador |

---

## 6. Estructura obligatoria de cada capítulo técnico

Cada archivo de capítulo debe iniciar con `\chapter{...}` y debe contener, como mínimo, las siguientes secciones:

```latex
\chapter{Título del capítulo}

\section{Propósito del capítulo}
\section{Contexto dentro del sistema general}
\section{Desarrollo técnico}
\section{Entradas, salidas e interfaces}
\section{Decisiones de diseño o implementación}
\section{Problemas presentados y ajustes realizados}
\section{Validación, pruebas o evidencias}
\section{Aprendizajes y transferencia de conocimiento}
\section{Limitaciones}
\section{Recomendaciones específicas}
```

Los capítulos transversales como introducción, conclusiones, recomendaciones y referencias pueden tener una estructura diferente, pero deben conservar coherencia con el informe.

---

## 7. Plantilla mínima para un capítulo

Cada autor puede usar esta plantilla dentro de su archivo `.tex`:

```latex
\chapter{Título del capítulo}

\section{Propósito del capítulo}
Describir qué documenta el capítulo y por qué es importante para el informe final.

\section{Contexto dentro del sistema general}
Explicar cómo se conecta este tema con los demás módulos del sistema.

\section{Desarrollo técnico}
Presentar arquitectura, metodología, componentes, parámetros, herramientas, modelos o criterios técnicos.

\section{Entradas, salidas e interfaces}
Describir qué recibe, qué procesa, qué entrega y con qué otros módulos se comunica.

\section{Decisiones de diseño o implementación}
Explicar decisiones tomadas, alternativas consideradas y justificación de la opción elegida.

\section{Problemas presentados y ajustes realizados}
Documentar problemas, evidencias, causas, decisiones, ajustes, resultados y aprendizajes.

\begin{longtable}{p{2.7cm} p{2.7cm} p{2.7cm} p{3cm} p{3cm}}
\caption{Problemas presentados, decisiones y ajustes realizados.}\\
\toprule
\textbf{Problema} & \textbf{Evidencia} & \textbf{Causa probable} & \textbf{Decisión o ajuste} & \textbf{Resultado} \\
\midrule
\endfirsthead
\toprule
\textbf{Problema} & \textbf{Evidencia} & \textbf{Causa probable} & \textbf{Decisión o ajuste} & \textbf{Resultado} \\
\midrule
\endhead
Problema identificado & Log, captura, prueba o medición & Causa técnica probable & Cambio aplicado y justificación & Resultado posterior \\
\bottomrule
\end{longtable}

\section{Validación, pruebas o evidencias}
Describir pruebas realizadas, resultados esperados, resultados obtenidos y evidencias.

\section{Aprendizajes y transferencia de conocimiento}
Registrar aprendizajes prácticos, buenas prácticas y errores frecuentes.

\section{Limitaciones}
Indicar restricciones, condiciones de operación y problemas no resueltos.

\section{Recomendaciones específicas}
Proponer mejoras futuras o acciones recomendadas.
```

---

## 8. Contenido esperado por capítulo

### 8.1 Análisis de requerimientos, restricciones y uso

Debe incluir:

- Propósito del sistema.
- Usuarios o actores principales.
- Casos de uso.
- Requerimientos funcionales.
- Requerimientos no funcionales.
- Restricciones técnicas, operativas y económicas.
- Supuestos.
- Criterios de aceptación.
- Riesgos.
- Problemas encontrados al definir requerimientos.
- Ajustes realizados sobre el alcance.
- Aprendizajes sobre el uso esperado del sistema.

### 8.2 Diseño general del sistema

Debe incluir:

- Arquitectura general.
- Diagrama de bloques.
- Flujo de datos extremo a extremo.
- Separación entre borde y nube.
- Interfaces entre módulos.
- Decisiones de diseño.
- Alternativas consideradas.
- Riesgos arquitectónicos.
- Problemas de integración previstos o encontrados.
- Aprendizajes sobre diseño modular.

### 8.3 Hardware

Debe incluir:

- Lista de componentes.
- Función de cada componente.
- Diagrama de conexión.
- Alimentación y consumo.
- Conectividad.
- Restricciones físicas.
- Limitaciones de hardware.
- Problemas presentados.
- Ajustes realizados.
- Recomendaciones de operación.

### 8.4 SDR: adquisición y preprocesamiento en borde

Debe incluir:

- Función del módulo SDR.
- Parámetros de adquisición.
- Frecuencia central.
- Sample rate.
- Ganancia.
- Número de muestras.
- NFFT, si aplica.
- Flujo de adquisición.
- Preprocesamiento aplicado.
- Formato de salida.
- Comunicación con la nube.
- Problemas presentados.
- Ajustes realizados.
- Evidencias.
- Enlace al repositorio real del software.

### 8.5 Plataforma web en la nube

Debe incluir:

- Propósito de la plataforma.
- Usuarios y roles.
- Funcionalidades.
- Arquitectura web.
- Frontend.
- Backend.
- Base de datos.
- APIs.
- Visualizaciones.
- Seguridad y control de acceso.
- Despliegue cloud.
- Problemas y ajustes.
- Enlace al repositorio real del software.

### 8.6 Análisis espectral y localización en la nube

Debe incluir:

- Datos de entrada.
- Flujo de procesamiento.
- Estimación espectral.
- PSD, Welch, FFT u otros métodos si aplican.
- Detección de emisiones o eventos.
- Estimación de frecuencia central.
- Estimación de ancho de banda.
- Localización o estimación espacial.
- Parámetros configurables.
- Resultados generados.
- Validación.
- Problemas y ajustes.
- Enlace al repositorio real del software.

### 8.7 Protocolos de prueba en nube y borde

Debe incluir:

- Objetivo de las pruebas.
- Alcance.
- Ambiente de prueba.
- Pruebas del módulo de borde.
- Pruebas del módulo cloud.
- Pruebas de la plataforma web.
- Pruebas de integración extremo a extremo.
- Métricas.
- Criterios de aceptación.
- Evidencias.
- Problemas encontrados durante pruebas.
- Ajustes derivados de pruebas.

### 8.8 Integración general del sistema

Debe incluir:

- Flujo completo de operación.
- Dependencias entre módulos.
- Secuencia de ejecución.
- Formatos de intercambio.
- Estado actual de integración.
- Problemas de integración.
- Ajustes realizados.
- Aprendizajes de coordinación técnica.

### 8.9 Aprendizajes y transferencia de conocimiento

Los aprendizajes deben aparecer en cada capítulo. Además, el integrador puede consolidarlos en un capítulo o anexo.

Deben incluir:

- Errores frecuentes.
- Buenas prácticas.
- Conocimiento reutilizable.
- Recomendaciones para nuevos integrantes.
- Reproducción de pruebas.
- Matriz de transferencia de conocimiento.

---

## 9. Figuras, diagramas y gráficas

Todas las figuras deben guardarse en:

```text
section/img/capXX_nombre/
```

Ejemplo:

```text
section/img/cap05_sdr/flujo_adquisicion.png
```

Para insertar una figura:

```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=0.85\textwidth]{section/img/cap05_sdr/flujo_adquisicion.png}
    \caption{Flujo de adquisición y preprocesamiento SDR en borde. Fuente: elaboración propia.}
    \label{fig:flujo_adquisicion_sdr}
\end{figure}
```

Toda figura debe:

- Tener `\caption{...}`.
- Tener `\label{...}`.
- Ser mencionada en el texto.
- Indicar fuente.
- Ser explicada.

Ejemplo de referencia en texto:

```latex
La Figura~\ref{fig:flujo_adquisicion_sdr} muestra el flujo de adquisición desde la configuración del SDR hasta el envío de datos hacia la nube.
```

---

## 10. Tablas

Las tablas deben estar escritas en LaTeX. No deben insertarse como imágenes.

Ejemplo:

```latex
\begin{table}[H]
\centering
\caption{Parámetros principales de adquisición SDR.}
\label{tab:parametros_sdr}
\begin{tabularx}{\textwidth}{>{\bfseries}l X X}
\toprule
Parámetro & Valor & Justificación \\
\midrule
Frecuencia central & 98 MHz & Banda de prueba inicial. \\
Sample rate & 2.4 MS/s & Compatible con el receptor usado. \\
Ganancia & 29.7 dB & Balance entre sensibilidad y saturación. \\
\bottomrule
\end{tabularx}
\end{table}
```

Toda tabla debe:

- Tener título.
- Tener `\label{...}`.
- Tener unidades cuando aplique.
- Ser mencionada en el texto.
- Ser editable en LaTeX.

---

## 11. Software y repositorios

Si se menciona software, scripts, notebooks, módulos, APIs, plataformas, librerías propias o herramientas desarrolladas por el grupo, **no se debe incluir código fuente completo dentro del informe final**.

Debe incluirse:

- Nombre del software.
- Repositorio real.
- Rama, versión o commit.
- Responsable.
- Función dentro del sistema.
- Entradas.
- Salidas.
- Dependencias principales.
- Estado actual.

Formato recomendado:

```latex
\begin{table}[H]
\centering
\caption{Repositorio asociado al componente de software.}
\label{tab:repo_nombre}
\begin{tabularx}{\textwidth}{>{\bfseries}l X}
\toprule
Nombre del software & Nombre del módulo \\
Repositorio & \url{https://github.com/organizacion/repositorio-real} \\
Rama, versión o commit & main / commit pendiente de especificar \\
Responsable & Nombre del responsable \\
Función dentro del sistema & Descripción breve \\
Entradas & Datos o parámetros de entrada \\
Salidas & Resultados o datos generados \\
Estado actual & Funcional / en pruebas / pendiente de integración \\
\bottomrule
\end{tabularx}
\end{table}
```

Si el repositorio todavía no existe, escribir:

```text
Repositorio pendiente de publicación.
```

No inventar enlaces.

---

## 12. Código fuente

Regla general:

> El informe explica el software; el repositorio contiene el código.

No se deben incluir bloques largos de código en el informe.

Se permiten únicamente:

- Comandos muy breves de instalación o ejecución.
- Pseudocódigo conceptual corto.
- Fragmentos mínimos necesarios para explicar una configuración.

Todo código fuente completo debe estar en el repositorio real correspondiente.

---

## 13. Referencias

Cada autor debe informar al integrador las fuentes usadas.

Pueden citarse:

- Manuales técnicos.
- Datasheets.
- Documentación oficial.
- Libros.
- Artículos científicos.
- Normas.
- Repositorios.
- Documentación de librerías.
- Documentación de APIs.

Las referencias se consolidarán en:

```text
section/12_References.tex
```

Se recomienda mantener un estilo único, preferiblemente IEEE.

---

## 14. Flujo de trabajo recomendado con GitHub

### Opción recomendada: una rama por autor

Cada autor crea una rama para su capítulo:

```bash
git checkout -b cap05-sdr-borde
```

Edita solo su archivo:

```text
section/5_SDR-acquisition.tex
```

Agrega imágenes solo en su carpeta:

```text
section/img/cap05_sdr/
```

Luego guarda cambios:

```bash
git add section/5_SDR-acquisition.tex section/img/cap05_sdr/
git commit -m "Completa capítulo SDR adquisición en borde"
git push origin cap05-sdr-borde
```

Después crea un Pull Request hacia `main`.

---

## 15. Flujo alternativo si los autores no usan Git

1. El integrador entrega a cada autor su archivo `.tex`.
2. El autor edita únicamente ese archivo.
3. El autor devuelve el archivo y sus imágenes.
4. El integrador reemplaza el archivo correspondiente en `section/`.
5. El integrador compila el documento completo.

---

## 16. Cómo compilar

Desde la raíz del repositorio:

```bash
pdflatex main.tex
pdflatex main.tex
```

Se compila dos veces para actualizar:

- tabla de contenido,
- numeración de figuras,
- numeración de tablas,
- referencias cruzadas.

En Overleaf:

1. Subir el repositorio.
2. Definir `main.tex` como archivo principal.
3. Compilar.
4. Corregir errores reportados.

---

## 17. Checklist para cada autor

Antes de entregar, cada autor debe verificar:

```text
[ ] Leí este README.
[ ] Edité únicamente mi archivo de capítulo.
[ ] No modifiqué main.tex.
[ ] No modifiqué capítulos ajenos.
[ ] Eliminé los \pendiente{} de mi capítulo.
[ ] Incluí propósito del capítulo.
[ ] Expliqué contexto dentro del sistema general.
[ ] Desarrollé el contenido técnico.
[ ] Describí entradas, salidas e interfaces.
[ ] Justifiqué decisiones técnicas.
[ ] Documenté problemas, evidencias, causas, ajustes y resultados.
[ ] Incluí pruebas o evidencias.
[ ] Incluí aprendizajes y transferencia de conocimiento.
[ ] Incluí limitaciones.
[ ] Incluí recomendaciones.
[ ] Las figuras tienen caption, label, fuente y explicación.
[ ] Las tablas son editables en LaTeX.
[ ] Las gráficas tienen ejes, unidades e interpretación.
[ ] No incluí código fuente completo.
[ ] Si mencioné software, agregué repositorio real o indiqué que está pendiente.
[ ] Informé las referencias usadas.
[ ] Mi capítulo compila o fue revisado con el integrador.
```

---

## 18. Checklist para el integrador

Antes de generar la versión final, el integrador debe verificar:

```text
[ ] main.tex compila correctamente.
[ ] Todos los archivos incluidos en main.tex existen.
[ ] No quedan \pendiente{} sin resolver.
[ ] Todos los capítulos tienen estructura homogénea.
[ ] No hay capítulos aislados sin conexión con el sistema.
[ ] Las figuras existen en las rutas indicadas.
[ ] Las tablas no se salen de página.
[ ] Las referencias cruzadas funcionan.
[ ] No hay código fuente largo dentro del informe.
[ ] Los repositorios mencionados son reales o dicen “Repositorio pendiente de publicación”.
[ ] Las referencias están consolidadas.
[ ] El capítulo de integración conecta todos los módulos.
[ ] Las conclusiones se derivan del contenido documentado.
[ ] Las recomendaciones son coherentes con problemas y limitaciones.
```

---

## 19. Convenciones de redacción

Preferir frases como:

- “El módulo cumple la función de...”
- “La decisión se tomó debido a...”
- “La evidencia observada fue...”
- “El problema identificado corresponde a...”
- “El ajuste realizado consistió en...”
- “El resultado posterior fue...”
- “El aprendizaje derivado de esta prueba fue...”

Evitar:

- “Se hicieron pruebas” sin explicar cuáles.
- “El sistema funciona” sin evidencia.
- Figuras sin descripción.
- Tablas sin unidades.
- Código largo dentro del informe.
- Enlaces inventados.
- Referencias incompletas.
- Texto genérico sin relación con el sistema.

---

## 20. Criterio final de calidad

Un capítulo está listo para integrarse si una persona externa al desarrollo puede leerlo y entender:

1. Qué componente o tema se está documentando.
2. Cómo se conecta con el sistema.
3. Cómo funciona.
4. Qué decisiones se tomaron.
5. Qué problemas aparecieron.
6. Qué ajustes se aplicaron.
7. Qué evidencia respalda el resultado.
8. Qué aprendió el equipo.
9. Dónde consultar el software real.
10. Qué queda pendiente o puede mejorarse.
