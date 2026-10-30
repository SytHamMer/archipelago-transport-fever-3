-- Computes which menu items and vehicles are locked, from the items the player has received.
-- Pure logic: the game's resources are scanned elsewhere and handed in as `catalog`.
--
-- catalog = {
--   eras = { B = <first year of era B>, C = <first year of era C> },
--   modes = { <mode> = { menu = { tag, ... }, vehicles = { { path = ..., year = ... }, ... } }, ... },
-- }
--   An entry may also have `types = { { tag = ..., year = ... }, ... }` and `type_item` (the name of the item that
--   releases them by tier): road and track types, tiered by first year like the vehicles.
-- Modes are road, tram, rail, water, air. Road starts unlocked.
local M = {}

local function capitalize(text)
	return text:sub(1, 1):upper() .. text:sub(2)
end

function M.mode_item(mode)
	return capitalize(mode) .. " Transport"
end

function M.vehicle_item(mode)
	return "Progressive " .. capitalize(mode) .. " Vehicles"
end

-- Vehicle tier from its first year: 0 before era B, 1 before era C, 2 afterwards (unknown year counts as 0).
local function tier_of(year, eras)
	if year == nil then return 0 end
	if year < eras.B then return 0 end
	if year < eras.C then return 1 end
	return 2
end

local function sorted_keys(set)
	local out = {}
	for key in pairs(set) do out[#out + 1] = key end
	table.sort(out)
	return out
end

function M.compute_locks(items, catalog)
	local menu, vehicles = {}, {}
	for mode, entry in pairs(catalog.modes) do
		local unlocked = (mode == "road") or ((items[M.mode_item(mode)] or 0) >= 1)
		if not unlocked then
			for _, tag in ipairs(entry.menu or {}) do menu[tag] = true end
			for _, vehicle in ipairs(entry.vehicles or {}) do vehicles[vehicle.path] = true end
		else
			local allowed = items[M.vehicle_item(mode)] or 0
			for _, vehicle in ipairs(entry.vehicles or {}) do
				if tier_of(vehicle.year, catalog.eras) > allowed then vehicles[vehicle.path] = true end
			end
		end
		-- road and track types: locked with the mode, then released step by step by their own item
		local allowed_types = entry.type_item and (items[entry.type_item] or 0) or 0
		for _, entry_type in ipairs(entry.types or {}) do
			if not unlocked or tier_of(entry_type.year, catalog.eras) > allowed_types then menu[entry_type.tag] = true end
		end
	end
	return { menu = sorted_keys(menu), vehicles = sorted_keys(vehicles) }
end

function M.deep_equal(a, b)
	if type(a) ~= type(b) then return false end
	if type(a) ~= "table" then return a == b end
	for key, value in pairs(a) do
		if not M.deep_equal(value, b[key]) then return false end
	end
	for key in pairs(b) do
		if a[key] == nil then return false end
	end
	return true
end

return M
