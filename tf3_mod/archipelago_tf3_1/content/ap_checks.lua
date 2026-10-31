-- Evaluates which checks and goals are reached from the readings taken in the game. Pure logic.
--
-- config   = the inbox `config`: { goals = {population, company_level, passengers, cargo},
--            checks = {population = {...}, company_level = {...}, passengers = {...}, cargo = {...},
--                      first_line = boolean, delivery = {...}, missions = {...}} }
-- readings = { experience, earned_level, passengers, cargo, line_modes = {[TransportMode index] = true},
--              delivered = {[cargo name] = amount} }   (any field may be missing)
local M = {}

-- TransportMode enum indexes (0-based) that count for each first-line check.
-- PERSON 0 and CARGO 1 are not vehicle lines.
local LINE_MODES = {
	road = { 2, 3, 4 },        -- CAR, BUS, TRUCK
	tram = { 5, 6 },           -- TRAM, ELECTRIC_TRAM
	rail = { 7, 8 },           -- TRAIN, ELECTRIC_TRAIN
	water = { 10, 12 },        -- SHIP, SMALL_SHIP
	air = { 9, 11, 13 },       -- AIRCRAFT, SMALL_AIRCRAFT, HELICOPTER
}

local GOAL_READINGS = {
	population = "experience",
	company_level = "earned_level",
	passengers = "passengers",
	cargo = "cargo",
}

local function number(value)
	return type(value) == "number" and value or 0
end

local function sorted_unique(list)
	local seen, out = {}, {}
	for _, value in ipairs(list) do
		if not seen[value] then seen[value] = true out[#out + 1] = value end
	end
	table.sort(out)
	return out
end

function M.evaluate(config, readings)
	local reached = {}
	local checks = config.checks or {}

	local function ladder(family, reading, use_level)
		for index, threshold in ipairs(checks[family] or {}) do
			if number(reading) >= threshold then
				reached[#reached + 1] = family .. ":" .. (use_level and threshold or index)
			end
		end
	end
	ladder("population", readings.experience)
	ladder("company_level", readings.earned_level, true)
	ladder("passengers", readings.passengers)
	ladder("cargo", readings.cargo)
	for index, needed in ipairs(checks.missions or {}) do
		if number(readings.missions) >= needed then reached[#reached + 1] = "mission:" .. index end
	end

	if checks.first_line then
		local modes = readings.line_modes or {}
		for name, indexes in pairs(LINE_MODES) do
			for _, index in ipairs(indexes) do
				if modes[index] then
					reached[#reached + 1] = "line:" .. name
					break
				end
			end
		end
	end

	for cargo, amount in pairs(readings.delivered or {}) do
		for tier, needed in ipairs(checks.delivery or {}) do
			if number(amount) >= needed then
				reached[#reached + 1] = "delivered:" .. cargo .. ":" .. tier
			end
		end
	end

	local goals = {}
	for name, reading in pairs(GOAL_READINGS) do
		local wanted = number((config.goals or {})[name])
		if wanted > 0 then goals[name] = number(readings[reading]) >= wanted end
	end
	return { checks = sorted_unique(reached), goals = goals }
end

-- The uids of the game's missions among the completed subventions `entries` ({ id, uid }): our own contracts are
-- subventions too and must not count as missions.
function M.foreign_mission_uids(entries)
	local uids = {}
	for _, entry in ipairs(entries or {}) do
		if type(entry.id) == "string" and type(entry.uid) == "number" and not entry.id:find("ap_subvention", 1, true) then
			uids[#uids + 1] = entry.uid
		end
	end
	return uids
end

-- Uids of the missions completed so far: the ones already known plus the ones the game lists now, each once.
-- A mission that later leaves the game's list stays counted.
function M.merge_missions(previous, current)
	local all = {}
	for _, value in ipairs(previous or {}) do all[#all + 1] = value end
	for _, value in ipairs(current or {}) do all[#all + 1] = value end
	return sorted_unique(all)
end

-- Whether the mod understands an inbox of this format version (an older or the same one: the client of a newer
-- version may write a format this mod does not know, and the mod then must not guess).
function M.format_supported(version, supported)
	return type(version) == "number" and version <= supported
end

-- Checks never go away, even if a reading later drops.
function M.merge_monotonic(previous, current)
	local all = {}
	for _, value in ipairs(previous or {}) do all[#all + 1] = value end
	for _, value in ipairs(current or {}) do all[#all + 1] = value end
	return sorted_unique(all)
end

-- Goals stay reached too: a goal that was reached once is never taken back by a later reading
-- (for example population falling below its target after another goal was reached).
function M.merge_goals(previous, current)
	local out = {}
	for name, reached in pairs(previous or {}) do out[name] = reached end
	for name, reached in pairs(current or {}) do out[name] = out[name] or reached end
	return out
end

return M
