-- Makes content available from the first day of the game, and remembers when it was meant to be. Pure logic.
--
-- The game hides vehicles, roads and stations until their first year. Instead of forcing a late start year, the mod
-- (at load time) sets that year to 0 so everything can be built at any date, and the items of the multiworld do the
-- locking. The year it came with is kept in `notificationSortKey`, an existing numeric field of the availability, so
-- that the mod can still build its vehicle tiers from the real years.
local M = {}

M.FIRST_YEAR, M.LAST_YEAR = 1800, 2200 -- a sort key in this range is a year we stored, anything else is not ours

-- The availability table of content: no first year, no end year, no "new content" notification (in place).
function M.free(availability)
	if type(availability) ~= "table" then return end
	local year = availability.yearFrom
	-- The game hides its placeholder models with a first year of 100000 (or -1): they must stay hidden.
	if type(year) == "number" and (year < 0 or year > M.LAST_YEAR) then return end
	if type(year) == "number" and year > 0 then
		availability.notificationSortKey = year
		availability.yearFrom = 0
		availability.notifyWhenAvailable = false
	end
	availability.yearTo = 0
end

-- The year the content was meant to become available: the one stored by free(), or its own first year.
function M.original(availability)
	if type(availability) ~= "table" then return nil end
	local key = availability.notificationSortKey
	if type(key) == "number" and key >= M.FIRST_YEAR and key <= M.LAST_YEAR then return key end
	return availability.yearFrom
end

-- Whether free() has removed a first year from this availability.
function M.freed(availability)
	return type(availability) == "table" and availability.yearFrom == 0 and M.original(availability) ~= 0
end

-- A construction and each of its era variants (`constructionTemplates`).
function M.free_construction(data)
	if type(data) ~= "table" then return end
	M.free(data.availability)
	for _, template in ipairs(type(data.constructionTemplates) == "table" and data.constructionTemplates or {}) do
		if type(template) == "table" then M.free(template.availability) end
	end
end

return M
