# Irix Classic — cobertura de ícones de 07/10/2026

A revisão completa parte do ZIP `auditoria-irix-completa-qt-dbus.zip` e de uma
nova auditoria da sessão real. O auditor externo permanece fora do Git.
Somente o catálogo normalizado, nossos geradores, a arte original e os testes
fazem parte do repositório.

## Resultado do pacote 0.3.0

O tema contém **720 ícones canônicos, 265 composições detalhadas e 2.296 nomes**.
Os aliases representam famílias MIME ou a função de cada aplicação. São SVGs
editáveis e PNGs nativos em 16, 22, 24, 32, 44, 48, 64, 96 e 128.
Os 126 desenhos canônicos anteriores em 64 foram preservados.

Todos os nomes do relatório inicial receberam cobertura explícita, inclusive
os que antes eram encontrados somente em Breeze/hicolor. Foram incorporadas
as variantes de status publicadas no computador: níveis e estados de Wi-Fi,
rede cabeada, rede móvel, Bluetooth, volume, microfone, bateria e notificações.
Os níveis e estados preservam símbolos próprios. Os desenhos seguem contorno
escuro, cores moderadas e a perspectiva do
[guia da SGI](https://techpubs.jurassic.nl/library/manuals/2000/007-2167-002/sgi_html/ch02.html).
A arte nova e os geradores têm licença MIT; não incluem logotipos comerciais,
fontes ou desenhos extraídos de outros temas.

O menu usa novamente o computador colorido. Os nomes `-symbolic` da bandeja
mantêm a paleta SGI; ações simbólicas continuam monocromáticas. Isso atende
os nomes solicitados pelo Plasma 6. Foram removidas imagens antigas em
contextos conflitantes, que o Qt selecionava antes dos desenhos atualizados.
Word, Excel e apresentações têm símbolos distintos.

## Integrações locais

`tools/adapt_classic_launchers.py` corrige ícones absolutos em uma lista
explícita de atalhos conhecidos. Preserva os comandos e outros campos, cria
cópias locais dos atalhos compartilhados e salva backup. Também corrige o
ícone absoluto do MIME de shell script no perfil local, preservando seus globs.
São 13 atalhos adaptados neste computador e um pacote MIME local corrigido.

```sh
python3 tools/adapt_classic_launchers.py --verificar
python3 tools/adapt_classic_launchers.py
python3 tools/adapt_classic_launchers.py --restaurar
```

O PIA fornece bitmaps próprios. A integração autorizada, documentada em
[integrations/pia](../integrations/pia/README.md), substitui somente os recursos
de bandeja da sua interface, preservando seis estados, menus e cliques. Foi
instalada exclusivamente no perfil atual. Não altera o daemon ou a conexão,
não acrescenta temporizadores e não modifica `/opt`.

## Verificação

- 32 testes de ícones e 74 testes de integração passaram.
- A inspeção estrutural encontrou zero erros e zero avisos.
- O Qt real realizou **20.664 consultas**: 2.296 nomes × nove tamanhos, sem
  temas herdados. Cada resultado corresponde aos pixels do PNG esperado.
- A auditoria externa final encontrou 1.561 nomes não vazios, todos no tema
  nos 12 tamanhos/escalas examinados: 18.732 resoluções próprias. Zero nomes
  ausentes, herdados, hicolor ou absolutos. O valor vazio restante pertence a
  metadados sem ícone e não representa um desenho faltante.
- Os 24 recursos do PIA foram conferidos com seu Qt e biblioteca de cliente.
  O bitmap real da bandeja corresponde à nossa arte de desconectado. A VPN
  permaneceu desconectada; somente a interface foi reaberta.
- A auditoria local da suíte com `--exigir-sons` passou, com dependências,
  perfil Classic e sons coerentes.

Essa cobertura corresponde aos nomes publicados neste computador; não
comprova os ícones internos de qualquer aplicação possível, miniaturas ou
conteúdo de páginas web. A auditoria registrou dois metadados externos
malformados (`snxgui.desktop` e `kcmtrash.desktop`), sem desenhos faltantes no
Classic. Não foram editados arquivos do sistema para ocultar esses avisos.

A recarga por `refreshCurrentShell` encerrou o Plasma durante o teste. O
serviço foi iniciado novamente com o layout preservado; as verificações
posteriores confirmaram serviço ativo e bandeja funcional. Não é necessário
usar esse método para aplicar os ícones.

```sh
python3 icons/tools/build_classic.py --output /tmp/IrixClassic-SGI-rebuild
python3 icons/tools/validate_theme.py /tmp/IrixClassic-SGI-rebuild
python3 -m unittest discover -s icons/tests
python3 -m unittest discover -s tests
python3 icons/tools/preview_classic_audit.py --saida /tmp/classic-auditoria.png
python3 tools/audit_suite.py --local --exigir-sons
```

A instalação, atualização dos caches e adaptações têm backups privados e
se restringem ao usuário atual. Nenhuma configuração de outros usuários foi
alterada. O fallback para nomes futuros desconhecidos continua disponível.
