# Validação — Irixium divisórias v2

## Executado

**39 testes passaram** na execução registrada em `tests/resultado-v2.txt`.
Nenhum teste foi ignorado nessa execução. Não foi feita nenhuma instalação no
KDE de um usuário ou alteração no repositório GitHub.

Os testes de instalação usam arquivos temporários e substituem a cópia com
privilégios administrativos por uma cópia local. Cobrem reconhecimento da v1,
atualização v1 → v2, preservação de configurações, idempotência, backup, restauração
exata para v1 e encadeamento de restauração para o estado anterior à v1.
Também mantêm as verificações de recusa de bases desconhecidas, cancelamento de
autorização simulado, cópia parcial, integridade de backup e alterações posteriores.

## Regressões reproduzidas

O teste `test_v1_skips_propertyless_maximize_v2_includes_it` avalia as expressões
JavaScript **extraídas dos arquivos QML entregues**, em Node.js, com um objeto
visível de maximizar/restaurar sem `buttonType`. A expressão da v1 resulta em
falso e a expressão da v2 resulta em verdadeiro.

O teste `test_normal_six_pixel_border_reproduces_v1_failure` avalia a condição
original dos cantos com bordas efetivas de 6. Na v1, o resultado é falso. Na v2,
a condição é verdadeira e são calculados os oito cortes, usando cada borda real.

Outros testes avaliam diretamente as expressões dos tamanhos e das coordenadas
na v2, com bordas de 0, 2, 4, 6, 7 e 12, incluindo valores assimétricos. Verificam
que os cortes não ultrapassam a faixa disponível e que a ausência de uma borda
não esconde os cortes das outras. Também cobrem botão de ajuda invisível,
espaçadores, botão desabilitado visível, janela maximizada e janela muito pequena.

## Preservação do código original

Ao remover o bloco entre `IRIXIUM_DIVISORIAS_BEGIN v2` e `IRIXIUM_DIVISORIAS_END`,
o QML coincide com a base original incluída, admitindo somente diferenças de
espaços e linhas em branco. A criação dos botões, a ordem, o Row e as expressões
das margens não foram alterados. O novo bloco não possui capturadores de entrada.

A v2 só troca o QML por padrão; cores no rc só mudam com `--titulo-preto`.
Também foram executados `py_compile`, `sh -n` e conferência do diff com `patch`.

## Não executado e limitações

**Não foram executados Qt 6/Qt Quick/KWin neste ambiente.** Não houve compilação
QML via qmllint nem renderização real pelo compositor. Node.js verifica as
expressões JavaScript, mas não os bindings, os modelos Repeater, o posicionamento
Row, o recorte de composição ou os eventos de entrada do Qt Quick.

Os screenshots recebidos permitem observar o resultado da v1, não confirmar
visualmente a v2. Escala fracionária, X11/Wayland e o encaixe final com os SVGs
continuam dependendo da aplicação e verificação na sessão KDE do usuário.

## Repetir testes

Na pasta do pacote, para testes Python e expressões JS:

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile irixium_install.py
sh -n instalar-divisorias.sh
sh -n restaurar-divisorias.sh
```

Node.js é usado apenas pelos testes de expressões; sem ele, esses testes são
explicitamente ignorados. O instalador e a restauração não dependem de Node.js.
