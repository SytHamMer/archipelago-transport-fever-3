# Upstream pull request readiness

Review of the world against Archipelago's [adding games](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/adding%20games.md)
and [world maintainer](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/world%20maintainer.md) guides.

**Nothing has been pushed or proposed.** There is no git remote. The pull request waits for the go of the author, after
a manual check of the web page and the documentation.

## Met

| Requirement | Where |
|---|---|
| World folder with `__init__.py`, `archipelago.json` (game, version, minimum AP version) | `tf3_world/transport_fever_3/` |
| `World` subclass with `game`, `web`, item and location name to id tables, `create_item`, regions, completion condition | `__init__.py`, `Items.py`, `Locations.py`, `Rules.py` |
| As many items as locations (filler fills the difference) | `get_filler_item_name`, filler weights in `data.py` |
| Game page `docs/en_Transport Fever 3.md` and setup guide `docs/setup_en.md`, declared in a `WebWorld` tutorial | `docs/`, `TF3Web` |
| Options as a dataclass, option groups, presets, item and location name groups | `Options.py`, `Items.py`, `Locations.py` |
| Options and `slot_data` can be pickled (upstream test `test_pickle_dumps_default`) | `"__module__": __name__` in the ladder factory, `test_every_option_class_can_be_pickled` |
| Tests inside the world, runner-agnostic, in `test/` | `tf3_world/transport_fever_3/test/` |
| Style: 120 columns, double quotes, annotations, snake_case | `tests/test_style.py` |
| Documentation in English | README, world docs, guides |

Upstream general tests (and the web host ones, see below), run with `AP_TEST_WORLDS=transport_fever_3` (the folder name, not the game name): 155 passed.

## Not done or not run

1. **Web host tests** (descriptions, docs, file generation, option presets): the 7 tests that cover the world pass. They were run with the web host requirements installed in the venv and the module updater disabled (it wants to downgrade other packages). The rendered pages themselves still need a manual look.
2. **The mod is not part of the apworld.** The game needs the Lua mod, installed by `scripts/install_mod.py`. The setup
   guide says to install it but has **no download link**: the mod has to be hosted (for example a GitHub release of the
   author's repository) before the pull request, and the link added to `docs/setup_en.md`.
3. **Client in the Launcher.** The client is registered as a Launcher component. It was checked with a real Launcher in a
   two-player and a mixed Transport Fever 3 and Satisfactory multiworld.
4. **Bug report page**: set to the issues page of the public repository (`bug_report_page` in the `WebWorld`).
5. **Author name** in the tutorial is `Mathys`; to be confirmed.
6. **Maintainer duties** (world maintainer guide): to be the maintainer of the world (the author of a merged world becomes it; the `docs/CODEOWNERS` entry is settled with the reviewers), to
   review the pull requests that touch it, to test the world on release candidates and to answer on Discord. The author
   has to accept these before the pull request.
7. **Not verified in game**: tram, water and air menus, the first line and delivery checks of each mode, the rail tiers
   (see `docs/improvements.md`).
8. **Balance** is a first guess: it can only be polished with feedback from real games (README, "Status and feedback",
   and the setup guide).
9. Dependency: Lua mod hooks into undocumented parts of the game, so a game update can break it. The README says so.

## To check by hand before the pull request

- The game page and the setup guide as rendered by the web host (links, headings, the feedback section).
- The option page: names, descriptions, groups and the three presets (Short game, Default, Long game).
- The wording of `README.md`, `docs/guide-installation.md` and `docs/playing-with-a-friend.md`.
- Whether `tf3_world` should be offered as an apworld download or only as a pull request.
