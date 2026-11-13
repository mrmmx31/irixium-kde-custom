-- Optional future-launch bridge. Does not alter video, clocks or input.
-- Before loading, set MAME_CONTROL_DIR to an existing private directory.
assert(not mame_live_bridge, 'A portable bridge is already installed')
local base = assert(os.getenv('MAME_CONTROL_DIR'), 'MAME_CONTROL_DIR is required')
assert(base:sub(1, 1) == '/', 'Control directory must be absolute')
base = base:gsub('/+$', '')
local command, running, result = base .. '/command.lua', base .. '/command.running.lua', base .. '/result.txt'
local probe = io.open(running, 'rb')
if probe then probe:close(); error('Unresolved running command; inspect before loading') end
local writable = assert(io.open(result, 'a'), 'Control directory must already exist and be writable')
writable:close()
local state = {base = base, disabled = false, commands = 0}
mame_live_bridge = state
emu.register_periodic(function()
    if state.disabled then return end
    local pending = io.open(command, 'rb')
    if not pending then return end
    pending:close()
    local renamed = os.rename(command, running)
    if not renamed then return end
    local f = assert(io.open(running, 'rb'))
    local source = f:read(1024 * 1024 + 1)
    f:close()
    local ok, value = false, 'Command exceeds 1 MiB'
    if #source <= 1024 * 1024 then
        local fn, problem = load(source, 'mame-live-bridge', 't', _G)
        if fn then ok, value = pcall(fn) else value = problem end
    end
    local log = io.open(result, 'a')
    if not log then
        state.disabled = true
        state.error = 'Cannot append reply; running command retained, do not retry'
        return
    end
    log:write(tostring(value), '\n')
    log:close()
    os.remove(running)
    state.commands = state.commands + 1
    state.last_ok = ok
end)
return 'Portable bridge attached without changing emulator settings'
