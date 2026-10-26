"""Cuenta la complejidad con la regla específica de la consigna del TP.

No suma except ni comprensiones; suma 1 por if, for, and, or y expresión
condicional. Cada función se mide de forma independiente.
"""

import ast
from pathlib import Path


def complejidad(funcion):
    total = 1
    for nodo in ast.walk(funcion):
        if isinstance(nodo, (ast.If, ast.For, ast.IfExp)):
            total += 1
        elif isinstance(nodo, ast.BoolOp):
            total += len(nodo.values) - 1
    return total


def medir(archivo):
    arbol = ast.parse(Path(archivo).read_text(encoding="utf-8"))
    return {n.name: complejidad(n) for n in ast.walk(arbol)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


if __name__ == "__main__":
    for archivo in ("tests/fixtures/gestor_legacy.py", "liquidacion_refactor.py", "liquidacion.py"):
        valores = medir(archivo)
        print(archivo, valores, "máxima:", max(valores.values()))
