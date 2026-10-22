"""Reglas compartidas por los tres formatos de facturación."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re


def normalizar_dni(valor):
    """Devuelve un DNI de siete u ocho dígitos, sin puntos."""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    dni = str(valor).strip().replace(".", "")
    if not re.fullmatch(r"[0-9]{7,8}", dni):
        raise ValueError("DNI inválido")
    return dni


def validar_fecha(valor, formato, hoy):
    """Admite desde hoy hasta sesenta días atrás, inclusive."""
    try:
        if isinstance(valor, datetime):
            fecha = valor.date()
        elif isinstance(valor, date):
            fecha = valor
        else:
            fecha = datetime.strptime(str(valor).strip(), formato).date()
    except (TypeError, ValueError):
        raise ValueError("Fecha inválida") from None
    if not 0 <= (hoy - fecha).days <= 60:
        raise ValueError("Fecha fuera de término")
    return fecha


def normalizar_importe(valor):
    """Convierte números de Excel o texto monetario argentino a Decimal."""
    if isinstance(valor, bool):
        raise ValueError("Importe inválido")
    if isinstance(valor, (int, float, Decimal)):
        texto = str(valor)
    else:
        texto = str(valor).strip().replace("$", "").replace(" ", "")
        patron = r"(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+)(?:,[0-9]{1,2})?"
        if not re.fullmatch(patron, texto):
            raise ValueError("Importe inválido")
        texto = texto.replace(".", "").replace(",", ".")
    try:
        importe = Decimal(texto)
        if not importe.is_finite() or importe <= 0:
            raise ValueError("Importe inválido")
        if importe != importe.quantize(Decimal("0.01")):
            raise ValueError("El importe tiene más de dos decimales")
    except InvalidOperation:
        raise ValueError("Importe inválido") from None
    return importe.quantize(Decimal("0.01"))
