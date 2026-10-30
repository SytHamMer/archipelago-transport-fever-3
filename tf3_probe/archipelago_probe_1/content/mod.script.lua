-- THROWAWAY PROBE 6: nothing is hidden at load any more; the game's own runtime filters are driven from probe.script.lua.
function data()
	local mod = {}
	mod.postRunFn = function(captureParams, configDict, allModParams, baseConfig)
		pcall(function() debugPrint("ARCHIPELAGO_PROBE6 postRun: inert (no load-time hiding)") end)
	end
	return mod
end
