from crt_ui import classe_status, info, linha, secao


def test_classe_status_usa_chave_crua():
    assert classe_status("CRITICO") == "crit"
    assert classe_status("SEM_DADOS") == "sem-dados"
    assert classe_status("DESCONHECIDO") == "ok"


def test_linha_tem_tag_estado_e_sos():
    out = linha(1, "ÁGUA", "2 DIAS", estado="crit", sos=True)
    assert "log-line crit" in out and "[2 DIAS]" in out and "badge sos" in out
    assert "<a" not in out


def test_linha_com_href_vira_link_self():
    out = linha(1, "GRUPO X", "OK", href="?grupo=GRUPO%20X")
    assert 'class="log-link"' in out and 'target="_self"' in out


def test_info_nao_tem_numero():
    out = info("REGIÃO", "NORTE")
    assert "REGIÃO" in out and "[NORTE]" in out and '"num"' not in out


def test_secao_envolve_titulo():
    out = secao("ESTOQUE", [linha(1, "ARROZ", "5 DIAS")])
    assert "section-title" in out and "ESTOQUE" in out
