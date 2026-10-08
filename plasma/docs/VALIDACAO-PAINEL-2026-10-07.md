# Painel Classic: validação local

O painel usa uma fileira de tarefas com ícone e legenda, molduras quadradas e
relevo de pressão ligado diretamente ao estado do mouse. Os cinco widgets têm
identificadores próprios; seus modelos e interações vêm do Plasma Desktop 6.3.6.
Os arquivos ORIGEM.json registram fontes, licenças e alterações.

## Resultados

- A suíte `bash testar-integracao.sh` passou, incluindo os testes do painel.
- Os 25 testes da migração verificaram configuração recursiva, ordem, atalhos,
  transferência da bandeja, reversão, falhas e recusa de alterações concorrentes.
- Aplicação e restauração reais passaram em um Plasma isolado por Xvfb e D-Bus.
  O teste preservou os 14 componentes internos da bandeja daquele perfil.
- A galeria Qt/KSvg passou por 56 verificações de pressão, cancelamento, soltura,
  tarefa ativa, switches, sliders nas duas orientações, listas, botões e
  resolução de ícones do menu.
- Os cinco widgets carregaram em hosts Plasma nativos isolados. O lançador
  mostrou o prefixo pressionado enquanto o mouse permaneceu abaixado, mudou
  935 pixels na região da tarefa e cancelou o efeito ao soltar fora.
- Três janelas Qt descartáveis foram verificadas em um KWin X11 isolado. Os
  estados ativo, inativo e minimizado vieram do TasksModel nativo, com PID e
  identificador X11 conferidos. A pressão teve efeito imediato e permaneceu
  durante a captura de 120 ms, sem executar a ação. Soltar fora cancelou;
  soltar dentro minimizou a janela ativa, ativou a inativa e restaurou a
  minimizada. Os estados também foram conferidos diretamente no X11.
  As regiões pressionadas mudaram 3067, 3697 e 3743 pixels, respectivamente.
- Na sessão Wayland de lsi, a migração preservou o painel 1822, altura de 64 px,
  largura configurada de 1440 px, posição, demais widgets e os 17 componentes
  internos da bandeja. Foram capturadas imagens da barra antes e depois.
- A execução pelo próprio usuário p001532 passou na sessão Wayland: os 22
  componentes instalados conferem com o pacote e o perfil Classic não tem
  divergências de seleção. A migração preservou o painel 342, os limites
  configurados de 1440 × 64 px, posição, ordem e os 16 componentes internos
  da bandeja. Foram substituídos somente os cinco widgets previstos, com
  recibos de restauração no perfil desse usuário. O recorte da captura dessa
  sessão também confirmou a fileira de ícones com legendas, o menu com três
  atalhos à esquerda e as molduras da bandeja e do relógio. O pager preservado
  não aparece nessa captura; seu relevo foi conferido na sessão lsi e na galeria.

Os testes isolados não acionam serviços reais de Wi-Fi/Bluetooth nem abrem
aplicativos do usuário. A galeria usa controles reais e tarefas demonstrativas;
o teste dos widgets usa o delegado e o modelo nativos. O teste opcional de
janelas abre somente três janelas Qt descartáveis, em Xvfb e D-Bus
privados, sem ativação de serviços nem um desktop Plasma completo. As capturas
da sessão lsi verificam a composição final do painel.

A instalação e a migração em p001532 foram verificadas por seus próprios
relatórios `RESULTADO.json` e `AUDITORIA.json`. A inspeção visual do relevo de
pressão e dos interruptores de Wi-Fi/Bluetooth nesse usuário continua pendente.
A captura foi produzida pelo Spectacle na própria sessão Wayland e foi
conferido somente o recorte do painel. A imagem estática confirma a composição;
não comprova o comportamento enquanto o mouse permanece pressionado. A opção
`--capturar` do pacote portátil acrescenta a imagem ao relatório existente.

## Reprodução

```sh
bash testar-integracao.sh
python3 plasma/tools/prever-painel.py --testar --offscreen --capturas /tmp/classic-galeria
python3 plasma/tools/testar-widgets.py --saida /tmp/classic-widgets
python3 plasma/tools/testar-widgets.py --widget iconbox --window-tasks --saida /tmp/classic-janelas
```

A última ferramenta exige Xvfb, D-Bus, compilador C++, Pillow e os arquivos de
desenvolvimento de Qt 6 Widgets/Test. Usa somente perfis temporários. As saídas
devem ser novas para conservar evidências de execuções anteriores.
O modo `--window-tasks` exige também `kwin_x11`, `xdotool` e `xprop`.

Para atualizar um painel existente, primeiro instale a suíte e execute
`python3 tools/classic_panel.py --verificar`, seguido do comando sem a opção.
`--restaurar` recupera os widgets anteriores pelo recibo do próprio usuário.
O procedimento exige um único painel Classic e recusa configurações alteradas
depois da migração; o arquivo original permanece guardado no backup.

## Referência visual

O vocabulário se inspira no Indigo Magic da SGI e no Motif: placas encaixadas,
contornos e relevos de workstation UNIX. O Iconbox e o pager adaptam a ideia
das ferramentas separadas da referência, mantendo o espaço compacto do KDE.

- [SGI: Indigo Magic User Interface Guidelines](https://techpubs.jurassic.nl/library/manuals/2000/007-2167-002/sgi_html/ch03.html)
- [OSF/Motif Style Guide, 1993](https://www.bitsavers.org/pdf/openSoftwareFoundation/motif/OSF_Motif_Style_Guide_Revision_1.2_1993.pdf)
