# Procesador de facturación de prestadores médicos

Trabajo Práctico Unidad 3 · Metodologías de Sistemas 2 · Grupo N.º 2.

Lee la facturación de Clínica San Martín en Excel, Laboratorio Bioan en TXT
de ancho fijo y Centro de Imágenes Delta en CSV. Normaliza los datos,
verifica las reglas del caso y genera una liquidación con los registros válidos
y un reporte de rechazos por prestador.

## Equipo

| Rol | Integrante |
| --- | --- |
| Product Owner | Nicolás Ventureira |
| Facilitador | Julián Tesoreiro |
| Desarrollo | Juan Zunino |
| Desarrollo | Lucas Lautaro Luciano |
| Desarrollo | Emir Negrete |
| Desarrollo | Esposito Lautaro |
| Desarrollo y pruebas | Norali Gorosito |

## Ejecutar

Requiere Python 3.11 o superior. Los archivos de `datos/` son muestras
académicas; no contienen una base real de afiliados.

```bash
python -m venv .venv
# Linux o macOS:
source .venv/bin/activate
# PowerShell, como alternativa:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python procesador.py --clinica datos/clinica.xlsx --afiliados datos/afiliados.json --fecha 2026-10-15 --salida salida/clinica
```

Resultado de la muestra de clínica: **5 recibidos, 1 aceptado, 4 rechazados**.
La fecha se recibe como parámetro para que el resultado de las pruebas no
cambie con el día en que se ejecutan.

Para procesar los tres formatos en un mismo lote:

```bash
python procesador.py --clinica datos/clinica.xlsx --laboratorio datos/laboratorio.txt --imagenes datos/imagenes.csv --afiliados datos/afiliados.json --fecha 2026-10-15 --salida salida/completo
```

Se obtienen `liquidacion.csv`, `rechazos_clinica.csv`,
`rechazos_laboratorio.csv`, `rechazos_imagenes.csv` y `resumen.json`.
El CSV de liquidación usa UTF-8, separador `;`, fecha `AAAA-MM-DD` e importe
con punto decimal y dos decimales. Este es el contrato elegido para el ejercicio.

Los archivos de entrada no se modifican. Cada ejecución genera una salida nueva
del lote; no se conecta a un sistema real de pagos ni conserva liquidaciones
anteriores. Para uso real se necesita persistencia e idempotencia entre lotes.

## Reglas y formatos

- DNI: siete u ocho dígitos numéricos, sin puntos después de normalizar.
- Afiliación: estado `activo` en el archivo de consulta; `baja` o ausencia se rechazan.
- Fechas: entre la fecha de ejecución y sesenta días atrás, inclusive.
- Importe: positivo, con dos decimales como máximo, procesado con `Decimal`.
- Duplicado: mismo DNI normalizado, fecha y código. Se conserva el primer
  registro que pasó **todas** las validaciones.
- El orden del lote es clínica, laboratorio e imágenes. La clave se comparte
  entre los tres prestadores durante esa ejecución.
- Si la base de afiliados no se puede leer o tiene un formato inválido,
  se interrumpe el lote sin emitir una nueva liquidación.

Excel acepta los encabezados originales y alias definidos en `ALIAS`.
Los encabezados desconocidos o ambiguos para campos obligatorios detienen el archivo.
Las celdas de importe numéricas se distinguen del texto monetario argentino.

El TXT usa exactamente 34 caracteres: DNI en posiciones 1–8, fecha AAAAMMDD
en 9–16, código en 17–24 e importe en centavos en 25–34. DNI de siete dígitos
y códigos de menos de ocho caracteres se completan con espacios a la derecha.
La posición de código e importe corresponde al código heredado de la consigna.

El CSV de imágenes usa `;` y cuatro columnas en este orden: fecha DD-MM-AAAA,
DNI, código e importe con coma decimal. Admite una primera fila de encabezado.

## Pruebas

```bash
python -m unittest discover -s tests -v
python -m compileall -q procesador.py prestadores.py validaciones.py tests
```

| Caso del TP | Implementación |
| --- | --- |
| P01 · DNI | Normalización, siete y ocho dígitos válidos; límites y valores inválidos |
| P02 · Clínica completa | Se crea y lee un Excel real con las cinco filas; se verifican liquidación, rechazos y conteos |
| P03 · Duplicados | DNI con y sin puntos, y primera fila inválida que no reserva la clave |
| Regresión del incidente | DNI de seis, siete, ocho y nueve dígitos en los tres adaptadores |

También se prueban límites de fechas, precisión monetaria, alias, errores de
estructura, consulta de afiliados y duplicados entre prestadores.

## Ejercicio de Git

Las ramas `feature/agrega-farmacia` y `feature/agrega-odontologia` parten de
la misma versión inicial de `prestadores.py` y modifican la misma línea.
Al incorporar farmacia en `main`, odontología queda en conflicto. La resolución
conserva las dos entradas:

```python
PRESTADORES = ["clinica", "laboratorio", "imagenes", "farmacia", "odontologia"]
```

Farmacia y odontología se incorporan **al catálogo del ejercicio Git**.
No tienen lectores implementados y no amplían la primera versión de tres formatos.
La resolución y su justificación se documentan en [docs/conflicto.md](docs/conflicto.md).

## Automatización y entrega

GitHub Actions ejecuta comprobación de sintaxis y estilo, pruebas automáticas,
construcción del paquete e instalación del paquete en un entorno limpio con una
prueba de humo. Un fallo impide que las etapas dependientes continúen.

El detalle de cada etapa está en [docs/pipeline.md](docs/pipeline.md).
Se publica un artefacto de prueba, sin desplegar en una infraestructura real ni
emitir liquidaciones contra servicios externos. El paso a producción se diseña
con aprobación del responsable y posibilidad de volver a una versión anterior.

## Estructura

```text
prestadores.py           Catálogo y ejercicio de ramas
validaciones.py          DNI, fechas e importes
procesador.py            Lectores, reglas del lote y exportación
tests/                  Pruebas unitarias, integración y regresión
datos/                  Muestras académicas de los tres formatos y afiliados
docs/                   Conflicto, pipeline e incidente
.github/workflows/      Integración continua y verificación del paquete
```
