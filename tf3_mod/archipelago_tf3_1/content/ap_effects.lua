-- Bookkeeping for effects that must happen exactly once, and for the level granted by items. Pure logic.
local M = {}

M.MAX_LEVEL = 15
M.LEVEL_ITEM = "Company Level +1"
M.MAX_FAILURES = 3 -- an effect that fails this many times is given up, so it cannot block the ones after it

-- Effects not yet applied, in the order they were received. `applied` is the highest effect id already done.
function M.pending(effects, applied)
	local out = {}
	for _, effect in ipairs(effects or {}) do
		if effect.id > (applied or 0) then out[#out + 1] = effect end
	end
	table.sort(out, function(a, b) return a.id < b.id end)
	return out
end

-- Counts one more failure for an effect id and tells whether it must now be skipped.
function M.register_failure(failures, id)
	failures[id] = (failures[id] or 0) + 1
	return failures[id] >= M.MAX_FAILURES
end

-- Company level to enforce: one level per "Company Level +1" item on top of level 1,
-- never below the level earned through experience, never above the maximum rank.
function M.granted_level(items, earned_level)
	local from_items = 1 + ((items or {})[M.LEVEL_ITEM] or 0)
	local level = math.max(from_items, earned_level or 1)
	return math.min(level, M.MAX_LEVEL)
end

-- The game's prices follow the date: a game that starts in 2020 costs six times what one in 1900 does, growing
-- exponentially between the two (its bank loans use the same 0.4 to 2.4 curve). Money amounts of the multiworld are
-- written in 1900 money and multiplied by this factor when they are booked, so they keep their weight at any start year.
M.INFLATION_FIRST_YEAR, M.INFLATION_LAST_YEAR, M.INFLATION_TOTAL = 1900, 2020, 6

function M.inflation(year)
	if type(year) ~= "number" then return 1 end
	local clamped = math.max(M.INFLATION_FIRST_YEAR, math.min(M.INFLATION_LAST_YEAR, year))
	return M.INFLATION_TOTAL ^ ((clamped - M.INFLATION_FIRST_YEAR) / (M.INFLATION_LAST_YEAR - M.INFLATION_FIRST_YEAR))
end

-- An amount in 1900 money as it is booked in the year `year`, rounded to a thousand and never below a thousand.
function M.scale_money(amount, year)
	return math.max(1000, math.floor(amount * M.inflation(year) / 1000 + 0.5) * 1000)
end

return M
