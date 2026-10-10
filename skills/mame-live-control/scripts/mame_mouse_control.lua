-- Load into an existing authorized bridge; loading this helper sends no input.
-- All device tags/masks are supplied by the caller after a read-only probe.
if mame_live_mouse then return 'Mouse helper already loaded; no input sent' end
local machine = manager.machine
local helper = {operation = nil}
mame_live_mouse = helper

local function field_for(tag, mask)
    assert(type(tag) == 'string' and type(mask) == 'number', 'Port tag and numeric field mask required')
    local port = assert(machine.ioport.ports[tag], 'Unknown input port: ' .. tag)
    return port, assert(port:field(mask), 'Unknown field mask on port: ' .. tag)
end

local function begin(config)
    assert(not helper.operation or helper.operation.done, 'An owned mouse operation is pending')
    assert(not helper.operation or not helper.operation.cleanup_error, 'Previous input cleanup failed; inspect and release it before more input')
    local limit = config.timeout_seconds or 3
    assert(type(limit) == 'number' and limit > 0 and limit <= 30, 'Deadline must be within 30 emulated seconds')
    local state = {done = false, fields = {}, started = machine.time:as_double(), limit = limit}
    helper.operation = state
    function state.finish(reason)
        if state.done and not state.cleanup_error then return end
        state.done = true
        state.reason = reason or 'released'
        local problems = {}
        for _, field in ipairs(state.fields) do
            local ok, error_message = pcall(function() field:clear_value() end)
            if not ok then problems[#problems + 1] = tostring(error_message) end
        end
        if state.subscription then
            local ok, error_message = pcall(function() state.subscription:unsubscribe() end)
            if not ok then problems[#problems + 1] = tostring(error_message) end
        end
        state.cleanup_error = #problems > 0 and table.concat(problems, '; ') or nil
    end
    function state.watch(step)
        state.subscription = emu.add_machine_frame_notifier(function()
            if state.done then return end
            local ok, error_message = pcall(function()
                local elapsed = machine.time:as_double() - state.started
                if elapsed >= state.limit then state.finish('deadline') else step(elapsed) end
            end)
            if not ok then state.error = tostring(error_message); state.finish('callback error') end
        end)
    end
    return state
end

function helper.hold(config)
    assert(config.confirm_target == true, 'Confirm the current native image shows the pointer over the intended target')
    local seconds = config.seconds or 0.8
    assert(type(seconds) == 'number' and seconds > 0 and seconds <= 3, 'Hold must be within three emulated seconds')
    local _, button = field_for(config.port, config.mask)
    local state = begin({timeout_seconds = seconds + 0.5})
    state.fields = {button}
    local ok, error_message = pcall(function()
        button:set_value(1)
        state.watch(function(elapsed)
            if elapsed >= seconds then state.finish('hold complete') end
        end)
    end)
    if not ok then state.error = tostring(error_message); state.finish('setup error'); error(error_message) end
    return 'Mouse hold queued; inspect mame_live_mouse.operation.done before more input'
end

function helper.move_counters(config)
    -- Apollo observed behavior: these are wrapped counters, not screen x/y.
    assert(config.confirm_counter_protocol == true, 'Verify the device uses wrapped relative counters before moving')
    local steps = config.steps or 1
    local interval = config.frame_interval or 10
    local dx, dy = config.dx or 0, config.dy or 0
    assert(steps % 1 == 0 and steps >= 1 and steps <= 100, 'Use at most 100 measured counter steps')
    assert(interval % 1 == 0 and interval >= 1 and interval <= 60, 'Frame interval must be 1..60')
    assert(dx % 1 == 0 and dy % 1 == 0 and math.abs(dx) <= 3 and math.abs(dy) <= 3, 'Use small integer counter steps')
    local modulus = config.modulus or 256
    assert(modulus % 1 == 0 and modulus >= 2 and modulus <= 65536, 'Invalid counter modulus')
    local px, fx = field_for(config.x_port, config.x_mask)
    local py, fy = field_for(config.y_port, config.y_mask)
    local state = begin(config)
    state.fields = {fx, fy}
    state.x, state.y, state.steps, state.ticks = px:read() % modulus, py:read() % modulus, 0, 0
    local ok, error_message = pcall(function()
        fx:set_value(state.x); fy:set_value(state.y)
        state.watch(function()
            state.ticks = state.ticks + 1
            if state.steps == steps then state.finish('counter steps complete'); return end
            if state.ticks % interval == 0 then
                state.x, state.y = (state.x + dx) % modulus, (state.y + dy) % modulus
                fx:set_value(state.x); fy:set_value(state.y)
                state.steps = state.steps + 1
            end
        end)
    end)
    if not ok then state.error = tostring(error_message); state.finish('setup error'); error(error_message) end
    return 'Relative counter movement queued; inspect native image after completion'
end

function helper.release()
    if helper.operation then
        helper.operation.finish('explicit release')
        assert(not helper.operation.cleanup_error, helper.operation.cleanup_error)
    end
    return 'Owned input released; unrelated input fields were not cleared'
end

emu.register_stop(function() helper.release() end)
return 'Mouse helper loaded; no input sent'
