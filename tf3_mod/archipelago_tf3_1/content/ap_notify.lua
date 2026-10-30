-- Builds the in-game notification messages from what changed since the last tick. Pure logic.
--
-- state  = { items = { [name] = count }, checks = { "population:1", ... } }
-- config = the inbox `config` (its `checks` hold the thresholds the check ids refer to)
-- A message is { title = ..., text = ... }.
local M = {}

M.DEFAULT_LIMIT = 5 -- notifications per tick, the last one sums up the rest
M.ITEM_TITLE = "Archipelago: item received"
M.CHECK_TITLE = "Archipelago: check sent"
M.CONTRACT_TITLE = "Archipelago: contract completed"
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
	elseif family == "mission" and threshold(checks.missions, parts[2]) then
		return "Missions completed: " .. with_separators(threshold(checks.missions, parts[2]))
	elseif family == "line" and parts[2] then
		return "First " .. parts[2] .. " line built"
	elseif family == "delivered" and parts[2] and threshold(checks.delivery, parts[3]) then
		return "Delivered " .. with_separators(threshold(checks.delivery, parts[3])) .. " " .. parts[2]:gsub("_", " ")
	end
	return "Check reached: " .. id
end

-- What a contract's progress follows, for the live "35 / 100" of the notifications tab: { kind, goal, cargo? }, or nil
-- for checks without a number to follow (first lines, missions). Static, so the notification parameters never change.
function M.progress_spec(id, config)
	local checks = (config and config.checks) or {}
	local parts = split(id)
	local family = parts[1]
	local function threshold(list, index) return list and list[tonumber(index)] end
	if family == "population" or family == "passengers" or family == "cargo" then
		local goal = threshold(checks[family], parts[2])
		return goal and { kind = family, goal = goal } or nil
	elseif family == "company_level" and tonumber(parts[2]) then
		return { kind = family, goal = tonumber(parts[2]) }
	elseif family == "delivered" and parts[2] then
		local goal = threshold(checks.delivery, parts[3])
		return goal and { kind = family, goal = goal, cargo = parts[2] } or nil
	end
	return nil
end

local FAMILY_ORDER = { "population", "company_level", "passengers", "cargo", "mission", "line", "delivered" }

-- The contracts still to do, for the notifications tab: { key, title, text } each, in a fixed order. Only the next
-- step of each ladder (and the next delivery tier of each cargo) is listed, the first lines all are.
-- `contracts` maps a check id to its reward { item, to, own }; `done` is the list of reached check ids.
function M.open_contracts(contracts, done, config)
	local finished = {}
	for _, id in ipairs(done or {}) do finished[id] = true end

	local ladder_next, rows = {}, {}
	for id, reward in pairs(contracts or {}) do
		if not finished[id] then
			local parts = split(id)
			local family = parts[1]
			local group = (family == "delivered") and (family .. ":" .. tostring(parts[2])) or family
			local step = tonumber(family == "delivered" and parts[3] or parts[2])
			if family == "line" then
				rows[#rows + 1] = { key = id, family = family, group = id, step = 0, reward = reward }
			elseif step and (not ladder_next[group] or step < ladder_next[group].step) then
				ladder_next[group] = { key = id, family = family, group = group, step = step, reward = reward }
			end
		end
	end
	for _, row in pairs(ladder_next) do rows[#rows + 1] = row end

	local rank = {}
	for index, family in ipairs(FAMILY_ORDER) do rank[family] = index end
	table.sort(rows, function(a, b)
		local ra, rb = rank[a.family] or 99, rank[b.family] or 99
		if ra ~= rb then return ra < rb end
		return a.key < b.key
	end)

	local out = {}
	for _, row in ipairs(rows) do
		local reward = row.reward
		out[#out + 1] = {
			key = row.key,
			title = "Contract: " .. M.describe_check(row.key, config),
			text = "Reward: " .. reward.item .. (reward.own and "" or (" for " .. reward.to)),
			progress = M.progress_spec(row.key, config),
		}
	end
	return out
end

-- Text of a received item: who sent it and for which check, when known. Our own checks are shown with the
-- readable check text, the others by the name the server gives them.
local function item_text(entry, config)
	local text = entry.item
	if entry.from then text = text .. " from " .. entry.from end
	if entry.where then
		text = text .. " (" .. (entry.own and M.describe_check(entry.where, config) or entry.where) .. ")"
	end
	return text
end

local function sorted_names(items)
	local names = {}
	for name in pairs(items or {}) do names[#names + 1] = name end
	table.sort(names)
	return names
end

-- Messages for what is new in `current` compared with `previous`. The first state (previous is nil) only sets the
-- baseline and notifies nothing, so a reloaded game does not replay everything already received.
-- `contracts` (optional) maps a check id to its reward { item, to, own }: such checks are announced as contracts.
function M.diff(previous, current, config, limit, contracts)
	if previous == nil then return {} end
	limit = limit or M.DEFAULT_LIMIT
	local messages = {}

	if current.log then
		-- the ordered log says who sent what: announce the entries that are new
		local seen = previous.log_size or #(previous.log or {})
		for index = seen + 1, #current.log do
			messages[#messages + 1] = { title = M.ITEM_TITLE, text = item_text(current.log[index], config) }
		end
	else
		for _, name in ipairs(sorted_names(current.items)) do
			local delta = (current.items[name] or 0) - ((previous.items or {})[name] or 0)
			if delta > 0 then
				messages[#messages + 1] = { title = M.ITEM_TITLE, text = delta > 1 and (name .. " x" .. delta) or name }
			end
		end
	end

	local known = {}
	for _, id in ipairs(previous.checks or {}) do known[id] = true end
	for _, id in ipairs(current.checks or {}) do
		if not known[id] then
			local text, reward = M.describe_check(id, config), contracts and contracts[id]
			if reward then
				text = text .. " - reward: " .. reward.item .. (reward.own and "" or (" for " .. reward.to))
			end
			messages[#messages + 1] = { title = reward and M.CONTRACT_TITLE or M.CHECK_TITLE, text = text }
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
