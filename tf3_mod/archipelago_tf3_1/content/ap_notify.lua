-- Builds the in-game notification messages from what changed since the last tick. Pure logic.
--
-- state  = { items = { [name] = count }, checks = { "population:1", ... } }
-- config = the inbox `config` (its `checks` hold the thresholds the check ids refer to)
-- A message is { title = ..., text = ... }.
local M = {}

M.DEFAULT_LIMIT = 5 -- notifications per tick, the last one sums up the rest
M.ITEM_TITLE = "Archipelago: item received"
M.CHECK_TITLE = "Archipelago: check sent"
M.SUMMARY_TITLE = "Archipelago"

local function with_separators(number)
	local digits = tostring(math.floor(number))
	local out = digits:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end

local function split(id)
	local parts = {}
	for part in id:gmatch("[^:]+") do parts[#parts + 1] = part end
	return parts
end

-- Readable text of a check id (see data.location_id on the Python side); unknown ids are shown as they are.
function M.describe_check(id, config)
	local checks = (config and config.checks) or {}
	local parts = split(id)
	local family = parts[1]
	local function threshold(list, index) return list and list[tonumber(index)] end

	if family == "population" and threshold(checks.population, parts[2]) then
		return "Population reached " .. with_separators(threshold(checks.population, parts[2]))
	elseif family == "company_level" and parts[2] then
		return "Company level " .. parts[2] .. " reached"
	elseif family == "passengers" and threshold(checks.passengers, parts[2]) then
		return "Passengers transported: " .. with_separators(threshold(checks.passengers, parts[2]))
	elseif family == "cargo" and threshold(checks.cargo, parts[2]) then
		return "Cargo transported: " .. with_separators(threshold(checks.cargo, parts[2]))
	elseif family == "line" and parts[2] then
		return "First " .. parts[2] .. " line built"
	elseif family == "delivered" and parts[2] and threshold(checks.delivery, parts[3]) then
		return "Delivered " .. with_separators(threshold(checks.delivery, parts[3])) .. " " .. parts[2]:gsub("_", " ")
	end
	return "Check reached: " .. id
end

local function sorted_names(items)
	local names = {}
	for name in pairs(items or {}) do names[#names + 1] = name end
	table.sort(names)
	return names
end

-- Messages for what is new in `current` compared with `previous`. The first state (previous is nil) only sets the
-- baseline and notifies nothing, so a reloaded game does not replay everything already received.
function M.diff(previous, current, config, limit)
	if previous == nil then return {} end
	limit = limit or M.DEFAULT_LIMIT
	local messages = {}

	for _, name in ipairs(sorted_names(current.items)) do
		local delta = (current.items[name] or 0) - ((previous.items or {})[name] or 0)
		if delta > 0 then
			messages[#messages + 1] = { title = M.ITEM_TITLE, text = delta > 1 and (name .. " x" .. delta) or name }
		end
	end

	local known = {}
	for _, id in ipairs(previous.checks or {}) do known[id] = true end
	for _, id in ipairs(current.checks or {}) do
		if not known[id] then
			messages[#messages + 1] = { title = M.CHECK_TITLE, text = M.describe_check(id, config) }
		end
	end

	if #messages > limit then
		local kept = {}
		for index = 1, limit - 1 do kept[index] = messages[index] end
		kept[limit] = { title = M.SUMMARY_TITLE, text = "and " .. (#messages - (limit - 1)) .. " more" }
		return kept
	end
	return messages
end

return M
