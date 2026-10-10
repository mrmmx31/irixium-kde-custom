// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library

// Preserve the measured Motif relief at the reference palette, and its
// relative light/shadow depth when KDE supplies another title-bar color.
function hsl(c) {
    var max=Math.max(c.r,c.g,c.b), min=Math.min(c.r,c.g,c.b);
    var delta=max-min, light=(max+min)/2, hue=0, saturation=0;
    if (delta > 0) {
        saturation=delta/(1-Math.abs(2*light-1));
        if (max === c.r) hue=((c.g-c.b)/delta)%6;
        else if (max === c.g) hue=(c.b-c.r)/delta+2;
        else hue=(c.r-c.g)/delta+4;
        hue=((hue/6)%1+1)%1;
    }
    return {h:hue,s:saturation,l:light};
}
function tone(base, original, target) {
    if (base.toString() === original.toString()) return target;
    var a=hsl(base), b=hsl(original), c=hsl(target);
    var light=c.l >= b.l
        ? a.l+(1-a.l)*(c.l-b.l)/(1-b.l) : a.l*c.l/b.l;
    var saturation=b.s > 0 ? Math.min(1,a.s*c.s/b.s) : a.s;
    return Qt.hsla(((a.h+c.h-b.h)%1+1)%1,saturation,
        Math.max(0,Math.min(1,light)),1);
}
