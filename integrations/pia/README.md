# Bandeja SGI para o Private Internet Access

Integração opcional, somente para o usuário atual, validada no PIA Linux
3.7.2, com o Qt 6 que acompanha o aplicativo. São desenhos originais MIT para
alerta, desconectado, conectado, desconectando, conectando e pausa.

O [cliente oficial](https://github.com/pia-foss/desktop/blob/master/client/src/linux/nativetrayqt.cpp)
usa PNGs embutidos, sem consultar o tema KDE. A biblioteca local registra
nossos 24 caminhos de recurso antes dos recursos originais: seis estados para
cada uma das quatro opções de aparência da bandeja. O código do PIA continua
escolhendo o estado e tratando os cliques e menus. Não há temporizador,
consulta periódica, mudança de conexão ou alteração de arquivos em `/opt`.
A opção de aparência do PIA permanece salva; todos os quatro conjuntos usam
os desenhos SGI enquanto a integração estiver ativa.

## Instalação e restauração

Requer o PIA com Qt 6 em `/opt/piavpn`, Python/CairoSVG, um compilador C e o
`rcc` do Qt 6. No Debian, os componentes de geração são `python3-cairosvg`,
`build-essential` e `qt6-base-dev-tools`. A instalação do tema pronto não
precisa dessas ferramentas; esta integração específica compila a biblioteca
para a arquitetura de cada computador. O binário compilado não é versionado.

```sh
python3 tools/adapt_pia_tray.py --verificar
python3 tools/adapt_pia_tray.py
# Para remover e recuperar os arquivos anteriores:
python3 tools/adapt_pia_tray.py --restaurar
```

Sem `sudo`. O instalador salva backup privado, cria um atalho local
`piavpn.desktop` e instala três arquivos em
`~/.local/share/irixium/integrations/pia/`. Comandos personalizados no atalho,
links simbólicos e destinos compartilhados são recusados. A restauração
preserva alterações posteriores do usuário, recusando sobrescrevê-las.
Por limitação do carregador Linux, o caminho da biblioteca não pode conter
espaços ou dois-pontos.

Para carregar ou retirar a integração, encerre apenas a interface do PIA e
reabra pelo menu de aplicações. Isso não é uma instrução para desligar a VPN.
Não execute um reinício automático enquanto houver uma conexão ativa.
O atalho define `LD_PRELOAD` exclusivamente para esta inicialização; a própria
biblioteca remove sua entrada do ambiente antes de o PIA iniciar outros
programas, preservando entradas previamente configuradas pelo usuário.
Abrir diretamente `/opt/piavpn/bin/pia-client` usa os ícones originais.
A restauração de uma sessão antiga do KDE também pode usar esse caminho direto;
nesse caso, reabra a interface pelo atalho local. As preferências de restauração
da sessão e inicialização automática do PIA não são modificadas.

## Verificação dos recursos

```sh
python3 integrations/pia/build.py --output /tmp/irix-pia-overlay
python3 -m unittest discover -s tests -p test_pia_tray.py
```

`verify.cpp` é um diagnóstico opcional com os cabeçalhos Qt instalados.
O teste feito neste computador ligou-o ao Qt do próprio PIA, carregou sua
biblioteca de cliente e comparou byte a byte os 24 recursos com nossos PNGs.
O estado desconectado enviado efetivamente pela bandeja D-Bus foi comparado
com a arte original: 1.983 pixels opacos idênticos e alpha idêntico; nos demais
canais não transparentes, diferença máxima de um nível por arredondamento.
Os seis desenhos também foram verificados como arquivos diferentes. Não foi
necessário conectar a VPN para simular mudanças de estado.
