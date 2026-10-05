# Contrato geométrico — Irixium moderno

Perfil padrão: botões 22×22, fator de tamanho Aurorae 1, sem padding adicional e
escala de monitor 100%. Valores em coordenadas lógicas.

## Horizontal

A lacuna entre duas faces é 6. Uma divisória ocupa 2 no centro, deixando 2 de cada
lado: `[face 22][folga 2][divisória 2][folga 2][face 22]`. O passo é 28.

Para um botão em `x` com largura `w`, na linha local:

- Grupo esquerdo: divisória depois da face, `x + w + gap/2 - 1`.
- Grupo direito: divisória antes da face, `x - gap/2 - 1`.

A margem normal da linha de botões é 9, tanto à esquerda quanto à direita. No
perfil SVG, a faixa externa superior/lateral do desenho tem 7; a face começa com
mais duas unidades de folga. A borda de entrada efetiva do KWin pode ser 6 na opção
Normal: não confundimos a espessura visual do SVG com a região de entrada do KWin.

No lado do texto, `TitleBorderLeft=TitleBorderRight=12`. A divisória fica no meio
da lacuna, deixando 8 até a caixa do título. Isso não garante oito pixels até o
primeiro traço de cada glifo: a fonte tem suas próprias margens e inclinação.

## Vertical

Normal: topo do conteúdo em 7, fim exclusivo em 33, face em `[9,31)`. Maximizada:
topo em 4, fim exclusivo em 30, face em `[6,28)`. Em ambos os casos há 2 acima e 2
abaixo da face; a divisória ocupa a faixa completa de 26.

O tema continua reservando 34 unidades acima do aplicativo em ambos os estados.
Normal: `7 + 26 + 1`; maximizada: `4 + 26 + 4`. Os centros continuam em 20 e 17,
respectivamente — o mesmo perfil centralizado anterior. Não se reintroduz um salto
relativo ao compartimento ao maximizar.

A sobreposição calcula a altura útil com a fórmula do Aurorae e centra a linha
real de botões. A lacuna é arredondada para um número par de unidades, nunca menor
que 4. Em tamanhos não inteiros, um arredondamento de até uma unidade pode ser
inevitável; os testes não certificam uma grade física idêntica em escala fracionária.

## Cantos e visibilidade

A coordenada normal de referência é `9 + 22 + 6/2 - 1 = 33`. Os cortes superiores
usam essa coordenada e seu espelho `largura - 33 - 2`, alinhando-os às divisórias
das células terminais do perfil padrão. Os cortes laterais/inferiores seguem os
mesmos espelhos e respeitam individualmente as bordas efetivas.

Apenas o grupo esquerdo desenha os cortes da moldura, evitando duplicação. Eles
ficam ocultos na maximização e em janelas pequenas demais. Uma borda ausente ou
estreita elimina apenas seu próprio corte.

A lista de divisórias acompanha os objetos reais criados e seus tipos. Não usa a
posição de um item em `Row.children` como se fosse a posição em `ButtonsOnRight`.
Itens antigos são ocultados antes do `destroy()` adiado do QML. Controles ocultos e
espaçadores não desenham divisórias. Controles desabilitados, mas visíveis,
conservam seu compartimento e a divisória — sem modificar o estado gráfico do SVG.
