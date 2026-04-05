from __future__ import annotations

from BaseClasses import CollectionState, Item, ItemClassification, LocationProgressType
from worlds.generic.Rules import add_rule, forbid_item, set_rule

from ..items.Items import (
    aomItemData,
    AgeUnlock,
    ArkantosHousing,
    Campaign,
    FinalUnlock,
    HeroActionBoost,
    HeroSpecialEffect,
    HeroStatBoost,
    HeroStatBoostFiller,
    PassiveIncomeLarge,
    Reinforcement,
    ReinforcementUseful,
    StartingResourcesLarge,
    UnitUnlockProgression,
    UnitUnlockUseful,
    item_type_to_classification,
)
from ..locations.Locations import (
    aomLocationData,
    aomLocationType,
    WAY_TO_ATLANTIS_LOCATION_NAME,
)
from ..locations.Scenarios import aomScenarioData
from ..Options import FinalScenarios


# --------------------------------------------------
# Helper naming functions
# --------------------------------------------------

def completion_event_name(scenario: aomScenarioData) -> str:
    return f"{scenario.region_name} Complete"


def completion_location_name(scenario: aomScenarioData) -> str:
    return f"{scenario.display_name}: Completion"


def entrance_name(source: str, target: str) -> str:
    return f"{source} -> {target}"


# --------------------------------------------------
# Completion tracking helpers
# --------------------------------------------------

def has_scenario_complete(state: CollectionState, player: int, scenario: aomScenarioData) -> bool:
    return state.has(completion_event_name(scenario), player)


def count_completed_scenarios(state: CollectionState, player: int) -> int:
    """Counts how many non-final scenarios have been completed."""
    non_final = [s for s in aomScenarioData if s.campaign.name != "FOTT_FINAL"]
    return sum(1 for s in non_final if has_scenario_complete(state, player, s))


# --------------------------------------------------
# Option parsing helpers
# --------------------------------------------------

def get_final_mode_value(world) -> int:
    return int(world.options.final_scenarios.value)


def get_x_scenarios_value(world) -> int:
    return int(world.options.x_scenarios.value)


# --------------------------------------------------
# Age unlock item name lists
# --------------------------------------------------

GREEK_UNLOCK_NAMES = [
    aomItemData.GREEK_AGE_UNLOCK_1.item_name,
    aomItemData.GREEK_AGE_UNLOCK_2.item_name,
    aomItemData.GREEK_AGE_UNLOCK_3.item_name,
]

EGYPTIAN_UNLOCK_NAMES = [
    aomItemData.EGYPTIAN_AGE_UNLOCK_1.item_name,
    aomItemData.EGYPTIAN_AGE_UNLOCK_2.item_name,
    aomItemData.EGYPTIAN_AGE_UNLOCK_3.item_name,
]

NORSE_UNLOCK_NAMES = [
    aomItemData.NORSE_AGE_UNLOCK_1.item_name,
    aomItemData.NORSE_AGE_UNLOCK_2.item_name,
    aomItemData.NORSE_AGE_UNLOCK_3.item_name,
]


def count_civ_unlocks(state: CollectionState, player: int, unlock_names: list[str]) -> int:
    return sum(1 for name in unlock_names if state.has(name, player))


# --------------------------------------------------
# Per-scenario age and point requirements
# --------------------------------------------------

def _build_scenario_requirements() -> dict[int, tuple[list[str], int, float]]:
    raw = {
        1:  (1, 1, True),   2:  (1, 2, False),  3:  (1, 3, False),
        4:  (2, 4, False),  5:  (3, 4, False),  6:  (3, 3, False),
        7:  (3, 4, True),   8:  (2, 4, False),  9:  (4, 4, True),
        10: (1, 4, True),   11: (1, 4, True),   12: (1, 4, False),
        13: (3, 4, False),  14: (3, 3, False),  15: (2, 4, False),
        16: (4, 4, True),   17: (3, 4, False),  18: (2, 4, False),
        19: (3, 4, False),  20: (3, 4, False),  21: (1, 4, False),
        22: (1, 3, False),  23: (2, 4, False),  24: (2, 3, False),
        25: (1, 4, True),   26: (2, 4, False),  27: (2, 4, False),
        28: (3, 4, False),  29: (2, 4, True),   30: (2, 4, False),
        31: (3, 4, False),  32: (3, 4, False),
    }

    def unlock_names_for(n: int) -> list[str]:
        if n <= 10 or n >= 31:
            return GREEK_UNLOCK_NAMES
        elif n <= 20:
            return EGYPTIAN_UNLOCK_NAMES
        else:
            return NORSE_UNLOCK_NAMES

    result: dict[int, tuple[list[str], int, float]] = {}
    for n, (start, max_age, no_tc) in raw.items():
        diff = max_age - start
        if no_tc or start == max_age:
            result[n] = ([], 0, 0.0)
            continue
        unlocks = 2 if diff >= 3 else max_age - 1
        # Norse uses 3× multiplier; Greek, Egyptian, and Final use 4×
        if 21 <= n <= 30:
            points = 3.0 * (max_age - 1)
        else:
            points = 4.0 * (max_age - 1)
        result[n] = (unlock_names_for(n), unlocks, points)

    return result


SCENARIO_REQUIREMENTS: dict[int, tuple[list[str], int, float]] = _build_scenario_requirements()


# --------------------------------------------------
# Point scoring system
# --------------------------------------------------

_BASE_POINTS: dict[type, float] = {
    Campaign:              1.0,  # section keys gate sections; points represent meta-progress
    FinalUnlock:           1.0,  # Atlantis Key
    AgeUnlock:             0.0,  # age unlocks gate ages directly; excluded from points
    UnitUnlockProgression: 4.0,
    UnitUnlockUseful:      2.0,
    StartingResourcesLarge: 1.0,
    PassiveIncomeLarge:    2.0,
    Reinforcement:         1.0,
    ReinforcementUseful:   2.0,
    HeroStatBoostFiller:   1.0,
    HeroStatBoost:         2.0,
    HeroSpecialEffect:     5.0,
    HeroActionBoost:       2.0,
    ArkantosHousing:       0.0,
}


def _item_point_value(item: aomItemData) -> float:
    """
    Returns the point value for a single item, applying hero multipliers:
      Arkantos hero items: ×2
      Odysseus or Reginleif hero items: ÷2
    Special case: REGINLEIF_JOINS is worth 10 points (she is a hero joining
    the campaign, not a generic reinforcement unit).
    """
    if item == aomItemData.REGINLEIF_JOINS:
        return 10.0

    base = _BASE_POINTS.get(item.type_data, 0.0)
    if base == 0.0:
        return 0.0

    hero_types = (HeroStatBoostFiller, HeroStatBoost, HeroSpecialEffect, HeroActionBoost)
    if not isinstance(item.type, hero_types):
        return base

    hero = item.type.hero
    if hero == "Arkantos":
        return base * 2.0
    elif hero in ("OdysseusSPC", "Reginleif"):
        return base * 0.5
    return base


def build_point_table() -> dict[str, float]:
    """Pre-builds a {item_name: point_value} mapping for fast rule evaluation."""
    return {item.item_name: _item_point_value(item) for item in aomItemData}


def count_points(state: CollectionState, player: int, point_table: dict[str, float]) -> float:
    total = 0.0
    for item_name, value in point_table.items():
        if value > 0.0:
            count = state.count(item_name, player)
            if count > 0:
                total += count * value
    return total


# --------------------------------------------------
# Completion events
# --------------------------------------------------

def place_completion_events(world) -> None:
    """
    Places a hidden completion event item in each scenario's Completion location.
    Also locks the real Victory item at FOTT_32's Victory location.
    """
    player = world.player
    multiworld = world.multiworld

    for scenario in aomScenarioData:
        location = multiworld.get_location(completion_location_name(scenario), player)
        event_item = Item(
            completion_event_name(scenario),
            ItemClassification.progression,
            None,
            player,
        )
        location.place_locked_item(event_item)

    victory_location = multiworld.get_location(
        f"{aomScenarioData.FOTT_32.display_name}: Victory",
        player,
    )
    victory_item = world.create_item(aomItemData.VICTORY.item_name)
    victory_location.place_locked_item(victory_item)


# --------------------------------------------------
# Atlantis Key placement
# --------------------------------------------------

def place_atlantis_key(world) -> None:
    """
    In beat_x_scenarios mode, locks the Atlantis Key to "The Way to Atlantis"
    and sets a rule requiring X non-final scenario completions.
    When the player beats enough scenarios, they receive the Atlantis Key as
    a clear item notification and the Final section opens.

    In all other modes, the Atlantis Key is placed freely by the fill
    algorithm — this function does nothing.
    """
    if get_final_mode_value(world) != FinalScenarios.option_beat_x_scenarios:
        return

    player = world.player
    multiworld = world.multiworld
    required = get_x_scenarios_value(world)

    location = multiworld.get_location(WAY_TO_ATLANTIS_LOCATION_NAME, player)
    atlantis_key = world.create_item(aomItemData.ATLANTIS_KEY.item_name)
    location.place_locked_item(atlantis_key)

    set_rule(
        location,
        lambda state: count_completed_scenarios(state, player) >= required,
    )


# --------------------------------------------------
# Section access rules
# --------------------------------------------------

def set_section_rules(world) -> None:
    """
    Gates access to each campaign section.

    Greek / Egyptian / Norse: require their section unlock item.

    Final section:
      - beat_x_scenarios: requires the Atlantis Key (awarded from "The Way to
        Atlantis" after beating X scenarios — see place_atlantis_key)
      - atlantis_key: requires the Atlantis Key (randomly placed in the pool)
      - always_open: no requirement
    """
    player = world.player
    multiworld = world.multiworld

    greek    = multiworld.get_entrance(entrance_name("Menu", "Fall of the Trident: Greek"),    player)
    egyptian = multiworld.get_entrance(entrance_name("Menu", "Fall of the Trident: Egyptian"), player)
    norse    = multiworld.get_entrance(entrance_name("Menu", "Fall of the Trident: Norse"),    player)
    final    = multiworld.get_entrance(entrance_name("Menu", "Fall of the Trident: Final"),    player)

    set_rule(greek,    lambda state: state.has(aomItemData.GREEK_SCENARIOS.item_name,    player))
    set_rule(egyptian, lambda state: state.has(aomItemData.EGYPTIAN_SCENARIOS.item_name, player))
    set_rule(norse,    lambda state: state.has(aomItemData.NORSE_SCENARIOS.item_name,    player))

    mode = get_final_mode_value(world)

    if mode == FinalScenarios.option_always_open:
        set_rule(final, lambda state: True)
    else:
        # Both beat_x_scenarios and atlantis_key require the Atlantis Key.
        # The difference is where the key comes from:
        #   beat_x_scenarios → locked to "The Way to Atlantis" after X completions
        #   atlantis_key     → randomly placed anywhere in the item pool
        set_rule(final, lambda state: state.has(aomItemData.ATLANTIS_KEY.item_name, player))


# --------------------------------------------------
# Age unlock and point rules
# --------------------------------------------------

def set_scenario_age_and_point_rules(world, point_table: dict[str, float]) -> None:
    """
    Applies per-scenario age unlock and point requirements using add_rule,
    ANDing them on top of the section access rule.
    """
    player = world.player
    multiworld = world.multiworld

    section_names = {
        "Greek":    "Fall of the Trident: Greek",
        "Egyptian": "Fall of the Trident: Egyptian",
        "Norse":    "Fall of the Trident: Norse",
        "Final":    "Fall of the Trident: Final",
    }

    def section_for(n: int) -> str:
        if n <= 10:   return section_names["Greek"]
        if n <= 20:   return section_names["Egyptian"]
        if n <= 30:   return section_names["Norse"]
        return section_names["Final"]

    for scenario in aomScenarioData:
        n = scenario.global_number
        unlock_names, unlocks_needed, points_needed = SCENARIO_REQUIREMENTS[n]

        if unlocks_needed == 0 and points_needed == 0.0:
            continue

        ent_name = entrance_name(section_for(n), scenario.region_name)
        entrance = multiworld.get_entrance(ent_name, player)

        def make_rule(unlock_names, unlocks_needed, points_needed):
            def rule(state: CollectionState) -> bool:
                if count_civ_unlocks(state, player, unlock_names) < unlocks_needed:
                    return False
                if count_points(state, player, point_table) < points_needed:
                    return False
                return True
            return rule

        add_rule(entrance, make_rule(unlock_names, unlocks_needed, points_needed))


# --------------------------------------------------
# Scenario 32 exclusion
# --------------------------------------------------

def exclude_scenario_32_locations(world) -> None:
    """
    Marks all FOTT_32 non-Victory locations as EXCLUDED so only filler
    items can be placed there. Victory is unaffected.
    """
    player = world.player
    multiworld = world.multiworld

    for location_data in aomLocationData:
        if location_data.scenario != aomScenarioData.FOTT_32:
            continue
        if location_data.type == aomLocationType.VICTORY:
            continue
        if location_data.type == aomLocationType.COMPLETION:
            continue

        location = multiworld.get_location(location_data.global_name(), player)
        location.progress_type = LocationProgressType.EXCLUDED


# --------------------------------------------------
# Item placement restrictions
# --------------------------------------------------

def set_item_placement_restrictions(world) -> None:
    """
    Prevents a section unlock item from appearing in its own section's locations.
    """
    player = world.player
    multiworld = world.multiworld

    campaign_to_forbidden = {
        "FOTT_GREEK":    aomItemData.GREEK_SCENARIOS.item_name,
        "FOTT_EGYPTIAN": aomItemData.EGYPTIAN_SCENARIOS.item_name,
        "FOTT_NORSE":    aomItemData.NORSE_SCENARIOS.item_name,
        "FOTT_FINAL":    aomItemData.ATLANTIS_KEY.item_name,
    }

    for location_data in aomLocationData:
        location = multiworld.get_location(location_data.global_name(), player)
        forbidden = campaign_to_forbidden.get(location_data.scenario.campaign.name)
        if forbidden:
            forbid_item(location, forbidden, player)


# --------------------------------------------------
# Win condition
# --------------------------------------------------

def set_completion_rule(world) -> None:
    world.multiworld.completion_condition[world.player] = (
        lambda state: state.has("Victory", world.player)
    )


# --------------------------------------------------
# Entry point
# --------------------------------------------------

def set_rules(world) -> None:
    """
    Main entry point called by the World.

    Order:
    1. Exclude FOTT_32 non-Victory locations.
    2. Place completion events and lock Victory.
    3. Lock Atlantis Key to "The Way to Atlantis" in beat_x mode.
    4. Apply section gate rules.
    5. Apply per-scenario age unlock and point rules.
    6. Apply item placement restrictions.
    7. Set win condition.
    """
    point_table = build_point_table()

    exclude_scenario_32_locations(world)
    place_completion_events(world)
    place_atlantis_key(world)
    set_section_rules(world)
    set_scenario_age_and_point_rules(world, point_table)
    set_item_placement_restrictions(world)
    set_completion_rule(world)