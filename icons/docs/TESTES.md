# Validação executada — 0.1.0

## Resultados obtidos neste ambiente

- **25 testes automatizados passaram**, sem testes ignorados nesta execução. O log está em `testes-unitarios.txt`.
- Auditoria do tema pronto: **2.628 entradas de imagem**, sendo **2.336 PNGs e 292 SVGs**, **zero erros, zero avisos, zero links simbólicos**.
- Todos os PNGs foram também decodificados com Pillow. Nenhum estava vazio e todos tinham fundo com transparência.
- Foram conferidas as dimensões físicas dos PNGs de acordo com o `index.theme`, a integridade por CRC, a estrutura dos SVGs e a ausência de dependências externas proibidas pelo verificador.
- Todos os aliases foram comparados byte a byte com os respectivos arquivos-base em todos os tamanhos.
- Foram feitas **1.008 renderizações vetoriais adicionais** com CairoSVG 2.8.2: 126 ícones-base × oito dimensões — 20, 28, 36, 56, 72, 160, 256 e 512 px. Isso verifica capacidade de renderização e transparência; não equivale a simular escalas do compositor.
- `gtk-update-icon-cache` criou o cache e o validou com sucesso. O cache transitório foi removido antes da distribuição. **Esse é um teste GTK, não um teste KDE.**
- A fixture do índice Irixium corresponde ao blob Git `b4ad6335a7fa38dc8d832838aced0635ebf2ac78`. `git apply --check` e a aplicação em uma cópia temporária passaram.
- As prévias foram renderizadas e inspecionadas visualmente, incluindo dimensões nativas sobre fundos claro e escuro.

Os relatórios de máquina são `validacao-tema.json` e `validacao-renderizacao.json`.

## Comportamentos de segurança/regressão testados

Auditoria sem mudança nos arquivos de origem; recusa de destino existente; recusa de sobreposição de origem e destino; preservação de bytes de arte válida; transporte de aliases internos como arquivos reais; omissão registrada de links externos/quebrados; identificação de PNG em formato errado; tratamento distinto de folhas de animação; normalização apenas quando solicitada; instalação sem modificar configuração do tema ativo; recusa de instalação de tema com erros.

Os testes de correção de imagens/links usam **fixtures sintéticas**, não uma alegada coleção completa de defeitos confirmados no Irixium do usuário.

## Não testado aqui

Não houve sessão de Plasma, Dolphin, Konsole, Wayland ou Qt disponível para teste de integração. Não foram medidos resultado na bandeja, geometria de applets, desempenho no seu computador, escala fracionária real ou cache do KIconLoader. Uma tentativa de disponibilizar bindings Qt não foi concluída; nenhum teste Qt é declarado como executado.

O auditor é uma ferramenta específica para estrutura de temas, não uma análise formal de segurança de todo SVG possível. Comportamentos de carregadores, arquivos XPM legados e defeitos visuais de padding requerem inspeção complementar. O gerador desta versão só produz PNG e SVG simples.

## Matriz sugerida no KDE do usuário

| Área | Teste | O que observar |
|---|---|---|
| Dolphin | Pastas em ícones, lista e detalhes | Tamanho aparente uniforme e ausência de recorte |
| Dolphin | Alternar 16/22/24/32/48/64/96/128 | Troca de detalhes pequena/grande sem sumiço |
| Dolphin | Desligar prévias temporariamente | Separar miniaturas reais de ícones do tema |
| Dolphin | Lixeira vazia e cheia | Estados visualmente diferentes |
| Konsole/Kate | Menu, abas e barra de ferramentas | Ações reconhecíveis e fallback correto |
| Menu de aplicativos | Abrir ícones KDE comuns | Verificar nomes usados pelos lançadores locais |
| Painel/bandeja | Áudio, clipboard e menu | Descobrir se o recurso vem do tema Plasma separado |
| Escala | Primeiro 100%; depois escalas usadas | Nitidez e diferenças de rasterização |
| Reversão | Selecionar Irixium/Breeze | Verificar que decoração e demais componentes permaneceram iguais |

Ao relatar um defeito, inclua a aplicação, a área, o tamanho pedido, a escala da tela, a versão do Plasma e uma captura. Prefira comparar a mesma aplicação com Irixium, Irixium-Fixed e IRIX Classic — SGI, mantendo o restante da sessão constante.
