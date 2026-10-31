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

-- Divides the cost and the upkeep of a matching construction by its era coefficient (in place).
function M.normalise(file_name, data)
	if type(data) ~= "table" or type(data.availability) ~= "table" then return end
	local year = data.availability.yearFrom
	if type(year) ~= "number" then return end
	local name = tostring(file_name)
	local matches = false
	for _, fragment in ipairs(M.FRAGMENTS) do
		if name:find(fragment, 1, true) then matches = true break end
	end
	if not matches then return end
	local coefficient = M.era_coefficient(year)
	if coefficient == 1 then return end
	divide(data.cost, coefficient)
	divide(data.maintenanceCost, coefficient)
end

return M
