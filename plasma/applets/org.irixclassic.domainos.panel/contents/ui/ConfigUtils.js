// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library

function copy(values) {
    const result = [];
    if (values) for (let i = 0; i < values.length; ++i) result.push(String(values[i]));
    return result;
}

function lines(text) {
    return String(text).split(/[\n,;]+/).map(value => value.trim()).filter(value => value.length > 0);
}

function unique(values) {
    return values.filter((value, index) => values.indexOf(value) === index);
}

function same(first, second) {
    return JSON.stringify(copy(first)) === JSON.stringify(copy(second));
}

function desktopId(value) {
    const normalized = String(value).trim().replace(/^applications:/, "");
    return /^[A-Za-z0-9_][A-Za-z0-9_.-]*\.desktop$/.test(normalized) ? normalized : "";
}

function desktopList(text) {
    const requested = lines(text);
    const normalized = requested.map(desktopId);
    return { valid: normalized.every(value => value.length > 0), values: unique(normalized), rejected: requested.filter((value, index) => !normalized[index]) };
}

function itemIds(text) {
    const requested = lines(text);
    return { valid: requested.every(value => /^[^\s\u0000-\u001f]+$/.test(value)), values: unique(requested) };
}

function move(values, index, delta) {
    const result = copy(values);
    const destination = index + delta;
    if (index < 0 || index >= result.length || destination < 0 || destination >= result.length) return result;
    const selected = result.splice(index, 1)[0];
    result.splice(destination, 0, selected);
    return result;
}

// KConfigPropertyMap exposes schema defaults beside the saved values as
// <key>Default. Resolve every requested value before touching local cfg_ edits;
// this never writes the map and leaves Plasma's Apply/Discard flow in charge.
function categoryDefaults(page, settings) {
    const result = {ok: false, keys: [], values: {}, missing: []};
    if (!page || !settings || typeof settings.keys !== "function") return result;
    const available = settings.keys();
    result.keys = available.filter(key => !key.endsWith("Default") && ("cfg_" + key) in page);
    for (const key of result.keys) {
        const defaultKey = key + "Default";
        if (available.indexOf(defaultKey) < 0 || settings[defaultKey] === undefined) {
            result.missing.push(key);
            continue;
        }
        // Lists belong to the edit buffer, never to the shared defaults map.
        result.values[key] = JSON.parse(JSON.stringify(settings[defaultKey]));
    }
    result.ok = result.keys.length > 0 && result.missing.length === 0;
    return result;
}

function resetCategory(page, settings) {
    const result = categoryDefaults(page, settings);
    if (result.ok) for (const key of result.keys) page["cfg_" + key] = result.values[key];
    return {ok: result.ok, keys: result.keys, missing: result.missing};
}
