# Decorações Aurorae IRIX

Este diretório separa as duas decorações de janela usadas no projeto:

| Decoração | Localização | Tipo |
|---|---|---|
| **Irixium** | `aurorae/Irixium/` | Tema Aurorae moderno, baseado no pacote de Phob1an |
| **IRIX Classic** | `classic-rewrite-rc1/package/` | Decoração KWin independente, com QML próprio |

`Irixium` preserva os arquivos do tema Aurorae original: SVGs da moldura e
botões, `Irixiumrc`, metadados e licença. `IRIX Classic` não é uma variante
do diretório Aurorae: possui outro identificador (`irixium_irix_classic_v4`),
estrutura KPackage própria e uma implementação QML independente.

As duas decorações podem coexistir no perfil do usuário. O instalador do
Classic coloca seus arquivos em `~/.local/share/kwin/decorations/` e não
altera `/usr/share` nem `/usr/lib`. O tema Aurorae moderno pode ser instalado
em `~/.local/share/aurorae/themes/Irixium/`.

O arquivo `applications.png` é um recurso adicional versionado pelo projeto
para a variante moderna; ele não é instalado por hooks globais do KWin.
