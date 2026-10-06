# Validar a integração

O inventário ativo é `components.json`. `tools/audit_suite.py` valida fontes,
manifestos de decoração, destinos e referências dos temas globais. Com `--local`,
compara o conteúdo instalado, normalizando links internos materializados e o ID
Classic transformado pelo instalador. Também verifica o esquema real de sons,
sem reprodução nem download. `--exigir-sons` torna obrigatório o esquema local.

`bash testar-integracao.sh` executa os testes públicos de instaladores, Kvantum,
decorações, ícones, sons e distribuição. Testes estáticos não provam interação
no compositor. Para Qt real, em D-Bus privado:

```sh
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software dbus-run-session -- \
  /usr/bin/python3 decorations/classic/tests/test_native_render.py
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software dbus-run-session -- \
  /usr/bin/python3 decorations/classic/tests/test_native_input.py
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software dbus-run-session -- \
  /usr/bin/python3 decorations/modern/tools/prever_renderizacao.py --testar
```

Os resultados anteriores e suas limitações estão em
`VALIDACAO-CORRECOES-2026-10-06.md`; a reorganização e a comparação local estão em
`REORGANIZACAO-2026-10-06.md`. Artefatos temporários e caches não fazem parte da
fonte distribuída. Não execute instaladores antigos de outros clones.
