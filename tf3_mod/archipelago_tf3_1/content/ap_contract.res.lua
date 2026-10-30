-- Notification type of the open contracts: they stay in the notifications tab until the check is reached.
function data()
	return {
		type = "notification",
		data = {
			guiType = "Opportunity",
			label = _("Archipelago contracts"),
			initiallyIgnoredType = false,
		},
	}
end
