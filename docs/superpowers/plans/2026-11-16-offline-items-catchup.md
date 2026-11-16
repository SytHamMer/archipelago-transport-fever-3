# Catch-up notification for items received while away — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After loading the game, tell the player which items arrived while they were away, as one grouped summary when the batch is big.

**Architecture:** The mod saves in its per-seed outbox how many entries of the inbox `log` it has announced (`notified`). On the first tick of a seed it resumes from that cursor instead of a silent baseline. The pure logic (resume point, grouped summary) lives in `ap_notify.lua`; `ap_main.script.lua` only persists and wires it.

**Tech Stack:** Lua mod (`tf3_mod/archipelago_tf3_1/content`), pytest with the Lua helpers of `tests/lua_helpers.py` (lupa).

**Spec:** [docs/superpowers/specs/2026-11-16-offline-items-catchup-design.md](../specs/2026-11-16-offline-items-catchup-design.md)

## Global Constraints

- The outbox file stays compatible both ways: an old outbox without `notified` starts silent (as today); an old mod ignores the new field. `FORMAT_VERSION` does not change.
- No replay of what was already announced, and no replay of checks (they come from the saved `state.checks`).
- Check notifications keep today's behavior; only item entries get the summary.
- The notifications limit stays `M.DEFAULT_LIMIT = 5`.
- Docs are in English. Nothing is pushed, tagged or released by this plan.

## Review Focus

- A saved cursor larger than the current log (reset server, other game, same seed name): silent baseline, no crash, no negative count.
- An old outbox without `notified`: silent baseline exactly as today.
- Exactly `limit` new items: announced one by one; `limit + 1`: one summary.
- The same item sent several times (possibly by different players): one name with a count.
- No log in the inbox at all (old client): the item-count path is unchanged.

---

### Task 1: Pure logic in `ap_notify.lua` (resume point and grouped summary)

**Files:**
- Modify: `tf3_mod/archipelago_tf3_1/content/ap_notify.lua` (`diff`, new `M.resume`, new constants)
- Test: `tests/test_lua_notify.py`

**Interfaces:**
- Produces: `M.resume(current, notified) -> previous | nil`. `current` is the state table of `notify_changes` (`{ items, checks, log?, log_size? }`), `notified` the saved number or nil. Returns `{ items = current.items, checks = current.checks, log_size = notified }` when `current.log` exists and `notified` is a number with `0 <= notified <= #current.log`; otherwise `nil`.
- Produces: `M.BATCH_TITLE = "Archipelago: items received"`, `M.BATCH_NAMES = 4`, `M.BATCH_SECONDS = 20`.
- Produces: in `diff`, when the new log entries number more than `limit`, they become one message `{ title = M.BATCH_TITLE, text = ..., seconds = M.BATCH_SECONDS }` instead of one message each. Text: the distinct item names sorted by count descending then name, each followed by ` x<count>` when the count is above 1, joined by `", "`, cut to `M.BATCH_NAMES` names, then `" and <k> more"` when names were cut.

- [ ] **Step 1: Write the failing tests** in `tests/test_lua_notify.py` (`log_state`, `diff`, `texts` already exist there)

```python
def resume(current, notified):
    runtime, notify = load_module("ap_notify")
    return from_lua(notify.resume(to_lua(runtime, current), notified))


def test_resume_starts_from_the_saved_cursor_so_missed_entries_are_new():
    entries = [{"item": f"Item {i}"} for i in range(3)]
    previous = resume(log_state(entries, ["population:1"]), 1)
    assert previous["log_size"] == 1 and previous["checks"] == ["population:1"]
    assert texts(diff(previous, log_state(entries, ["population:1"]))) == ["Item 1", "Item 2"]


def test_resume_without_a_cursor_or_with_a_cursor_past_the_log_is_silent():
    current = log_state([{"item": "A"}])
    assert resume(current, None) is None
    assert resume(current, 5) is None
    assert resume(current, -1) is None
    assert resume(state(), 0) is None  # no log in the inbox: the item-count path is unchanged


def test_a_batch_above_the_limit_is_one_grouped_summary():
    entries = [{"item": "Rail Transport"}, {"item": "Rail Transport"}, {"item": "Tool: Bus Lanes"}] + \
        [{"item": f"Extra {i}"} for i in range(4)]
    messages = diff(log_state([]), log_state(entries), limit=5)
    assert messages == [{"title": "Archipelago: items received", "seconds": 20,
                         "text": "Rail Transport x2, Extra 0, Extra 1, Extra 2 and 3 more"}]


def test_exactly_the_limit_is_announced_one_by_one():
    entries = [{"item": f"Item {i}"} for i in range(5)]
    assert len(diff(log_state([]), log_state(entries), limit=5)) == 5


def test_the_summary_counts_the_same_item_from_different_players_together():
    entries = [{"item": "Rail Transport", "from": "Alice"}, {"item": "Rail Transport", "from": "Bob"}] + \
        [{"item": f"Item {i}"} for i in range(4)]
    assert texts(diff(log_state([]), log_state(entries), limit=5))[0].startswith("Rail Transport x2")


def test_the_summary_comes_before_the_check_messages():
    entries = [{"item": f"Item {i}"} for i in range(6)]
    messages = diff(log_state([]), log_state(entries, ["population:1"]), limit=5)
    assert [m["title"] for m in messages] == ["Archipelago: items received", "Archipelago: check sent"]
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/test_lua_notify.py -q`
Expected: the new tests FAIL (`resume` missing, no summary); the old ones pass.

- [ ] **Step 3: Implement `M.resume`, the constants and the summary branch of `M.diff`** in `ap_notify.lua`

Approach: in `diff`, collect the new entries (`seen + 1 .. #current.log`); if there are more than `limit`, build one message with a local `batch_text(entries)` (count per name, sort, cut); otherwise keep the existing per-entry loop. Leave the final cap (`#messages > limit`) untouched.

- [ ] **Step 4: Run to verify they pass**

Run: `python -m pytest tests/test_lua_notify.py -q`
Expected: all PASS, old tests included.

- [ ] **Step 5: Commit**

```bash
git add tf3_mod/archipelago_tf3_1/content/ap_notify.lua tests/test_lua_notify.py
git commit -m "notify: resume point from a saved cursor, grouped summary for a big batch"
```

### Task 2: Persist the cursor and use it on the first tick

**Files:**
- Modify: `tf3_mod/archipelago_tf3_1/content/ap_main.script.lua` (`state` ~line 50, `adopt_seed` ~333, `write_outbox` ~352, `send_notification` ~523, `notify_changes` ~614)
- Test: `tests/test_lua_main_smoke.py`, `tests/test_bridge.py`

**Interfaces:**
- Consumes: `notify.resume(current, notified)` and the optional `seconds` field of a message, from Task 1.
- Produces: outbox field `notified` (number: announced log entries). `state.notified` (number or nil) is read from the seed's outbox by `adopt_seed`; `write_outbox` writes `state.last_notified.log_size` when present, else `state.notified`.

- [ ] **Step 1: Write the failing tests**
  - `tests/test_bridge.py`: an outbox file carrying `notified = 3` is still read by `Bridge.read_outbox()` with the same checks, goals and heartbeat (unknown fields ignored).
  - `tests/test_lua_main_smoke.py`: following its existing pattern, one test where the seed's outbox holds `notified = 1` and the inbox log has 3 entries: after one tick the notification events sent contain the two missed items; one test where the outbox has no `notified`: nothing is announced. If the smoke harness cannot observe the sent notifications, say so in a comment and cover this wiring with the manual check of Task 3.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/test_bridge.py tests/test_lua_main_smoke.py -q`
Expected: the new smoke test FAILS (nothing announced); the bridge test may already pass (it pins the compatibility).

- [ ] **Step 3: Implement the wiring**
  - `adopt_seed`: `state.notified = previous.notified` for a table of this seed, otherwise nil (also reset on a seed change).
  - `notify_changes`: when `state.last_notified == nil`, pass `notify.resume(current, state.notified)` to `notify.diff` as the previous state (nil keeps today's silent baseline).
  - `write_outbox`: add `notified = (state.last_notified and state.last_notified.log_size) or state.notified`.
  - `send_notification`: use `message.seconds` when it is a number instead of `NOTIFICATION_SECONDS`.

- [ ] **Step 4: Run the whole suite**

Run: `python -m pytest -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add tf3_mod/archipelago_tf3_1/content/ap_main.script.lua tests/test_bridge.py tests/test_lua_main_smoke.py
git commit -m "mod: remember the announced items in the outbox and catch up after a load (issue #1)"
```

### Task 3: Docs and the manual check

**Files:**
- Modify: `README.md` and `docs/guide-installation.md` (the notifications paragraph), `docs/improvements.md` (point from the 0.2.0 history idea to this fix), `docs/superpowers/specs/2026-11-16-offline-items-catchup-design.md` (settle "Left to the builder" with the values chosen here, add the manual check)

- [ ] **Step 1: Write the doc changes**: English, one or two sentences each: items received while the game was closed are announced when the save is loaded, as one summary when there are more than 5.
- [ ] **Step 2: Add the manual in-game check** to the design doc: play with the mod, close the game, receive 1 then 8 items from another slot (client connected), start the game and load the save. Expected: the single item by name in the first case, one "Archipelago: items received" summary in the second, nothing repeated after a second reload. Mark it "not run" until it has been run by hand.
- [ ] **Step 3: Run the style test**

Run: `python -m pytest tests/test_style.py -q`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add README.md docs
git commit -m "docs: items received while away are summed up when the game loads"
```
