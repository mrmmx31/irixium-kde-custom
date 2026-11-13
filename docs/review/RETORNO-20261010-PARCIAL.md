# Retorno parcial das pranchetas — 2026-10-10

Foram salvas **duas avaliações**, V01 e V02. Os dez grupos do projeto
(P01–P10) e os oito visuais restantes (V03–V10) continuam **sem resposta**.
Silêncio não foi convertido em aprovação, falha ou pedido de nova confirmação.

| Item | Avaliação humana | Consequência para o trabalho |
| --- | --- | --- |
| V01 — cores das setas | Confirmado. O usuário comparou com a VM e informou que as setas das barras GTK estão corretas. | Conservar essa avaliação no escopo observado. Novo defeito: o sinal **+** do spin tem cor diferente do **−**; correção pendente. |
| V02 — barras, relevo e encaixe GTK3 | Confirmado. O usuário pediu usar essas configurações como exemplo para as demais versões GTK. | Adotar o GTK3 observado como referência de adaptação. Cada outra família continua com comparação própria; a moldura principal da GtkTreeView preenchida permanece uma pendência técnica explícita. |

## Escopo da avaliação

A prévia disponível para essa avaliação é o snapshot **R13**, preservado.
A correção posterior **r2 das cores nos limites GTK3** tem
[evidência técnica própria](../DOMAINOS-CORES-SETAS-REVISAO.md), mas ainda não
foi apresentada nessa janela Xephyr. Não atribuir a essas respostas uma
aprovação humana do código r2, de todas as famílias ou de estados históricos
que não foram observados. A confirmação do V02 também não apaga a limitação
de desenho da moldura da tabela.

Trechos do retorno que orientam a próxima ação:

> “Corrija agora o sinal de + que está com cor diferente do - lá no spinl”

> “Use inclusive essas configurações para comparar as demais versões do GTK.”

## Registro preservado

- Origem local: `/tmp/domainos-review-1000/respostas.json`, UID 1000.
- Gravação: `2026-10-10T12:54:02.229930+00:00`; `submitted: true`.
- SHA-256: `0196d67e8dd8b3f1e8320669a9fd469a6202da80bae1e0490cf7f07b91730952`.
- Tamanho: 7005 bytes. Os 20 hashes de critérios coincidem com os datasets 1.0.
- JSON de respostas, datasets e janela da prancheta não foram alterados nesta
  leitura. Não havia diretório de histórico na leitura registrada.

Este retorno orienta a [fila de revisão](../DOMAINOS-FILA-REVISAO-VISUAL.md)
e o [resumo das pranchetas](../DOMAINOS-CHECKLISTS-REVISAO.md). Nenhum teste
do produto ou comando na VM foi executado para registrar as respostas.
