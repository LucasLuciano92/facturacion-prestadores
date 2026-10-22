import csv
from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from openpyxl import Workbook

from prestadores import PRESTADORES
from procesador import (
    exportar, procesar_clinica, procesar_imagenes, procesar_laboratorio, procesar_lote,
)
from validaciones import normalizar_dni, normalizar_importe, validar_fecha


HOY = date(2026, 10, 15)
ACTIVOS = {"30125448": "activo", "35111222": "activo", "22333444": "baja",
           "1234567": "activo"}
MUESTRA = [
    ["03/10/2026", "30.125.448", "Gomez Ana", "420101", "$12.500,00"],
    ["03/10/2026", "30125448", "Gomez Ana", "420101", "$12.500,00"],
    ["05/10/2026", "284556712", "Ruiz Pedro", "170101", "$8.300,00"],
    ["12/11/2026", "35111222", "Sosa Lucia", "420101", "$12.500,00"],
    ["07/10/2026", "22333444", "Diaz Raul", "340201", "$45.000,00"],
]


def crear_excel(path, filas=MUESTRA, encabezado=None):
    libro = Workbook()
    libro.active.append(encabezado or ["Fecha", "DNI", "Afiliado", "Cod_Practica", "Importe"])
    for fila in filas:
        libro.active.append(fila)
    libro.save(path)
    libro.close()


class ValidacionesTest(unittest.TestCase):
    def test_p01_dni_valido(self):
        for entrada, esperado in [("30.125.448", "30125448"), ("1234567", "1234567"),
                                  (30125448.0, "30125448")]:
            with self.subTest(entrada=entrada):
                self.assertEqual(normalizar_dni(entrada), esperado)

    def test_p01_dni_invalido(self):
        for dni in ["123456", "284556712", "ABC12345", "", None, "１２３４５６７"]:
            with self.subTest(dni=dni), self.assertRaises(ValueError):
                normalizar_dni(dni)

    def test_fechas_en_limites(self):
        for dias in [0, 60]:
            fecha = HOY - timedelta(days=dias)
            self.assertEqual(validar_fecha(fecha, "%d/%m/%Y", HOY), fecha)
        for dias in [-1, 61]:
            with self.subTest(dias=dias), self.assertRaises(ValueError):
                validar_fecha(HOY - timedelta(days=dias), "%d/%m/%Y", HOY)
        with self.assertRaisesRegex(ValueError, "Fecha inválida"):
            validar_fecha("31/02/2026", "%d/%m/%Y", HOY)

    def test_importes_exactos(self):
        for importe in ["$12.500,00", 12500, 12500.0, Decimal("12500")]:
            self.assertEqual(normalizar_importe(importe), Decimal("12500.00"))
        for importe in ["", "nan", -1, 0, True, float("inf"), 1.234]:
            with self.subTest(importe=importe), self.assertRaises(ValueError):
                normalizar_importe(importe)


class LoteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.carpeta = Path(self.tmp.name)

    def test_p02_excel_completo_y_exportacion(self):
        archivo = self.carpeta / "clinica.xlsx"
        crear_excel(archivo)
        original = archivo.read_bytes()
        validos, rechazos = procesar_lote([("clinica", archivo)], ACTIVOS, HOY)
        self.assertEqual(len(validos), 1)
        self.assertEqual(validos[0]["importe"], Decimal("12500.00"))
        self.assertEqual([r["motivo"] for r in rechazos], [
            "Práctica duplicada", "DNI inválido", "Fecha fuera de término",
            "Afiliado inexistente o dado de baja",
        ])
        self.assertEqual([r["fila"] for r in rechazos], [3, 4, 5, 6])
        destino = self.carpeta / "salida"
        self.assertEqual(exportar(validos, rechazos, destino),
                         {"recibidos": 5, "aceptados": 1, "rechazados": 4})
        with (destino / "liquidacion.csv").open(encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f, delimiter=";"))
        self.assertEqual(filas, [{"prestador": "clinica", "dni": "30125448",
                                 "fecha": "2026-10-03", "codigo": "420101",
                                 "importe": "12500.00"}])
        self.assertEqual(json.loads((destino / "resumen.json").read_text())["recibidos"], 5)
        self.assertEqual(archivo.read_bytes(), original)

    def test_alias_de_excel_y_celda_numerica(self):
        archivo = self.carpeta / "alias.xlsx"
        crear_excel(archivo, [[HOY, 30125448, "Gomez Ana", "420101", 12500]],
                    ["Fecha atención", "Documento", "Nombre", "Código práctica", "Monto"])
        validos, rechazos = procesar_lote([("clinica", archivo)], ACTIVOS, HOY)
        self.assertEqual((len(validos), len(rechazos)), (1, 0))

    def test_excel_sin_columnas_obligatorias(self):
        archivo = self.carpeta / "invalido.xlsx"
        crear_excel(archivo, [], ["Fecha", "DNI"])
        with self.assertRaisesRegex(ValueError, "Faltan columnas"):
            procesar_lote([("clinica", archivo)], ACTIVOS, HOY)

    def test_p03_duplicado_despues_de_normalizar(self):
        fila = {"Fecha": "03/10/2026", "DNI": "30.125.448",
                "Cod_Practica": "420101", "Importe": "$12.500,00"}
        vistos = set()
        self.assertIsNone(procesar_clinica(fila, HOY, ACTIVOS, vistos)[1])
        fila["DNI"] = "30125448"
        self.assertEqual(procesar_clinica(fila, HOY, ACTIVOS, vistos)[1], "Práctica duplicada")

    def test_rechazado_no_reserva_clave(self):
        fila = {"Fecha": "03/10/2026", "DNI": "30125448",
                "Cod_Practica": "420101", "Importe": "0"}
        vistos = set()
        self.assertIsNone(procesar_clinica(fila, HOY, ACTIVOS, vistos)[0])
        self.assertFalse(vistos)
        fila["Importe"] = "100,00"
        self.assertIsNone(procesar_clinica(fila, HOY, ACTIVOS, vistos)[1])

    def test_txt_csv_y_duplicado_entre_prestadores(self):
        txt, csv_path = self.carpeta / "bioan.txt", self.carpeta / "delta.csv"
        txt.write_text("1234567 " + "20261003" + "420101  " + "0001250000" + "\n",
                       encoding="utf-8")
        csv_path.write_text("Fecha;DNI;Codigo;Importe\n03-10-2026;1234567;420101;12500,00\n",
                            encoding="utf-8")
        validos, rechazos = procesar_lote(
            [("laboratorio", txt), ("imagenes", csv_path)], ACTIVOS, HOY
        )
        self.assertEqual((len(validos), len(rechazos)), (1, 1))
        self.assertEqual(validos[0]["importe"], Decimal("12500.00"))
        self.assertEqual(rechazos[0]["motivo"], "Práctica duplicada")

    def test_lineas_estructuralmente_invalidas(self):
        txt, csv_path = self.carpeta / "corto.txt", self.carpeta / "corto.csv"
        txt.write_text("123\n", encoding="utf-8")
        csv_path.write_text("03-10-2026;1234567\n", encoding="utf-8")
        validos, rechazos = procesar_lote(
            [("laboratorio", txt), ("imagenes", csv_path)], ACTIVOS, HOY
        )
        self.assertEqual((len(validos), len(rechazos)), (0, 2))

    def test_afiliados_indisponibles_detienen_lote(self):
        with self.assertRaisesRegex(ValueError, "base de afiliados"):
            procesar_lote([], None, HOY)


class RegresionTest(unittest.TestCase):
    def test_dni_de_siete_y_ocho_digitos_en_tres_adaptadores(self):
        adaptadores = [(procesar_clinica, "03/10/2026"),
                       (procesar_laboratorio, "20261003"),
                       (procesar_imagenes, "03-10-2026")]
        for procesar, fecha in adaptadores:
            for dni in ["123456", "1234567", "30125448", "284556712"]:
                with self.subTest(adaptador=procesar.__name__, dni=dni):
                    registro, error = procesar(
                        {"DNI": dni, "Fecha": fecha, "Cod_Practica": "420101",
                         "Importe": "100,00"}, HOY, ACTIVOS, set()
                    )
                    if len(dni) in {7, 8}:
                        self.assertIsNone(error)
                        self.assertIsNotNone(registro)
                    else:
                        self.assertEqual(error, "DNI inválido")

    def test_catalogo_conserva_ambas_contribuciones(self):
        self.assertEqual(PRESTADORES, ["clinica", "laboratorio", "imagenes",
                                      "farmacia", "odontologia"])
        self.assertEqual(len(PRESTADORES), len(set(PRESTADORES)))


if __name__ == "__main__":
    unittest.main()
