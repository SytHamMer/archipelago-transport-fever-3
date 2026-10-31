# Installation and play guide: Transport Fever 3 x Archipelago

This guide is for a player who has never seen the project. It describes how everything is installed, what each piece does, how to choose the start year, and what to do when something does not work.

> Status: version 2, tested locally on Windows 11 with Archipelago 0.6.8 and Transport Fever 3 (Steam). It has not been proposed to the official Archipelago repository.

## 1. How it works

```
Archipelago server  <->  Client (in the Launcher)  <->  two files  <->  Mod in Transport Fever 3
```

- The **world** (`transport_fever_3.apworld`) tells Archipelago which items and checks exist.
- The **client** connects to the server and writes the wanted state (received items, options, the reward of each contract) into an `inbox` file. It reads an `outbox` file to send the checks.
- The **mod** runs in the game. Every 2 seconds it reads the `inbox`, locks or unlocks the modes, vehicles, road and rail types, tools and cargo classes, applies money and traps, creates and finishes the contracts, then writes the `outbox` (reached checks, game year, heartbeat).

The game does not let mods read or write files freely: they only get one fixed folder, `towns_industries`, in TF3's user data. That is the exchange folder.

## 2. What you need

- Transport Fever 3 (Steam), the version with the mod tools (the normal version has them).
- Archipelago 0.6.x, installed as described in the [official documentation](https://archipelago.gg/tutorial/Archipelago/setup/en).
- The two deliverables of the project:
  - `dist/transport_fever_3.apworld` (the world);
  - `tf3_mod/archipelago_tf3_1/` (the mod).

To rebuild the world: `python scripts/build_world.py`.

## 3. Install the world

Adding an `.apworld` to Archipelago is described in the [official documentation](https://archipelago.gg/tutorial/Archipelago/setup/en) (Launcher, **Install APWorld**, then restart the Launcher). Here the file is `dist/transport_fever_3.apworld`, and the tool to look for afterwards in the Launcher is called **Transport Fever 3 Client**.

## 4. Install the mod in the game

**Close Transport Fever 3 first.** The mod is installed as a **new folder** in the user mods folder; neither the game installation nor your saves are touched.

With the script (recommended):

```
python scripts/install_mod.py          # first installation
python scripts/install_mod.py --update # update of an already installed copy
```

The script refuses to run while the game is running, and only copies one folder. It detects the mods folder; otherwise pass `--mods-dir`.

By hand: copy the `tf3_mod/archipelago_tf3_1` folder into

```
C:\Program Files (x86)\Steam\userdata\<your Steam id>\3493540\local\mods\
```

The folder of this mod must be named exactly `archipelago_tf3_1`. The `save` folder next to it must never be modified.

When TF3 starts, the "Archipelago for Transport Fever 3" mod appears in the mod manager; it must be **enabled when the game is created**.

To remove it: delete that folder from `mods` (game closed).

## 5. Create the game in Transport Fever 3

An Archipelago game is a **dedicated game**: one slot, one seed. The mod is not attached to an existing save.

1. New free-play (sandbox) game, with the mod enabled.
2. **Start year: as late as possible, 2000 or later.** The maximum offered is 2020.

### Why the start year matters

The game hides vehicles (and stations, tracks...) whose release year has not come yet. The mod's filters can only hide **more**: they cannot show a vehicle the game already hides. In a game that starts in 1890, a train from 1950 would be out of reach of any item, and waiting for years to pass defeats the idea of a faster game.

Starting in 2020, everything is available by date, and the items of the multiworld do the locking. The mod also removes the end dates of vehicles and roads (like the official "vehicles without end year" mod), so that old vehicles stay on sale.

If the year is before 2000, the client shows a warning in its window: recreate the game with a later year. The mod never sets the date itself.

## 6. Set the options (YAML)

How YAML files work (the Launcher template, the `Players` folder, weights and random values) is described in the [official settings documentation](https://archipelago.gg/tutorial/Archipelago/advanced_settings/en). This world only adds its own options, listed below.

Main options (see the README for the full list and an example):

- **Missions**: `mission_checks` (3 by default, 0 to 30) creates contracts "N missions completed". A mission is an offer of the game, for example connecting two towns; it counts once completed, whatever its type.
- **Money**: `money_scale` (in %, 100 by default) multiplies every money grant and every money loss (base: 50,000, 250,000 and 1,000,000 for grants; 50,000 and 250,000 for losses). Lower it for a harder game.
- **Loans**: `loan_scale` (in %, 10 by default, 1 to 200) scales the amount of every bank loan. The game multiplies its loan amounts by 2.4 in 2020 (12 to 144 million each), which would make the money of the multiworld meaningless. The four loans the game creates when the game starts use the default scale (10%) because the game makes them before the mod can read your YAML value; your `loan_scale` applies to every loan the game makes afterwards (about every 6 months of game time, or after you take one).
- **Goals**: `goal_population`, `goal_company_level`, `goal_passengers`, `goal_cargo`. 0 disables a goal. The game is won when **all** active goals are reached. At least one must stay active.
- **Checks**: population, passengers and cargo steps (count, first and last value), company levels, deliveries per cargo, first line of each mode, game missions.
- There must be at least as many checks as progression items, otherwise generation stops with a message that gives the number.

How the game's values are measured: **population** is read from the company's experience (equal to the total population); passengers and cargo come from the all-time totals of the game's top bar.

## 7. Generate, host, connect

These steps are Archipelago's in general: see the [official documentation](https://archipelago.gg/tutorial/Archipelago/setup/en). Two points specific to this client:

- The tool to start is **Transport Fever 3 Client**. In its address field, **erase all** the default text before typing the server address, or the connection fails.
- It shows "Game connected" as soon as the mod answers. Archipelago automatically releases the remaining items when a player finishes their goal: this is normal, everything then unlocks in the game.

## 8. In the game

- With no item received: the **road** is free, **tram, rail, water and air** are locked, and only the oldest vehicles (before 1920) are on sale.
- The **mode** items unlock the menus (stations, depots, tracks, signals) and the vehicles of that mode. The "progressive vehicles" items add two tiers: 1920 to 1960, then after 1960. The **"Progressive Road Types"** and **"Progressive Rail Tracks"** items do the same for road types (old country and town roads at the start, then recent roads and motorways) and rail types (simple track at the start, then standard track with catenary, then high speed).
- Five **tools** are unlocked by their own item: **Tool: Bus Lanes**, **Tool: Tram Tracks** (tram tracks on roads), **Tool: Rail Signals**, **Tool: Electrification** and **Tool: Noise Barriers**. A tool of a locked mode stays closed even with its item. Roundabouts and interchanges follow the road types, by year.
- Four **cargo class** items (`Cargo Class: Bulk`, `Flatbed`, `Goods`, `Liquid`) unlock the specialised freight vehicles of that class (bulk wagons, tankers...). **Universal** vehicles (any cargo) and passenger vehicles are never locked by class: a universal cart or truck of the first tier carries every cargo from the start.
- The "**company level +1**" items grant a level, with the game's usual benefits.
- **Money** arrives as accounting entries; traps remove money (a loss of 50,000 or 250,000).
- Money effects are applied **only once**, but they are tied to the seed, not to the save: if you reload an old save, the money already received does not come back.

### Contracts

Every open check is a **contract**, shown with the game's own contract interface: an icon at the top of the screen, a notification (category "Opportunity"), and a window with the task and, under "On completion", the reward (the item and the player who receives it). It looks like the game's own subsidies, with no deadline and no penalty. The window shows the current value, for example "Population reached 1,260 (579 / 1,260)".

- **Contracts do not need to be accepted to be completed.** The check is reached when the game reaches its value; the mod then accepts and finishes the contract by itself, and the reward goes out. Accepting a contract only moves it to "contract in progress". The game's own subsidies are separate and keep appearing as usual, **as long as fewer than 5 contracts are active**: the game only proposes new subsidies while fewer than 5 are active, and it counts ours. So do not accept more than 5 Archipelago contracts at the same time, or its own subsidies (such as "Connect towns") stop appearing until some of ours are finished.
- Only the next step of each ladder is shown (the next population level, the next company level, the next delivery tier of each cargo, every first line), so the game is not flooded with contracts.
- If you **decline** a contract, it comes back with a new identifier until its check is reached.
- The client command `/contracts` lists the open contracts with their reward.
- Each item received and each check sent is also announced by a **notification** with the Archipelago logo (top of the screen, then the notifications tab): "Rail Transport from Alice (their check)", "Population reached 2,500"... When a game is loaded, nothing that was already received is announced again. Items and checks also appear in the client window.

## 9. When it does not work

| Symptom | Likely cause | What to do |
|---|---|---|
| The client does not appear in the Launcher | World not installed or Launcher not restarted | Redo **Install APWorld**, restart the Launcher |
| Connection error with `archipelago.gg:...` in the field | Default text not erased | Erase the whole field, retype the address |
| Generation stops on "only give N checks" | Not enough checks for the items | Raise the check options |
| Generation stops on "no goal is active" | The four goals are at 0 | Set one goal above 0 |
| "Waiting for the game mod" | The mod has not written this seed's `outbox` | Check that the mod is active and the game is started |
| "The game mod is not answering" | The game is closed or paused for a long time | Restart the game |
| "user data not found" | TF3's data folder not found (Steam installed elsewhere) | In the client, type `/folder <path of the towns_industries folder>` |
| Warning about the game year | Game created before 2000 | Recreate the game, latest start year |
| The game refuses to start: "try removing the mod" | Error in a mod script | Read `...\3493540\local\crash_dump\error.json` and remove the mod in the meantime |
| No recent vehicle despite the items | Game from before 2000 | See "Start year" above |
| Red screen "Reload UI" | Error in a mod script or a contract window | Copy the message (Copy to clipboard) and read `crash_dump\stdout.txt` |

Useful files:
- the game log: `...\3493540\local\crash_dump\stdout.txt` (the mod's lines start with `ARCHIPELAGO`);
- the exchange files: `...\3493540\local\towns_industries\archipelago_tf3_inbox.lua` and `archipelago_tf3_outbox_<seed>.lua` (one file per seed), readable in a text editor.

## 10. Current limits

- Temperate climate cargos only.
- Tram, water and air have not all been verified in the menus; see `docs/superpowers/plans/e2e-checklist.md`.
- No tracking window in the game: the open contracts use the game's contract interface, and items and checks are announced by notifications.
- Platform: Windows PC only.
