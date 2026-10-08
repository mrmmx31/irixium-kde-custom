# IRIX Classic gr_osview

Widget de desktop do Plasma 6 com sete instrumentos de CPU, memória, swap,
leitura/escrita de disco e recepção/envio de rede. O tamanho inicial é 280×220;
movimentação e redimensionamento usam as alças normais de edição do Plasma.

Os valores vêm de `org.kde.ksysguard.sensors.Sensor` e do daemon `ksystemstats`.
CPU, memória e swap usam percentuais de 0 a 100. As taxas de disco/rede usam o
pico observado por barra desde a criação do widget, informado no rodapé; os
valores mantêm as unidades nativas formatadas pelo KDE. Dados indisponíveis
aparecem como `—`, sem serem apresentados como zero real.

Dependências: Plasma 6, módulo QML `org.kde.ksysguard.sensors` e `ksystemstats`.
O intervalo nativo é de 1 segundo. Não há Timer de animação ou repaint contínuo.
O applet não instala serviços, modifica seleção de tema ou grava preferências
de outros usuários. O instalador do repositório integra este pacote por usuário.

Implementação e arte de instrumento originais do projeto, sob GPL-3.0-or-later.
O nome faz referência histórica ao monitor IRIX; nenhum executável ou recurso
gráfico da SGI foi incorporado. A API e as fontes locais usadas na implementação
estão registradas em `ORIGEM.json`.

Para validar o applet com leituras reais e salvar somente a janela do widget:

```sh
python3 tools/testar.py --saida /tmp/irix-grosview-nativo
```

A fixture exige uma pasta nova em `/tmp`, Xvfb, D-Bus, `plasmawindowed`, compilador
C++ e cabeçalhos Qt6Widgets. Ela inicia um daemon de estatísticas separado,
com D-Bus e HOME/XDG temporários, confere três amostras nativas e encerra os
processos. Não acessa nem captura a sessão gráfica pessoal.

Por padrão o barramento do sistema também fica bloqueado. Nesse modo, os sensores
agregados de disco podem retornar zero sem dispositivos enumerados. Para conferir
a descoberta real de discos, acrescente `--system-bus-readonly`: o daemon privado
consulta somente os metadados nativos de UDisks/UPower, sem solicitar ações sobre
dispositivos ou configurações globais.
