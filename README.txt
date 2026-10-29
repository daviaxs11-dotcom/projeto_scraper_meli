PROJETO - SCRAPER MERCADO LIVRE EM PYTHON
==========================================

O que foi convertido
--------------------
A lógica da macro VBA foi migrada para Python:

- Aba PRODUTOS
- Consulta somente células destacadas da coluna A
- Busca direta no Mercado Livre
- Ordenação por menor preço
- Sem Apify e sem token
- Remove os resultados anteriores
- Cria/usa a aba RESULTADO MELI
- Evita anúncios duplicados pelo Link
- Grava:
  Código
  Imagem
  Produto
  Marca
  Preço
  Vendedor
  Frete Grátis
  Avaliação
  Link
- Baixa e insere as imagens no Excel
- Formata colunas e preços
- Mostra contadores no terminal
- Se o arquivo for XLSM, abre com keep_vba=True para preservar o VBA existente

COMO USAR
----------

1. Coloque este projeto em uma pasta.

2. Coloque o seu Excel na mesma pasta.

3. Em config.py, ajuste:
   EXCEL_NAME = "nome_do_seu_arquivo.xlsx"

4. Execute:
   instalar.bat

5. Depois execute:
   executar.bat

IMPORTANTE
----------

Este projeto NÃO usa Apify.

Não é necessário:
- APIFY_TOKEN
- APIFY_ACTOR
- aba CONFIG_APIFY

O scraper acessa diretamente a página pública de resultados do Mercado Livre.

SE O EXCEL FOR XLSM
-------------------
Altere EXCEL_NAME para o nome do arquivo .xlsm.

Exemplo:
EXCEL_NAME = "web skraping meli.xlsm"

O openpyxl é chamado com keep_vba=True para preservar o projeto VBA.

REGRAS DA BUSCA
---------------
QTD_RESULTADOS = 0
    Tenta gravar todos os anúncios encontrados nas páginas configuradas.

MAX_PAGINAS = 10
    Limite de páginas consultadas por código.

Se quiser reduzir:
MAX_PAGINAS = 3

Se quiser um limite:
QTD_RESULTADOS = 50

CÉLULAS DESTACADAS
------------------
A consulta continua seguindo a regra da macro:
somente células da coluna A com preenchimento/destaque são consultadas.

OBSERVAÇÃO SOBRE O SCRAPER
--------------------------
O Mercado Livre pode alterar classes HTML e elementos da página.
O scraper possui seletores alternativos, mas mudanças futuras no site
podem exigir ajuste em scraper.py.

NÃO COLOQUE CREDENCIAIS
-----------------------
Não existe .env neste projeto porque o scraper direto não precisa de
token da Apify.

EXECUÇÃO
--------
Duplo clique em:
    instalar.bat

Depois:
    executar.bat

Ou pelo terminal:
    python main.py
