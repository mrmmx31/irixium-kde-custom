# Irixium / IRIX Classic

Personalizações mantidas por **`mrmmx31`**. Decoração de janela e estilo de
aplicativos são componentes separados; instalar um não deve trocar o outro.

| Componente | Diretório | Situação |
|---|---|---|
| Decoração Irixium moderno | `modern-rewrite-rc1/` (assets em `aurorae/Irixium/`) | Pacote KWin independente `irixium_modern`; símbolos e efeitos modernos. |
| Decoração IRIX Classic | `classic-rewrite-rc1/` | Reescrita 1.0.0-rc3; preenchimento restrito à miniatura do KCM. |
| Application Style Irixium | `kvantum/Irixium/` | Base original preservada. |
| Application Style IrixClassic | `kvantum/IrixClassic/` | Primeira candidata 0.1.0-rc1 para Qt Widgets. |
| Tema GTK | `gtk/` | Base preservada; não é instalada pelos novos fluxos abaixo. |
| Ícones Irixium | `icons/Irixium/` | Snapshot do pacote KDE Store 2142965; licença upstream ainda não declarada no payload. |
| Plasma Style Irixium | `plasma/Irixium/` | Snapshot do pacote KDE Store 1457753; GPL3 declarada pelo pacote. |
| Plasma Style IrixClassic | `plasma/IrixClassic/` | Cópia nomeada do Irixium, reservada para futuras alterações do Classic. |
| Look-and-Feel e splash | `look-and-feel/org.magpie.irixium.desktop/` | Splash incluído no pacote; declarações de licença conflitantes preservadas. |
| Cursores SGI | `cursors/sgi/` | Cursor ativo; cópia verificada do upstream `jujum4n/sgi-enhanced`. |

## Atualização segura da decoração moderna

Na raiz do checkout, como usuário normal, **sem sudo**:

```sh
bash update-irixium.sh --verificar
bash update-irixium.sh
```

O fluxo instala/atualiza o pacote `irixium_modern` em
`~/.local/share/kwin/decorations/`, preserva a seleção atual e não altera
componentes Aurorae compartilhados do sistema. Assim, quem está usando IRIX
Classic não é trocado para o moderno sem pedir.

Opções explícitas:

```sh
bash update-irixium.sh --ativar
```

`--ativar` seleciona `irixium_modern`. O pacote possui seu próprio botão de ações
e seus próprios assets; nenhuma cópia de `MenuButton.qml`, `AuroraeButtonGroup.qml`
ou `applications.png` é feita em `/usr`.

**Salve o trabalho, encerre a sessão e entre novamente** para recarregar QML.
Não há reinício forçado do KWin. Arquivos da Classic e do Kvantum não são alterados.

Restauração da última atualização do pacote moderno:

```sh
bash restaurar-irixium.sh --verificar
bash restaurar-irixium.sh
```

Recibos privados ficam em
`${XDG_STATE_HOME:-$HOME/.local/state}/irixium-modern/backups/`. A restauração
somente remove a cópia instalada pelo pacote e recoloca o backup anterior.

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

`moderno/geometria/` é um histórico de integração do Aurorae compartilhado e não
faz parte do novo fluxo. Não o execute: o pacote moderno independente já contém
seu layout, assets e controles.

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

Os componentes KDE Store preservam seus metadados originais. A licença dos
ícones não está declarada no snapshot instalado; o Look-and-Feel contém
declarações conflitantes entre `metadata.desktop` e `metadata.json`. Essas
pendências não são substituídas por uma suposição local. O cursor `sgi` é
declarado pelo upstream como GPL, sem versão especificada no checkout atual;
sua procedência está em `cursors/sgi/ORIGEM.json`.

`applications.png` é o desenho de 22×22 desta personalização. O SVG IrixClassic
Kvantum é novo; o moderno não é sobrescrito. Os novos utilitários são
GPL-3.0-or-later. IRIX e SGI são referências/marcas de seus titulares; nenhum
binário, fonte tipográfica ou código privado do IRIX é incluído.

Fora do Irixium, o `MenuButton.qml` mantém o ícone da janela fornecido por
`decoration.client.icon`. Quando o cliente não fornece um ícone, usa
`application-x-executable` como fallback para que o botão de ações não fique
vazio.
