# Validação local — IrixClassic Files 0.1.0-alpha1

Revisão de 2026-10-07, na branch `#irixfiles`. Estado: aplicativo experimental
compilado e executado; nenhuma publicação ou instalação global realizada.

## Entrada e plataforma

ZIP fornecido: `irixclassic-files-0.1.0-alpha1-mrmmx31.zip`.
SHA-256: `7a329d198f9690064ed95c229935cff05ec93d4d22ee723fcfc37ac863eeb59b`.
Extração conferida contra caminhos absolutos, travessia de diretórios e links.

Debian 13 amd64, Qt 6.8.2, KF6 6.13 e GCC 14.2. Fonte Dolphin Debian
`4:25.04.3-1+deb13u1`, obtida pelo APT com versão exata e patches Debian aplicados.
As dependências de desenvolvimento ausentes foram baixadas como pacotes Debian
oficiais e extraídas em `/tmp`; nenhum pacote foi instalado no sistema.

O programa é uma derivação que liga componentes internos do Dolphin, não um
cliente de uma API pública estável. A receita fixa a fonte e verifica as âncoras;
portar para outra versão exige revisar essas transformações.

## Correções necessárias

- Habilitar exceções somente na interface nova e seus consumidores: o Dolphin
  desabilita exceções por padrão, mas `ClassicShell` lança um erro de contrato
  tratado pelo entry point. O ZIP original não compilava nessa configuração.
- Usar `KStandardAction::name(KStandardAction::Redisplay)` no botão Atualizar;
  `redisplay` não era o nome registrado. O botão aparecia desativado com `?`.
- Fixar RUNPATH relativo nas bibliotecas e executáveis privados, desabilitando a
  inclusão automática de diretórios de link. O resultado usa `$ORIGIN` nas
  bibliotecas e `$ORIGIN/../lib` no aplicativo, sem depender do SDK temporário.
- Ampliar os testes nativos para seleção inicial (`--select`), seleção/preview,
  pin na Shelf, cópia e movimentação de arquivo com espaços e acentos, conteúdo
  preservado e vista dividida. A lista selecionada é guardada antes da cópia,
  porque a ação nativa atualiza a seleção ao criar os itens de destino.

## Resultados

- 41 testes Python do kit: aprovados.
- Configuração CMake e compilação de `irixclassic-bundle` e `irixclassic-tests`:
  aprovadas sobre a árvore Debian completa.
- Duas suítes CTest: aprovadas, 11 verificações Qt de CoreTest e 9 de AppTest
  (incluem inicialização/finalização). Duração final: 5,18 segundos; zero falhas.
- Preparação repetida do fonte original: 786 arquivos conferidos byte a byte
  contra o fonte usado na compilação; manifesto de preparação atualizado.
- Execução gráfica Wayland com Kvantum IrixClassic: navegação, imagem, texto e
  vista dividida. Quatro capturas reais conferidas. O botão Atualizar corrigido
  aparece ativo. Perfis e dados artificiais ficaram em `/tmp`.
- `ldd` sem bibliotecas ausentes nem dependências do SDK temporário. Pacote
  relocável inclui executável, worker e duas bibliotecas com SONAMEs próprios.

Os testes nativos rodam com `dbus-run-session`, Qt offscreen e diretórios
HOME/XDG temporários definidos pelo próprio teste. A falta de `org.kde.kuiserver`
no barramento privado gera aviso sobre progresso de jobs; cópia e movimentação
concluíram normalmente. Esse aviso não é uma falha de acesso a arquivos.

A aplicação gráfica usa cópias temporárias das configurações de Kvantum e KDE,
sem substituir o Dolphin, registrar FileManager1 ou alterar associações MIME.
As janelas abertas para captura foram fechadas após cada cenário.

## Escopo e reprodução

O repositório recebe apenas o kit, testes, documentação e workflow independente.
Fontes gerados, SDK, binários, logs e capturas não entram no Git. Os resultados
locais são entregues em `Downloads/irixclassic-files-validacao-20261007/`.

Construção normal: comandos do README. Na revisão, após fornecer o SDK em `/tmp`,
foram retomados os mesmos alvos CMake e executado:

```sh
env QT_QPA_PLATFORM=offscreen dbus-run-session -- ctest \
  --test-dir DIRETORIO-DE-BUILD -R '^irixclassic-' \
  --no-tests=error --output-on-failure --output-junit TESTS.xml
```

A etapa de empacotamento de `tools/build.py` foi reutilizada após os testes,
conservando binário e código-fonte correspondente juntos. O pacote permanece
alpha: não certifica fidelidade visual exata ao IRIX, todos os gestos Wayland,
protocolos remotos, lixeira, renomeação interativa ou regressão completa das
operações do Dolphin. O visualizador usa limites e processo separado, não
sandbox. Esses pontos continuam sujeitos a ensaios adicionais antes de estabilidade.
