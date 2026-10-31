-- An Archipelago contract (a check) as a real game subvention, so the game shows its own contract window.
function data()
	local icon = "archipelago_tf3_1::/ap_icon.tga"
	return {
		type = "subvention",
		data = {
			scriptFile = "archipelago_tf3_1::/ap_subvention.script@ap_contract",
			icons = {
				fallback = icon,
				proposed = icon,
				active = icon,
				complete = icon,
				failed = icon,
			},
		},
	}
end
