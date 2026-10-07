# Ícones SGI para a barra lateral do Kate

IRIX Classic 0.4.1 acrescenta `project-open` (pasta de projeto com índice) e
`git` (placa em perspectiva com os ramos do Git), desenhados em SVG no próprio
repositório. O Kate 25.04.3 consulta `project-open` pelo tema, mas sua função
`gitIcon()` lê o recurso `:/icons/icons/sc-apps-git.svg`, sem consultar o tema.
Isso explica por que apenas atualizar o pacote não corrige o segundo botão.

A integração opcional registra somente esse SVG antes dos recursos originais,
apenas no processo do Kate aberto pelo atalho local. Não altera o pacote da
distribuição, documentos, sessões ou configurações de outros usuários. Não há
repaint extra, temporizador ou consulta periódica. O próprio Kate mantém o
comportamento das ações. A biblioteca remove seu preload do ambiente antes
de o aplicativo iniciar terminais e outros programas.

```sh
python3 icons/tools/install_theme.py --atualizar
python3 tools/adapt_kate_icons.py
# Somente conferir, ou desfazer:
python3 tools/adapt_kate_icons.py --verificar
python3 tools/adapt_kate_icons.py --restaurar
```

Execute sem sudo. Requer Kate com Qt 6, CairoSVG para gerar o tema,
compilador C e `rcc` do Qt 6. Instala um wrapper, biblioteca compilada localmente,
manifesto e cópia de `org.kde.kate.desktop`, com backup/restauração. A biblioteca
compilada não é versionada. Comandos personalizados, ativação D-Bus personalizada
e links simbólicos são recusados; a restauração preserva edições posteriores.

Salve seus documentos e reabra o Kate pelo menu para carregar o recurso novo.
Um processo que já está aberto conserva o ícone Git em cache. Abrir diretamente
`/usr/bin/kate` usa o recurso original. A instalação não encerra suas janelas.

Validação neste computador: três testes de instalação/restauração,
35 testes de ícones, comparação do recurso e dos pixels retornados pela função
real `gitIcon()` em 16/24/32 px, além de captura de uma janela de teste separada.
`verify.cpp` é um diagnóstico opcional que requer os cabeçalhos Qt 6 e
uma sessão D-Bus acessível. A fonte dos dois desenhos está em
`icons/tools/classic_identity.py`; o catálogo em `classic-identities.json`.

Referência: [barra lateral do plugin de projetos do Kate](https://github.com/KDE/kate/blob/master/addons/project/kateprojectpluginview.cpp).
