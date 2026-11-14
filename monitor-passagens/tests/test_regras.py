from monitor.regras import avaliar

FAIXA = (3500.0, 5200.0)


def decidir(preco, nivel="typical", faixa=FAIXA, anteriores=(), alvo=None, ultimo=None, rearmado=False):
    return avaliar(preco, nivel, faixa, list(anteriores), alvo, ultimo, rearmado)


def test_preco_normal_nao_avisa():
    decisao = decidir(4000)
    assert not decisao.avisar and decisao.motivos == []


def test_motivo_1_nivel_baixo():
    decisao = decidir(4000, nivel="low")
    assert decisao.avisar and "baixo" in decisao.motivos[0]


def test_motivo_2_abaixo_da_faixa_tipica():
    assert decidir(3499).avisar
    assert not decidir(3500).avisar  # igual ao limite inferior não é "menor que"
    assert "R$ 3.500,00 a R$ 5.200,00" in decidir(3499).motivos[0]


def test_motivo_3_mediana_so_depois_de_8_verificacoes():
    assert not decidir(3600, anteriores=[4000] * 7).avisar
    assert decidir(3600, anteriores=[4000] * 8).avisar       # exatamente 10% abaixo
    assert not decidir(3601, anteriores=[4000] * 8).avisar   # 9,98% abaixo


def test_motivo_4_preco_alvo():
    assert decidir(3800, alvo=3800).avisar
    assert not decidir(3801, alvo=3800).avisar


def test_sem_price_insights_nao_quebra():
    assert not avaliar(4000, None, None, [], None, None, False).avisar


def test_varios_motivos_ao_mesmo_tempo():
    assert len(decidir(3000, nivel="low", anteriores=[4000] * 8, alvo=3200).motivos) == 4


def test_antispam_so_reavisa_com_queda_de_3_por_cento():
    assert not decidir(3000, nivel="low", ultimo=3000).avisar
    assert not decidir(2911, nivel="low", ultimo=3000).avisar   # caiu 2,97%
    assert decidir(2910, nivel="low", ultimo=3000).avisar       # caiu 3%


def test_alta_de_mais_de_10_por_cento_rearma_o_aviso():
    subiu = decidir(3301, nivel="low", ultimo=3000)   # +10,03%: não avisa na alta, só libera
    assert not subiu.avisar and subiu.rearmado
    nao_subiu = decidir(3300, nivel="low", ultimo=3000)  # exatamente +10% não libera
    assert not nao_subiu.avisar and not nao_subiu.rearmado
    assert decidir(4000, ultimo=3000).rearmado           # libera mesmo sem motivo de oferta

    # Próxima queda: avisa mesmo estando acima do último aviso, e consome a liberação.
    queda = decidir(3100, nivel="low", ultimo=3000, rearmado=True)
    assert queda.avisar and not queda.rearmado


def test_liberacao_continua_valendo_enquanto_nao_houver_oferta():
    decisao = decidir(3900, ultimo=3000, rearmado=True)
    assert not decisao.avisar and decisao.rearmado
