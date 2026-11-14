"""Fluxo completo com GitHub, SerpApi e SMTP simulados."""

import json
from datetime import datetime, timedelta, timezone

from conftest import AGORA, SEM_VOOS, corpo, html_de, resposta_serpapi
from monitor import correio
from monitor.historico import MAX_REGISTROS


def horas(n):
    return AGORA + timedelta(hours=n)


def estado(monitor, numero=1):
    return json.loads(monitor.caminho.read_text(encoding="utf-8"))["buscas"].get(str(numero))


# ---- início e frequência -----------------------------------------------------

def test_primeira_verificacao_comenta_monitoramento_iniciado(monitor, internet, caixa):
    internet.criar_issue(1, corpo())
    assert monitor.executar(AGORA) == 0

    (comentario,) = internet.comentarios_de(1)
    assert "✅ **Monitoramento iniciado**" in comentario
    assert "R$ 4.000,00" in comentario and "R$ 3.500,00 a R$ 5.200,00" in comentario
    assert "TAP, Iberia" in comentario and "1 escala (MAD)" in comentario and "12h 35min" in comentario
    assert caixa.mensagens == []  # preço típico: sem e-mail

    consulta = internet.consultas[0]
    assert consulta["api_key"] == "chave-falsa" and consulta["departure_id"] == "GRU,CGH"
    assert (consulta["currency"], consulta["hl"], consulta["gl"]) == ("BRL", "pt-BR", "br")
    assert estado(monitor)["verificacoes"] == 1


def test_usa_o_menor_preco_entre_best_e_other(monitor, internet):
    internet.serpapi = resposta_serpapi(preco=4000, outros=(3900, 4500))
    internet.criar_issue(1, corpo())
    monitor.executar(AGORA)
    assert estado(monitor)["registros"][0]["preco"] == 3900
    assert "LATAM" in internet.comentarios_de(1)[0]


def test_respeita_a_frequencia_de_cada_busca(monitor, internet):
    internet.criar_issue(1, corpo())                                      # 3 h (padrão)
    internet.criar_issue(2, corpo(**{"Frequência de verificação": "1 h"}))
    internet.criar_issue(3, corpo(**{"Frequência de verificação": "24 h"}))

    monitor.executar(AGORA)
    assert len(internet.consultas) == 3
    monitor.executar(horas(1))
    assert [c["departure_id"] for c in internet.consultas[3:]] == ["GRU,CGH"]  # só a de 1 h
    assert estado(monitor, 2)["verificacoes"] == 2 and estado(monitor, 1)["verificacoes"] == 1
    monitor.executar(horas(2))
    monitor.executar(horas(3))
    assert estado(monitor, 1)["verificacoes"] == 2
    assert estado(monitor, 2)["verificacoes"] == 4
    assert estado(monitor, 3)["verificacoes"] == 1
    assert len(internet.comentarios_de(1)) == 1  # "iniciado" só uma vez


def test_tolera_atraso_do_cron(monitor, internet):
    internet.criar_issue(1, corpo())
    monitor.executar(AGORA)
    monitor.executar(horas(3) - timedelta(minutes=10))  # o cron adiantou/atrasou alguns minutos
    assert estado(monitor)["verificacoes"] == 2


def test_issues_que_nao_sao_buscas_sao_ignoradas(monitor, internet):
    internet.criar_issue(1, corpo(), titulo="Bug no robô")
    internet.criar_issue(2, corpo())
    internet.issues[2]["pull_request"] = {}
    monitor.executar(AGORA)
    assert internet.consultas == [] and internet.comentarios == []


# ---- ofertas -----------------------------------------------------------------

def test_oferta_envia_email_html_e_comenta(monitor, internet, caixa):
    internet.criar_issue(1, corpo(**{"Preço-alvo (R$)": "3.300,00"}))
    monitor.executar(AGORA)
    internet.serpapi = resposta_serpapi(preco=3200, nivel="low")
    monitor.executar(horas(3))

    (mensagem,) = caixa.para("eu@gmail.com")
    assert "R$ 3.200,00" in mensagem["Subject"]
    html = html_de(mensagem)
    for trecho in ("R$ 3.200,00", "TAP, Iberia", "1 escala (MAD)", "12h 35min", "R$ 4.000,00",
                   "https://www.google.com/travel/flights?tfs=abc", "Ver no Google Flights",
                   "confirme o valor final no site", "preço-alvo de R$ 3.300,00", "faixa típica"):
        assert trecho in html, trecho
    assert caixa.conexoes[0] == {"host": "smtp.gmail.com", "porta": 587, "ssl": False, "tls": True,
                                 "login": ("eu@gmail.com", "senha-de-app")}

    comentario = internet.comentarios_de(1)[-1]
    assert "🔥 **Oferta encontrada: R$ 3.200,00**" in comentario
    assert "Menor preço visto antes:** R$ 4.000,00" in comentario
    assert "E-mail enviado para eu@gmail.com" in comentario


def test_antispam_no_fluxo(monitor, internet, caixa):
    internet.criar_issue(1, corpo(**{"Frequência de verificação": "1 h"}))
    precos = [3000, 3000, 2950, 2900, 3400, 3350]
    avisos = []
    for i, preco in enumerate(precos):
        internet.serpapi = resposta_serpapi(preco=preco)
        monitor.executar(horas(i))
        avisos.append(len(caixa.mensagens))
    # 3000 avisa; 3000 e 2950 (-1,7%) não; 2900 (-3,3%) avisa;
    # 3400 (+17%) só libera; 3350 é a queda seguinte e avisa.
    assert avisos == [1, 1, 1, 2, 2, 3]


def test_alta_libera_aviso_na_proxima_queda(monitor, internet, caixa):
    internet.criar_issue(1, corpo(**{"Frequência de verificação": "1 h"}))
    for i, (preco, esperado) in enumerate([(3000, 1), (4000, 1), (3450, 2)]):
        internet.serpapi = resposta_serpapi(preco=preco)
        monitor.executar(horas(i))
        assert len(caixa.mensagens) == esperado, preco


def test_mediana_do_historico_proprio(monitor, internet, caixa):
    internet.criar_issue(1, corpo(**{"Frequência de verificação": "1 h"}))
    internet.serpapi = resposta_serpapi(preco=5000, faixa=(3000, 6000))
    for i in range(8):
        monitor.executar(horas(i))
    internet.serpapi = resposta_serpapi(preco=4400, faixa=(3000, 6000))
    monitor.executar(horas(8))
    assert len(caixa.mensagens) == 1
    assert "12% abaixo da mediana" in html_de(caixa.mensagens[0])


def test_email_proprio_da_busca(monitor, internet, caixa):
    internet.serpapi = resposta_serpapi(preco=3000, nivel="low")
    internet.criar_issue(1, corpo(**{"E-mail para avisos": "cliente@exemplo.com"}))
    internet.criar_issue(2, corpo())
    monitor.executar(AGORA)
    assert len(caixa.para("cliente@exemplo.com")) == 1 and len(caixa.para("eu@gmail.com")) == 1


def test_falha_no_email_ainda_comenta_na_issue(monitor, internet, caixa):
    caixa.falhar = True
    internet.serpapi = resposta_serpapi(preco=3000, nivel="low")
    internet.criar_issue(1, corpo())
    assert monitor.executar(AGORA) == 0
    assert "Não consegui enviar o e-mail" in internet.comentarios_de(1)[-1]


def test_smtp_porta_465_usa_ssl_direto(caixa):
    config = correio.ConfigSMTP.do_ambiente(
        {"SMTP_USER": "eu@outlook.com", "SMTP_PASSWORD": "x", "SMTP_HOST": "smtp.exemplo.com", "SMTP_PORT": "465"}
    )
    correio.enviar(config, "a@b.com", "Assunto", "<p>oi</p>", "oi")
    assert caixa.conexoes[0]["ssl"] and not caixa.conexoes[0]["tls"]
    assert caixa.conexoes[0]["host"] == "smtp.exemplo.com"
    padrao = correio.ConfigSMTP.do_ambiente({"SMTP_USER": "eu@gmail.com", "SMTP_HOST": "", "SMTP_PORT": ""})
    assert (padrao.host, padrao.porta) == ("smtp.gmail.com", 587)


# ---- erros de cadastro e edição ----------------------------------------------

def test_erro_de_cadastro_comenta_uma_vez_so(monitor, internet):
    internet.criar_issue(1, corpo(Origem="SAO PAULO", Adultos="10"))
    monitor.executar(AGORA)
    monitor.executar(horas(1))
    (comentario,) = internet.comentarios_de(1)
    assert "Não consegui iniciar o monitoramento" in comentario
    assert "código IATA inválido" in comentario and "máximo é 9" in comentario
    assert internet.consultas == []

    internet.issues[1]["body"] = corpo(Origem="SAO PAULO")  # corrigiu só um dos erros
    monitor.executar(horas(2))
    assert len(internet.comentarios_de(1)) == 2

    internet.issues[1]["body"] = corpo()  # corrigiu tudo
    monitor.executar(horas(2))
    assert "Monitoramento iniciado" in internet.comentarios_de(1)[-1]


def test_data_ja_passada_e_erro_de_cadastro(monitor, internet):
    internet.criar_issue(1, corpo(**{"Data de ida": "05/01/2027", "Data de volta": "20/01/2027"}))
    monitor.executar(AGORA)
    assert "já passou" in internet.comentarios_de(1)[0]
    assert internet.issues[1]["state"] == "open" and internet.consultas == []


def test_editar_a_issue_revalida_zera_historico_e_verifica_na_hora(monitor, internet, caixa):
    internet.serpapi = resposta_serpapi(preco=3000, nivel="low")
    internet.criar_issue(1, corpo())
    monitor.executar(AGORA)
    assert estado(monitor)["ultimo_aviso_preco"] == 3000

    internet.issues[1]["body"] = corpo(Destino="OPO")
    monitor.executar(AGORA + timedelta(minutes=5))  # bem antes das 3 h
    novo = estado(monitor)
    assert internet.consultas[-1]["arrival_id"] == "OPO"
    assert novo["verificacoes"] == 1 and len(novo["registros"]) == 1
    assert sum("Monitoramento iniciado" in c for c in internet.comentarios_de(1)) == 2
    assert len(caixa.mensagens) == 2  # histórico zerado: a oferta é avisada de novo


# ---- sem resultado -----------------------------------------------------------

def test_sem_resultado_comenta_uma_vez_e_continua_tentando(monitor, internet, caixa):
    internet.serpapi = SEM_VOOS
    internet.criar_issue(1, corpo())
    for i in range(3):
        assert monitor.executar(horas(3 * i)) == 0
    assert len(internet.consultas) == 3
    (comentario,) = internet.comentarios_de(1)
    assert "não retornou resultado" in comentario and "hasn't returned any results" in comentario

    internet.serpapi = resposta_serpapi()
    monitor.executar(horas(9))
    assert "Monitoramento iniciado" in internet.comentarios_de(1)[-1]

    internet.serpapi = {"best_flights": [], "other_flights": [{"flights": []}]}  # voos sem preço
    monitor.executar(horas(12))
    assert len(internet.comentarios_de(1)) == 3  # voltou a falhar: avisa de novo, uma vez
    assert estado(monitor)["verificacoes"] == 5 and len(estado(monitor)["registros"]) == 1


# ---- encerramento ------------------------------------------------------------

def test_encerra_ao_passar_do_prazo(monitor, internet, caixa):
    internet.criar_issue(1, corpo(**{"Data de ida": "13/01/2027", "Data de volta": "20/01/2027"}))
    for i, preco in enumerate([4000, 4600, 3900]):
        internet.serpapi = resposta_serpapi(preco=preco)
        monitor.executar(horas(3 * i))
    consultas = len(internet.consultas)

    # Limite = véspera da ida (12/01). Dia 12 às 23h de Brasília ainda monitora...
    monitor.executar(datetime(2027, 1, 13, 2, 0, tzinfo=timezone.utc))
    assert internet.issues[1]["state"] == "open" and len(internet.consultas) == consultas + 1
    # ...e no dia 13 (horário de Brasília) encerra.
    monitor.executar(datetime(2027, 1, 13, 4, 0, tzinfo=timezone.utc))

    assert internet.issues[1]["state"] == "closed" and internet.issues[1]["state_reason"] == "completed"
    comentario = internet.comentarios_de(1)[-1]
    assert "🏁 **Monitoramento encerrado**" in comentario
    assert "Menor preço visto:** R$ 3.900,00" in comentario
    assert "Maior preço visto:** R$ 4.600,00" in comentario
    assert "Verificações feitas:** 4" in comentario
    assert "Monitoramento encerrado" in caixa.mensagens[-1]["Subject"]
    assert "R$ 3.900,00" in html_de(caixa.mensagens[-1])
    assert len(internet.consultas) == consultas + 1  # não consulta ao encerrar
    assert estado(monitor) is None


def test_encerra_pela_data_monitorar_ate(monitor, internet):
    internet.criar_issue(1, corpo(**{"Monitorar até": "11/01/2027"}))
    monitor.executar(AGORA)
    monitor.executar(AGORA + timedelta(days=2))
    assert internet.issues[1]["state"] == "closed"


def test_fechar_a_issue_manualmente_para_o_monitoramento(monitor, internet):
    internet.criar_issue(1, corpo())
    monitor.executar(AGORA)
    internet.issues[1]["state"] = "closed"
    monitor.executar(horas(3))
    assert len(internet.consultas) == 1 and estado(monitor) is None


# ---- robustez ----------------------------------------------------------------

def test_erro_em_uma_busca_nao_derruba_as_outras(monitor, internet):
    def serp(params):
        if params["arrival_id"] == "XXX":
            raise ValueError("resposta inesperada")
        return resposta_serpapi()

    internet.serpapi = serp
    internet.criar_issue(1, corpo(Destino="XXX"))
    internet.criar_issue(2, corpo())
    internet.criar_issue(3, corpo(Destino="MAD"))
    internet.falhar_comentario_em = {3}

    assert monitor.executar(AGORA) == 2
    assert "Monitoramento iniciado" in internet.comentarios_de(2)[0]
    assert estado(monitor, 2)["verificacoes"] == 1  # histórico salvo mesmo com falhas

    internet.falhar_comentario_em = set()
    monitor.executar(horas(3))
    assert "Monitoramento iniciado" in internet.comentarios_de(3)[0]  # tenta de novo depois


def test_historico_limitado_a_500_registros_e_so_grava_se_mudar(monitor, internet):
    internet.criar_issue(1, corpo(**{"Frequência de verificação": "1 h"}))
    monitor.executar(AGORA)
    dados = json.loads(monitor.caminho.read_text(encoding="utf-8"))
    dados["buscas"]["1"]["registros"] = [{"quando": "x", "preco": 4000 + i} for i in range(MAX_REGISTROS)]
    monitor.caminho.write_text(json.dumps(dados), encoding="utf-8")
    monitor.executar(horas(1))
    registros = estado(monitor)["registros"]
    assert len(registros) == MAX_REGISTROS and registros[-1]["preco"] == 4000 and registros[0]["preco"] == 4001

    antes = monitor.caminho.stat().st_mtime_ns
    monitor.executar(horas(1) + timedelta(minutes=5))  # nada vence: arquivo intocado
    assert monitor.caminho.stat().st_mtime_ns == antes


def test_paginacao_das_issues(monitor, internet):
    for numero in range(1, 121):
        internet.criar_issue(numero, corpo(), titulo="Outra coisa")
    internet.criar_issue(121, corpo())
    monitor.executar(AGORA)
    assert len(internet.consultas) == 1
