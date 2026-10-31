-- Load-time script: keeps every vehicle on sale once its first year has passed.
-- The game hides vehicles whose end year is behind the current date, and the mod's filters can only hide things,
-- never bring one back. Removing the end years (as the official "vehicles without end year" mod does) leaves
-- the first year, which the mod's tiers are built on, untouched.
function data()
	return {
		runFn = function(captureParams, settings)
			-- PROBE (temporary): what does the load-time script have access to?
			local function say(text) pcall(debugPrint, "ARCHIPELAGO load probe: " .. text) end
			say("app=" .. type(app) .. " io=" .. type(io) .. " os=" .. type(os) .. " require=" .. type(require))
			if type(app) == "table" then
				local ok, value = pcall(app.loadUserdata, "towns_industries", "archipelago_tf3_inbox")
				say("loadUserdata ok=" .. tostring(ok) .. " type=" .. type(value) .. " loan_scale=" ..
					tostring(type(value) == "table" and value.config and value.config.loan_scale))
			end
			local sampled = 0
			addModifier("loadConstruction", function(fileName, data)
				local name = tostring(fileName)
				if sampled < 6 and (name:find("bus_station", 1, true) or name:find("road_depot", 1, true)) then
					sampled = sampled + 1
					local keys = {}
					for key in pairs(data) do keys[#keys + 1] = tostring(key) end
					table.sort(keys)
					say(name .. " keys{" .. table.concat(keys, ",") .. "} cost=" .. tostring(data.cost and (data.cost.price or data.cost[1])) ..
						" availability.yearFrom=" .. tostring(data.availability and data.availability.yearFrom))
				end
				return data
			end)
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
