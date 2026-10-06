# IrixClassic 0.7.1 — código-fonte e instalador de usuário

Esta distribuição corresponde ao tema estável IrixClassic 0.7.1, GPL-3.0-or-later.
Contém os geradores da arte, configuração, procedência, registro da promoção,
ferramentas de pacote e instalador com restauração. Não inclui fontes binárias,
plugin Kvantum, GTK, decoração externa ou o reparo de sistema Qt Quick.

Na raiz desta pasta, como usuário normal:

```sh
bash kvantum/instalar-classic.sh --verificar
bash kvantum/instalar-classic.sh
# Instalar sem trocar a seleção. Opcional: --ativar.
bash kvantum/restaurar-classic.sh
```

Para reproduzir o SVG e conferir pacotes, Python 3.10+ é suficiente:

```sh
python3 kvantum/tools/build_classic.py
python3 kvantum/tools/update_manifest.py
bash distribuicao/gerar-kvantum.sh --verificar
bash distribuicao/gerar-kvantum.sh --saida /caminho/novo/fora-desta-pasta
```

Não mude o código congelado da 0.7.1 e reutilize a mesma tag/artefato publicado.
O gerador detecta alterações funcionais em relação à candidata aceita. Uma
nova correção deve ter novo número de versão e registro de mudanças.

As galerias completas de desenvolvimento ficam no repositório. Os testes de
empacotamento presentes neste ZIP não substituem o aceite gráfico recebido.
Publicar requer um checkout Git com o commit remoto correspondente, acesso à
conta GitHub e execução explícita do script de publicação. Apenas gerar ou
instalar os pacotes não publica nada. Veja `distribuicao/PUBLICAR-ESTAVEL.md`.
