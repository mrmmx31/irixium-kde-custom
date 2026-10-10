// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library

// Selection owns window identities, never view rows or group identities.
function unique(keys) {
    const result = []
    for (const key of keys) if (key && result.indexOf(key) < 0) result.push(key)
    return result
}

function reconcile(keys, windows) {
    const available = windows.map(window => window.key)
    return unique(keys).filter(key => available.indexOf(key) >= 0)
}

function toggle(keys, key, checked) {
    const result = keys.filter(existing => existing !== key)
    if (checked) result.push(key)
    return unique(result)
}

function click(keys, anchor, order, key, control, shift) {
    if (shift && order.indexOf(anchor) >= 0 && order.indexOf(key) >= 0) {
        const first = order.indexOf(anchor), last = order.indexOf(key)
        const interval = order.slice(Math.min(first,last), Math.max(first,last)+1)
        return {keys: unique(control ? keys.concat(interval) : interval), anchor: anchor}
    }
    return {keys: control ? toggle(keys,key,keys.indexOf(key)<0) : [key], anchor: key}
}

function memberState(keys, members) {
    const count = members.filter(key => keys.indexOf(key) >= 0).length
    return {count: count, total: members.length, selected: count > 0,
            partial: count > 0 && count < members.length}
}

function minimizedOnly(mode, threshold, windowCount) {
    return mode === "minimized" || (mode === "automatic" && Number.isInteger(threshold)
            && threshold >= 0 && windowCount > threshold)
}
