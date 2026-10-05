# Irixium / IRIX Classic

Personalizações mantidas por **`mrmmx31`**. Decoração de janela e estilo de
aplicativos são componentes separados; instalar um não deve trocar o outro.

| Componente | Diretório | Situação |
|---|---|---|
| Decoração Irixium moderno | `aurorae/Irixium/` + `moderno/geometria/` | Símbolos e efeitos modernos; margens e divisórias organizadas. |
| Decoração IRIX Classic | `classic-rewrite-rc1/` | Reescrita 1.0.0-rc3; preenchimento restrito à miniatura do KCM. |
| Application Style Irixium | `kvantum/Irixium/` | Base original preservada. |
| Application Style IrixClassic | `kvantum/IrixClassic/` | Primeira candidata 0.1.0-rc1 para Qt Widgets. |
| Tema GTK | `gtk/` | Base preservada; não é instalada pelos novos fluxos abaixo. |

## Atualização segura da decoração moderna

Na raiz do checkout, como usuário normal, **sem sudo**:

```sh
bash update-irixium.sh --verificar
bash update-irixium.sh
```

**Mudança em relação ao instalador anterior:** sem opções, instala/atualiza o
Irixium, mas preserva a seleção atual, a disposição global dos botões e as fontes.
Assim, quem está usando IRIX Classic não é trocado para o moderno sem pedir.

Opções explícitas:

```sh
bash update-irixium.sh --ativar
bash update-irixium.sh --ativar --aplicar-fontes
```

`--ativar` seleciona Irixium e aplica a disposição de `kwin-decoration.conf`.
`--aplicar-fontes` reaplica o perfil declarado em `kde-fonts.conf`. O primeiro
comando não aplica fontes por implicação. Nenhum muda a escala da tela.

O plano completo é validado antes da primeira escrita. Um recibo privado guarda
conteúdo e permissões anteriores de cada arquivo afetado; falhas provocam tentativa
de restauração. A geometria vem exclusivamente de `moderno/geometria/`, nunca do
`AuroraeButtonGroup.qml` legado na raiz. A seleção/fontes são gravadas por último;
`reconfigure` só é solicitado depois da conferência final.

Os componentes `MenuButton.qml`, `AuroraeButtonGroup.qml` e a imagem de menu são
recursos compartilhados do Aurorae: sua cópia exige autorização administrativa
solicitada pelo próprio instalador. Os comportamentos personalizados continuam
limitados ao Irixium. Uma versão desconhecida do grupo Aurorae é recusada.

**Salve o trabalho, encerre a sessão e entre novamente** para recarregar QML.
Não há reinício forçado do KWin. Arquivos da Classic e do Kvantum não são alterados.

Restauração da última atualização global:

```sh
bash restaurar-irixium.sh --verificar
bash restaurar-irixium.sh
```

Em caso de interrupção ou restauração não concluída, use `--recuperar`. Recibos:
`${XDG_STATE_HOME:-$HOME/.local/state}/irixium-update/backups/`.
Edições posteriores desconhecidas bloqueiam a restauração, em vez de serem apagadas.
Cópias legadas `*.irixium-original` não são substituídas nem removidas.
Consulte `docs/INSTALACAO-RECUPERAVEL.md` para limites e recuperação.

## Decoração IRIX Classic

Esta atualização não modifica a reescrita nem sua correção de duplo clique.
Seu fluxo permanece:

```sh
bash classic-rewrite-rc1/instalar.sh --verificar
bash classic-rewrite-rc1/instalar.sh
```

A Classic independente não exige sobrescrever QML de sistema. Suas opções,
restauração e limitações de integração estão no README próprio. `classic-v4/`,
`controles-v3/`, `divisorias-v1/` e `divisorias-v2/` ficam como histórico/referência,
não como etapas que devem ser reinstaladas em sequência.

Para atualizar somente a geometria do moderno, o complemento existente continua
válido: `bash moderno/geometria/instalar.sh --verificar`. Não execute dois
instaladores ao mesmo tempo. O fluxo global coopera com o bloqueio desse módulo.

## Application Style IrixClassic (Kvantum)

Primeiro teste em uma galeria Qt Widgets com configuração temporária:

```sh
bash kvantum/prever-classic.sh
```

Exige PyQt6 ou PySide6 e Kvantum Qt 6; dependência ausente é informada, não instalada.
Para copiar o tema sem selecionar:

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
```

Depois selecione **IrixClassic** no Kvantum Manager, mantendo **kvantum** como
Application Style do KDE. Ou use `--ativar` para trocar somente a seleção interna
do Kvantum. Reabra os aplicativos. A decoração da janela não é trocada.
Restauração: `bash kvantum/restaurar-classic.sh`.

A paleta e o desenho são uma proposta baseada nas referências IRIX; abas e estados
não documentados são adaptações declaradas. Não há alegação de identidade completa
com o IRIX. As fontes globais continuam intocadas. Veja `kvantum/IrixClassic/README.md`.

## Desenvolvimento e revisão

```sh
bash testar-integracao.sh
./check-upstreams.sh
```

Os testes automatizados de integração não substituem testes reais no KWin/Qt.
Confira `docs/VALIDACAO-INTEGRACAO.md`. Nenhum script faz commit ou push.
Revisões de upstream devem ser propostas em branch separada e revisadas antes do
merge na branch de destino; nunca substitua personalizações automaticamente.

## Créditos e licença

A decoração `aurorae/Irixium/` é baseada em Irixium por Phob1an. O Kvantum moderno
é de Mark Whittaker/Phob1an. `gtk/` é baseado em Irixium por TheJollyDuck/Shauna
Recto. Créditos, licenças e fontes preservadas estão nos respectivos diretórios;
os textos GPL permanecem em `LICENSE`, `gtk/LICENSE` e nos pacotes.

`applications.png` é o desenho de 22×22 desta personalização. O SVG IrixClassic
Kvantum é novo; o moderno não é sobrescrito. Os novos utilitários são
GPL-3.0-or-later. IRIX e SGI são referências/marcas de seus titulares; nenhum
binário, fonte tipográfica ou código privado do IRIX é incluído.

Fora do Irixium, o `MenuButton.qml` mantém o ícone da janela fornecido por
`decoration.client.icon`. Quando o cliente não fornece um ícone, usa
`application-x-executable` como fallback para que o botão de ações não fique
vazio.
