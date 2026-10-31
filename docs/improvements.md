# Improvements to make

Points noted while testing, to be done later. Each one says what is wrong, why it matters, and how it could be done.
Newest at the end of each section. Nothing here is started unless it says so.

## Checks that fit the map and the game

### 1. Only ask for cargos the map can produce (done on the `cargo-balance` branch)

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

### 2. Cargo difficulty (done on the `cargo-balance` branch)

- **Problem:** every cargo has the same delivery tiers (100, 500, 2,000, 10,000) and the same access rules. A car or
  a machine, which needs a whole production chain, is far harder to deliver than vegetables or grain.
- **Ideas:**
  - give each cargo a difficulty level (raw material, intermediate good, final good) from its position in the
    production chains;
  - scale the tiers by difficulty (smaller amounts for hard cargos);
  - make the logic reflect it: hard cargos need more items (modes, vehicle tiers, the matching cargo class) than easy ones;
  - let the YAML choose how many of each level are checks.

## Economy at a 2020 start

### 3. Everything costs far more than in an early game (partly done on the `cargo-balance` branch)

- **Done, not yet checked in game:** the era coefficient of depots, stations and terminals (x9 from 1980) is divided out at load (`ap_costs.lua`).
- **Still open:** vehicle prices (computed by the engine), road and track prices, and a YAML-driven cost scale (needs the load script to read the exchange file, see the probe on the `economy` branch).

- **Problem:** the game inflates prices with the year. Starting in 2020 (needed for vehicles, see the guide), a bus
  stop costs about 300,000 where an early game has it at about 12,000. The whole game is unbalanced for a new company.
- **Why it matters:** the cheap start of the base game (small first lines, growing slowly) does not exist any more;
  the starting money covers almost nothing.
- **Ideas:** find where the game applies the inflation (finance utilities) and offset it, for example by scaling
  construction and vehicle costs back, or by giving the company a starting capital that fits the year; to be
  measured in game before choosing.

### 4. Money rewards are far too small for that economy (done on the `cargo-balance` branch)

- **Done, not yet checked in game:** grants are now 1,000,000 / 5,000,000 / 20,000,000 and losses 1,000,000 / 5,000,000.

- **Problem:** the money grants (50,000 / 250,000 / 1,000,000) and the losses (50,000 / 250,000) are tiny compared with
  prices at 2020, so a grant buys almost nothing and a loss is not felt.
- **Ideas:** scale the amounts with the same factor as the prices (the inflation of the current year), keeping
  `money_scale` as the player's difficulty percentage; decide the base amounts from what a first line costs.

## Start year

- **Experiment on the `free-years` branch:** the first years of vehicles, road and track types, stations and depots are
  set to 0 at load, with the real year kept in `notificationSortKey`, so any start year works and an early start gets
  the early prices (which follow the date). To check in game: that the tiers still follow the real years, that nothing
  that should be locked shows up, that the menus are not cluttered by the era variants of depots and stations, and that
  towns and industries behave in an early year.

## DeathLink

- Receive only for now. A TF3 "death" to send (for example going bankrupt) is an open question.
- The loss amount is set by the YAML option `death_link_loss` (exact, not scaled).
- The effect is applied when the mod next reads the inbox; a death received while the game is closed is lost (the server does not replay deaths).

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
