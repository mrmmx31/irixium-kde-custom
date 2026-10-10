# DomainOS SR10.4 — decoração de janelas

Opção Aurorae/QML independente do IRIX Classic. O pacote usa apenas a captura
**Domain_OS SR10.4 - 01 VUE desktop.png** fornecida pelo usuário e documentação
identificada como SR10.4. A barra azul externa pertence ao emulador MAME e não
faz parte da decoração.

Instalação no próprio perfil, sem selecionar a decoração ou alterar `kwinrc`:

```sh
python3 tools/install_domainos_decoration.py --verificar
python3 tools/install_domainos_decoration.py
```

Selecione **DomainOS SR10.4** em Configurações do Sistema → Cores e temas →
Decorações da janela. A instalação completa por `tools/install_suite.py` também
inclui essa opção, mantendo as decorações padrão dos perfis Classic e Moderno.
A restauração independente usa
`python3 tools/install_domainos_decoration.py --restaurar`.

O desenho tem moldura ciano na janela inativa, rosa na ativa, título branco
centralizado entre os controles e relevos de um e dois pixels. As laterais e a
base medem 11 pixels; o topo mede 30 pixels, incluindo a faixa de redimensionar.
Maximizada, a janela mantém apenas 20 pixels de título. O centro permanece
transparente para o KWin desenhar o aplicativo, enquanto toda a moldura é opaca.

O botão de menu fica à esquerda; minimizar e maximizar ficam à direita. O relevo
pressionado aparece durante o clique e a ação ocorre na soltura. Arrastar para
fora cancela a ação. O duplo clique no menu fecha também uma janela inicialmente
inativa; o clique simples aguarda o intervalo de duplo clique do sistema. Esse
único temporizador resolve o gesto do menu e não participa do desenho ou do
redimensionamento.

O manual de VUE distribuído para SR10.4 indica Swiss 742 bold como fonte média
e Helvetica bold como pequena. A captura não prova qual dessas fontes estava
selecionada. Usamos **Nimbus Sans bold, 12 px, sem antialias**, como aproximação
disponível neste sistema; o pacote não contém fontes. `Settings.qml` mantém
essas escolhas locais à decoração, sem alterar escala ou fontes do KDE.

Referências:

- [Captura exata SR10.4 do Virtual OS Museum](https://virtualosmuseum.org/images/more_screenshots/Domain_OS%20SR10.4%20-%2001%20VUE%20desktop.png).
- [Manual HP VUE: vuestyle(1X), árvore Domain/OS SR10.4](https://typewritten.org/Manual/Apollo/Domain%3AOS/SR10.4/man1X/vuestyle.bsd.html).
- [Installing DOMAIN Software, março de 1992](https://bitsavers.org/pdf/apollo/008860-A03_Installing_DOMAIN_Software_Mar92.pdf), para identificação da distribuição.

`ORIGEM.json` registra o hash da captura, cores e medidas. Não há arte de
SR10.4.1 ou de outras versões. A captura não é redistribuída no pacote.
Os estados pressionado e maximizado são adaptações funcionais: não aparecem
no print de referência.

Prévia real de KDecoration3, sem aplicar ao KWin da sessão:

```sh
python3 decorations/tools/preview_domainos.py --saida /tmp/domainos-preview
python3 decorations/tools/preview_domainos.py --saida /tmp/domainos-preview-interativo --interativo
```

A comparação com a captura é opcional: acrescente `--referencia CAMINHO_DA_IMAGEM`
à prévia ou ao teste de renderização. A ferramenta não procura imagens em pastas
de outros usuários e não baixa a captura.

Testes de eventos Qt e renderização:

```sh
python3 decorations/domainos/tests/test_input_render.py --saida /tmp/domainos-input
python3 decorations/domainos/tests/test_native_actions.py --saida /tmp/domainos-native
```

Os testes criam HOME/XDG e, no teste de ações, Xvfb/Xephyr/KWin próprios. Os
relatórios conferem os hashes do pacote testado, do IRIX Classic e das
configurações pessoais antes/depois. Os testes não selecionam essa decoração
na sessão real.
