-- GUI side of the notification: turns the parameters sent by ap_main.script.lua into what the player sees.
-- The icon is ap_icon@2x.tga (the game loads "name.tga" from the "name@2x.tga" file).
local notification = {}

notification.useDataState = function(params)
	return {
		title = params and params.title or "Archipelago",
		description = params and params.text or "",
		icon = "archipelago_tf3_1::/ap_icon.tga",
	}
end

-- Defined as well, for loaders that call data() on script resources.
function data()
	return notification
end

return notification
