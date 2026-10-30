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
		end,
	}
end
