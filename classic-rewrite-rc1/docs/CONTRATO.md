# Contrato da revisão consolidada

## Separar fidelidade comprovada de adaptação

Aparência em repouso: reproduz os recortes de referência usados no desenvolvimento,
excluindo texto e aplicativos. Esses mesmos recortes são dados de construção,
não um teste cego de identidade com qualquer versão do IRIX.

Pressão: usa o princípio de inversão de sombras documentado no CDE/Motif, aplicado
à geometria IRIX já reconstruída. Não usa as cores adicionais de hover do antigo
Irixium. Hover é graficamente inerte, mesmo que a janela ganhe foco e mude de paleta.

Indisponibilidade: símbolos claros/escuros sem contorno preto; adaptação da base,
não comprovação de um decalque histórico específico do 4Dwm.

## Estados e invariantes

| Eixo | Estados tratados |
|---|---|
| Janela | ativa/inativa, normal/maximizada, largura suficiente/reduzida |
| Capacidade | minimizar permitido/proibido, maximizar permitido/proibido |
| Ponteiro | fora/dentro, pressionado dentro/fora, solto, cancelado |
| Menu | clique esquerdo pendente, duplo clique, manter pressionado, clique direito; popup nativo externo |
| Instalação | verificada, preparada, instalada, restaurada ou pendente de recuperação |

O hover não muda pixels do botão. Pressão não desloca símbolos. A janela inativa
não é tratada como indisponível. A perda de capacidade durante o gesto cancela-o;
reabilitar o botão não ressuscita esse gesto. Não há ação a partir de uma soltura
sem pressão válida. Uma segunda tecla do mouse não substitui a primeira capturada.
O fechamento por duplo clique é habilitado pela preferência LOCAL
`menuDoubleClickClosesWindow` (padrão true), não pela preferência global do KDE.
A configuração global não é escrita. O temporizador resolve apenas a ambiguidade
de clique simples; não altera os pixels nem simula um estado de popup aberto.
A ação fica pendente após a primeira soltura esquerda. O evento nativo de duplo
clique cancela essa pendência antes de solicitar Fechar. Fechamento depende também
da capacidade closeable conferida no adaptador KWin.

Um único Canvas contém os elementos gráficos; texto usa a renderização nativa
separada. A grade e as capacidades do controlador são as mesmas do desenhista.
Em janelas extremamente estreitas, alvos que colidiriam deixam de ser exibidos;
isso não é confundido com desenho desativado por capacidade. A posição dos três
controles em larguras normais permanece a da referência. Altura insuficiente
recorta o desenho sem desenhar fora da superfície.

## O que NÃO é prometido

- Identidade tipográfica ou reprodução universal de variantes do IRIX.
- Suavização perfeita em escala fracionária; o instalador não a modifica.
- Estado visual persistente de popup sem notificação real do KWin.
- Equivalência completa dos grabs X11/dtwm com o popup nativo Wayland/KWin.
- Compatibilidade homologada com todas as versões do Plasma.
- Aprovação de runtime baseada em contagem de testes JavaScript.

Alvo principal: Plasma 6.3.6, Qt 6.8.2, Wayland, tela em 100%, conforme informado
pelo usuário. A API foi confrontada com o ramo Plasma/6.3 do KDE; a candidata
precisa do ensaio real para fechar a homologação.
