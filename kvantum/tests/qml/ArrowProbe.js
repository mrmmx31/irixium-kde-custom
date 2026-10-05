// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library

// Measured on demand after polish, never cached at component construction.
function scan(length, cross, vertical, hitTest, target) {
    length = Math.min(4096, Math.floor(length));
    cross = Math.floor(cross);
    var first = -1, last = -1;
    for (var i = 0; i < length; ++i) {
        var hit = vertical ? hitTest(cross,i) : hitTest(i,cross);
        if (hit === target) { if (first < 0) first=i; last=i; }
        else if (first >= 0) break;
    }
    if (first < 0) return null;
    var middle=Math.floor((first+last)/2);
    return {x:vertical ? cross:middle, y:vertical ? middle:cross, first:first, last:last};
}
function inside(point,rect) {
    return point && rect && rect.width>0 && rect.height>0 &&
        point.x>=rect.x && point.x<rect.x+rect.width &&
        point.y>=rect.y && point.y<rect.y+rect.height;
}
function clearTarget(point, own, other) {
    return inside(point,own) && !inside(point,other);
}
function collect(item, out) {
    if (!item) return;
    if (item.elementType === "scrollbar" && typeof item.hitTest === "function") out.push(item);
    if (item.children) for (var i=0;i<item.children.length;++i) collect(item.children[i],out);
}
function choose(list) {
    if (!list.length) return null;
    for (var i=0;i<list.length;++i) {
        if (list[i].visible && list[i].opacity>0 && list[i].activeControl!=="none") return list[i];
    }
    return list[0];
}
