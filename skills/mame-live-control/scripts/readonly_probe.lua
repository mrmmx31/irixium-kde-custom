-- Pure observation: no input, clocks, throttle, UI or capture mutations.
local machine = manager.machine
local hook = domainos_mouse_host or mame_live_mouse_host
local lines = {
    'frameskip=' .. tostring(machine.video.frameskip),
    'throttled=' .. tostring(machine.video.throttled),
    'paused=' .. tostring(machine.paused),
    'ui_active=' .. tostring(manager.ui and manager.ui.ui_active),
    'mouse_hook=' .. tostring(type(hook)),
    'captured=' .. tostring(hook and hook.captured),
    'wait_button_up=' .. tostring(hook and hook.wait_button_up),
    'portable_mouse_operation=' .. tostring(mame_live_mouse and mame_live_mouse.operation and mame_live_mouse.operation.done),
}
for tag, port in pairs(machine.ioport.ports) do
    lines[#lines + 1] = 'port=' .. tag
    for name, field in pairs(port.fields) do
        lines[#lines + 1] = 'field=' .. tag .. '/' .. tostring(name) .. ' mask=' .. tostring(field.mask)
    end
end
for tag, _ in pairs(machine.screens) do lines[#lines + 1] = 'screen=' .. tag end
table.sort(lines)
return table.concat(lines, '\n')
