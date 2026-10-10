#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native panel reconstruction primitives; no session operation on import.

Append SCRIPT after classic_panel.SCRIPT in a KDE WorkspaceScripting request.
The caller owns authorization, per-user snapshots, journal and postconditions.
Existing panels/applets are never reused or modified by reconstruction.
"""
from __future__ import annotations

import json


SCRIPT = r'''
function layoutIsTray(type) {
    return isTray(type) || type === "org.irixclassic.domainos.panel";
}
function layoutWidgetSnapshot(widget) {
    var result = {id:widget.id,type:widget.type,config:configuration(widget),
        shortcut:widget.globalShortcut,background:widget.userBackgroundHints,geometry:widget.geometry};
    if (layoutIsTray(widget.type)) {
        var containment=inner(widget);
        result.tray={id:containment.id,config:configuration(containment,true),
            widgets:containment.widgets().filter(w=>w.id>0&&!removedIds.includes(w.id)).sort((a,b)=>a.id-b.id).map(layoutWidgetSnapshot)};
    }
    return result;
}
function layoutPanelSnapshot(panel) {
    var result=panelSnapshot(panel);
    result.widgets=result.widgets.map(saved=>layoutWidgetSnapshot(panel.widgetById(saved.id)));
    return result;
}
function layoutToken(panel) {
    var initial=panel.currentConfigGroup.slice();
    try {panel.currentConfigGroup=["General"];return String(panel.readConfig("DomainOSLayoutToken",""));}
    finally {panel.currentConfigGroup=initial;}
}
function layoutMarker(panel,token) {
    var initial=panel.currentConfigGroup.slice();
    try {panel.currentConfigGroup=["General"];panel.writeConfig("DomainOSLayoutToken",token);}
    finally {panel.currentConfigGroup=initial;}
}
function layoutValidateSnapshot(snapshot,token) {
    if (!snapshot || snapshot.type!=="org.kde.panel" || !snapshot.geometry || !snapshot.config || !Array.isArray(snapshot.widgets))
        throw new Error("Snapshot de painel nativo inválido.");
    if (typeof token!=="string" || !/^[a-f0-9]{32}$/.test(token))
        throw new Error("Marcador de reconstrução inválido.");
    var g=snapshot.geometry;
    if (!Number.isInteger(g.screen) || g.screen<0 || g.screen>=screenCount ||
        !["top","bottom","left","right"].includes(g.location) ||
        !["left","center","right"].includes(g.alignment) ||
        !["fill","fit","custom"].includes(g.lengthMode) ||
        !["none","autohide","dodgewindows","windowsgobelow"].includes(g.hiding) ||
        !["adaptive","opaque","translucent"].includes(g.opacity) ||
        !Number.isFinite(g.offset) || !Number.isFinite(g.height) || g.height<=0 ||
        !Number.isFinite(g.minimumLength) || g.minimumLength<=0 ||
        !Number.isFinite(g.maximumLength) || g.maximumLength<g.minimumLength)
        throw new Error("Geometria de reconstrução inválida.");
    var ids=[];
    function widget(spec) {
        if (!spec || !Number.isInteger(spec.id) || spec.id<=0 || ids.includes(spec.id) ||
            typeof spec.type!=="string" || !knownWidgetTypes.includes(spec.type) || !spec.config ||
            typeof spec.shortcut!=="string" || typeof spec.background!=="string")
            throw new Error("Widget do snapshot indisponível ou inválido.");
        ids.push(spec.id);
        if (layoutIsTray(spec.type)) {
            if (!spec.tray || !Number.isInteger(spec.tray.id) || !spec.tray.config || !Array.isArray(spec.tray.widgets))
                throw new Error("Snapshot da bandeja nativa inválido.");
            spec.tray.widgets.forEach(widget);
        }
    }
    snapshot.widgets.forEach(widget);
}
function layoutSetGeometry(panel,geometry) {
    panel.screen=geometry.screen;
    panel.location=geometry.location;
    panel.alignment=geometry.alignment;
    panel.offset=geometry.offset;
    panel.lengthMode=geometry.lengthMode;
    panel.minimumLength=geometry.minimumLength;
    panel.maximumLength=geometry.maximumLength;
    panel.height=geometry.height;
    panel.hiding=geometry.hiding;
    panel.floating=geometry.floating;
    panel.opacity=geometry.opacity;
    // length is an automatic content-size getter and may be transiently huge.
    // Mode and min/max bounds, above, are the durable configuration.
}
function layoutPopulateTray(replacement,saved) {
    if (!saved || !saved.config || !Array.isArray(saved.widgets))
        throw new Error("Snapshot da bandeja nativa inválido.");
    var containment=inner(replacement);
    if (containment.id===saved.id)
        throw new Error("A bandeja recriada não tem identidade independente.");
    function populate(parent,spec) {
        if (!spec || !knownWidgetTypes.includes(spec.type) || !spec.config ||
            typeof spec.shortcut!=="string" || typeof spec.background!=="string")
            throw new Error("Provedor da bandeja original indisponível ou inválido.");
        var child=parent.addWidget(spec.type);
        if (!child || child.id<=0 || child.type!==spec.type)
            throw new Error("Falha ao recriar "+spec.type);
        writeConfiguration(child,spec.config,layoutIsTray(spec.type));
        child.userBackgroundHints=spec.background;
        child.globalShortcut=spec.shortcut;
        if (layoutIsTray(spec.type))layoutPopulateTray(child,spec.tray);
    }
    // The caller owns a newly allocated replacement containment. Defaults in
    // this containment are disposable; the saved source is never touched.
    writeConfiguration(containment,saved.config,false);
    containment.widgets().slice().forEach(child=>{removedIds.push(child.id);child.remove();});
    saved.widgets.forEach(child=>populate(containment,child));
    return containment.id;
}
function createFromSnapshot(snapshot,token) {
    layoutValidateSnapshot(snapshot,token);
    if (panels().some(panel=>layoutToken(panel)===token))
        throw new Error("Já existe um painel com este marcador; recriação recusada.");
    var created=null;
    var identifiers={},trayIdentifiers={};
    function widget(parent,saved) {
        var replacement=parent.addWidget(saved.type);
        if (!replacement || replacement.id<=0 || replacement.type!==saved.type)
            throw new Error("Falha ao recriar "+saved.type);
        identifiers[saved.id]=replacement.id;
        writeConfiguration(replacement,saved.config,layoutIsTray(saved.type));
        replacement.userBackgroundHints=saved.background;
        replacement.globalShortcut=saved.shortcut;
        if (layoutIsTray(saved.type)) {
            var containment=inner(replacement);
            if (containment.id===saved.tray.id)
                throw new Error("A bandeja recriada não tem identidade independente.");
            trayIdentifiers[saved.tray.id]=containment.id;
            writeConfiguration(containment,saved.tray.config,false);
            // A fresh wrapper creates provider defaults. Remove only these
            // fresh instances, then reproduce each saved child's own settings.
            containment.widgets().slice().forEach(defaultWidget=>{
                removedIds.push(defaultWidget.id);defaultWidget.remove();
            });
            saved.tray.widgets.forEach(child=>widget(containment,child));
        }
        return replacement;
    }
    try {
        created=new Panel();
        layoutMarker(created,token);
        writeConfiguration(created,snapshot.config,false);
        // The saved General group can contain another reconstruction marker.
        // This newly created panel always belongs to this transaction's token.
        layoutMarker(created,token);
        layoutSetGeometry(created,snapshot.geometry);
        snapshot.widgets.forEach(saved=>widget(created,saved));
        var after=layoutPanelSnapshot(created);
        after.widgets=snapshot.widgets.map(saved=>after.widgets.find(current=>current.id===identifiers[saved.id]));
        if (after.widgets.some(current=>!current))throw new Error("Widget recriado ausente.");
        return {ok:true,panelId:created.id,panel:after,widgetIds:identifiers,trayIds:trayIdentifiers,token:token};
    } catch (error) {
        // This function never removes the source panel or an unrelated panel.
        // A partial replacement is its own marked, newly allocated containment.
        if (created && created.id>0 && layoutToken(created)===token)created.remove();
        throw error;
    }
}
function removePanelChecked(expected,token) {
    if (!expected || !Number.isInteger(expected.id) || expected.id<=0)
        throw new Error("Identidade do painel a remover inválida.");
    var target=panelById(expected.id);
    if (!target || !same(stablePanel(layoutPanelSnapshot(target)),stablePanel(expected)))
        throw new Error("O painel mudou após o snapshot; remoção recusada.");
    if (token!==undefined && (typeof token!=="string" || !/^[a-f0-9]{32}$/.test(token) || layoutToken(target)!==token))
        throw new Error("O marcador não corresponde ao painel a remover.");
    var captured=layoutPanelSnapshot(target);
    var id=target.id;
    target.remove();
    return {ok:true,removedPanelId:id,before:captured};
}
'''


def script(body: str) -> str:
    """Compose the audited original snapshot helpers and reconstruction APIs."""
    import classic_panel

    return classic_panel.SCRIPT + "\n" + SCRIPT + "\n" + body


def create_script(snapshot: dict, token: str) -> str:
    """Return JS only; the caller decides which own KDE bus may execute it."""
    return script("print(JSON.stringify(createFromSnapshot(" + json.dumps(snapshot, ensure_ascii=True)
                  + "," + json.dumps(token) + ")));\n")


def remove_script(snapshot: dict, token: str | None = None) -> str:
    arguments=json.dumps(snapshot,ensure_ascii=True)
    if token is not None:
        arguments+=","+json.dumps(token)
    return script("print(JSON.stringify(removePanelChecked("+arguments+")));\n")
