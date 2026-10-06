import QtQuick
import QtQuick.Controls

Rectangle {
    id: background
    anchors.centerIn: parent
    color: "black"

    Image {
        id: spinner
        source: "./spinner.svg"
        anchors.centerIn: parent
        RotationAnimator {
            target: spinner;
            from: 0;
            to: 360;
            loops: Animation.Infinite
            duration: 1000
            running: true
        }
    }
}
