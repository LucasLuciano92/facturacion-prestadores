# Pipeline de integración y entrega

| Etapa | Qué verifica | Qué ocurre si falla |
| --- | --- | --- |
| Sintaxis y estilo | Compilación y Ruff sobre módulos y pruebas | El job falla e informa el archivo y la regla |
| Pruebas unitarias | DNI, fechas, importes y duplicados | No se construye el paquete |
| Integración y regresión | Excel real, TXT, CSV, afiliados de prueba, reportes y DNI de siete dígitos | No se construye el paquete |
| Empaquetado | Construcción de wheel y distribución fuente | No se publica el artefacto |
| Ensayo | Instalación del wheel en entorno aislado y procesamiento de la muestra | No se publica el artefacto |
| Aprobación y producción | Revisión de resultados, versión y contrato de salida | Se conserva la versión anterior; no hay despliegue productivo automático |

Las cinco primeras verificaciones se implementan en `.github/workflows/ci.yml`.
La aprobación y el despliegue productivo son el diseño de entrega: este trabajo
no dispone de un servidor ni de un sistema real de liquidación.

La configuración del workflow comprueba los PR y `main`. Para impedir también
el merge mediante la interfaz de GitHub se debe configurar una regla de rama
que exija estos checks y revisión. Un workflow por sí solo no configura esa regla.

Las dependencias de ejecución y herramientas del workflow se fijan por versión.
El paquete se instala fuera del directorio del código fuente para comprobar
que no depende accidentalmente del checkout. La prueba de humo verifica los
conteos y el importe de la única fila aceptada.

No se suben credenciales ni una base real de afiliados. Una integración futura
debe guardar credenciales como secretos del entorno y verificar acceso a la base
antes de generar liquidaciones.
