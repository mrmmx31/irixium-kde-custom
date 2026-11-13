# T01 — contrato de medidas do laboratório

O editor solicita uma largura e uma altura por controle. Zero delega o eixo ao
layout nativo da amostra; um número positivo é uma proposta. No GTK3,
`set_size_request` estabelece um mínimo, não promete diminuir o controle abaixo
do mínimo exigido pelo conteúdo e pelo estilo. A interface mostra separadamente
pedido em edição, alocação efetiva e mínimo/preferido do GTK3.

As medidas GTK3 usam pixels lógicos e informam o fator de escala. Comparação
1:1 com os pixels X11 do Motif só é válida com escala GTK3 igual a 1. Não converter
um resultado com escala 2 em igualdade de tamanho físico. A prévia acoplada e a
separada possuem medidas independentes, identificadas no evento.

A referência Motif usa sua receita própria. `XtQueryGeometry` fornece o tamanho
preferido quando disponível; na ausência de um eixo preferido, o valor mostrado
é o tamanho atual. Não existe um mínimo público genérico para todos os controles
Motif: a interface informa essa ausência em vez de inventar um número. A largura
inicial da amostra Motif inclui decisões de montagem; não é um default universal.

Os eventos GTK3 carregam o hash da cena aplicada, identidade do controle, origem,
espaço de coordenadas, escala e medidas. O controlador rejeita eventos de outra
cena e a visão conserva medidas ao atualizar somente os campos do editor. Uma
cena nova invalida a medida antiga. O emissor ignora callbacks de controles
removidos, elimina duplicatas por cena/medida e libera os gestos antes de destruir
os controles. Medidas são efêmeras; não alteram projetos nem evidências históricas.

O botão de seta GTK3 automático continua seguindo a geometria da receita de seta;
os demais controles não recebem mais o mínimo oculto de 140 × 44. As células de
montagem mantêm sua organização, mas não representam a borda do controle medido.
Nenhuma cor foi introduzida: a interface e as prévias conservam os papéis atuais.

## Verificação e limites desta etapa

`make -C tools/theme-lab all check` compila e verifica modelo, parser e cenas.
`make -C tools/theme-lab check-native-metrics` usa Xvfb privado para a visão
Motif e os controles reais GTK3 acoplados/separados. O ensaio inclui redimensionar
um botão para 220 × 80, correspondência entre evento e alocação, origem/escala,
rejeição de callback antigo, duplicatas, independência da receita Motif e
preservação/invalidação do cache.

`make -C tools/theme-lab check-controller-spin` exercita o controlador real,
geração privada e prévias GTK3 reais em Xvfb/bwrap. Requer Xvfb, xauth,
xdotool, bubblewrap, unshare, dbus-run-session, ImageMagick, GTK3/PyGObject e
o leitor de cores KDE compilado (`make native-colors`). O display tem autoridade
própria, rede isolada e HOME descartável; não acessa o perfil pessoal nem o bus
do desktop. A saída fica em `.qa-theme-lab-spin-*` para evitar consumir os
inodes compartilhados de `/tmp`.

O ensaio usa cliques X11 nas setas dos spins: largura no modo manual, altura no
automático. Confere as duas alocações, a espera por Atualizar e a independência
da referência Motif. As fixtures de mínimo/automático usam a API pública do
campo Motif e seu callback real; não comprovam atalhos de teclado. A comparação
das fixtures exige cena aplicada e observação posterior à invalidação, evitando
aceitar medidas de uma cena anterior. Capturas e resultados identificam o escopo.

Essas provas não certificam fidelidade histórica de SR10.4. A VM não foi
modificada. Demais toolkits e o tema permanecem fora deste escopo. A edição segura do laboratório agora possui prova própria:
`.qa-theme-lab-spin-8wih82ap/RESULTADO.json`. Foram comprovados atalhos de
edição, múltiplos Undo/Redo, texto UTF-8, menu, salvamento, recuperação após
reabrir e históricos independentes ao trocar controles. Home/End movem o cursor
sem mudar o valor numérico. A entrega pessoal ainda depende da preservação
do projeto e das entradas da instância atual; não foi realizada por esses ensaios.


## Revalidação T01 — 2026-10-18

A build principal atual passou com C99 `-Wall -Wextra -Werror`. A visão Motif
nativa passou alocação, posição/peças e invalidação de medidas antigas; a sonda
GTK3 passou 2/2 testes para canvas acoplado e separado, redimensionamento e
rejeição de callbacks obsoletos. O controlador real passou o percurso de spin:
221×80 solicitado foi aplicado às duas prévias; pedido 1×1 e modo automático
resultaram em 70×30 nas duas, o mínimo/preferido observado para essa amostra.
Escala GTK3 e Motif = 1.

O primeiro ensaio via Xvfb não conectou ao display privado :199. Repeti no
Xephyr próprio :76 sem tocar nas outras sessões; o ensaio completou. Recibo,
resultado, hashes e captura nativa estão em
[ T01-METRICAS-NATIVAS-REVALIDACAO-20261018.json ](review/T01-METRICAS-NATIVAS-REVALIDACAO-20261018.json) e
`~/tempia/t01-controller-rerun-20261017/theme-lab-spin-gqrz67lu/`. Os avisos
de fontes/charset Motif continuam limitando a prova tipográfica. Abrir o binário
principal diretamente não disponibiliza o worker GTK; para avaliação integrada
é necessário usar o launcher privado documentado acima. Não registrei aprovação
visual humana.
