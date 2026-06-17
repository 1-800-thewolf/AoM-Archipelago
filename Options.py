# =============================================================================
# Age of Mythology Retold — YAML Option Definitions
# =============================================================================
#
# Every player-facing option is defined here as an Archipelago `Choice`,
# `Range`, or `Toggle` subclass.  The `AomOptions` dataclass at the bottom
# binds each class to its YAML key — that is the single source of truth used
# by the Archipelago framework to parse YAMLs and by `aomWorld.options` at
# runtime.
#
# Lifecycle:
#   * The Archipelago website reads the option metadata (display_name,
#     internal_name, defaults, docstring) and renders the YAML template.
#   * At generation time the framework instantiates `AomOptions`, which
#     populates `self.options` on `aomWorld`.
#   * `aomWorld.generate_early()` (in __init__.py) reads `self.options.<x>.value`
#     to drive every world-shaping decision (excluded civs, disabled campaigns,
#     gem shop generation, etc.).  See the data-flow diagram in __init__.py.
#   * Many options are echoed into `fill_slot_data()` so the running game
#     client (client/ApClient.py + client/GameClient.py) can branch on them.
#
# Web display order is controlled by `aomWorld.web.option_groups` over in
# __init__.py — keep that list in sync when adding new options.
#
# -----------------------------------------------------------------------------
# ADDING A NEW OPTION
# -----------------------------------------------------------------------------
#   1. Subclass `Choice`/`Range`/`Toggle` here with `internal_name`,
#      `display_name`, defaults, and a docstring (the docstring becomes the
#      tooltip / YAML comment shown to players).
#   2. Add a field on `AomOptions` whose attribute name matches
#      `internal_name`.
#   3. Import the class in __init__.py and (if user-facing) add it to a group
#      in `aomWorld.web.option_groups`.
#   4. Read the value in `generate_early()` (or wherever applies) via
#      `self.options.<name>.value`.
#   5. If the running game needs to know about the option, surface it from
#      `fill_slot_data()` and consume it in client/ApClient.py + GameClient.py
#      (XS emitter).
#
# Disabling civs / campaigns:
#   The `shuffle_<civ>_major_gods` toggles drive `excluded_civs`, and the
#   `<campaign>_campaign` toggles drive `disabled_campaigns`.  Items.py and
#   Locations.py honor these by skipping civ-tagged items and excluded
#   campaigns; Rules.py honors them by skipping rules for missing locations.
# =============================================================================

from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range, StartInventoryPool, Toggle


# ################
# # Goal Options #
# ################
#
# class Goal(Choice):
#     """Goal for this playthrough.
#
# fott_32_victory:
# Beat scenario 32, A Place in My Dreams, to win.
# Note: Beating scenario 32 requires all 3 Progressive Age Unlock items for whatever the civilization is for that scenario (vanilla Greek)
# (the Mythic Age is needed to build the Wonder)."""
#     internal_name = "goal"
#     display_name = "Goal"
#     option_fott_32_victory = 0
#     default = option_fott_32_victory


#####################
# Starting Campaign #
#####################

class StartingScenarios(Choice):
    """Which civilization block is unlocked at the start? All other enabled campaigns start locked.

greek:        Scenarios 1-10 (Fall of the Trident: Greek)
egyptian:     Scenarios 11-20 (Fall of the Trident: Egyptian)
norse:        Scenarios 21-30 (Fall of the Trident: Norse)
new_atlantis: Start with the New Atlantis Campaign.
pillars: Start with the Pillars of the Gods Campaign.

Starting with the Greek block is the easiest."""
    internal_name = "starting_scenarios"
    display_name = "Starting Scenarios"
    option_greek        = 0
    option_egyptian     = 1
    option_norse        = 2
    option_new_atlantis = 3
    option_pillars = 4
    default = option_greek


class FinalScenarios(Choice):
    """What unlocks the Final scenario block (scenarios 31-32)?

beat_x_scenarios (recommended):
Beat the chosen number of scenarios (set via x_scenarios below) to receive the Atlantis Key and open the Final section.

always_open:
The Final section is available from the start. This can result in a much shorter experience.

atlantis_key:
The Atlantis Key is shuffled randomly into the item pool. Finding it anywhere opens the Final section."""
    internal_name = "final_scenarios"
    display_name = "Final Scenarios"
    option_beat_x_scenarios = 0
    option_always_open      = 1
    option_atlantis_key     = 2
    default = option_beat_x_scenarios


class XScenarios(Range):
    """If Final Scenarios (above) is set to beat_x_scenarios, this is how many scenarios must be completed before you receive the Atlantis Key.

You may beat any combination of scenarios from any activated campaigns. 
(46 requires beats all 30 Fall of the Trident, all 12 New Atlantis, and all 4 Golden Gift scenarios)
****Updated to 54 max for PoTG"""

    internal_name = "x_scenarios"
    display_name = "X Scenarios"
    range_start = 0
    range_end   = 54
    default     = 12


class ExtraFinalMissionAgeUnlocks(Range):
    """Scenario 32 normally requires 3 Age Unlock items to reach the Mythic Age and build the Wonder. 
This adds extra copies of whichever civilization's Age Unlock corresponds to the god assigned to scenario 32 (Greek by default, or randomized if Random Major gods is enabled).

At the default of 1, there are 4 total copies of that unlock in the pool."""
    internal_name = "extra_final_mission_age_unlocks"
    display_name = "Extra Final Mission Age Unlocks"
    range_start = 0
    range_end   = 5
    default     = 1


#################
# Gem Shop      #
#################

class GemShop(Toggle):
    """
    Enable the Gem Shop.

    When enabled: beating scenarios earns Gems (currency). Spend them in the shop to receive items and hints.
    Gem Shop is accessible from the AoM AP Launcher window.

    When disabled: victories award random multiworld items instead of Gems and you can't enter the shop.
    """
    internal_name = "gem_shop"
    display_name = "Gem Shop"
    default = 1


class WinsToOpenShop(Range):
    """
    Number of scenario victories required to open each additional shop tier (only used when Gem Shop is enabled).
    Shop A is always open. Shop B opens after this many wins. Shop C opens after 2x wins. Shop D opens after 3x wins.
    Set to 0 to open all shops immediately.
    """
    internal_name = "wins_to_open_shop"
    display_name  = "Wins to Open Shop"
    range_start   = 0
    range_end     = 10
    default       = 4


class MaxProgressionItemsInEachShop(Range):
    """
    Maximum number of progression items allowed in each non-first shop (Shop B, Shop C, Shop D).

    Set to 0 to forbid progression items in shops entirely (recommended). Set to 15 to allow every slot in those 3 shops to hold any item.

    Careful setting this too high as you can't grind gems. If you spend your gems unwisely, you could softlock the seed. (If that happens you can use JUNK FOOD NIGHT to cheat)
    """
    internal_name = "max_progression_items_in_each_shop"
    display_name  = "Max Progression Items In Each Shop"
    range_start   = 0
    range_end     = 15
    default       = 0


#############
# Item Pool #
#############

class Random_Major_Gods(Toggle):
    """Randomize the major god for each scenario at generation time. The assigned god determines which techs and minor gods are available.
    Think on your feet with this turned on."""
    internal_name = "random_major_gods"
    display_name = "Random Major gods"
    default = 1


class ForceDifferentGod(Toggle):
    """When random_major_gods is enabled, forces the random god to never be the vanilla major god for that scenario and makes it more likely to play a civilization different from the vanilla.
(e.g. 1. Omens is normally Poseidon, so you'll never play Poseidon on that mission with this on, and Zeus, Hades, and Demeter are much less likely)"""
    internal_name = "force_different_god"
    display_name = "Force Different Major god"
    default = 1


class HeroAbilities(Toggle):
    """Include custom hero special ability items in the item pool?

enabled (true):
Recommended setting for an exciting, hero-focused campaign.
The following items are included:

Arkantos:
  - Arkantos Lifesteal         (Arkantos' melee attacks heal him)
  - Arkantos Petrifying Shout  (shout ability petrifies and damages nearby enemies)
  - Arkantos is a House        (Arkantos provides +10 population capacity)
  - Arkantos Attack Speed      (increases melee attack speed)

Ajax:
  - Ajax Stunning Blow         (shield bash stuns the target for 10 seconds)
  - Ajax Smiting Strikes       (melee attacks temporarily reduce target's max HP)
  - Ajax Shield Bash AOE       (shield bash hits a wide area)

Chiron:
  - Chiron Poison Arrow        (arrows apply a poison damage over time)
  - Chiron Crippling Fire      (arrows slow the target's attack rate significantly)
  - Chiron Shotgun Special     (special shot fires a ton of extra arrows)

Amanra:
  - Amanra Whirlwind Throw     (leap attack sends targets flying)
  - Amanra Army of the Dead    (enemies slain by Amanra are reincarnated as allied minions)
  - Amanra Divine Smite        (melee attacks deal +5 divine damage)

Odysseus:
  - Odysseus Entangling Shot   (special shot snares the targets' movement for 10 seconds)
  - Odysseus Swift Escape      (ranged attacks cripple the target's speed)
  - Odysseus Perfect Accuracy  (ranged attacks never miss)

Reginleif:
  - Reginleif Frost Strike     (javelins progressively freeze the target)
  - Reginleif +1 Projectile    (fire an additional javelin)

Kastor (only in pool when New Atlantis campaign is enabled):
  - Kastor Undermines with Attacks  (melee attacks deal large damage over time to buildings)
  - Kastor Can Summon Soldiers      (Kastor can train Hoplites, Spearmen, Berserks, Murmillos, Yari Spearmen, Tlamanih Spearmen, Dao Swordsmen, Prodromos, War Elephants, Jarls, Destroyers, Samurai, Shorn Ones, and Tiger Cavalry)
  - Kastor is a Manor               (Kastor provides +20 population capacity)

disabled (false):
All above hero ability items are removed from the pool and replaced with
filler. Removing these makes the game much harder and less hero-focused."""
    internal_name = "hero_abilities"
    display_name = "Hero Abilities"
    default = 1


####################
# Options Dataclass #
####################


class TrapPercentage(Range):
    """
    Percentage of filler items to replace with traps (0 = no traps, 100 = all filler becomes traps).
    Traps fire randomly during scenarios. Only filler items are replaced; useful items are never swapped for traps.
    """
    internal_name = "trap_percentage"
    display_name  = "Trap Percentage"
    range_start   = 0
    range_end     = 100
    default       = 25

class LocalFillerFrequency(Range):
    """
    Percentage of filler items that will be placed locally in your own world instead of the shared multiworld pool.
    0 = all filler goes into the shared pool (default, fully multiworld).
    75 = up to 75% of filler items are guaranteed to stay in your own game.
    Has no effect in single-player games (all items are local anyway).
    """
    internal_name = "local_filler_frequency"
    display_name  = "Local Filler Frequency"
    range_start   = 0
    range_end     = 75
    default       = 0



class GreekMajorGods(Toggle):
    """Include Greek major gods in the random major god pool. Turn this off to never play as the Greeks.
Only applies when Random Major gods is enabled."""
    internal_name = "shuffle_greek_major_gods"
    display_name  = "Shuffle Greek Major gods"
    default = 1


class EgyptianMajorGods(Toggle):
    """Include Egyptian major gods in the random major god pool. Turn this off to never play as the Egyptians.
Only applies when Random Major gods is enabled."""
    internal_name = "shuffle_egyptian_major_gods"
    display_name  = "Shuffle Egyptian Major gods"
    default = 1


class NorseMajorGods(Toggle):
    """Include Norse major gods in the random major god pool. Turn this off to never play as the Norse.
Only applies when Random Major gods is enabled."""
    internal_name = "shuffle_norse_major_gods"
    display_name  = "Shuffle Norse Major gods"
    default = 1


class AtlanteanMajorGods(Toggle):
    """Include Atlantean major gods in the random major god pool. Turn this off to never play as the Atlanteans.
Only applies when Random Major gods is enabled."""
    internal_name = "shuffle_atlantean_major_gods"
    display_name  = "Shuffle Atlantean Major gods"
    default = 1


class ChineseMajorGods(Toggle):
    """Include Chinese major gods in the random major god pool. Turn this off to never play as the Chinese.
If you don't have the Chinese DLC, Favored Land won't work for you and some graphics may look wrong. Buy the Chinese DLC for best results, but you can still play as them even if you don't have the DLC.
Only applies when Random Major gods is enabled."""
    internal_name = "shuffle_chinese_major_gods"
    display_name  = "Shuffle Chinese Major gods"
    default = 0


class JapaneseMajorGods(Toggle):
    """Include Japanese major gods in the random major god pool. Turn this off to never play as the Japanese.
If you don't have the Japanese DLC, Japanese Experience Points won't work for you and some graphics may look wrong. Buy the Japanese DLC for best results, but you can still play as them even if you don't have the DLC.
Only applies when Random Major gods is enabled."""
    internal_name = "shuffle_japanese_major_gods"
    display_name  = "Shuffle Japanese Major gods"
    default = 0


class AztecMajorGods(Toggle):
    """Include Aztec major gods in the random major god pool. Turn this off to never play as the Aztecs.
    If you don't have the Aztec DLC, Aztec Tonalli favor won't work for you and some graphics may look wrong. Buy the Aztec DLC for best results, but you can still play as them even if you don't have the DLC. 
    Only applies when Random Major gods is enabled."""
    internal_name = "shuffle_aztec_major_gods"
    display_name  = "Shuffle Aztec Major gods"
    default = 0


# class MoreFrequentDLCGods(Toggle):
#     """Demeter and Freyr are more likely as random major gods.
#     If the random major god is Greek, you're more likely to play as Demeter and if the random major god is Norse Freyr is more likely.
#     Yes, you can actually play as these even if you don't have the DLC.
#     Only applies when Random Major gods is enabled."""
#     internal_name = "more_frequent_dlc_gods"
#     display_name  = "More Frequent DLC gods"
#     default = 0


class FottGreekCampaign(Toggle):
    """Include the Fall of the Trident: Greek campaign (scenarios 1-10).
When disabled, those 10 scenarios are unplayable and are removed from the pool."""
    internal_name = "fott_greek_campaign"
    display_name  = "FotT Greek Campaign"
    default = 1


class FottEgyptianCampaign(Toggle):
    """Include the Fall of the Trident: Egyptian campaign (scenarios 11-20).
When disabled, those 10 scenarios are unplayable and are removed from the pool."""
    internal_name = "fott_egyptian_campaign"
    display_name  = "FotT Egyptian Campaign"
    default = 1


class FottNorseCampaign(Toggle):
    """Include the Fall of the Trident: Norse campaign (scenarios 21-30).
When disabled, those 10 scenarios are unplayable and are removed from the pool."""
    internal_name = "fott_norse_campaign"
    display_name  = "FotT Norse Campaign"
    default = 1


class NewAtlantis(Toggle):
    """Include The New Atlantis campaign.
    When disabled, those 12 scenarios are unplayable and are removed from the pool."""
    internal_name = "new_atlantis_campaign"
    display_name  = "New Atlantis Campaign"
    default = 0


class GoldenGift(Toggle):
    """Include The Golden Gift campaign.
When disabled, those 4 scenarios are unplayable and are removed from the pool."""
    internal_name = "golden_gift_campaign"
    display_name  = "Golden Gift Campaign"
    default = 0

class PillarsOfTheGods(Toggle):
    """Include The Pillars of The Gods campaign.
    When disabled, those 9 scenarios are unplayable and are removed from the pool."""
    internal_name = "pillars_of_the_gods"
    display_name = "Pillars of The Gods Campaign"
    default = 0

class MaxKeysOnKeyrings(Range):
    """Maximum number of Scenario Keys carried by a Key Ring item.

When more than 0, every scenario is locked behind a Scenario Key and one or more Scenario Keys are found on Key Ring items.
When you or any other player in the multiworld finds a Key Ring, every Scenario Key on that ring is delivered to you.

You begin with one starter Key Ring which includes at least one scenario you can attempt immediately. The remaining rings are shuffled into the item pool.

To Turn this Off:
0 — feature disabled; scenarios are not locked behind keys at all. Unlocking a campaign gives you access to all the scenarios in that branch.
"""
    internal_name = "max_keys_on_keyrings"
    display_name  = "Max Keys on Keyrings"
    range_start   = 0
    range_end     = 15
    default       = 0


class Relicsanity(Toggle):
    """Include Relicsanity locations in the pool.

When enabled, every relic in the campaigns becomes its own check — garrisoning a relic in a Temple sends a check to the multiworld.
Roughly doubles locations and items in your world.
"""
    internal_name = "relicsanity"
    display_name  = "Relicsanity"
    default = 0


class OptionalObjectivesAreLocations(Toggle):
    """Turn each scenario's optional (secondary) objectives into Archipelago locations.
    """
    internal_name = "optional_objectives_are_locations"
    display_name  = "Optional Objectives Are Locations"
    default = 0


@dataclass
class AomOptions(PerGameCommonOptions):
    """All options for the Age of Mythology Retold Archipelago world."""
    start_inventory_from_pool:          StartInventoryPool
    # goal:                             Goal  # hidden from players; uncomment to re-expose
    gem_shop:                           GemShop
    wins_to_open_shop:                  WinsToOpenShop
    max_progression_items_in_each_shop: MaxProgressionItemsInEachShop
    fott_greek_campaign:                FottGreekCampaign
    fott_egyptian_campaign:             FottEgyptianCampaign
    fott_norse_campaign:                FottNorseCampaign
    new_atlantis_campaign:              NewAtlantis
    golden_gift_campaign:               GoldenGift
    pillars_of_the_gods:                PillarsOfTheGods
    relicsanity:                        Relicsanity
    optional_objectives_are_locations:  OptionalObjectivesAreLocations
    max_keys_on_keyrings:               MaxKeysOnKeyrings
    starting_scenarios:                 StartingScenarios
    final_scenarios:                    FinalScenarios
    x_scenarios:                        XScenarios
    random_major_gods:                  Random_Major_Gods
    force_different_god:                ForceDifferentGod
    shuffle_greek_major_gods:           GreekMajorGods
    shuffle_egyptian_major_gods:        EgyptianMajorGods
    shuffle_norse_major_gods:           NorseMajorGods
    shuffle_atlantean_major_gods:       AtlanteanMajorGods
    shuffle_chinese_major_gods:         ChineseMajorGods
    shuffle_japanese_major_gods:        JapaneseMajorGods
    shuffle_aztec_major_gods:           AztecMajorGods
    # more_frequent_dlc_gods:           MoreFrequentDLCGods  # hidden from players; uncomment to re-expose
    extra_final_mission_age_unlocks:    ExtraFinalMissionAgeUnlocks
    hero_abilities:                     HeroAbilities
    local_filler_frequency:             LocalFillerFrequency
    trap_percentage:                    TrapPercentage
