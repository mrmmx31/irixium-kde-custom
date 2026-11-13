# IRIX Classic para Wine

Tema visual original com a paleta e 53 bitmaps dos controles do GTK Classic
deste repositório: botões e estados pressionados, check vermelho, rádio em
losango azul, campos, listas, barras de rolagem, abas, progresso e menus.
O tema herda as fontes do prefixo e dos aplicativos. Não acrescenta timers
de animação, serviços ou substituições de DLLs.

## Aplicar num prefixo

Execute como o dono de um prefixo já inicializado, sem sudo:

```sh
python3 wine/IrixClassic/package/manage.py --prefix "$HOME/.wine"
python3 wine/IrixClassic/package/manage.py --prefix "$HOME/.wine" --verificar
python3 wine/IrixClassic/package/manage.py --prefix "$HOME/.wine" --exibir
# Restaurar a aparência anterior:
python3 wine/IrixClassic/package/manage.py --prefix "$HOME/.wine" --restaurar
```

O assistente instala `IrixClassic.msstyles` dentro do prefixo selecionado e
ativa o estilo pela API de temas do próprio Wine. O backup fica em
`PREFIX/.irixclassic-theme/backups/`. A restauração confere alterações
posteriores e recompõe somente os valores de aparência alterados pela
instalação. Preserva configurações de aplicativos, DLLs, versão do Windows e
preferências posteriores que não foram alteradas pelo tema. Não encerra o
Wine nem aplicativos em execução. Reabra os aplicativos para conferir o estilo.

O assistente e a galeria fornecidos são x86-64; precisam de prefixo `win64`.
O recurso `.msstyles` também pode ser selecionado manualmente pela aba
**Desktop Integration / Integração com a área de trabalho** do `winecfg` em
outros prefixos; essa utilização não foi certificada no teste win64. O arquivo
`.theme` oferece apenas a paleta para importação manual, sem os bitmaps.
Aplicativos que desenham seus próprios controles podem ignorar o estilo Wine.

`instalar-irixium.sh` copia este pacote para
`$XDG_DATA_HOME/irixium-suite/wine/IrixClassic` (normalmente `~/.local/share`).
Essa instalação geral não exige Wine e não aplica o estilo a prefixos.
O `manage.py` instalado funciona sem acesso ao checkout e continua exigindo
`--prefix` explícito. Escolher o tema global KDE não troca o tema do Wine.

## Origem e manutenção

Código e adaptação: GPL-3.0-or-later. Os desenhos vêm exclusivamente de
`gtk/IrixClassic/common/assets`; hashes e referências estão em
[`ORIGEM.json`](IrixClassic/package/ORIGEM.json). Não há tema da Microsoft ou
tema de terceiros importado. Fontes dos utilitários Win32 estão em `native/`.

```sh
# Dependências opcionais de manutenção: Python/Pillow, Clang,
# LLVM dlltool/rc/cvtres 19 e GNU ld com suporte PE.
python3 wine/tools/build_theme.py
python3 wine/tools/build_native.py
python3 -m unittest discover -s tests -p test_wine_classic.py
# Wine, Xvfb, xdotool e ImageMagick para o teste nativo isolado:
xvfb-run -a -s '-screen 0 1200x800x24' python3 wine/tools/test_native.py \
  --output /tmp/irix-wine-test-novo
```

O teste cria seu próprio prefixo, verifica o carregamento de nove classes,
captura controles reais nos estados normal/pressionado, executa um clique
Win32 e valida idempotência, fontes, restauração e recuperação de falha na
gravação do recibo. As capturas e os prefixos temporários não são versionados.
Consulte a [validação nativa](VALIDACAO-2026-10-08.md).

Referências técnicas: [carregador do Wine 10](https://github.com/wine-mirror/wine/blob/wine-10.0/dlls/uxtheme/msstyles.c),
[API de temas do Wine](https://github.com/wine-mirror/wine/blob/wine-10.0/dlls/uxtheme/uxtheme.spec)
e [formato de cores .theme](https://learn.microsoft.com/en-us/windows/win32/controls/themesfileformat-overview).
