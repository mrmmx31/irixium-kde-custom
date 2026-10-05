// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library
// Deterministic input state. The QML Timer only resolves an ambiguous menu click;
// it never prolongs the pressed artwork. Native popup lifecycle belongs to KWin.
function idle() {
    return {button:0, armed:false, inside:false, menuIssued:false,
            waiting:false, doubleEligible:false};
}
function permits(kind, button, keys) {
    if (kind !== "menu" && kind !== "minimize" && kind !== "maximize") return false;
    return button === keys.left || (button === keys.right && kind !== "minimize")
        || (button === keys.middle && kind === "maximize");
}
function canClose(state, policy, button, keys) {
    return !!(policy.available && policy.kind === "menu" && policy.closeOnDouble
        && button === keys.left && !state.menuIssued
        && (state.waiting || state.doubleEligible));
}
function step(state, event, policy, keys) {
    var s = {button:state.button, armed:state.armed, inside:state.inside,
             menuIssued:state.menuIssued, waiting:!!state.waiting,
             doubleEligible:!!state.doubleEligible};
    var action = "", actionButton = event.button || 0;
    if (!policy.available || event.type === "cancel")
        return {state:idle(), action:"", button:0};
    if (event.type === "press") {
        if (s.armed || !event.inside || !permits(policy.kind,event.button,keys))
            return {state:s, action:"", button:0};
        var eligible = s.waiting && policy.kind === "menu" && policy.closeOnDouble
            && event.button === keys.left;
        s = {button:event.button, armed:true, inside:true, menuIssued:false,
             waiting:false, doubleEligible:eligible};
        // Left menu press must NOT post a popup while a double-click is possible.
        // Merely changing menuOnPress to false is not enough: release is also deferred.
        if (policy.kind === "menu" && policy.menuOnPress
                && !(policy.closeOnDouble && event.button === keys.left)) {
            s.menuIssued = true;
            action = "activate";
        }
    } else if (event.type === "move") {
        if (s.waiting && !event.inside) s = idle();
        else s.inside = !!event.inside;
    } else if (event.type === "release") {
        if (s.armed && s.button === event.button) {
            var activate = event.inside && permits(policy.kind,event.button,keys) && !s.menuIssued;
            s = idle();
            if (activate) {
                if (policy.kind === "menu" && policy.closeOnDouble && event.button === keys.left) {
                    s.waiting = true; // no pressed artwork while waiting after release
                    s.inside = true;
                } else action = "activate";
            }
        }
    } else if (event.type === "double") {
        // Qt/KWin, not the action timer, supplies the native double-click event.
        if (event.inside && canClose(s,policy,event.button,keys)) {
            s = idle();
            action = "close";
        }
    } else if (event.type === "timeout") {
        if (s.waiting && policy.kind === "menu" && policy.closeOnDouble) {
            s = idle();
            action = "activate";
            actionButton = keys.left;
        }
    } else if (event.type === "hold") {
        if (policy.kind === "menu" && s.armed && s.inside && event.inside
                && s.button === keys.left && !s.menuIssued) {
            s = idle(); // native popup may cancel input synchronously
            action = "activate";
            actionButton = keys.left;
        }
    } else if (event.type === "accessible") {
        if (permits(policy.kind,keys.left,keys)) {
            s = idle(); action = "activate"; actionButton = keys.left;
        }
    }
    return {state:s, action:action, button:actionButton};
}
function depressed(state, available) { return !!(available && state.armed && state.inside); }
