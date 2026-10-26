# Etapas 5 y 6

## Etapa 5

La referencia original está aislada en `tests/fixtures/gestor_legacy.py`.
`liquidacion_refactor.py` extrae nombres, constantes y funciones sin corregir
las reglas heredadas: mantiene los avisos por registro, el reloj inyectable y
la misma representación de resultados. La comparación supone filas estables
y una base de afiliados estable durante cada prueba.

`liquidacion.py` es una segunda fase de correcciones explícitas: reutiliza
`normalizar_dni`, `validar_fecha` y `normalizar_importe`, consulta una vez por
fila, registra rechazos, controla duplicados del lote y separa el cierre con
un correo y un PDF. Estos cambios NO se presentan como una refactorización
de comportamiento idéntico al legado. Se conserva la regla heredada de usar
el primer tope; auditoría debe confirmar su validez antes de pagos reales.

Las dos caracterizaciones son: afiliado de baja no se liquida; importe de
180000 con tope 120000 se liquida por 120000. Pasan sobre las tres versiones.
No prueban equivalencia universal. Los tests adicionales comprueban los
cambios intencionales y los límites de esta implementación.

### Métricas

Ejecutar `python medir_complejidad.py`. La regla del profesor suma 1 más cada
if, for, and, or y condicional de una línea. El máximo baja de 8 a 4 tanto en
la extracción como en la versión corregida. No se suman except con esta regla;
es una medida local del módulo y no de todo el proyecto.

El módulo original tiene ocho responsabilidades: adaptación de entrada,
DNI, fecha, consulta de afiliación, cálculo por tope, acumulación de salida,
correo y PDF. En la versión corregida la función con CC máxima es
`obtener_tope`: su responsabilidad es consultar y validar la cobertura.
Las once apariciones de números sin nombre del original se sustituyen por
constantes. La misma conversión de importe y la consulta de afiliado dejan
de repetirse en la versión corregida.

### Ejecución

```bash
python -m unittest discover -s tests -v
python medir_complejidad.py
```

La CLI existente sigue siendo el procesador de archivos de las etapas 1 a 4.
El módulo de topes es un ejercicio independiente, probado con dependencias
inyectadas; no está conectado a una base ni a servicios reales de correo/PDF.
No ejecuta pagos. El lote debe terminar antes de llamar a `cerrar_lote`.

### Deuda técnica

Tablero: https://trello.com/b/SkXhEpWE

- DT01: persistir lotes y claves para evitar repeticiones entre ejecuciones.
- DT02: sustituir consultas ficticias por integración real de afiliados.
- DT03: confirmar topes por práctica/plan/vigencia y persistir el cierre.

Las tres tarjetas se identifican como Deuda técnica y llevan la etiqueta
naranja. Su nombre nativo debe editarse en Trello a “Deuda técnica”. No hay
histórico persistente ni un outbox implementado. Una segunda ejecución del
mismo lote vuelve a aceptarlo; un test documenta esa limitación.

La revisión cruzada queda pendiente del equipo asignado y del checklist de
clase. No se registra una revisión externa ni una aprobación inexistente.

## Etapa 6

MVP elegido: clínica de punta a punta, con archivo original intacto, CSV de
válidos y reporte de rechazos. La implementación ya lee TXT y CSV, pero eso
no acredita aceptación de los tres prestadores. La demo usa datos de prueba.

Must para liberar un cierre real: clínica, validaciones, exportación,
rechazos, resumen mínimo, control histórico de duplicados, integración de
afiliados, nomenclador vigente, topes confirmados e informe de calidad.
Should: homologar laboratorio/imágenes y automatizar el cierre idempotente.
Could: resumen gerencial ampliado. Won't en este MVP: farmacia JSON,
odontología y aplicaciones móviles o integración bancaria.

Se prueba primero con las administrativas. Se medirá tiempo total del cierre
y de intervención manual, integridad de conteos, rechazos por motivo y
duplicados liquidados. El objetivo original sigue siendo pasar de cuatro a
un día hábil para los tres prestadores antes del cierre de noviembre; el
piloto de clínica no demuestra ese objetivo global.

Ante la salida de una desarrolladora y el adelanto de dos semanas elegimos B,
reducir alcance. Bajo el supuesto previo de cinco personas técnicas a seis
horas semanales, la capacidad de un sprint de dos semanas pasa de 60 a 48 h.
Se debe reestimar el tiempo restante; no se inventa una fecha acordada ni se
suprimen las pruebas. La demo del 02/11/2026 sigue siendo una demostración.

El incidente real agregado a V2 es la resonancia duplicada por $180000. P03
detecta duplicados dentro del lote; para evitar su repetición entre cierres
se necesita DT01 y una regresión de reenvío y concurrencia. Es un bloqueo
para producción, no una garantía ya implementada.
