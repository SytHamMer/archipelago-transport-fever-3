-- Notification type used by the mod for received items and sent checks (the game's own ones look the same).
function data()
	return {
		type = "notification",
		data = {
			guiType = "Info",
			label = _("Archipelago"),
			initiallyIgnoredType = false,
		},
	}
end
