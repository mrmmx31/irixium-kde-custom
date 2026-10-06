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

O botão de ações é parte do pacote. Duplo clique esquerdo fecha a janela; clique
esquerdo simples aguarda o intervalo de duplo clique do Qt. Clique direito abre
o menu imediatamente. O timer é exclusivo desse gesto e não participa do resize.

## Instalação e seleção

```sh
bash instalar.sh --verificar
bash instalar.sh
bash instalar.sh --ativar
```

Para alternar sem reinstalar:

```sh
bash ../aurorae/selecionar-user.sh moderno
bash ../aurorae/selecionar-user.sh classic
```

O instalador é transacional, cria backup privado e recusa execução como root.
`restaurar.sh` restaura a última versão instalada sem tocar em componentes do
sistema.
