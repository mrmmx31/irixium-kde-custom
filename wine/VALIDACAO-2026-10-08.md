# Validação do Wine Classic — 2026-10-08

Ambiente: Wine 10.0 do Debian (`10.0~repack-6`), prefixo win64 temporário,
Xvfb 1200×800. A galeria é um executável Win32 original, com manifesto de
controles v6; não é uma simulação Qt/HTML da interface Windows.

`wine/tools/test_native.py` confirmou:

- Aplicação pelo carregador nativo de `.msstyles`, paleta Classic e seleção
  persistente `Classic / NormalSize` em processos novos.
- Nove classes abertas com partes definidas e bitmaps: Button, Edit, ComboBox,
  ScrollBar, Tab, Progress, TrackBar, Header e ToolBar. A galeria mostra botões,
  check vermelho, rádios em losango azul, campo, combo, lista e barras reais.
  A existência das partes de Tab/TrackBar/Header/ToolBar foi consultada pela
  API; esses quatro controles não foram desenhados na captura.
- Pressão real via X11 alterou os pixels da galeria sem alterar sua dimensão.
  A ação Win32 não chegou durante a pressão e chegou após soltar o botão.
  Os intervalos de captura existem apenas no teste, fora do tema/utilitário.
- As fontes de aparência permaneceram byte a byte iguais. O Wine normaliza
  alturas LOGFONT ao aplicar um tema; o assistente repõe os valores originais,
  sem escolher outra fonte ou tamanho.
- Aplicação repetida identificou a instalação existente. A restauração
  retornou ao Light anterior, recompôs os valores de aparência e removeu
  somente o `.msstyles` criado pelo teste. Uma preferência `IconTitleWrap`
  alterada depois da instalação permaneceu como o usuário a havia escolhido.
- Uma falha de gravação do recibo depois da aplicação disparou a recuperação:
  valores anteriores e ausência original do arquivo foram conferidos.

Os testes Python cobrem parsing UTF-16/Unicode/binário, limites de registro,
restauração que preserva mudanças posteriores e recusa conflitos, prefixo
inexistente, links, estrutura PE sem código/imports e hashes de origem.
Inventário e instalação validam os 27 componentes e o manifesto do pacote.
Os utilitários produziram os mesmos hashes em duas compilações consecutivas.

O assistente requer um prefixo explícito e já inicializado, pertencente ao
usuário atual. Usa apenas `Control Panel\Colors`, `Control Panel\Desktop`
e `ThemeManager`; não importa nem substitui o hive inteiro de registro.
O instalador da suíte apenas disponibiliza os arquivos no XDG do usuário.

A aplicação em lsi (UID 1000) confirmou o estilo ativo em
`C:\windows\resources\themes\IrixClassic\IrixClassic.msstyles`, com
`Classic / NormalSize`. O recibo original e a leitura posterior confirmaram
as fontes preservadas; repetir a aplicação não alterou a seleção nem as
preferências Wine exportadas nessa repetição. O assistente instalado no XDG
também confirmou a seleção, sem depender do checkout. O prefixo de p001532
não faz parte dessa instalação.
A auditoria final de lsi passou para os 27 componentes, as duas cópias GTK2,
os três conjuntos de cursores e a seleção Classic sem divergências.

Limites: validação nativa em Wine 10/win64. O helper fornecido é x86-64.
Aplicativos que usam desenho próprio ou outra biblioteca visual podem
ignorar parte do estilo. Não há certificação de todas as combinações de
controles, menus, aplicativos, DPI ou prefixos de 32 bits. A seleção manual
via `winecfg` continua disponível. Capturas, prefixos e backups de perfil
ficam fora do repositório.
