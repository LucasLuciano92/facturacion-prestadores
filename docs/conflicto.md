# Conflicto entre las ramas de prestadores

Las dos ramas parten de la misma lista inicial: clínica, laboratorio e imágenes.
`feature/agrega-farmacia` incorpora farmacia y `feature/agrega-odontologia`
incorpora odontología sobre esa misma versión. Se integra farmacia en `main`
y luego se incorpora `main` a odontología. Git detecta un conflicto porque
ambas ramas modificaron la misma línea de `prestadores.py`.

La práctica se ejecutó y el conflicto se resolvió conservando ambas entradas:

```python
PRESTADORES = ["clinica", "laboratorio", "imagenes", "farmacia", "odontologia"]
```

Elegir solo una versión habría perdido la contribución de la otra rama.
Se quitaron los marcadores y se creó un commit de resolución con los dos
padres. Después se integró odontología a main.

La prueba `test_catalogo_conserva_ambas_contribuciones` comprueba los cinco
nombres y la ausencia de duplicados. El historial conserva ambas ramas y
la resolución. Los cambios de catálogo no agregan lectores de farmacia ni
odontología: el procesador mantiene los tres formatos de la primera versión.
