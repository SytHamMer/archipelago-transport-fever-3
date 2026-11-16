# Items received while away: catch-up notification (issue #1)

Short design for [issue #1](https://github.com/SytHamMer/archipelago_tf3/issues/1) ("Check validate when offline"),
meant for 0.1.1.

## Intent and why

A Transport Fever 3 player gets items sent by other players while they are offline (game closed, or game loaded after
the client reconnected). Today the game gives no sign of it: the items are applied, but never announced. The player
cannot tell what unlocked while they were away.

## Cause (found in the code)

The mod keeps what it already announced in memory only (`state.last_notified`). The first tick after every game load
only records the current state, silently (`notify.diff` with `previous == nil`), so everything received while the game
was closed is lost to the player. When the game is running, new items are announced, but at most 5 notifications and
then "and N more", which does not say which.

## Goals

- After loading the game, the player is told which items arrived since the last time they played.
- A big batch (after a long absence, or a reconnection) is one readable summary, not a wall of notifications and not
  "and N more".
- No replay of everything at each load: only what is new since the last announcement.

## Non-goals and anti-goals

- No new window or in-game history (kept as an idea for 0.2.0, see `docs/improvements.md`).
- Do not announce again what the player already saw. Do not break old outboxes: one without the new field starts
  silent, as today.
- No change to the client or to the checks logic.

## Approaches considered

1. Remember the last announced item in the outbox, announce the new ones one by one (same limit of 5 plus "and N
   more"). Smallest change, but "and 12 more" does not say which items.
2. **Chosen.** The same memory, plus a grouped summary for a batch.
3. An in-game history window of the received items. Most complete, but the mod has no window of its own and the game's
   interface crashes easily on a malformed one: a later version.

## Design

- The outbox (already kept per seed, with `applied`) gets one more field, `notified`: the number of entries of the
  inbox `log` already announced. `write_outbox` saves it, `adopt_seed` reads it back into the state.
- `notify_changes`: on the first tick of a seed, when the outbox gave a `notified` value that is not larger than the
  log, the baseline is that value instead of "everything now": what arrived since is announced. Without the field (old
  outbox) or with a value larger than the log (another game, reset server), the baseline stays silent as today.
- `ap_notify.diff`: when the new log entries number more than the limit, they are replaced by one notification titled
  "Archipelago: while you were away" (or an equivalent title) that groups them by item name with a count, sorted, and
  limited to a few names followed by "and N more". Up to the limit, items are announced one by one as today (item,
  sender, check). The summary is also used when the game was running and a reconnection brings a big batch.
- The summary may stay on screen longer than the usual 8 seconds (builder's call).
- The checks already persisted in the outbox are not replayed.
- Tests: the pure logic of `ap_notify` (diff with a cursor, grouping, limit, old outbox, cursor larger than the log) in
  the existing Lua tests; no in-game test is possible without the game, so a manual check is listed.

## Left to the builder

Exact wording and title of the summary, how many names it lists, its display duration, and the manual test steps
(play, close the game, receive items from another slot, reload, check the notification).

## Next steps after this change (release, not part of this design)

Test in game, version 0.1.1 (mod, world, release notes), tag, then push and publish for the other players. Nothing is
pushed or tagged without an explicit go.
