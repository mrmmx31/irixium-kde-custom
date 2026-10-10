// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "Artwork.js" as Artwork

QtObject {
    id: colors
    // Reference mode is only for comparison with the approved prototype.
    property bool followSystem: true
    // Retain the injectable role object used by isolated tests; the default is
    // the native KDE scheme, independent of application-style palette overrides.
    property QtObject system: DomainOSKDEPalette {}
    readonly property color background: followSystem ? system.window : "#7894a7"
    readonly property color recessed: followSystem ? system.base : "#607f91"
    readonly property color text: followSystem ? system.windowText : "#102b37"
    readonly property color black: followSystem ? system.buttonText : "#07141b"
    readonly property color blue: followSystem ? system.highlight : "#3297c7"
    readonly property color white: followSystem ? system.highlightedText : "#ffffff"
    // The live Window role is the native primary ColorSet 3. The approved
    // prototype's steel background remains an artwork substitution key only;
    // using it as the live saturation anchor distorted CoralReef's blue/cyan.
    readonly property color nativePrimary: "#78a0d5"
    readonly property color dark: tone(background, nativePrimary, "#194b63")
    readonly property color shadow: tone(background, nativePrimary, "#3e536e")
    readonly property color highlight: tone(background, nativePrimary, "#c5e8e6")
    readonly property color pale: tone(background, nativePrimary, "#a3d0e6")
    readonly property color metalLight: tone(background, nativePrimary, "#c4d5ed")
    readonly property color metalDark: shadow
    readonly property color cyan: tone(background, nativePrimary, "#7acac5")
    readonly property color cyanShadow: tone(background, nativePrimary, "#406b68")
    readonly property color label: tone(background, nativePrimary, "#a2c0ce")
    readonly property color lens: tone(blue, "#3297c7", "#78a0d5")
    readonly property color focus: followSystem ? system.highlight : "#dddd28"
    // Preserve the approved yellow; protect it when a yellow scheme hides it.
    // Both states depend only on the palette, never on pointer input.
    readonly property var pagerTones: pagerIndicatorTones()
    readonly property color pagerLight: pagerTones.light
    readonly property color pagerPressedLight: pagerTones.pressed
    readonly property bool pagerContrastProtected: pagerTones.protected
    // Activity has its own yellow role: it is not the Pager selection light.
    // Protect it only when the actual lens/metal surround has a yellow collision.
    readonly property bool activityContrastProtected: followSystem
        && (yellowCollision(lens) || yellowCollision(metalLight))
    readonly property color activityLight: activityContrastProtected
        ? activityYellowTone() : "#dddd28"
    // The sample LED is an accent, not a live device status indicator.
    readonly property color green: followSystem ? system.highlight : "#76a52b"
    readonly property color greenDark: tone(green, "#76a52b", "#314a14")
    readonly property var svgColors: ({
        "#7894a7": background.toString(), "#607f91": recessed.toString(),
        "#194b63": dark.toString(), "#3e536e": shadow.toString(),
        "#c5e8e6": highlight.toString(), "#a3d0e6": pale.toString(),
        "#3297c7": blue.toString(), "#ffffff": white.toString(),
        "#102b37": text.toString(), "#07141b": black.toString(),
        "#76a52b": green.toString(), "#314a14": greenDark.toString(),
        "#c4d5ed": metalLight.toString(), "#78a0d5": lens.toString()
    })
    // URLs depend only on palette roles, never on window size or pointer state.
    readonly property var assetUrls: Artwork.urls(svgColors)

    function luminance(color) {
        const channel = value => value <= 0.04045 ? value/12.92 : Math.pow((value+0.055)/1.055, 2.4)
        if (typeof color === "string") {
            return 0.2126*channel(parseInt(color.slice(1,3),16)/255)
                +0.7152*channel(parseInt(color.slice(3,5),16)/255)
                +0.0722*channel(parseInt(color.slice(5,7),16)/255)
        }
        return 0.2126*channel(color.r)+0.7152*channel(color.g)+0.0722*channel(color.b)
    }
    function contrast(first, second) {
        const a = luminance(first), b = luminance(second)
        return (Math.max(a,b)+0.05)/(Math.min(a,b)+0.05)
    }
    function yellowCollision(surface) {
        const value = hsl(surface)
        const distance = Math.abs(value.h-1/6)
        return value.s >= 0.2 && Math.min(distance,1-distance) <= 0.06
            && contrast("#dddd28",surface) < 3
    }
    function pagerYellowTone(preferred, minimum) {
        const original = hsl("#dddd28"), target = hsl(preferred)
        let best = preferred, bestDistance = Infinity, fallback = preferred, bestContrast = -1
        // A bounded search runs only when the KDE palette changes.
        for (let step = 1; step < 50; ++step) {
            const lightness = step/50
            const candidate = Qt.hsla(original.h,original.s,lightness,1)
            const score = Math.min(contrast(candidate,background),contrast(candidate,recessed))
            if (score > bestContrast) { bestContrast = score; fallback = candidate }
            if (score >= minimum && Math.abs(lightness-target.l) < bestDistance) {
                best = candidate; bestDistance = Math.abs(lightness-target.l)
            }
        }
        return bestDistance < Infinity ? best : fallback
    }
    function pagerIndicatorTones() {
        if (!followSystem || !(yellowCollision(background) || yellowCollision(recessed)))
            return {light:"#dddd28", pressed:Qt.lighter("#dddd28",1.25), protected:false}
        // Leave contrast headroom so the held lamp can brighten safely.
        const light = pagerYellowTone("#dddd28",4)
        const pressed = pagerYellowTone(Qt.lighter(light,1.25),3)
        return {light:light, pressed:pressed, protected:true}
    }
    function activityYellowTone() {
        const original = hsl("#dddd28")
        let best = "#dddd28", distance = Infinity, fallback = best, bestContrast = -1
        // Palette changes only; never hover, a frame tick or command timing.
        for (let step = 1; step < 50; ++step) {
            const candidate = Qt.hsla(original.h, original.s, step/50, 1)
            const score = Math.min(contrast(candidate,lens),contrast(candidate,metalLight))
            if (score > bestContrast) { bestContrast = score; fallback = candidate }
            if (score >= 3 && Math.abs(step/50-original.l) < distance) {
                best = candidate; distance = Math.abs(step/50-original.l)
            }
        }
        return distance < Infinity ? best : fallback
    }

    function hsl(color) {
        let r, g, b
        if (typeof color === "string") {
            r = parseInt(color.slice(1, 3), 16)/255
            g = parseInt(color.slice(3, 5), 16)/255
            b = parseInt(color.slice(5, 7), 16)/255
        } else {
            r = color.r; g = color.g; b = color.b
        }
        const max = Math.max(r,g,b), min = Math.min(r,g,b)
        const delta = max-min, light = (max+min)/2
        let hue = 0, saturation = 0
        if (delta > 0) {
            saturation = delta/(1-Math.abs(2*light-1))
            if (max === r) hue = ((g-b)/delta)%6
            else if (max === g) hue = (b-r)/delta+2
            else hue = (r-g)/delta+4
            hue = ((hue/6)%1+1)%1
        }
        return {h:hue, s:saturation, l:light}
    }
    function tone(base, referenceBase, referenceTone) {
        if (!followSystem || base.toString() === referenceBase)
            return referenceTone
        const current = hsl(base), original = hsl(referenceBase), target = hsl(referenceTone)
        // Keep the prototype's relative light/shadow depth even on dark schemes.
        const light = target.l >= original.l
            ? current.l+(1-current.l)*(target.l-original.l)/(1-original.l)
            : current.l*target.l/original.l
        const saturation = original.s > 0 ? Math.min(1,current.s*target.s/original.s) : current.s
        return Qt.hsla(((current.h+target.h-original.h)%1+1)%1, saturation, Math.max(0,Math.min(1,light)), 1)
    }
}
