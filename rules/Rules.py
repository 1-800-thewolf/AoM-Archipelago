# =============================================================================
# Age of Mythology Retold — Reachability rules and forced placements
# =============================================================================
#
# `set_rules(world)` is the entry point Archipelago calls after `create_regions`
# and `create_items`.  It does three big things:
#
#   1. Mark every COMPLETION location with a locked event item (so downstream
#      rules can check completion via `state.has(...)`) and lock the singular
#      Victory item to FOTT_32's Victory location.
#   2. Install access rules (`set_rule` / `add_rule`) on Region entrances so
#      reachability honors:
#         * section unlocks (Greek/Egyptian/Norse/etc. campaign items)
#         * per-scenario age & military requirements
#         * point-totals (so the player can't enter scenarios with no useful
#           items in their inventory)
#   3. Install forced item placements for the gem shop:
#         * Gems on every non-32 Victory
#         * Progressive Shop Info on each tier's hint slot 1
#         * Tier-locked entrances for B/C/D shops
#
# Three big tables drive scenario rules:
#
#   _SCENARIO_DATA[n]      — (start_age, min_unlocks, points, exempt, myth_only)
#                            One entry per scenario (global_number 1-32, NA
#                            501-512, GG 601-604).  Adding a scenario REQUIRES
#                            adding a row here.
#   _VANILLA_CIV[n]        — civ string used as a fallback when god randomization
#                            is off (or as a hint when picking units).
#   _VANILLA_GODS[n]       — vanilla god id; mirrors __init__.py::_VANILLA_GODS.
#
# -----------------------------------------------------------------------------
# EXTENDING
# -----------------------------------------------------------------------------
#   * New scenario:  add to `_SCENARIO_DATA`, `_VANILLA_CIV`, `_VANILLA_GODS`.
#                    Add to `_SCENARIO_AGE_CAP` if it has a hard age cap; or
#                    `_SCENARIO_HEROIC_FLOOR` if Heroic-floor + Mythic-max.
#                    Add a section_for() branch in
#                    `set_scenario_age_and_point_rules` if it falls in a new
#                    APScenarioID range.
#   * New civ:       add unlock-name list to `_CIV_UNLOCK_NAMES`, units per
#                    age tier to `_HUMAN_UNITS`, and myth unit items to
#                    `_MYTH_ITEMS_BY_UNLOCK`.  Also add the civ god ids to
#                    `_GREEK_GOD_IDS`/`_EGYPTIAN_GOD_IDS`/etc and to `_GOD_TO_CIV`.
#   * New campaign:  add a `_maybe_set` line for its menu→region entrance in
#                    `set_section_rules`, with the appropriate Campaign item
#                    or unconditional access.
#   * New item type that should count toward the points gate: extend
#                    `_BASE_POINTS` with the new dataclass type.
#   * New age-cap behavior: write a `_make_*_scenario_rule` factory and
#                    dispatch to it from `set_scenario_age_and_point_rules`.
# =============================================================================

from __future__ import annotations

from BaseClasses import CollectionState, Item, ItemClassification, LocationProgressType
from worlds.generic.Rules import add_rule, forbid_item, set_rule

from ..items.Items import (
    # ProgressiveShopInfo,                # UNUSED in Rules.py
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
    StartingArmy,
    StartingArmyUseful,
    StartingResources,
    StartingResourcesLarge,
    TitanAgeUnlock,
    UnitUnlockProgression,
    UnitUnlockUseful,
    ChineseUnitUnlockProgression,
    ChineseUnitUnlockUseful,
    ChineseMythUnitUnlock,
    JapaneseUnitUnlockProgression,
    JapaneseUnitUnlockUseful,
    JapaneseMythUnitUnlock,
    AztecUnitUnlockProgression,
    AztecUnitUnlockUseful,
    AztecMythUnitUnlock,
    # item_type_to_classification,        # UNUSED in Rules.py
)
from ..locations.Locations import (
    aomLocationData,
    aomLocationType,
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
        # ProgressiveShopInfo,            # UNUSED in Rules.py (also stray-indented)
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
    """Name of the locked event item placed on a scenario's COMPLETION
    location.  Used as the key for `state.has(...)` checks elsewhere in
    rules — e.g. `count_completed_scenarios`, beat_x final-mode rule."""
    return f"{scenario.region_name} Complete"


def completion_location_name(scenario: aomScenarioData) -> str:
    """Display name of a scenario's COMPLETION location, matching the format
    `aomLocationData.global_name()` produces.  Used to look up the location
    via `multiworld.get_location` for placing the event item."""
    return f"{scenario.display_name}: Completion"


def entrance_name(source: str, target: str) -> str:
    """Format an entrance name to match `regions/Regions.py::connect_regions`.
    Both halves of the codebase MUST agree on this exact format."""
    return f"{source} -> {target}"


# --------------------------------------------------
# Completion tracking helpers
# --------------------------------------------------

def has_scenario_complete(state: CollectionState, player: int, scenario: aomScenarioData) -> bool:
    """True if the player has the locked completion event item for `scenario`.
    Used by section rules (beat_x mode) and by gem shop tier gates."""
    return state.has(completion_event_name(scenario), player)


def count_completed_scenarios(state: CollectionState, player: int) -> int:
    """Total number of non-Final scenarios the player has completed.  Used by
    the FinalScenarios=beat_x_scenarios mode and by shop tier unlock gates.
    The Final section is excluded so completing FOTT_31/32 doesn't help
    unlock the Final section in beat_x mode."""
    non_final = [s for s in aomScenarioData if s.campaign.name != "FOTT_FINAL"]
    return sum(1 for s in non_final if has_scenario_complete(state, player, s))


# --------------------------------------------------
# Option parsing helpers
# --------------------------------------------------

def get_final_mode_value(world) -> int:
    """Return the FinalScenarios option as an int (matches `Options.FinalScenarios.option_*` consts)."""
    return int(world.options.final_scenarios.value)


def get_x_scenarios_value(world) -> int:
    """Return the X-scenarios threshold for FinalScenarios=beat_x_scenarios mode."""
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

try:
    CHINESE_UNLOCK_NAMES  = [aomItemData.CHINESE_AGE_UNLOCK.item_name]
    JAPANESE_UNLOCK_NAMES = [aomItemData.JAPANESE_AGE_UNLOCK.item_name]
    AZTEC_UNLOCK_NAMES    = [aomItemData.AZTEC_AGE_UNLOCK.item_name]
except AttributeError:
    CHINESE_UNLOCK_NAMES  = []
    JAPANESE_UNLOCK_NAMES = []
    AZTEC_UNLOCK_NAMES    = []


def count_civ_unlocks(state: CollectionState, player: int, unlock_names: list[str]) -> int:
    """Total number of progressive age unlock items the player has across the
    given civ's unlock-name list.  Used by per-scenario hard-floor checks
    (e.g. scenario 32 needs 3 unlocks for the Wonder)."""
    return sum(state.count(name, player) for name in unlock_names)


# --------------------------------------------------
# Godsanity god-to-civ mappings
# --------------------------------------------------

_GREEK_GOD_IDS     = frozenset({1, 2, 3, 13})
_EGYPTIAN_GOD_IDS  = frozenset({4, 5, 6})
_NORSE_GOD_IDS     = frozenset({7, 8, 9, 14})
_ATLANTEAN_GOD_IDS = frozenset({10, 11, 12})
_CHINESE_GOD_IDS   = frozenset({15, 16, 17})
_JAPANESE_GOD_IDS  = frozenset({18, 19, 20})
_AZTEC_GOD_IDS     = frozenset({21, 22, 23})
_GREEK_FREE_MYTHIC_GODS = _GREEK_GOD_IDS

_GOD_TO_CIV: dict[int, str] = {
    1: "Greek", 2: "Greek",    3: "Greek",     13: "Greek",
    4: "Egyptian", 5: "Egyptian", 6: "Egyptian",
    7: "Norse",    8: "Norse",    9: "Norse",  14: "Norse",
    10: "Atlantean", 11: "Atlantean", 12: "Atlantean",
    15: "Chinese",   16: "Chinese",   17: "Chinese",
    18: "Japanese",  19: "Japanese",  20: "Japanese",
    21: "Aztec",     22: "Aztec",     23: "Aztec",
}

_CIV_UNLOCK_NAMES: dict[str, list[str]] = {
    "Greek":     GREEK_UNLOCK_NAMES,
    "Egyptian":  EGYPTIAN_UNLOCK_NAMES,
    "Norse":     NORSE_UNLOCK_NAMES,
    "Atlantean": ATLANTEAN_UNLOCK_NAMES,
    "Chinese":   CHINESE_UNLOCK_NAMES,
    "Japanese":  JAPANESE_UNLOCK_NAMES,
    "Aztec":     AZTEC_UNLOCK_NAMES,
}

# UNUSED: scenario rules look up `_CIV_UNLOCK_NAMES[god_civ]` directly. Kept (commented).
# def _unlock_names_for_god(god_id: int) -> list[str]:
#     """Map a god id to its civ's age-unlock item-name list.  Used internally
#     by scenario rules to figure out which civ's age unlocks count for the
#     scenario's currently-assigned god."""
#     if god_id in _GREEK_GOD_IDS:      return GREEK_UNLOCK_NAMES
#     if god_id in _EGYPTIAN_GOD_IDS:   return EGYPTIAN_UNLOCK_NAMES
#     if god_id in _ATLANTEAN_GOD_IDS:  return ATLANTEAN_UNLOCK_NAMES
#     return NORSE_UNLOCK_NAMES


# --------------------------------------------------
# Scenario data
# (start_age_num, max_unlock_count, points_needed, is_exempt, is_myth_only)
# Age nums: 1=Archaic 2=Classical 3=Heroic 4=Mythic
# --------------------------------------------------

# (start_age_num, min_required_unlocks, points_needed, is_exempt, is_myth_only)
#
# start_age_num: 1=Archaic, 2=Classical, 3=Heroic, 4=Mythic
# min_required_unlocks: minimum age unlock ITEMS the player must have to enter
#   this scenario in logic (absolute age tier to reach: 1=Classical, 2=Heroic,
#   3=Mythic; 0=no advancement needed).  This is a FLOOR — more unlocks let the
#   player advance further.
#
# AGE-FLOOR POLICY: logic expects at most ONE age advancement above the
#   scenario's starting age (e.g. Classical start -> reach Heroic; Heroic start
#   -> reach Mythic).  EXCEPTION: scenarios that start in Archaic AND can reach
#   Mythic in vanilla expect TWO advancements (reach Heroic) — fott 12 is the
#   only such scenario.  Several scenarios further override the floor and/or
#   point threshold to custom values below.
_SCENARIO_DATA: dict[int, tuple[int, int, float, bool, bool]] = {
    1:  (1, 0,  0.0,  True,  False),  # no TC; always accessible
    2:  (1, 1,  4.0,  False, False),  # reach Classical (1 advancement)
    3:  (1, 1,  4.0,  False, False),  # reach Classical (1 advancement); custom points
    4:  (2, 2, 16.0,  False, False),  # reach Heroic (1 advancement)
    5:  (3, 3, 16.0,  False, False),  # reach Mythic (1 advancement)
    6:  (3, 0,  9.0,  False, False),  # custom: no age floor
    7:  (3, 0,  1.0,  False, False),  # special: no TC, no age req, points only
    8:  (2, 2, 22.0,  False, False),  # reach Heroic (1 advancement); custom points
    9:  (4, 0,  0.0,  True,  False),  # always accessible
    10: (1, 0,  0.0,  True,  False),  # always accessible
    11: (1, 0,  0.0,  True,  False),  # always accessible
    12: (1, 2,  9.0,  False, False),  # Archaic+Mythic -> reach Heroic (2 advancements); custom points
    13: (3, 0,  6.0,  False, False),  # custom: no age floor + points
    14: (3, 0,  9.0,  False, True),   # myth-only; custom: no age floor
    15: (2, 2, 16.0,  False, False),  # reach Heroic (1 advancement)
    16: (4, 0,  0.0,  True,  False),  # always accessible
    17: (3, 3, 16.0,  False, False),  # reach Mythic (1 advancement)
    18: (2, 2, 16.0,  False, False),  # reach Heroic (1 advancement)
    19: (3, 0, 16.0,  False, False),  # custom: no age floor
    20: (3, 3, 22.0,  False, False),  # reach Mythic (1 advancement); custom points
    21: (2, 2,  9.0,  False, False),  # reach Heroic (1 advancement); custom points
    22: (1, 1,  4.0,  False, False),  # reach Classical (1 advancement); custom points
    23: (2, 2, 20.0,  False, False),  # reach Heroic (1 advancement); custom points
    24: (2, 2,  2.0,  False, False),  # reach Heroic (1 advancement); custom points
    25: (1, 0,  0.0,  True,  False),  # no TC; always accessible
    26: (2, 2,  6.0,  False, False),  # reach Heroic (1 advancement); custom points
    27: (2, 2, 20.0,  False, False),  # reach Heroic (1 advancement); custom points
    28: (3, 0,  6.0,  False, False),  # custom: no age floor + points
    29: (2, 0,  0.0,  True,  False),  # always accessible
    30: (2, 2, 24.0,  False, False),  # reach Heroic (1 advancement); custom points
    31: (3, 3, 21.0,  False, False),  # reach Mythic (1 advancement); custom points
    32: (3, 3, 25.0,  False, False),  # reach Mythic (1 advancement); custom points
    # ---------------------------------------------------------------------------
    # New Atlantis (APScenarioIDs 501-512)
    # Age-capped (501,503,504,505,511,512) and exempt (506,507) scenarios ignore
    # min_required_unlocks; only points_needed gates them.
    # ---------------------------------------------------------------------------
    501: (3, 0,  9.0, False, False),  # age-capped @Heroic; custom points
    502: (1, 1,  4.0, False, False),  # reach Classical (1 advancement)
    503: (3, 0,  0.0, False, False),  # age-capped @Heroic, NO TC
    504: (3, 0, 20.0, False, False),  # age-capped @Heroic; custom points
    505: (3, 0, 16.0, False, False),  # age-capped @Heroic
    506: (4, 0,  0.0, True,  False),  # Mythic start, NO TC — always accessible
    507: (3, 0,  0.0, True,  False),  # always accessible — sphere 1
    508: (3, 0, 16.0, False, False),  # custom: no age floor
    509: (3, 0,  2.0, False, False),  # custom: no age floor + points
    510: (3, 3, 16.0, False, False),  # reach Mythic (1 advancement)
    511: (4, 0, 21.0, False, False),  # age-capped @Mythic; custom points
    512: (4, 0,  9.0, False, False),  # age-capped @Mythic; custom points
    # ---------------------------------------------------------------------------
    # The Golden Gift (APScenarioIDs 601-604)
    # 601,602 age-capped @Heroic; 603 heroic-floor (Mythic via 3 unlocks);
    # 604 points-only gate (was always-accessible).
    # ---------------------------------------------------------------------------
    601: (3, 0,  9.0,  False, False),  # age-capped @Heroic; custom points
    602: (3, 0,  4.0,  False, False),  # age-capped @Heroic
    603: (3, 0, 16.0,  False, False),  # heroic-floor; custom points
    604: (4, 0,  2.0,  False, False),  # points-only gate (custom; no longer exempt)
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
    # New Atlantis (APScenarioIDs 501-512)
    501: "Atlantean", 502: "Atlantean", 503: "Atlantean", 504: "Atlantean",
    505: "Atlantean", 506: "Atlantean", 507: "Egyptian",  508: "Egyptian",
    509: "Norse",     510: "Atlantean", 511: "Atlantean", 512: "Atlantean",
    # The Golden Gift (APScenarioIDs 601-604)
    601: "Norse", 602: "Norse", 603: "Norse", 604: "Norse",
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
    # New Atlantis (APScenarioIDs 501-512)
    501: 11, 502: 10, 503: 10, 504: 10, 505: 10, 506: 10,
    507:  5, 508:  6, 509:  8, 510: 12, 511: 11, 512: 12,
    # The Golden Gift (APScenarioIDs 601-604)
    601: 8, 602: 9, 603: 9, 604: 8,
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
        # Hirdman intentionally omitted — its unlock item is classified Useful,
        # not Progression, so it must not gate scenario access here.
        1: ["Can train Throwing Axeman", "Can train Raiding Cavalry"],
        2: ["Can train Jarl", "Can train Huskarl"],
    },
    "Atlantean": {
        1: ["Can train Murmillo", "Can train Katapeltes",
            "Can train Turma", "Can train Cheiroballista"],
        2: ["Can train Contarius", "Can train Arcus", "Can train Destroyer"],
        3: ["Can train Fanatic"],
    },
    "Chinese": {
        1: ["Can train Dao Swordsman", "Can train Ge Halberdier",
            "Can train Wuzu Javelineer", "Can train Fire Archer"],
        2: ["Can train Chu Ko Nu", "Can train White Horse Cavalry"],
        3: ["Can train Tiger Cavalry"],
    },
    "Japanese": {
        1: ["Can train Yari Spearman", "Can train Yumi Archer",
            "Can train Samurai", "Can train Naginata Rider"],
        2: ["Can train Yumi Horse Archer", "Can train Shinobi"],
        # Japanese has no Mythic-tier human unit — Mythic logic relies on the
        # myth-tier item ("Can train Japanese Mythic Myth Units") instead.
    },
    "Aztec": {
        0: ["Can train Quimichin Spy"],   # archaic-trainable HumanSoldier
        1: ["Can train Tlamanih Spearman", "Can train Tequihua Archer",
            "Can train Coyote Warrior", "Can train Ocelotl Warrior"],
        2: ["Can train Eagle Warrior", "Can train Otontin", "Can train Shorn One"],
        3: ["Can train Jaguar Rider"],
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
    "Chinese": {
        1: "Can train Chinese Classical Myth Units",
        2: "Can train Chinese Heroic Myth Units",
        3: "Can train Chinese Mythic Myth Units",
    },
    "Japanese": {
        1: "Can train Japanese Classical Myth Units",
        2: "Can train Japanese Heroic Myth Units",
        3: "Can train Japanese Mythic Myth Units",
    },
    "Aztec": {
        1: "Can train Aztec Classical Myth Units",
        2: "Can train Aztec Heroic Myth Units",
        3: "Can train Aztec Mythic Myth Units",
    },
}


# --------------------------------------------------
# Titan access  (civ → "Unlock <Civ> Titan Age" item name)
# --------------------------------------------------
# Building a Titan Gate counts as a trainable military unit (and toward the
# points gate) when ALL of the following hold:
#   1. the scenario has a town center (the player can age up / build the gate),
#   2. the player can reach the Mythic age in that scenario, and
#   3. the player holds the Titan Age item matching the scenario's civ.
_TITAN_ITEM_BY_CIV: dict[str, str] = {
    item.type.culture: item.item_name
    for item in aomItemData
    if isinstance(item.type, TitanAgeUnlock)
}

# Scenarios with no town center.  Without a town center the player can neither
# advance ages nor place a Titan Gate, so a Titan never counts as a trainable
# unit or toward the points gate here.  (Exempt / scenario-7 no-TC scenarios
# don't run the unit machinery anyway; they're listed for documentation and
# defence-in-depth.)
_SCENARIO_NO_TC: frozenset = frozenset({1, 7, 25, 503, 506})

# Point value of a buildable Titan toward the per-scenario points threshold.
_TITAN_POINTS: float = 10.0


def _titan_buildable(
    state: CollectionState,
    player: int,
    god_civ: str,
    can_reach_mythic: bool,
    has_town_center: bool,
) -> bool:
    """True when the player could build a Titan in this scenario: a town centre
    is present, the Mythic age is reachable, and the civ's Titan Age item is
    held."""
    if not (has_town_center and can_reach_mythic):
        return False
    titan_item = _TITAN_ITEM_BY_CIV.get(god_civ)
    return bool(titan_item) and state.has(titan_item, player)


# --------------------------------------------------
# Non-combative myth units
# --------------------------------------------------
# Some minor gods grant only a non-combative myth unit (e.g. the Atlantean
# Oceanus grants the Caladria, a healing unit).  When such a god is a scenario's
# FORCED floor minor god, the matching "Can train <Civ> <Tier> Myth Units" item
# only ever produces that non-combat unit, so it must NOT satisfy the trainable-
# military-unit requirement on its own.  Above-floor tiers are excluded because
# the player picks the minor god freely there and can choose a combat one.
#   tech const name -> (civ, tier) of the myth-unit item it would otherwise gate.
_NONCOMBAT_MINOR_GOD_TECHS: dict[str, tuple] = {
    "cTechClassicalAgeOceanus": ("Atlantean", 1),  # Oceanus -> Caladria (healer)
}


def _excluded_myth_items(floor_minor_god_techs) -> frozenset:
    """Myth-unit item names that do NOT count as a trainable military unit for a
    scenario, because its forced floor minor god grants only a non-combative
    myth unit (currently only Oceanus -> Caladria).

    `floor_minor_god_techs` is the scenario's `minor_god_assignments` entry — a
    flat list of floor age-tech const names (base + minor interleaved)."""
    out = set()
    for tech in (floor_minor_god_techs or []):
        info = _NONCOMBAT_MINOR_GOD_TECHS.get(tech)
        if info is None:
            continue
        civ, tier = info
        item = _MYTH_ITEMS_BY_UNLOCK.get(civ, {}).get(tier)
        if item:
            out.add(item)
    return frozenset(out)


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
    StartingArmy:          1.0,
    StartingArmyUseful:    2.0,
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

_BASE_POINTS[ChineseUnitUnlockProgression]  = 3.0
_BASE_POINTS[ChineseUnitUnlockUseful]       = 3.0
_BASE_POINTS[ChineseMythUnitUnlock]         = 5.0
_BASE_POINTS[JapaneseUnitUnlockProgression] = 3.0
_BASE_POINTS[JapaneseUnitUnlockUseful]      = 3.0
_BASE_POINTS[JapaneseMythUnitUnlock]        = 5.0
_BASE_POINTS[AztecUnitUnlockProgression]    = 3.0
_BASE_POINTS[AztecUnitUnlockUseful]         = 3.0
_BASE_POINTS[AztecMythUnitUnlock]           = 5.0


def _item_point_value(item: aomItemData) -> float:
    """Score an item for the per-scenario points gate.

    Reginleif/Odysseus "Joins" items are special-cased high (4.0) because
    they grant a hero immediately on receipt and substantially boost combat.

    Hero stat/action/special boosts are scaled by the hero's relative usefulness:
      Arkantos        : x2.0 (always present in FotT, gets the most mileage)
      Odysseus/Reginleif: x0.5 (only present in 1-2 scenarios)
      Other heroes      : x1.0
    """
    if item == aomItemData.REGINLEIF_JOINS or item == aomItemData.ODYSSEUS_JOINS:
        return 4.0
    if item == aomItemData.AJAX_AMANRA_DREAMS:
        return 0.0

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
    """Build {item_name: points} for every item in the catalog.  Computed once
    per `set_rules` invocation and passed to every per-scenario rule so the
    per-call cost is just dict lookups."""
    return {item.item_name: _item_point_value(item) for item in aomItemData}


def count_points(state: CollectionState, player: int, point_table: dict[str, float]) -> float:
    """Sum of points across all items the player currently has.  AP calls
    this many times during fill, so it's optimized to skip 0-valued items."""
    total = 0.0
    for item_name, value in point_table.items():
        if value > 0.0:
            count = state.count(item_name, player)
            if count > 0:
                total += count * value
    return total


# --------------------------------------------------
# Age-capped scenarios: the player starts at a given age and cannot advance
# beyond it (no TC, no Mythic temple, or scenario design cap).
# Key = scenario global_number, value = max accessible age tier (0-3).
# All units at tiers 0..max_tier are freely accessible with only the
# corresponding 'Can train X' item — no age unlock items are required.
# --------------------------------------------------

# Scenarios where the starting age grants free access to all tiers up to the cap.
# No age unlock items are needed; the player simply cannot advance beyond max_tier.
_SCENARIO_AGE_CAP: dict[int, int] = {
    501: 2,  # NA 1:  starts Heroic, max Heroic → capped at tier 2
    503: 2,  # NA 3:  starts Heroic, no TC     → capped at tier 2
    504: 2,  # NA 4:  starts Heroic, max Heroic → capped at tier 2
    505: 2,  # NA 5:  starts Heroic, max Heroic → capped at tier 2
    511: 3,  # NA 11: starts Mythic, max Mythic → capped at tier 3
    512: 3,  # NA 12: starts Mythic, max Mythic → capped at tier 3
    601: 2,  # GG 1:  starts Heroic, max Heroic → capped at tier 2
    602: 2,  # GG 2:  starts Heroic, max Heroic → capped at tier 2
}

# Scenarios where the starting age gives free access to tiers 0-2, but tier 3
# (Mythic) is still reachable with 3 age unlock items.
# These are NOT in _SCENARIO_AGE_CAP; they use _make_heroic_floor_scenario_rule.
_SCENARIO_HEROIC_FLOOR: set[int] = {
    603,  # GG 3: Heroic start, Mythic max — Classical/Heroic units free, Mythic needs 3 unlocks
}


def _make_age_capped_scenario_rule(
    player: int,
    god_id: int,
    max_tier: int,
    point_table: dict[str, float],
    points_needed: float,
    scenario_n: int = 0,
    excluded_myth: frozenset = frozenset(),
):
    """Rule for scenarios whose max accessible age is fixed at scenario start.

    The starting age is already granted, so no age unlock items are needed.
    Any human or myth unit at tier <= max_tier puts the scenario in logic.
    Tiers above max_tier (e.g. Mythic on a Heroic-capped scenario) never count.

    A Titan also counts as a trainable unit when the cap reaches Mythic
    (max_tier >= 3), the scenario has a town centre, and the civ's Titan Age
    item is held.
    """
    god_civ = _GOD_TO_CIV.get(god_id, "Greek")
    has_tc  = scenario_n not in _SCENARIO_NO_TC

    def rule(state: CollectionState) -> bool:
        can_titan = _titan_buildable(state, player, god_civ, max_tier >= 3, has_tc)
        points = count_points(state, player, point_table)
        if can_titan:
            points += _TITAN_POINTS
        if points < points_needed:
            return False
        if can_titan:
            return True
        for tier in range(0, max_tier + 1):
            for unit_name in _HUMAN_UNITS.get(god_civ, {}).get(tier, []):
                if state.has(unit_name, player):
                    return True
        for tier in range(1, max_tier + 1):
            myth_name = _MYTH_ITEMS_BY_UNLOCK.get(god_civ, {}).get(tier)
            if myth_name and myth_name not in excluded_myth and state.has(myth_name, player):
                return True
        return False

    return rule


def _make_heroic_floor_scenario_rule(
    player: int,
    god_id: int,
    point_table: dict[str, float],
    points_needed: float,
    scenario_n: int = 0,
    excluded_myth: frozenset = frozenset(),
):
    """Rule for Heroic-start, Mythic-max scenarios where the starting age floor
    grants free access to tiers 0-2, but Mythic (tier 3) still requires 3 unlocks.

    Used for scenarios like GG 3 where Classical and Heroic human/myth units are
    immediately trainable, but advancing to Mythic requires age unlock items.

    A Titan counts as a trainable unit once Mythic is reachable (3 unlocks), the
    scenario has a town centre, and the civ's Titan Age item is held.
    """
    god_civ = _GOD_TO_CIV.get(god_id, "Greek")
    unlock_names = _CIV_UNLOCK_NAMES[god_civ]
    has_tc  = scenario_n not in _SCENARIO_NO_TC

    def rule(state: CollectionState) -> bool:
        unlock_count = min(sum(state.count(n, player) for n in unlock_names), 3)
        can_titan = _titan_buildable(state, player, god_civ, unlock_count >= 3, has_tc)
        points = count_points(state, player, point_table)
        if can_titan:
            points += _TITAN_POINTS
        if points < points_needed:
            return False
        if can_titan:
            return True
        # Tiers 0-2: freely accessible at Heroic start
        for tier in range(0, 3):
            for unit_name in _HUMAN_UNITS.get(god_civ, {}).get(tier, []):
                if state.has(unit_name, player):
                    return True
        for tier in range(1, 3):
            myth_name = _MYTH_ITEMS_BY_UNLOCK.get(god_civ, {}).get(tier)
            if myth_name and myth_name not in excluded_myth and state.has(myth_name, player):
                return True
        # Tier 3 (Mythic): needs 3 age unlock items
        if unlock_count >= 3:
            for unit_name in _HUMAN_UNITS.get(god_civ, {}).get(3, []):
                if state.has(unit_name, player):
                    return True
            myth_name = _MYTH_ITEMS_BY_UNLOCK.get(god_civ, {}).get(3)
            if myth_name and myth_name not in excluded_myth and state.has(myth_name, player):
                return True
            if god_id in _GREEK_FREE_MYTHIC_GODS:
                return True
        return False

    return rule


# --------------------------------------------------
# Per-scenario military + point rule factory
# --------------------------------------------------

def _make_scenario_rule(
    player: int,
    god_id: int,
    vanilla_civ: str,
    start_age_num: int,
    min_required_unlocks: int,
    is_myth_only: bool,
    point_table: dict[str, float],
    points_needed: float,
    scenario_n: int = 0,
    excluded_myth: frozenset = frozenset(),
):
    """Build the access rule for a scenario.

    Two requirements must both be met:

    1. AGE FLOOR: unlock_count >= min_required_unlocks.
       The player must be able to reach at least the vanilla max age for this
       scenario. This is a minimum — with more unlocks they can go higher.

    2. MILITARY UNIT: the player can train at least one military unit whose age
       tier is <= their current unlock_count. A unit at tier T is accessible
       only if unlock_count >= T (the player has actually reached that age).

    Tiers:
      0 = Archaic   (available at start, no unlock needed)
      1 = Classical (needs 1 age unlock item)
      2 = Heroic    (needs 2 age unlock items)
      3 = Mythic    (needs 3 age unlock items)

    Starting-age myth units (vanilla_starting_myth) have their techs
    pre-researched, so the player only needs the ITEM — but they still must
    meet the age floor before those count as putting the scenario in logic.
    """
    MAX_AGE_TIERS = 3
    god_civ      = _GOD_TO_CIV.get(god_id, "Greek")
    unlock_names = _CIV_UNLOCK_NAMES[god_civ]
    has_tc       = scenario_n not in _SCENARIO_NO_TC

    # Myth units whose techs are pre-researched at scenario start.
    # These are accessible without spending unlock items on their age tier,
    # but the player must still meet the min_required_unlocks floor.
    vanilla_starting_myth: list[str] = [
        _MYTH_ITEMS_BY_UNLOCK[god_civ][tier]
        for tier in range(1, start_age_num)
        if tier in _MYTH_ITEMS_BY_UNLOCK.get(god_civ, {})
        and _MYTH_ITEMS_BY_UNLOCK[god_civ][tier] not in excluded_myth
    ]

    def rule(state: CollectionState) -> bool:
        unlock_count = min(sum(state.count(n, player) for n in unlock_names), MAX_AGE_TIERS)

        # A buildable Titan (town centre + Mythic reachable + civ Titan item)
        # counts as a trainable unit and adds _TITAN_POINTS to the points gate.
        can_titan = _titan_buildable(state, player, god_civ, unlock_count >= 3, has_tc)

        points = count_points(state, player, point_table)
        if can_titan:
            points += _TITAN_POINTS
        if points < points_needed:
            return False

        # ── Requirement 1: age floor ──────────────────────────────────────
        # Player must be able to reach at least the vanilla max age.
        # Applied before unit checks so a player with Classical myths and
        # 0 unlocks cannot enter a Heroic-floor scenario like scenario 24.
        if unlock_count < min_required_unlocks:
            return False

        # A Titan satisfies the military-unit requirement (myth-only too — it
        # requires Mythic, the strictest tier).
        if can_titan:
            return True

        # ── Requirement 2: military unit ──────────────────────────────────
        # is_myth_only: only myth units count; must have a starting-age one.
        if is_myth_only:
            return bool(vanilla_starting_myth) and any(
                state.has(m, player) for m in vanilla_starting_myth
            )

        # Starting-age myth units: tech is pre-researched so the ITEM alone
        # suffices — no unlock items needed for their tier.
        # Age floor is already satisfied above.
        if vanilla_starting_myth and any(state.has(m, player) for m in vanilla_starting_myth):
            return True

        # Higher tiers: player must have enough unlock items to reach that age.
        # Loop 0..unlock_count — units at tiers > unlock_count are inaccessible.
        for needed in range(0, MAX_AGE_TIERS + 1):
            if unlock_count < needed:
                break
            for unit_name in _HUMAN_UNITS.get(god_civ, {}).get(needed, []):
                if state.has(unit_name, player):
                    return True
            if needed >= 1:
                myth_name = _MYTH_ITEMS_BY_UNLOCK.get(god_civ, {}).get(needed)
                if myth_name and myth_name not in excluded_myth and state.has(myth_name, player):
                    return True
            # Note: Norse Berserks (tier 0) are handled by the human unit loop above.
            # No special shortcut — Norse tier 1+ units require their items like any civ.
            if god_id in _GREEK_FREE_MYTHIC_GODS and needed >= 3:
                return True

        return False

    return rule


def _human_unit_item_names() -> set:
    """Set of item names for human (non-myth) unit unlocks across every civ.
    Used by the scenario-7 points rule, which excludes human-unit items from
    its point total.  Shared between the generation rule and the client-side
    in-logic replica so the two never drift."""
    human_unit_types = (UnitUnlockProgression, UnitUnlockUseful)
    if _ATLANTEAN_TYPES:
        human_unit_types = human_unit_types + (
            AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful
        )
    human_unit_types = human_unit_types + (
        ChineseUnitUnlockProgression, ChineseUnitUnlockUseful,
        JapaneseUnitUnlockProgression, JapaneseUnitUnlockUseful,
        AztecUnitUnlockProgression, AztecUnitUnlockUseful,
    )
    return {
        item.item_name for item in aomItemData
        if isinstance(item.type, human_unit_types)
    }


def _scenario7_effective_table(point_table: dict[str, float]) -> dict[str, float]:
    """Copy of `point_table` with every human-unit item zeroed — scenario 7's
    points gate ignores human-unit unlocks."""
    names = _human_unit_item_names()
    return {
        name: (0.0 if name in names else val)
        for name, val in point_table.items()
    }


def _get_scenario_god(world, scenario_n: int) -> int:
    """Resolve the god assigned to a scenario for rule purposes.  When
    `random_major_gods` is on `world.god_assignments` is a real mapping;
    otherwise fall back to the vanilla god so non-randomized seeds still
    use the correct civ for unit-availability rules.

    Args:
        scenario_n: APScenarioID (the scenario's `global_number`).
    """
    assignments = getattr(world, "god_assignments", {})
    if assignments:
        return assignments.get(scenario_n, _VANILLA_GODS[scenario_n])
    return _VANILLA_GODS[scenario_n]


# --------------------------------------------------
# Client-side reachability replica (gates 1-5)
# --------------------------------------------------

class _DictState:
    """Minimal `CollectionState` stand-in backed by a plain item-name → count
    dict.  Implements only the `has` / `count` surface the scenario rule
    factories touch, so the *generation* rules can be replayed by the client
    without a multiworld.  Keeps the logic definition in one place."""

    def __init__(self, counts: dict[str, int]):
        self._counts = counts

    def has(self, name: str, player: int, count: int = 1) -> bool:
        return self._counts.get(name, 0) >= count

    def count(self, name: str, player: int) -> int:
        return self._counts.get(name, 0)


def compute_scenarios_in_logic(
    received_counts: dict[str, int],
    god_assignments: dict[int, int],
    campaign_unlocked_by_id: dict[int, bool],
    scenario_to_gate_id: dict[int, int],
    held_gate_ids: set,
    max_keys_on_keyrings: int,
    disabled_campaign_ids: set = frozenset(),
    player: int = 1,
    minor_god_assignments: dict = None,
) -> dict[int, bool]:
    """Replay gates 1-5 for every scenario without a multiworld and return
    `{global_number: in_logic}`.

    Mirrors `set_section_rules` (gate 1), `set_scenario_key_rules` (gate 2)
    and `set_scenario_age_and_point_rules` (gates 3-5: age floor, military
    unit, points) by reusing the very same rule factories against a
    `_DictState` built from the player's received items.

    Args:
        received_counts:         item_name → count the player currently holds.
        god_assignments:         scenario global_number → major-god id (empty
                                 dict for non-randomized seeds → vanilla gods).
        campaign_unlocked_by_id: campaign.id → bool (section/Final unlock).
        scenario_to_gate_id:     scenario global_number → gate item id (Scenario
                                 Key or Key Ring); only consulted when
                                 max_keys_on_keyrings > 0.
        held_gate_ids:           gate item ids the player holds.
        max_keys_on_keyrings:    option value (0 = key gate off).
        disabled_campaign_ids:   campaign.id ints to skip.
    """
    state       = _DictState(received_counts)
    point_table = build_point_table()
    eff7        = _scenario7_effective_table(point_table)
    minor_god_assignments = minor_god_assignments or {}
    result: dict[int, bool] = {}

    for scenario in aomScenarioData:
        if scenario.campaign.id in disabled_campaign_ids:
            continue
        n    = scenario.global_number
        data = _SCENARIO_DATA.get(n)
        if data is None:
            continue
        start_age_num, min_required_unlocks, points_needed, is_exempt, is_myth_only = data

        # Gate 1 — section / Final unlock.
        if not campaign_unlocked_by_id.get(scenario.campaign.id, False):
            result[n] = False
            continue

        # Gate 2 — scenario key / key ring.
        if max_keys_on_keyrings > 0:
            gid = scenario_to_gate_id.get(n)
            if gid is not None and gid not in held_gate_ids:
                result[n] = False
                continue

        # Gates 3-5 — exempt scenarios skip the age/military/points machinery.
        if is_exempt:
            result[n] = True
            continue

        god_id       = god_assignments.get(n) or _VANILLA_GODS[n]
        god_civ      = _GOD_TO_CIV.get(god_id, "Greek")
        unlock_names = _CIV_UNLOCK_NAMES[god_civ]
        excl         = _excluded_myth_items(minor_god_assignments.get(n, []))

        if n in _SCENARIO_AGE_CAP:
            rule = _make_age_capped_scenario_rule(
                player, god_id, _SCENARIO_AGE_CAP[n], point_table, points_needed,
                scenario_n=n, excluded_myth=excl,
            )
            result[n] = rule(state)
            continue

        if n in _SCENARIO_HEROIC_FLOOR:
            rule = _make_heroic_floor_scenario_rule(
                player, god_id, point_table, points_needed,
                scenario_n=n, excluded_myth=excl,
            )
            result[n] = rule(state)
            continue

        if n == 604:
            result[n] = count_points(state, player, point_table) >= points_needed
            continue

        if n == 7:
            result[n] = count_points(state, player, eff7) >= points_needed
            continue

        rule = _make_scenario_rule(
            player, god_id, _VANILLA_CIV[n],
            start_age_num, min_required_unlocks, is_myth_only,
            point_table, points_needed,
            scenario_n=n, excluded_myth=excl,
        )
        ok = rule(state)
        if ok and n == 2:
            ok = count_civ_unlocks(state, player, unlock_names) >= 1
        if ok and n == 32:
            ok = count_civ_unlocks(state, player, unlock_names) >= 3
        result[n] = ok

    return result


# --------------------------------------------------
# Completion events
# --------------------------------------------------

def place_completion_events(world) -> None:
    """Place a locked event item on every scenario's COMPLETION location and
    the singular Victory item on FOTT_32's Victory location.

    Completion event items have `code=None` so they only exist in collection
    state — they're not real AP items.  Other rules check
    `state.has(<event_name>, player)` to see if a scenario was beaten.

    Skips scenarios in disabled campaigns.

    Called from `set_rules`.
    """
    player    = world.player
    multiworld = world.multiworld
    disabled_campaigns = getattr(world, "disabled_campaigns", set())
    for scenario in aomScenarioData:
        if scenario.campaign in disabled_campaigns:
            continue
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
# Section access rules
# --------------------------------------------------

def set_section_rules(world) -> None:
    """Install access rules for each Menu→<campaign-section> entrance.

    The four FotT sections gate on their Campaign item (Greek/Egyptian/Norse
    Scenarios, plus optional NewAtlantis and GoldenGift).  The Final section
    is gated by the FinalScenarios option (always_open / atlantis_key /
    beat_x_scenarios).

    Disabled campaigns are skipped — `regions/Regions.py` won't have created
    those entrances either.

    Called from `set_rules`.
    """
    player    = world.player
    multiworld = world.multiworld
    from ..locations.Campaigns import aomCampaignData
    disabled = getattr(world, "disabled_campaigns", set())

    def _maybe_set(campaign, region_name, rule):
        if campaign in disabled:
            return
        ent = multiworld.get_entrance(entrance_name("Menu", region_name), player)
        set_rule(ent, rule)

    _maybe_set(aomCampaignData.FOTT_GREEK,    "Fall of the Trident: Greek",
               lambda state: state.has(aomItemData.GREEK_SCENARIOS.item_name, player))
    _maybe_set(aomCampaignData.FOTT_EGYPTIAN, "Fall of the Trident: Egyptian",
               lambda state: state.has(aomItemData.EGYPTIAN_SCENARIOS.item_name, player))
    _maybe_set(aomCampaignData.FOTT_NORSE,    "Fall of the Trident: Norse",
               lambda state: state.has(aomItemData.NORSE_SCENARIOS.item_name, player))
    _maybe_set(aomCampaignData.NEW_ATLANTIS,  "The New Atlantis",
               lambda state: state.has(aomItemData.UNLOCK_NEW_ATLANTIS.item_name, player))
    _maybe_set(aomCampaignData.GOLDEN_GIFT,   "The Golden Gift",
               lambda state: state.has(aomItemData.UNLOCK_GOLDEN_GIFT.item_name, player))

    mode = get_final_mode_value(world)
    if mode == FinalScenarios.option_always_open:
        _maybe_set(aomCampaignData.FOTT_FINAL, "Fall of the Trident: Final",
                   lambda state: True)
    elif mode == FinalScenarios.option_beat_x_scenarios:
        required = get_x_scenarios_value(world)
        _maybe_set(aomCampaignData.FOTT_FINAL, "Fall of the Trident: Final",
                   lambda state, r=required: count_completed_scenarios(state, player) >= r)
    else:  # atlantis_key
        _maybe_set(aomCampaignData.FOTT_FINAL, "Fall of the Trident: Final",
                   lambda state: state.has(aomItemData.ATLANTIS_KEY.item_name, player))


# --------------------------------------------------
# Per-scenario military + point rules
# --------------------------------------------------

def set_scenario_age_and_point_rules(world, point_table: dict[str, float]) -> None:
    """Apply per-scenario age/military/points access rules to every
    section→scenario entrance.

    Three kinds of scenarios get different rule machinery:
      * `_SCENARIO_AGE_CAP[n]` — fixed-age scenarios; uses
        `_make_age_capped_scenario_rule` (no unlock items needed).
      * `_SCENARIO_HEROIC_FLOOR` — Heroic-floor + Mythic-max; uses
        `_make_heroic_floor_scenario_rule` (3 unlocks for Mythic).
      * everything else — uses `_make_scenario_rule` with min_required_unlocks
        and points gates pulled from `_SCENARIO_DATA`.

    Two scenarios get hard-floor add_rules layered on top:
      * scenario 2: needs at least 1 unlock (Advance to Classical objective)
      * scenario 32: needs 3 unlocks (must reach Mythic to build the Wonder)

    Args:
        world:        the aomWorld
        point_table:  output of `build_point_table()` — passed in to avoid
                      rebuilding it per-scenario.
    """
    player    = world.player
    multiworld = world.multiworld
    disabled_campaigns = getattr(world, "disabled_campaigns", set())

    section_names = {
        "Greek":       "Fall of the Trident: Greek",
        "Egyptian":    "Fall of the Trident: Egyptian",
        "Norse":       "Fall of the Trident: Norse",
        "Final":       "Fall of the Trident: Final",
        "NewAtlantis": "The New Atlantis",
        "GoldenGift":  "The Golden Gift",
    }

    def section_for(n: int) -> str:
        if n <= 10:          return section_names["Greek"]
        if n <= 20:          return section_names["Egyptian"]
        if n <= 30:          return section_names["Norse"]
        if n <= 32:          return section_names["Final"]
        if 501 <= n <= 512:  return section_names["NewAtlantis"]
        if 601 <= n <= 604:  return section_names["GoldenGift"]
        return section_names["Final"]

    for scenario in aomScenarioData:
        if scenario.campaign in disabled_campaigns:
            continue
        n = scenario.global_number
        start_age_num, min_required_unlocks, points_needed, is_exempt, is_myth_only = _SCENARIO_DATA[n]

        if is_exempt:
            continue

        god_id      = _get_scenario_god(world, n)
        vanilla_civ = _VANILLA_CIV[n]
        god_civ     = _GOD_TO_CIV.get(god_id, "Greek")
        unlock_names = _CIV_UNLOCK_NAMES[god_civ]
        excl = _excluded_myth_items(
            getattr(world, "minor_god_assignments", {}).get(n, [])
        )

        ent_name = entrance_name(section_for(n), scenario.region_name)
        entrance = multiworld.get_entrance(ent_name, player)

        # Age-capped scenario: player cannot advance beyond the starting age.
        # All units up to the capped tier are freely accessible without unlock items.
        if n in _SCENARIO_AGE_CAP:
            add_rule(entrance, _make_age_capped_scenario_rule(
                player, god_id, _SCENARIO_AGE_CAP[n], point_table, points_needed,
                scenario_n=n, excluded_myth=excl,
            ))
            continue

        # Heroic-floor scenario: tiers 0-2 are freely accessible (Heroic start),
        # but Mythic (tier 3) still requires 3 age unlock items.
        if n in _SCENARIO_HEROIC_FLOOR:
            add_rule(entrance, _make_heroic_floor_scenario_rule(
                player, god_id, point_table, points_needed,
                scenario_n=n, excluded_myth=excl,
            ))
            continue

        # Scenario 604: points-only gate (no age/military requirement) using the
        # full point table.  Formerly exempt (always accessible).
        if n == 604:
            add_rule(entrance,
                lambda state, p=points_needed:
                    count_points(state, player, point_table) >= p
            )
            continue

        # Scenario 7: human unit unlocks don't count toward points,
        # no age or military unit unlock required — just 1 point of non-unit items.
        if n == 7:
            effective_table = _scenario7_effective_table(point_table)
            add_rule(entrance,
                lambda state, t=effective_table, p=points_needed:
                    count_points(state, player, t) >= p
            )
            continue

        else:
            effective_table = point_table

        # Age floor + military rule. min_required_unlocks is the vanilla max age
        # (a floor, not a cap — player can advance further with more unlocks).
        add_rule(entrance, _make_scenario_rule(
            player, god_id, vanilla_civ,
            start_age_num, min_required_unlocks, is_myth_only,
            effective_table, points_needed,
            scenario_n=n, excluded_myth=excl,
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
    """Mark non-victory FOTT_32 locations as EXCLUDED so AP fill won't place
    progression items there.  Scenario 32 is the win condition — players
    shouldn't be required to collect optional objectives or relics there
    just to finish a multiworld.  Victory and COMPLETION are exempt
    (Victory holds the actual Victory item; COMPLETION is the locked event).

    Called from `set_rules`.
    """
    player    = world.player
    multiworld = world.multiworld
    disabled_campaigns = getattr(world, "disabled_campaigns", set())
    relicsanity_on = bool(getattr(world, "relicsanity_enabled", False))
    for location_data in aomLocationData:
        if location_data.scenario.campaign in disabled_campaigns:
            continue
        if location_data.scenario != aomScenarioData.FOTT_32:
            continue
        if location_data.type in (aomLocationType.VICTORY, aomLocationType.COMPLETION):
            continue
        if not relicsanity_on and location_data.type == aomLocationType.RELIC:
            continue
        location = multiworld.get_location(location_data.global_name(), player)
        location.progress_type = LocationProgressType.EXCLUDED


# --------------------------------------------------
# Item placement restrictions
# --------------------------------------------------

def set_item_placement_restrictions(world) -> None:
    """Forbid each campaign's section-unlock item from being placed at any
    location inside that same section.  Without this, a player could be
    locked behind their own section unlock — e.g. Greek Scenarios placed
    inside scenario 5, which is itself inside the Greek section.

    Called from `set_rules`.
    """
    player    = world.player
    multiworld = world.multiworld
    campaign_to_forbidden = {
        "FOTT_GREEK":    aomItemData.GREEK_SCENARIOS.item_name,
        "FOTT_EGYPTIAN": aomItemData.EGYPTIAN_SCENARIOS.item_name,
        "FOTT_NORSE":    aomItemData.NORSE_SCENARIOS.item_name,
        "FOTT_FINAL":    aomItemData.ATLANTIS_KEY.item_name,
        "NEW_ATLANTIS":  aomItemData.UNLOCK_NEW_ATLANTIS.item_name,
        "GOLDEN_GIFT":   aomItemData.UNLOCK_GOLDEN_GIFT.item_name,
    }
    disabled_campaigns = getattr(world, "disabled_campaigns", set())
    relicsanity_on = bool(getattr(world, "relicsanity_enabled", False))
    for location_data in aomLocationData:
        if location_data.scenario.campaign in disabled_campaigns:
            continue
        if not relicsanity_on and location_data.type == aomLocationType.RELIC:
            continue
        location  = multiworld.get_location(location_data.global_name(), player)
        forbidden = campaign_to_forbidden.get(location_data.scenario.campaign.name)
        if forbidden:
            forbid_item(location, forbidden, player)


# --------------------------------------------------
# Win condition
# --------------------------------------------------

def set_completion_rule(world) -> None:
    """Tell AP what 'beating the multiworld' means for this slot:
    receiving the Victory item.  Called once during set_rules.

    NOTE: this function is currently NOT called from `set_rules` — the win
    condition is implicit because the Victory item is locked to FOTT_32's
    Victory location and standard AP framework treats holding the Victory
    item as the world's completion signal.  Kept here for clarity in case
    future changes need explicit completion wiring.
    """
    world.multiworld.completion_condition[world.player] = (
        lambda state: state.has("Victory", world.player)
    )


# --------------------------------------------------
# Entry point
# --------------------------------------------------



def place_gems(world) -> None:
    """Lock Gems at Victory locations 1-31 when gem_shop is on; otherwise leave them for pool fill.

    Honors `starting_gems_from_pool` (parsed from `start_inventory_from_pool: Gem: N`):
    N randomly-chosen Victory locations are SKIPPED here — those slots become
    free-fill (AP will drop filler/useful there) and N precollected Gem items
    are pushed via create_items in lockstep.  Player ends with the same total
    gems either way; the swap just front-loads them."""
    if not world.gem_shop_enabled:
        return  # victories hold random pool items when shop is disabled
    player     = world.player
    multiworld = world.multiworld
    disabled_campaigns = getattr(world, "disabled_campaigns", set())

    eligible = [
        s for s in aomScenarioData
        if s != aomScenarioData.FOTT_32 and s.campaign not in disabled_campaigns
    ]

    # Pick which Victories to SKIP (swapped to free-fill).  Deterministic via
    # world.random so the same seed reproduces the same swap.
    n_skip = max(0, int(getattr(world, "starting_gems_from_pool", 0)))
    n_skip = min(n_skip, len(eligible))
    skip_set: set = set()
    if n_skip > 0:
        skip_set = set(world.random.sample(eligible, n_skip))

    for scenario in eligible:
        if scenario in skip_set:
            continue
        loc = multiworld.get_location(VICTORY_LOCATIONS[scenario].global_name(), player)
        gem = world.create_item(aomItemData.GEM.item_name)
        loc.place_locked_item(gem)


def place_progressive_shop_info(world) -> None:
    """Lock one Progressive Shop Info item at each shop's hint slot 1 location.
    Shop A has no PSI button — only B/C/D get a PSI placement (via
    `PROGRESSIVE_INFO_IDS`, which already excludes A)."""
    if not world.gem_shop_enabled:
        return
    player     = world.player
    multiworld = world.multiworld
    for tier, loc_id in PROGRESSIVE_INFO_IDS.items():
        name = location_id_to_name.get(loc_id)
        if not name:
            continue
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
        # Also gate the progressive info location for this tier (only B/C/D
        # have a PSI location; A is absent from PROGRESSIVE_INFO_IDS).
        pi_id = PROGRESSIVE_INFO_IDS.get(tier_name)
        if pi_id is None:
            continue
        pi_name = location_id_to_name.get(pi_id)
        if pi_name:
            loc = multiworld.get_location(pi_name, player)
            set_rule(loc, lambda state, r=required: count_completed_scenarios(state, player) >= r)

    # The Marsh shop (tier A) is always open and accessible early, so progression
    # items must never appear there — players buy blind and could otherwise lock
    # themselves out of required items. Useful items are still allowed.
    marsh_item_ids = set(TIER_ITEM_IDS.get("A", []))

    # Item classification per location:
    #   - exactly 1 progression slot per non-Marsh shop (no restriction)
    #   - Marsh shop: filler/useful/trap only (no progression)
    #   - randomly excluded locations get no item_rule (filler/trap fills them via AP)
    #   - ~half of the remaining non-excluded are filler-only
    #   - the rest accept filler or useful (not progression)
    prog_slots   = getattr(world, "shop_progression_slots", {})
    filler_only  = getattr(world, "shop_filler_only", set())

    # Flatten the per-tier set of progression-allowed slot ids for membership checks.
    all_prog_slot_ids: set[int] = set()
    for _ids in prog_slots.values():
        all_prog_slot_ids.update(_ids)

    # EXCLUDED shop slots are precomputed in `aomWorld.generate_early()` and
    # stored on `world.shop_excluded_ids` so `create_items` can use the exact
    # count when sizing the useful pool (EXCLUDED slots accept only
    # filler/trap, never useful).  Fall back to an empty set on older worlds.
    excluded_ids = set(getattr(world, "shop_excluded_ids", set()))

    for loc_id in ALL_SHOP_ITEM_IDS:
        name = location_id_to_name.get(loc_id)
        if not name:
            continue
        loc = multiworld.get_location(name, player)
        is_marsh = loc_id in marsh_item_ids
        # Marsh shop slots are never progression — skip the prog_slot exception
        is_prog_slot = (not is_marsh) and (loc_id in all_prog_slot_ids)
        if is_prog_slot:
            pass  # no restriction on non-Marsh progression slots
        elif loc_id in excluded_ids:
            loc.progress_type = LocationProgressType.EXCLUDED  # filled with filler/trap
        elif is_marsh:
            # Marsh shop: useful/filler/trap but never progression
            loc.item_rule = lambda item: item.classification in (
                ItemClassification.filler, ItemClassification.useful, ItemClassification.trap
            )
        elif loc_id in filler_only:
            # progress_type=EXCLUDED tells AP's fill to prefer filler items
            # here before placing them in unrestricted slots, which prevents
            # filler from crowding out useful items in useful-capable slots.
            # item_rule still hard-enforces filler/trap only.
            loc.progress_type = LocationProgressType.EXCLUDED
            loc.item_rule = lambda item: item.classification in (
                ItemClassification.filler, ItemClassification.trap
            )
        else:
            loc.item_rule = lambda item: item.classification in (
                ItemClassification.filler, ItemClassification.useful, ItemClassification.trap
            )

    # Shop E item rules are no longer set here — the 48 card locations are
    # fully force-placed via `place_shop_e_items` so AP's fill never sees them.

def place_shop_e_items(world) -> None:
    """Force-place the 48 Shop E card items onto their locations.

    Items are pre-reserved in `world.shop_e_forced_items` (set by create_items)
    from the existing useful / filler pools.  Placing them via
    `place_locked_item` keeps the locations out of AP's main fill, which
    avoids the 48 EXCLUDED slots crowding out progression placement on
    item-pool-heavy YAMLs.
    """
    if not getattr(world, "shop_e_enabled", False):
        return
    forced = getattr(world, "shop_e_forced_items", None) or {}
    if not forced:
        return
    player     = world.player
    multiworld = world.multiworld
    for loc_id, item_name in forced.items():
        name = location_id_to_name.get(loc_id)
        if not name:
            continue
        try:
            loc = multiworld.get_location(name, player)
        except KeyError:
            continue
        if loc.item is not None:
            continue
        item = world.create_item(item_name)
        loc.place_locked_item(item)

def set_rules(world) -> None:
    """Top-level entry point — Archipelago calls this after create_regions /
    create_items.  Order matters:

      1. build_point_table     — once, used by every scenario rule below.
      2. exclude_scenario_32   — must run before any rule walks FOTT_32 locations.
      3. place_completion_events / place_gems / place_progressive_shop_info
         — forced placements; must run before AP's main fill so those slots
         are reserved.
      4. set_section_rules     — Menu→section gates.
      5. set_scenario_age_and_point_rules — section→scenario gates.
      6. set_item_placement_restrictions — forbid section-unlock items inside
         their own sections.
      7. set_shop_rules        — only meaningful when gem_shop is on.
    """
    point_table = build_point_table()
    exclude_scenario_32_locations(world)
    place_completion_events(world)
    place_gems(world)
    place_progressive_shop_info(world)
    place_shop_e_items(world)
    set_section_rules(world)
    set_scenario_age_and_point_rules(world, point_table)
    set_scenario_key_rules(world)
    set_item_placement_restrictions(world)
    set_shop_rules(world)
    set_completion_rule(world)


# --------------------------------------------------
# Scenario key / key ring rules (max_keys_on_keyrings)
# --------------------------------------------------

def set_scenario_key_rules(world) -> None:
    """When `max_keys_on_keyrings > 0`, layer a per-scenario unlock requirement
    on top of the existing section→scenario entrance rules.

    Dispatch:
      * max == 1: each scenario is gated on its own Scenario Key item
        (`world.scenario_to_key_id` maps global_number → key item id).
      * max >= 2: each scenario is gated on the Key Ring item that carries
        its key (`world.scenario_to_ring_item_id` maps global_number → ring
        item id).
    """
    mk = int(getattr(world, "max_keys_on_keyrings", 0))
    if mk <= 0:
        return

    from ..items.Items import ID_TO_ITEM
    player    = world.player
    multiworld = world.multiworld
    disabled_campaigns = getattr(world, "disabled_campaigns", set())

    section_names = {
        "FOTT_GREEK":    "Fall of the Trident: Greek",
        "FOTT_EGYPTIAN": "Fall of the Trident: Egyptian",
        "FOTT_NORSE":    "Fall of the Trident: Norse",
        "FOTT_FINAL":    "Fall of the Trident: Final",
        "NEW_ATLANTIS":  "The New Atlantis",
        "GOLDEN_GIFT":   "The Golden Gift",
    }

    if mk == 1:
        scenario_to_item_id: dict[int, int] = (
            getattr(world, "scenario_to_key_id", {}) or {}
        )
    else:
        scenario_to_item_id = (
            getattr(world, "scenario_to_ring_item_id", {}) or {}
        )

    for scenario in aomScenarioData:
        if scenario.campaign in disabled_campaigns:
            continue
        n   = scenario.global_number
        iid = scenario_to_item_id.get(n)
        if iid is None:
            continue
        item = ID_TO_ITEM.get(iid)
        if item is None:
            continue
        gate_name = item.item_name
        section   = section_names.get(scenario.campaign.name)
        if section is None:
            continue
        ent = multiworld.get_entrance(entrance_name(section, scenario.region_name), player)
        add_rule(ent, lambda state, name=gate_name: state.has(name, player))