# Contornos dos cursores — 07/10/2026

A ampliação por vizinho mais próximo da base nominal 32 produzia blocos
irregulares em 48 e ampliava os degraus nos tamanhos maiores. Essa ampliação
permanece somente na alternativa `sgi`, para comparação com a recriação antiga.

## Correção

- `SGI-Classic`: seta original preservada byte a byte em 32; outros tamanhos
  renderizados novamente com bordas opacas, mantendo o aspecto de bitmap.
- `SGI-Irixium`: contornos renderizados com antialiasing em 24/32/48/64/96.
- Seta definida por polígonos contínuos ajustados à silhueta da referência;
  outros estados usam contornos simplificados extraídos da base. Os relógios
  são desenhados por primitivas diretamente na resolução de cada tamanho.
- Furos e regiões separadas são preservados. Pixels de baixa opacidade da
  base antiga são descartados antes da reconstrução dos contornos.
- Bordas suaves são codificadas com alpha premultiplicado para Xcursor.
  A visualização faz a conversão inversa para exibir corretamente sobre fundos
  claros e escuros. Fontes históricas e hashes continuam intactos.

Não se trata de extração dos cursores originais do IRIX. As variantes são
adaptações da recriação documentada em `cursors/README.md`.

## Verificação

Passaram 62 testes de integração e 10 testes de cursores. Os testes adicionais
conferem a seta Classic em 32 contra a fonte preservada, bordas opacas nos
outros tamanhos Classic, ausência da antiga ampliação e a codificação do alpha
de todos os pixels modernos. O carregador real libXcursor passou nas 525
consultas dos papéis, tamanhos e variantes, incluindo hotspots e animações.

A comparação foi gerada a partir dos binários finais por
`cursors/tools/preview.py`. Mostra cada cursor em 48 no tamanho real e numa
lupa de 2×, além das setas em todos os tamanhos sobre fundos claro e escuro.
Não é uma captura de aplicações pedindo os estados de ocupado.

As cópias locais são instaladas pelo instalador existente, com backups, em
`~/.local/share/icons` e `~/.icons`. A preferência de tamanho 48 é mantida.
Nenhum timer de aplicação ou serviço foi acrescentado.

A auditoria local com `--exigir-sons` terminou sem falhas; as três cópias em
`~/.icons` conferiram com o repositório. A ferramenta nativa selecionou
Irixium e voltou ao Classic para invalidar o cursor anterior em uso.
O estado final é `cursorTheme=SGI-Classic`, `cursorSize=48`. Backup da instalação:
`~/.local/state/irixium-suite/backups/9d242fe108d849738e8713ec0d47a0aa`.
