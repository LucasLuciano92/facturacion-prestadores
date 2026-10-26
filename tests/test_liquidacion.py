"""Caracterización del legado y pruebas de cambios intencionales de la etapa 5."""

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from liquidacion import GestorFacturacion, RepositorioCobertura, cerrar_lote
from liquidacion_refactor import GestorFacturacion as GestorRefactor
from tests.fixtures.gestor_legacy import GestorFacturacion as GestorLegacy

HOY = date(2026, 10, 15)
AHORA = datetime(2026, 10, 15, 12)
FILA = ["03/10/2026", "30.125.448", "420101", "180000"]


def base_de_prueba(estado=1, topes=None):
    topes = [120000] if topes is None else topes
    cobertura = SimpleNamespace(estado=estado, topes=topes)
    afiliado = SimpleNamespace(plan=SimpleNamespace(cobertura=cobertura))
    return Mock(buscar=Mock(return_value=afiliado))


def ejecutar_original(db, filas):
    gestor = GestorLegacy()
    gestor.db, gestor.mail, gestor.pdf = db, Mock(), Mock()
    with patch("tests.fixtures.gestor_legacy.datetime") as reloj:
        reloj.now.return_value = AHORA
        reloj.strptime.side_effect = datetime.strptime
        resultado = gestor.proc(filas, 1)
    return resultado, gestor


class CaracterizacionTests(unittest.TestCase):
    def test_c01_baja_no_se_liquida_en_las_tres_versiones(self):
        original, _ = ejecutar_original(base_de_prueba(estado=2), [FILA])
        refactor = GestorRefactor(base_de_prueba(estado=2), Mock(), Mock(), lambda: AHORA)
        nuevo = GestorFacturacion(RepositorioCobertura(base_de_prueba(estado=2)))
        self.assertEqual(original, [])
        self.assertEqual(refactor.proc([FILA], 1), original)
        resultado = nuevo.procesar([FILA], 1, HOY)
        self.assertEqual(resultado.aceptados, [])
        self.assertIn("baja", resultado.rechazos[0]["motivo"])

    def test_c02_importe_mayor_al_tope_se_limita_en_las_tres_versiones(self):
        original, _ = ejecutar_original(base_de_prueba(), [FILA])
        refactor = GestorRefactor(base_de_prueba(), Mock(), Mock(), lambda: AHORA)
        nuevo = GestorFacturacion(RepositorioCobertura(base_de_prueba()))
        self.assertEqual(original[0][3], 120000)
        self.assertEqual(refactor.proc([FILA], 1), original)
        self.assertEqual(nuevo.procesar([FILA], 1, HOY).aceptados[0]["importe"],
                         Decimal("120000.00"))

    def test_refactor_conserva_avisos_por_fila_y_tipo_del_tope(self):
        filas = [FILA, ["04/10/2026", "35111222", "420101", "120000"]]
        original, gestor_original = ejecutar_original(base_de_prueba(), filas)
        refactor = GestorRefactor(base_de_prueba(), Mock(), Mock(), lambda: AHORA)
        resultado = refactor.proc(filas, 1)
        self.assertEqual(resultado, original)
        self.assertIs(type(resultado[1][3]), type(original[1][3]))
        self.assertEqual(refactor.mail.enviar.call_args_list,
                         gestor_original.mail.enviar.call_args_list)
        self.assertEqual(refactor.pdf.generar.call_count, 2)


class LiquidacionTests(unittest.TestCase):
    def setUp(self):
        self.db = base_de_prueba()
        self.gestor = GestorFacturacion(RepositorioCobertura(self.db))

    def test_consulta_una_vez_y_cierra_con_un_mail_y_un_pdf(self):
        resultado = self.gestor.procesar(
            [FILA, ["04/10/2026", "35111222", "420101", "100"]], 1, HOY)
        self.assertEqual(self.db.buscar.call_count, 2)
        mail, pdf = Mock(), Mock()
        mail.enviar.side_effect = lambda *args: self.assertEqual(pdf.generar.call_count, 1)
        cerrar_lote(resultado, mail, pdf)
        mail.enviar.assert_called_once_with("auditoria@obrasocial.com", "2")
        pdf.generar.assert_called_once_with(resultado.aceptados)

    def test_dni_fecha_importe_incorrectos_dejan_motivo(self):
        filas = [["03/10/2026", "abcdefgh", "420101", "100"],
                 ["16/10/2026", "30125448", "420101", "100"],
                 ["03/10/2026", "30125448", "420101", "-100"]]
        resultado = self.gestor.procesar(filas, 1, HOY)
        self.assertEqual(len(resultado.rechazos), 3)
        self.assertEqual(resultado.aceptados, [])
        self.assertTrue(all(r["motivo"] for r in resultado.rechazos))

    def test_duplicados_y_primera_invalida_no_reserva_clave(self):
        mala = ["03/10/2026", "30125448", "420101", "-100"]
        repetida = ["03/10/2026", "30125448", "420101", "180000"]
        resultado = self.gestor.procesar([mala, FILA, repetida], 1, HOY)
        self.assertEqual(len(resultado.aceptados), 1)
        self.assertEqual(len(resultado.rechazos), 2)
        self.assertEqual(resultado.rechazos[1]["motivo"], "Práctica duplicada")

    def test_diccionario_y_siete_digitos(self):
        fila = {"DNI": "1234567", "Fecha": "03/10/2026",
                "Cod_Practica": "420101", "Importe": "$12.500,00"}
        self.assertEqual(self.gestor.procesar([fila], 0, HOY).aceptados[0]["dni"], "1234567")

    def test_afiliado_ausente_y_tope_faltante(self):
        self.db.buscar.return_value = None
        self.assertIn("inexistente", self.gestor.procesar([FILA], 1, HOY).rechazos[0]["motivo"])
        gestor = GestorFacturacion(RepositorioCobertura(base_de_prueba(topes=[])))
        self.assertIn("sin tope", gestor.procesar([FILA], 1, HOY).rechazos[0]["motivo"])

    def test_falla_base_detiene_procesamiento_y_no_se_notifica(self):
        self.db.buscar.side_effect = ConnectionError("base no disponible")
        with self.assertRaises(ConnectionError):
            self.gestor.procesar([FILA], 1, HOY)

    def test_falla_pdf_no_envia_mail(self):
        resultado = self.gestor.procesar([FILA], 1, HOY)
        mail, pdf = Mock(), Mock()
        pdf.generar.side_effect = OSError("sin espacio")
        with self.assertRaises(OSError):
            cerrar_lote(resultado, mail, pdf)
        mail.enviar.assert_not_called()

    def test_deduplicacion_no_persiste_entre_ejecuciones(self):
        primero = self.gestor.procesar([FILA], 1, HOY)
        segundo = self.gestor.procesar([FILA], 1, HOY)
        self.assertEqual(len(primero.aceptados), 1)
        self.assertEqual(len(segundo.aceptados), 1)


if __name__ == "__main__":
    unittest.main()
