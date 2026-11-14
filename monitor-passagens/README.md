# Monitor de Passagens ✈️

Robô que acompanha preços de passagens aéreas 24 horas por dia e avisa por **e-mail** quando
aparece um preço abaixo do mercado. Roda de graça no GitHub Actions, em repositório privado,
e usa a [SerpApi](https://serpapi.com) (Google Flights) como fonte de preços, cobrindo todas
as companhias que o Google Flights mostra.

## Como funciona

1. Cada viagem é uma **issue** criada pelo formulário **✈️ Monitorar passagem**.
2. O workflow `Monitor de passagens` roda de hora em hora, quando você dispara manualmente e
   sempre que uma busca é criada ou editada.
3. Para cada issue aberta com título começando em `[Passagem]`, o robô consulta a SerpApi
   (respeitando a frequência escolhida) e pega o **menor preço** entre `best_flights` e
   `other_flights`. O valor é o total para todos os passageiros.
4. Na primeira verificação ele comenta **✅ Monitoramento iniciado**, com o preço atual e a
   faixa típica da rota.
5. Quando o preço está abaixo do mercado, envia um e-mail em HTML e comenta na issue.
6. Ao passar do prazo, comenta um resumo, envia um e-mail de encerramento e fecha a issue.

### Quando o robô avisa

Basta **uma** das situações:

| # | Situação |
|---|----------|
| 1 | O Google Flights classifica o preço como baixo (`price_level == "low"`) |
| 2 | Preço menor que o limite inferior da faixa típica (`typical_price_range`) |
| 3 | Preço pelo menos 10% abaixo da mediana do seu próprio histórico (depois de 8 verificações) |
| 4 | Preço igual ou menor que o seu preço-alvo |

**Contra spam:** depois de um aviso, só avisa de novo se o preço cair mais 3%. Se o preço
subir mais de 10% acima do último aviso, o robô libera um novo aviso para a próxima vez que o
preço voltar a ser uma oferta (a alta em si não gera e-mail).

### Passageiros

- 12 anos ou mais conta como adulto; de 2 a 11, criança; menor de 2, bebê.
- Bebês viajam com assento, a não ser que você marque **Os bebês viajam no colo**.
- Máximo de 9 passageiros; não pode haver mais bebês no colo do que adultos; bagagens de mão
  não podem passar do número de passageiros com assento.

Se o cadastro tiver erro, o robô comenta na issue dizendo o que corrigir.

## Instalação passo a passo

1. **Repositório.** Crie um repositório **privado** e envie este código para a branch principal.
2. **Permissões do Actions.** Em *Settings → Actions → General → Workflow permissions*, marque
   **Read and write permissions**. Pelo terminal:
   ```bash
   gh api -X PUT repos/SEU_USUARIO/monitor-passagens/actions/permissions/workflow \
     -f default_workflow_permissions=write
   ```
3. **Chave da SerpApi.** Crie uma conta grátis em [serpapi.com](https://serpapi.com) e copie a
   *API Key* do painel.
4. **Senha de app do Gmail.** Com a verificação em duas etapas ativada, gere uma senha em
   [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
5. **Secrets.** Em *Settings → Secrets and variables → Actions → New repository secret*
   (ou `gh secret set NOME`, que pede o valor sem gravá-lo em arquivo):

   | Secret | Obrigatório | Valor |
   |--------|-------------|-------|
   | `SERPAPI_KEY` | sim | chave da SerpApi |
   | `SMTP_USER` | sim | seu e-mail (ex.: `voce@gmail.com`) |
   | `SMTP_PASSWORD` | sim | senha de app |
   | `EMAIL_DESTINO` | não | quem recebe os avisos (padrão: `SMTP_USER`) |
   | `SMTP_HOST` | não | padrão `smtp.gmail.com` (Outlook: `smtp-mail.outlook.com`) |
   | `SMTP_PORT` | não | padrão `587` (STARTTLS); use `465` para SSL direto |

6. **Teste.** Crie uma busca pelo formulário (*Issues → New issue*) e acompanhe a aba
   *Actions*. Em cerca de 1 minuto deve aparecer o comentário **✅ Monitoramento iniciado**.

Nenhuma chave ou senha fica gravada no código: tudo vem dos secrets.

## Uso diário

- **Criar uma busca:** *Issues → New issue → ✈️ Monitorar passagem*. Complete o título
  (mantendo `[Passagem]` no início), preencha os campos e envie. A primeira verificação
  acontece na hora.
- **Editar uma busca:** abra a issue, menu **···** → **Edit**, altere os valores (sem apagar as
  linhas `### ...`) e salve. O robô valida de novo, **zera o histórico** daquela busca e
  verifica na hora.
- **Parar uma busca:** feche a issue. Reabrir recomeça o monitoramento do zero.
- **Verificar agora:** *Actions → Monitor de passagens → Run workflow*. Só são consultadas as
  buscas cuja frequência já venceu.
- **Histórico:** fica em `data/historico.json` (até 500 registros por busca), commitado pelo
  próprio workflow quando muda.

Os avisos chegam por e-mail e também como comentário na issue. Confirme sempre o preço no
site antes de comprar: o valor pode mudar entre a verificação e a compra.

## Consumo da SerpApi

Cada verificação de cada busca gasta **1 consulta**. O plano grátis dá **250 consultas por mês**.

| Frequência | Consultas por mês (1 busca) | Buscas que cabem no plano grátis |
|------------|-----------------------------|----------------------------------|
| 1 h | ≈ 720 | nenhuma |
| 2 h | ≈ 360 | nenhuma |
| **3 h (padrão)** | **≈ 240** (8 por dia × 30 dias) | **1** |
| 6 h | ≈ 120 | 2 |
| 12 h | ≈ 60 | 4 |
| 24 h | ≈ 30 | 8 |

Com mais de uma viagem ao mesmo tempo, aumente o intervalo ou assine um plano pago. Se a cota
acabar, o robô comenta uma vez na issue com a mensagem da SerpApi e volta a funcionar sozinho
quando a cota renovar.

**GitHub Actions:** em repositório privado, a conta gratuita inclui 2.000 minutos por mês. O
robô faz cerca de 720 execuções mensais de menos de 1 minuto (cobradas como 1 minuto cada).
O GitHub desativa workflows agendados após 60 dias sem atividade no repositório; os commits do
histórico contam como atividade, e basta reativar na aba *Actions* se isso acontecer.

## Desenvolvimento

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Os testes rodam offline: GitHub, SerpApi e SMTP são simulados.

| Arquivo | Papel |
|---------|-------|
| `monitor/formulario.py` | lê e valida o formulário; gera os parâmetros da SerpApi |
| `monitor/serpapi.py` | consulta a SerpApi e extrai o menor preço |
| `monitor/regras.py` | regra de "abaixo do mercado" e trava anti-spam |
| `monitor/historico.py` | estado e histórico em `data/historico.json` |
| `monitor/github.py` | lista issues, comenta e fecha |
| `monitor/correio.py` | envio por SMTP |
| `monitor/mensagens.py` | textos dos comentários e e-mails |
| `monitor/principal.py` | orquestra tudo; um erro em uma busca não afeta as outras |

Cada busca já carrega o próprio e-mail de destino, e as dependências externas são injetadas em
`Monitor`, o que facilita trocar issues por outro cadastro quando houver vários usuários.
