# Transport Fever 3 x Archipelago 0.1.0

First public test version of an unofficial Archipelago world for Transport Fever 3 (PC, Steam). It is not part of the
official Archipelago repository: it is published here so that people can try it and report how it plays, before it is
proposed upstream.

## Files

- `transport_fever_3.apworld`: the world (Launcher, **Install APWorld**).
- `archipelago_tf3_1.zip`: the mod; extract it into `...\3493540\local\mods\` with the game closed.

The README and [docs/guide-installation.md](guide-installation.md) describe the installation, and
[docs/playing-with-a-friend.md](playing-with-a-friend.md) a multiworld with another game. Needs Archipelago 0.6.x
(tested with 0.6.8).

## What it does

- The game locks the transport modes, the vehicles by era, road and track types, construction tools and cargo classes
  until the items are received.
- The checks (population, company level, passengers and cargo transported, first lines, deliveries per cargo, missions)
  are shown in the game as real contracts, and sent by the mod itself.
- Money grants, money losses (traps), DeathLink, loans scaled by an option, and any start year.

## What is verified

In game: the road (all vehicle tiers), contracts, notifications, DeathLink, loans, free start year, and a two-player
multiworld, including one with Satisfactory.

Not verified yet: tram, water and air menus, the first line and delivery checks of each mode, the rail tiers.

## Help wanted: balance

The numbers (checks, delivery amounts, money, logic) are a first guess. They can only be polished with feedback from
real games. Please report, in an issue: the YAML (or main options), the start year and climate, what felt too easy, too
hard, too slow or too fast, how long the game lasted, and the lines starting with `ARCHIPELAGO` in
`...\3493540\local\crash_dump\stdout.txt` if something looked wrong.

The mod uses parts of the game that are not documented: a game update can break it.
