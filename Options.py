from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range, StartInventoryPool, Toggle


################
# Goal Options #
################

class Goal(Choice):
    """
    Goal for this playthrough.

    fott_32_victory:
    Beat scenario 32, A Place in My Dreams, to win.
    Note: Beating scenario 32 requires all 3 Progressive Greek Age Unlock items
    (the Mythic Age is needed to build the Wonder).
    """
    internal_name = "goal"
    display_name = "Goal"

    option_fott_32_victory = 0
    default = option_fott_32_victory


##################
# Starting Setup #
##################

class StartingScenarios(Choice):
    """
    Which civilization block is unlocked at the start?

    greek:    Scenarios 1-10
    egyptian: Scenarios 11-20
    norse:    Scenarios 21-30

    The other two sections must be found as items in the pool. Within a section, all scenarios are immediately accessible.

    Starting with the Greek block is the easiest.
    """
    internal_name = "starting_scenarios"
    display_name = "Starting Scenarios"

    option_greek    = 0
    option_egyptian = 1
    option_norse    = 2

    default = option_greek


class StartingGreekAgeUnlocks(Range):
    """
    You cannot advance ages until you have received enough Progressive Age Unlock items. For each civilization:
      1st unlock = Classical Age available
      2nd unlock = Heroic Age available
      3rd unlock = Mythic Age available

    Scenarios will not be in logic until you can reach a reasonable age to beat them.
    Starting with unlocks makes more scenarios accessible earlier and a much easier experience.

    ---

    Number of Progressive Greek Age Unlock items with which to start:
    """
    internal_name = "starting_greek_age_unlocks"
    display_name = "Starting Greek Age Unlocks"

    range_start = 0
    range_end   = 3
    default     = 0


class StartingEgyptianAgeUnlocks(Range):
    """
    Number of Progressive Egyptian Age Unlock items with which to start:
    """
    internal_name = "starting_egyptian_age_unlocks"
    display_name = "Starting Egyptian Age Unlocks"

    range_start = 0
    range_end   = 3
    default     = 0


class StartingNorseAgeUnlocks(Range):
    """
    Number of Progressive Norse Age Unlock items with which to start:
    """
    internal_name = "starting_norse_age_unlocks"
    display_name = "Starting Norse Age Unlocks"

    range_start = 0
    range_end   = 3
    default     = 0


#################
# Final Section #
#################

class FinalScenarios(Choice):
    """
    What unlocks the Final scenario block (scenarios 31-32)?

    beat_x_scenarios (recommended):
    Beat the chosen number of scenarios (set via x_scenarios below) to receive the Atlantis Key and open the Final section.

    always_open:
    The Final section is available from the start. This can result in a much shorter experience.

    atlantis_key:
    The Atlantis Key is shuffled randomly into the item pool. Finding it anywhere opens the Final section.
    """
    internal_name = "final_scenarios"
    display_name = "Final Scenarios"

    option_beat_x_scenarios = 0
    option_always_open      = 1
    option_atlantis_key     = 2

    default = option_beat_x_scenarios


class XScenarios(Range):
    """
    If Final Scenarios (above) is set to beat_x_scenarios, this is how many scenarios must be completed before you receive the Atlantis Key.

    You may beat any combination of the 30 non-final scenarios.
    """
    internal_name = "x_scenarios"
    display_name = "X Scenarios"

    range_start = 0
    range_end   = 30
    default     = 12


#############
# Item Pool #
#############

class ExtraFinalMissionAgeUnlocks(Range):
    """
    Scenario 32 requires 3 Age Unlock items to reach the Mythic Age and build the Wonder. 
    This adds extra copies of whichever civilization's Age Unlock corresponds to the god assigned to scenario 32 (Greek by default, or randomized if godsanity is enabled). These replace filler items.

    At the default of 1, there are 4 total copies of that unlock in the pool.
    """
    internal_name = "extra_final_mission_age_unlocks"
    display_name = "Extra Final Mission Age Unlocks"

    range_start = 0
    range_end   = 5
    default     = 1


class Godsanity(Toggle):
    """
    Randomize the major god for each scenario at generation time. The assigned god determines which techs and minor gods are available.
    Be ready to think on your feat with this turned on.
    """
    internal_name = "godsanity"
    display_name = "godsanity"
    default = 1


class GodForceChange(Toggle):
    """
    When godsanity is enabled, forces the random god to never be the vanilla major god for that scenario and makes it more likely to play a civilization different from the vanilla.
    (e.g. If 1. Omens is normally Poseidon, you'll never play Poseidon on that mission with this on, and Zeus and Hades are much less likely)
    """
    internal_name = "god_force_change"
    display_name = "God Force Change"
    default = 1


class MythUnitSanity(Toggle):
    """
    Include myth unit tier unlock items in the pool.
    When enabled, all myth units are forbidden at the start and must be unlocked by finding the corresponding tier item.
    Turn this off for an easier time.
    """
    internal_name = "myth_unit_sanity"
    display_name = "Myth Unit Sanity"
    default = 1


class StartingGems(Range):
    """
    Number of Gems to start with.
    Gems are earned by beating scenarios (1 per scenario, up to 31).
    They are spent in the shop to receive items and hints.
    """
    internal_name = "starting_gems"
    display_name  = "Starting Gems"
    range_start   = 0
    range_end     = 10
    default       = 3


class WinsToOpenShop(Range):
    """
    Number of scenario victories required to open each additional shop tier.
    Shop A is always open (no requirement).
    Shop B opens after this many wins.
    Shop C opens after 2x this many wins.
    Shop D opens after 3x this many wins.

    Set to 0 to open all shops immediately.
    At the maximum of 10: Shop B at 10 wins, Shop C at 20 wins, Shop D at 30 wins.
    """
    internal_name = "wins_to_open_shop"
    display_name  = "Wins to Open Shop"
    range_start   = 0
    range_end     = 10
    default       = 5


class HeroAbilities(Toggle):



    """
    Include custom hero special ability items in the item pool?

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

    disabled (false):
    All above hero ability items are removed from the pool and replaced with
    filler. Removing these makes the game much harder and less hero-focused.
    """
    internal_name = "hero_abilities"
    display_name = "Hero Abilities"

    default = 1  # enabled


####################
# Options Dataclass #
####################

@dataclass
class AomOptions(PerGameCommonOptions):
    """All options for the Age of Mythology Retold Archipelago world."""
    start_inventory_from_pool:       StartInventoryPool
    goal:                            Goal
    starting_scenarios:              StartingScenarios
    starting_greek_age_unlocks:      StartingGreekAgeUnlocks
    starting_egyptian_age_unlocks:   StartingEgyptianAgeUnlocks
    starting_norse_age_unlocks:      StartingNorseAgeUnlocks
    final_scenarios:                 FinalScenarios
    x_scenarios:                     XScenarios
    extra_final_mission_age_unlocks: ExtraFinalMissionAgeUnlocks
    starting_gems:                   StartingGems
    wins_to_open_shop:               WinsToOpenShop
    godsanity:                       Godsanity
    god_force_change:                GodForceChange
    myth_unit_sanity:                MythUnitSanity
    hero_abilities:                  HeroAbilities