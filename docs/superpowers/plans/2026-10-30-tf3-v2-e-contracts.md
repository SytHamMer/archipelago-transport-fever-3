# Contracts (V2-E) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (native, inline). Steps use checkbox syntax.

**Goal:** Present checks as contracts with a visible reward (item + receiving player), via scouting, notifications and `/contracts`.

**Architecture:** The client scouts all own locations, builds `contracts = {check_id: {item, to, own}}`, writes it in the inbox; `ap_notify.diff` takes it as a 5th argument and appends the reward to check messages.

**Tech Stack:** Python (client, bridge), Lua (ap_notify, ap_main glue), pytest + lupa.

**Spec:** docs/superpowers/specs/2026-10-30-tf3-v2-e-contracts-design.md

## Global Constraints

- Check ids are location names (e.g. `population:1`); the inbox key is `contracts`; entry `{item=string, to=string, own=bool}`.
- Without contracts, messages stay exactly as today. No push, no PR.

## Review Focus

- Scout reply missing/late: no contracts, plain notifications.
- A location the scout cannot name is skipped.

### Task 1: `contracts_from_scout` + bridge inbox

**Files:** Modify `tf3_world/transport_fever_3/client/tf3_client.py`, `bridge.py`; Test `tests/test_contracts.py`.

**Interfaces:** Produces `contracts_from_scout(infos, own_slot, location_name, item_name, player_name) -> dict`, with `infos` a list of `(location_id, item_id, receiver_slot)`; `Bridge.write_inbox(slot_data, received, log=None, contracts=None)` writes `inbox["contracts"]` when not None.

- [ ] Tests: own item (`own` True, `to` = player name), other player, unnameable location skipped; inbox contains `contracts` only when given.
- [ ] Run (FAIL), implement, run (PASS).

### Task 2: Lua notify with rewards

**Files:** Modify `tf3_mod/archipelago_tf3_1/content/ap_notify.lua`, `ap_main.script.lua` (pass `inbox.contracts`); Test `tests/test_lua_notify.py`.

**Interfaces:** `M.diff(previous, current, config, limit, contracts)`; check message title `Archipelago: contract completed`, text `<describe> - reward: <item> for <to>` (own: `reward: <item>`).

- [ ] Tests: reward appended for own and other, unchanged text without contracts, title changed only when a contract is known.
- [ ] Run (FAIL), implement, run (PASS).

### Task 3: Scouting in the client + `/contracts`

**Files:** Modify `tf3_client.py` (TF3Sync stores contracts; context sends `LocationScouts` on Connected, handles `LocationInfo`; `_cmd_contracts`); Test `tests/test_contracts.py`.

**Interfaces:** `TF3Sync.set_contracts(contracts)` rewrites the inbox; `contracts_report(contracts, done: set) -> list[str]`.

- [ ] Tests: `set_contracts` rewrites the inbox with contracts; `contracts_report` lists open contracts and a done/total line.
- [ ] Implement, run suite; extend `scripts/e2e_headless.py` fake mod check for `contracts` in the inbox.

### Task 4: Docs and commit

- [ ] Guide section, full suite green, commit on `v2`.
