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
function size(value) { return value ? {width:value.width,height:value.height} : null; }
function snapshot(window) {
    return {id:norm(window.internalId),pid:window.pid,title:window.caption,geometry:rect(window.frameGeometry),
        minSize:size(window.minSize),maxSize:size(window.maxSize),
        tile:window.tile ? {geometry:rect(window.tile.absoluteGeometry),padding:window.tile.padding} : null,
        desktopIds:Array.from(window.desktops).map(desktop=>desktop.id),minimized:window.minimized,
        maximizeMode:Number(window.maximizeMode),
        output:window.output ? window.output.name : "",movable:window.moveable,resizable:window.resizeable,
        transient:window.transient,modal:window.modal,
        transientFor:window.transientFor ? norm(window.transientFor.internalId) : null,
        active:workspace.activeWindow===window,stackingOrder:Number(window.stackingOrder),
        desktopFileName:applicationToken(window,"desktopFileName"),
        resourceClass:applicationToken(window,"resourceClass")};
}
function resolve(record) {
    const identifier = String(record.windowIds[0]);
    const all = workspace.windowList();
    let window = null;
    const x11=/^\d+$/.test(identifier);
    if (x11 && typeof workspace.getClient === "function")
        window = workspace.getClient(Number(identifier));
    else window = all.find(candidate=>norm(candidate.internalId)===norm(identifier));
    if (!window || !all.includes(window) || window.deleted)
        throw new Error("Uma janela selecionada não está mais disponível; atualize a seleção antes de tentar novamente.");
    const kwinPid=Number(window.pid);
    const authenticatedLegacyX11=x11 && kwinPid===0 && record.x11PidAuthenticated===true;
    if (kwinPid!==record.pid && !authenticatedLegacyX11)
        throw new Error("A identidade de processo de uma janela selecionada mudou; atualize a seleção antes de tentar novamente.");
    if (window.specialWindow || (!window.normalWindow && !window.dialog))
        throw new Error("This window type is not an application layout target");
    return window;
}
function onDesktop(window, desktop) { return window.desktops.some(value=>value.id===desktop.id); }
function applicationToken(window, property) {
    return String(window[property] || "").trim().toLowerCase();
}
function sameApplication(left, right) {
    const leftPid=Number(left.pid), rightPid=Number(right.pid);
    if (leftPid>0 && rightPid>0 && leftPid===rightPid) return true;
    // X11 group transients do not always expose transientFor. Keep the safety
    // barrier when KWin still identifies the same application, without making
    // one unrelated application's dialog disable organization desktop-wide.
    return ["desktopFileName","resourceClass"].some(property=>{
        const leftToken=applicationToken(left,property);
        return leftToken && leftToken===applicationToken(right,property);
    });
}
function hasApplicationIdentity(window) {
    return Number(window.pid)>0 || applicationToken(window,"desktopFileName")
        || applicationToken(window,"resourceClass");
}
function requireIndependentTargets(windows) {
    const all=workspace.windowList().filter(window=>!window.deleted);
    // KWin propagates desktop/output changes to transient descendants and modal
    // parents. Its scripting API does not expose mainWindows()/transients(), so
    // do not promise an isolated batch for these related windows.
    for (const window of windows) {
        if (window.transient || window.modal || window.transientFor
                || all.some(candidate=>candidate.transientFor===window))
            throw new Error("A organização em lote está indisponível porque \""+window.caption
                +"\" tem uma janela relacionada; o KWin também poderia alterar uma janela não selecionada.");
    }
    // X11 group transients can have several parents without a transientFor.
    // Only ambiguity that intersects the selected applications is relevant;
    // an unrelated VPN/file-dialog must not disable every Iconbox batch.
    const unresolved=all.find(candidate=>(candidate.normalWindow || candidate.dialog)
            && candidate.transient && !candidate.transientFor
            && (!hasApplicationIdentity(candidate)
                || windows.some(window=>candidate===window || sameApplication(candidate,window))));
    if (unresolved)
        throw new Error("A organização em lote está indisponível porque \""+unresolved.caption
            +"\" ainda tem uma relação de janela pai não resolvida.");
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
function sizeCompatibility(window,cell) {
    const minimum=window.minSize || {width:0,height:0};
    const maximum=window.maxSize || {width:Number.MAX_SAFE_INTEGER,height:Number.MAX_SAFE_INTEGER};
    if (cell.width+1<Number(minimum.width || 0) || cell.height+1<Number(minimum.height || 0))
        return {fits:false,kind:"minimum",size:minimum};
    if ((Number(maximum.width || 0)>0 && cell.width-1>Number(maximum.width))
            || (Number(maximum.height || 0)>0 && cell.height-1>Number(maximum.height)))
        return {fits:false,kind:"maximum",size:maximum};
    return {fits:true,kind:"",size:null};
}
function geometryText(value) {
    return Math.round(value.width)+"x"+Math.round(value.height)+" em "
        +Math.round(value.x)+","+Math.round(value.y);
}
try {
    if (request.action==="inspect") {
        send({ok:true,outcome:"observed",windows:workspace.windowList().map(snapshot),
            currentDesktop:{id:workspace.currentDesktop.id,x11Number:workspace.currentDesktop.x11DesktopNumber},
            output:workspace.activeScreen ? workspace.activeScreen.name : ""});
    } else if (request.action==="preflight") {
        // Selection guidance is read-only and deliberately reports an
        // unavailable result as data. It must never open a failure dialog or
        // mutate a client merely because the user checked a box.
        try {
            const windows=request.windows.map(resolve);
            let available=true, geometryAvailable=true, detail="";
            try { requireIndependentTargets(windows); }
            catch (error) { available=false;geometryAvailable=false;detail=String(error.message || error); }
            const tiled=windows.find(window=>window.tile);
            if (tiled && available) {
                geometryAvailable=false;
                detail="\""+tiled.caption+"\" está vinculada ao mosaico do KWin. Retire-a do tiling antes de usar colunas, linhas ou mosaico; nenhuma geometria foi solicitada.";
            }
            const immovable=windows.find(window=>!window.moveable);
            if (immovable && available && geometryAvailable) {
                geometryAvailable=false;
                detail="\""+immovable.caption+"\" não aceita movimento; colunas, linhas e mosaico ficam indisponíveis. Outras ações de estado continuam disponíveis.";
            }
            const fixed=windows.find(window=>!window.resizeable);
            if (fixed && available && geometryAvailable) {
                geometryAvailable=false;
                detail="\""+fixed.caption+"\" não aceita redimensionamento; colunas, linhas e mosaico ficam indisponíveis. Outras ações de estado continuam disponíveis.";
            }
            send({ok:true,outcome:"preflight",available:available,
                geometryAvailable:geometryAvailable,detail:detail,
                windows:windows.map((window,index)=>Object.assign(snapshot(window),
                    {key:String(request.windows[index].key || "")}))});
        } catch (error) {
            send({ok:true,outcome:"preflight",available:false,geometryAvailable:false,
                detail:String(error.message || error),windows:[]});
        }
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
        } else if (request.action==="restore") {
            if (windows.length<2) throw new Error("Select at least two windows to restore");
            requireIndependentTargets(windows);
            const issued=windows.map(()=>false);
            const raised=windows.map(()=>false);
            const activeTarget=windows[windows.length-1];
            let frontIssued=false;
            let checking=false;
            const observed=()=>windows.map((window,index)=>({id:norm(window.internalId),pid:window.pid,
                title:window.caption,actual:rect(window.frameGeometry),issued:issued[index],
                raised:raised[index],active:workspace.activeWindow===window,
                stackingOrder:Number(window.stackingOrder),
                minimized:window.minimized,maximizeMode:Number(window.maximizeMode),
                desktopIds:Array.from(window.desktops).map(value=>value.id),
                output:window.output ? window.output.name : ""}));
            const normalStateMatches=()=>windows.every((window,index)=>issued[index]
                && !window.minimized && Number(window.maximizeMode)===0);
            const sharesDesktop=(left,right)=>left.desktops.some(leftDesktop=>
                right.desktops.some(rightDesktop=>rightDesktop.id===leftDesktop.id));
            const frontMatches=()=>{
                if (!frontIssued || !raised.every(Boolean) || workspace.activeWindow!==activeTarget)
                    return false;
                const stack=Array.from(workspace.stackingOrder || []);
                if (!stack.length) return true;
                return windows.every(window=>{
                    const index=stack.indexOf(window);
                    if (index<0) return false;
                    return !stack.slice(index+1).some(candidate=>!windows.includes(candidate)
                        && !candidate.deleted && (candidate.normalWindow || candidate.dialog)
                        && !candidate.specialWindow && !candidate.keepAbove && !candidate.fullScreen
                        && candidate.output===window.output && sharesDesktop(candidate,window));
                });
            };
            const bringForward=()=>{
                // Restore every selected client before changing the stacking
                // order. Each identity is raised once; activating the last
                // selected client leaves one deterministic window on top.
                frontIssued=true;
                for (let index=0; index<windows.length; ++index) {
                    workspace.raiseWindow(windows[index]);
                    raised[index]=true;
                }
                workspace.activeWindow=activeTarget;
            };
            const check=()=>{
                if (complete || checking) return;
                checking=true;
                try {
                    const all=workspace.windowList();
                    if (windows.some(window=>!all.includes(window) || window.deleted)) {
                        send({ok:false,outcome:"partial-request",action:"restore",
                            detail:"A selected window closed while its normal state was being restored"});
                        return;
                    }
                    if (normalStateMatches() && !frontIssued) bringForward();
                    if (normalStateMatches() && frontMatches())
                        send({ok:true,outcome:"confirmed",action:"restore",windows:observed(),
                            activeWindow:norm(activeTarget.internalId),
                            detail:"KWin confirms that the selected windows are restored and brought to the front"});
                } catch (error) {
                    send({ok:false,outcome:"partial-request",action:"restore",
                        windows:observed(),detail:String(error.message || error)});
                } finally { checking=false; }
            };
            // Subscribe before issuing the one-shot state requests. Restoring a
            // maximized client is asynchronous, and no timeout may repeat it.
            for (const window of windows) {
                window.frameGeometryChanged.connect(check);
                window.outputChanged.connect(check); window.desktopsChanged.connect(check);
                window.minimizedChanged.connect(check); window.maximizedChanged.connect(check);
                window.stackingOrderChanged.connect(check);
            }
            workspace.windowActivated.connect(check);
            for (let index=0; index<windows.length; ++index) {
                const window=windows[index];
                issued[index]=true;
                if (window.minimized) window.minimized=false;
                if (Number(window.maximizeMode)!==0) window.setMaximize(false,false);
            }
            check();
            if (!complete) {
                const deadline=new QTimer();
                deadline.singleShot=true; deadline.interval=5000;
                deadline.timeout.connect(()=>{
                    const rows=observed();
                    const failed=rows.filter(row=>!row.issued || row.minimized || row.maximizeMode!==0);
                    const first=failed[0];
                    let detail=normalStateMatches()
                        ? "As janelas foram restauradas, mas o KWin não confirmou todo o conjunto à frente com a última seleção ativa. Nenhum pedido foi repetido."
                        : "O estado normal solicitado não foi confirmado antes do prazo. Nenhum pedido foi repetido.";
                    if (first) detail="\""+first.title+"\" ainda apresenta "
                        +(first.minimized ? "estado minimizado" : "modo de maximização "+first.maximizeMode)
                        +". "+(failed.length>1 ? String(failed.length)+" janelas divergiram. " : "")
                        +"Nenhum pedido foi repetido.";
                    send({ok:false,outcome:"partial-request",action:"restore",windows:rows,detail:detail});
                });
                deadline.start();
            }
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
                if (geometryLayout && window.tile)
                    throw new Error("\""+window.caption+"\" está vinculada ao mosaico do KWin. Retire-a do tiling antes de organizar; nenhuma geometria foi solicitada.");
                if (request.mode==="maximize" && (!window.maximizable || window.fullScreen))
                    throw new Error("A selected window cannot be maximized in its current state");
                if (request.mode==="minimize" && !window.minimizable)
                    throw new Error("A selected window cannot be minimized");
                if (window.output!==output && !window.moveableAcrossScreens)
                    throw new Error("A selected window cannot move to the current monitor");
            }
            const cells=geometryLayout ? layoutRects(area,windows.length,request.mode) : [];
            if (geometryLayout) {
                const compatibility=windows.map((window,index)=>sizeCompatibility(window,cells[index]));
                const incompatible=compatibility.findIndex(result=>!result.fits);
                if (incompatible>=0) {
                    const window=windows[incompatible], limit=compatibility[incompatible];
                    throw new Error("A célula reservada para \""+window.caption+"\" mede "+geometryText(cells[incompatible])
                        +", mas o aplicativo declara "+(limit.kind==="maximum" ? "máximo" : "mínimo")+" de "
                        +Math.round(limit.size.width)+"x"+Math.round(limit.size.height)
                        +". Escolha outra disposição ou menos janelas; nenhuma geometria foi solicitada.");
                }
            }
            const issued=windows.map(()=>false);
            const geometryIssued=windows.map(()=>false);
            let checking=false;
            const observed=()=>windows.map((window,index)=>({id:norm(window.internalId),pid:window.pid,
                title:window.caption,requested:cells[index] || null,actual:rect(window.frameGeometry),
                minSize:size(window.minSize),maxSize:size(window.maxSize),geometryIssued:geometryIssued[index],
                minimized:window.minimized,maximizeMode:Number(window.maximizeMode),
                desktopIds:Array.from(window.desktops).map(value=>value.id),output:window.output ? window.output.name : ""}));
            const timeoutDetail=()=>{
                const rows=observed();
                const failed=rows.filter((row,index)=>{
                    const window=windows[index];
                    if (!issued[index] || !onDesktop(window,desktop) || window.output!==output) return true;
                    if (request.mode==="collect") return false;
                    if (request.mode==="minimize") return !row.minimized;
                    if (request.mode==="maximize") return row.minimized || row.maximizeMode!==3;
                    if (!geometryIssued[index] || row.minimized || row.maximizeMode!==0) return true;
                    const target=row.requested, actual=row.actual;
                    return Math.abs(actual.x-target.x)>1 || Math.abs(actual.y-target.y)>1
                        || Math.abs(actual.width-target.width)>1 || Math.abs(actual.height-target.height)>1;
                });
                if (!failed.length) return "O estado solicitado não foi confirmado antes do prazo. Nenhum pedido foi repetido.";
                const first=failed[0];
                let reason="solicitado "+(first.requested ? geometryText(first.requested) : request.mode)
                    +"; observado "+geometryText(first.actual);
                if (first.output!==output.name)
                    reason += "; saída solicitada "+output.name+", observada "+(first.output || "nenhuma");
                if (first.desktopIds.indexOf(desktop.id)<0)
                    reason += "; área de trabalho solicitada "+desktop.id+", observadas "+first.desktopIds.join(",");
                if (first.minimized) reason += "; a janela continua minimizada";
                if (!first.geometryIssued && geometryLayout)
                    reason += first.maximizeMode!==0 ? "; aguardando o modo de maximização "+first.maximizeMode+" ser removido"
                        : "; a geometria ainda não foi emitida";
                else if (first.maximizeMode!==0) reason += "; modo de maximização "+first.maximizeMode;
                if (first.minSize) reason += "; mínimo declarado "+Math.round(first.minSize.width)+"x"+Math.round(first.minSize.height);
                return "\""+first.title+"\" não confirmou a disposição solicitada ("+reason+"). "
                    +(failed.length>1 ? String(failed.length)+" janelas divergiram. " : "")+"Nenhum pedido foi repetido.";
            };
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
                // Restoring a maximized client is asynchronous. Wait for every
                // selected client before emitting any rectangle: one slow
                // restore must not leave its peers repositioned after a timeout.
                if (geometryLayout) {
                    const allReady=windows.every((window,index)=>issued[index] && onDesktop(window,desktop)
                        && window.output===output && !window.minimized && Number(window.maximizeMode)===0);
                    if (allReady) windows.forEach((window,index)=>{
                        if (!geometryIssued[index]) {
                            geometryIssued[index]=true;
                            window.frameGeometry=cells[index];
                        }
                    });
                }
                const matches=windows.every((window,index)=>{
                    const actual=window.frameGeometry, target=cells[index];
                    if (!issued[index] || !onDesktop(window,desktop) || window.output!==output) return false;
                    if (request.mode==="collect") return true;
                    if (request.mode==="minimize") return window.minimized;
                    if (request.mode==="maximize") return !window.minimized && Number(window.maximizeMode)===3;
                    return geometryIssued[index] && !window.minimized && Number(window.maximizeMode)===0
                        && Math.abs(actual.x-target.x)<=1 && Math.abs(actual.y-target.y)<=1
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
                    window.minimized=false;
                    if (Number(window.maximizeMode)!==0) window.setMaximize(false,false);
                }
                issued[index]=true;
            }
            check();
            if (!complete) {
                const deadline=new QTimer();
                deadline.singleShot=true; deadline.interval=5000;
                deadline.timeout.connect(()=>send({ok:false,outcome:"partial-request",mode:request.mode,
                    windows:observed(),detail:timeoutDetail()}));
                deadline.start();
            }
        }
    }
} catch (error) {
    send({ok:false,outcome:"unavailable",detail:String(error.message || error)});
}
