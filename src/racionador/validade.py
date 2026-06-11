import datetime

from racionador.modelos import Suprimento


def status_validade(
    validade: datetime.date | None, hoje: datetime.date, dias_aviso: int = 3
) -> str:
    """Classifica uma validade: "" (ok/sem data), "VENCE_HOJE" ou "ESGOTADO"."""
    if validade is None:
        return ""
    if validade < hoje:
        return "ESGOTADO"
    if (validade - hoje).days <= dias_aviso:
        return "VENCE_HOJE"
    return ""


def alertas_validade(
    suprimentos: list[Suprimento], hoje: datetime.date, dias_aviso: int = 3
) -> list[tuple[str, str, datetime.date]]:
    """Tuplas (nome, status, validade) dos suprimentos em alerta, mais urgente primeiro.

    Ordena ESGOTADO antes de VENCE_HOJE; dentro de cada grupo por validade
    crescente; desempate por nome. Itens com status "" são filtrados.
    """
    _ordem = {"ESGOTADO": 0, "VENCE_HOJE": 1}
    alertas = [
        (s.nome, status, s.validade)
        for s in suprimentos
        if (status := status_validade(s.validade, hoje, dias_aviso))
    ]
    return sorted(alertas, key=lambda a: (_ordem[a[1]], a[2], a[0]))
