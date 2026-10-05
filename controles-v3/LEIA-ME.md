# Irixium — controles clássicos v3

Complemento para o Irixium já instalado. **Não é um tema completo nem uma atualização cumulativa das divisórias.** Mantém o `AuroraeButtonGroup.qml` existente; use junto da v2 das divisórias para conservar aquela correção.

## Resultado

- Menu da janela (“More actions”/“Mais ações”) à esquerda: `M`.
- Minimizar e maximizar/restaurar à direita: `IA`, no lugar de `HXA`.
- O símbolo pequeno que antes executava Fechar passa a executar **Minimizar**. O instalador copia, byte a byte, o `close.svg` local conferido para `minimize.svg`. Isso preserva todos os estados de desenho, inclusive inativo, hover e pressionado. Não é apenas uma mudança de rótulo: `I` seleciona a ação nativa de minimizar do Aurorae.
- O `close.svg` original não é apagado nem modificado. O botão `X` apenas deixa de integrar a disposição.
- Maximizar/restaurar conserva sua função e os SVGs atuais.
- Fechar permanece disponível no menu da janela. Atalhos não são alterados. A preferência já existente de fechar com duplo clique no menu também é preservada: o pacote não a liga nem a desliga.
- O botão de menu ganha fundo e relevo no hover, relevo mais profundo enquanto pressionado e um pequeno deslocamento do símbolo. Um feedback de 120 ms torna cliques rápidos perceptíveis sem acrescentar espera à ação do menu; sair da área/cancelar limpa o efeito. Essa duração não representa “menu aberto”: o efeito não fica travado até o fechamento do menu.

## O que o instalador escreve

1. `MenuButton.qml` do módulo Aurorae/Qt 6 instalado no sistema.
2. `~/.local/share/aurorae/themes/Irixium/minimize.svg` (respeita `XDG_DATA_HOME`).
3. Somente `ButtonsOnLeft` e `ButtonsOnRight` na seção `[org.kde.kdecoration2]` do `kwinrc` (respeita `XDG_CONFIG_HOME`).

Não escreve `AuroraeButtonGroup.qml`, `Irixiumrc`, `decoration.svg`, `maximize.svg`, `restore.svg`, `close.svg`, fontes, configurações GTK ou imagem do menu.

**Limites de escopo:** o desenho novo do menu só aparece no tema com pasta `Irixium`. Já a ordem de botões é uma preferência global do KWin, como era a ordem `HXA`; ela pode ser reaproveitada quando você selecionar outra decoração. Este pacote não cria perfis de ordem por tema.

## Aplicação

Salve e extraia o ZIP em uma pasta separada. Abra um terminal dentro de `irixium-controles-v3`.

```bash
bash instalar-controles.sh --verificar
bash instalar-controles.sh
```

Execute como seu usuário normal, **sem `sudo` antes do script**. A autorização administrativa é pedida somente para a cópia do QML do sistema, por `pkexec` ou `sudo` quando `pkexec` não estiver disponível.

O script usa Python 3 e a biblioteca padrão. Node.js é necessário apenas para reproduzir os testes de JavaScript, não para instalar.

O script aceita as duas versões de `MenuButton.qml` analisadas no repositório (antes e depois da restrição ao Irixium), além da própria v3. Recusa um componente diferente, um SVG de origem diferente, destinos que sejam links simbólicos ou uma decoração ativa diferente de Irixium. **Não force a instalação sobre um erro de compatibilidade.** `--verificar` não cria arquivos nem backups.

A imagem `/usr/share/kwin/aurorae/Irixium/applications.png` deve já existir; ela é a mesma usada na sua personalização atual.

Depois de aplicar, salve o trabalho, encerre a sessão do KDE e entre novamente. O script solicita apenas uma recarga de configuração quando `qdbus6` estiver disponível; não reinicia nem substitui o KWin e não encerra aplicativos. A sessão nova é necessária para testar o novo QML, que pode continuar em cache.

Caminhos fora do padrão podem ser indicados com `--qml-dir CAMINHO` e `--theme-dir CAMINHO`. `--qml-dir` deve ser o diretório que contém `MenuButton.qml`, não o caminho do arquivo. Use as mesmas opções ao restaurar.

## Verificação na sessão

Na mesma janela, teste o pequeno quadrado: ele deve minimizar, não fechar. Reabra pelo painel e confira maximizar/restaurar. No menu à esquerda, observe hover, clique mantido e soltura; saia da área durante um clique para confirmar que o relevo não fica preso. Verifique janela ativa/inativa, normal/maximizada, e a ação Fechar dentro do menu. A política de duplo clique deve continuar igual à configurada antes da v3.

As divisórias e as margens devem permanecer como estavam. Esta versão não tenta corrigir outras diferenças visuais da v2.

## Restauração

```bash
bash restaurar-controles.sh --verificar
bash restaurar-controles.sh
```

Encerre a sessão e entre novamente. A restauração recupera o menu e o minimizar anteriores à v3 e os valores anteriores da disposição. Não desfaz a v2 das divisórias. Outras alterações posteriores no `kwinrc` são preservadas.

Backups ficam, por padrão, em:

```text
~/.local/state/irixium-controles-v3/backups/
```

O backup inclui cópias completas anteriores, cópias das versões instaladas e hashes no manifesto. A restauração automática recusa conflitos quando o menu, o SVG ou a disposição foram alterados depois. Nessa situação, preserve o backup e reconcilie os arquivos; não force a cópia. Uma falha de autorização ou gravação gera tentativa de reversão, com indicação explícita caso seja necessária recuperação manual.

## Tornar as mudanças persistentes no seu checkout Git

A aplicação acima altera a instalação, **não o seu repositório**. O `update-irixium.sh` antigo continua contendo `ButtonsOnRight HXA`, e uma futura execução dele pode desfazer o comportamento novo e reinstalar o menu antigo.

O utilitário opcional abaixo atualiza quatro arquivos no checkout local: `MenuButton.qml`, `aurorae/Irixium/minimize.svg`, `kwin-decoration.conf` e somente a definição da ordem à direita em `update-irixium.sh`.

```bash
python3 integrar-repositorio.py /caminho/irixium-kde-custom --verificar
python3 integrar-repositorio.py /caminho/irixium-kde-custom
```

Ele exige que esses arquivos não tenham mudanças locais pendentes em relação ao HEAD. Não faz `commit`, `push`, troca de branch ou instalação; não altera o GitHub. Guarda um backup no diretório administrativo local do Git e deixa as alterações disponíveis para `git diff`. Use uma branch de trabalho e revise o diff antes de registrar.

O script `update-irixium.sh` do repositório continua com suas demais ações antigas (inclusive copiar o tema completo e aplicar fontes). A integração **não transforma esse script em um instalador parcial**, nem incorpora as divisórias da v2 ao repositório. Para apenas aplicar a v3 na sessão, prefira `instalar-controles.sh`.

## Arquivos avulsos

`MenuButton.qml` é o componente novo. `kwin-decoration.conf` neste pacote é um **fragmento de referência**, não substitui o seu `kwinrc` completo. `minimize.svg` é produzido na instalação/integração a partir do seu `close.svg`; não é necessário baixar outro desenho.

## Validação e licenças

Consulte `VALIDACAO.md`. Os testes exercitam instalação em diretórios temporários e JavaScript extraído do QML. **Não houve execução no Qt Quick/KWin real neste ambiente.** É necessária a conferência visual na sua sessão.

A autoria e a licença GPL-2.0-or-later do componente QML foram preservadas. O SVG reutilizado mantém o licenciamento original do Irixium. Textos de licença estão em `LICENSES/`, e referências/hash de origem em `ORIGEM.json`.
