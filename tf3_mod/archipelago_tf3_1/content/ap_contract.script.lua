-- GUI side of an open contract: the parameters are { title, text } built by ap_notify.open_contracts.
local contract = {}

contract.useDataState = function(params)
	return {
		title = params and params.title or "Archipelago contract",
		description = params and params.text or "",
		icon = "archipelago_tf3_1::/ap_icon.tga",
		hudIcon = "archipelago_tf3_1::/ap_icon.tga",
		status = "Pending",
	}
end

function data()
	return contract
end

return contract
