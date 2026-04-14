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

    The other two sections must be found as items in the pool.
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
    Beat the chosen number of scenarios to receive the Atlantis Key.

    always_open:
    The Final section is available from the start.

    atlantis_key:
    The Atlantis Key is shuffled randomly into the item pool.
    """
    internal_name = "final_scenarios"
    display_name = "Final Scenarios"
    option_beat_x_scenarios = 0
    option_always_open      = 1
    option_atlantis_key     = 2
    default = option_beat_x_scenarios


class XScenarios(Range):
    """
    If Final Scenarios is set to beat_x_scenarios, how many scenarios must be
    completed before you receive the Atlantis Key.
    """
    internal_name = "x_scenarios"
    display_name = "X Scenarios"
    range_start = 0
    range_end   = 30
    default     = 12


class ExtraFinalMissionAgeUnlocks(Range):
    """
    Scenario 32 requires 3 Age Unlock items to reach the Mythic Age and build
    the Wonder. This adds extra copies of the relevant civ's Age Unlock.
    At the default of 1, there are 4 total copies in the pool.
    """
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

    When enabled: beating scenarios earns Gems (currency), which are spent
    in the shop to receive items and hints. The shop scenario is accessible
    from the campaign map.

    When disabled: victories award random multiworld items instead of Gems,
    the shop scenario returns the player to the menu immediately, and no
    shop-related items or locations are generated.
    """
    internal_name = "gem_shop"
    display_name = "Gem Shop"
    default = 1


class StartingGems(Range):
    """
    Number of Gems to start with (only used when Gem Shop is enabled).
    Gems are earned by beating scenarios (1 per scenario, up to 31).
    """
    internal_name = "starting_gems"
    display_name  = "Starting Gems"
    range_start   = 0
    range_end     = 10
    default       = 0


class WinsToOpenShop(Range):
    """
    Number of scenario victories required to open each additional shop tier
    (only used when Gem Shop is enabled).
    Shop A (Marsh) is always open. Shop B (Desert) opens after this many wins.
    Shop C (Grass) opens after 2x wins. Shop D (Hades) opens after 3x wins.
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

class Godsanity(Toggle):
    """
    Randomize the major god for each scenario at generation time.
    """
    internal_name = "godsanity"
    display_name = "godsanity"
    default = 1


class GodForceChange(Toggle):
    """
    When godsanity is enabled, forces the random god to never be the vanilla
    major god for that scenario, and makes a different civilization more likely.
    """
    internal_name = "god_force_change"
    display_name = "God Force Change"
    default = 1


class MythUnitSanity(Toggle):
    """
    Include myth unit tier unlock items in the pool.
    When enabled, all myth units are forbidden at the start and must be unlocked.
    """
    internal_name = "myth_unit_sanity"
    display_name = "Myth Unit Sanity"
    default = 1


class HeroAbilities(Toggle):
    """
    Include custom hero special ability items in the item pool?

    enabled (true): Recommended for an exciting, hero-focused campaign.
    disabled (false): All hero ability items are replaced with filler.
    """
    internal_name = "hero_abilities"
    display_name = "Hero Abilities"
    default = 1


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
    gem_shop:                        GemShop
    starting_gems:                   StartingGems
    wins_to_open_shop:               WinsToOpenShop
    godsanity:                       Godsanity
    god_force_change:                GodForceChange
    myth_unit_sanity:                MythUnitSanity
    hero_abilities:                  HeroAbilities
