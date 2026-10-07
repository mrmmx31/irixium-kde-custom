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
  tarefa ativa, switches, sliders nas duas orientações, listas, botões e resolução de ícones do menu.
- Os cinco widgets carregaram em hosts Plasma nativos isolados. A tarefa real
  mostrou o prefixo pressionado enquanto o mouse permaneceu abaixado, mudou
  935 pixels na região da tarefa e cancelou o efeito ao soltar fora.
- Na sessão Wayland de lsi, a migração preservou o painel 1822, altura de 64 px,
  largura configurada de 1440 px, posição, demais widgets e os 17 componentes
  internos da bandeja. Foram capturadas imagens da barra antes e depois.

Os testes isolados não acionam serviços reais de Wi-Fi/Bluetooth nem abrem
aplicativos. A galeria usa controles reais e tarefas demonstrativas; o teste
dos widgets usa o delegado e o modelo nativos. As capturas da sessão lsi
verificam a composição final do painel.

A execução no perfil protegido p001532 requer seu próprio terminal KDE e não
é certificada pelos testes de lsi. O pacote portátil instala os componentes
somente nesse perfil, produz seu relatório e conserva recibos de restauração.
A inspeção manual do relevo de pressão nesse usuário continua necessária.

## Reprodução

```sh
bash testar-integracao.sh
python3 plasma/tools/prever-painel.py --testar --offscreen --capturas /tmp/classic-galeria
python3 plasma/tools/testar-widgets.py --saida /tmp/classic-widgets
```

A última ferramenta exige Xvfb, D-Bus, compilador C++, Pillow e os arquivos de
desenvolvimento de Qt 6 Widgets/Test. Usa somente perfis temporários. As saídas
devem ser novas para conservar evidências de execuções anteriores.

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
