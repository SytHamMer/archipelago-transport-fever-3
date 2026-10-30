-- GUI side of an open contract. The parameters are { title, text, progress } built by ap_notify.open_contracts;
-- `progress` ({ kind, goal, cargo }) says which number the contract follows, and is read live here, so the
-- parameters stay the same while the number moves (the game would replace the notification if they changed).
local contract = {}

local NEWLINE = string.char(10)

local function cargo_id(short)
	for id, name in pairs(api.res.cargoTypeRep.getAll()) do
		if tostring(name):match("/cargos/([^/]+)/") == short then return id end
	end
end

-- The current value of what a contract follows, or nil when it cannot be read.
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

-- { text = "35 / 100", fraction = 0.35 } for a contract that follows a number, nil otherwise.
local function progress_of(spec)
	if type(spec) ~= "table" or not spec.goal then return nil end
	local ok, value = pcall(current_value, spec)
	if not ok or type(value) ~= "number" then return nil end
	local shown = math.min(value, spec.goal)
	return {
		text = with_separators(shown) .. " / " .. with_separators(spec.goal),
		fraction = math.max(0, math.min(1, value / spec.goal)),
	}
end

contract.useDataState = function(params)
	local engine_react_util = ug_require("::/gui/main/engine_react_util.tl")
	local state = engine_react_util.useStepStateTimer(function()
		return { progress = params and progress_of(params.progress) or nil }
	end)
	local progress = state:old().progress

	-- the notifications tab only shows the description: the task (with its progress), then what completing it gives
	local task = (params and params.title or "Archipelago contract") .. (progress and (" (" .. progress.text .. ")") or "")
	return {
		title = "Archipelago contract",
		description = task .. NEWLINE .. (params and params.text or ""),
		icon = "archipelago_tf3_1::/ap_icon.tga",
		hudIcon = "archipelago_tf3_1::/ap_icon.tga",
		status = "Pending",
		progresses = progress and { { percentage = progress.fraction, text = progress.text } } or nil,
	}
end

function data()
	return contract
end

return contract
