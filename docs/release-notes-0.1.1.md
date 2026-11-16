# Transport Fever 3 x Archipelago 0.1.1

Second public test version of the unofficial Archipelago world for Transport Fever 3 (PC, Steam). It fixes a gap found by
testers and makes the documentation clearer about the game's own subsidies. It is still not part of the official
Archipelago repository.

## Files

- `transport_fever_3.apworld`: the world (Launcher, **Install APWorld**).
- `archipelago_tf3_1.zip`: the mod; extract it into `...\3493540\local\mods\` with the game closed (or
  `python scripts/install_mod.py --update` from a clone).

Update both files: the world only changes its version number, the mod carries the fix. The installation guide is
[guide-installation.md](guide-installation.md). Needs Archipelago 0.6.x (tested with 0.6.8).

## What changed

- **Items received while the game was closed are now announced** when you load the save
  ([issue #1](https://github.com/SytHamMer/archipelago_tf3/issues/1)). Before, they were applied but never shown. Up to
  5 items are announced one by one; beyond that, one "Archipelago: items received" notification lists the item names
  with their count (the first four, then "and N more"). These notifications stay on screen 30 seconds. Nothing already
  announced is announced again. Type `/received` in the client to list every item received.
- **Documentation: do NOT accept the Archipelago contracts.** You never need to: a check is reached without it. The game
  only proposes its own subsidies while fewer than 5 contracts are active, and ours count, so accepting them can stop the
  subsidies from appearing and make the "N missions completed" checks unreachable. If no subsidy appears, check this
  first, or set `mission_checks: 0` in your YAML to remove those checks (the default stays 3).

## Known limits

- The "and N more" of the summary cannot be expanded in the game; an in-game history window is an idea for 0.2.0.
- The mod could keep at most four Archipelago contracts active so a place always stays free for the game's subsidies;
  this is not done yet and needs to be confirmed in game first.
- Everything listed as not verified in the 0.1.0 notes still applies (tram, water and air menus, the first line and
  delivery checks of each mode, the rail tiers).

## Verified for this version

In game, with a one-player multiworld: one item received while the game was closed is announced, a batch of items
received while the game was closed gives one grouped summary, and reloading does not announce anything twice.
