# Validação da entrega — IrixClassic Files 0.1.0-alpha1

Data da entrega original: 2026-10-06. Manutenção: `mrmmx31`.

A revisão posterior compilou e executou esta alpha no Debian 13. Os resultados
atuais estão em [VALIDACAO-LOCAL-2026-10-07.md](VALIDACAO-LOCAL-2026-10-07.md).
O registro abaixo descreve o estado anterior à revisão local.

## Registro histórico do ZIP original

Implementação de código-fonte C++/Qt/KDE e integração de build, pronta para a
primeira compilação na plataforma de destino. **Não há executável compilado,
aceite nativo, screenshot da aplicação ou release publicada nesta entrega.**
O nome alpha não certifica funcionamento. Não promover para estável a partir
dos resultados estáticos abaixo.

## Verificações executadas

- 41 testes Python: transformações com âncoras únicas, funções C++ com comentários/
  strings, isolamento de view properties/bookmarks, preservação da origem,
  rejeição de bases erradas e de links, contratos estruturais e manifesto de
  instalação. Todos aprovados.
- 9 testes do aplicador: consulta sem escrita, aplicação, idempotência, preservação
  do stage, reversão e recusas de conflitos/edições/links/hash. Todos aprovados.
- Leitura sintática de todos os módulos Python e `sh -n` dos scripts: aprovada.
- Workflow analisado como YAML; `contents: read` e actions fixadas por SHA.
- Patch aditivo: aplicação e reversão conferidas em checkout temporário, com
  hashes e permissões dos alvos conferidos.
- Integridade do ZIP e correspondência do manifesto: conferidas.

**As transformações foram exercitadas em fixtures estruturais baseadas nos trechos
upstream consultados. Não foi obtida nem compilada uma árvore completa do fonte
Debian neste ambiente.** A fixture testa o algoritmo, não prova que todas as
âncoras da distribuição coincidam. A versão, a série de patches e as âncoras são
verificadas novamente pelo preparador local, que recusa divergências.

## Verificações nativas não executadas

A sondagem real de pré-requisitos com CMake parou em `find_package(Qt6)` por
falta de `Qt6Config.cmake`. O ambiente também não dispõe dos SDKs KF6 e o download
por DNS do container estava indisponível. Portanto não houve compilação,
linkedição, execução dos testes Qt, teste do instalador com binários reais,
validação Wayland ou execução do workflow GitHub Actions. Não contamos esses
itens como aprovados ou como falhas de interação da aplicação.

Os dois executáveis Qt de teste estão no código (navegação/ações, Shelf,
preview e armazenamento privado). O construtor exige configuração, compilação,
CTest e bibliotecas relocáveis aprovados antes de criar os arquivos distribuíveis.
Isso não substitui o primeiro ensaio local com dados de demonstração.

## Limites e aceite para uma primeira prerelease

Usar `tools/create_demo.py` para começar. Confirmar navegação, abas/vista dividida,
seleção por mouse/teclado, referências da Shelf sem mover/excluir originais,
preview de texto e imagens, recusa de arquivo não suportado e coexistência com
o Dolphin. Operações nativas de cópia/movimentação/exclusão continuam reais e
não foram submetidas a uma regressão completa aqui. Não começar o teste com
arquivos importantes. O helper de preview limita trabalho, mas não é sandbox.

A aparência exata, ícones históricos e thumbwheel não foram certificados; o zoom
vertical atual é um slider nativo. Sons, mídia/PDF e refinamentos posteriores
ficam no plano. O gerenciador original, os temas estáveis, as decorações e o
esquema sonoro não são substituídos por este kit.

## Publicação

O script de publicação só aceita um relatório de build nativo bem-sucedido,
os mesmos fontes e pacotes, e um commit revisado/enviado. A publicação é explícita
como prerelease `irixclassic-files-v0.1.0-alpha1`. Nenhuma tag ou publicação foi
executada nesta entrega. Hashes não são assinatura digital nem prova de autoria.
