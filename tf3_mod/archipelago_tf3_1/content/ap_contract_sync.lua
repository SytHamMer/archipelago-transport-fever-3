-- Decides what to tell the game so that every open contract is a game subvention (the game then shows its own
-- contract window, icon and notification for it) and that a reached check finishes its subvention. Pure logic.
--
-- open     = ap_notify.open_contracts(...): { { key, title, text, progress }, ... }
-- checks   = the reached check ids
-- spawned  = { [key] = { uid, n, tick, seen, accepted, sent } }, kept by the caller and updated here
-- present  = { uid, ... } the uids of the subventions the game lists as proposed, active or completed
-- tick     = a counter that grows by one per mod tick
local M = {}

M.RETRY_TICKS = 10 -- a spawn the game never lists is sent again after this many ticks

-- The uid of the n-th subvention of a check. A declined subvention cannot reuse its uid, so n grows.
function M.uid(key, n)
	local sum = 910000
	for index = 1, #key do sum = (sum * 31 + key:byte(index)) % 100000007 end
	return sum * 100 + n
end

function M.plan(open, checks, spawned, present, tick)
	local reached, listed = {}, {}
	for _, id in ipairs(checks or {}) do reached[id] = true end
	for _, uid in ipairs(present or {}) do listed[uid] = true end

	local actions = { spawn = {}, accept = {}, reached = {} }

	for _, contract in ipairs(open or {}) do
		local key = contract.key
		local entry = spawned[key]
		local need = false
		if not entry then
			need = true
		elseif listed[entry.uid] then
			entry.seen = true
		elseif entry.seen or tick - entry.tick >= M.RETRY_TICKS then
			need = true -- declined, or never taken by the game
		end
		if need and not reached[key] then
			-- a spawn the game never took is sent again with the same uid (the game ignores a uid it already took, so a
			-- slow game cannot end up with two contracts); a declined one needs a new uid
			local n = entry and (entry.seen and entry.n + 1 or entry.n) or 1
			local uid = M.uid(key, n)
			spawned[key] = { uid = uid, n = n, tick = tick }
			actions.spawn[#actions.spawn + 1] = {
				key = key, uid = uid, title = contract.title, text = contract.text, progress = contract.progress,
			}
		end
	end

	for key, entry in pairs(spawned) do
		if reached[key] and listed[entry.uid] then
			if not entry.accepted then
				entry.accepted = tick -- the game completes only an accepted (active) subvention
				actions.accept[#actions.accept + 1] = { key = key, uid = entry.uid }
			elseif not entry.sent and tick > entry.accepted then
				entry.sent = true
				actions.reached[#actions.reached + 1] = { key = key, uid = entry.uid }
			end
		end
	end
	return actions
end

return M
