-- EXPERIMENT: game side of an Archipelago contract that is a real game subvention (see ap_subvention.res.lua).
-- It is never spawned by the game itself (canSpawn is false): ap_main.script.lua spawns it with the
-- "subventionSpawn" event, and reports the check as reached with an "ArchipelagoContract"/"reached" event.
local subvention_util = ug_require("/game_mechanics/subventions/subvention_util.tl")

local ICON = "archipelago_tf3_1::/ap_icon.tga"
local FOREVER_MONTHS = 1200 -- no deadline: a hundred years

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

	getRelevantEntities = function() return {}, {} end,
	getRelevantEntityNames = function() return {} end,

	-- The card the game shows: the task as the description, what completing it gives under "on completion".
	getCardData = function(state)
		local card = subvention_util.makeDefaultCardData(state, ICON)
		card.description = state.data.task or ""
		card.deadline, card.expireDuration = nil, nil
		card.upfront, card.failure = {}, {}
		card.complete = { { text = state.data.reward or "" } }
		return card
	end,
}

return {
	ap_contract = contract,
}
