-- GUI side of an open contract: the parameters are { title, text } built by ap_notify.open_contracts.
local contract = {}

contract.useDataState = function(params)
	return {
		title = "Archipelago contract",
		-- the notifications tab only shows the description: the task first, then what completing it gives
		description = params and ((params.title or "") .. "
" .. (params.text or "")) or "",
		icon = "archipelago_tf3_1::/ap_icon.tga",
		hudIcon = "archipelago_tf3_1::/ap_icon.tga",
		status = "Pending",
	}
end

function data()
	return contract
end

return contract
