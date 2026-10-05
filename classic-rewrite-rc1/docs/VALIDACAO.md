# Validação — IRIX Classic 1.0.0-rc1

## Executado nesta revisão

| Teste | Resultado | Alcance |
|---|---|---|
| Python/unittest | 29 testes aprovados | Sistema de arquivos real em pastas temporárias; backend KDE e UID simulados |
| Máquina de estados JavaScript | 18 testes aprovados | Sequências de pressão, soltura, cancelamento, capacidade, menu, clique duplo e acessibilidade |
| Desenho/geometria JavaScript | 108 cenários aprovados | Limites, paleta, grade, efeitos, alvos sem colisão e 36 sequências de repouso preservadas |
| Referência IRIX 1 | 22.311 pixels, 0 divergências | Moldura e símbolos, sem texto nem aplicativo |
| Referência IRIX 2 | 10.064 pixels, 0 divergências | Barra superior, sem texto |
| Sintaxe Python e shell | aprovada | ast.parse e sh -n |
| Pixels.js | bytes idênticos aos da base anterior | SHA-256 em validation/provenance.json |

Os cenários de desenho incluem a comparação das 36 sequências: não são 108 + 36
cenários independentes. As referências são as mesmas utilizadas para construir
os mapas, e não amostras cegas de validação de todo o IRIX.

O desenhista executado é o próprio `Artwork.js`. Um gravador Context2D registra
retângulos, inclusive translate/save/restore, e a comparação com os PNGs utiliza
Pillow. **Isso não é uma captura Qt Quick, nem testa antialiasing/escala/texto do
compositor.** A correspondência medida não garante identidade pixel a pixel na
sessão final, particularmente em escala fracionária.

A suíte do instalador cobre reutilização de v4/v5, ausência de novas entradas,
ambiguidade de múltiplas instalações, atualização no mesmo destino, configuração
não relacionada, restauração de pasta, preservação de escolha posterior, recusa
de edições posteriores, recusa de backup alterado, links simbólicos, alteração de
manifesto, falha de ativação, migração literal de aparência, execução root,
recibos inválidos e interrupção simulada entre as renomeações de diretório.

## Não executado

Não há runtime Qt 6/KWin disponível no ambiente de preparação. A tentativa de
executar `bash testar.sh --qml` foi encerrada com **código 77: executor ausente**.
Os dez casos de QtTest estão fornecidos para execução local, mas **não foram
contabilizados como aprovados**.

Também não foram executados: carga do plugin nativo, foco real entre aplicativos,
ações de minimizar/maximizar sobre clientes, seleção arrastada do popup nativo,
duplo clique que atravesse a captura do menu, transporte de acessibilidade e
renderização de fonte. A API foi consultada em fontes primárias, sem substituí-las
por APIs inventadas, mas inspeção de código não equivale a teste de integração.

**Resultado: candidata para ensaio local; não release homologada no KWin.**
A reescrita organiza e testa o contrato do código; não elimina a necessidade de
registrar o roteiro de ACEITACAO.md na sessão Wayland do usuário.

## Reproduzir

```sh
bash testar.sh
bash testar.sh --qml
bash testar.sh --janelas
```

Os dois últimos comandos são opcionais e dependem dos executores Qt 6. Nenhum
comando instala dependências. `--qml` testa os componentes portáveis sem o backend
KWin; `--janelas` abre clientes nativos para ensaiar a decoração selecionada.

A comparação com os arquivos originais pode ser repetida com Pillow e Node:

```sh
python3 tests/compare_references.py --irix1 /caminho/irix-1280x1024.png --irix2 /caminho/irix-1024x768.png
```

Registros brutos: `validation/automated.txt`, `validation/reference-pixels.json`
e `validation/qt-runtime.txt`.
