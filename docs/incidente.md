# Incidente simulado y prueba de regresión

El Centro de Imágenes rechaza una factura de un afiliado con DNI válido de
siete dígitos. El escenario se propone para el ejercicio y surge del código heredado:

```python
if len(dni) < 8 or not dni.isdigit():
    return None, "DNI inválido"
```

Esa condición rechaza siete dígitos y no limita por arriba los valores de nueve
o más dígitos. Las otras copias aplicaban un rango distinto.

La solución centraliza la validación en `normalizar_dni` y conecta los tres
adaptadores a la misma regla. La prueba
`test_dni_de_siete_y_ocho_digitos_en_tres_adaptadores` comprueba los límites de
seis, siete, ocho y nueve dígitos con los tres formatos de fecha.

La prueba unitaria de DNI detecta la condición incorrecta en la función común;
la regresión de los tres adaptadores detecta además que un prestador conserve
por error una copia divergente. Ambas comprobaciones se ejecutan antes de
empaquetar y publicar el artefacto.

En una situación real se identificarían los rechazos afectados y se acordaría
su reprocesamiento con el responsable, verificando que no se dupliquen pagos.
Este proyecto no simula un incidente real de una obra social ni conecta pagos.
