// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
DomainOSIconboxPreview {
    id:host
    function prepare(grouped) {
        resetUi();controller.groupingMode=grouped ? 1 : 0
        controller.onlyCurrentDesktop=false;controller.onlyCurrentActivity=false
        iconbox.wheelRotation=0;iconbox.firstVisible=0
    }
    function snapshot() {
        return JSON.stringify({rows:controller.taskRows,requests:requests,selected:controller.selectedKeys,
            firstVisible:iconbox.firstVisible,attention:controller.demandsAttention})
    }
    function setWheelActivation(value) {iconbox.iconboxWheelActivates=value}
    function seedNoActive() {for (const row of windows) mutate(row.ids[0],"active",false)}
    function setStatuses(key) {
        const button=iconbox.buttonForKey(key)
        button.smartLauncherItem=Qt.createQmlObject('import QtQuick; QtObject { property bool urgent:true;property bool progressVisible:true;property int progress:42;property bool countVisible:true;property int count:7 }',button)
        button.audioStreams=[audio1,audio2]
    }
    QtObject {id:audio1;property bool muted:false;property bool corked:false;function mute(){muted=true} function unmute(){muted=false}}
    QtObject {id:audio2;property bool muted:false;property bool corked:false;function mute(){muted=true} function unmute(){muted=false}}
}
