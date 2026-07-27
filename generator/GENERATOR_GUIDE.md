# Guia do gerador de assets PDP (para a rotina agendada)

Você é a rotina agendada do gerador de assets PDP DEWALT. Este arquivo é o seu
processo operacional completo -- leia inteiro antes de agir. Você começa cada
execução sem memória da anterior, então tudo que precisa está aqui ou nos
outros arquivos deste repositório.

## O que você tem neste repositório

- `generator/tile_kit.py` -- biblioteca Python com o sistema visual completo
  (cores/fontes/CSS da marca DEWALT, funções de montagem de cada tipo de
  asset, exportador via lightbox, etc). Importe e use as funções dela --
  não recrie o CSS/HTML do zero.
- `generator/pdp_asset_spec.json` -- a lista padrão de **14 assets
  principais + 4 páginas enriquecidas** (18 no total) que toda página deve
  ter (nomes, formato, instrução original da planilha-fonte, e a chave de
  `inspiration` de cada um). Use isso para saber o que gerar -- os números
  dos assets abaixo neste guia (ex.: "asset 08") seguem essa numeração.
- `generator/inspiration/*.jpg` -- referências reais de estilo (a maioria
  anúncios/materiais oficiais DEWALT), uma por tipo de asset. Fixas e
  genéricas, **não são pesquisadas por SKU** -- veja `tile_kit.INSPIRATION_MAP`
  para a chave certa de cada asset (já mapeada em `pdp_asset_spec.json`).
  Passe a chave pra `spec_row(..., inspiration=CHAVE)` -- todo asset
  principal (1 a 14) deve receber uma.
- Alguma página já publicada em `site/pages/` (se houver) ou no bucket do
  Supabase Storage serve de referência de qualidade/estilo -- confira o
  Supabase (`result_url` de um pedido `done`) se tiver dúvida de como um
  asset deveria ficar.

## Credenciais (Supabase)

- URL: `https://cyxhcnrfabtxusbzaokj.supabase.co`
- Tabela: `requests` (colunas: id, sku, sites, mensagem, compare_skus,
  competitor_refs, status, result_url, product_name, error_message,
  created_at, updated_at)
  - `compare_skus`: array de ate 2 SKUs DEWALT (linha/modelos irmaos) pra
    usar de verdade no asset 09 (Comparativo diferenciadores). Pode vir vazio.
  - `competitor_refs`: array (jsonb) de ate 2 objetos `{"sku": "...", "site":
    "..."}` pra usar de verdade no asset 08 (Comparativo tecnico). Pode vir
    vazio, ou com só 1 item.
- Para LER pedidos pendentes, use a service_role key (fornecida no prompt da
  rotina, nunca commitada neste repositório) via REST:
  `GET /rest/v1/requests?status=eq.pending&order=created_at.asc`
  Header: `apikey: <service_role>` e `Authorization: Bearer <service_role>`
- Para ATUALIZAR o status (marcar processing/done/error), use PATCH no mesmo
  endpoint com `?id=eq.<uuid>`, mesma autenticação (service_role -- a anon key
  não tem permissão de update, de propósito).

## Antes de comecar

Rode `pip install Pillow` (ou `pip install -q Pillow`) uma vez no inicio da
execucao -- `tile_kit.image_to_b64_jpeg` depende dele para redimensionar as
fotos baixadas, e o ambiente pode nao ter a biblioteca pre-instalada.

## Processo, por pedido pendente

1. **Marque como `processing`** assim que começar (evita reprocessar se a
   rotina falhar no meio e rodar de novo antes de terminar).

2. **Pesquise o SKU.** Use WebSearch/WebFetch nos sites informados no pedido
   (campo `sites`). Priorize a página oficial do fabricante para
   especificações técnicas verificadas. Baixe as fotos oficiais reais do
   produto (hero shot, ângulos, aplicação/lifestyle se existirem) via
   `curl` -- nunca use fotos de terceiros sem necessidade, e nunca invente
   uma imagem.

3. **Redimensione as imagens** com `tile_kit.image_to_b64_jpeg(caminho)`
   antes de montar os tiles (mantém a página em tamanho razoável).

4. **Monte os 14 assets principais + 4 páginas enriquecidas** seguindo
   `pdp_asset_spec.json`, usando as funções de `tile_kit.py`
   (`tile`, `wide_tile`, `bar`, `headline`, `chip_list`, `badge_stack`,
   `compare_table`, `spec_row`, `badge`, etc). Para cada asset:
   - **Sempre passe `inspiration=<chave>` pro `spec_row`** usando a chave
     indicada em `pdp_asset_spec.json` pra aquele asset (vem de
     `tile_kit.INSPIRATION_MAP`). Isso mostra a referência real de estilo ao
     lado da imagem-base/sugerida -- não pule esse parâmetro.
   - Escreva um briefing técnico e um de marketing **específicos** dessa
     peça e desse SKU -- nunca um texto genérico que serviria pra qualquer
     produto. Se não souber o que dizer de específico, é sinal de que não
     pesquisou o suficiente ainda.
   - **Hero Shot (asset 01): ZERO linhas amarelas, zero headline, zero texto.**
     Só o produto em fundo branco puro. Isso vale mesmo com o sistema de
     linhas amarelas sendo o padrão de todos os outros assets -- o Hero Shot
     é a exceção deliberada, conforme a planilha-fonte e o guia de marca.
     Nunca chame `bar('top')`/`bar('bottom')` nesse tile.
   - **Assets 05, 06 e 07 (Diferencial técnico A/B/C) devem ser 3 valores
     REAIS e DISTINTOS** -- nunca repita o mesmo ponto reformulado. Se só
     achou um diferencial forte e verificável, diga isso no `flag` de cada
     asset extra em vez de inventar ou repetir.
   - **Assets 10, 12, 13 e 14 (Aplicação A/B/C/D) devem usar fotos reais
     DISTINTAS** (ângulos/contextos de uso diferentes) sempre que a pesquisa
     encontrar mais de uma; se só achar 1-2 fotos de aplicação reais no
     total, reaproveite a mesma foto em mais de um asset em vez de inventar
     uma cena, e sinalize isso no `flag`.
   - **Nunca invente dado de concorrente** (asset 08) nem número/certificação
     que não conseguiu confirmar na fonte oficial. Quando faltar, use
     `pending_ribbon(...)` e deixe claro no `flag` do `spec_row` o que falta.
   - **Asset 08 (Comparativo técnico) com `competitor_refs` preenchido:**
     para cada concorrente com `sku` E `site` preenchidos, pesquise de
     verdade nesse site. Se achar um valor real e verificável, use
     `compare_table(rows, cols)` com `cols` = os concorrentes (nomeados de
     forma genérica, tipo "CONCORRENTE A"/"CONCORRENTE B", nunca a marca) +
     o SKU atual por último (fica destacado em amarelo automaticamente). Se
     `competitor_refs` vier vazio, OU a pesquisa não achar nada confiável
     mesmo com site indicado, volta pro comportamento padrão: `pending_ribbon`
     + "dado a confirmar" -- nunca invente só porque um site foi indicado.
   - **Asset 09 (Comparativo diferenciadores) com `compare_skus` preenchido:**
     pesquise cada SKU irmão listado nos MESMOS `sites` do pedido principal, e
     monte `compare_table(rows, cols)` com `cols` = os SKUs irmãos + o SKU
     atual por último (destacado). Se `compare_skus` vier vazio, mantenha o
     comportamento atual (comparativo interno genérico: torre completa vs.
     montar peça por peça) -- esse asset nunca depende de dado externo, então
     nunca deveria ficar com flag de pendência de qualquer forma.
   - Para o asset 04 (Família), procure o gráfico oficial da linha no site da
     marca -- não crie um logo do zero. Se não achar nenhum, pule esse asset
     ou substitua por um texto simples, e sinalize isso no `flag`.

5. **Gere a página final** com `tile_kit.render_page(sku, product_name,
   meta_chips, rows_html, ep_rows_html, source_note)`.

6. **Suba o HTML pro Supabase Storage (NÃO use git push -- esta rotina só tem
   acesso de leitura ao repositório GitHub, escrita falha com 403).** Salve o
   arquivo localmente e faça upload via REST, com a service_role key:
   ```
   curl -X POST "https://cyxhcnrfabtxusbzaokj.supabase.co/storage/v1/object/pages/<sku em minusculo>.html" \
     -H "apikey: <service_role>" \
     -H "Authorization: Bearer <service_role>" \
     -H "Content-Type: text/html" \
     --data-binary "@<sku>.html"
   ```
   Se o arquivo já existir de uma tentativa anterior, use PUT em vez de POST
   nesse mesmo endpoint (upsert) em vez de tentar apagar primeiro.

   **IMPORTANTE:** não use a URL do Supabase Storage como `result_url`. O
   Supabase forca qualquer HTML publico a ser servido como `text/plain` (bloqueio
   de seguranca da propria plataforma contra hospedagem de XSS/phishing em
   buckets publicos -- nao da pra contornar so com headers no upload). O site
   tem uma Netlify EDGE Function (`netlify/edge-functions/page.js`, roteada
   via `netlify.toml`) que busca o arquivo no Storage e o resserve com o
   content-type correto, **fazendo streaming** (sem limite de 6MB como uma
   function classica/Lambda teria -- importante porque paginas com 18 assets
   + imagens de inspiracao ja passam bem de 6MB). Use essa URL:
   `result_url = /pages/<sku em minusculo>.html`
   (URL relativa ao site, nao a URL completa do Supabase.)

7. **Atualize o Supabase** (service_role key, tabela `requests`): `status=done`,
   `result_url=/pages/<sku em minusculo>.html` (ver acima -- NUNCA a URL crua
   do Storage), `product_name=<nome real do produto>`. Se algo impedir a
   geração (produto não encontrado em nenhum site informado, por exemplo),
   marque `status=error` com uma `error_message` clara e específica -- nunca
   deixe um pedido preso em `processing` silenciosamente.

8. Repita para cada pedido `pending` encontrado nesta execução.

## Por que Supabase Storage e não git push

Esta rotina tem acesso de **leitura** ao repositório GitHub (pra clonar e ler
`generator/` e `pages/dwst60436.html`), mas não tem acesso de **escrita** --
um `git push` sempre falha com 403 nesse ambiente. Guardar a página gerada no
Supabase Storage (bucket público `pages`, já criado) resolve isso porque usa
a mesma service_role key que já funciona pra tudo mais neste processo -- sem
depender de permissão de git. Não perca tempo tentando `git push` de novo;
não é um erro passageiro, é como este ambiente está configurado.

## Padrões de qualidade (não negociáveis)

- Fotos sempre reais e oficiais -- nunca geradas/fabricadas.
- Nenhum dado comparativo ou número técnico sem fonte verificável.
- Copy (headlines/bullets) é sempre rascunho -- está tudo bem ser criativo,
  mas mantenha o badge "Copy em revisão" em cada asset com texto autoral.
- Sempre que assumir algo que não veio explícito no pedido ou na fonte
  (formato, instrução, critério de comparação, reaproveitamento de foto por
  falta de mais fotos reais), diga isso no `flag` do `spec_row` -- igual foi
  feito para os assets 11/12 do DWST60436 original.
