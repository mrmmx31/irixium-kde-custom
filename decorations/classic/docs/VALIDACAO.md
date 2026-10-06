# Validação — IRIX Classic 1.0.0-rc3

## Base e preservação

Base pública: `mrmmx31/irixium-kde-custom`, commit
`3b128920e860119e686f1258f01208c4dbe771bb`, branch `#kvantum-classic-rc1`.
A integração anterior de Kvantum/instalador está presente nesse commit. Esta
correção não inclui nem substitui seus arquivos.

A cópia da Classic rc2 usada como origem reproduz exatamente o objeto de árvore
Git `8bb1602bd67d21a9b7eeb3779b4f62c6c8a51098`, incluindo permissões de execução.
O pacote gráfico anterior é a árvore `be3b83bd73c29bca39039a114f75b105b394b857`.
Os sete arquivos de desenho, geometria, Surface, entrada e preferências
registrados em `tests/preview-preserved.json` continuam byte a byte idênticos.
`main.qml` apenas instancia o novo componente antes de Surface; retirar esse
bloco recompõe exatamente o hash do adaptador rc2.

## Executado

| Teste | Resultado | Alcance |
|---|---|---|
| Python/unittest | 38 aprovados | 32 do instalador/recuperação, com backend simulado; 6 novos testes estáticos de integração e preservação |
| Máquina de estados JS | 34 aprovados | Sem alteração na lógica do clique, duplo clique, menu ou indisponibilidade |
| Desenho/geometria JS | 108 cenários aprovados | Incluem as 36 sequências de repouso da base anterior |
| Contrato de prévia JS | 21 aprovados | Executa PreviewSupport.js de produção com hospedeiros de teste; pai ausente/real, identidade, cor, supressão nativa, recolhimento |
| Geometria de área cliente | 96 cenários aprovados | Escalas internas 1/2/3, normal/maximizada, larguras/alturas e limites não negativos |
| Referências IRIX | 22.311 e 10.064 pixels, zero divergências | Retângulos de Artwork.js rasterizados em Pillow; não inclui o texto nem o conteúdo dos aplicativos |
| Sintaxe Python/shell | aprovada | ast.parse e sh -n |

Os testes JS do preenchimento não rasterizam o Loader QML: verificam o contrato
e as coordenadas. Os testes de desenho existentes não incluem a nova camada de
prévia. A ausência de mudanças nos retângulos antigos é uma regressão útil, não
uma prova da renderização da miniatura no compositor.

## Não executado

`bash testar.sh --qml` retornou 77: Qt 6 qmltestrunner ausente. Os 12 testes
QtTest novos de `tst_preview.qml` **não foram contabilizados como aprovados**.
O arquivo exercita instância/destruição do Loader, mudanças de pai/cor, inversão
de `drawBackground`, normal/maximizada e recolhimento com um PreviewItem simulado.

Não houve execução do KCM nativo, KWin ou do plugin Kvantum. É necessário reabrir
Configurações do Sistema depois da instalação e conferir a sobreposição das
miniaturas. O menu nativo e os gestos continuam sujeitos aos limites de teste
local já registrados na rc2; esta revisão não reimplementa esses comportamentos.

## Reprodução

```sh
bash testar.sh
bash testar.sh --qml
python3 tests/compare_references.py --irix1 /caminho/irix-1280x1024.png --irix2 /caminho/irix-1024x768.png
```

Referências não são redistribuídas. Registros desta revisão:
`validation/rc3-automated.txt`, `validation/rc3-qt-runtime.txt` e
`validation/rc3-reference-pixels.json`. Registros rc2 continuam preservados como
histórico, não como validação QML desta revisão.
