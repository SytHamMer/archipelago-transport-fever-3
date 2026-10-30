-- THROWAWAY PROBE 6 (GUI context): drives the game's own runtime lock filters, as campaign missions do.
--   vfilter{kinds={"bus",...}}   -> api.gui.fireReactEvent("setVehicleFilter", {disabledVehicles = paths of those kinds})
--   mfilter{items={"resName",...}} -> api.gui.fireReactEvent("setMenuFilter", {disabledItems = items})
--   consnames{pattern,max}       -> logs construction resource names containing the pattern
--   clear{}                      -> empties both filters
-- inbox = { seq = N, ops = {...} }; the ops run once each time seq increases. Nothing is written to disk by the game here.
local DIR = "towns_industries"
local IN_NAME = "archipelago_probe_inbox"

local function say(text)
	pcall(function() debugPrint("ARCHIPELAGO_PROBE6 " .. text) end)
end

local function pathKind(path, kind)
	return type(path) == "string"
		and (path:find("/vehicle/" .. kind .. "/", 1, true) or path:find("^vehicle/" .. kind .. "/"))
end

local function vehiclePaths(kinds)
	local out = {}
	api.res.modelRep.forEachModelWithMetadata("transportVehicle", function(path)
		for _, k in ipairs(kinds) do
			if pathKind(path, k) then out[#out + 1] = path break end
		end
	end)
	return out
end

local ops = {
	vfilter = function(o)
		local paths = vehiclePaths(o.kinds or {})
		api.gui.fireReactEvent("setVehicleFilter", { enabledVehicles = {}, disabledVehicles = paths })
		say("vfilter: fired setVehicleFilter with " .. #paths .. " disabled paths, first=" .. tostring(paths[1]))
	end,
	mfilter = function(o)
		api.gui.fireReactEvent("setMenuFilter", { enabledItems = {}, disabledItems = o.items or {}, disabledParams = {} })
		say("mfilter: fired setMenuFilter with " .. #(o.items or {}) .. " disabled items, first=" .. tostring((o.items or {})[1]))
	end,
	consnames = function(o)
		local n, shown = 0, 0
		for id, name in pairs(api.res.constructionRep.getAll(true)) do
			if type(name) == "string" and name:find(o.pattern or "", 1, true) then
				n = n + 1
				if shown < (o.max or 8) then shown = shown + 1 say("consname[" .. n .. "]=" .. name) end
			end
		end
		say("consnames pattern='" .. tostring(o.pattern) .. "': matches=" .. n)
	end,
	-- lock{modes={"rail","tram","water","air"}}: disables the menu items AND the vehicles of those transport modes
	lock = function(o)
		-- repo -> list of path fragments (plain find) per mode; resource names look like "::/stations/rail/..."
		local modeItems = {
			rail = { cons = { "/stations/rail/", "/depots/rail/", "/infrastructure/signal/" },
				meta = { "/stations/rail/" }, streets = { "/infrastructure/track/" }, tools = {} },
			tram = { cons = { "/depots/road/tram_depot/" }, meta = {}, streets = {},
				tools = { "::/gui/construction/tools/tram_track_tool.res" } },
			water = { cons = { "/stations/water/", "/depots/water/" }, meta = { "/stations/water/" }, streets = {}, tools = {} },
			air = { cons = { "/stations/air/airfield", "/stations/air/airport", "/depots/air/" },
				meta = { "/stations/air/" }, streets = {}, tools = {} },
		}
		local modeVehicles = {
			rail = { "train", "waggon" }, tram = { "tram" }, water = { "ship" },
			air = { "plane", "helicopter", "zeppelin" },
		}
		local items, kinds, seen = {}, {}, {}
		local function add(tag)
			if not seen[tag] then seen[tag] = true items[#items + 1] = tag end
		end
		local function scan(rep, fragments, mode, label)
			if #fragments == 0 then return end
			local n, sample = 0, nil
			for _, name in pairs(rep.getAll(true)) do
				if type(name) == "string" then
					for _, f in ipairs(fragments) do
						if name:find(f, 1, true) and not name:find("/assets/", 1, true) then
							n = n + 1
							sample = sample or name
							add(name)
							if label ~= "street" then for i = 0, 11 do add(name .. "@" .. i) end end
							break
						end
					end
				end
			end
			say("lock " .. mode .. " " .. label .. ": matches=" .. n .. " sample=" .. tostring(sample))
		end
		for _, mode in ipairs(o.modes or {}) do
			local m = modeItems[mode]
			if m then
				scan(api.res.constructionRep, m.cons, mode, "con")
				scan(api.res.metaConstructionRep, m.meta, mode, "metacon")
				scan(api.res.streetTemplateRep, m.streets, mode, "street")
				for _, t in ipairs(m.tools) do add(t) end
				for _, k in ipairs(modeVehicles[mode] or {}) do kinds[#kinds + 1] = k end
			else
				say("lock: unknown mode " .. tostring(mode))
			end
		end
		api.gui.fireReactEvent("setMenuFilter", { enabledItems = {}, disabledItems = items, disabledParams = {} })
		local paths = vehiclePaths(kinds)
		api.gui.fireReactEvent("setVehicleFilter", { enabledVehicles = {}, disabledVehicles = paths })
		say("lock: fired menu filter with " .. #items .. " items and vehicle filter with " .. #paths .. " vehicles")
	end,
	-- ===== probe 8: read-only readouts for checks (population, lines per mode, transported, per-cargo, levels) =====
	reads = function(_)
		local function keysOf(t)
			local out = {}
			if type(t) == "table" then for k, v in pairs(t) do out[#out + 1] = tostring(k) .. "=" .. tostring(v) end end
			table.sort(out)
			return table.concat(out, ",")
		end
		local player = api.engine.util.getPlayer()

		-- population: sum of residential "used" capacity over all towns
		local okP, errP = pcall(function()
			local townUtil = ug_require("::/game_mechanics/towns/town_util.tl")
			local towns = api.engine.getEntitiesWithComponent(api.type.ComponentType.TOWN)
			local total, n = 0, 0
			for _, town in ipairs(towns) do
				local caps = townUtil.getTownCapacityUsages(town)
				local res = caps[api.type["enum"].LandUseType.RESIDENTIAL + 1]
				if n == 0 then say("population: first town caps[1]={" .. keysOf(caps[1]) .. "} residentialIndex=" .. tostring(api.type["enum"].LandUseType.RESIDENTIAL)) end
				total = total + ((res and res.used) or 0)
				n = n + 1
			end
			say("population: towns=" .. n .. " residential used sum=" .. total)
		end)
		if not okP then say("population FAILED: " .. tostring(errP)) end

		-- lines per transport mode
		local okL, errL = pcall(function()
			local lines = api.engine.system.lineSystem.getLinesForPlayer(player)
			local perMode, n = {}, 0
			for _, line in ipairs(lines) do
				n = n + 1
				local comp = api.engine.getComponent(line, api.type.ComponentType.LINE)
				local modes = comp and comp.vehicleInfo and comp.vehicleInfo.transportModes
				local key = keysOf(modes)
				perMode[key] = (perMode[key] or 0) + 1
				if n == 1 then say("lines: first line vehicleInfo keys={" .. keysOf(comp and comp.vehicleInfo) .. "}") end
			end
			local out = {}
			for k, v in pairs(perMode) do out[#out + 1] = "[" .. k .. "]x" .. v end
			say("lines: count=" .. n .. " byTransportModes=" .. table.concat(out, ";"))
		end)
		if not okL then say("lines FAILED: " .. tostring(errL)) end

		-- headquarters statistics
		local okH, errH = pcall(function()
			local t = api.engine.util.headquarters.getTransportedData()
			local v = api.engine.util.headquarters.getCompaniesValue()
			say("transported: passengers=" .. tostring(t.passengersTransported) .. " cargo=" .. tostring(t.cargoTransported))
			say("companyValue: {" .. keysOf(v) .. "}")
		end)
		if not okH then say("headquarters FAILED: " .. tostring(errH)) end

		-- per-cargo lifetime counters in the logbook (player and world entities)
		local okC, errC = pcall(function()
			local world = api.engine.util.getWorld()
			local found = {}
			for cargoId, name in pairs(api.res.cargoTypeRep.getAll()) do
				for label, entity in pairs({ player = player, world = world }) do
					local ok, v = pcall(function()
						return api.engine.util.logbook.getLogValueMostRecent(entity, "itemsTransported" .. tostring(cargoId))
					end)
					if ok and v and v ~= 0 then found[#found + 1] = label .. ":" .. tostring(name):gsub("^.*/", "") .. "=" .. tostring(v) end
				end
			end
			say("itemsTransported nonzero: " .. (#found > 0 and table.concat(found, " ") or "(none)"))
		end)
		if not okC then say("itemsTransported FAILED: " .. tostring(errC)) end

		-- earned (real) company level, independent of enforcedLevel
		local okV, errV = pcall(function()
			local cu = ug_require("::/game_mechanics/company/company_util.tl")
			local pu = ug_require("::/game_mechanics/company/company_progression_util.tl")
			local st = pu.getCompanyProgressionState(player)
			local level, fraction = pu.getLevelAndFraction(cu.getBasePopulation(), st.experience)
			say("companyLevel: effective=" .. tostring(st.level) .. " earnedFromExp=" .. tostring(level)
				.. " fraction=" .. tostring(fraction) .. " exp=" .. tostring(st.experience))
		end)
		if not okV then say("companyLevel FAILED: " .. tostring(errV)) end
	end,
	-- ===== probe 7: money, company level, forced loan =====
	balance = function(_)
		local ok, b = pcall(function() return api.engine.util.getPlayersBalance(api.engine.util.getPlayer()) end)
		say("balance: ok=" .. tostring(ok) .. " value=" .. tostring(b))
	end,
	money = function(o)
		local entry = api.type.JournalEntry.new()
		entry.amount = o.amount
		entry.time = -1
		entry.category.type = (o.amount >= 0) and api.type.JournalEntry.Type.INCOME or api.type.JournalEntry.Type.OTHER
		api.cmd.sendCommand(api.cmd.makeJournalBookAssetCmd(api.engine.util.getPlayer(), entry, api.type.Vec3f.new(0, 0, 0)),
			function(_, success) say("money command callback: amount=" .. tostring(o.amount) .. " success=" .. tostring(success)) end)
		say("money: sent amount=" .. tostring(o.amount))
	end,
	level = function(o)
		local rep = api.res.genericRep
		local id = rep.find("::/game_mechanics/company/company_growth_config.res")
		say("level: genericRep.find -> " .. tostring(id))
		local t = rep.getAsTable(id)
		local before = t and t.data and t.data.enforcedLevel
		say("level: getAsTable type=" .. tostring(t and t.type) .. " before enforcedLevel=" .. tostring(before))
		t.data = t.data or {}
		t.data.enforcedLevel = o.value
		local okSet = rep.setAsTable(id, t)
		local after = rep.getAsTable(id)
		say("level: setAsTable returned " .. tostring(okSet) .. ", read back enforcedLevel="
			.. tostring(after and after.data and after.data.enforcedLevel))
		local ok, util = pcall(function() return ug_require("::/game_mechanics/company/company_progression_util.tl") end)
		if ok and type(util) == "table" then
			local ok2, st = pcall(function() return util.getCompanyProgressionState(api.engine.util.getPlayer()) end)
			say("level: progression state ok=" .. tostring(ok2) .. " level=" .. tostring(ok2 and st and st.level)
				.. " exp=" .. tostring(ok2 and st and st.experience))
		else
			say("level: could not load company_progression_util: " .. tostring(util))
		end
	end,
	loan = function(o)
		local util = ug_require("::/game_mechanics/finance/loan_util.tl")
		local loan = util.createSmallLoan()
		say("loan: created small loan amount=" .. tostring(loan.amount) .. " type=" .. tostring(loan.type))
		api.cmd.sendCommand(api.cmd.makeScriptingSendEventCmd("", "Loan", "Obtain", { loan, loan }))
		say("loan: Obtain event sent")
	end,
	clear = function(_)
		api.gui.fireReactEvent("setVehicleFilter", { enabledVehicles = {}, disabledVehicles = {} })
		api.gui.fireReactEvent("setMenuFilter", { enabledItems = {}, disabledItems = {}, disabledParams = {} })
		say("clear: both filters emptied")
	end,
}

local lastTime, lastSeq = 0, -1

local function step()
	if type(app) ~= "table" then return end
	local now = os.time()
	if now - lastTime < 2 then return end
	lastTime = now

	local ok, res = pcall(function() return app.loadUserdata(DIR, IN_NAME) end)
	if not ok or type(res) ~= "table" then return end
	if type(res.seq) ~= "number" or res.seq == lastSeq then return end
	lastSeq = res.seq
	say("run seq=" .. res.seq)
	for _, o in ipairs(res.ops or {}) do
		local f = ops[o.op]
		if f then
			local okO, errO = pcall(f, o)
			if not okO then say("op " .. tostring(o.op) .. " FAILED: " .. tostring(errO)) end
		else
			say("unknown op " .. tostring(o.op))
		end
	end
end

function data()
	return {
		update = function(_userParams, _state, _dt) end,
		handleEvent = function(_userParams, _state, _src, _id, _name, _param) end,
		guiUpdate = function(...) step() end,
		guiHandleEvent = function(...) end,
	}
end
