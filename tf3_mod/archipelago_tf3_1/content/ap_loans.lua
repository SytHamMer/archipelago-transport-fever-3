-- Scales the amounts of the game's bank loans. Pure logic.
local M = {}

-- The amount with `percent` applied, rounded to a thousand and never below a thousand. A missing or invalid
-- percentage leaves the amount as the game made it.
function M.scale_amount(amount, percent)
	if type(percent) ~= "number" or percent <= 0 then return amount end
	return math.max(1000, math.floor(amount * percent / 100 / 1000 + 0.5) * 1000)
end

return M
