"""Primera fase: extracción de responsabilidades sin corregir reglas heredadas.

Conserva las notificaciones por registro y las limitaciones de entrada del
fragmento original. Solo se usa para comparar el antes y el después.
"""

from datetime import datetime

TIPO_SECUENCIA = 1
POS_FECHA = 0
POS_DNI = 1
POS_CODIGO = 2
POS_IMPORTE = 3
PRIMER_TOPE = 0
MIN_DIGITOS = 7
MAX_DIGITOS = 8
MAX_DIAS = 60
ESTADO_BAJA = 2
FORMATO_FECHA = "%d/%m/%Y"
DESTINO_AUDITORIA = "auditoria@obrasocial.com"


def leer_dni(fila, tipo):
    if tipo == TIPO_SECUENCIA:
        return fila[POS_DNI].replace(".", "")
    return fila["DNI"].replace(".", "")


def longitud_admitida(dni):
    return MIN_DIGITOS <= len(dni) <= MAX_DIGITOS


def importe_hasta_tope(valor, tope):
    importe = float(valor)
    return importe if importe < tope else tope


class GestorFacturacion:
    def __init__(self, db, mail, pdf, reloj=datetime.now):
        self.db = db
        self.mail = mail
        self.pdf = pdf
        self.reloj = reloj

    def proc(self, filas, tipo):
        resultados = []
        for fila in filas:
            registro = self.liquidar_fila(fila, tipo)
            if registro is not None:
                resultados.append(registro)
                self.notificar_avance(resultados)
        return resultados

    def liquidar_fila(self, fila, tipo):
        dni = leer_dni(fila, tipo)
        if not longitud_admitida(dni):
            return None
        fecha = datetime.strptime(fila[POS_FECHA], FORMATO_FECHA)
        if (self.reloj() - fecha).days > MAX_DIAS:
            return None
        if self.db.buscar(dni).plan.cobertura.estado == ESTADO_BAJA:
            return None
        tope = self.db.buscar(dni).plan.cobertura.topes[PRIMER_TOPE]
        importe = importe_hasta_tope(fila[POS_IMPORTE], tope)
        return [dni, fecha, fila[POS_CODIGO], importe]

    def notificar_avance(self, resultados):
        self.mail.enviar(DESTINO_AUDITORIA, str(len(resultados)))
        self.pdf.generar(resultados)
