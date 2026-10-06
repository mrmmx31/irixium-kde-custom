# Reorganização e inventário — 06/10/2026

Branch: `#irixfiles`. Base anterior: commit `8b9d6a4`.

## O que foi retirado ou realocado

- `classic-rewrite-rc1/` → `decorations/classic/`.
- `modern-rewrite-rc1/` → `decorations/modern/`.
- Retirados `moderno/geometria/`, `MenuButton.qml`, `AuroraeButtonGroup.qml`,
  `tools/update_irixium.py`, `kde-fonts.conf`, `kwin-decoration.conf` e seus testes
  específicos do instalador legado. O fluxo ativo não os usava.
- Retirada a cópia `aurorae/Irixium/`: os seis assets usados pela decoração
  independente eram idênticos aos já mantidos em seu pacote. Metadados, RC e
  procedência upstream foram preservados em `decorations/modern/`; créditos e
  licença continuam presentes. SVGs de controles não implementados no fluxo
  atual deixaram de ser distribuídos como uma segunda decoração concorrente.
- Retirados diretórios vazios/caches Python de `classic-v4/` e `controles-v3/`.
  Esses dois nomes já não continham fontes versionadas.
- Retirados checksums, logs, relatórios e prévias estáticas dos ícones que ainda
  descreviam o kit 0.1.0. O pacote atual é 0.3.0; a arte, os manifestos de
  geração/expansão e as ferramentas para gerar novas prévias foram mantidos.
- READMEs, atalhos e caminhos dos testes passaram a apontar para a estrutura ativa.
  Documentação de instalação antiga que descrevia escrita no sistema foi refeita.

Os arquivos retirados continuam no histórico Git. Baselines usados pelos testes,
fontes de geração dos ícones/Kvantum, referências de desenho e os registros da
release Kvantum 0.7.1 foram mantidos. O auxiliar da correção opcional do KDE
Qt Quick ainda é usado por essa ferramenta e seus testes; não faz parte do
instalador dos temas e não foi executado no sistema nesta reorganização.

## Componentes realmente usados

`components.json` é o inventário único de fontes, destinos e perfis consumido
pelo instalador. Declara 15 componentes gráficos: duas decorações, dois temas de
ícones, cursor SGI, GTK Irixium, cores Irixium, dois Plasma Styles, dois wallpapers,
dois Kvantum e dois temas globais com splash.

`tools/audit_suite.py` verifica fontes, manifestos e vínculos de ícones, cores,
Plasma, cursores, wallpapers e splash. Com `--local`, compara os bytes instalados,
considera links internos materializados e normaliza o ID Classic transformado
pelo instalador. Também verifica a seleção efetiva, incluindo os defaults do KDE.

A comparação local confirmou que **todos os assets gráficos utilizados já estão
no repositório**. Não foi necessário importar imagens, fontes ou configurações
pessoais adicionais. As diferenças aparentes dos ícones/cursores eram links
simbólicos transformados em arquivos portáveis, não arquivos faltantes.
A Classic usa o ID de instalação `irixium_irix_classic_v4`, preservado.

O GTK 3/4 estava instalado, mas a seleção do tema dependia de preferências locais
já existentes. `aplicar-tema.sh` agora escreve somente tema, ícones e cursor em
`gtk-3.0/settings.ini` e `gtk-4.0/settings.ini`, preservando fonte e outras chaves.
Esses arquivos também entram no backup/rollback. Aplicação recusa dependências
necessárias ausentes antes de alterar configurações.

## Sons preservados

O esquema público contém todo o código, catálogo, identidade de origem e
mapeamento necessários para gerar e instalar os 24 eventos a partir dos oito
originais. Os bytes dos áudios não entram no repositório. Nenhum download foi
adicionado ao fluxo público e o downloader privado não é chamado por ele.

O esquema local instalado, seus WAVs/PCM/manifesto e os oito originais no cache
foram validados, sem reprodução. Estava selecionado `IrixClassic`, conforme o
usuário, que informou já estar funcional. Scripts de `sons/local/` foram
preservados byte a byte e continuam ignorados pelo Git.

Ao aplicar um perfil, o esquema SGI já instalado é validado e selecionado, sem
modificar habilitação, volume, mudo ou regras por aplicativo. `--sem-sons` preserva
a seleção; `--exigir-sons` recusa a aplicação se o esquema não estiver instalado.
Em outro computador, use `sons/instalar.sh --origem DIRETORIO` com os originais
locais autorizados. Os áudios são a única dependência temática deliberadamente
mantida fora da distribuição pública. A revisão dos termos históricos e a
distinção entre uso com atribuição e redistribuição estão registradas em
`sons/docs/CREDITOS-E-AUDIOS.md`; a política de distribuição foi preservada.

A fonte Nimbus Sans e Plasma/Aurorae/KSvg/Kvantum/FFmpeg são dependências de
execução fornecidas pela distribuição; não são arquivos pessoais ausentes do tema.

## Serviço opcional e validação

O serviço existente `irix-classic-user.service` apontava para o caminho antigo.
O instalador migrou somente o `ExecStart` deste checkout, com backup em
`XDG_STATE_HOME/irixium-hook-migration`, e recarregou as definições do systemd do
usuário. Não iniciou o serviço nem trocou o tema. Serviços de outro checkout
ou editados pelo usuário não são sobrescritos.

Passaram **629 testes Python**: 59 de instalação/integração, 324 Kvantum,
40 Classic, 34 moderno, 27 ícones, 46 sons e 99 distribuição. Também passaram
os testes Node da Classic e os eventos reais do Qt após a realocação dos pacotes.

Em perfil temporário vazio, com nome contendo espaços e acentos: instalação e
segunda execução passaram; aplicação de ambos os perfis selecionou GTK,
Kvantum e sons coerentes; fontes e habilitação de sons foram preservadas;
a restauração devolveu todos os arquivos exatamente ao estado anterior.
Os sons já existentes foram copiados somente para esse perfil temporário de teste.

A auditoria final do perfil real passou com seleção Classic coerente e sons
validados. Os componentes gráficos já estavam atualizados; o único ajuste local
foi o caminho do hook, com backup. Artefatos da auditoria/testes ficam em
`/tmp/irix-reorganizacao-20261006`, fora do repositório. Nenhum recurso de sistema
ou configuração de outro usuário foi alterado.
