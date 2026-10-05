# Upstream sources

This repository intentionally keeps the GTK and KDE/Aurorae portions in
separate directories while distributing them together for convenience.

| Directory | Upstream | Maintainer/source |
| --- | --- | --- |
| `gtk/` | https://github.com/TheJollyDuck/Irixium | TheJollyDuck / Shauna Recto |
| KDE/Kvantum | https://www.opencode.net/phob1an/irixium | Theme author: Mark Whittaker |

Use `./check-upstreams.sh` to fetch and display new commits from the GTK
upstream. Do not overwrite local changes automatically; review upstream
changes and merge them deliberately. The preserved modern Kvantum source is
under `kvantum/Irixium/`; `kvantum/IrixClassic/` is reserved for the future
variant. The Aurorae decoration remains separately under `aurorae/Irixium/`.
