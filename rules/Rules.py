from __future__ import annotations

from BaseClasses import CollectionState, Item, ItemClassification, LocationProgressType
from worlds.generic.Rules import add_rule, forbid_item, set_rule

from ..items.Items import (
    ProgressiveShopInfo,
    aomItemData,
    AgeUnlock,
    MythUnitUnlockFiller,
    MythUnitUnlockProgression,
    MythUnitUnlockUseful,
    ArkantosHousing,
    Campaign,
    FinalUnlock,
    HeroActionBoost,
    HeroSpecialEffect,
    HeroStatBoost,
    HeroStatBoostFiller,
    PassiveIncome,
    PassiveIncomeLarge,
    Reinforcement,
    ReinforcementUseful,
    StartingResources,
    StartingResourcesLarge,
    UnitUnlockProgression,
    UnitUnlockUseful,
    item_type_to_classification,
)
from ..locations.Locations import (
    aomLocationData,
    aomLocationType,
    WAY_TO_ATLANTIS_LOCATION_NAME,
    VICTORY_LOCATIONS,
    ALL_SHOP_ITEM_IDS,
    ALL_PROGRESSIVE_INFO_IDS,
    SHOP_TIER_CONFIGS,
    TIER_ITEM_IDS,
    PROGRESSIVE_INFO_IDS,
    location_id_to_name,
)
from ..locations.Scenarios import aomScenarioData
from ..Options import FinalScenarios

# Atlantean types — only available when godsanity Items.py is packaged
try:
    from ..items.Items import (
    ProgressiveShopInfo,
        AtlanteanMythUnitUnlock,
        AtlanteanUnitUnlockProgression,
        AtlanteanUnitUnlockUseful,
    )
    _ATLANTEAN_TYPES = True
except (ImportError, AttributeError):
    _ATLANTEAN_TYPES = False


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

GREEK_UNLOCK_NAMES    = [aomItemData.GREEK_AGE_UNLOCK.item_name]
EGYPTIAN_UNLOCK_NAMES = [aomItemData.EGYPTIAN_AGE_UNLOCK.item_name]
NORSE_UNLOCK_NAMES    = [aomItemData.NORSE_AGE_UNLOCK.item_name]

try:
    ATLANTEAN_UNLOCK_NAMES = [aomItemData.ATLANTEAN_AGE_UNLOCK.item_name]
except AttributeError:
    ATLANTEAN_UNLOCK_NAMES = []


def count_civ_unlocks(state: CollectionState, player: int, unlock_names: list[str]) -> int:
    return sum(state.count(name, player) for name in unlock_names)


# --------------------------------------------------
# Godsanity god-to-civ mappings
# --------------------------------------------------

_GREEK_GOD_IDS     = frozenset({1, 2, 3})
_EGYPTIAN_GOD_IDS  = frozenset({4, 5, 6})
_NORSE_GOD_IDS     = frozenset({7, 8, 9})
_ATLANTEAN_GOD_IDS = frozenset({10, 11, 12})
_GREEK_FREE_MYTHIC_GODS = _GREEK_GOD_IDS

_GOD_TO_CIV: dict[int, str] = {
    1: "Greek", 2: "Greek",    3: "Greek",
    4: "Egyptian", 5: "Egyptian", 6: "Egyptian",
    7: "Norse",    8: "Norse",    9: "Norse",
    10: "Atlantean", 11: "Atlantean", 12: "Atlantean",
}

_CIV_UNLOCK_NAMES: dict[str, list[str]] = {
    "Greek":     GREEK_UNLOCK_NAMES,
    "Egyptian":  EGYPTIAN_UNLOCK_NAMES,
    "Norse":     NORSE_UNLOCK_NAMES,
    "Atlantean": ATLANTEAN_UNLOCK_NAMES,
}

def _unlock_names_for_god(god_id: int) -> list[str]:
    if god_id in _GREEK_GOD_IDS:      return GREEK_UNLOCK_NAMES
    if god_id in _EGYPTIAN_GOD_IDS:   return EGYPTIAN_UNLOCK_NAMES
    if god_id in _ATLANTEAN_GOD_IDS:  return ATLANTEAN_UNLOCK_NAMES
    return NORSE_UNLOCK_NAMES


# --------------------------------------------------
# Scenario data
# (start_age_num, max_unlock_count, points_needed, is_exempt, is_myth_only)
# Age nums: 1=Archaic 2=Classical 3=Heroic 4=Mythic
# --------------------------------------------------

_SCENARIO_DATA: dict[int, tuple[int, int, float, bool, bool]] = {
    1:  (1, 0,  0.0,  True,  False),
    2:  (1, 1,  4.0,  False, False),
    3:  (1, 2,  9.0,  False, False),
    4:  (2, 3, 16.0,  False, False),
    5:  (3, 3, 16.0,  False, False),
    6:  (3, 2,  9.0,  False, False),
    7:  (3, 2,  1.0,  False, False),   # special: 1pt required, human units excluded
    8:  (2, 3, 16.0,  False, False),
    9:  (4, 3,  0.0,  True,  False),
    10: (1, 3,  0.0,  True,  False),
    11: (1, 3,  0.0,  True,  False),
    12: (1, 3, 16.0,  False, False),
    13: (3, 3, 16.0,  False, False),
    14: (3, 2,  9.0,  False, True),
    15: (2, 3, 16.0,  False, False),
    16: (4, 3,  0.0,  True,  False),
    17: (3, 3, 16.0,  False, False),
    18: (2, 3, 16.0,  False, False),
    19: (3, 3, 16.0,  False, False),
    20: (3, 3, 16.0,  False, False),
    21: (1, 3, 16.0,  False, False),
    22: (1, 2,  9.0,  False, False),
    23: (2, 3, 16.0,  False, False),
    24: (2, 2,  9.0,  False, False),
    25: (1, 3,  0.0,  True,  False),
    26: (2, 3, 16.0,  False, False),
    27: (2, 3, 16.0,  False, False),
    28: (3, 3, 16.0,  False, False),
    29: (2, 3,  0.0,  True,  False),
    30: (2, 3, 16.0,  False, False),
    31: (3, 3, 16.0,  False, False),
    32: (3, 3, 16.0,  False, False),
}

_VANILLA_CIV: dict[int, str] = {
    1: "Greek",  2: "Greek",  3: "Greek",  4: "Greek",
    5: "Greek",  6: "Greek",  7: "Greek",  8: "Greek",  9: "Greek",  10: "Greek",
    11: "Egyptian", 12: "Egyptian", 13: "Egyptian", 14: "Egyptian",
    15: "Egyptian", 16: "Greek",
    17: "Egyptian", 18: "Egyptian", 19: "Egyptian", 20: "Egyptian",
    21: "Greek",
    22: "Norse", 23: "Norse", 24: "Norse", 25: "Norse",
    26: "Norse", 27: "Norse", 28: "Norse", 29: "Norse", 30: "Norse",
    31: "Greek", 32: "Greek",
}

_VANILLA_GODS: dict[int, int] = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
    11: 4, 12: 5, 13: 6, 14: 4, 15: 4,
    16: 3,
    17: 5, 18: 5, 19: 4, 20: 4,
    21: 1,
    22: 8, 23: 8,
    24: 9, 25: 9,
    26: 7, 27: 7, 28: 7,
    29: 8, 30: 8,
    31: 1, 32: 1,
}


# --------------------------------------------------
# Military access tables  (string literals to avoid
# aomItemData attribute lookups at module load time)
# --------------------------------------------------

_HUMAN_UNITS: dict[str, dict[int, list[str]]] = {
    "Greek": {
        1: ["Can train Hoplite", "Can train Toxotes", "Can train Hippeus"],
        2: ["Can train Hypaspist", "Can train Peltast", "Can train Prodromos"],
    },
    "Egyptian": {
        1: ["Can train Spearman", "Can train Axeman",
            "Can train Slinger", "Can train Chariot Archer"],
        2: ["Can train Camel Rider", "Can train War Elephant"],
    },
    "Norse": {
        0: ["Can train Berserk"],   # archaic, item needed, no unlock required
        1: ["Can train Hirdman", "Can train Throwing Axeman", "Can train Raiding Cavalry"],
        2: ["Can train Jarl", "Can train Huskarl"],
    },
    "Atlantean": {
        1: ["Can train Murmillo", "Can train Katapeltes",
            "Can train Turma", "Can train Cheiroballista"],
        2: ["Can train Contarius", "Can train Arcus", "Can train Destroyer"],
        3: ["Can train Fanatic"],
    },
}

_MYTH_ITEMS_BY_UNLOCK: dict[str, dict[int, str]] = {
    "Greek": {
        1: "Can train Greek Classical Myth Units",
        2: "Can train Greek Heroic Myth Units",
        3: "Can train Greek Mythic Myth Units",
    },
    "Egyptian": {
        1: "Can train Egyptian Classical Myth Units",
        2: "Can train Egyptian Heroic Myth Units",
        3: "Can train Egyptian Mythic Myth Units",
    },
    "Norse": {
        1: "Can train Norse Classical Myth Units",
        2: "Can train Norse Heroic Myth Units",
        3: "Can train Norse Mythic Myth Units",
    },
    "Atlantean": {
        1: "Can train Atlantean Classical Myth Units",
        2: "Can train Atlantean Heroic Myth Units",
        3: "Can train Atlantean Mythic Myth Units",
    },
}


# --------------------------------------------------
# Point scoring system
# --------------------------------------------------

_BASE_POINTS: dict[type, float] = {
    AgeUnlock:              1.0,   # small contribution to bootstrap early fill chain
    Campaign:               0.0,
    FinalUnlock:            0.0,
    UnitUnlockProgression:  3.0,
    UnitUnlockUseful:       3.0,
    MythUnitUnlockProgression: 5.0,
    MythUnitUnlockUseful:      5.0,
    MythUnitUnlockFiller:      5.0,
    StartingResources:      1.0,
    StartingResourcesLarge: 2.0,
    PassiveIncome:          1.0,
    PassiveIncomeLarge:     2.0,
    Reinforcement:          1.0,
    ReinforcementUseful:    2.0,
    HeroStatBoostFiller:    1.0,
    HeroStatBoost:          2.0,
    HeroSpecialEffect:      2.0,
    HeroActionBoost:        2.0,
    ArkantosHousing:        2.0,
}

if _ATLANTEAN_TYPES:
    _BASE_POINTS[AtlanteanUnitUnlockProgression] = 3.0
    _BASE_POINTS[AtlanteanUnitUnlockUseful]      = 3.0
    _BASE_POINTS[AtlanteanMythUnitUnlock]        = 5.0


def _item_point_value(item: aomItemData) -> float:
    if item == aomItemData.REGINLEIF_JOINS or item == aomItemData.ODYSSEUS_JOINS:
        return 4.0

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
# Per-scenario military + point rule factory
# --------------------------------------------------

def _make_scenario_rule(
    player: int,
    god_id: int,
    vanilla_civ: str,
    start_age_num: int,
    max_unlock_count: int,
    is_myth_only: bool,
    point_table: dict[str, float],
    points_needed: float,
):
    god_civ      = _GOD_TO_CIV.get(god_id, "Greek")
    unlock_names = _CIV_UNLOCK_NAMES[god_civ]

    # Myth items accessible at starting age for the ASSIGNED GOD's civ.
    # With godsanity, APInitStartingAgeTechs grants these techs at scenario
    # start, so those myth units are available without item finds.
    vanilla_starting_myth: list[str] = [
        _MYTH_ITEMS_BY_UNLOCK[god_civ][tier]
        for tier in range(1, start_age_num)
        if tier in _MYTH_ITEMS_BY_UNLOCK.get(god_civ, {})
    ]

    def rule(state: CollectionState) -> bool:
        if count_points(state, player, point_table) < points_needed:
            return False

        raw_count    = sum(state.count(n, player) for n in unlock_names)
        unlock_count = min(raw_count, max_unlock_count)

        if is_myth_only:
            return bool(vanilla_starting_myth) and any(
                state.has(m, player) for m in vanilla_starting_myth
            )

        if vanilla_starting_myth and any(state.has(m, player) for m in vanilla_starting_myth):
            return True

        for needed in range(0, max_unlock_count + 1):
            if unlock_count < needed:
                break
            for unit_name in _HUMAN_UNITS.get(god_civ, {}).get(needed, []):
                if state.has(unit_name, player):
                    return True
            if needed >= 1:
                myth_name = _MYTH_ITEMS_BY_UNLOCK.get(god_civ, {}).get(needed)
                if myth_name and state.has(myth_name, player):
                    return True
            if god_civ == "Norse" and needed >= 1:
                return True
            if god_id in _GREEK_FREE_MYTHIC_GODS and needed >= 3:
                return True

        return False

    return rule


def _get_scenario_god(world, scenario_n: int) -> int:
    assignments = getattr(world, "god_assignments", {})
    if assignments:
        return assignments.get(scenario_n, _VANILLA_GODS[scenario_n])
    return _VANILLA_GODS[scenario_n]


# --------------------------------------------------
# Completion events
# --------------------------------------------------

def place_completion_events(world) -> None:
    player    = world.player
    multiworld = world.multiworld
    for scenario in aomScenarioData:
        location   = multiworld.get_location(completion_location_name(scenario), player)
        event_item = Item(
            completion_event_name(scenario),
            ItemClassification.progression,
            None,
            player,
        )
        location.place_locked_item(event_item)
    victory_location = multiworld.get_location(
        f"{aomScenarioData.FOTT_32.display_name}: Victory", player
    )
    victory_item = world.create_item(aomItemData.VICTORY.item_name)
    victory_location.place_locked_item(victory_item)


# --------------------------------------------------
# Atlantis Key placement
# --------------------------------------------------

def place_atlantis_key(world) -> None:
    if get_final_mode_value(world) != FinalScenarios.option_beat_x_scenarios:
        return
    player    = world.player
    multiworld = world.multiworld
    required  = get_x_scenarios_value(world)
    location     = multiworld.get_location(WAY_TO_ATLANTIS_LOCATION_NAME, player)
    atlantis_key = world.create_item(aomItemData.ATLANTIS_KEY.item_name)
    location.place_locked_item(atlantis_key)
    set_rule(location, lambda state: count_completed_scenarios(state, player) >= required)


# --------------------------------------------------
# Section access rules
# --------------------------------------------------

def set_section_rules(world) -> None:
    player    = world.player
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
        set_rule(final, lambda state: state.has(aomItemData.ATLANTIS_KEY.item_name, player))


# --------------------------------------------------
# Per-scenario military + point rules
# --------------------------------------------------

def set_scenario_age_and_point_rules(world, point_table: dict[str, float]) -> None:
    player    = world.player
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
        start_age_num, max_unlock_count, points_needed, is_exempt, is_myth_only = _SCENARIO_DATA[n]

        if is_exempt:
            continue

        god_id      = _get_scenario_god(world, n)
        vanilla_civ = _VANILLA_CIV[n]
        god_civ     = _GOD_TO_CIV.get(god_id, "Greek")
        unlock_names = _CIV_UNLOCK_NAMES[god_civ]

        ent_name = entrance_name(section_for(n), scenario.region_name)
        entrance = multiworld.get_entrance(ent_name, player)

        # Scenario 7: human unit unlocks don't count toward points,
        # and the threshold is just 1pt.
        if n == 7:
            human_unit_types = (UnitUnlockProgression, UnitUnlockUseful)
            if _ATLANTEAN_TYPES:
                human_unit_types = human_unit_types + (
                    AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful
                )
            human_unit_names = {
                item.item_name for item in aomItemData
                if isinstance(item.type, human_unit_types)
            }
            effective_table = {
                name: (0.0 if name in human_unit_names else val)
                for name, val in point_table.items()
            }
        else:
            effective_table = point_table

        # Military + points rule
        add_rule(entrance, _make_scenario_rule(
            player, god_id, vanilla_civ,
            start_age_num, max_unlock_count, is_myth_only,
            effective_table, points_needed,
        ))

        # Hard requirement: scenario 2 needs at least 1 age unlock
        # (must advance to Classical age to complete its objective)
        if n == 2:
            add_rule(entrance,
                lambda state, un=unlock_names:
                    count_civ_unlocks(state, player, un) >= 1
            )

        # Hard requirement: scenario 32 needs 3 age unlocks (Mythic age for the Wonder)
        if n == 32:
            add_rule(entrance,
                lambda state, un=unlock_names:
                    count_civ_unlocks(state, player, un) >= 3
            )


# --------------------------------------------------
# Scenario 32 exclusion
# --------------------------------------------------

def exclude_scenario_32_locations(world) -> None:
    player    = world.player
    multiworld = world.multiworld
    for location_data in aomLocationData:
        if location_data.scenario != aomScenarioData.FOTT_32:
            continue
        if location_data.type in (aomLocationType.VICTORY, aomLocationType.COMPLETION):
            continue
        location = multiworld.get_location(location_data.global_name(), player)
        location.progress_type = LocationProgressType.EXCLUDED


# --------------------------------------------------
# Item placement restrictions
# --------------------------------------------------

def set_item_placement_restrictions(world) -> None:
    player    = world.player
    multiworld = world.multiworld
    campaign_to_forbidden = {
        "FOTT_GREEK":    aomItemData.GREEK_SCENARIOS.item_name,
        "FOTT_EGYPTIAN": aomItemData.EGYPTIAN_SCENARIOS.item_name,
        "FOTT_NORSE":    aomItemData.NORSE_SCENARIOS.item_name,
        "FOTT_FINAL":    aomItemData.ATLANTIS_KEY.item_name,
    }
    for location_data in aomLocationData:
        location  = multiworld.get_location(location_data.global_name(), player)
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



def place_gems(world) -> None:
    """Lock Gems at Victory locations 1-31 when gem_shop is on; otherwise leave them for pool fill."""
    if not world.gem_shop_enabled:
        return  # victories hold random pool items when shop is disabled
    player     = world.player
    multiworld = world.multiworld
    for scenario in aomScenarioData:
        if scenario == aomScenarioData.FOTT_32:
            continue
        loc = multiworld.get_location(VICTORY_LOCATIONS[scenario].global_name(), player)
        gem = world.create_item(aomItemData.GEM.item_name)
        loc.place_locked_item(gem)


def place_progressive_shop_info(world) -> None:
    """Lock one Progressive Shop Info item at each shop's hint slot 1 location."""
    if not world.gem_shop_enabled:
        return
    player     = world.player
    multiworld = world.multiworld
    for tier, display, *_ in SHOP_TIER_CONFIGS:
        loc_id = PROGRESSIVE_INFO_IDS[tier]
        name   = location_id_to_name.get(loc_id)
        if name:
            loc  = multiworld.get_location(name, player)
            item = world.create_item(aomItemData.PROGRESSIVE_SHOP_INFO.item_name)
            loc.place_locked_item(item)


def set_shop_rules(world) -> None:
    """Set access rules and item classification constraints for shop locations."""
    if not world.gem_shop_enabled:
        return
    player     = world.player
    multiworld = world.multiworld
    threshold  = int(world.options.wins_to_open_shop.value)

    # Tier access rules — Desert/Grass/Hades require N/2N/3N wins
    tier_multipliers = {"B": 1, "C": 2, "D": 3}
    for tier_name, _disp, _item_obs, _hint_obs in SHOP_TIER_CONFIGS:
        multiplier = tier_multipliers.get(tier_name, 0)
        if multiplier == 0:
            continue  # Marsh is always open
        required = threshold * multiplier
        if required == 0:
            continue
        for loc_id in TIER_ITEM_IDS[tier_name]:
            name = location_id_to_name.get(loc_id)
            if name:
                loc = multiworld.get_location(name, player)
                set_rule(loc, lambda state, r=required: count_completed_scenarios(state, player) >= r)
        # Also gate the progressive info location for this tier
        pi_id = PROGRESSIVE_INFO_IDS[tier_name]
        pi_name = location_id_to_name.get(pi_id)
        if pi_name:
            loc = multiworld.get_location(pi_name, player)
            set_rule(loc, lambda state, r=required: count_completed_scenarios(state, player) >= r)

    # Item classification per location:
    #   - exactly 1 progression slot per shop (no restriction)
    #   - ~half of the rest are filler-only
    #   - remainder accept filler or useful (not progression)
    prog_slots   = getattr(world, "shop_progression_slots", {})
    filler_only  = getattr(world, "shop_filler_only", set())
    for loc_id in ALL_SHOP_ITEM_IDS:
        name = location_id_to_name.get(loc_id)
        if not name:
            continue
        loc = multiworld.get_location(name, player)
        is_prog_slot = any(loc_id == prog_slots.get(tier) for tier, *_ in SHOP_TIER_CONFIGS)
        if is_prog_slot:
            pass  # no restriction — this slot gets exactly 1 progression item
        elif loc_id in filler_only:
            loc.item_rule = lambda item: item.classification == ItemClassification.filler
        else:
            loc.item_rule = lambda item: item.classification in (
                ItemClassification.filler, ItemClassification.useful
            )

def set_rules(world) -> None:
    point_table = build_point_table()
    exclude_scenario_32_locations(world)
    place_completion_events(world)
    place_gems(world)
    place_progressive_shop_info(world)
    place_atlantis_key(world)
    set_section_rules(world)
    set_scenario_age_and_point_rules(world, point_table)
    set_item_placement_restrictions(world)
    set_shop_rules(world)
    set_completion_rule(world)