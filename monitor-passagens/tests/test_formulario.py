from datetime import date

import pytest

from conftest import corpo
from monitor.formato import brl, duracao
from monitor.formulario import interpretar


def ok(**mudancas):
    busca, erros = interpretar(1, corpo(**mudancas))
    assert erros == []
    return busca


def erros_de(**mudancas):
    busca, erros = interpretar(1, corpo(**mudancas))
    assert busca is None
    return "\n".join(erros)


def test_leitura_basica_e_padroes():
    busca = ok()
    assert busca.origens == ["GRU", "CGH"] and busca.destinos == ["LIS"]
    assert busca.ida_e_volta and busca.data_ida == date(2027, 3, 15) and busca.data_volta == date(2027, 3, 29)
    assert (busca.adultos, busca.criancas, busca.bebes_assento, busca.bebes_colo) == (2, 0, 0, 0)
    assert busca.frequencia_horas == 3
    assert busca.monitorar_ate == date(2027, 3, 14)  # véspera da ida
    assert busca.preco_alvo is None and busca.email is None


def test_parametros_serpapi_ida_e_volta():
    params = ok().parametros_serpapi()
    assert params == {
        "engine": "google_flights", "departure_id": "GRU,CGH", "arrival_id": "LIS",
        "outbound_date": "2027-03-15", "return_date": "2027-03-29", "type": 1, "travel_class": 1,
        "adults": 2, "children": 0, "infants_in_seat": 0, "infants_on_lap": 0, "stops": 0, "bags": 0,
        "currency": "BRL", "hl": "pt-BR", "gl": "br",
    }


def test_somente_ida_ignora_volta():
    busca = ok(**{"Tipo de viagem": "Somente ida", "Data de volta": "_No response_"})
    params = busca.parametros_serpapi()
    assert params["type"] == 2 and "return_date" not in params


def test_idades_viram_adulto_crianca_e_bebe_com_assento():
    busca = ok(**{"Idade de cada criança": "14, 12, 11, 7, 2, 1, 0"})
    assert (busca.adultos, busca.criancas, busca.bebes_assento, busca.bebes_colo) == (4, 3, 2, 0)
    assert busca.passageiros == 9 and busca.com_assento == 9


def test_bebes_no_colo_com_checkbox():
    busca = ok(**{"Idade de cada criança": "7 anos, 4 e 1", "Bebês no colo": "- [X] Os bebês viajam no colo"})
    assert (busca.adultos, busca.criancas, busca.bebes_assento, busca.bebes_colo) == (2, 2, 0, 1)
    params = busca.parametros_serpapi()
    assert params["infants_on_lap"] == 1 and params["infants_in_seat"] == 0 and params["children"] == 2


@pytest.mark.parametrize("texto,classe", [
    ("Econômica", 1), ("Econômica premium", 2), ("Executiva", 3), ("Primeira classe", 4),
])
def test_classes(texto, classe):
    assert ok(Classe=texto).parametros_serpapi()["travel_class"] == classe


@pytest.mark.parametrize("texto,escalas", [
    ("Qualquer", 0), ("Direto", 1), ("Máx. 1 escala", 2), ("Máx. 2 escalas", 3),
])
def test_escalas(texto, escalas):
    assert ok(Escalas=texto).parametros_serpapi()["stops"] == escalas


@pytest.mark.parametrize("texto,valor", [
    ("3.500,00", 3500.0), ("R$ 3500", 3500.0), ("3.500", 3500.0), ("2999,90", 2999.9), ("1234.5", 1234.5),
])
def test_preco_alvo(texto, valor):
    assert ok(**{"Preço-alvo (R$)": texto}).preco_alvo == valor


def test_campos_opcionais_preenchidos():
    busca = ok(**{
        "Frequência de verificação": "12 h", "Monitorar até": "01/03/2027",
        "E-mail para avisos": "cliente@exemplo.com", "Bagagens de mão": "2",
    })
    assert busca.frequencia_horas == 12 and busca.monitorar_ate == date(2027, 3, 1)
    assert busca.email == "cliente@exemplo.com" and busca.parametros_serpapi()["bags"] == 2


def test_monitorar_ate_depois_da_ida_e_limitado_a_ida():
    assert ok(**{"Monitorar até": "30/12/2027"}).monitorar_ate == date(2027, 3, 15)


# ---- erros de cadastro -------------------------------------------------------

def test_erro_iata_invalido():
    assert "código IATA inválido (GUARULHOS)" in erros_de(Origem="GUARULHOS")


def test_erro_origem_igual_destino():
    assert "aparece nos dois campos" in erros_de(Destino="GRU")


def test_erro_data_invalida_e_volta_obrigatoria():
    assert "Data de ida" in erros_de(**{"Data de ida": "2027-03-15"})
    assert "Data de volta" in erros_de(**{"Data de volta": "_No response_"})
    assert "não pode ser antes" in erros_de(**{"Data de volta": "01/03/2027"})


def test_erro_mais_de_nove_passageiros():
    assert "máximo é 9" in erros_de(Adultos="6", **{"Idade de cada criança": "5, 6, 7, 8"})


def test_erro_mais_bebes_no_colo_que_adultos():
    texto = erros_de(Adultos="1", **{"Idade de cada criança": "1, 0",
                                    "Bebês no colo": "- [x] Os bebês viajam no colo"})
    assert "2 bebê(s) no colo para 1 adulto(s)" in texto


def test_bebes_com_assento_nao_dependem_de_adultos():
    busca = ok(Adultos="1", **{"Idade de cada criança": "1, 0"})
    assert busca.bebes_assento == 2


def test_erro_bagagens_acima_dos_assentos():
    texto = erros_de(Adultos="2", **{"Idade de cada criança": "1", "Bagagens de mão": "3",
                                    "Bebês no colo": "- [x] Os bebês viajam no colo"})
    assert "3 é mais do que os 2 passageiro(s) com assento" in texto


def test_erro_sem_adulto():
    assert "pelo menos 1 passageiro com 12 anos" in erros_de(Adultos="0", **{"Idade de cada criança": "8"})


def test_erro_idades_e_email_e_varios_erros_juntos():
    texto = erros_de(**{"Idade de cada criança": "sete", "E-mail para avisos": "sem-arroba",
                        "Preço-alvo (R$)": "barato"})
    assert "Idade de cada criança" in texto and "E-mail" in texto and "Preço-alvo" in texto


def test_corpo_sem_formulario():
    busca, erros = interpretar(1, "quero uma passagem barata")
    assert busca is None and "formulário" in erros[0]


def test_formatos():
    assert brl(1234.56) == "R$ 1.234,56"
    assert brl(980) == "R$ 980,00"
    assert brl(1234567.8) == "R$ 1.234.567,80"
    assert duracao(755) == "12h 35min" and duracao(120) == "2h" and duracao(45) == "45min"


def test_todo_campo_do_issue_form_e_reconhecido_pelo_leitor():
    """Se alguém renomear um campo no formulário, o leitor precisa acompanhar."""
    import re
    from pathlib import Path

    from monitor.formulario import ler_secoes

    modelo = Path(__file__).resolve().parent.parent / ".github" / "ISSUE_TEMPLATE" / "passagem.yml"
    rotulos = re.findall(r"^      label: (.+)$", modelo.read_text(encoding="utf-8"), flags=re.M)
    assert len(rotulos) == 15
    campos = ler_secoes("\n\n".join(f"### {rotulo}\n\nvalor" for rotulo in rotulos))
    assert len(campos) == 15
