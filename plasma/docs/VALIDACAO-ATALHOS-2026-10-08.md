# Configuração e recuperação dos atalhos Classic

O grupo de atalhos de lsi tinha apenas Chrome; Konsole e IRIX Files estavam em
dois widgets de ícone separados, antes desse grupo. O reparo pela API nativa
do Plasma reuniu Chrome, IRIX Files e Konsole nessa ordem no widget 1852 do
painel 1822. Removeu somente os dois ícones duplicados, 1881 e 1882.

Foi salvo um backup privado do arquivo do painel antes do reparo. A comparação
confirmou alterações somente em `launcherUrls`, na ordem do painel e nas duas
seções removidas. Os demais widgets, sua ordem e a altura de 64 pixels foram
preservados. O reparo foi aplicado exclusivamente à sessão lsi.

O widget 0.1.3 agora oferece **Organize Launchers…** no menu contextual e abre
a categoria **Launchers** primeiro. A página apresenta lista, Adicionar,
Substituir, Remover, Subir e Descer. Trabalha com cópias de `cfg_launcherUrls`
para o protocolo Aplicar/Cancelar do Plasma. Substituir usa o seletor nativo
de aplicativos, conserva a posição e não edita o `.desktop` do aplicativo.
Se a lista mudar durante essa seleção não modal, a escolha antiga é recusada.
Os tokens `applications:`/`file:` são preservados; handlers de pressão,
layout e arrastar não foram alterados.

## Verificações

- A página real e o backend Quicklaunch nativo passaram 28 verificações em
  `plasmawindowed`, incluindo quatro diálogos `KOpenWithDialog`: cancelamento,
  adição, substituição Dolphin→Files e seleção antiga após mudança da lista.
  Tokens mistos com espaço e `%`, limites de movimento, remoção e descarte
  da página também foram exercitados. Nenhum aplicativo instalado foi lançado.
- O host isolado verificou largura de 520 pixels e controles de 12 pt;
  não houve erro QML. A captura usa Fusion e aplicativos fictícios. A mensagem
  visível sobre alteração da lista pertence ao teste deliberado de proteção.
- Aplicar/Cancelar são modelados nesse host através da transferência da lista;
  ele não executa o diálogo completo de configuração do Plasma. O mapeamento
  `cfg_*` foi conferido no `AppletConfiguration.qml` instalado do KDE 6.3.6.
- Passaram os nove testes do inventário e os onze testes existentes de Plasma;
  os hashes atuais do pacote e os hashes originais de proveniência foram
  conferidos separadamente.
- O novo pacote foi instalado somente em lsi, com backup próprio. Após recarregar
  `plasma-plasmashell.service` desse usuário, os três atalhos e os IDs/ordem dos
  demais widgets foram confirmados novamente. A configuração nativa foi aberta
  nessa sessão, com versão 0.1.3 e sem diagnóstico QML do novo componente.
- A auditoria local final passou para os 26 componentes, sem divergências de
  instalação ou seleção.

Prova reproduzível:

```sh
python3 plasma/tools/testar-atalhos.py --saida /tmp/irix-atalhos-teste
```

Os relatórios públicos e a captura do host isolado estão em
`/home/lsi/Downloads/irix-launchers-20261008/`. Backups do perfil e scripts
temporários de recuperação ficam fora do repositório.
