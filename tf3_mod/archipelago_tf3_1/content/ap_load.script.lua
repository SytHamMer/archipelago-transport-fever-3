-- Load-time script: makes content available whatever the start year of the game is.
-- The game hides vehicles, road and track types, stations and depots until their first year and after their end year,
-- and its prices follow the date (a game that starts in 2020 costs several times what one in 1900 does). Instead of
-- forcing a late start year, this script sets their first and end years to 0 (see ap_years.lua), which also keeps the
-- old ones on sale as the official "vehicles without end year" mod does. The real first year is stored in the content
-- and read back by ap_main.script.lua, whose tiers of unlocks are built on it; the items of the multiworld lock the
-- content the player has not earned yet.
function data()
	return {
		runFn = function(captureParams, settings)
			local found, years = pcall(require, "archipelago_tf3_1::/ap_years.lua")
			if not found then pcall(debugPrint, "ARCHIPELAGO years module unavailable: " .. tostring(years)) end

			-- Vehicles.
			addModifier("loadModel", function(fileName, data)
				local metadata = data.metadata
				if metadata and metadata.transportVehicle and metadata.availability then
					if found then years.free(metadata.availability) else metadata.availability.yearTo = 0 end
				end
				return data
			end)
			-- Roads and tracks: the old types have an end year too (for example the old country roads end in 1940).
			addModifier("loadStreetTemplate", function(fileName, data)
				if found then years.free(data.availability) elseif data.availability then data.availability.yearTo = 0 end
				return data
			end)
			-- Interchanges, roundabouts, signals, stations and depots (with their era variants): never buildings or
			-- industries.
			addModifier("loadConstruction", function(fileName, data)
				local name = tostring(fileName)
				if name:find("/infrastructure/", 1, true) or name:find("/stations/", 1, true) or name:find("/depots/", 1, true) then
					if found then
						years.free_construction(data)
					elseif data.availability and name:find("/infrastructure/", 1, true) then
						data.availability.yearTo = 0
					end
				end
				return data
			end)
		end,
	}
end
