# Irix Classic DomainOS 0.2.8

Atualização independente do painel, gr_osview, Plasma Style `IrixClassicDomainOS`
e esquema **DomainOS SR10.4**. O style mantém sua versão 0.1.1. A integração
opcional com Thunderbird acompanha as fontes do pacote e tem instalação separada.

Requer Plasma **6.1 ou superior**, Qt **6.8 ou superior**, KSystemStats e PyQt6
QtCore/QtDBus do Python da distribuição. O ambiente de validação é Plasma 6.3
com Qt 6.8. A propriedade usada para as janelas suspensas foi introduzida no
[Qt 6.8](https://doc.qt.io/qt-6.8/qml-qtquick-controls-popup.html#popupType-prop).
O instalador verifica os módulos nativos e o Qt; não instala pacotes de sistema.


## Troca de cores no KDE

O nome mostrado continua **DomainOS SR10.4**. O arquivo instalado passa a ser
`DomainOS-SR10-4.colors`: no Plasma 6.3, o primeiro ponto do nome anterior
interrompia o identificador usado por Aplicar, apesar da prévia correta.
A fonte do repositório conserva o nome original; suas cores e fontes não mudam.

O painel recebe os papéis nativos do KDE em vez do `SystemPalette` que o
Kvantum pode fixar durante a inicialização. Trocas efetivas de esquema atualizam
a mesma arte. O modo de referência aprovado continua disponível para comparação.
Os menus e quadros QML recebem os mesmos papéis ativos; o texto desativado
usa o papel nativo exposto pelo Plasma. Isso não equivale a reproduzir todos
os efeitos Inactive/Disabled da paleta QWidget.
Botões, campos, caixas da seleção de grupo e rodapés dos diálogos próprios usam
os componentes SVG do Plasma. Assim, suas faces acompanham o esquema em vez
dos pincéis fixos do Kvantum. A largura mínima dos botões de texto e o espaço
dos campos foram preservados; os botões compactos da gaveta mantêm 28 × 28.
Os comandos e as ações padrão dos diálogos continuam pertencendo ao Qt.

## Instalação por usuário

Extraia `irixclassic-domainos-0.2.8.zip` e execute dentro da pasta extraída,
como seu próprio usuário, sem `sudo`:

```sh
sha256sum -c SHA256SUMS
python3 tools/install_domainos.py --verificar
python3 tools/install_domainos.py
```

O instalador do painel conserva os quatro destinos em `XDG_DATA_HOME`,
normalmente `~/.local/share`. Não escolhe o esquema de cores, não substitui
painéis nem muda suas preferências. Recibos e recursos anteriores ficam em
`XDG_STATE_HOME/irixium-domainos`. Para restaurar:

```sh
python3 tools/install_domainos.py --restaurar
```

Ao atualizar uma instalação anterior, o arquivo legado `DomainOS-SR10.4.colors`
só é retirado quando corresponde à versão canônica conhecida. Edições são
preservadas e informadas. O backup dessa migração fica em
`XDG_STATE_HOME/irixium-domainos-color-migration`; a restauração confere os dois
recibos antes de escrever e recupera o nome antigo antes de retirar o novo.
Os journals são separados, sem promessa de atomicidade entre eles. Se houver
interrupção registrada, confira e conclua a recuperação com
`--restaurar --recuperar --verificar` e depois `--restaurar --recuperar`.
Alterações posteriores continuam protegidas pelas guardas dos backups.

Para atualizar um painel DomainOS já aberto, recarregue o Plasma da própria
sessão após a instalação. Nas sessões com a unidade KDE:

```sh
systemctl --user restart plasma-plasmashell.service
```

Os aplicativos permanecem abertos. Para a primeira substituição de um painel,
confira o painel escolhido e selecione o style:

```sh
python3 tools/activate_domainos.py --verificar
plasma-apply-desktoptheme IrixClassicDomainOS
python3 tools/activate_domainos.py
```

Se houver vários painéis, use `--painel ID`. A alternância autorizada entre os
styles Classic e DomainOS pode ser habilitada com
`python3 tools/domainos_style_bridge.py --instalar --iniciar`.
O style `IrixClassic` precisa estar instalado para essa alternância; suas
fontes correspondentes acompanham o pacote, mas ele não é um quinto destino
do instalador independente.

## Janelas, seleção e menus

Na lista de um grupo, as caixas formam a seleção de operações. **Continuar
seleção** conserva as escolhas ao passar para outro grupo ou uma janela avulsa.
Sem caixas marcadas, clicar no título restaura/ativa a janela. Com seleção
explícita, o título acrescenta ou retira a janela dessa seleção.

**Operações** fica acessível com uma janela escolhida para oferecer **Fixar
temporariamente na Iconbox**. A fixação usa a identidade da janela e seu PID,
retira somente ela do grupo e a apresenta à esquerda. As próximas fixações
seguem a ordem escolhida. Não cria um lançador permanente nem salva o pin no
perfil. Fechar a janela remove seu pin. Filtros continuam valendo: sair do
escopo esconde a janela, sem confundir isso com seu fechamento.
Recarregar o Plasma também encerra esses pins temporários.

No menu direito de uma janela fixada, **Desafixar esta janela da Iconbox** é
a primeira opção. Organizações em lote continuam exigindo duas ou mais janelas.
Os comandos atuam no conjunto capturado e verificam identidade e permissões.
Um comando nativo de criar desktop que incluiria membros retirados por pin é
recusado; escolher um desktop existente move os membros capturados.

O menu nativo recebe uma âncora nas coordenadas da janela, sem reescalar seu
tamanho junto com a arte do painel. Dicas e miniaturas conservam a espera do
sistema. A legenda cortada de uma miniatura recebe sua própria dica completa;
essa dica não depende de manter também o modo de dicas de texto da Iconbox.

Os quadros e menus QML do painel acompanham o esquema KDE. O menu direito nativo
usa o estilo de aplicação: Kvantum IrixClassic conserva suas próprias cores e
arte de QWidget. Essa limitação está registrada na validação; selecionar outro
esquema KDE não recolore universalmente esse estilo de aplicação.

## Calendário, correio e luz

Em **Relógio e calendário**, selecione a fonte **Feriados**. A página nativa
da fonte permite escolher suas regiões. Fontes vazias têm uma explicação
visível; não são substituídas por eventos de exemplo. Calendários PIM, quando
instalados, continuam sendo outra fonte opcional com sua própria configuração.

Para **Manaus — Amazonas — Brasil, 2026**, o pacote oferece uma região adicional
nativa do KHolidays. A definição brasileira instalada no ambiente de teste
é antiga e não distingue corretamente alguns feriados atuais. O configurador
opcional seleciona a região de Manaus 2026, substitui somente `br_pt-br` se
estiver escolhida e conserva outras regiões:

```sh
python3 tools/configure_domainos_holidays.py --manaus-2026 --verificar
python3 tools/configure_domainos_holidays.py --manaus-2026
```

Depois escolha **Feriados** nas preferências do calendário. A região tem ano
explícito e cobre somente 2026; não promete datas para outros anos nem inclui
pontos facultativos como feriados. As fontes oficiais e o alcance estão junto
da [definição regional](../plasma/applets/org.irixclassic.domainos.panel/contents/code/holidays/README.md).
O configurador usa só dados/configuração do usuário e mantém backup. Para
restaurar a região e a seleção anteriores:

```sh
python3 tools/configure_domainos_holidays.py --restaurar
```

Uma edição posterior bloqueia a restauração para não perder escolhas novas.

Em **Correio e comandos**, escolha um cliente instalado ou siga o preferido
do KDE. Essa escolha vale para o botão do painel; não altera o cliente padrão
do desktop. O botão abre o cliente sem iniciar uma mensagem.

A contagem de não lidas usa a integração opcional do Thunderbird:

```sh
python3 integrations/thunderbird-domainos/install.py --install-user
```

O comando registra o integrador somente no usuário atual e informa o caminho
do XPI. Instale esse arquivo pelo gerenciador de extensões do Thunderbird e
habilite **Mostrar a contagem real** nas preferências do painel. Veja as
[instruções da integração](../integrations/thunderbird-domainos/README.md).
Nenhum perfil ou conta é modificado por esse instalador.

O total soma pastas físicas, sem contar novamente pastas virtuais, unificadas
ou de tags. O integrador compartilha somente disponibilidade e total numérico;
não exporta contas, nomes de pastas ou conteúdo. Fonte ausente aparece como
indisponível, e não como zero. Perda do integrador invalida a disponibilidade.

A lente de atividade é amarela ao acender, com proteção de contraste apenas
quando o esquema conflita com esse amarelo. Uma confirmação imediata pode
terminar antes da pintura; o recibo de apresentação mantém o sinal até um
quadro apresentado, sem prolongar a operação. A preferência de manter a luz
acesa depois da conclusão continua opcional e desligada inicialmente. A luz
de seleção do Pager não foi alterada.

O [registro de validação](VALIDACAO-DOMAINOS-0.2.8-2026-10-09.md) identifica as
provas e seus limites. Os manuais
[funcional](../plasma/applets/org.irixclassic.domainos.panel/FUNCTIONAL.md) e de
[preferências](../plasma/applets/org.irixclassic.domainos.panel/PREFERENCES.md)
descrevem as demais funções. O arraste de janelas entre miniaturas do Pager
continua adiado.
