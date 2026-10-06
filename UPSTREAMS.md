# Upstream sources

This repository intentionally keeps the GTK, KDE, Plasma, icon, cursor and
Aurorae portions in separate directories while distributing them together for
convenience.

| Directory | Upstream | Maintainer/source |
| --- | --- | --- |
| `gtk/` | https://github.com/TheJollyDuck/Irixium | TheJollyDuck / Shauna Recto |
| KDE/Kvantum | https://www.opencode.net/phob1an/irixium | Theme author: Mark Whittaker |
| `icons/Irixium/` | https://www.pling.com/p/2142965/ (package 2142965) | Irixium icon package; license not declared in the installed snapshot |
| `plasma/Irixium/` | https://www.pling.com/p/1457753/ (package 1457753) | Phob1an; GPL3 |
| `look-and-feel/org.magpie.irixium.desktop/` | https://www.pling.com/u/phob1an/ | Mark Whittaker; installed metadata declares conflicting GPL 3+ / GPL-2.0+ |
| `cursors/sgi/` | https://github.com/jujum4n/sgi-enhanced/tree/master/cursor/sgi | jujum4n and contributors; upstream README declares GPL without a version |

Use `./check-upstreams.sh` to fetch and display new commits from the GTK
upstream. Do not overwrite local changes automatically; review upstream
changes and merge them deliberately. The preserved modern Kvantum source is
under `kvantum/Irixium/`; `kvantum/IrixClassic/` is reserved for the future
variant. The Aurorae decoration remains separately under `aurorae/Irixium/`.

The KDE Store components are package snapshots rather than Git checkouts.
Their package pages and IDs are monitored for availability by the scheduled
workflow; changes must be reviewed manually. The active cursor selection is
`sgi`, as recorded in `cursors/sgi/ORIGEM.json`.
