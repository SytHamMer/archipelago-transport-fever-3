-- Archipelago for Transport Fever 3: the mod's main loop (GUI context).
-- Every 2 seconds: read the inbox, apply locks / level / one-shot effects, evaluate checks, write the outbox.
-- The game gives mods no file or network access, so everything goes through app.loadUserdata/saveUserdata
-- in the "towns_industries" folder, which the game accepts for mods.
local MOD = "archipelago_tf3_1"
local DIR = "towns_industries"
local INBOX, OUTBOX_PREFIX = "archipelago_tf3_inbox", "archipelago_tf3_outbox_" -- one outbox per seed
local TICK_SECONDS = 2
local CATALOG_RETRY_SECONDS = 30 -- wait before building the catalog again after a failure
local FORMAT_VERSION = 1
local ERAS = { B = 1920, C = 1960 } -- first years of vehicle era B and C

-- Menu and vehicle catalog per mode. Fragments are searched in the game's resource names (plain find).
local MODES = {
	-- `streets` are locked together with the mode; `types` (street templates) and `con_types` (constructions such as
	-- interchanges) are tiered by year and released by the mode's `type_item`, on top of the mode itself.
	-- `tools` are released one by one by their item (and need their mode): `tags` are exact resource names, `cons`
	-- and `edges` are fragments searched in the construction and edge decoration resources.
	-- `era_cons` are the depots and stations that come in several eras (a mode that is not locked has no `cons`).
	road = { vehicles = { "bus", "truck", "car" }, type_item = "Progressive Road Types",
		era_cons = { "/depots/road/road_depot/", "/depots/road/road_maint_station", "/stations/street/small_stops/",
			"/stations/street/modular_street_station/" },
		types = { "/infrastructure/street/country/", "/infrastructure/street/town/", "/infrastructure/street/highway/" },
		con_types = { "/infrastructure/street_construction/" },
		tools = {
			{ item = "Tool: Bus Lanes", tags = { "::/gui/construction/tools/bus_lane_tool.res" } },
			{ item = "Tool: Noise Barriers", edges = { "/infrastructure/edge_addons/barrier" } },
		} },
	tram = { cons = { "/depots/road/tram_depot/" }, streets = { "/infrastructure/street/tram/" }, vehicles = { "tram" },
		tools = { { item = "Tool: Tram Tracks", tags = { "::/gui/construction/tools/tram_track_tool.res" } } } },
	rail = { cons = { "/stations/rail/", "/depots/rail/" }, meta = { "/stations/rail/" }, era_cons = { "/depots/rail/" },
		vehicles = { "train", "waggon" }, type_item = "Progressive Rail Tracks", types = { "/infrastructure/track/" },
		tools = {
			{ item = "Tool: Rail Signals", cons = { "/infrastructure/signal/" } },
			{ item = "Tool: Electrification", tags = { "::/gui/construction/tools/rail_electrification_tool.res" } },
		} },
	water = { cons = { "/stations/water/", "/depots/water/" }, meta = { "/stations/water/" }, era_cons = { "/depots/water/" },
		vehicles = { "ship" } },
	air = { cons = { "/stations/air/airfield", "/stations/air/airport", "/depots/air/" }, meta = { "/stations/air/" },
		streets = { "/infrastructure/street/airport/" }, vehicles = { "plane", "helicopter", "zeppelin" } },
}
local TEMPLATE_SUFFIXES = 12 -- constructions are tagged "name@0" .. "name@11" in the menu

local locks, checks, effects, notify, contract_sync, loans, years

local state = {
	last_tick = 0,
	catalog = nil,
	last_menu = nil, last_vehicles = nil,
	seed = nil, checks = {}, goals = {}, missions = {}, applied = 0, applied_deaths = 0, year = nil, years_freed = false,
	messages = {}, -- notifications waiting to be sent (DeathLink losses)
	enforced = nil,
	inflight = false,
	failures = {}, -- failed attempts per effect id
	last_notified = nil, -- items and checks as of the last tick; nil until the first tick of a seed (silent baseline)
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
	locks, checks, effects, notify = load("ap_locks"), load("ap_checks"), load("ap_effects"), load("ap_notify")
	contract_sync = load("ap_contract_sync")
	loans = load("ap_loans")
	years = load("ap_years")
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

-- Cargo classes a vehicle model declares (BULK, FLATBED, GOODS, LIQUID, UNIVERSAL, PASSENGERS), without duplicates.
local function cargo_classes(model)
	local seen, out = {}, {}
	local vehicle = model and model.metadata and model.metadata.transportVehicle
	for _, compartment in ipairs(vehicle and vehicle.compartments or {}) do
		for _, load in ipairs(compartment.loadConfigs or {}) do
			local set = load.cargoEntry and load.cargoEntry.cargoTypeSet
			for _, class in ipairs(set and set.cargoClassesIncluded or {}) do
				local name = tostring(class)
				if not seen[name] then seen[name] = true out[#out + 1] = name end
			end
		end
	end
	return out
end

local function vehicles_of(kinds)
	local out = {}
	api.res.modelRep.forEachModelWithMetadata("transportVehicle", function(path)
		for _, kind in ipairs(kinds) do
			if path:find("/vehicle/" .. kind .. "/", 1, true) or path:find("^vehicle/" .. kind .. "/") then
				local id = api.res.modelRep.find(path)
				local table_ = api.res.modelRep.getAsTable(id)
				local availability = table_ and table_.metadata and table_.metadata.availability
				out[#out + 1] = { path = path, year = years.original(availability), classes = cargo_classes(table_),
					freed = years.freed(availability) }
				break
			end
		end
	end)
	return out
end

-- Street templates matching the fragments, each with its first year (nil counts as the first tier).
local function street_types(fragments)
	local out = {}
	local rep = api.res.streetTemplateRep
	for id, name in pairs(rep.getAll(true)) do
		if type(name) == "string" then
			for _, fragment in ipairs(fragments) do
				if name:find(fragment, 1, true) then
					local table_ = rep.getAsTable(id)
					local availability = table_ and table_.availability
					out[#out + 1] = { tag = name, year = years.original(availability) }
					break
				end
			end
		end
	end
	return out
end

-- The era variants of the constructions matching the fragments (depots, stations).
-- * A depot or maintenance station is one construction with three templates (1900, 1940, 1980), the menu entries
--   "<name>@0", "@1", "@2". The game cannot hand the templates over as a table (reading them fails), but they all follow
--   that order, so the later ones are tiered by their index.
-- * Other stations, such as the small bus stops, are separate constructions with their own first year.
local ERA_TEMPLATE_YEARS = { [1] = 1940, [2] = 1980 }
-- The street terminal (bus, truck and tram platforms) has six templates: three passenger ones, then three cargo ones,
-- each trio in the eras 1900, 1950 and 1990.
local TERMINAL_TEMPLATE_YEARS = { [1] = 1950, [2] = 1990, [4] = 1950, [5] = 1990 }

local function construction_variants(fragments)
	local out = {}
	local rep = api.res.constructionRep
	for id, name in pairs(rep.getAll(true)) do
		if type(name) == "string" then
			for _, fragment in ipairs(fragments) do
				if name:find(fragment, 1, true) then
					local read, table_ = pcall(rep.getAsTable, id)
					if read and type(table_) == "table" then
						local year = years.original(table_.availability)
						if year and year > 0 then out[#out + 1] = { tag = name, year = year } end
					else
						local template_years = name:find("modular_terminal", 1, true) and TERMINAL_TEMPLATE_YEARS or ERA_TEMPLATE_YEARS
						for index, year in pairs(template_years) do
							out[#out + 1] = { tag = name .. "@" .. index, year = year }
						end
					end
					break
				end
			end
		end
	end
	return out
end

-- Constructions matching the fragments, each with its first year (interchanges, roundabouts).
local function construction_types(fragments)
	local out = {}
	local rep = api.res.constructionRep
	for id, name in pairs(rep.getAll(true)) do
		if type(name) == "string" then
			for _, fragment in ipairs(fragments) do
				if name:find(fragment, 1, true) then
					local table_ = rep.getAsTable(id)
					local availability = table_ and table_.availability
					out[#out + 1] = { tag = name, year = years.original(availability) }
					break
				end
			end
		end
	end
	return out
end

-- The tools of a mode with the menu tags each one releases.
local function tool_list(defs)
	local out = {}
	for _, def in ipairs(defs or {}) do
		local tags = {}
		for _, tag in ipairs(def.tags or {}) do tags[#tags + 1] = tag end
		scan(api.res.constructionRep, def.cons or {}, false, tags)
		scan(api.res.edgeDecorationRep, def.edges or {}, false, tags)
		out[#out + 1] = { item = def.item, tags = tags }
	end
	return out
end

local function build_catalog()
	local catalog = { eras = ERAS, modes = {} }
	for mode, def in pairs(MODES) do
		local menu = {}
		scan(api.res.constructionRep, def.cons or {}, true, menu)
		scan(api.res.metaConstructionRep, def.meta or {}, false, menu)
		scan(api.res.streetTemplateRep, def.streets or {}, false, menu)
		local types = street_types(def.types or {})
		for _, entry_type in ipairs(construction_types(def.con_types or {})) do types[#types + 1] = entry_type end
		catalog.modes[mode] = { menu = menu, vehicles = vehicles_of(def.vehicles),
			type_item = def.type_item, types = types, tools = tool_list(def.tools),
			variants = construction_variants(def.era_cons or def.cons or {}) }
	end
	return catalog
end

-- Diagnostic report of what the game contains, written once to the log (lines start with "ARCHIPELAGO catalog").
local function catalog_report(catalog)
	local freed, total = 0, 0
	for _, entry in pairs(catalog.modes) do
		for _, vehicle in ipairs(entry.vehicles or {}) do
			total = total + 1
			if vehicle.freed then freed = freed + 1 end
		end
	end
	say("catalog dates freed by the mod: " .. freed .. " of " .. total .. " vehicles (the rest was available from the start)")
	local function keys_of(table_)
		local names = {}
		if type(table_) == "table" then for key in pairs(table_) do names[#names + 1] = tostring(key) end end
		table.sort(names)
		return table.concat(names, ",")
	end
	local function names_matching(rep, fragments, limit)
		local out = {}
		for id, name in pairs(rep.getAll(true)) do
			if type(name) == "string" then
				for _, fragment in ipairs(fragments) do
					if name:find(fragment, 1, true) then out[#out + 1] = name break end
				end
			end
		end
		table.sort(out)
		local shown = {}
		for index = 1, math.min(#out, limit) do shown[index] = out[index] end
		return #out, table.concat(shown, " | ")
	end

	for mode, entry in pairs(catalog.modes) do
		local histogram = {}
		for _, entry_type in ipairs(entry.types or {}) do
			local key = tostring(entry_type.year)
			histogram[key] = (histogram[key] or 0) + 1
		end
		local parts = {}
		for key, count in pairs(histogram) do parts[#parts + 1] = key .. ":" .. count end
		table.sort(parts)
		local classes = {}
		for _, vehicle in ipairs(entry.vehicles) do
			local key = table.concat(vehicle.classes or {}, "+")
			classes[key] = (classes[key] or 0) + 1
		end
		local class_parts = {}
		for key, count in pairs(classes) do class_parts[#class_parts + 1] = (key == "" and "none" or key) .. ":" .. count end
		table.sort(class_parts)
		say("catalog " .. mode .. " vehicle classes{" .. table.concat(class_parts, " ") .. "}")
		local sample = {}
		for index, variant in ipairs(entry.variants or {}) do
			if index <= 6 then sample[#sample + 1] = tostring(variant.tag):match("([^/]+)$") .. ":" .. tostring(variant.year) end
		end
		say("catalog " .. mode .. " era variants: " .. #(entry.variants or {}) .. " " .. table.concat(sample, " "))
		say("catalog " .. mode .. ": types=" .. #(entry.types or {}) .. " years{" .. table.concat(parts, " ") .. "} menu=" .. #entry.menu
			.. " vehicles=" .. #entry.vehicles)
	end
	local rep = api.res.streetTemplateRep
	for id, name in pairs(rep.getAll(true)) do
		if type(name) == "string" and name:find("country_old_small", 1, true) then
			local table_ = rep.getAsTable(id)
			say("catalog sample " .. name .. " keys{" .. keys_of(table_) .. "} availability{" .. keys_of(table_ and table_.availability)
				.. "} yearFrom=" .. tostring(table_ and table_.availability and table_.availability.yearFrom))
			break
		end
	end
	local count, names = names_matching(api.res.constructionRep, { "/infrastructure/street_construction/" }, 12)
	say("catalog street constructions: " .. count .. " " .. names)
	count, names = names_matching(api.res.genericRep, { "/gui/construction/tools/" }, 25)
	say("catalog tools: " .. count .. " " .. names)
	count, names = names_matching(api.res.edgeDecorationRep, { "barrier", "noise" }, 15)
	say("catalog noise barriers: " .. count .. " " .. names)
	count, names = names_matching(api.res.constructionRep, { "/infrastructure/signal/" }, 12)
	say("catalog signals: " .. count .. " " .. names)
end

-- ===== inbox / outbox =====

local function read_inbox()
	local inbox = app.loadUserdata(DIR, INBOX)
	if type(inbox) ~= "table" or inbox.version == nil then return nil end
	if not checks.format_supported(inbox.version, FORMAT_VERSION) then
		problem("inbox", "format " .. tostring(inbox.version) .. " is newer than this mod understands: update the mod")
		return nil
	end
	return inbox
end

-- The outbox file name carries the seed (same character rule as the client), so seeds never share progress:
-- going back to an earlier seed finds its own checks and effect cursor again.
local function outbox_name(seed)
	return OUTBOX_PREFIX .. (tostring(seed):gsub("[^%w_%-]", "_"))
end

local function adopt_seed(seed)
	if state.seed == seed then return end
	-- A different seed means a different game: start from the outbox of that seed, or from nothing.
	state.seed = seed
	state.checks, state.goals, state.missions, state.applied, state.failures = {}, {}, {}, 0, {}
	state.applied_deaths, state.messages = 0, {}
	state.last_notified = nil -- a new seed starts a new silent baseline
	state.spawned = nil
	state.sent_loan_scale = nil
	local previous = app.loadUserdata(DIR, outbox_name(seed))
	if type(previous) == "table" and previous.seed == seed then
		state.checks = previous.checks or {}
		state.goals = previous.goals or {}
		state.missions = previous.missions or {}
		state.applied = previous.applied or 0
		state.applied_deaths = previous.applied_deaths or 0
	end
end

local function write_outbox()
	if not state.seed then return end
	app.saveUserdata(DIR, outbox_name(state.seed), {
		version = FORMAT_VERSION, seed = state.seed, checks = state.checks, goals = state.goals, missions = state.missions,
		applied = state.applied, applied_deaths = state.applied_deaths, heartbeat = os.time(), year = state.year, years_freed = state.years_freed,
	})
end

-- ===== locks =====

local function apply_locks(items, eras)
	if not state.catalog then
		-- a failed build is not retried on every tick: the game stays unlocked, so wait before trying again
		if state.catalog_retry_at and os.time() < state.catalog_retry_at then return end
		local built, catalog = pcall(build_catalog)
		if not built then
			state.catalog_retry_at = os.time() + CATALOG_RETRY_SECONDS
			error(catalog, 0)
		end
		state.catalog = catalog
		for _, entry in pairs(catalog.modes) do
			for _, vehicle in ipairs(entry.vehicles or {}) do
				if vehicle.freed then state.years_freed = true end
			end
		end
		guarded("catalog report", catalog_report, state.catalog)
	end
	state.catalog.eras = eras or ERAS
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
	if not status then return nil end -- the company is not ready yet right after the game loads
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

-- Uids of the missions (the game's "subventions") the game lists as completed. Empty when they cannot be read.
local function completed_mission_uids()
	local uids = {}
	local script = api.engine.system.gameScriptSystem.getEntityForGameScript("::/game_mechanics/subventions/subventions.gs")
	local component = script and api.engine.getComponent(script, api.type.ComponentType.GAME_SCRIPT)
	local list = component and component.state_native and component.state_native:find("completedSubventions")
	local entries = {}
	for _, entry in pairs(list and list:asTable() or {}) do
		if type(entry) == "table" then entries[#entries + 1] = { id = tostring(entry.id), uid = entry.uid } end
	end
	return checks.foreign_mission_uids(entries)
end

-- ===== effects =====

local function book_money(player, amount, on_done)
	local entry = api.type.JournalEntry.new()
	entry.amount = amount
	entry.time = -1
	entry.category.type = (amount >= 0) and api.type.JournalEntry.Type.INCOME or api.type.JournalEntry.Type.OTHER
	api.cmd.sendCommand(api.cmd.makeJournalBookAssetCmd(player, entry, api.type.Vec3f.new(0, 0, 0)), on_done)
end

-- Applies the next effect of `list` that the cursor `state[field]` has not passed: the effects of the received items
-- (`applied`) or the DeathLink losses (`applied_deaths`, ids that come from the time of the death).
local function apply_next_effect(player, list, field)
	if state.inflight then return end
	local effect = effects.pending(list, state[field])[1]
	if not effect then return end
	local seed = state.seed -- a callback arriving after a seed change must not move the new seed's cursor

	local function release()
		state.inflight = false
	end
	local function done(id)
		release()
		if state.seed ~= seed then return end
		state[field] = id
		guarded("outbox", write_outbox) -- persist the cursor immediately so a crash cannot repeat the effect
	end
	-- A failing effect is retried a few times, then skipped, so it can never block the effects after it.
	local function failed(reason)
		release()
		problem("effect " .. tostring(effect.id), reason)
		if state.seed == seed and effects.register_failure(state.failures, effect.id) then
			say("effect " .. tostring(effect.id) .. " given up after repeated failures")
			done(effect.id)
		end
	end
	local function on_money(_, success)
		if not success then failed("the game refused the command") return end
		if field == "applied_deaths" and state.seed == seed then
			state.messages[#state.messages + 1] = notify.death_message(effect)
		end
		done(effect.id)
	end

	state.inflight = true
	local ok, err = pcall(function()
		-- the amounts are in 1900 money: the game's prices (and so their weight) follow the year of the game
		local amount = effects.scale_money(effect.amount or 0, api.engine.util.getYear())
		if effect.kind == "money" then
			book_money(player, amount, on_money)
		elseif effect.kind == "money_loss" or field == "applied_deaths" then
			book_money(player, -amount, on_money)
		else
			say("unknown effect kind " .. tostring(effect.kind) .. ", skipped")
			done(effect.id)
		end
	end)
	if not ok then failed(err) end
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

-- ===== notifications =====

local NOTIFICATION_TYPE = MOD .. "::/ap_notification.script"
local NOTIFICATION_SECONDS = 8

local function send_notification(message)
	api.cmd.sendCommand(api.cmd.makeScriptingSendEventCmd("", "Notifications", "add", {
		type = NOTIFICATION_TYPE,
		params = { title = message.title, text = message.text },
		autoDismissDuration = NOTIFICATION_SECONDS * 1000,
	}))
end

-- Every open contract (check) is a real game subvention, so the game shows its own contract window, icon and
-- notification for it. A reached check accepts and finishes its subvention: the player never has to accept it.
local SUBVENTION_RES = MOD .. "::/ap_subvention.res"

-- Uids of the subventions the game lists as proposed, active or completed.
local function listed_subvention_uids()
	local uids = {}
	local script = api.engine.system.gameScriptSystem.getEntityForGameScript("::/game_mechanics/subventions/subventions.gs")
	local component = script and api.engine.getComponent(script, api.type.ComponentType.GAME_SCRIPT)
	local native = component and component.state_native
	if not native then return uids end
	for _, name in ipairs({ "proposedSubventions", "activeSubventions", "completedSubventions" }) do
		local list = native:find(name)
		for _, entry in pairs(list and list:asTable() or {}) do
			if type(entry) == "table" and type(entry.uid) == "number" then uids[#uids + 1] = entry.uid end
		end
	end
	return uids
end

local function sync_contracts(inbox)
	if not inbox.contracts then return end
	state.spawned = state.spawned or {}
	state.sync_tick = (state.sync_tick or 0) + 1
	local open = notify.open_contracts(inbox.contracts, state.checks, inbox.config)
	local actions = contract_sync.plan(open, state.checks, state.spawned, listed_subvention_uids(), state.sync_tick)
	local function send(event, name, param)
		api.cmd.sendCommand(api.cmd.makeScriptingSendEventCmd("", event, name, param))
	end
	for _, spawn in ipairs(actions.spawn) do
		send("Subvention", "subventionSpawn", {
			name = SUBVENTION_RES,
			specific = { uid = spawn.uid, expireDurationProposed = -1, task = spawn.title, reward = spawn.text,
				progress = spawn.progress },
		})
	end
	for _, accept in ipairs(actions.accept) do send("Subvention", "onAccept", { uid = accept.uid }) end
	for _, done in ipairs(actions.reached) do
		send("ArchipelagoContract", "reached", { uid = done.uid })
		say("contract finished: " .. done.key)
	end
end

-- ===== bank loans =====
-- The loans are made by the game's loan script (simulation side): their amounts are scaled by wrapping the functions
-- that make them. The GUI side sends the wanted percentage as an event; the simulation side keeps it in its state so
-- that it is applied again after a load. Loans the game already made keep their amount until it renews them.

-- The game makes its first four loans when the game is created, before the mod can read the YAML value: the
-- replacement is installed as soon as the script is loaded, with this default (the default of the loan_scale option,
-- which leaves the game's own amounts as they are).
local DEFAULT_LOAN_PERCENT = 100

local LOAN_MAKERS = { "createSmallLoan", "createMediumLoan", "createLargeLoan", "createExtraLargeLoan" }

local function patch_loans(percent)
	if not loans then load_modules() end
	local loan_util = ug_require("::/game_mechanics/finance/loan_util.tl")
	if not loan_util.archipelago_wrapped then
		loan_util.archipelago_wrapped = true
		for _, name in ipairs(LOAN_MAKERS) do
			local original = loan_util[name]
			loan_util[name] = function(...)
				local loan = original(...)
				loan.amount = loans.scale_amount(loan.amount, loan_util.archipelago_percent)
				return loan
			end
		end
	end
	loan_util.archipelago_percent = percent
end

-- GUI side: tell the simulation side the wanted percentage whenever it changes.
local function send_loan_scale(inbox)
	local percent = inbox.config and inbox.config.loan_scale
	if type(percent) ~= "number" or percent == state.sent_loan_scale then return end
	state.sent_loan_scale = percent
	api.cmd.sendCommand(api.cmd.makeScriptingSendEventCmd("", "ArchipelagoLoans", "scale", { percent = percent }))
	say("loan scale sent: " .. percent)
end

-- Tells the player about received items and sent checks. The first tick of a seed only records what is already
-- there, so reloading a game does not replay everything.
local function notify_changes(inbox)
	local items, ids = {}, {}
	for name, count in pairs(inbox.items or {}) do items[name] = count end
	for _, id in ipairs(state.checks) do ids[#ids + 1] = id end
	local current = { items = items, checks = ids }
	if inbox.log then
		current.log = inbox.log
		current.log_size = #inbox.log
	end
	local messages = notify.diff(state.last_notified, current, inbox.config, nil, inbox.contracts)
	state.last_notified = current
	for _, message in ipairs(state.messages) do messages[#messages + 1] = message end -- DeathLink losses
	state.messages = {}
	for _, message in ipairs(messages) do
		local ok, err = pcall(send_notification, message)
		if not ok then problem("notification", err) break end
	end
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
	guarded("locks", apply_locks, items, inbox and inbox.config and inbox.config.eras) -- without an inbox the start state is enforced: everything locked but the road
	if not inbox then return end

	adopt_seed(inbox.seed)
	state.year = guarded("year", function() return api.engine.util.getYear() end)
	local player = api.engine.util.getPlayer()
	local readings = guarded("readings", take_readings, player)
	if readings then
		state.missions = checks.merge_missions(state.missions, guarded("missions", completed_mission_uids) or {})
		readings.missions = #state.missions
		guarded("level", apply_level, items, readings.earned_level)
		local result = checks.evaluate(inbox.config or {}, readings)
		state.checks = checks.merge_monotonic(state.checks, result.checks)
		state.goals = checks.merge_goals(state.goals, result.goals)
	end
	guarded("effects", apply_next_effect, player, inbox.effects, "applied")
	guarded("deaths", apply_next_effect, player, inbox.deaths, "applied_deaths")
	guarded("notify", notify_changes, inbox)
	guarded("sync", sync_contracts, inbox)
	guarded("loans", send_loan_scale, inbox)
	guarded("outbox", write_outbox)
end

pcall(patch_loans, DEFAULT_LOAN_PERCENT)

function data()
	return {
		update = function(_userParams, game_state, _dt)
			if not game_state:hasEventSubscriptions() then game_state:subscribeToEvent("scale") end
			local saved = game_state:get()
			local percent = type(saved) == "table" and saved.loan_percent or nil
			if percent then
				local ok, loan_util = pcall(ug_require, "::/game_mechanics/finance/loan_util.tl")
				if ok and loan_util.archipelago_percent ~= percent then pcall(patch_loans, percent) end
			end
		end,
		handleEvent = function(_userParams, game_state, _src, id, name, param)
			if id == "ArchipelagoLoans" and name == "scale" and type(param) == "table" and type(param.percent) == "number" then
				game_state:set({ loan_percent = param.percent })
				pcall(patch_loans, param.percent)
			end
		end,
		guiUpdate = function(...) guarded("tick", tick) end,
		guiHandleEvent = function(...) end,
	}
end
