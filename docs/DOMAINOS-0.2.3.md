# Irix Classic DomainOS 0.2.3

Pacote independente do painel DomainOS, gr_osview, Plasma Style
`IrixClassicDomainOS` e esquema de cores **DomainOS SR10.4**. As versões internas
do monitor e do style permanecem independentes da versão 0.2.3 do painel.

Requer Plasma 6 com Qt **6.8 ou superior**, KSystemStats e PyQt6 QtCore/QtDBus
do Python da distribuição. Os módulos nativos de tarefas, bandeja, aplicativos,
calendário e preferências são fornecidos pelo KDE instalado. O instalador confere
essas dependências; não baixa nem instala pacotes de sistema.

Extraia `irixclassic-domainos-0.2.3.zip` e, dentro da pasta extraída, confira os
arquivos e instale como seu próprio usuário, sem `sudo`:

```sh
sha256sum -c SHA256SUMS
python3 tools/install_domainos.py --verificar
python3 tools/install_domainos.py
```

São instalados exatamente quatro destinos em `XDG_DATA_HOME`, normalmente
`~/.local/share`. O recibo e os arquivos anteriores ficam em
`XDG_STATE_HOME/irixium-domainos`. A instalação conserva o painel ativo e suas
preferências. Para restaurar os recursos anteriores:

```sh
python3 tools/install_domainos.py --restaurar
```

Ao atualizar um painel DomainOS que já está aberto, recarregue o Plasma da
própria sessão depois da instalação, para descartar componentes QML que o
processo anterior ainda mantém carregados. Nas sessões com a unidade KDE:

```sh
systemctl --user restart plasma-plasmashell.service
```

Essa recarga conserva as preferências e os aplicativos abertos. O painel
desaparece brevemente; não é necessário encerrar a sessão.

A substituição da barra é uma etapa separada, dentro da sua própria sessão KDE.
Confira primeiro o painel escolhido e selecione o Plasma Style DomainOS:

```sh
python3 tools/activate_domainos.py --verificar
plasma-apply-desktoptheme IrixClassicDomainOS
python3 tools/activate_domainos.py
python3 tools/domainos_style_bridge.py --instalar --iniciar
```

O ativador só remove a barra anterior depois que o novo painel e sua bandeja
estão prontos. A recuperação fica em arquivo, em
`XDG_STATE_HOME/irixium-domainos-panel`; nenhuma segunda barra fica oculta.
Se houver vários painéis, escolha o ID mostrado na verificação com `--painel ID`.

A ponte é opcional e pertence ao usuário que a instalou. Depois dessa autorização,
selecionar `IrixClassic` no seletor de **Plasma Style** reconstrói a barra anterior;
selecionar `IrixClassicDomainOS` traz de volta a barra DomainOS com suas
preferências. Outros estilos não acionam essa troca. Ela observa a seleção,
sem escolher o estilo ou o esquema de cores por você.
Para essa alternância automática, o Plasma Style `IrixClassic` também precisa
estar instalado. Este arquivo independente instala apenas o style DomainOS.

O serviço usa cópias locais dos scripts; a pasta extraída pode ser removida.
Para desativar a ponte, preservando a barra atual:

```sh
python3 tools/domainos_style_bridge.py --desativar
```

Para recuperar a barra manualmente, selecione `IrixClassic` e execute
`python3 tools/activate_domainos.py --restaurar`. Os recibos da ponte, scripts e
unidade de serviço ficam no perfil do próprio usuário. Nenhuma configuração de
outro usuário ou instalação global é alterada.

Os controles de grupos, dicas/miniaturas, aplicativos fixados, ordem da bandeja
e restauração de padrões estão nas preferências da própria instância. Veja o
[manual funcional](../plasma/applets/org.irixclassic.domainos.panel/FUNCTIONAL.md)
e o [manual de preferências](../plasma/applets/org.irixclassic.domainos.panel/PREFERENCES.md).

Esta atualização mantém uma única barra ativa e oferece a recuperação da Classic
por Plasma Style. A flutuação usa a regra nativa do KDE: afasta-se da borda quando
a área está livre e encosta quando uma janela maximizada/sobreposta exige isso.
Os menus próprios seguem os papéis do esquema de cores do KDE.

O seletor de membros calcula o espaço do cabeçalho, lista e botões. Listas
extensas ficam limitadas à altura útil da tela. A corrida identificada ao
reabrir uma lista maior foi corrigida; um ensaio X11 privado verificou 165
critérios, incluindo os sinais de abertura, alterações de tamanho ao vivo e
a superfície nativa dentro da tela. O registro de validação conserva as
tentativas falhas anteriores e os limites. Títulos longos são abreviados na
linha e apresentados por uma única dica. O painel unificado já desenha sua
moldura; seu containment não acrescenta outra chapa por trás dela.

A gaveta mantém as preferências permanentes no topo, os pins da barra de
tarefas na segunda seção e os favoritos do menu Applications do KDE na terceira.
Separadores identificam as fontes. Os favoritos acompanham o mesmo modelo e
ordem do menu, e os comandos compactos dos pins deixam mais espaço aos nomes.

A roda da Iconbox navega pelos itens por padrão. Ativar janelas pela roda é
alternativa nas preferências. O clique simples abre o seletor de membros, inclusive
para uma janela só; o duplo clique individual minimiza a ativa, restaura a
minimizada ou ativa a inativa. Clicar no retângulo geométrico do Pager ativa a
janela representada. A primeira ativação transfere filtros/agrupamento/gestos
compatíveis e configurações individuais da bandeja; retornos posteriores preservam
as preferências próprias do DomainOS.

As miniaturas começam desligadas. Ensaios anteriores validaram a captura em
X11 e em Wayland com duas janelas de teste, incluindo atualização dos pixels
pelo compositor real de lsi. Esta rodada verifica a apresentação e o ciclo de
vida das dicas: 59/59 critérios em sessão X11 privada, cartões clicáveis com
imagem ausente, troca de proprietário e retorno ao modo textual. Essa prova
não é uma nova captura Wayland. O painel usa capacidades
reais dos provedores KDE, e dispositivos ou funções indisponíveis na máquina
continuam indisponíveis. Foram observados diagnósticos do PromptDialog do SDK
Kirigami durante ensaios de Aplicar/Descartar; também ocorreram com o pacote
anterior, sem a função de reset. Não há correção global do SDK neste pacote.

Licenças e atribuições acompanham cada componente e a fonte bitmap da data.
`plasma/IrixClassic` está incluído apenas como fonte correspondente para o gerador
do artwork DomainOS; não é um quinto destino instalado. O pacote contém código
e recursos editáveis, não inclui sons, configurações pessoais, auditor privado ou
o pacote completo de ícones. A decoração DomainOS paralela é distribuída à parte.
Os hashes verificam integridade; os artefatos não têm assinatura digital.

Para gerar novamente a distribuição sem instalar ou publicar:

```sh
python3 tools/package_domainos.py --verificar
python3 tools/package_domainos.py --saida /caminho/novo
```

## Dicas dentro do seletor de membros

A 0.2.3 apresenta o título completo dentro da janela já aberta do seletor,
sem acrescentar outro `PlasmaQuick::ToolTipDialog` a essa janela. As dicas nas
células da Iconbox continuam nativas e são ocultadas enquanto o seletor está
aberto. A preferência de dicas permanece ligada por padrão. O destaque das janelas
pelo compositor fica desligado por padrão e tem uma opção independente em
Preferências → Iconbox; quando habilitado, atua nos ícones e nos títulos
individuais do seletor. Sair do item, fechar a lista ou desligar a preferência
cancela o destaque, e uma saída atrasada do item anterior não cancela o novo. As miniaturas
continuam opcionais e usam os mesmos provedores de captura.

O conteúdo das miniaturas é compartilhado entre as duas apresentações; a dica
textual não carrega um provedor de captura. O texto é literal e acompanha o
título atual da janela, preservando identidade/PID.

Os ensaios privados e seus limites estão no registro
[de correção das dicas](VALIDACAO-DOMAINOS-DICAS-2026-10-09.md) e no
[registro desta rodada](VALIDACAO-DOMAINOS-AJUSTES-2026-10-09.md). A avaliação
manual da sessão Wayland do lsi ainda deve confirmar o caso que travou.
O arquivo 0.2.2 já distribuído permanece congelado e não contém esta correção.
