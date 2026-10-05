# Upstream sources

This repository intentionally keeps the GTK and KDE/Aurorae portions in
separate directories while distributing them together for convenience.

| Directory | Upstream | Maintainer/source |
| --- | --- | --- |
| `gtk/` | https://github.com/TheJollyDuck/Irixium | TheJollyDuck / Shauna Recto |
| KDE/Aurorae | https://www.opencode.net/phob1an/irixium | Phob1an |

Use `./check-upstreams.sh` to fetch and display new commits from the GTK
upstream. Do not overwrite local changes automatically; review upstream
changes and merge them deliberately. The preserved Aurorae source snapshot is
under `upstream/aurorae-irixium/`; the customized installation remains under
`aurorae/Irixium/`.
