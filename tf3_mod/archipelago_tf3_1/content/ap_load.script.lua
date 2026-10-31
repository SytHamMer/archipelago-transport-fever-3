-- Load-time script: keeps every vehicle on sale once its first year has passed.
-- The game hides vehicles whose end year is behind the current date, and the mod's filters can only hide things,
-- never bring one back. Removing the end years (as the official "vehicles without end year" mod does) leaves
-- the first year, which the mod's tiers are built on, untouched.
function data()
	return {
		runFn = function(captureParams, settings)
			addModifier("loadModel", function(fileName, data)
				local metadata = data.metadata
				if metadata and metadata.transportVehicle and metadata.availability then
					metadata.availability.yearTo = 0
				end
				return data
			end)
			-- Roads and tracks: the old types have an end year too (for example the old country roads end in 1940),
			-- and the game hides them from a late start year on.
			addModifier("loadStreetTemplate", function(fileName, data)
				if data.availability then data.availability.yearTo = 0 end
				return data
			end)
			-- Modern depots and stations cost nine times their first-era price (an era coefficient in their files): bring
			-- them back, or a game that starts in 2020 has no cheap way to build a first line (see ap_costs.lua).
			local found, costs = pcall(require, "archipelago_tf3_1::/ap_costs.lua")
			if not found then pcall(debugPrint, "ARCHIPELAGO costs module unavailable: " .. tostring(costs)) end
			-- Interchanges, roundabouts, signals: only the infrastructure constructions, never buildings or industries.
			addModifier("loadConstruction", function(fileName, data)
				if data.availability and tostring(fileName):find("/infrastructure/", 1, true) then
					data.availability.yearTo = 0
				end
				if found then pcall(costs.normalise, fileName, data) end
				return data
			end)
		end,
	}
end
