# I120 — fontes e equivalência de medidas

Referência exclusiva: Domain/OS SR10.4 com HP VUE2.01, na VM existente.
Investigação autorizada na revisão1. Nenhuma fonte do tema foi substituída.

## Referência confirmada

| Uso/configuração | Fonte resolvida no servidor | Medidas |
| --- | --- | --- |
| `*FontList`, `*systemFont` e alias `system16` | Bitstream Swiss742 Bold, HP-Roman8 | 16px; ascendente12, descendente4; proporcional |
| `*Font`, `*userFont`, XmText e XmTextField | Bitstream Prestige Medium, HP-Roman8 | 16px; ascendente12, descendente4; avanço8px |
| Data do painel, recurso `fontList1/2: system17` | Bitstream Swiss742 Bold | 17px; ascendente13, descendente4 |
| Primeira linha da data nas configurações HighRes, alias `system23` | Bitstream Swiss742 Medium | 23px; ascendente18, descendente5 |

`xlsfonts -o` abre a fonte solicitada. A simples enumeração de um padrão
retornou também uma Prestige de23px por conter120 no campo de largura média;
essa entrada não é a fonte selecionada pelo padrão da sessão. A resolução
OpenFont e a propriedade FONT ficam preservadas nas consultas.

As dimensões de tinta de seis textos coincidem com os pixels da captura:
OK16×9, Cancel39×9, Help24×12, Terminal49×9, Oct11 com espaço42×10 e Fri17×10.
Isso confirma consistência entre a amostra e as métricas consultadas. Não
substitui introspecção dos widgets nem prova que duas fontes têm glyphs iguais.
O campo de título e os rótulos coincidem com as métricas da Swiss16; a data
coincide com as da Swiss17, conforme o recurso específico do painel.

## Alternativas medidas, ainda sem escolha

| Referência | Alternativa/Pango | Resultado da amostra ASCII |
| --- | --- | --- |
| Swiss16 Bold | Nimbus Sans Bold12px | Diferença média absoluta de avanço0,83px nos seis textos; os limites de tinta ainda diferem |
| Swiss16 Bold | Liberation Sans Bold12px | Mesma diferença média de avanço; descida e contorno diferem |
| Prestige16 | Nimbus Mono PS13px | Mesmo avanço inteiro em Pango, mas desenho e altura não equivalem |
| Prestige16 | Liberation Mono13px | Mesmo avanço inteiro em Pango; glyphs e descendentes diferem |

O tamanho nominal12 ou13 não significa que o controle terá essa altura total.
Para comparar escala, considerar tinta, avanço, ascendente, descendente e
espaçamento do widget separadamente. Usar16px modernos só por a fonte histórica
se chamar16px produziria uma equivalência não demonstrada.

Qt5.15.15 e Qt6.8.2 foram medidos por QFontMetricsF na plataforma offscreen.
O avanço das candidatas próximas também difere da referência; algumas métricas
verticais e de tinta diferem entre as versões Qt. QFontInfo retornou exactMatch
falso para Nimbus no Qt6: o resultado permanece explícito, sem afirmar que o
arquivo específico foi confirmado nessa resolução. Fontes medidas por Pango
não são uma prova automática de GTK2/4, Motif, Kvantum ou Plasma.

## Proveniência e limites

As fontes da VM declaram Copyright1989 Bitstream, All rights reserved.
Não foi encontrada licença de redistribuição; seus binários não foram copiados
ou incluídos no projeto. As alternativas instaladas possuem declarações nos
pacotes locais: Nimbus/URW Base35, AGPL3 com exceção de fonte; Liberation,
SIL-OFL1.1. Não foram empacotadas ou modificadas nesta investigação.

A comparação histórica é ASCII. Roman8 não equivale a Unicode; preservar
acentos e cobertura do locale continua obrigatório na ferramenta. O avanço
igual de uma sequência não aprova aparência, Unicode ou substituição geral.
As fontes e tamanhos privados já aprovados do protótipo continuam preservados.

## Provas reproduzíveis e próximo passo

- [Consultas X11 e hashes](referencias/domainos-sr104/I120-QUERIES-X11.json).
- [Métricas e pixels dos textos nativos](referencias/domainos-sr104/I120-TEXTOS-CAPTURA-METRICAS.json).
- [Comparações completas](referencias/domainos-sr104/I120-COMPARACAO-METRICAS.json).
- [Proveniência das alternativas](referencias/domainos-sr104/I120-PROVENIENCIA-ALTERNATIVAS.json).
- [Leitor comparativo](referencias/domainos-sr104/compare_font_metrics.py).

Próximo: comparar as amostras gráficas de Motif/GTK3 usando as fontes realmente
carregadas e registrar diferenças de glyphs/Unicode. Só depois selecionar
equivalentes; instalar ou trocar fontes no tema permanece separado dessa prova.
## Prova gráfica Motif/GTK3

Os [rótulos GTK3 reais](referencias/domainos-sr104/i120-native-fonts/gtk.png)
e os [conjuntos Motif atuais](referencias/domainos-sr104/i120-native-fonts/motif.png)
foram capturados em escala1, com face/texto obtidos dos papéis KDE atuais.
Quinze textos Motif retornaram UTF-8 idêntico; vinte rótulos GTK3 também
conservaram o texto e não apresentaram glyphs ausentes nessa amostra.

O FontSet `fixed` observado na prévia privada não contém ISO10646. A captura
mostra outro sinal no lugar do travessão, embora o texto permaneça correto.
Helvetica com fallback incluiu ISO10646 e desenhou esta amostra; isso não
comprova cobertura de todos os idiomas. I179 propõe tratar esse limite no
laboratório, sem autorização automática a partir desta investigação.

Dezesseis [comparações de pixels fortes](referencias/domainos-sr104/I120-GLYPHS-GTK3-COMPARACAO.json)
dos rótulos GTK3 com a captura SR10.4 mostraram máscaras diferentes em todos
os casos. O alinhamento foi pelo limite da tinta, sem interpolação. O limiar
de intensidade explicita a diferença entre antialiasing e pixels binários;
a estatística de interseção não é percentual de fidelidade visual do tema.

A primeira prova GTK herdou Wayland e falhou ao consultar uma janela X11.
O processo próprio foi encerrado, sem envio de input ou fechamento de
aplicações do usuário. O ambiente foi corrigido para X11 privado e a prova
final terminou normalmente; a falha e seus artefatos ficaram preservados no
[recibo](review/I120-NATIVE-FONTES-20261011.json).

I120 cerca de80% da investigação. Ainda faltam cobertura explícita das outras
famílias nativas e apresentação final das alternativas para escolha.
Não foi aplicada nem aprovada uma substituição no tema.

## Qt5 e Qt6: rótulos nativos

As capturas `i120-native-fonts/qt-result/qt5.png` e `qt6.png` usam
QLabel reais na plataforma offscreen, escala1, com papéis de janela/texto KDE.
Vinte rótulos por versão conservaram seus textos, com zero índices de glyph
ausente na amostra. QTextLayout registra também as famílias de cada glyph run.
Qt5.15.15 retorna exactMatch verdadeiro nas quatro alternativas; Qt6.8.2
retorna falso para as duas Nimbus. O resultado não é ocultado nem equivale
a identificar o arquivo efetivo em todos os fallbacks. As imagens mostram
diferenças de desenho/escala entre as versões; tamanho nominal não as elimina.

### Cobertura desta investigação

| Família | Evidência atual | Limite |
| --- | --- | --- |
| SR10.4/VUE2.01 | Recursos, fontes resolvidas X11, métricas e captura | Somente referência histórica autorizada |
| Motif atual | FontSets e captura nativa, leitura UTF-8 | fixed não cobre o travessão; I179 autorizado para tratamento separado |
| GTK3 | Pango, rótulos nativos e máscaras comparadas com VM | Candidatas têm desenhos diferentes |
| Qt5/Qt6 | Métricas e QLabel nativos, glyph runs | Sem prova de estilo Kvantum/Plasma |
| GTK2/GTK4 | Equivalência própria pendente | Não herdam automaticamente resultados GTK3; I167/I168 autorizados |
| GTK1/GTK5 | Investigação de disponibilidade separada | Nenhuma renderização substituta constitui prova |
| Kvantum/Plasma | Etapas próprias previstas | Não inferir adaptação pelas métricas Qt |

I120 cerca de90%: identidade/proveniência histórica e comparação Motif/GTK3/Qt
registradas. Falta consolidar a proposta de equivalentes por papel e seus limites
para a escolha do usuário. Preservar fonte atual; nenhuma instalação nesta etapa.

## Proposta consolidada por papel — pesquisa concluída

| Uso | Candidata para comparação manual | Diferença conhecida |
| --- | --- | --- |
| Controles | Liberation Sans Bold12px; Nimbus Sans Bold12px como alternativa | Avanço médio0,83px distante nos seis textos; glyphs diferentes |
| Texto | Liberation Mono13px; Nimbus Mono PS13px como alternativa | Avanço8px em Pango,7,796875px Qt; altura/desenho diferentes |
| Data | Liberation Sans Bold14px | Oct11/Fri em Pango têm avanço−2/−1px e altura de tinta10px igual à Swiss17 |

A medição da data está em `I120-DATA-PANGO.json`, reproduzível com
`/usr/bin/python3 compare_date_fonts.py`. Nimbus13 mantém altura10px, mas
fica6px mais estreita em Oct11; Nimbus14 reduz a diferença de avanço, porém
aumenta a altura em1px. Assim, não estender automaticamente a candidata12px
de controles para a data. O painel conserva a tipografia privada aprovada.

`I120-PROPOSTA-EQUIVALENTES.json` separa proposta, aplicação e aprovação.
Liberation é a proposta inicial de comparação; escolher Nimbus continua possível.
Nenhuma é a fonte original. Não alterar espaçamento entre letras para esconder
essas diferenças sem uma regra e comparação próprias. Tamanho de controle,
margens e fonte devem permanecer medidas independentes.

I120:100% da **investigação solicitada**, com identidade/proveniência, métricas,
comparações nativas e proposta por uso entregues. Isso não conclui adaptação de
fontes em todos os toolkits, nem seleção/aprovação humana ou instalação.
Próxima implementação autorizada: I179, cobertura/fallback do Motif.
