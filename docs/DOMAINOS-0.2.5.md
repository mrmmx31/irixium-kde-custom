# Irix Classic DomainOS 0.2.5

Pacote independente do painel DomainOS, gr_osview, Plasma Style
`IrixClassicDomainOS` e esquema de cores **DomainOS SR10.4**. As versões internas
do monitor e do style permanecem independentes da versão 0.2.5 do painel;
o Plasma Style desta entrega usa a versão 0.1.1.

Requer Plasma 6 com Qt **6.8 ou superior**, KSystemStats e PyQt6 QtCore/QtDBus
do Python da distribuição. Os módulos nativos de tarefas, bandeja, aplicativos,
calendário e preferências são fornecidos pelo KDE instalado. O instalador confere
essas dependências; não baixa nem instala pacotes de sistema.

Extraia `irixclassic-domainos-0.2.5.zip` e, dentro da pasta extraída, confira os
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
Separadores identificam as fontes. Os membros e as ações dos favoritos usam
o provedor nativo. Ao abrir a gaveta,
a ordem do menu KDE externo é lida sem alterar sua configuração. Na ausência
do menu anterior, a gaveta identifica uma ordem legada compatível; ordens
conflitantes de vários menus existentes são informadas e a lista é preservada.
Os comandos compactos dos pins deixam mais espaço aos nomes.

A roda da Iconbox navega pelos itens por padrão. Ativar janelas pela roda é
alternativa nas preferências. O clique simples abre o seletor de membros, inclusive
para uma janela só; o duplo clique individual minimiza a ativa, restaura a
minimizada ou ativa a inativa. Clicar no retângulo geométrico do Pager ativa a
janela representada. A primeira ativação transfere filtros/agrupamento/gestos
compatíveis e configurações individuais da bandeja; retornos posteriores preservam
as preferências próprias do DomainOS.

As miniaturas começam desligadas. A captura Wayland na fonte atual passou
24/24 critérios com duas janelas próprias, pixels atualizados pelo compositor
real de lsi e provedores descarregados ao fechar. A apresentação e o ciclo de
vida têm prova separada de 59/59 critérios em sessão X11 privada, incluindo
cartões clicáveis sem imagem, troca de proprietário e retorno ao modo textual.
O painel usa capacidades reais dos provedores KDE, e dispositivos ou funções indisponíveis na máquina
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

O painel apresenta o título completo dentro da janela já aberta do seletor,
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


## Funções mantidas da 0.2.4

A roda do Pager calcula o destino sem repetir passos por detente: preserva
movimentos parciais e o padrão de navegar sem ativar; a alternativa de ativação
faz no máximo um pedido por evento. Dez testes nativos incluem valores extremos
e recuperação de entrada inválida. A regra da Iconbox continua separada.

Uma prova Wayland atual de 62 critérios verifica seleção parcial acumulada
entre dois grupos reais, colunas/minimização dos dois UUIDs/PIDs escolhidos e
preservação das três janelas restantes.

A consulta da ordem externa dos favoritos acontece ao abrir a gaveta. Não há
polling no hover nem cópia para a lista de pins. Respostas de gavetas fechadas,
de outra atividade, tokens desconhecidos ou dados inválidos não substituem a
lista atual. Ler a ordem não altera o arquivo do menu KDE. Os itens sem posição
externa preservam explicitamente a ordem do provedor, sem depender da estabilidade
do sort do Qt instalado.

A importação opcional de pins libera os controles também quando a consulta
falha. Não repete uma importação automaticamente nem aplica uma resposta com
token inválido; uma nova tentativa continua disponível.

A avaliação dos resets usa as 44 entradas atuais, cinco categorias restantes,
Aplicar/Descartar e reinício de instância privada. Os comportamentos passaram;
o relatório geral conserva os seis diagnósticos do PromptDialog do SDK e saída
1. A outra instância e os arquivos reais permaneceram intactos.

A [auditoria dos gates](DOMAINOS-AUDITORIA-2026-10-09.md) distingue provas
atuais, limites e a avaliação final em p001532. O backup aprovado e os ZIPs
anteriores permanecem congelados.


## Correções da 0.2.5

Os SVGs funcionais do Plasma Style acompanham os papéis reais do esquema KDE,
inclusive os cabeçalhos e rodapés usados pelo volume e pelas notificações.
As superfícies usam Background/HeaderBackground, ButtonBackground e
ViewBackground; seleções e texto usam os papéis correspondentes. As faixas de
relevo clareiam ou escurecem a própria superfície. O gerador conserva cores de
referência apenas para classificar a arte histórica; não as instala como uma
paleta funcional fixa. As quatro paletas privadas e a troca sem recarregar o
motor QML são verificadas separadamente.

O seletor distingue seleção comum de intenção expressa nos checkboxes.
Sem nenhuma caixa marcada, clicar no título restaura/ativa a janela.
Após marcar uma caixa, os títulos acrescentam/retiram membros da seleção;
marcar a caixa não aciona a janela. O botão Operações requer duas ou mais
janelas escolhidas. Ele encerra o seletor antes de abrir o menu, preserva
UUID/PID e verifica novamente a identidade dos alvos.

O menu nativo do botão direito usa um pai persistente e fecha o menu anterior
antes de criar o sucessor. Sua primeira abertura foi medida com Wayland e
QStyle Kvantum; as opções já cabem na superfície inicial. O submenu Mais do
KDE continua sendo um submenu. Se o provedor falhar, a criação parcial é
descartada, o erro é informado e o menu próprio de recuperação aparece.

Os cartões das miniaturas, com título e ação, existem antes da imagem.
Só os provedores dos cartões dentro da região visível são carregados, de
forma assíncrona. Rolar, trocar o proprietário da dica ou fechá-la descarrega
as criações anteriores. Não há fila externa crescente, repaint periódico ou
transferência de objetos gráficos para uma thread de trabalho.

A [validação desta entrega](VALIDACAO-DOMAINOS-0.2.5-2026-10-09.md)
registra os ensaios atuais e uma falha fatal de protocolo observada na sessão
com a 0.2.4. Os testes da nova sequência não reproduziram a falha; isso não
atribui o objeto citado no log a um componente específico nem substitui a
avaliação manual das aplicações pessoais. O monitor continua somente observador;
esta entrega não instala um mecanismo que encerre aplicações ou reinicie o Plasma
automaticamente.
