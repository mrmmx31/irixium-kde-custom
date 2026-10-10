# Irix Classic DomainOS

O applet `org.irixclassic.domainos.panel`, versão 0.2.11, conecta o desenho aprovado
do painel a aplicativos, relógio/calendário, sensores, janelas, áreas de trabalho
e bandeja nativos do KDE. A Iconbox seleciona janelas com um clique e ativa com
duplo clique; o pager mostra mapas das áreas reais. A gaveta guarda uma lista
própria de aplicativos fixados. As páginas de preferências pertencem à
instância do applet e ao usuário que a utiliza.

No seletor de um grupo, clicar no título restaura a janela diretamente enquanto
nenhum checkbox estiver marcado. Marcar um checkbox inicia a seleção em lote;
nessa situação, clicar nos títulos marca ou desmarca membros. Ao esvaziar essa
seleção, os títulos voltam a restaurar. As miniaturas ao passar o mouse são uma
opção na página Iconbox, desligada por padrão. Clicar novamente no botão que
abriu um menu ou uma gaveta fecha esse conteúdo, sem atraso de clique.

A Iconbox mostra por padrão o título da janela ou a lista ordenada do grupo
ao passar o mouse. Na mesma página pode escolher miniaturas ou nenhuma dica.
As dicas dos demais botões e da bandeja são uma opção separada em Interação e
atividade, desligada por padrão.

O menu DomainOS continua sendo o padrão; sua busca procura aplicativos em todas
as categorias. Na página Aplicativos fixados pode selecionar a interface nativa
do Menu de aplicativos do KDE. A gaveta contém sempre “Preferências do painel…”
como primeiro item, independentemente da lista de pins.

Em **Bandeja e notificações**, os itens podem ser ordenados pelo nome com as
setas de subir e descer; Aplicar confirma e Descartar conserva a ordem anterior.
Cada categoria tem um botão de restaurar seus padrões, e **Padrões do painel**
prepara a restauração geral desta instância. Uma tarefa minimizada levanta o
relevo no Iconbox mesmo quando continua selecionada.

O [manual funcional](FUNCTIONAL.md) explica cada botão, os gestos, a configuração
e as limitações. A referência visual continua disponível em `DomainOSPanel.qml`
sem controlador funcional. Seu desenho e o backup congelado não são substituídos
pela integração.

Terminal, Aparência, xman e Ajuda KDE usam KIO com um Desktop Entry temporário
privado para solicitar a notificação de inicialização, preservando argumentos e
diretório de trabalho. O arquivo é removido e não entra no catálogo do usuário.
O retorno confirma a aceitação do pedido; a espera visual acompanha os registros
reais do TaskManager. Sem KIO, a criação direta do processo informa sua limitação.
Um timeout do launcher mantém o estado da aplicação desconhecido e não provoca
uma nova tentativa automática. A espera desse caminho foi verificada em X11;
o contexto de ativação Wayland ainda não foi comprovado.
O `TasksModel` pode absorver a inicialização de um aplicativo com janela já
aberta; sem esse registro, o painel confirma somente o pedido, sem inventar
uma espera por PID, título ou duração fixa.

No tema global DomainOS, as cores seguem a paleta CoralReef da VM SR10.4:
o alto do painel usa os tons do conjunto 5; a chapa usa a luz e a sombra do
conjunto 3; as molduras ativa e inativa usam os conjuntos 1 e 2. O cálculo
dinâmico parte da cor primária nativa, evitando a saturação excessiva que
ocorria ao usar o fundo antigo do protótipo como referência. Outros esquemas
KDE continuam recolorindo essas relações; o modo de comparação conserva o
desenho aprovado. A VM atribui ainda cores secundárias por aplicativo — por
exemplo, o conjunto 7 ao Style Manager e o 6 ao Help — que uma única paleta
global KDE não distingue automaticamente.

## Instalação por usuário

Na raiz do repositório, como o próprio usuário e sem `sudo`:

```sh
python3 tools/install_domainos.py --verificar
python3 tools/install_domainos.py
```

O instalador independente verifica as dependências nativas e instala exatamente
quatro destinos em `XDG_DATA_HOME`, normalmente `~/.local/share`: este applet,
o gr_osview, o Plasma Style `IrixClassicDomainOS` e o esquema opcional
**DomainOS SR10.4**. Os recibos e arquivos anteriores ficam em
`XDG_STATE_HOME/irixium-domainos`, normalmente `~/.local/state/irixium-domainos`.
Não há escrita em `XDG_CONFIG_HOME`, compatibilidade GTK/cursores, refresh de caches,
sinais de sessão ou hooks. A validação recusa execução como root, caminhos de sistema,
links de destino e raízes XDG pertencentes a outro usuário.

Instalar disponibiliza os componentes. Não insere um painel, não troca widgets,
não seleciona o Style ou o esquema de cores e não altera as preferências dos
outros usuários. Em **Adicionar widgets**, escolha **Irix Classic DomainOS**
somente quando quiser utilizá-lo. O Classic anterior continua disponível.

Para substituir a barra deste perfil, selecione o Style e execute a ativação:

```sh
plasma-apply-desktoptheme IrixClassicDomainOS
python3 tools/activate_domainos.py --verificar
python3 tools/activate_domainos.py
python3 tools/domainos_style_bridge.py --instalar --iniciar
```

O ativador guarda o layout em `XDG_STATE_HOME/irixium-domainos-panel` e remove a
barra anterior depois de conferir a nova; não deixa outro painel oculto. A ponte
é um serviço do próprio usuário: a escolha de IrixClassic recupera a barra anterior,
e IrixClassicDomainOS recupera a DomainOS. Seus fixados e preferências são guardados
entre essas trocas. Os demais Styles não acionam mudanças de layout.

Para recuperar a barra anterior pelo terminal:

```sh
python3 tools/activate_domainos.py --restaurar
```

A restauração usa o scripting KDE e as configurações guardadas dos widgets; não
sobrescreve o arquivo inteiro de configurações enquanto o Plasma está em execução.
Os IDs das instâncias reconstruídas são novos. A ponte pode ser desativada com
`python3 tools/domainos_style_bridge.py --desativar`. A distribuição e suas limitações
estão em [DomainOS 0.2.11](../../../docs/DOMAINOS-0.2.11.md).

Para conferir e restaurar os componentes alterados pela última instalação
independente DomainOS:

```sh
python3 tools/install_domainos.py --restaurar --verificar
python3 tools/install_domainos.py --restaurar
```

A restauração recupera os destinos anteriores e remove os que aquela instalação
criou. O recibo contém somente os destinos que mudaram naquela execução: se uma
atualização mudou apenas o applet, restaurá-la recupera somente o applet anterior,
sem desinstalar os outros três componentes. Ela recusa edições posteriores nos
destinos ou no backup, evitando apagá-las.
Não restaura layouts/preferências que você modificou ao usar o painel. Para esse
procedimento no checkout, veja também [Instalação recuperável](../../../docs/INSTALACAO-RECUPERAVEL.md).

No checkout completo, `bash instalar-irixium.sh` instala a suíte inteira
com seu estado separado `irixium-suite`. Seus recibos abrangem o catálogo completo,
inclusive estes quatro destinos. A restauração de cada instalador verifica o estado
atual: se outra instalação ou edição mudou um destino depois, ela recusa sobrescrever
a mudança. Esse comando não está incluído no ZIP independente DomainOS, que usa
`tools/install_domainos.py`. Atualizar arquivos não recarrega o QML de uma instância já em memória;
reabra o widget quando quiser carregar a atualização.

## Execução e desenho

São necessários Plasma 6 com Qt 6.8 ou superior, os módulos KDE nativos de tarefas, pager, aplicações,
bandeja, calendário e sensores, `ksystemstats` e as dependências verificadas pelo
instalador. Operações de organização/encerramento usam `/usr/bin/python3` com os
bindings QtCore/QtDBus do PyQt6 da distribuição e um script KWin transitório no
barramento da própria sessão. O pacote inclui um módulo C++ local ao applet para
menus e estilos nativos; não instala módulos globais. Thunderbird,
Konsole e xman só são necessários quando forem os programas escolhidos para seus
respectivos comandos.

A base do desenho é 1942 × 218; a escala de 50% ocupa 971 × 109. O applet escala
os módulos uniformemente e pede espaço ao Plasma, sem definir a altura do painel
que o contém. As fontes e os relevos conservam o desenho aprovado: Courier bitmap
na data, Nimbus Sans nos rótulos, chapa com quatro sulcos e resposta pressionada
imediata. A paleta acompanha as cores Qt/KDE em execução. O pager preserva a luz
amarela original nos esquemas aprovados e protege seu contraste em fundos amarelos.

[ARTWORK.md](ARTWORK.md) documenta a arte e a procedência. [INSTRUMENTS.md](INSTRUMENTS.md),
[APPLICATIONS.md](APPLICATIONS.md) e [PREFERENCES.md](PREFERENCES.md) detalham os
contratos dos componentes. As capturas externas de referência não integram o pacote.
O relevo não depende de timers ou transições: amostragem dos instrumentos, observação
de operações e permanência opcional da lente têm funções separadas do clique.

A indicação de espera do VUE usa `waitingBlinkRate` de 500 ms por meio ciclo.
A lente do painel acompanha esse ritmo enquanto há uma operação observável
pendente e interrompe o pulso na conclusão. Pedidos já aceitos em um único turno
têm somente a confirmação de apresentação. Nos lançadores, a observação atual
termina na confirmação do processo auxiliar; ela não mede o tempo até a janela
do aplicativo aparecer. O VUE original podia esperar o mapeamento dessa janela.
O tempo opcional após a conclusão permanece desabilitado por padrão e só
posterga o apagamento. O LED mantém seu amarelo, com proteção de contraste;
a seleção do pager conserva seu comportamento independente.

## Ensaios isolados

As ferramentas abaixo são de desenvolvimento. Criam saídas e perfis privados em
`/tmp`, sem substituir o painel em uso; dependências de teste não são dependências
extras do applet.

```sh
python3 plasma/tools/prever-domainos.py --saida /tmp/domainos-referencia
python3 plasma/tools/testar-domainos-package.py --saida /tmp/domainos-package
python3 plasma/tools/testar-domainos-tarefas.py --saida /tmp/domainos-tarefas
python3 plasma/tools/testar-domainos-iconbox.py --saida /tmp/domainos-iconbox
python3 plasma/tools/testar-domainos-iconbox-nativa.py --saida /tmp/domainos-iconbox-nativa
python3 plasma/tools/testar-domainos-integracao.py --saida /tmp/domainos-integracao
```

A prévia visual continua sem ações reais. Os ensaios funcionais usam janelas,
provedores e sessão privados; o ensaio integrado carrega o KPackage de produção.
As seleções de exemplo Work/Procrastination pertencem à referência, não são nomes
impostos às áreas de trabalho do usuário.
