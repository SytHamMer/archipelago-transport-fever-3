# Improvements to make

Points noted while testing, to be done later. Each one says what is wrong, why it matters, and how it could be done.
Newest at the end of each section. Nothing here is started unless it says so.

## Checks that fit the map and the game

### 1. Only ask for cargos the map can produce

- **Problem:** the delivery checks (`delivered:<cargo>:<tier>`) cover all 28 cargos of the temperate climate. Some
  biomes and maps have no industry for some of them, so the check can never be reached.
- **Why it matters:** an impossible check is a location that can hold a progression item nobody can reach. The
  multiworld then cannot be completed.
- **Constraint:** the multiworld is generated before the game exists, so the world cannot look at the map.
- **Ideas:**
  - a YAML option to choose the cargos (or the climate) that deliveries cover, checked against the game's cargo list;
  - a preset per climate/biome with the cargos that exist there (to be measured from the game's industries and
    climates);
  - at least a warning in the client when a check needs a cargo that the loaded map has no producer for.

### 2. Cargo difficulty

- **Problem:** every cargo has the same delivery tiers (100, 500, 2,000, 10,000) and the same access rules. A car or
  a machine, which needs a whole production chain, is far harder to deliver than vegetables or grain.
- **Ideas:**
  - give each cargo a difficulty level (raw material, intermediate good, final good) from its position in the
    production chains;
  - scale the tiers by difficulty (smaller amounts for hard cargos);
  - make the logic reflect it: hard cargos need more items (modes, vehicle tiers, the matching cargo class) than easy ones;
  - let the YAML choose how many of each level are checks.

## Known minor issues (from earlier reviews)

- The locks flicker for up to 2 seconds when the client reconnects.
- A money effect that is in flight while the seed changes can, in a narrow window, be booked for the old seed.
- The "too few checks" message could say more clearly which options to raise.

## Not verified in game yet

- Tram, water and air menus in detail; first line and delivery checks for each mode; rail tier C at its real year
  bounds; air mode.
- A multiworld with a game other than Transport Fever 3 and Satisfactory, and with more than two players.

## Before proposing the world upstream

- A `docs/` folder inside the world (a game page and a setup guide) and a `WebWorld`, as the official worlds have.
- Review of the world against Archipelago's world guidelines, and a decision on what the maintainers should see.
- Nothing is pushed or proposed to the official repository until the user says so.
