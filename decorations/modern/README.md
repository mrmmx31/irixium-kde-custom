# Irixium Moderno independente

Esta é a decoração KWin moderna do Irixium em um pacote próprio, instalado
somente no perfil do usuário:

```text
~/.local/share/kwin/decorations/irixium_modern/
```

Ela usa o adaptador `org.kde.kwin.aurorae`, mas não depende de `MenuButton.qml`,
`AuroraeButtonGroup.qml`, `applications.png` ou qualquer outro arquivo
personalizado em `/usr/share` ou `/usr/lib`. Os SVGs e o PNG do tema Aurorae
original são mantidos dentro deste pacote.

O botão de ações é parte do pacote. Duplo clique esquerdo fecha a janela na
segunda soltura; clique
esquerdo simples aguarda o intervalo de duplo clique do Qt. Clique direito abre
o menu na soltura, sem espera adicional. O timer é exclusivo desse gesto e não participa do resize.
O duplo clique também funciona em janelas inativas e durante mudanças de foco,
sem exigir um clique adicional para ativar a janela.

A barra contém menu de ações, minimizar e maximizar/restaurar. Não há botão
fechar separado; o fechamento continua disponível pelo duplo clique no menu
e pelas ações nativas do KWin.

Os botões mostram o estado pressionado enquanto o mouse está segurado e
executam a ação ao soltar. O menu bitmap usa bordas de relevo baixo; os demais
botões usam seus SVGs pressionados. Não há timer para esse feedback.

## Instalação e seleção

```sh
bash instalar.sh --verificar
bash instalar.sh
bash instalar.sh --ativar
```

Se uma atualização mantiver o código antigo em memória, execute na própria
sessão KDE `python3 ../../tools/reload_decoration.py`. A ferramenta recarrega o
QML sem alterar a seleção ou as configurações e sem reiniciar o KWin.

Para alternar sem reinstalar:

```sh
bash ../../aplicar-tema.sh moderno
bash ../../aplicar-tema.sh classic
```

O instalador é transacional, cria backup privado e recusa execução como root.
`restaurar.sh` restaura a última versão instalada sem tocar em componentes do
sistema.
