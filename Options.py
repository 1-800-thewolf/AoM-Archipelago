from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range, StartInventoryPool, Toggle


################
# Goal Options #
################

class Goal(Choice):
    """Goal for this playthrough.

fott_32_victory:
Beat scenario 32, A Place in My Dreams, to win.
Note: Beating scenario 32 requires all 3 Progressive Age Unlock items for whatever the civilization is for that scenario (vanilla Greek)
(the Mythic Age is needed to build the Wonder)."""
    internal_name = "goal"
    display_name = "Goal"
    option_fott_32_victory = 0
    default = option_fott_32_victory


##################
# Starting Setup #
##################

class StartingScenarios(Choice):
    """Which civilization block is unlocked at the start?

greek:        Scenarios 1-10 (Fall of the Trident: Greek)
egyptian:     Scenarios 11-20 (Fall of the Trident: Egyptian)
norse:        Scenarios 21-30 (Fall of the Trident: Norse)
new_atlantis: Start with the New Atlantis Campaign. All of Fall of the Trident is locked until you find unlock items.
              Requires new_atlantis_campaign to be enabled.

The other FotT sections must be found as items in the pool. Within a section, all scenarios are immediately accessible.

Starting with the Greek block is the easiest."""
    internal_name = "starting_scenarios"
    display_name = "Starting Scenarios"
    option_greek        = 0
    option_egyptian     = 1
    option_norse        = 2
    option_new_atlantis = 3
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
(46 requires beats all 30 Fall of the Trident, all 12 New Atlantis, and all 4 Golden Gift scenarios)"""
    internal_name = "x_scenarios"
    display_name = "X Scenarios"
    range_start = 0
    range_end   = 46
    default     = 12


class ExtraFinalMissionAgeUnlocks(Range):
    """Scenario 32 requires 3 Age Unlock items to reach the Mythic Age and build the Wonder. 
This adds extra copies of whichever civilization's Age Unlock corresponds to the god assigned to scenario 32 (Greek by default, or randomized if Random Major Gods is enabled).

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

    When enabled: beating scenarios earns Gems (currency), which are spent in the shop to receive items and hints. The shop scenario is accessible from the campaign menu.

    When disabled: victories award random multiworld items instead of Gems,
    the shop scenario returns the player to the menu immediately, and no
    shop-related items or locations are generated.
    """
    internal_name = "gem_shop"
    display_name = "Gem Shop"
    default = 1


class WinsToOpenShop(Range):
    """
    Number of scenario victories required to open each additional shop tier (only used when Gem Shop is enabled).
    Shop A (Marsh) is always open. Shop B (Desert) opens after this many wins. Shop C (Grass) opens after 2x wins. Shop D (Hades) opens after 3x wins.
    Set to 0 to open all shops immediately.
    """
    internal_name = "wins_to_open_shop"
    display_name  = "Wins to Open Shop"
    range_start   = 0
    range_end     = 10
    default       = 4


#############
# Item Pool #
#############

class Random_Major_Gods(Toggle):
    """Randomize the major god for each scenario at generation time. The assigned god determines which techs and minor gods are available.
Be ready to think on your feat with this turned on."""
    internal_name = "random_major_gods"
    display_name = "random_major_gods"
    default = 1


class ForceDifferentGod(Toggle):
    """When random_major_gods is enabled, forces the random god to never be the vanilla major god for that scenario and makes it more likely to play a civilization different from the vanilla.
(e.g. 1. Omens is normally Poseidon, so you'll never play Poseidon on that mission with this on, and Zeus and Hades are much less likely)"""
    internal_name = "force_different_god"
    display_name = "Force Different Major God"
    default = 1


class MythUnitSanity(Toggle):
    """Include myth unit tier unlock items in the pool.
When enabled, all myth units are forbidden at the start and must be unlocked by finding the corresponding tier item.
Turn this off for an easier time, but there will be very little variety in playstyle."""
    internal_name = "myth_unit_sanity"
    display_name = "Shuffle Myth Unit Unlocks"
    default = 1


class HeroAbilities(Toggle):
    """Include custom hero special ability items in the item pool?

enabled (true):
Recommended setting for an exciting, hero-focued campaign.
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
  - Reginleif Frost Strike     (arrows progressively freeze the target)
  - Reginleif +1 Projectile    (fire an additional javelin)

Kastor (only in pool when New Atlantis campaign is enabled):
  - Kastor Undermines with Attacks  (melee attacks deal large damage over time to buildings)
  - Kastor Can Summon Soldiers      (Kastor can train Hoplites, Spearmen, Berserks, and Murmillos)
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
    At 20%, there will be roughly 15 traps total.
    """
    internal_name = "trap_percentage"
    display_name  = "Trap Percentage"
    range_start   = 0
    range_end     = 100
    default       = 20

class UpdateBuildingsForRandomGod(Toggle):
    """
    When Random_Major_Gods is enabled, transform your starting military buildings to match the randomly assigned civilization.
    For example, 1. Omens is normally Greek. If you're randomly assigned Set, the Military Academies and Archery Ranges are transformed into Egyptian Barracks.
    """
    internal_name = "update_buildings_for_random_god"
    display_name  = "Update Buildings for Random God"
    default = 1




class GreekMajorGods(Toggle):
    """Include Greek major gods in the random major god pool. Turn this off to never play as the Greeks.
Only applies when Random Major Gods is enabled."""
    internal_name = "shuffle_greek_major_gods"
    display_name  = "Shuffle Greek Major Gods"
    default = 1


class EgyptianMajorGods(Toggle):
    """Include Egyptian major gods in the random major god pool. Turn this off to never play as the Egyptians.
Only applies when Random Major Gods is enabled."""
    internal_name = "shuffle_egyptian_major_gods"
    display_name  = "Shuffle Egyptian Major Gods"
    default = 1


class NorseMajorGods(Toggle):
    """Include Norse major gods in the random major god pool. Turn this off to never play as the Norse.
Only applies when Random Major Gods is enabled."""
    internal_name = "shuffle_norse_major_gods"
    display_name  = "Shuffle Norse Major Gods"
    default = 1


class AtlanteanMajorGods(Toggle):
    """Include Atlantean major gods in the random major god pool. Turn this off to never play as the Atlanteans
Only applies when Random Major Gods is enabled."""
    internal_name = "shuffle_atlantean_major_gods"
    display_name  = "Shuffle Atlantean Major Gods"
    default = 1


class FottGreekCampaign(Toggle):
    """Include the Fall of the Trident: Greek campaign (scenarios 1-10).
When disabled, FotT scenarios 1-10 are removed from the pool."""
    internal_name = "fott_greek_campaign"
    display_name  = "FotT Greek Campaign"
    default = 1


class FottEgyptianCampaign(Toggle):
    """Include the Fall of the Trident: Egyptian campaign (scenarios 11-20).
When disabled, FotT scenarios 11-20 are removed from the pool."""
    internal_name = "fott_egyptian_campaign"
    display_name  = "FotT Egyptian Campaign"
    default = 1


class FottNorseCampaign(Toggle):
    """Include the Fall of the Trident: Norse campaign (scenarios 21-30).
When disabled, FotT scenarios 21-30 are removed from the pool."""
    internal_name = "fott_norse_campaign"
    display_name  = "FotT Norse Campaign"
    default = 1


class NewAtlantis(Toggle):
    """Include The New Atlantis campaign.
     When disabled, all 12 New Atlantis scenarios are removed from the pool."""
    internal_name = "new_atlantis_campaign"
    display_name  = "New Atlantis Campaign"
    default = 0


class GoldenGift(Toggle):
    """Include The Golden Gift campaign.
When disabled, all 4 Golden Gift scenarios are removed from the pool."""
    internal_name = "golden_gift_campaign"
    display_name  = "Golden Gift Campaign"
    default = 0


class Relicsanity(Toggle):
    """Include Relicsanity locations in the pool.

When enabled, every relic in the campaigns becomes its own check — garrisoning a relic in a Temple sends a check to the multiworld.
174 total relic locations across all campaigns: 103 in Fall of the Trident, 51 in The New Atlantis, 20 in The Golden Gift.
Relics in disabled campaigns are removed alongside that campaign's other locations."""
    internal_name = "relicsanity"
    display_name  = "Relicsanity"
    default = 0


@dataclass
class AomOptions(PerGameCommonOptions):
    """All options for the Age of Mythology Retold Archipelago world."""
    start_inventory_from_pool:       StartInventoryPool
    goal:                            Goal
    starting_scenarios:              StartingScenarios
    final_scenarios:                 FinalScenarios
    x_scenarios:                     XScenarios
    extra_final_mission_age_unlocks: ExtraFinalMissionAgeUnlocks
    gem_shop:                        GemShop
    wins_to_open_shop:               WinsToOpenShop
    random_major_gods:                       Random_Major_Gods
    force_different_god:                ForceDifferentGod
    myth_unit_sanity:                MythUnitSanity
    hero_abilities:                  HeroAbilities
    trap_percentage:                 TrapPercentage
    update_buildings_for_random_god: UpdateBuildingsForRandomGod
    shuffle_greek_major_gods:        GreekMajorGods
    shuffle_egyptian_major_gods:     EgyptianMajorGods
    shuffle_norse_major_gods:        NorseMajorGods
    shuffle_atlantean_major_gods:    AtlanteanMajorGods
    fott_greek_campaign:             FottGreekCampaign
    fott_egyptian_campaign:          FottEgyptianCampaign
    fott_norse_campaign:             FottNorseCampaign
    new_atlantis_campaign:           NewAtlantis
    golden_gift_campaign:            GoldenGift
    relicsanity:                     Relicsanity
