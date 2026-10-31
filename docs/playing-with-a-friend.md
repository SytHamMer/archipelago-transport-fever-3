# Playing Transport Fever 3 with a friend on another game (for example Satisfactory)

This is a step by step plan for a multiworld with one player on Transport Fever 3 (the host) and one on another game.
It uses Satisfactory as the example. Generic Archipelago steps (installing, generating, hosting) are in the
[official documentation](https://archipelago.gg/tutorial/Archipelago/setup/en) and are only summarised here.

`localhost` only works for the player on the same computer as the server. A friend at home needs an address that
reaches your computer, see step 4.

## Part A: for the host (Transport Fever 3)

### 1. Get the latest versions ready

1. Close Transport Fever 3.
2. Rebuild and install the mod: `python scripts/install_mod.py --update`.
3. Rebuild the world: `python scripts/build_world.py`, then in the Archipelago Launcher use **Install APWorld** on
   `dist/transport_fever_3.apworld` and restart the Launcher.
4. Both of you must use the same Archipelago version (0.6.x, tested with 0.6.8).

### 2. Collect the two YAML files

1. Your YAML: `players/tf3.yaml` of this repository (name `Mathys`, see the README for the options).
2. Your friend's YAML: they create it (see Part B) and send it to you. Their slot name must be different from yours.
3. Put both files in the `Players` folder of your Archipelago installation.

A good first test: a small TF3 goal so that the game does not end too early (`goal_population: 2500` is the
default), and a few more checks (`population_checks`, `delivery_checks`) so that the friend receives many items.

### 3. Generate

In the Launcher, click **Generate**. The multiworld zip appears in the `output` folder of the Archipelago
installation. Generation needs both worlds installed on your computer: Transport Fever 3 (step 1) and the other
game (Satisfactory is in the Launcher already).

### 4. Make your server reachable

Pick one of the two ways. The Archipelago server listens on port **38281** by default.

**Option 1: a private network (recommended, nothing is exposed on the internet).**
This uses [Tailscale](https://tailscale.com/) (its free personal plan covers two computers; check its pricing page).
[ZeroTier](https://www.zerotier.com/) works the same way if you prefer it.

1. Install Tailscale on your computer and sign in (an existing Google, Microsoft or GitHub account is enough).
2. Find your private address: in the Tailscale icon menu it is listed under your device name, an address of the form
   `100.x.y.z`. Write it down.
3. Share your computer with your friend: open the Tailscale admin console in a browser (login.tailscale.com),
   go to **Machines**, open the menu of your computer, choose **Share**, and send the link to your friend. They
   accept it with their own Tailscale account, after which your computer appears on their side.
4. Allow the Archipelago port in the Windows firewall for the Tailscale network. In an administrator PowerShell:
   `New-NetFirewallRule -DisplayName "Archipelago 38281" -Direction Inbound -Protocol TCP -LocalPort 38281 -Action Allow`
5. Once the server runs (step 5), check from your friend's computer that it is reachable:
   `Test-NetConnection <your private address> -Port 38281` in PowerShell must say `TcpTestSucceeded : True`.

Your friend connects to `<your private address>:38281`.

**Option 2: open the port on your router.**
Forward TCP port 38281 of your router to your computer, and allow it in the Windows firewall (accept the Windows
prompt for the Archipelago program when the server starts). Your friend connects to `<your public IP>:38281`.
Set a password in that case (see the Archipelago documentation on server passwords): anyone who knows the address
could try to connect.

### 5. Host the multiworld

In the Launcher click **Host Game** and choose the zip of step 3. Leave the server window open for the whole game.

### 6. Start your side

1. Start Transport Fever 3 with a new free-play game, start year 2020 or later, and the mod enabled.
2. Open **Transport Fever 3 Client** (not the Text Client), erase the default address, type `localhost:38281` and
   connect with your slot name. It must say "Game connected".
3. Type `/contracts`: the rewards for your friend show the item names of their game (for example "Building: Blender").

### 7. Play and check

- Your contracts that reward your friend send them items of their game; the contract window shows the item and
  "for <friend>".
- When your friend finds an item for you (for example "Progressive Rail Vehicles"), TF3 shows a notification with
  the sender, and the item is applied.
- Archipelago releases the remaining items of a player who reaches their goal: if you reach your goal first, your
  friend receives everything at once. That is normal.

### 8. If something fails

| Symptom | What to check |
|---|---|
| Your friend gets "connection refused" | The server window is open, the private network is connected on both sides, or the port is forwarded and the firewall allows it |
| Both connect but names fail | The slot name must be exactly the name in the YAML, with the same capitals |
| Your TF3 client says "Waiting for the game mod" | The mod is enabled in the game and the game is running |
| A version error | Both of you use the same Archipelago version |

## Part B: for your friend (Satisfactory), send them this part

Your friend does **not** need the Transport Fever 3 world or mod. They only need Satisfactory and its Archipelago
mod. The official guide is in the Archipelago documentation (Satisfactory setup guide); here is the short version.

1. **Install what you need.**
   - Satisfactory (Steam or Epic). Launch it once so the Mod Manager finds it.
   - The Satisfactory Mod Manager: <https://smm.ficsit.app/>.
   - In the Mod Manager, install the mod **Archipelago Randomizer**.
2. **Make your YAML file.** On <https://archipelago.gg/games/Satisfactory/player-options> choose your options,
   set your player name (for example `Friend`), download the YAML and send it to the host. No other file is needed.
3. **Join the private network** (if the host chose option 1): install Tailscale from <https://tailscale.com/download>,
   sign in with your own account (Google, Microsoft or GitHub), then open the sharing link the host sent you and
   accept it. The host's computer then appears in your Tailscale list: its private address (`100.x.y.z`) is the
   address to use. Once the host says the server runs, you can check it with `Test-NetConnection <that address> -Port 38281`
   in PowerShell (it must say `TcpTestSucceeded : True`).
4. **Wait for the host to say the server is running**, then start Satisfactory through the Mod Manager or your usual
   shortcut and create a **new game**.
5. In the new game screen, click **Mod Savegame Settings** (bottom right) and fill in:
   - **Server URI**: `<host address>:38281`
   - **User Name**: exactly the player name of your YAML
   - **Password**: empty unless the host gave you one
6. When the world loads, the in-game chat says you are connected to the Archipelago server. Type `/help` in the
   chat for the commands (they have no `!` in Satisfactory).
7. If the connection is refused: check that the host's server is running, that you are on the same private
   network (or that the port is open), and that the name matches the YAML.
