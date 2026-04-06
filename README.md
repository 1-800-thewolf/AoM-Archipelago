![randomizer thumbnail](https://github.com/user-attachments/assets/db65528f-16f9-4459-aa71-b75256ac5a51)

## Age of Mythology: Retold — Fall of the Trident Archipelago Randomizer

An [Archipelago](https://archipelago.gg) multiworld randomizer for the **Fall of the Trident** campaign in Age of Mythology: Retold.

Current version: **0.1.2**

---

## What Is This?

This mod transforms the Fall of the Trident campaign into an Archipelago multiworld randomizer. Instead of progressing through the campaign in order and completing missions normally, items are shuffled into a randomized pool.

You might start a scenario unable to advance beyond the Classical Age, and the only military units you can train are myth units. You might find an upgrade giving Arkantos lifesteal and a petrifying shout.

**What is Archipelago?**
Archipelago is a free, open-source multiworld randomizer platform that connects players across dozens of different games simultaneously. Each player randomizes their own game, and items from one game can appear in another player's world. Learn more at [archipelago.gg](https://archipelago.gg).

> Archipelago also supports solo play if you want to play Fall of the Trident Archipelago Randomizer on your own.

---

## Features

**32 randomized scenarios** across the Greek, Egyptian, Norse, and Final campaign sections. All sections unlock independently — finding the Egyptian Scenarios item immediately opens missions 11–20 regardless of Greek progress.

**Over 150 items** in the pool, including:
- Hero special abilities (Arkantos lifesteal, Ajax shield bash in an area, Chiron poison arrow, Amanra reincarnating enemies as minions, and more)
- Progressive Age Unlock items (Classical, Heroic, Mythic) per civilization
- Unit unlock items for each civ (Hoplite, Berserk, Spearman, and more)
- Section unlock items (Greek Scenarios, Egyptian Scenarios, Norse Scenarios, Atlantis Key)
- Starting resource and passive income boosts
- Reinforcement units that spawn in your base
- Villager carry capacity and cost upgrades
- Hero stat boosts (HP, Attack, Recharge Time, Regen) for major heroes

**Over 150 locations** across all 32 scenarios — Victory checks and primary objectives.
-Primary Objectives are indicated in the upper right corner in each scenario. Secondary and option objectives aren't locations.

**Logic system** that ensures scenarios are only in logic when you have enough age unlocks and items to reasonably complete them. The game won't expect you to beat a Mythic Age scenario with nothing in your inventory.

**Configurable options** including:
- Starting civilization (Greek, Egyptian, or Norse)
- Starting age unlock items per civilization
- Final section unlock mode (beat X scenarios, Atlantis Key, or always open)
- Hero abilities toggle

---

## How It Works

**The Fall of the Trident Archipelago Randomizer** AoM Mod runs inside Age of Mythology: Retold. It reads a state file to apply received items at the start of each scenario (age unlocks, hero upgrades, unit unlocks, etc.) and fires objective checks to the client as you complete them.

**The Archipelago Client** is a background application that connects to your Archipelago server. It writes the state file the mod reads, polls for completed objective checks during gameplay, and sends and receives items between your game and the multiworld between scenarios.

  Due to AoM XS code limitations, checks can only be received and sent _between_ scenarios. Sorry. If anyone has a concrete solution to this problem, please let me know!

---

## Installation

### Requirements
- [Age of Mythology: Retold (Steam)](https://store.steampowered.com/app/1934680/Age_of_Mythology_Retold/)
- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 0.6.5 or later

### Steps

**1. Install the AoM mod**

Subscribe to the **Fall of the Trident Archipelago Randomizer** mod on the Age of Mythology: Retold mod platform and enable it in your in-game mod manager. Quit AoM and keep the game closed for now.
<img width="1577" height="1276" alt="image" src="https://github.com/user-attachments/assets/0839e1f9-e182-4dad-9ab2-e2dc60c7cb6a" />
<img width="1066" height="298" alt="image" src="https://github.com/user-attachments/assets/a92311d4-3e07-4777-8d30-97bc73e17b70" />
<img width="298" height="166" alt="image" src="https://github.com/user-attachments/assets/03a42723-789a-4d7e-9b97-7b10aeeda7bd" />


**2. Install the apworld**

Download `aom.apworld` from the [latest release](https://github.com/1-800-thewolf/AoM-Archipelago/releases/latest) and launch it, or manually place it in your Archipelago `custom_worlds` folder normally here:
```
C:\ProgramData\Archipelago\custom_worlds\
```

**3. Launch the client**

Open the Archipelago Launcher and select **Age of Mythology Retold Client**. On first launch, a folder picker will appear — navigate to and select your AoM Retold user data folder. This is the folder named after your Steam ID and it's a series of numbers like 12315152:
```
C:\Users\[YourName]\Games\Age of Mythology Retold\[SteamID]\
```
<img width="790" height="246" alt="image" src="https://github.com/user-attachments/assets/3a4f2c7b-1840-416b-9f3f-e00c83f639d9" />

**4. Connect to your server**
Connect to your Archipelago server using the client as you would with any other AP game. The client will automatically install the required trigger files into your game folder on first connect. Make sure AoM is closed the very first time you connect.
The general process for this step is this:
1. [Archipelago guides and overview](https://archipelago.gg/tutorial/)
2. [Generate a game in your own Archipelago Client](https://archipelago.gg/tutorial/Archipelago/setup_en#generating-a-game)
3. [Host the game on the website](https://archipelago.gg/tutorial/Archipelago/setup_en#hosting-an-archipelago-server)
4. [Connect to the Archipelago server](https://archipelago.gg/tutorial/Archipelago/setup_en#connecting-to-an-archipelago-server)

**Important**: Connect to your Archipelago server with AoM _closed_ the first time you play. The client sets up required files on first connect and if AoM is already running, they won't load correctly.

**5. Play**

Launch scenarios through the in-game mod, not the vanilla campaign menu. The Archipelago client must be running and connected while you play.
<img width="1143" height="761" alt="image" src="https://github.com/user-attachments/assets/b29fa941-f570-4369-8a3a-338d7be8b3dd" />
<img width="861" height="511" alt="image" src="https://github.com/user-attachments/assets/78d9cf4f-056a-4e41-9fb3-dc51f4b57422" />
<img width="509" height="441" alt="image" src="https://github.com/user-attachments/assets/dab9476d-5dda-48ff-bb48-8cb68c06a178" />


**6. Move the mod to your local folder**

Only if the campaign doesn't appear under "Custom Campaigns" in step 5, move the mod from your "subscribed" mod folder to your "local" mod folder.

Copy it away from here:
C:\Users\[YourName]\Games\Age of Mythology Retold\[SteamID]\mods\subscribed
<img width="970" height="276" alt="image" src="https://github.com/user-attachments/assets/4faf0b81-ada1-4bfb-b34a-705a6c1c21c2" />


Paste it here:
C:\Users\[YourName]\Games\Age of Mythology Retold\[SteamID]\mods\local
 <img width="970" height="276" alt="image" src="https://github.com/user-attachments/assets/a95b0069-ec1b-415c-af4d-dd91e95ed5a0" />

Return to step 5
---

## Generating a Game

To generate a multiworld, each player needs a YAML configuration file. Generate a template from the Archipelago launcher or copy the example in the repository as a starting point.

Key options to consider:
- `starting_scenarios` — which civilization to begin with (greek is recommended for the first time)
- `final_scenarios` — what unlocks the last two missions (beat_x_scenarios is recommended)
- `x_scenarios` — how many missions to beat before the final section opens.
- `hero_abilities` — include hero special ability items in the pool (recommended: true). The randomizer is much harder with this turned off.

---

## Notes

- The mod must be **enabled** in the AoM Retold mod manager before launching a scenario. Game updates may disable mods — re-enable after any update.
- The client must remain running and connected throughout your play session for checks to register.

---

For support, questions, and discussion, please join us on the [AoM:R Archipelago discord](https://discord.com/channels/731205301247803413/1302047515482390588).

Link to the [Archipelago Discord](https://discord.gg/archipelago) if you're not already a member.

---

## Credits

Developed by **1.800.thewolf**

Thanks to the Archipelago and Age of Mythology Modding community for tooling, documentation, and support.
