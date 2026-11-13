// SPDX-License-Identifier: GPL-3.0-or-later
// Initial layout only; the per-user bridge handles existing panels transactionally.
const existing = panels().filter(p => p.widgets().some(w => w.type === "org.irixclassic.domainos.panel"));
if (existing.length === 0) {
    const panel = new Panel;
    const geo = screenGeometry(panel.screen);
    panel.location = "bottom";
    panel.alignment = "center";
    panel.offset = 0;
    panel.height = 109;
    panel.lengthMode = "custom";
    panel.minimumLength = Math.min(971, geo.width);
    panel.maximumLength = Math.min(971, geo.width);
    panel.floating = true;
    panel.hiding = "none";
    panel.addWidget("org.irixclassic.domainos.panel");
}
