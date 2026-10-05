# Fontes técnicas

Repositório do projeto, base examinada:

https://github.com/mrmmx31/irixium-kde-custom/tree/790fcbcb44c3ba05dbcc4114b473b9b875e30820

Arquivos examinados: `aurorae/Irixium/Irixiumrc`, `update-irixium.sh` e árvore de
arquivos. O estado público dessa base não contém as decorações Classic entregues
separadamente; este pacote não presume que estejam publicadas no remoto.

KDE Plasma 6.3:

https://github.com/KDE/kwin/blob/Plasma/6.3/src/plugins/kdecorations/aurorae/src/qml/AuroraeButtonGroup.qml

Criação dos controles, Row, espaçamento e margens dos grupos.

https://github.com/KDE/kwin/blob/Plasma/6.3/src/plugins/kdecorations/aurorae/src/qml/aurorae.qml

Posição dos grupos, `childrenRect.width`, espaço do título e camadas da moldura.

https://github.com/KDE/kwin/blob/Plasma/6.3/src/plugins/kdecorations/aurorae/src/lib/auroraetheme.cpp

Cálculo da altura total, fator de tamanho e limites de borda do KWin.

https://github.com/KDE/kwin/blob/Plasma/6.3/src/plugins/kdecorations/aurorae/src/lib/themeconfig.cpp

Leitura dos parâmetros da seção Layout e seu tratamento de DPI.

As sobreposições v1/v2 incluídas em `compatibilidade/` servem apenas para
reconhecimento da atualização. Não são instaladas juntamente com a nova versão.
