# Irixium / IRIX Classic

Temas mantidos por **mrmmx31** para KDE Plasma 6. Todos os instaladores de temas
usam somente o perfil do usuário atual. Execute **sem sudo**.

## Instalar e aplicar

```sh
bash instalar-irixium.sh --verificar
bash instalar-irixium.sh
bash aplicar-tema.sh classic     # ou: moderno
```

A instalação atualiza 15 componentes gráficos locais, com backup, sem trocar a
seleção. A aplicação escolhe tema global, decoração, Kvantum, GTK, ícones,
cursores, cores, Plasma Style e splash correspondentes, sem redefinir painéis.
Não há download de dependências temáticas pela KDE Store nem instalação de SDDM.
Plasma 6, Aurorae/KSvg Qt 6 e Kvantum Qt 6 devem estar instalados pela distribuição.

Os temas completos e os destinos estão em [components.json](components.json),
usado pelo instalador e pela auditoria. A aplicação seleciona o esquema de sons
SGI **quando ele já está instalado e validado**; não modifica volume, mudo,
Não perturbe nem habilita eventos. `--sem-sons` preserva a seleção de sons.

Após atualizar QML em uso, salve o trabalho e encerre/entre novamente na sessão.
Reabra os aplicativos para carregar Kvantum e ícones. Não há reinício forçado do
KWin. Os botões mostram relevo durante a pressão e executam a ação na soltura;
duplo clique no menu fecha também a janela inativa. Somente o clique simples no
menu aguarda o intervalo de duplo clique do Qt; esse timer não participa do resize.

## Sons SGI: instalação local separada

O esquema, catálogo, mapeamento e instaladores estão em [sons/](sons/README.md).
Os áudios são baixados e instalados para seu usuário com atribuição à
[página histórica da SGI](https://ftp.jurassic.nl/mirrors/ftp.sgi.com/sgi/desktop/sounds/sounds.html).
Em outro computador:

```sh
bash sons/instalar.sh --baixar
bash aplicar-tema.sh classic --exigir-sons
```

O download usa HTTPS e valida os oito originais antes de converter para WAV.
Os bytes não entram no Git nem nos ZIPs. Com fontes já preparadas no cache local,
`bash sons/instalar.sh` reinstala sem rede; `--origem DIRETORIO` permite importar
uma cópia local. O downloader público substitui a necessidade do script privado.

Para exigir uma instalação com sons completos, audite com `--exigir-sons`.
Sem os originais, o conjunto gráfico continua instalável e o comando de aplicação
preserva os sons existentes. O comando com `--exigir-sons` recusa a aplicação,
em vez de anunciar que um esquema ausente foi configurado.

## Estrutura mantida

| Componente | Fonte |
|---|---|
| Decoração IRIX Classic | `decorations/classic/` |
| Decoração Irixium e seus assets | `decorations/modern/` |
| Estilos Qt Widgets | `kvantum/IrixClassic/`, `kvantum/Irixium/` |
| GTK 3/4 | `gtk/` |
| Ícones | `icons/themes/IrixClassic-SGI/`, `icons/Irixium/` |
| Cursores | `cursors/sgi/` |
| Cores | `colors/Irixium.colors` |
| Plasma Styles | `plasma/IrixClassic/`, `plasma/Irixium/` |
| Wallpapers | `wallpapers/IrixClassic/`, `wallpapers/Irixium/` |
| Tema global e splash | `look-and-feel/` |
| Sons, sem os áudios | `sons/` |
| Instaladores, auditoria, transações | `tools/` |
| Testes e validação | `tests/`, `docs/`, testes dos componentes |
| Empacotamento/release estável do Kvantum | `distribuicao/` |

As decorações não sobrescrevem o Aurorae compartilhado. Os antigos overlays,
instaladores de sistema e cópias redundantes foram retirados da árvore ativa;
continuam recuperáveis pelo histórico Git. Veja
[reorganização e inventário local](docs/REORGANIZACAO-2026-10-06.md).

O hook opcional da Classic só mantém seu pacote disponível no perfil do usuário;
não troca a seleção. O reparo opcional do KDE Qt Quick em `tools/qtquick_scrollbar_fix.py`
é uma ferramenta de manutenção separada, fora da instalação dos temas.

## Validar e restaurar

```sh
python3 tools/audit_suite.py                    # fontes e vínculos no repositório
python3 tools/audit_suite.py --local --exigir-sons
bash testar-integracao.sh                      # todos os componentes públicos
bash instalar-irixium.sh --restaurar --verificar
bash instalar-irixium.sh --restaurar
bash aplicar-tema.sh --restaurar
```

As restaurações recusam sobrescrever edições posteriores. Backups ficam em
`XDG_STATE_HOME/irixium-suite` e `XDG_STATE_HOME/irixium-selection`. Sons possuem
seus próprios backups e restauração em `sons/restaurar.sh`.

Para desenvolvimento de componentes individuais, os READMEs das decorações e
Kvantum descrevem suas prévias, testes e instaladores. `update-irixium.sh` e
`restaurar-irixium.sh` continuam como atalhos para a decoração moderna.

## Créditos e licenças

Irixium moderno/Aurorae e Kvantum: Mark Whittaker / Phob1an. GTK: TheJollyDuck /
Shauna Recto. Cursores: jujum4n e colaboradores. Metadados e procedência ficam
junto de cada componente e em [UPSTREAMS.md](UPSTREAMS.md).

Créditos/licenças dos assets upstream foram preservados. O snapshot de ícones
Irixium não declara licença; o tema global upstream tem declarações GPL
conflitantes. Essas pendências não foram substituídas por uma licença presumida.
GTK separa licença de código e imagens no seu README. Os sons SGI não recebem
uma licença local nem entram no pacote público. IRIX/SGI são referências/marcas
de seus titulares; fontes tipográficas proprietárias e código privado do IRIX
não são incluídos. Nimbus Sans é fornecida pela distribuição.
