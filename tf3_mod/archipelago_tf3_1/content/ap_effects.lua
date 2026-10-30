-- Bookkeeping for effects that must happen exactly once, and for the level granted by items. Pure logic.
local M = {}

M.MAX_LEVEL = 15
M.LEVEL_ITEM = "Company Level +1"

-- Effects not yet applied, in the order they were received. `applied` is the highest effect id already done.
function M.pending(effects, applied)
	local out = {}
	for _, effect in ipairs(effects or {}) do
		if effect.id > (applied or 0) then out[#out + 1] = effect end
	end
	table.sort(out, function(a, b) return a.id < b.id end)
	return out
end

-- Company level to enforce: one level per "Company Level +1" item on top of level 1,
-- never below the level earned through experience, never above the maximum rank.
function M.granted_level(items, earned_level)
	local from_items = 1 + ((items or {})[M.LEVEL_ITEM] or 0)
	local level = math.max(from_items, earned_level or 1)
	return math.min(level, M.MAX_LEVEL)
end

return M
