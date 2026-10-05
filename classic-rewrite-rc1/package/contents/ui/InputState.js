// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library
// A deterministic gesture state machine. No timers, popup polling or app names.
// MouseArea owns the grab. The native compositor owns the popup's lifecycle.
function idle() { return {button: 0, armed: false, inside: false, menuIssued: false}; }
function permits(kind, button, keys) {
    if (kind !== "menu" && kind !== "minimize" && kind !== "maximize") return false;
    return button === keys.left || (button === keys.right && kind !== "minimize")
        || (button === keys.middle && kind === "maximize");
}
function step(state, event, policy, keys) {
    var s = {button: state.button, armed: state.armed,
             inside: state.inside, menuIssued: state.menuIssued};
    var action = "", actionButton = event.button || 0;
    if (!policy.available || event.type === "cancel") return {state: idle(), action: "", button: 0};
    if (event.type === "press") {
        if (s.armed || !event.inside || !permits(policy.kind,event.button,keys))
            return {state:s, action:"", button:0};
        s = {button:event.button, armed:true, inside:true, menuIssued:false};
        if (policy.kind === "menu" && policy.menuOnPress) {
            s.menuIssued = true;
            action = "activate";
        }
    } else if (event.type === "move") {
        s.inside = !!event.inside;
    } else if (event.type === "release") {
        if (s.armed && s.button === event.button) {
            if (event.inside && permits(policy.kind,event.button,keys) && !s.menuIssued)
                action = "activate";
            s = idle();
        }
    } else if (event.type === "double") {
        // Only called for a menu double-click accepted by the Qt handler.
        s = idle();
        if (policy.kind === "menu" && policy.closeOnDouble && event.button === keys.left)
            action = "close";
    } else if (event.type === "accessible") {
        if (permits(policy.kind,keys.left,keys)) { action = "activate"; actionButton = keys.left; }
    }
    return {state:s, action:action, button:actionButton};
}
function depressed(state, available) { return !!(available && state.armed && state.inside); }
