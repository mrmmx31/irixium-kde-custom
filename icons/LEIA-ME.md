# Ícones Irixium / IrixClassic-SGI

`Irixium/` mantém o snapshot upstream; `themes/IrixClassic-SGI/` contém o tema
Classic expandido **0.3.0**. O conjunto principal instala e atualiza ambos:

```sh
bash ../instalar-irixium.sh
bash ../aplicar-tema.sh classic     # ou: moderno
```

Para atualizar somente os arquivos dos ícones, preservando a seleção:

```sh
python3 tools/install_theme.py --atualizar
python3 tools/install_theme.py --theme Irixium --atualizar
```

Sem `--atualizar`, o instalador individual recusa destino existente. Atualizações
usam backup por usuário e atualizam os caches disponíveis. Não apague caches de
outros temas/usuários. Reabra os aplicativos, ou entre novamente na sessão,
quando o carregador ainda mantiver imagens antigas.

## Validar

```sh
python3 tools/validate_theme.py themes/IrixClassic-SGI --report /tmp/irixclassic-icons.json
python3 tools/validate_theme.py Irixium --report /tmp/irixium-icons.json
python3 -m unittest discover -s tests -v
```

O auditor confere índice, nomes, imagens, dimensões, transparência, aliases e
recursos externos. A instalação comum usa Python padrão; testes e geração
opcionais exigem os módulos informados pelas ferramentas. Nenhum script instala
pacotes de sistema ou baixa recursos.

## Fontes e referências

`tools/build_classic.py` gera a base original 0.1.0. Seus 126 ícones-base e 292
nomes não representam a contagem do pacote expandido 0.3.0. `manifest.json`,
`manifest-0.2.0.json` e `manifest-0.3.0.json` preservam as etapas de geração e
expansão; consulte também `PROVENANCE.txt` e a licença do tema.

Para produzir a base e novas prévias em diretório inexistente fora do checkout:

```sh
python3 tools/build_classic.py --output /tmp/irix-icons-base --previews /tmp/irix-icons-previas
```

Essa saída é a base de geração, não substitui automaticamente o pacote 0.3.0.
O gerador requer CairoSVG; as prévias também requerem Pillow. Arte original,
aliases adicionais e estados simbólicos distribuídos permanecem no pacote.
Logs, checksums e prévias antigas foram retirados; resultados novos ficam fora
da fonte. Os testes de cache GTK não substituem a inspeção de aplicativos KDE.

`tools/repair_irixium.py` cria uma cópia corrigida e registra alterações sem
reescrever o original. O patch de índice em `patches/` e sua fixture ainda são
usados pelos testes. Procedência/licenças e limites ficam em `docs/` e
`Irixium/ORIGEM.json`; não se atribuiu uma licença presumida ao snapshot upstream.

O Classic é uma criação inspirada em SGI, não uma extração oficial. Temas de
fallback `breeze,hicolor` são fornecidos pelo sistema. Aplicativos com imagens
embutidas, miniaturas e ícones de applets podem usar outros mecanismos.
