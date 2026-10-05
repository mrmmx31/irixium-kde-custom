# Validação — IRIX Classic v4

## Realizado neste ambiente

1. **20 testes Python do instalador/restauração**, usando diretórios temporários
   e chamadas KDE simuladas: instalação sem ativação, ativação das duas chaves,
   restauração de chaves ausentes, preservação de chaves não relacionadas,
   preservação de outra seleção feita depois, backup de pasta anterior,
   recusa de remoção de edições locais, rejeição de links simbólicos,
   recusa de execução privilegiada, validação de recibos e reversão de uma
   falha simulada de ativação. Resultado: todos passaram.
2. **84 cenários do desenhista JavaScript**: janelas de diferentes dimensões,
   fatores inteiros 1/2/3, estado ativo/inativo, normal/maximizado, hover,
   pressionado e desabilitado. Verificadas coordenadas inteiras, retângulos
   válidos, limites de desenho e uso exclusivo da paleta prevista. Também foram
   verificados tamanhos dos símbolos e consistência da faixa de título.
3. **Comparação com as referências**: as próprias funções de `Painter.js` foram
   executadas em Node.js com um gravador de chamadas Context2D. Os retângulos
   resultantes foram rasterizados em Pillow sem interpolação. São testes de
   reconstrução das referências usadas para criar o desenho, não testes cegos
   com imagens independentes.

| Comparação | Pixels conferidos | Divergências |
|---|---:|---:|
| Moldura e símbolos da janela ativa de 591 × 540, referência 1 | 22.311 | 0 |
| Barra ativa de 628 × 32, referência 2 | 10.064 | 0 |

O texto dos títulos e o conteúdo dos aplicativos foram excluídos dessas
comparações. A transparência da área reservada ao conteúdo e a opacidade da
moldura foram verificadas. O resultado bruto está em
`validacao/comparacao-pixels.json`.

Foram realizadas também compilação sintática do Python, verificação sintática
dos wrappers shell e leitura da estrutura/identificação do pacote. Nenhum teste
executou ações no desktop do usuário. Nenhum arquivo de fonte foi incluído.

## Não realizado — importante

**Não houve execução do QML em Qt Quick nem carregamento real pelo KWin.**
Este ambiente não dispõe do runtime Qt 6/KWin. O Context2D gravador não verifica
resolução de imports QML, integração do compositor, rasterização da fonte ou
entrega real de eventos de ponteiro.

O código foi confrontado com a API dos exemplos do KDE Plasma/6.3, mas isso não
substitui testar a miniatura e a aplicação na instalação do usuário. A
verificação `--verificar` também não valida o runtime QML.

A correspondência dos pixels medida acima não é uma promessa de que a captura
final do KDE será idêntica: a escala física, o compositor, o rasterizador de
texto, a fonte disponível e estados não mostrados nas referências podem diferir.
A versão deve ser tratada como uma reconstrução de referência para teste visual,
não como uma release já homologada em uma sessão KDE real.

## Conferência na sessão

Antes de aplicar, confira a miniatura. Depois, use uma janela comum que permita
minimizar/maximizar e verifique: janela normal ativa e inativa; menu abrindo e
recuperando o relevo depois de fechar; minimizar sem fechar; maximizar/restaurar
sem salto vertical; redimensionamento e cantos; título comprido; aplicativo
com controles desabilitados; escala efetiva do monitor.

Se a miniatura não carregar, mantenha o tema anterior. Se necessário, use
`restaurar-v4.sh`. Não tente corrigir isso reiniciando à força o KWin.

## Reexecutar os testes de desenvolvimento

```sh
python3 -m unittest discover -s tests -v
node tests/test_painter.js
```

A instalação em si não exige Node.js, Pillow ou NumPy. Os testes são ferramentas
de desenvolvimento e não substituem o ensaio real com Qt/KWin.

Com os dois PNGs originais, a comparação pode ser repetida (Pillow necessário):

```sh
python3 tests/comparar_referencias.py --irix1 /caminho/irix-1280x1024.png --irix2 /caminho/irix-1024x768.png
```

O script recusa resoluções diferentes, pois as coordenadas das molduras se
referem exatamente às duas capturas fornecidas. Isso evita comparar miniaturas
ou imagens redimensionadas como se fossem os pixels originais.
