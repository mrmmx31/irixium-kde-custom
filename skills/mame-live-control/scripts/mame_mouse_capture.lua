-- Parameterized AltGr release / left-click recapture hook, MAME 0.276 SDL.
-- Requires MAME_MOUSE_CAPTURE_CONFIG. Never replace an existing capture hook.
assert(not domainos_mouse_host and not mame_live_mouse_host, 'Preserve the already installed mouse hook')
local config = assert(MAME_MOUSE_CAPTURE_CONFIG, 'Configure input ports before loading the capture hook')
assert(type(config.port_tags) == 'table' and #config.port_tags > 0, 'Explicit mouse port tags required')
local machine, input = manager.machine, manager.machine.input
local alt = input:code_from_token(config.release_token or 'KEYCODE_RALT')
local click = input:code_from_token(config.capture_token or 'MOUSECODE_1_BUTTON1')
local previous_alt, previous_click = false, false
local state = {captured = true, transitions = 0, version = 2}
local fields = {}
for _, tag in ipairs(config.port_tags) do
    local port = assert(machine.ioport.ports[tag], 'Unknown mouse port: ' .. tag)
    for _, field in pairs(port.fields) do
        local seqs = {}
        for _, kind in ipairs({'standard', 'increment', 'decrement'}) do
            seqs[kind] = emu.input_seq(field:input_seq(kind))
        end
        fields[#fields + 1] = {field = field, seqs = seqs}
    end
end
if config.expected_fields then assert(#fields == config.expected_fields, 'Mouse field count differs from configuration') end
assert(#fields > 0, 'No mouse fields found')
local function guest_input(enabled)
    for _, entry in ipairs(fields) do
        for kind, seq in pairs(entry.seqs) do
            entry.field:set_input_seq(kind, enabled and seq or emu.input_seq())
        end
    end
end
state.guest_input = guest_input
mame_live_mouse_host = state
function state.release()
    guest_input(false)
    machine.options.entries.mouse:value(false)
    state.captured, state.wait_button_up = false, false
    state.transitions = state.transitions + 1
end
function state.capture()
    machine.options.entries.mouse:value(true)
    state.captured, state.wait_button_up = true, true
    state.transitions = state.transitions + 1
end
emu.register_periodic(function()
    if state.disabled then return end
    local a, c = input:code_pressed(alt), input:code_pressed(click)
    if a and not previous_alt then
        state.release()
    elseif not state.captured and not a and c and not previous_click then
        state.capture()
    end
    if state.captured and state.wait_button_up and not c then
        guest_input(true)
        state.wait_button_up = false
    end
    previous_alt, previous_click = a, c
end)
emu.register_stop(function()
    guest_input(true)
    machine.options.entries.mouse:value(true)
end)
if config.start_released then state.release() end
return 'Capture hook attached; preserve and report its state before GUI work'
