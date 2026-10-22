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

## Evidencia del ejercicio

- [Repositorio del equipo](https://github.com/LucasLuciano92/facturacion-prestadores).
- [Commit inicial común](https://github.com/LucasLuciano92/facturacion-prestadores/commit/ebc7434a264f531e9d11ad4f044ee988018cb621).
- [PR #1: incorporación de farmacia](https://github.com/LucasLuciano92/facturacion-prestadores/pull/1).
- [PR #2: incorporación de odontología y resolución del conflicto](https://github.com/LucasLuciano92/facturacion-prestadores/pull/2).
- [Commit de resolución con ambos padres](https://github.com/LucasLuciano92/facturacion-prestadores/commit/75a6df7a824ac081fe20e2398ef8a77999beb1fe).
- [PR #3: procesador, pruebas y automatización](https://github.com/LucasLuciano92/facturacion-prestadores/pull/3).

Las operaciones se realizaron con la cuenta propietaria del repositorio. El
historial evidencia la práctica de ramas e integración; no representa revisiones
independientes ni intervenciones de distintas cuentas de integrantes.
