// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
// request/resultService are JSON literals injected by the transient helper.
let complete = false;
function send(result) {
    if (complete) return;
    complete = true;
    callDBus(resultService, "/Result", "org.irixclassic.DomainOS.WindowOperation", "completed", JSON.stringify(result));
}
function norm(value) { return String(value).replace(/[{}]/g, "").toLowerCase(); }
function rect(value) { return {x:value.x,y:value.y,width:value.width,height:value.height}; }
function snapshot(window) {
    return {id:norm(window.internalId),pid:window.pid,title:window.caption,geometry:rect(window.frameGeometry),
        desktopIds:Array.from(window.desktops).map(desktop=>desktop.id),minimized:window.minimized,
        output:window.output ? window.output.name : "",movable:window.moveable,resizable:window.resizeable,
        transient:window.transient,modal:window.modal,
        transientFor:window.transientFor ? norm(window.transientFor.internalId) : null};
}
function resolve(record) {
    const identifier = String(record.windowIds[0]);
    const all = workspace.windowList();
    let window = null;
    if (/^\d+$/.test(identifier) && typeof workspace.getClient === "function")
        window = workspace.getClient(Number(identifier));
    else window = all.find(candidate=>norm(candidate.internalId)===norm(identifier));
    if (!window || !all.includes(window) || window.deleted || window.pid!==record.pid)
        throw new Error("A selected window disappeared or changed process identity");
    if (window.specialWindow || (!window.normalWindow && !window.dialog))
        throw new Error("This window type is not an application layout target");
    return window;
}
function onDesktop(window, desktop) { return window.desktops.some(value=>value.id===desktop.id); }
function requireIndependentTargets(windows) {
    const all=workspace.windowList().filter(window=>!window.deleted);
    // KWin propagates desktop/output changes to transient descendants and modal
    // parents. Its scripting API does not expose mainWindows()/transients(), so
    // do not promise an isolated batch for these related windows.
    for (const window of windows) {
        if (window.transient || window.modal || window.transientFor
                || all.some(candidate=>candidate.transientFor===window))
            throw new Error("Batch organization is unavailable for a window with related dialogs; KWin may also change an unselected window");
    }
    // X11 group transients can have several parents without a transientFor.
    // Without that relation we cannot prove that none belongs to this batch.
    if (all.some(window=>(window.normalWindow || window.dialog) && window.transient && !window.transientFor))
        throw new Error("Batch organization is unavailable while an application dialog has an unresolved parent relation");
}
function layoutRects(area, count, mode) {
    const columns = mode==="columns" ? count : mode==="rows" ? 1 : Math.ceil(Math.sqrt(count));
    const rows = Math.ceil(count/columns);
    const cells = [];
    for (let index=0; index<count; ++index) {
        const column=index%columns, row=Math.floor(index/columns);
        const left=Math.round(area.x+area.width*column/columns), right=Math.round(area.x+area.width*(column+1)/columns);
        const top=Math.round(area.y+area.height*row/rows), bottom=Math.round(area.y+area.height*(row+1)/rows);
        cells.push({x:left,y:top,width:right-left,height:bottom-top});
    }
    return cells;
}
try {
    if (request.action==="inspect") {
        send({ok:true,outcome:"observed",windows:workspace.windowList().map(snapshot),
            currentDesktop:{id:workspace.currentDesktop.id,x11Number:workspace.currentDesktop.x11DesktopNumber},
            output:workspace.activeScreen ? workspace.activeScreen.name : ""});
    } else {
        const windows=request.windows.map(resolve);
        if (request.action==="terminate-check") {
            const target=windows[0], selected=request.selectedKeys || [];
            const siblings=workspace.windowList().filter(window=>window.pid===target.pid && !window.deleted);
            const allowed=request.windows[0].windowIds.map(norm);
            for (const key of selected) {
                const id=String(key).replace(/^window:/,"");
                if (/^\d+$/.test(id) && typeof workspace.getClient==="function") {
                    const sibling=workspace.getClient(Number(id));
                    if (sibling && sibling.pid===target.pid) allowed.push(norm(sibling.internalId));
                } else allowed.push(norm(id));
            }
            if (siblings.some(window=>!allowed.includes(norm(window.internalId)) && window!==target))
                throw new Error("The process also owns an unselected window outside the current scope");
            send({ok:true,outcome:"identity-verified",pid:target.pid,x11:/^\d+$/.test(String(request.windows[0].windowIds[0]))});
        } else {
            if (windows.length<2 && request.mode!=="collect") throw new Error("Select at least two windows to organize");
            requireIndependentTargets(windows);
            const desktop=workspace.currentDesktop;
            if (norm(request.desktopId)!==norm(desktop.id) && Number(request.desktopId)!==desktop.x11DesktopNumber)
                throw new Error("The current desktop changed before the operation");
            const output=workspace.activeScreen;
            if (!output) throw new Error("The current monitor is unavailable");
            const area=workspace.clientArea(KWin.MaximizeArea,output,desktop);
            if (area.width<=0 || area.height<=0) throw new Error("The monitor work area is unavailable");
            const geometryLayout=["columns","rows","mosaic"].includes(request.mode);
            for (const window of windows) {
                if (geometryLayout && (!window.moveable || !window.resizeable || window.fullScreen))
                    throw new Error("A selected window does not accept movement/resizing in its current state");
                if (request.mode==="maximize" && (!window.maximizable || window.fullScreen))
                    throw new Error("A selected window cannot be maximized in its current state");
                if (request.mode==="minimize" && !window.minimizable)
                    throw new Error("A selected window cannot be minimized");
                if (window.output!==output && !window.moveableAcrossScreens)
                    throw new Error("A selected window cannot move to the current monitor");
            }
            const cells=geometryLayout ? layoutRects(area,windows.length,request.mode) : [];
            const issued=windows.map(()=>false);
            let checking=false;
            const observed=()=>windows.map((window,index)=>({id:norm(window.internalId),pid:window.pid,
                requested:cells[index] || null,actual:rect(window.frameGeometry),minimized:window.minimized,maximizeMode:Number(window.maximizeMode),
                desktopIds:Array.from(window.desktops).map(value=>value.id),output:window.output.name}));
            const check=()=>{
                if (complete || checking) return;
                checking=true;
                try {
                const all=workspace.windowList();
                if (windows.some(window=>!all.includes(window) || window.deleted)) {
                    send({ok:false,outcome:"partial-request",detail:"A selected window closed during organization"}); return;
                }
                // A hidden Wayland client can defer the output configure. Let
                // the move commit before hiding it; only native state changes
                // advance this operation, never a delay or a repeated request.
                if (request.mode==="minimize") {
                    windows.forEach((window,index)=>{
                        if (issued[index] && onDesktop(window,desktop) && window.output===output && !window.minimized)
                            window.minimized=true;
                    });
                }
                const matches=windows.every((window,index)=>{
                    const actual=window.frameGeometry, target=cells[index];
                    if (!issued[index] || !onDesktop(window,desktop) || window.output!==output) return false;
                    if (request.mode==="collect") return true;
                    if (request.mode==="minimize") return window.minimized;
                    if (request.mode==="maximize") return !window.minimized && Number(window.maximizeMode)===3;
                    return !window.minimized && Math.abs(actual.x-target.x)<=1 && Math.abs(actual.y-target.y)<=1
                        && Math.abs(actual.width-target.width)<=1 && Math.abs(actual.height-target.height)<=1;
                });
                if (matches) send({ok:true,outcome:"confirmed",mode:request.mode,output:output.name,desktopId:desktop.id,
                    area:rect(area),windows:observed(),detail:"KWin confirms the selected window organization"});
                } catch (error) {
                    send({ok:false,outcome:"partial-request",detail:String(error.message || error)});
                } finally { checking=false; }
            };
            // Subscribe before issuing requests; Wayland geometry commits are
            // asynchronous. No wait precedes the operation or its visual reply.
            for (const window of windows) {
                window.frameGeometryChanged.connect(check);
                window.outputChanged.connect(check); window.desktopsChanged.connect(check);
                window.minimizedChanged.connect(check); window.maximizedChanged.connect(check);
            }
            for (let index=0; index<windows.length; ++index) {
                const window=windows[index];
                window.desktops=[desktop];
                if (request.mode==="minimize" && window.output!==output && window.minimized)
                    window.minimized=false;
                workspace.sendClientToScreen(window,output);
                if (request.mode==="maximize") { window.minimized=false; window.setMaximize(true,true); }
                else if (geometryLayout) {
                    window.minimized=false; window.setMaximize(false,false); window.frameGeometry=cells[index];
                }
                issued[index]=true;
            }
            check();
            if (!complete) {
                const deadline=new QTimer();
                deadline.singleShot=true; deadline.interval=2500;
                deadline.timeout.connect(()=>send({ok:false,outcome:"partial-request",mode:request.mode,
                    windows:observed(),detail:"Geometry was requested; one or more clients did not confirm the requested size/position"}));
                deadline.start();
            }
        }
    }
} catch (error) {
    send({ok:false,outcome:"unavailable",detail:String(error.message || error)});
}
