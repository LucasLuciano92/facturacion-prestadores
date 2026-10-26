"""Segunda fase: reglas compartidas y cierre del lote sin envíos por fila.

No ejecuta pagos ni guarda liquidaciones entre ejecuciones. La integración con
repositorio, correo y PDF se inyecta; los tests usan dobles locales.
"""

from dataclasses import dataclass, field

from validaciones import normalizar_dni, normalizar_importe, validar_fecha

ESTADO_BAJA = 2
PRIMER_TOPE = 0
TIPO_SECUENCIA = 1
POS_FECHA = 0
POS_DNI = 1
POS_CODIGO = 2
POS_IMPORTE = 3
PRIMERA_FILA = 1
FORMATO_FECHA = "%d/%m/%Y"
DESTINO_AUDITORIA = "auditoria@obrasocial.com"


@dataclass
class ResultadoLiquidacion:
    aceptados: list = field(default_factory=list)
    rechazos: list = field(default_factory=list)


def adaptar_fila(fila, tipo):
    if tipo == TIPO_SECUENCIA:
        return {"DNI": fila[POS_DNI], "Fecha": fila[POS_FECHA],
                "Cod_Practica": fila[POS_CODIGO], "Importe": fila[POS_IMPORTE]}
    return fila


def normalizar_fila(fila, hoy):
    codigo = str(fila["Cod_Practica"] or "").strip()
    if not codigo:
        raise ValueError("Código de práctica vacío")
    return {"dni": normalizar_dni(fila["DNI"]),
            "fecha": validar_fecha(fila["Fecha"], FORMATO_FECHA, hoy),
            "codigo": codigo, "importe": normalizar_importe(fila["Importe"])}


class RepositorioCobertura:
    """Encapsula el acceso al modelo heredado; consulta una vez por fila."""

    def __init__(self, db):
        self.db = db

    def obtener_tope(self, dni):
        afiliado = self.db.buscar(dni)
        if afiliado is None:
            raise ValueError("Afiliado inexistente")
        cobertura = afiliado.plan.cobertura
        if cobertura.estado == ESTADO_BAJA:
            raise ValueError("Afiliado dado de baja")
        if not cobertura.topes:
            raise ValueError("Cobertura sin tope configurado")
        return normalizar_importe(cobertura.topes[PRIMER_TOPE])


class GestorFacturacion:
    def __init__(self, coberturas):
        self.coberturas = coberturas

    def liquidar_fila(self, fila, hoy):
        registro = normalizar_fila(fila, hoy)
        tope = self.coberturas.obtener_tope(registro["dni"])
        registro["importe"] = min(registro["importe"], tope)
        return registro

    def procesar(self, filas, tipo, hoy):
        resultado = ResultadoLiquidacion()
        vistos = set()
        for numero, fila in enumerate(filas, start=PRIMERA_FILA):
            try:
                registro = self.liquidar_fila(adaptar_fila(fila, tipo), hoy)
                clave = (registro["dni"], registro["fecha"], registro["codigo"])
                if clave in vistos:
                    raise ValueError("Práctica duplicada")
                vistos.add(clave)
                resultado.aceptados.append(registro)
            except (ValueError, KeyError, IndexError) as error:
                resultado.rechazos.append({"fila": numero, "motivo": str(error)})
        return resultado


def cerrar_lote(resultado, mail, pdf):
    """Un PDF y un correo por cierre; un error se propaga al llamador.

    No reintentar automáticamente: no hay idempotencia persistente para envíos.
    """
    pdf.generar(resultado.aceptados)
    mail.enviar(DESTINO_AUDITORIA, str(len(resultado.aceptados)))
