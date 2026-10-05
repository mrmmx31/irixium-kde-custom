# Validação — IRIX Classic 1.0.0-rc2

## Executado nesta revisão

| Teste | Resultado | Alcance |
|---|---|---|
| Python/unittest | 32 testes aprovados | Instalação/restauração em diretórios temporários; backend KDE e UID simulados |
| Máquina de estados JavaScript | 34 testes aprovados | Inclui clique simples pendente, duplo clique sem popup, segundo press antes de double, cancelamentos, clique direito e pressão longa |
| Desenho/geometria JavaScript | 108 cenários aprovados | Inclui 36 sequências de repouso preservadas; não são 108 + 36 cenários |
| Referência IRIX 1 | 22.311 pixels, 0 divergências | Arte da moldura e símbolos; exclui texto e aplicativos |
| Referência IRIX 2 | 10.064 pixels, 0 divergências | Arte da barra superior; exclui texto |
| Sintaxe Python/shell | aprovada | ast.parse e sh -n |
| Pixels.js, Artwork.js, Geometry.js | idênticos à rc1 | Comparação de bytes e SHA-256 registrados em validation/rc2-artwork.json |

O teste regressivo principal executa Press-Release-Press-DoubleClick-Release
na máquina de estados e exige exatamente uma ação Close, sem qualquer ação Open.
Outro teste exige que o clique simples só publique o menu no timeout, uma única
vez, com o estado visual de pressão já desativado.

A política local de fechamento é habilitada ao migrar de rc1, sem escrever
CloseOnDoubleClickOnMenu no KDE. Um false local explícito de uma rc2 anterior é
preservado. Há testes de migração e restauração para essas condições.

Os resultados gráficos são obtidos por um gravador Context2D executando Artwork.js
em Node e rasterização em Pillow. São as mesmas referências utilizadas na
construção; não são testes cegos. Não demonstram rasterização, texto ou integração
em Qt Quick/KWin. As imagens completas de referência não são redistribuídas.

## Não executado — limite importante

Não há executor Qt 6/KWin disponível neste ambiente. A chamada
`bash testar.sh --qml` retornou código 77, indicando executor ausente.
**Os 20 testes QtTest incluídos NÃO foram contabilizados como aprovados.**
Não foram ensaiados o popup nativo, fechamento de aplicações reais, seleção
arrastada, diálogo de confirmação de saída ou cache de componentes do KWin.

A rc2 corrige uma disputa identificável no código entre o primeiro clique e o
popup, além da dependência da preferência global desabilitada. Isso não equivale
a alegar homologação em uma sessão Wayland. Testar primeiro em janela descartável
após atualizar e iniciar nova sessão, conforme ACEITACAO.md.

## Reproduzir

```sh
bash testar.sh
bash testar.sh --qml
bash testar.sh --janelas
```

Os executores Qt 6 são necessários apenas para os dois últimos comandos;
nenhum desses comandos instala dependências. `--qml` exercita Surface/ButtonInput,
não o backend C++ do KWin. `--janelas` abre clientes descartáveis para teste manual.

Registros: validation/automated.txt, validation/qt-runtime.txt,
validation/reference-pixels.json e validation/rc2-artwork.json.
