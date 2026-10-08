# Irix Classic DomainOS — Design

Este applet reúne o desenho do novo painel em uma única chapa. Ele segue as
proporções do projeto fornecido pelo usuário: relógio azul, data, gráfico e Mail
à esquerda; Iconbox com ícones IRIX; dois quadros de áreas de trabalho; bandeja
em duas linhas de três ícones; setas e faixa inferior com cinco atalhos. O Style
`IrixClassicDomainOS` e o esquema opcional **DomainOS SR10.4** são componentes
separados. O Classic existente continua disponível.

Esta versão é **um desenho executável para revisão**. Hora/data, gráfico,
janelas, miniaturas das áreas e dispositivos são amostras fixas da referência.
Os botões mostram o relevo pressionado enquanto o mouse permanece sobre eles e
voltam ao estado normal ao soltar ou sair. Nenhum deles lança aplicativos,
troca áreas, bloqueia a sessão ou modifica dispositivos. A lista de decisões
pendentes está em [DOMAINOS-REQUISITOS.md](../../../docs/DOMAINOS-REQUISITOS.md).
Cada função será implementada depois de sua confirmação pelo usuário.

O desenho tem base de 1942 × 218 pixels, com escala uniforme e sem deformação
dos módulos. Na escala de 50%, ocupa 971 × 109 pixels e os símbolos da bandeja
têm 16 pixels. O widget pede essas dimensões ao Plasma, mas não cria um painel,
não altera a altura do painel atual e não força áreas de trabalho. Selecionar
um Plasma Style também não substitui o layout dos widgets.

O instalador da suite disponibiliza os arquivos somente para o usuário que o
executa, sem selecionar o novo Style ou o esquema de cores. O widget aparece
como **Irix Classic DomainOS — Design** em Adicionar widgets. Sua inserção e a
troca definitiva do painel ainda dependem das decisões da próxima fase.

Para gerar prints e testar o relevo fora da sessão real:

```sh
python3 plasma/tools/prever-domainos.py --saida /tmp/domainos-design
```

Esse teste usa PyQt6 e um perfil XDG temporário. `--interativo` mantém a janela
de revisão aberta na própria sessão; os botões continuam sem ações. O teste
nativo adicional carrega o KPackage de produção em `plasmawindowed`, usando
Xvfb e um barramento D-Bus privado:

```sh
python3 plasma/tools/testar-domainos-package.py --saida /tmp/domainos-package
```

São ferramentas de desenvolvimento opcionais, não dependências do widget.
O applet utiliza Qt Quick e Plasma 6. A data usa DejaVu Sans Mono; rótulos usam
Nimbus Sans. As fontes são resolvidas pelo Qt, sem instalar fontes ou alterar
as preferências do usuário. O relatório nativo registra a família efetivamente
resolvida para detectar substituições.

[ARTWORK.md](ARTWORK.md) descreve os desenhos, as referências e a paleta.
`contents/images/ORIGEM.json` registra os hashes dos novos SVGs;
`ICONBOX-ORIGEM.json` identifica as cópias dos ícones IRIX já existentes no
repositório. As capturas de referência não fazem parte do pacote. O painel não
contém timers, animações, filtros, sombras desfocadas ou transições de relevo.
