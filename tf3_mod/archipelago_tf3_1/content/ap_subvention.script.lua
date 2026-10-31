-- EXPERIMENT: game side of an Archipelago contract that is a real game subvention (see ap_subvention.res.lua).
-- It is never spawned by the game itself (canSpawn is false): ap_main.script.lua spawns it with the
-- "subventionSpawn" event, and reports the check as reached with an "ArchipelagoContract"/"reached" event.
local subvention_util = ug_require("::/game_mechanics/subventions/subvention_util.tl")

local ICON = "archipelago_tf3_1::/ap_icon.tga"
local FOREVER_MONTHS = 1200 -- no deadline: a hundred years

-- The game only shows an offer (notification, icon, window) that points at an entity of the world: the first town.
local function anchor_town()
	local town
	api.engine.forEachEntityWithComponent(function(entity)
		if not town then town = entity end
	end, api.type.ComponentType.TOWN)
	return town
end

local function cargo_id(short)
	for id, name in pairs(api.res.cargoTypeRep.getAll()) do
		if tostring(name):match("/cargos/([^/]+)/") == short then return id end
	end
end

-- The current value of what a contract follows ({ kind, goal, cargo? }), or nil when it cannot be read.
local function current_value(spec)
	local player = api.engine.util.getPlayer()
	if spec.kind == "passengers" or spec.kind == "cargo" then
		local transported = api.engine.util.headquarters.getTransportedData()
		return spec.kind == "passengers" and transported.passengersTransported or transported.cargoTransported
	elseif spec.kind == "delivered" then
		local id = cargo_id(spec.cargo)
		return id and api.engine.util.logbook.getLogValueMostRecent(player, "itemsTransported" .. tostring(id)) or 0
	end
	local progression = ug_require("::/game_mechanics/company/company_progression_util.tl")
	local status = progression.getCompanyProgressionState(player)
	if not status then return nil end
	if spec.kind == "population" then return status.experience end
	if spec.kind == "company_level" then
		local company = ug_require("::/game_mechanics/company/company_util.tl")
		return (progression.getLevelAndFraction(company.getBasePopulation(), status.experience))
	end
end

local function with_separators(number)
	local digits = tostring(math.floor(number))
	local out = digits:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end

-- "35 / 100" for a contract that follows a number, nil otherwise.
local function progress_text(spec)
	if type(spec) ~= "table" or not spec.goal then return nil end
	local ok, value = pcall(current_value, spec)
	if not ok or type(value) ~= "number" then return nil end
	return with_separators(math.min(value, spec.goal)) .. " / " .. with_separators(spec.goal), math.min(1, value / spec.goal)
end

local function text_of(params)
	return params and params.text or ""
end

local contract = {
	handleLegacy = function(state) return state end,

	canSpawn = function() return false end,
	onSpawn = function() return nil, nil end,

	-- param = { uid, expireDurationProposed = -1, task, reward } sent by ap_main.script.lua
	spawnSpecific = function(param)
		local state = subvention_util.makeDefaultSubventionTemplate(param.task or "Archipelago contract")
		state.expireDurationProposed = -1
		state.expireDuration = api.util.getDefaultMonthDuration() * FOREVER_MONTHS
		state.effectDuration = api.util.getDefaultMonthDuration() * 6
		state.upfront, state.failure, state.complete = {}, {}, {}
		state.task = param.task
		state.progress = param.progress
		state.reward = param.reward
		state.reached = false
		return state, param.uid
	end,

	isComplete = function(state) return state.data.reached == true end,

	onAccept = function() end,
	onFailure = function() end,
	onComplete = function() end,
	onUpdate = function() end,
	shouldDespawn = function(state, now) return subvention_util.defaultTimeout(state, now) end,
	onDespawn = function() end,

	eventsToHandle = function() return { "reached" } end,
	handleEvent = function(_src, id, name, param, state)
		if id == "ArchipelagoContract" and name == "reached" and param and param.uid == state.uid then
			state.data.reached = true
		end
	end,

	getNotificationParams = function(state)
		return { task = state.data.task, reward = state.data.reward }
	end,

	getNotificationData = function(subventionId, params, status, reason)
		return subvention_util.makeDefaultNotificationData(status, reason, subvention_util.getIcon(subventionId, status),
			function() return text_of({ text = (params.task or "") .. " - " .. (params.reward or "") }) end)
	end,

	getNotificationMissedData = function(subventionId, _params, reason)
		return subvention_util.makeDefaultMissedNotificationData(reason, subvention_util.getIcon(subventionId, "Failed"),
			function() return "" end)
	end,

	getRelevantEntities = function()
		local town = anchor_town()
		return town and { town } or {}, {}
	end,
	getRelevantEntityNames = function()
		local town = anchor_town()
		return town and { [town] = api.engine.util.getEntityName(town) or "" } or {}
	end,

	-- The card the game shows: the task as the description, what completing it gives under "on completion".
	getCardData = function(state)
		local card = subvention_util.makeDefaultCardData(state, ICON)
		local text, fraction = progress_text(state.data.progress)
		card.description = (state.data.task or "") .. (text and (" (" .. text .. ")") or "")
		if text and card.status == "Active" then card.progress = { value = fraction, text = text } end
		card.deadline, card.expireDuration = nil, nil
		card.upfront, card.failure = {}, {}
		card.complete = { { text = state.data.reward or "" } }
		local town = anchor_town()
		if town then card.location = { to = { town, api.engine.util.getEntityName(town) or "" } } end
		return card
	end,
}

-- The game loads a script resource through its data(); the module is returned as well for loaders that read the chunk.
local module = { ap_contract = contract }

function data()
	return module
end

return module
