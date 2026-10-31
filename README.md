# Transport Fever 3 x Archipelago

Play Transport Fever 3 (PC, Steam) in an [Archipelago](https://archipelago.gg) multiworld, without the honor system: the game locks what has not been received and sends the checks itself.

Status: version 2, tested locally. **Nothing has been proposed to the official Archipelago repository**: everything stays local until testing is finished.

## What you need

- Transport Fever 3 (Steam) and Archipelago 0.6.x installed.
- The two deliverables of this project, described below: the world (`.apworld`) and the mod.

## Install and play

Installing Archipelago, adding a world, generating, hosting and connecting a client are covered by the [official Archipelago documentation](https://archipelago.gg/tutorial/Archipelago/setup/en), so they are not repeated here. What is specific to this world:

- The world to install is `dist/transport_fever_3.apworld` (`python scripts/build_world.py`). The client is called **Transport Fever 3 Client** in the Launcher.
- The mod `tf3_mod/archipelago_tf3_1` is installed with `python scripts/install_mod.py` (game closed). The script only writes one new folder into `...\3493540\local\mods\`.
- Create a **new free-play game** with the "Archipelago for Transport Fever 3" mod enabled and a **start year of 2000 or later** (2020 is the maximum offered). Without that, no item can unlock vehicles newer than the game's date.

The client and the mod exchange two files in `...\3493540\local\towns_industries\` (the game only lets mods use that folder and `mod_presets`). Set the `TF3_USERDATA_DIR` variable to change the folder.

Step by step instructions, the choice of the start year and troubleshooting are in [docs/guide-installation.md](docs/guide-installation.md).

## What is in the game

- **Items**: one item per transport mode (tram, rail, water, air; the road is free), vehicles by year tier for each mode, road and rail types, five tools (bus lanes, tram tracks, signals, electrification, noise barriers), four cargo classes (bulk, flatbed, goods, liquid), company levels, money and traps (money losses).
- **Checks**: population, company levels, passengers and cargo transported, the first line of each mode, deliveries per cargo and missions completed. Every check is a **contract**, see below.
- **Goals**: population, company level, passengers or cargo; the game is won when all the active goals are reached.

### Contracts

Each open check is shown as a real game contract, with the game's own window (task, and what completing it gives: the item and the player who receives it), icon and notification, like the game's own subsidies. A contract has no deadline and no penalty.

**Contracts do not need to be accepted to be completed.** A check is reached as soon as the game reaches its value, whether or not the contract was accepted; the mod then accepts and finishes the contract by itself. Accepting only makes it appear under "contract in progress". **Do not accept more than 5 Archipelago contracts at the same time**: the game only proposes its own subsidies while fewer than 5 contracts are active, so accepting more of ours stops its subsidies (such as "Connect towns") from appearing until some of ours are finished. The game's own subsidies (for example "Connect towns") keep appearing as usual as long as you do not accept too many contracts, see below. If you decline a contract it comes back, until its check is reached.

Only the next step of each ladder is shown (the next population level, the next company level, the next delivery tier of each cargo, every first line), so the game does not fill up with contracts. The client command `/contracts` lists the open contracts with their reward.

## YAML options

The format of a YAML file, weights and random options are explained in the [official settings documentation](https://archipelago.gg/tutorial/Archipelago/advanced_settings/en). The options of this world:

| Option | Default | Role |
|---|---|---|
| `population_checks`, `population_first`, `population_last` | 4, 500, 5000 | population steps (count, first, last) |
| `passengers_checks` / `_first` / `_last` | 3, 100, 2000 | passengers transported in total |
| `cargo_checks` / `_first` / `_last` | 3, 100, 2000 | cargo transported in total |
| `company_level_checks` | 4 | company levels 2, 3, 4... |
| `delivery_checks` | 1 | delivery tiers per cargo type (100, 500, 2,000, 10,000) |
| `first_line_checks` | yes | first line of each mode |
| `mission_checks` | 3 | number of "N game missions completed" checks (0 to 30) |
| `money_scale` | 100 | percentage applied to every money grant and loss (10 to 1000) |
| `loan_scale` | 10 | percentage applied to the amount of every bank loan (1 to 200; 100 = the game's amounts, very large in 2020) |
| `goal_population`, `goal_company_level`, `goal_passengers`, `goal_cargo` | 2500, 0, 0, 0 | goals; 0 disables a goal; the game is won when **all** active goals are reached |

Bank loans are scaled by `loan_scale`: the game multiplies its loan amounts by 2.4 in 2020 (tens of millions each), which would make the multiworld's money meaningless. The four loans the game creates when the game starts use the default scale (10%) because the game makes them before the mod can read your YAML value; your `loan_scale` applies to every loan the game makes afterwards (about every 6 months of game time, or after you take one).

The base money amounts (grants 50,000 / 250,000 / 1,000,000, losses 50,000 / 250,000) are multiplied by `money_scale`.

Example:

```yaml
name: MyName
game: Transport Fever 3
Transport Fever 3:
  goal_population: 5000
  goal_passengers: 1000
  population_checks: 6
  population_last: 8000
```

There must be at least as many checks as progression items: otherwise generation stops with a message that says how many.

## Known limits

- One-shot effects (money, traps) are tied to the **seed**, not to the save: loading an old save does not give back the money already received.
- Cargos are the temperate climate ones.
- Air mode, tram, water, the first line and delivery checks, and tier 3 of the vehicles have not all been verified in game (see `docs/superpowers/plans/e2e-checklist.md`).
- Missions of the game count once completed, whatever their type; the mod reads them every 2 seconds.
- There is no tracking window in the game: items received and checks sent are announced by notifications (with the Archipelago logo), and the open contracts are the game's own contract interface.

## Development

```
venv\Scripts\python -m pytest                       # tests (world, client, Lua modules through lupa)
venv\Scripts\python scripts\build_world.py          # dist/transport_fever_3.apworld
venv\Scripts\python scripts\install_mod.py --update # installs the mod (game closed)
venv\Scripts\python scripts\dev_inbox.py --seed s1 "Rail Transport"   # simulates the client (--contracts: fake contracts)
venv\Scripts\python scripts\e2e_headless.py out\AP_xxx.zip            # server + client + fake mod
```

`ap/` (an Archipelago clone) and `m/` (the Manual template) are not tracked by git. `tf3_ap/` is the Manual prototype, `tf3_probe/` the probes used to measure what the game allows.
