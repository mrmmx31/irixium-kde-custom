# Proposta I175 — composição compacta do painel

**Estado:** proposta privada para revisão; nenhuma alteração de produto ou
instalação foi feita. Usa as medidas do recibo
[`VALIDACAO-I174-PAINEL-20261014.json`](VALIDACAO-I174-PAINEL-20261014.json)
e as capturas SR10.4/HP VUE 2.01 e Plasma/KWin já registradas.

## Medidas que restringem o desenho

| Região | VUE SR10.4 | Painel atual | Diferença |
| --- | ---: | ---: | ---: |
| Canvas externo da captura | 947×93 px | 971×109 px | +24×16 px |
| Faixa superior até o início do rodapé | 63 px | 79 px | +16 px |
| Faixa inferior metálica | 30 px | 30 px | igual |

As duas imagens são recortes 1:1. O QML do painel atual desenha em 1942×218 e
usa escala 0,5 para produzir 971×109. O recorte atual tem 8 px pretos à
esquerda; o recibo I174 preserva a dimensão do canvas e registra à parte a
caixa pintada, sem interpretar a margem como arte.

Uma redução uniforme não alcança simultaneamente as dimensões históricas:
ajustar 109 px para 93 px resultaria em cerca de 865×93 px; ajustar 971 px
para 947 px resultaria em aproximadamente 947×106 px. A versão compacta deve
redistribuir os controles na área útil, manter a faixa inferior em 30 px e
reservar 63 px para a região superior. Não esticar o painel inteiro.

## Variantes para escolha

**A — compacto nas dimensões VUE.** Reconstruir a composição em canvas de
947×93 px, com duas faixas de 63 e 30 px. Redistribuir as funções existentes
horizontalmente. O Pager poderá usar a contagem definida em Q355; a faixa de
títulos de janelas só será mantida/posicionada conforme Q356. Q358 decide se
essa dimensão compacta deve substituir o canvas atual.

**B — desenho atual com reordenação.** Manter 971×109 px e a separação atual
das funções. Aplicar a sequência histórica como referência de agrupamento,
sem prometer as dimensões VUE. Q355, Q356 e Q358 continuam decisões distintas.

Em ambas as variantes, preservar relógio/data, indicadores de rede e correio,
Iconbox, lista de janelas, Pager, atalhos de aplicações, bandeja e navegação.
Cada ícone mantém proporção intrínseca e será dimensionado pelo retângulo
medido no VUE e pelo espaço funcional disponível; não deformar bitmap/SVG para
forçar o encaixe. A definição de dimensões finais dos ícones aguarda a medição
pareada das peças correspondentes na captura nativa.

## Regras de implementação se a variante for escolhida

- Derivar chassis, faces, trilhos e textos dos papéis atuais do esquema KDE;
  não gravar cores RGB finais no desenho. A indicação do LED segue somente a
  exceção de sinal já autorizada, com contraste preservado.
- Manter controles funcionais reais e ações atuais, inclusive quando a
  composição mudar; não substituir o painel instalado nesta proposta.
- Comparar a variante escolhida com o SR10.4 em Xephyr a 1:1, registrar hashes,
  medir limites dos grupos e validar quatro esquemas antes de apresentar a
  avaliação manual.

## Pendências registradas

- Q355: quantidade de células do Pager.
- Q356: manter, reposicionar ou remover a faixa de títulos de janelas.
- Q358: conservar a proporção externa atual ou aproximar o recorte VUE.
- A aparência final só pode ser avaliada após uma variante escolhida e
  renderizada; esta proposta textual não é uma renderização nativa.

Não houve alteração do applet, dos SVGs, das preferências KDE, do backup de
Downloads ou da VM. A implementação permanece aguardando as escolhas acima e
a etapa P10, conforme a ordem registrada para I175.
