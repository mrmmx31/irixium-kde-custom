# Validação — controles v3

## Executado

**31 testes de Python passaram**, usando diretórios temporários, cópia administrativa simulada e SVG de teste. Cobrem alteração exclusiva das duas chaves, preservação de outras seções/CRLF, rejeição de configurações duplicadas/bloqueadas, pré-verificação sem escrita, instalação, idempotência, compatibilidade dos dois menus anteriores, símbolos/destinos desconhecidos, cancelamento administrativo, falha parcial de cópia e reversão, restauração, detecção de conflitos e preparação das alterações do checkout.

**14 testes de JavaScript passaram no Node.js**, executando os handlers extraídos do arquivo QML entregue com objetos simulados. Cobrem identificação do tema, hover, pressionamento, clique rápido, clique mantido, cancelamento, saída da área, abertura do menu para as configurações testadas e preservação da preferência existente de duplo clique nos temas Irixium e não Irixium.

A identidade das duas cópias de origem de `MenuButton.qml` foi conferida pelo cálculo de Git blob SHA-1 e comparação com os identificadores retornados pelo GitHub. O hash esperado do `close.svg` vem da mesma consulta; o instalador verifica esse hash no arquivo real do usuário antes de copiá-lo para `minimize.svg`.

Também executados: compilação sintática Python e `sh -n` nos wrappers.

Logs completos: `tests/resultado-python.txt` e `tests/resultado-javascript.txt`.

## Não executado

Não havia Qt 6/Qt Quick, Kirigami e KWin instalados neste ambiente. Não foi possível testar aqui a importação real dos componentes, a renderização, a sessão X11/Wayland, a abertura do menu nativo nem o comportamento do compositor com diferentes escalas.

Os testes **não comprovam** a aparência final ou que o pacote funciona em qualquer versão do Plasma. O código foi preparado sobre a personalização do repositório indicada em `ORIGEM.json`; o teste visual e funcional deve ser concluído na sessão do usuário. Este pacote é complementar e não revalida a implementação de divisórias da v2.

## Reproduzir

```bash
python3 -m unittest discover -s tests -v
node --test tests/test_menu.js
sh -n instalar-controles.sh
sh -n restaurar-controles.sh
```
