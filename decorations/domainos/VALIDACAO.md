# Validação — DomainOS SR10.4, 2026-10-09

Pacote `0.1.0`, com Nimbus Sans bold de 12 px, testado a partir dos arquivos
reais do pacote. Os hashes registrados nos relatórios finais correspondem ao
`MANIFEST.json`. A comparação usa apenas a captura fornecida de SR10.4.

| Verificação | Resultado | Evidência local |
| --- | --- | --- |
| Entrada Qt, gesto, relevo e redimensionamento | 68/68 | `/tmp/domainos-sr104-input-render-r4/RESULTADO.json` |
| Moldura e botões: 12 regiões, 36.427 pixels | Zero diferenças | `/tmp/domainos-sr104-input-render-r4/REFERENCE-PIXELS.json` |
| KWin isolado, com janelas próprias | 30/30 | `/tmp/domainos-sr104-native-actions-r5/RESULTADO.json` |
| Prévia real de KDecoration3 | 9/9 | `/tmp/domainos-sr104-native-preview-r3/RESULTADO.json` |
| Instalação, repetição e restauração isoladas | 24/24 | `/tmp/irix-domainos-decoration-entrega-r3/RESULTADO.json` |
| Inventário completo da suíte | 31 componentes; nenhuma falha | `tools/audit_suite.py` |
| Instalação da opção no lsi | 4/4 | `/tmp/domainos-decoration-installed-lsi-r2/RESULTADO.json` |

O teste de opacidade compõe a moldura sobre dois fundos diferentes: a moldura
mantém os mesmos pixels e a área do cliente conserva o fundo. Não usamos o
alpha de `grabWindow()` como prova, pois o backend software retorna RGB32.

No KWin privado, os botões afundam antes da ação, minimizar/maximizar atuam na
soltura, arrastar para fora cancela e o duplo clique fecha tanto a janela ativa
como a originalmente inativa. O redimensionamento pela borda e o movimento
pelo título funcionam. Não sobra menu atrasado depois do duplo clique.

O título e o conteúdo do aplicativo ficam fora da comparação estrita de
pixels. Com Nimbus Sans 12, a tinta de “Help Index” mede 59 × 11 px; no print,
59 × 12 px, com deslocamento de um pixel. A fonte é uma aproximação livre,
explicitada em `ORIGEM.json`, e não uma identificação exata da fonte do print.

Os testes preservaram as configurações pessoais verificadas, o pacote IRIX
Classic e a captura original. A instalação real acrescentou somente a opção
no perfil lsi. `kpackagetool6 --type KWin/Decoration --list` confirmou
`domainos_sr104`; a seleção atual e o painel não foram alterados.

Print comparativo final:
`/tmp/domainos-sr104-native-preview-r3/reference-native-comparison.png`.
Janelas reais do KWin isolado:
`/tmp/domainos-sr104-native-actions-r5/native-active-inactive.png`.

As rodadas anteriores continuam em `/tmp`. As falhas iniciais eram do teste:
socket X11 bloqueado pelo sandbox, interpretação do alpha de RGB32 e
`xdotool mousemove --sync` sem deslocamento. Os relatórios finais usam o
harness corrigido e repetem os testes contra o pacote final.
