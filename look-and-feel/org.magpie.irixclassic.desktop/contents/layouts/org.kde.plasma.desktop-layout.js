var panel = new Panel
var panelScreen = panel.screen
panel.height = 64
panel.location = "bottom";
const geo = screenGeometry(panelScreen);
panel.alignment = "center";
panel.minimumLength = geo.width * 3 /4
panel.maximumLength = geo.width * 3 /4
panel.lengthMode = "custom"
panel.floating = true

kickoff = panel.addWidget("org.irixclassic.applications")

const browserId = defaultApplication("browser", true)
const launcherUrls = []
if (browserId) {
    launcherUrls.push("applications:" + encodeURIComponent(browserId))
}
launcherUrls.push("applications:org.kde.dolphin.desktop",
                  "applications:org.kde.konsole.desktop")

const appsLaunch = panel.addWidget("org.irixclassic.quicklaunch")
appsLaunch.currentConfigGroup = ["General"]
appsLaunch.writeConfig("launcherUrls", launcherUrls)
appsLaunch.writeConfig("maxSectionCount", 1)

panel.addWidget("org.kde.plasma.panelspacer")

const tasks = panel.addWidget("org.irixclassic.iconbox")
tasks.currentConfigGroup = ["General"]
tasks.writeConfig("maxStripes", "1")
tasks.writeConfig("forceStripes", true)
tasks.writeConfig("launchers", "")
tasks.writeConfig("onlyGroupWhenFull", false)

panel.addWidget("org.kde.plasma.panelspacer")
panel.addWidget("org.kde.plasma.pager")

var langIds = ["as",    // Assamese
               "bn",    // Bengali
               "bo",    // Tibetan
               "brx",   // Bodo
               "doi",   // Dogri
               "gu",    // Gujarati
               "hi",    // Hindi
               "ja",    // Japanese
               "kn",    // Kannada
               "ko",    // Korean
               "kok",   // Konkani
               "ks",    // Kashmiri
               "lep",   // Lepcha
               "mai",   // Maithili
               "ml",    // Malayalam
               "mni",   // Manipuri
               "mr",    // Marathi
               "ne",    // Nepali
               "or",    // Odia
               "pa",    // Punjabi
               "sa",    // Sanskrit
               "sat",   // Santali
               "sd",    // Sindhi
               "si",    // Sinhala
               "ta",    // Tamil
               "te",    // Telugu
               "th",    // Thai
               "ur",    // Urdu
               "vi",    // Vietnamese
               "zh_CN", // Simplified Chinese
               "zh_TW"] // Traditional Chinese

if (langIds.indexOf(languageId) != -1) {
    panel.addWidget("org.kde.plasma.kimpanel");
}

panel.addWidget("org.kde.plasma.marginsseparator")
panel.addWidget("org.irixclassic.systemtray")
panel.addWidget("org.kde.plasma.marginsseparator")

var aclock = panel.addWidget("org.irixclassic.analogclock")
aclock.currentConfigGroup = ["General"]
aclock.writeConfig("showSecondHand", true)

// Initial placement only. Existing monitors keep the user's chosen position.
var desktop = desktopForScreen(panelScreen)
if (desktop && geo.width >= 312 && geo.height >= 252 &&
    !desktop.widgets().some(w => w.type === "org.irixclassic.grosview")) {
    desktop.addWidget("org.irixclassic.grosview", geo.width - 296, 16, 280, 220)
}
