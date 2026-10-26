"""Fragmento original de la etapa 5; no se usa para liquidaciones reales."""

from datetime import datetime


class GestorFacturacion:
    def proc(self, d, t):
        # recorre las filas y hace todo
        res = []
        for x in d:
            if t == 1:
                dni = x[1].replace(".", "")
            else:
                dni = x["DNI"].replace(".", "")
            if len(dni) < 7 or len(dni) > 8:
                continue
            f = datetime.strptime(x[0], "%d/%m/%Y")
            if (datetime.now() - f).days > 60:
                continue
            # si estado es 2 el afiliado está de baja
            if self.db.buscar(dni).plan.cobertura.estado == 2:
                continue
            tope = self.db.buscar(dni).plan.cobertura.topes[0]
            imp = float(x[3]) if float(x[3]) < tope else tope
            res.append([dni, f, x[2], imp])
            self.mail.enviar("auditoria@obrasocial.com", str(len(res)))
            self.pdf.generar(res)
        return res
