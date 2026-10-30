-- Archipelago for Transport Fever 3: the mod's main loop (GUI context).
-- Every 2 seconds: read the inbox, apply locks / level / one-shot effects, evaluate checks, write the outbox.
-- The game gives mods no file or network access, so everything goes through app.loadUserdata/saveUserdata
-- in the "towns_industries" folder, which the game accepts for mods.
local MOD = "archipelago_tf3_1"
local DIR = "towns_industries"
local INBOX, OUTBOX = "archipelago_tf3_inbox", "archipelago_tf3_outbox"
local TICK_SECONDS = 2
local FORMAT_VERSION = 1
local ERAS = { B = 1920, C = 1960 } -- first years of vehicle era B and C

-- Menu and vehicle catalog per mode. Fragments are searched in the game's resource names (plain find).
local MODES = {
	road = { vehicles = { "bus", "truck", "car" } },
	tram = { cons = { "/depots/road/tram_depot/" }, tools = { "::/gui/construction/tools/tram_track_tool.res" }, vehicles = { "tram" } },
	rail = { cons = { "/stations/rail/", "/depots/rail/", "/infrastructure/signal/" }, meta = { "/stations/rail/" },
		streets = { "/infrastructure/track/" }, vehicles = { "train", "waggon" } },
	water = { cons = { "/stations/water/", "/depots/water/" }, meta = { "/stations/water/" }, vehicles = { "ship" } },
	air = { cons = { "/stations/air/airfield", "/stations/air/airport", "/depots/air/" }, meta = { "/stations/air/" },
		vehicles = { "plane", "helicopter", "zeppelin" } },
}
local TEMPLATE_SUFFIXES = 12 -- constructions are tagged "name@0" .. "name@11" in the menu

local locks, checks, effects

local state = {
	last_tick = 0,
	catalog = nil,
	last_menu = nil, last_vehicles = nil,
	seed = nil, checks = {}, goals = {}, applied = 0,
	enforced = nil,
	inflight = false,
	logged = {},
}

local function say(text)
	pcall(function() debugPrint("ARCHIPELAGO " .. text) end)
end

-- Log each distinct problem once, so a failing reading does not flood the log every 2 seconds.
local function problem(stage, err)
	local key = stage .. tostring(err)
	if not state.logged[key] then
		state.logged[key] = true
		say(stage .. " failed: " .. tostring(err))
	end
end

local function guarded(stage, fn, ...)
	local ok, result = pcall(fn, ...)
	if not ok then problem(stage, result) return nil end
	return result
end

local function load_modules()
	local function load(name) return require(MOD .. "::/" .. name .. ".lua") end
	locks, checks, effects = load("ap_locks"), load("ap_checks"), load("ap_effects")
end

-- ===== catalog of lockable content, built once from the game's resources =====

local function scan(rep, fragments, add_templates, into)
	for _, name in pairs(rep.getAll(true)) do
		if type(name) == "string" and not name:find("/assets/", 1, true) then
			for _, fragment in ipairs(fragments) do
				if name:find(fragment, 1, true) then
					into[#into + 1] = name
					if add_templates then
						for index = 0, TEMPLATE_SUFFIXES - 1 do into[#into + 1] = name .. "@" .. index end
					end
					break
				end
			end
		end
	end
end

local function vehicles_of(kinds)
	local out = {}
	api.res.modelRep.forEachModelWithMetadata("transportVehicle", function(path)
		for _, kind in ipairs(kinds) do
			if path:find("/vehicle/" .. kind .. "/", 1, true) or path:find("^vehicle/" .. kind .. "/") then
				local id = api.res.modelRep.find(path)
				local table_ = api.res.modelRep.getAsTable(id)
				local availability = table_ and table_.metadata and table_.metadata.availability
				out[#out + 1] = { path = path, year = availability and availability.yearFrom or nil }
				break
			end
		end
	end)
	return out
end

local function build_catalog()
	local catalog = { eras = ERAS, modes = {} }
	for mode, def in pairs(MODES) do
		local menu = {}
		scan(api.res.constructionRep, def.cons or {}, true, menu)
		scan(api.res.metaConstructionRep, def.meta or {}, false, menu)
		scan(api.res.streetTemplateRep, def.streets or {}, false, menu)
		for _, tool in ipairs(def.tools or {}) do menu[#menu + 1] = tool end
		catalog.modes[mode] = { menu = menu, vehicles = vehicles_of(def.vehicles) }
	end
	return catalog
end

-- ===== inbox / outbox =====

local function read_inbox()
	local inbox = app.loadUserdata(DIR, INBOX)
	if type(inbox) ~= "table" or inbox.version == nil then return nil end
	return inbox
end

local function adopt_seed(seed)
	if state.seed == seed then return end
	-- A different seed means a different game: start from the outbox of that seed, or from nothing.
	state.seed = seed
	state.checks, state.goals, state.applied = {}, {}, 0
	local previous = app.loadUserdata(DIR, OUTBOX)
	if type(previous) == "table" and previous.seed == seed then
		state.checks = previous.checks or {}
		state.applied = previous.applied or 0
	end
end

local function write_outbox()
	app.saveUserdata(DIR, OUTBOX, {
		version = FORMAT_VERSION, seed = state.seed or "", checks = state.checks, goals = state.goals,
		applied = state.applied, heartbeat = os.time(),
	})
end

-- ===== locks =====

local function apply_locks(items)
	if not state.catalog then state.catalog = build_catalog() end
	local result = locks.compute_locks(items or {}, state.catalog)
	if not locks.deep_equal(result.menu, state.last_menu or {}) or state.last_menu == nil then
		api.gui.fireReactEvent("setMenuFilter", { enabledItems = {}, disabledItems = result.menu, disabledParams = {} })
		state.last_menu = result.menu
	end
	if not locks.deep_equal(result.vehicles, state.last_vehicles or {}) or state.last_vehicles == nil then
		api.gui.fireReactEvent("setVehicleFilter", { enabledVehicles = {}, disabledVehicles = result.vehicles })
		state.last_vehicles = result.vehicles
	end
end

-- ===== readings =====

local function cargo_ids()
	local out = {}
	for id, name in pairs(api.res.cargoTypeRep.getAll()) do
		local short = tostring(name):match("/cargos/([^/]+)/")
		if short and short ~= "passengers" then out[short] = id end
	end
	return out
end

local function take_readings(player)
	local readings = {}
	local progression = ug_require("::/game_mechanics/company/company_progression_util.tl")
	local company = ug_require("::/game_mechanics/company/company_util.tl")
	local status = progression.getCompanyProgressionState(player)
	readings.experience = status.experience
	readings.earned_level = progression.getLevelAndFraction(company.getBasePopulation(), status.experience)

	local transported = api.engine.util.headquarters.getTransportedData()
	readings.passengers, readings.cargo = transported.passengersTransported, transported.cargoTransported

	readings.line_modes = {}
	for _, line in ipairs(api.engine.system.lineSystem.getLinesForPlayer(player)) do
		local component = api.engine.getComponent(line, api.type.ComponentType.LINE)
		local modes = component and component.vehicleInfo and component.vehicleInfo.transportModes
		if modes then
			for index, active in pairs(modes) do
				if active == true then readings.line_modes[index] = true end
			end
		end
	end

	readings.delivered = {}
	for short, id in pairs(cargo_ids()) do
		local value = api.engine.util.logbook.getLogValueMostRecent(player, "itemsTransported" .. tostring(id))
		if value and value > 0 then readings.delivered[short] = value end
	end
	return readings
end

-- ===== effects =====

local function book_money(player, amount, on_done)
	local entry = api.type.JournalEntry.new()
	entry.amount = amount
	entry.time = -1
	entry.category.type = (amount >= 0) and api.type.JournalEntry.Type.INCOME or api.type.JournalEntry.Type.OTHER
	api.cmd.sendCommand(api.cmd.makeJournalBookAssetCmd(player, entry, api.type.Vec3f.new(0, 0, 0)), on_done)
end

local function apply_next_effect(player, inbox)
	if state.inflight then return end
	local pending = effects.pending(inbox.effects, state.applied)
	local effect = pending[1]
	if not effect then return end
	local function done(id)
		state.applied = id
		state.inflight = false
		guarded("outbox", write_outbox) -- persist the cursor immediately so a crash cannot repeat the effect
	end
	state.inflight = true
	if effect.kind == "money" then
		book_money(player, effect.amount, function(_, success) if success then done(effect.id) else state.inflight = false end end)
	elseif effect.kind == "money_loss" then
		book_money(player, -effect.amount, function(_, success) if success then done(effect.id) else state.inflight = false end end)
	elseif effect.kind == "loan" then
		local loan = ug_require("::/game_mechanics/finance/loan_util.tl").createSmallLoan()
		api.cmd.sendCommand(api.cmd.makeScriptingSendEventCmd("", "Loan", "Obtain", { loan, loan }))
		done(effect.id)
	else
		say("unknown effect kind " .. tostring(effect.kind) .. ", skipped")
		done(effect.id)
	end
end

local function apply_level(items, earned)
	local wanted = effects.granted_level(items, earned)
	if state.enforced == wanted then return end
	local repo = api.res.genericRep
	local id = repo.find("::/game_mechanics/company/company_growth_config.res")
	local config = repo.getAsTable(id)
	config.data = config.data or {}
	config.data.enforcedLevel = wanted
	repo.setAsTable(id, config)
	state.enforced = wanted
end

-- ===== main loop =====

local function tick()
	if type(app) ~= "table" then return end
	local now = os.time()
	if now - state.last_tick < TICK_SECONDS then return end
	state.last_tick = now
	if not locks then guarded("modules", load_modules) end
	if not locks then return end

	local inbox = guarded("inbox", read_inbox)
	local items = inbox and inbox.items or {}
	guarded("locks", apply_locks, items) -- without an inbox the start state is enforced: everything locked but the road
	if not inbox then return end

	adopt_seed(inbox.seed)
	local player = api.engine.util.getPlayer()
	local readings = guarded("readings", take_readings, player)
	if readings then
		guarded("level", apply_level, items, readings.earned_level)
		local result = checks.evaluate(inbox.config or {}, readings)
		state.checks = checks.merge_monotonic(state.checks, result.checks)
		state.goals = result.goals
	end
	guarded("effects", apply_next_effect, player, inbox)
	guarded("outbox", write_outbox)
end

function data()
	return {
		update = function(_userParams, _state, _dt) end,
		handleEvent = function(_userParams, _state, _src, _id, _name, _param) end,
		guiUpdate = function(...) guarded("tick", tick) end,
		guiHandleEvent = function(...) end,
	}
end
