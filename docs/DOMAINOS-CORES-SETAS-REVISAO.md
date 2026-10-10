# Cores das setas — diagnóstico R13

2026-10-10. Análise das capturas existentes, sem novos comandos na VM ou testes
da suíte. **Aceitação visual aberta.** A referência continua sendo SR10.4 / VUE 2.01.

| Célula GTK3 na captura R13 | Comparação com a célula normal da VM |
| --- | --- |
| Baixo e direita | Mesmas cores e pixels: 0 diferenças em cada célula de 11 × 11. |
| Cima e esquerda | Paleta desabilitada exportada pelo KDE: 121 pixels diferentes por célula; diferença máxima de 11 por canal. |

As cores normais são face `#78a0d5`, luz `#c4d5ed`, sombra `#3e536e` e
trilho `#6688b5`. As desabilitadas nessa captura são `#6d99d0`, `#bfd2ea`,
`#384f6c` e `#5d82b1`, respectivamente. Esses valores documentam uma captura;
**não são cores fixas para inserir no tema**.

A atribuição ao estado desabilitado vem da coincidência integral com os papéis
exportados e com seu desenho gerado. O Trash Can vazio da VM mostra as quatro
setas com a paleta normal. Isso não comprova a aparência de um widget Motif
realmente insensível: esse estado continua sem regra histórica confirmada.
Não é correto concluir que todas as diferenças de setas do Linux têm esta causa.

O resultado anterior de igualdade dos quatro triângulos cobria o desenho normal.
Não validava a harmonia de todos os estados GTK, nem Qt, Kvantum ou Plasma.
A revisão atual explicita essa lacuna em vez de repetir aquela prova.

Os [dados e hashes](review/arrow-color-evidence.json) preservam a comparação.
Os recortes são pixels nativos, sem interpolação:

| Direção | VM, estado normal | GTK3, captura R13 |
| --- | --- | --- |
| Cima | [Original](review/images/arrow-colors-r13/up-VM-normal.png) | [Desabilitada](review/images/arrow-colors-r13/up-R13-current.png) |
| Baixo | [Original](review/images/arrow-colors-r13/down-VM-normal.png) | [Normal](review/images/arrow-colors-r13/down-R13-current.png) |
| Esquerda | [Original](review/images/arrow-colors-r13/left-VM-normal.png) | [Desabilitada](review/images/arrow-colors-r13/left-R13-current.png) |
| Direita | [Original](review/images/arrow-colors-r13/right-VM-normal.png) | [Normal](review/images/arrow-colors-r13/right-R13-current.png) |

## Correção aplicada — limites da rolagem GTK3

O contrato agora distingue o bloqueio de uma seta por chegar ao fim da rolagem
do estado insensível de todo o controle. No primeiro caso, a seta mantém os
papéis atuais do scrollbar pai, inclusive sem foco; o clique continua bloqueado.
No segundo, usa os papéis KDE desabilitados. A [regra comum](DOMAINOS-REGRAS-ROLAGEM.md)
identifica essa decisão como adaptação baseada na continuidade da paleta nativa,
sem atribuir ao SR10.4 uma aparência de `XtSensitive=False` ainda não comprovada.

O ensaio focado passou **468/468** verificações em GTK3 real: azul, cinza, escuro
e amarelo, com limites inferior/superior, sem foco e contêiner insensível. Foram
verificados pixels da janela, cantos e 64 cliques bloqueados. Os quatro insumos
são snapshots reais dos papéis KDE da ponte, normalizados sem inventar cores;
este ensaio não testa novamente a troca de esquema ao vivo nem o exportador.

Nas duas posições limite com a paleta azul, as oito células das setas coincidem
com os recortes normais da VM: **0 pixels diferentes**. Na comparação dos papéis
gerados, somente a paleta escura apresenta arredondamento de até uma unidade de
canal; geometria e captura efetiva não têm corte ou diferença de composição.

| Direção | GTK3 corrigido, pixels nativos |
| --- | --- |
| Cima | [Recorte](review/images/arrow-colors-boundary-r2/up-GTK3-corrected.png) |
| Baixo | [Recorte](review/images/arrow-colors-boundary-r2/down-GTK3-corrected.png) |
| Esquerda | [Recorte](review/images/arrow-colors-boundary-r2/left-GTK3-corrected.png) |
| Direita | [Recorte](review/images/arrow-colors-boundary-r2/right-GTK3-corrected.png) |

Os [resultados e hashes](review/arrow-boundary-color-result.json) identificam o
escopo. As três identidades GTK têm o mesmo CSS corrigido; 757 arquivos de
GTK2, GTK4, Kvantum e desenho compartilhado permaneceram iguais. A prévia R13
congelada continua preservada e contém o desenho anterior, sem atualização no lugar.

Próximo passo: a moldura principal de GtkTreeView preenchida. A família GTK3
continua parcial; as outras famílias não herdam esta prova. A
[prancheta visual](review/visual-checklist.json), grupo V01, continua sem
aprovação manual preenchida pela IA.
