-- Brings the prices of modern depots, stations and terminals back to those of the first era. Pure logic.
--
-- Many constructions multiply their price by a coefficient that depends on their first year: 1 before 1940, 3 from
-- 1940 and 9 from 1980. A game that starts in 2020 only offers the recent models, so every depot and station costs nine
-- times what it does in an early game. Dividing by the same coefficient restores the early prices.
local M = {}

-- Fragments of the resource names of the constructions whose price carries that coefficient.
M.FRAGMENTS = {
	"/depots/road/road_depot", "/depots/road/road_maint_station", "/depots/road/tram_depot",
	"/depots/rail/rail_depot", "/depots/rail/rail_maint_station",
	"/depots/water/water_depot", "/depots/water/water_maint_station",
	"/stations/rail/modular_station", "/stations/street/modular_street_station", "/stations/street/modular_terminal",
	"/stations/street/underground_station",
}

function M.era_coefficient(year)
	if year >= 1980 then return 9 end
	if year >= 1940 then return 3 end
	return 1
end

local function divide(list, coefficient)
	if type(list) ~= "table" then return end
	for index, value in ipairs(list) do
		if type(value) == "number" and value > 0 then
			list[index] = math.max(1, math.floor(value / coefficient + 0.5))
		end
	end
end

local function normalise_attributes(attributes, year)
	if type(attributes) ~= "table" or type(year) ~= "number" then return end
	local coefficient = M.era_coefficient(year)
	if coefficient == 1 then return end
	divide(attributes.cost, coefficient)
	divide(attributes.maintenanceCost, coefficient)
end

local function matches(file_name)
	local name = tostring(file_name)
	for _, fragment in ipairs(M.FRAGMENTS) do
		if name:find(fragment, 1, true) then return true end
	end
	return false
end

-- Divides the cost and the upkeep of a matching construction by its era coefficient (in place). The era variants
-- of a depot or station are the `constructionTemplates` of its file, each with its own first year and prices; a file
-- that has its price at the top level instead (with an `availability.yearFrom`) is handled too.
function M.normalise(file_name, data)
	if type(data) ~= "table" or not matches(file_name) then return end
	if type(data.availability) == "table" then normalise_attributes(data, data.availability.yearFrom) end
	for _, template in ipairs(type(data.constructionTemplates) == "table" and data.constructionTemplates or {}) do
		if type(template) == "table" and type(template.availability) == "table" and type(template.description) == "table" then
			normalise_attributes(template.description.attributes, template.availability.yearFrom)
		end
	end
end

return M
