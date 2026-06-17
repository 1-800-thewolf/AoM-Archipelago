# =============================================================================
# Age of Mythology Retold — Location catalog
# =============================================================================
#
# Every check in the AoMR randomizer is enumerated as a member of
# `aomLocationData` (or one of the per-shop enums lower in this file).
#
# Concepts:
#   * Location TYPES (`aomLocationType`):
#       VICTORY    — the visible "you beat the scenario" check (gets a real
#                    AP item).  Holds Gem when gem_shop is on.
#       COMPLETION — invisible AP-event check; never has a real address.
#                    Rules.py places a locked event item on it, gating
#                    reachability for downstream rules.
#       OBJECTIVE  — optional bonus checks within a scenario (collectibles,
#                    side objectives) reported by the running game via
#                    `APLocationCheck` events.
#       RELIC      — relicsanity locations, only generated when the
#                    `relicsanity` YAML option is on.  Each relic placed
#                    in any P1 temple sends a check.
#
#   * Location IDs:
#       global_location_id(scenario_id, local_id) = BASE_ID + scenario_id*100 + local_id
#       — `scenario_id` is the packed `campaign*100+chapter` value from
#         `aomScenarioData`, NOT the APScenarioID.  This collision-proof
#         packing reserves 100 slots per scenario.
#       — Adding a new location: pick the next free local_id within the
#         scenario's 100-slot block.
#       — `BASE_ID` is the global AP offset (see items/Items.py).
#
#   * Shop locations (gem_shop):
#       Tier-prefixed enums (A_*, B_*, C_*, D_*) plus PROGRESSIVE_INFO_IDS
#       and ALL_SHOP_ITEM_IDS provide named slots for the shop scenario.
#       Their IDs are hand-picked outside the per-scenario blocks and live
#       at the bottom of this file.
#
# Adding a new location:
#   1. Add an `aomLocationData` member with `(global_location_id(...), name,
#      scenario, type)`.
#   2. The lookup tables at the bottom of this file (`location_id_to_name`,
#      `REGION_TO_LOCATIONS`, `location_name_to_id`) auto-populate from
#      iteration over `aomLocationData`.
#   3. If the location requires special rules (e.g. only reachable with a
#      particular item), add an `add_rule` call in `rules/Rules.py`.
#   4. The running game (archipelago.xs) needs to send the matching
#      location id via `APLocationCheck` when the in-game trigger fires.
# =============================================================================

import enum

from .Scenarios import aomScenarioData
from ..items.Items import BASE_ID


class aomLocationType(enum.Flag):
    """Kind-of-check categorization, used to drive Region wiring (Regions.py
    skips RELIC locations when relicsanity is off) and forced placements
    (Rules.py keys on VICTORY for gems and on COMPLETION for event items)."""
    VICTORY    = enum.auto()
    COMPLETION = enum.auto()
    OBJECTIVE  = enum.auto()
    RELIC      = enum.auto()
    OPTIONAL_OBJECTIVE = enum.auto()


def global_location_id(scenario_id: int, local_location_id: int) -> int:
    """Compose the globally-unique AP location id for a scenario-local check.

    Args:
        scenario_id:       `aomScenarioData.id` — campaign*100 + chapter.
                           NOTE this is NOT the APScenarioID the running game
                           uses (which is `global_number`).  We use the
                           packed id here because it is collision-proof
                           across campaigns even though APScenarioIDs jump
                           ranges (1-32, 501-512, 601-604).
        local_location_id: 0..99 unique-per-scenario index.  Convention:
                           0 = VICTORY, 1 = COMPLETION, 2..N = objectives /
                           relics in any order.

    The 100-slot per-scenario stride must be honored when adding new
    locations; collisions silently alias inside the IntEnum and remove the
    later member from the world.
    """
    return BASE_ID + scenario_id * 100 + local_location_id


class aomLocationData(enum.IntEnum):
    """Catalog of every check.  See module-level header for the ID scheme.

    Member tuple is `(global_id, display_name, scenario, type)`.  The
    location's full label exposed to the multiworld is
    `<scenario_display_name>: <location_name>` (see `global_name` below).
    """
    def __new__(cls, id: int, *args, **kwargs):
        """IntEnum constructor — uses the precomputed `global_id` as the
        member's int value so direct integer comparison works."""
        value = id
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    def __init__(
        self,
        id: int,
        location_name: str,
        scenario: aomScenarioData,
        type: aomLocationType,
    ) -> None:
        """Args:
            id:            global location id (output of `global_location_id`).
            location_name: short label (e.g. "Victory", "Relic 1").
            scenario:      parent scenario; required for region wiring.
            type:          `aomLocationType` flag.
        """
        self.id = id
        self.location_name = location_name
        self.scenario = scenario
        self.type = type

    def global_name(self) -> str:
        """Globally-unique display string used as the AP `Location` name.
        Format: "<scenario display name>: <location_name>".  Rules.py
        looks locations up via this string when applying access rules."""
        return f"{self.scenario.display_name}: {self.location_name}"

    # FOTT 1
    FOTT_1_VICTORY = (
        global_location_id(aomScenarioData.FOTT_1.id, 0),
        "Victory",
        aomScenarioData.FOTT_1,
        aomLocationType.VICTORY,
    )
    FOTT_1_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_1.id, 1),
        "Completion",
        aomScenarioData.FOTT_1,
        aomLocationType.COMPLETION,
    )

    # FOTT 2
    FOTT_2_VICTORY = (
        global_location_id(aomScenarioData.FOTT_2.id, 0),
        "Victory",
        aomScenarioData.FOTT_2,
        aomLocationType.VICTORY,
    )
    FOTT_2_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_2.id, 1),
        "Completion",
        aomScenarioData.FOTT_2,
        aomLocationType.COMPLETION,
    )

    # FOTT 3
    FOTT_3_VICTORY = (
        global_location_id(aomScenarioData.FOTT_3.id, 0),
        "Victory",
        aomScenarioData.FOTT_3,
        aomLocationType.VICTORY,
    )
    FOTT_3_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_3.id, 1),
        "Completion",
        aomScenarioData.FOTT_3,
        aomLocationType.COMPLETION,
    )

    # FOTT 4
    FOTT_4_VICTORY = (
        global_location_id(aomScenarioData.FOTT_4.id, 0),
        "Victory",
        aomScenarioData.FOTT_4,
        aomLocationType.VICTORY,
    )
    FOTT_4_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_4.id, 1),
        "Completion",
        aomScenarioData.FOTT_4,
        aomLocationType.COMPLETION,
    )

    # FOTT 5
    FOTT_5_VICTORY = (
        global_location_id(aomScenarioData.FOTT_5.id, 0),
        "Victory",
        aomScenarioData.FOTT_5,
        aomLocationType.VICTORY,
    )
    FOTT_5_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_5.id, 1),
        "Completion",
        aomScenarioData.FOTT_5,
        aomLocationType.COMPLETION,
    )

    # FOTT 6
    FOTT_6_VICTORY = (
        global_location_id(aomScenarioData.FOTT_6.id, 0),
        "Victory",
        aomScenarioData.FOTT_6,
        aomLocationType.VICTORY,
    )
    FOTT_6_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_6.id, 1),
        "Completion",
        aomScenarioData.FOTT_6,
        aomLocationType.COMPLETION,
    )

    # FOTT 7
    FOTT_7_VICTORY = (
        global_location_id(aomScenarioData.FOTT_7.id, 0),
        "Victory",
        aomScenarioData.FOTT_7,
        aomLocationType.VICTORY,
    )
    FOTT_7_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_7.id, 1),
        "Completion",
        aomScenarioData.FOTT_7,
        aomLocationType.COMPLETION,
    )

    # FOTT 8
    FOTT_8_VICTORY = (
        global_location_id(aomScenarioData.FOTT_8.id, 0),
        "Victory",
        aomScenarioData.FOTT_8,
        aomLocationType.VICTORY,
    )
    FOTT_8_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_8.id, 1),
        "Completion",
        aomScenarioData.FOTT_8,
        aomLocationType.COMPLETION,
    )

    # FOTT 9
    FOTT_9_VICTORY = (
        global_location_id(aomScenarioData.FOTT_9.id, 0),
        "Victory",
        aomScenarioData.FOTT_9,
        aomLocationType.VICTORY,
    )
    FOTT_9_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_9.id, 1),
        "Completion",
        aomScenarioData.FOTT_9,
        aomLocationType.COMPLETION,
    )

    # FOTT 10
    FOTT_10_VICTORY = (
        global_location_id(aomScenarioData.FOTT_10.id, 0),
        "Victory",
        aomScenarioData.FOTT_10,
        aomLocationType.VICTORY,
    )
    FOTT_10_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_10.id, 1),
        "Completion",
        aomScenarioData.FOTT_10,
        aomLocationType.COMPLETION,
    )

    # FOTT 11
    FOTT_11_VICTORY = (
        global_location_id(aomScenarioData.FOTT_11.id, 0),
        "Victory",
        aomScenarioData.FOTT_11,
        aomLocationType.VICTORY,
    )
    FOTT_11_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_11.id, 1),
        "Completion",
        aomScenarioData.FOTT_11,
        aomLocationType.COMPLETION,
    )

    # FOTT 12
    FOTT_12_VICTORY = (
        global_location_id(aomScenarioData.FOTT_12.id, 0),
        "Victory",
        aomScenarioData.FOTT_12,
        aomLocationType.VICTORY,
    )
    FOTT_12_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_12.id, 1),
        "Completion",
        aomScenarioData.FOTT_12,
        aomLocationType.COMPLETION,
    )

    # FOTT 13
    FOTT_13_VICTORY = (
        global_location_id(aomScenarioData.FOTT_13.id, 0),
        "Victory",
        aomScenarioData.FOTT_13,
        aomLocationType.VICTORY,
    )
    FOTT_13_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_13.id, 1),
        "Completion",
        aomScenarioData.FOTT_13,
        aomLocationType.COMPLETION,
    )

    # FOTT 14
    FOTT_14_VICTORY = (
        global_location_id(aomScenarioData.FOTT_14.id, 0),
        "Victory",
        aomScenarioData.FOTT_14,
        aomLocationType.VICTORY,
    )
    FOTT_14_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_14.id, 1),
        "Completion",
        aomScenarioData.FOTT_14,
        aomLocationType.COMPLETION,
    )

    # FOTT 15
    FOTT_15_VICTORY = (
        global_location_id(aomScenarioData.FOTT_15.id, 0),
        "Victory",
        aomScenarioData.FOTT_15,
        aomLocationType.VICTORY,
    )
    FOTT_15_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_15.id, 1),
        "Completion",
        aomScenarioData.FOTT_15,
        aomLocationType.COMPLETION,
    )

    # FOTT 16
    FOTT_16_VICTORY = (
        global_location_id(aomScenarioData.FOTT_16.id, 0),
        "Victory",
        aomScenarioData.FOTT_16,
        aomLocationType.VICTORY,
    )
    FOTT_16_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_16.id, 1),
        "Completion",
        aomScenarioData.FOTT_16,
        aomLocationType.COMPLETION,
    )

    # FOTT 17
    FOTT_17_VICTORY = (
        global_location_id(aomScenarioData.FOTT_17.id, 0),
        "Victory",
        aomScenarioData.FOTT_17,
        aomLocationType.VICTORY,
    )
    FOTT_17_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_17.id, 1),
        "Completion",
        aomScenarioData.FOTT_17,
        aomLocationType.COMPLETION,
    )

    # FOTT 18
    FOTT_18_VICTORY = (
        global_location_id(aomScenarioData.FOTT_18.id, 0),
        "Victory",
        aomScenarioData.FOTT_18,
        aomLocationType.VICTORY,
    )
    FOTT_18_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_18.id, 1),
        "Completion",
        aomScenarioData.FOTT_18,
        aomLocationType.COMPLETION,
    )

    # FOTT 19
    FOTT_19_VICTORY = (
        global_location_id(aomScenarioData.FOTT_19.id, 0),
        "Victory",
        aomScenarioData.FOTT_19,
        aomLocationType.VICTORY,
    )
    FOTT_19_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_19.id, 1),
        "Completion",
        aomScenarioData.FOTT_19,
        aomLocationType.COMPLETION,
    )

    # FOTT 20
    FOTT_20_VICTORY = (
        global_location_id(aomScenarioData.FOTT_20.id, 0),
        "Victory",
        aomScenarioData.FOTT_20,
        aomLocationType.VICTORY,
    )
    FOTT_20_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_20.id, 1),
        "Completion",
        aomScenarioData.FOTT_20,
        aomLocationType.COMPLETION,
    )

    # FOTT 21
    FOTT_21_VICTORY = (
        global_location_id(aomScenarioData.FOTT_21.id, 0),
        "Victory",
        aomScenarioData.FOTT_21,
        aomLocationType.VICTORY,
    )
    FOTT_21_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_21.id, 1),
        "Completion",
        aomScenarioData.FOTT_21,
        aomLocationType.COMPLETION,
    )

    # FOTT 22
    FOTT_22_VICTORY = (
        global_location_id(aomScenarioData.FOTT_22.id, 0),
        "Victory",
        aomScenarioData.FOTT_22,
        aomLocationType.VICTORY,
    )
    FOTT_22_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_22.id, 1),
        "Completion",
        aomScenarioData.FOTT_22,
        aomLocationType.COMPLETION,
    )

    # FOTT 23
    FOTT_23_VICTORY = (
        global_location_id(aomScenarioData.FOTT_23.id, 0),
        "Victory",
        aomScenarioData.FOTT_23,
        aomLocationType.VICTORY,
    )
    FOTT_23_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_23.id, 1),
        "Completion",
        aomScenarioData.FOTT_23,
        aomLocationType.COMPLETION,
    )

    # FOTT 24
    FOTT_24_VICTORY = (
        global_location_id(aomScenarioData.FOTT_24.id, 0),
        "Victory",
        aomScenarioData.FOTT_24,
        aomLocationType.VICTORY,
    )
    FOTT_24_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_24.id, 1),
        "Completion",
        aomScenarioData.FOTT_24,
        aomLocationType.COMPLETION,
    )

    # FOTT 25
    FOTT_25_VICTORY = (
        global_location_id(aomScenarioData.FOTT_25.id, 0),
        "Victory",
        aomScenarioData.FOTT_25,
        aomLocationType.VICTORY,
    )
    FOTT_25_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_25.id, 1),
        "Completion",
        aomScenarioData.FOTT_25,
        aomLocationType.COMPLETION,
    )

    # FOTT 26
    FOTT_26_VICTORY = (
        global_location_id(aomScenarioData.FOTT_26.id, 0),
        "Victory",
        aomScenarioData.FOTT_26,
        aomLocationType.VICTORY,
    )
    FOTT_26_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_26.id, 1),
        "Completion",
        aomScenarioData.FOTT_26,
        aomLocationType.COMPLETION,
    )

    # FOTT 27
    FOTT_27_VICTORY = (
        global_location_id(aomScenarioData.FOTT_27.id, 0),
        "Victory",
        aomScenarioData.FOTT_27,
        aomLocationType.VICTORY,
    )
    FOTT_27_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_27.id, 1),
        "Completion",
        aomScenarioData.FOTT_27,
        aomLocationType.COMPLETION,
    )

    # FOTT 28
    FOTT_28_VICTORY = (
        global_location_id(aomScenarioData.FOTT_28.id, 0),
        "Victory",
        aomScenarioData.FOTT_28,
        aomLocationType.VICTORY,
    )
    FOTT_28_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_28.id, 1),
        "Completion",
        aomScenarioData.FOTT_28,
        aomLocationType.COMPLETION,
    )

    # FOTT 29
    FOTT_29_VICTORY = (
        global_location_id(aomScenarioData.FOTT_29.id, 0),
        "Victory",
        aomScenarioData.FOTT_29,
        aomLocationType.VICTORY,
    )
    FOTT_29_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_29.id, 1),
        "Completion",
        aomScenarioData.FOTT_29,
        aomLocationType.COMPLETION,
    )

    # FOTT 30
    FOTT_30_VICTORY = (
        global_location_id(aomScenarioData.FOTT_30.id, 0),
        "Victory",
        aomScenarioData.FOTT_30,
        aomLocationType.VICTORY,
    )
    FOTT_30_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_30.id, 1),
        "Completion",
        aomScenarioData.FOTT_30,
        aomLocationType.COMPLETION,
    )

    # FOTT 31
    FOTT_31_VICTORY = (
        global_location_id(aomScenarioData.FOTT_31.id, 0),
        "Victory",
        aomScenarioData.FOTT_31,
        aomLocationType.VICTORY,
    )
    FOTT_31_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_31.id, 1),
        "Completion",
        aomScenarioData.FOTT_31,
        aomLocationType.COMPLETION,
    )

    # FOTT 32
    FOTT_32_VICTORY = (
        global_location_id(aomScenarioData.FOTT_32.id, 0),
        "Victory",
        aomScenarioData.FOTT_32,
        aomLocationType.VICTORY,
    )
    FOTT_32_COMPLETION = (
        global_location_id(aomScenarioData.FOTT_32.id, 1),
        "Completion",
        aomScenarioData.FOTT_32,
        aomLocationType.COMPLETION,
    )

    # -----------------------------------------------------------------------
    # Objective locations (local_id = 2+) — one per primary objective
    # -----------------------------------------------------------------------

    # FOTT 1: 1. Omens
    FOTT_1_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_1.id, 2),
        "Kill the Kraken.",
        aomScenarioData.FOTT_1,
        aomLocationType.OBJECTIVE,
    )
    FOTT_1_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_1.id, 3),
        "Train reinforcements to defend the harbor.",
        aomScenarioData.FOTT_1,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 2: 2. Consequences
    FOTT_2_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_2.id, 2),
        "Advance to the Classical Age.",
        aomScenarioData.FOTT_2,
        aomLocationType.OBJECTIVE,
    )
    FOTT_2_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_2.id, 3),
        "Gather 400 Food",
        aomScenarioData.FOTT_2,
        aomLocationType.OBJECTIVE,
    )
    FOTT_2_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_2.id, 4),
        "Build a House",
        aomScenarioData.FOTT_2,
        aomLocationType.OBJECTIVE,
    )
    FOTT_2_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_2.id, 5),
        "Build a Temple",
        aomScenarioData.FOTT_2,
        aomLocationType.OBJECTIVE,
    )
    FOTT_2_OBJ_5 = (
        global_location_id(aomScenarioData.FOTT_2.id, 6),
        "Destroy the pirate Town Center.",
        aomScenarioData.FOTT_2,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 3: 3. Scratching the Surface
    FOTT_3_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_3.id, 2),
        "Reach the unclaimed Settlement.",
        aomScenarioData.FOTT_3,
        aomLocationType.OBJECTIVE,
    )
    FOTT_3_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_3.id, 3),
        "Build a Town Center.",
        aomScenarioData.FOTT_3,
        aomLocationType.OBJECTIVE,
    )
    FOTT_3_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_3.id, 4),
        "Destroy the Trojan docks.",
        aomScenarioData.FOTT_3,
        aomLocationType.OBJECTIVE,
    )
    FOTT_3_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_3.id, 5),
        "Destroy the last Trojan dock.",
        aomScenarioData.FOTT_3,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 4: 4. A Fine Plan
    FOTT_4_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_4.id, 2),
        "Find and take a Gold Mine from the Trojans.",
        aomScenarioData.FOTT_4,
        aomLocationType.OBJECTIVE,
    )
    FOTT_4_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_4.id, 3),
        "Destroy the Trojan West Gate.",
        aomScenarioData.FOTT_4,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 5: 5. Just Enough Rope
    FOTT_5_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_5.id, 2),
        "Defeat the cavalry attacking Ajax.",
        aomScenarioData.FOTT_5,
        aomLocationType.OBJECTIVE,
    )
    FOTT_5_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_5.id, 3),
        "Reach Ajax's Town Center.",
        aomScenarioData.FOTT_5,
        aomLocationType.OBJECTIVE,
    )
    FOTT_5_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_5.id, 4),
        "Destroy all buildings in the Trojan forward base.",
        aomScenarioData.FOTT_5,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 6: 6. I Hope This Works
    FOTT_6_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_6.id, 2),
        "Accumulate 1000 Wood.",
        aomScenarioData.FOTT_6,
        aomLocationType.OBJECTIVE,
    )
    FOTT_6_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_6.id, 3),
        "Build the Trojan Horse.",
        aomScenarioData.FOTT_6,
        aomLocationType.OBJECTIVE,
    )
    FOTT_6_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_6.id, 4),
        "Destroy the Trojan gate.",
        aomScenarioData.FOTT_6,
        aomLocationType.OBJECTIVE,
    )
    FOTT_6_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_6.id, 5),
        "Destroy the three Fortresses within Troy's walls.",
        aomScenarioData.FOTT_6,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 7: 7. More Bandits
    FOTT_7_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_7.id, 2),
        "Reach the prison area.",
        aomScenarioData.FOTT_7,
        aomLocationType.OBJECTIVE,
    )
    FOTT_7_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_7.id, 3),
        "Defeat the bandits guarding the prison.",
        aomScenarioData.FOTT_7,
        aomLocationType.OBJECTIVE,
    )
    FOTT_7_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_7.id, 4),
        "Destroy the enemy Watch Tower and Barracks.",
        aomScenarioData.FOTT_7,
        aomLocationType.OBJECTIVE,
    )
    FOTT_7_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_7.id, 5),
        "Destroy the enemy Watch Tower and Temple.",
        aomScenarioData.FOTT_7,
        aomLocationType.OBJECTIVE,
    )
    FOTT_7_OBJ_5 = (
        global_location_id(aomScenarioData.FOTT_7.id, 6),
        "Destroy the Migdol Stronghold.",
        aomScenarioData.FOTT_7,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 8: 8. Bad News
    FOTT_8_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_8.id, 2),
        "Fight your way to the mine.",
        aomScenarioData.FOTT_8,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 9: 9. Revelation
    FOTT_9_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_9.id, 2),
        "Destroy the ram before it breaks down the Gate.",
        aomScenarioData.FOTT_9,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 10: 10. Strangers
    FOTT_10_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_10.id, 2),
        "Seek the Shades.",
        aomScenarioData.FOTT_10,
        aomLocationType.OBJECTIVE,
    )
    FOTT_10_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_10.id, 3),
        "Scout forward with the Shades.",
        aomScenarioData.FOTT_10,
        aomLocationType.OBJECTIVE,
    )
    FOTT_10_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_10.id, 4),
        "Kill the Minotaur.",
        aomScenarioData.FOTT_10,
        aomLocationType.OBJECTIVE,
    )
    FOTT_10_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_10.id, 5),
        "Collect the three relics of Hades.",
        aomScenarioData.FOTT_10,
        aomLocationType.OBJECTIVE,
    )
    FOTT_10_OBJ_5 = (
        global_location_id(aomScenarioData.FOTT_10.id, 6),
        "Bring the three relics to the temple complex.",
        aomScenarioData.FOTT_10,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 11: 11. The Lost Relic
    FOTT_11_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_11.id, 2),
        "Dig out the artifact.",
        aomScenarioData.FOTT_11,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 12: 12. Light Sleeper
    FOTT_12_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_12.id, 2),
        "Kill the guards watching the Laborers.",
        aomScenarioData.FOTT_12,
        aomLocationType.OBJECTIVE,
    )
    FOTT_12_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_12.id, 3),
        "Bring at least five Villagers safely to their Town Center.",
        aomScenarioData.FOTT_12,
        aomLocationType.OBJECTIVE,
    )
    FOTT_12_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_12.id, 4),
        "Bring the Sword Bearer to the Guardian.",
        aomScenarioData.FOTT_12,
        aomLocationType.OBJECTIVE,
    )
    FOTT_12_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_12.id, 5),
        "Use the Guardian to destroy Kemsyt's army.",
        aomScenarioData.FOTT_12,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 13: 13. Tug of War
    FOTT_13_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_13.id, 2),
        "Move the Osiris Piece Cart into your city.",
        aomScenarioData.FOTT_13,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 14: 14. Isis, Hear My Plea.
    FOTT_14_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_14.id, 2),
        "Destroy Gargarensis' Migdol Stronghold.",
        aomScenarioData.FOTT_14,
        aomLocationType.OBJECTIVE,
    )
    FOTT_14_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_14.id, 3),
        "Amanra must reach the Transport Ship.",
        aomScenarioData.FOTT_14,
        aomLocationType.OBJECTIVE,
    )
    FOTT_14_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_14.id, 4),
        "Bring Amanra to the Abydos harbor.",
        aomScenarioData.FOTT_14,
        aomLocationType.OBJECTIVE,
    )
    FOTT_14_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_14.id, 5),
        "Break Amanra into the prison.",
        aomScenarioData.FOTT_14,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 15: 15. Let's Go
    FOTT_15_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_15.id, 2),
        "Survive until Setna's transports arrive from the southwest.",
        aomScenarioData.FOTT_15,
        aomLocationType.OBJECTIVE,
    )
    FOTT_15_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_15.id, 3),
        "Move your troops to the allied purple town.",
        aomScenarioData.FOTT_15,
        aomLocationType.OBJECTIVE,
    )
    FOTT_15_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_15.id, 4),
        "Capture the Osiris Piece Cart and move it outside the city's south gate.",
        aomScenarioData.FOTT_15,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 16: 16. Good Advice
    FOTT_16_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_16.id, 2),
        "Follow Kastor.",
        aomScenarioData.FOTT_16,
        aomLocationType.OBJECTIVE,
    )
    FOTT_16_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_16.id, 3),
        "Garrison the Relic into the Temple, and defend the Temple.",
        aomScenarioData.FOTT_16,
        aomLocationType.OBJECTIVE,
    )
    FOTT_16_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_16.id, 4),
        "Defeat the guardians of the Shrine.",
        aomScenarioData.FOTT_16,
        aomLocationType.OBJECTIVE,
    )
    FOTT_16_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_16.id, 5),
        "Destroy the large boulder.",
        aomScenarioData.FOTT_16,
        aomLocationType.OBJECTIVE,
    )
    FOTT_16_OBJ_5 = (
        global_location_id(aomScenarioData.FOTT_16.id, 6),
        "Transport Arkantos and Kastor to the white flag beach.",
        aomScenarioData.FOTT_16,
        aomLocationType.OBJECTIVE,
    )
    FOTT_16_OBJ_6 = (
        global_location_id(aomScenarioData.FOTT_16.id, 7),
        "Destroy the enemy wonder.",
        aomScenarioData.FOTT_16,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 17: 17. The Jackal's Stronghold
    FOTT_17_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_17.id, 2),
        "Bring Amanra to the village.",
        aomScenarioData.FOTT_17,
        aomLocationType.OBJECTIVE,
    )
    FOTT_17_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_17.id, 3),
        "Bring Amanra to the Osiris Piece Box.",
        aomScenarioData.FOTT_17,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 18: 18. A Long Way From Home
    FOTT_18_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_18.id, 2),
        "Reach the desert nomad camp.",
        aomScenarioData.FOTT_18,
        aomLocationType.OBJECTIVE,
    )
    FOTT_18_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_18.id, 3),
        "Recover the head of Osiris from the Tamarisk tree.",
        aomScenarioData.FOTT_18,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 19: 19. Watch That First Step
    FOTT_19_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_19.id, 2),
        "Destroy the forward base to capture the Black Sails.",
        aomScenarioData.FOTT_19,
        aomLocationType.OBJECTIVE,
    )
    FOTT_19_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_19.id, 3),
        "Claim a Settlement.",
        aomScenarioData.FOTT_19,
        aomLocationType.OBJECTIVE,
    )
    FOTT_19_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_19.id, 4),
        "Siege Kamos' base.",
        aomScenarioData.FOTT_19,
        aomLocationType.OBJECTIVE,
    )
    FOTT_19_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_19.id, 5),
        "Eliminate Kamos' guards and defeat him.",
        aomScenarioData.FOTT_19,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 20: 20. Where They Belong
    FOTT_20_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_20.id, 2),
        "Survive until Arkantos arrives.",
        aomScenarioData.FOTT_20,
        aomLocationType.OBJECTIVE,
    )
    FOTT_20_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_20.id, 3),
        "Bring all four Osiris pieces to the Obelisk.",
        aomScenarioData.FOTT_20,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 21: 21. Old Friends
    FOTT_21_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_21.id, 2),
        "Save the pigs from being slaughtered.",
        aomScenarioData.FOTT_21,
        aomLocationType.OBJECTIVE,
    )
    FOTT_21_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_21.id, 3),
        "Bring the Boars and Pigs past the gates to the Temple of Zeus.",
        aomScenarioData.FOTT_21,
        aomLocationType.OBJECTIVE,
    )
    FOTT_21_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_21.id, 4),
        "Destroy Circe's Fortress.",
        aomScenarioData.FOTT_21,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 22: 22. North
    FOTT_22_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_22.id, 2),
        "Claim a Settlement.",
        aomScenarioData.FOTT_22,
        aomLocationType.OBJECTIVE,
    )
    FOTT_22_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_22.id, 3),
        "Destroy all three enemy Temples.",
        aomScenarioData.FOTT_22,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 23: 23. The Dwarven Forge
    FOTT_23_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_23.id, 2),
        "Build a Town Center.",
        aomScenarioData.FOTT_23,
        aomLocationType.OBJECTIVE,
    )
    FOTT_23_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_23.id, 3),
        "Eliminate the Giants and Trolls near the Dwarven Forge.",
        aomScenarioData.FOTT_23,
        aomLocationType.OBJECTIVE,
    )
    FOTT_23_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_23.id, 4),
        "Defend the Dwarven Forge until the Giants retreat!",
        aomScenarioData.FOTT_23,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 24: 24. Not From Around Here
    FOTT_24_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_24.id, 2),
        "Protect Skult and the Folstag Flag Bearer.",
        aomScenarioData.FOTT_24,
        aomLocationType.OBJECTIVE,
    )
    FOTT_24_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_24.id, 3),
        "Bring Skult and the Flag Bearer to the far north.",
        aomScenarioData.FOTT_24,
        aomLocationType.OBJECTIVE,
    )
    FOTT_24_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_24.id, 4),
        "Advance to the Heroic Age.",
        aomScenarioData.FOTT_24,
        aomLocationType.OBJECTIVE,
    )
    FOTT_24_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_24.id, 5),
        "Break through the boulder wall.",
        aomScenarioData.FOTT_24,
        aomLocationType.OBJECTIVE,
    )
    FOTT_24_OBJ_5 = (
        global_location_id(aomScenarioData.FOTT_24.id, 6),
        "Move Skult and the Flag Bearer to the north end of the pass.",
        aomScenarioData.FOTT_24,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 25: 25. Welcoming Committee
    FOTT_25_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_25.id, 2),
        "Protect Skult and the Folstag Flag Bearer.",
        aomScenarioData.FOTT_25,
        aomLocationType.OBJECTIVE,
    )
    FOTT_25_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_25.id, 3),
        "Eliminate all three clan leaders.",
        aomScenarioData.FOTT_25,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 26: 26. Union
    FOTT_26_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_26.id, 2),
        "Follow the trail to the first Norse clan.",
        aomScenarioData.FOTT_26,
        aomLocationType.OBJECTIVE,
    )
    FOTT_26_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_26.id, 3),
        "Defeat the Trolls in the mines to the west.",
        aomScenarioData.FOTT_26,
        aomLocationType.OBJECTIVE,
    )
    FOTT_26_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_26.id, 4),
        "Exit the mines and find two more Norse clans.",
        aomScenarioData.FOTT_26,
        aomLocationType.OBJECTIVE,
    )
    FOTT_26_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_26.id, 5),
        "Build five towers near the flagged sites around Lothbrok's village.",
        aomScenarioData.FOTT_26,
        aomLocationType.OBJECTIVE,
    )
    FOTT_26_OBJ_5 = (
        global_location_id(aomScenarioData.FOTT_26.id, 6),
        "Destroy the Southern Watch Tower.",
        aomScenarioData.FOTT_26,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 27: 27. The Well of Urd
    FOTT_27_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_27.id, 2),
        "Destroy the gate to the Well of Urd.",
        aomScenarioData.FOTT_27,
        aomLocationType.OBJECTIVE,
    )
    FOTT_27_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_27.id, 3),
        "Defeat all myth units at the Well of Urd.",
        aomScenarioData.FOTT_27,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 28: 28. Beneath the Surface
    FOTT_28_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_28.id, 2),
        "Kill the Fire Giants guarding the ram.",
        aomScenarioData.FOTT_28,
        aomLocationType.OBJECTIVE,
    )
    FOTT_28_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_28.id, 3),
        "The Well of Urd must not be destroyed",
        aomScenarioData.FOTT_28,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 29: 29. Unlikely Heroes
    FOTT_29_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_29.id, 2),
        "Protect the Dwarves while they cut the hammer haft from the taproot.",
        aomScenarioData.FOTT_29,
        aomLocationType.OBJECTIVE,
    )
    FOTT_29_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_29.id, 3),
        "Bring the two pieces of Thor's hammer together.",
        aomScenarioData.FOTT_29,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 30: 30. All Is Not Lost
    FOTT_30_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_30.id, 2),
        "Build a Town Center in the abandoned mining town.",
        aomScenarioData.FOTT_30,
        aomLocationType.OBJECTIVE,
    )
    FOTT_30_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_30.id, 3),
        "Build up your defenses before Gargarensis attacks.",
        aomScenarioData.FOTT_30,
        aomLocationType.OBJECTIVE,
    )
    FOTT_30_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_30.id, 4),
        "Survive for 20 minutes until help arrives.",
        aomScenarioData.FOTT_30,
        aomLocationType.OBJECTIVE,
    )
    FOTT_30_OBJ_4 = (
        global_location_id(aomScenarioData.FOTT_30.id, 5),
        "Fight your way northward to Gargarensis.",
        aomScenarioData.FOTT_30,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 31: 31. Welcome Back
    FOTT_31_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_31.id, 2),
        "Claim a Settlement on Atlantis.",
        aomScenarioData.FOTT_31,
        aomLocationType.OBJECTIVE,
    )
    FOTT_31_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_31.id, 3),
        "Transport 15 Atlantean Prisoners to the flagged island.",
        aomScenarioData.FOTT_31,
        aomLocationType.OBJECTIVE,
    )

    # FOTT 32: 32. A Place in My Dreams
    FOTT_32_OBJ_1 = (
        global_location_id(aomScenarioData.FOTT_32.id, 2),
        "Advance to the Mythic Age and construct a Wonder.",
        aomScenarioData.FOTT_32,
        aomLocationType.OBJECTIVE,
    )
    FOTT_32_OBJ_2 = (
        global_location_id(aomScenarioData.FOTT_32.id, 3),
        "Use the Blessing of Zeus God Power on Arkantos.",
        aomScenarioData.FOTT_32,
        aomLocationType.OBJECTIVE,
    )
    FOTT_32_OBJ_3 = (
        global_location_id(aomScenarioData.FOTT_32.id, 4),
        "Defeat the Living Statue of Poseidon.",
        aomScenarioData.FOTT_32,
        aomLocationType.OBJECTIVE,
    )


    # ===========================================================================
    # THE NEW ATLANTIS (APScenarioIDs 501-512)
    # ===========================================================================

    # NA_1: A Lost People
    NA_1_VICTORY = (
        global_location_id(aomScenarioData.NA_1.id, 0),
        "Victory",
        aomScenarioData.NA_1,
        aomLocationType.VICTORY,
    )
    NA_1_COMPLETION = (
        global_location_id(aomScenarioData.NA_1.id, 1),
        "Completion",
        aomScenarioData.NA_1,
        aomLocationType.COMPLETION,
    )
    NA_1_OBJ_1 = (
        global_location_id(aomScenarioData.NA_1.id, 2),
        "Build an army of at least ten soldiers",
        aomScenarioData.NA_1,
        aomLocationType.OBJECTIVE,
    )
    NA_1_OBJ_2 = (
        global_location_id(aomScenarioData.NA_1.id, 3),
        "Find the Sky Passage",
        aomScenarioData.NA_1,
        aomLocationType.OBJECTIVE,
    )
    NA_1_OBJ_3 = (
        global_location_id(aomScenarioData.NA_1.id, 4),
        "Defeat the barbarians at the Sky Passage",
        aomScenarioData.NA_1,
        aomLocationType.OBJECTIVE,
    )
    NA_1_OBJ_4 = (
        global_location_id(aomScenarioData.NA_1.id, 5),
        "Garrison five Villagers into the Sky Passage",
        aomScenarioData.NA_1,
        aomLocationType.OBJECTIVE,
    )
    NA_1_OBJ_5 = (
        global_location_id(aomScenarioData.NA_1.id, 6),
        "Build a Town Center beyond the Sky Passage",
        aomScenarioData.NA_1,
        aomLocationType.OBJECTIVE,
    )

    # NA_2: Atlantis Reborn
    NA_2_VICTORY = (
        global_location_id(aomScenarioData.NA_2.id, 0),
        "Victory",
        aomScenarioData.NA_2,
        aomLocationType.VICTORY,
    )
    NA_2_COMPLETION = (
        global_location_id(aomScenarioData.NA_2.id, 1),
        "Completion",
        aomScenarioData.NA_2,
        aomLocationType.COMPLETION,
    )
    NA_2_OBJ_1 = (
        global_location_id(aomScenarioData.NA_2.id, 2),
        "Repair the Temples to Kronos and Oranos",
        aomScenarioData.NA_2,
        aomLocationType.OBJECTIVE,
    )
    NA_2_OBJ_2 = (
        global_location_id(aomScenarioData.NA_2.id, 3),
        "Advance to the Classical Age",
        aomScenarioData.NA_2,
        aomLocationType.OBJECTIVE,
    )
    NA_2_OBJ_3 = (
        global_location_id(aomScenarioData.NA_2.id, 4),
        "Destroy the Greek Town Center",
        aomScenarioData.NA_2,
        aomLocationType.OBJECTIVE,
    )

    # NA_3: Greetings From Greece
    NA_3_VICTORY = (
        global_location_id(aomScenarioData.NA_3.id, 0),
        "Victory",
        aomScenarioData.NA_3,
        aomLocationType.VICTORY,
    )
    NA_3_COMPLETION = (
        global_location_id(aomScenarioData.NA_3.id, 1),
        "Completion",
        aomScenarioData.NA_3,
        aomLocationType.COMPLETION,
    )
    NA_3_OBJ_1 = (
        global_location_id(aomScenarioData.NA_3.id, 2),
        "Kill General Melagius",
        aomScenarioData.NA_3,
        aomLocationType.OBJECTIVE,
    )

    # NA_4: Odin's Tower
    NA_4_VICTORY = (
        global_location_id(aomScenarioData.NA_4.id, 0),
        "Victory",
        aomScenarioData.NA_4,
        aomLocationType.VICTORY,
    )
    NA_4_COMPLETION = (
        global_location_id(aomScenarioData.NA_4.id, 1),
        "Completion",
        aomScenarioData.NA_4,
        aomLocationType.COMPLETION,
    )
    NA_4_OBJ_1 = (
        global_location_id(aomScenarioData.NA_4.id, 2),
        "Replace all Norse Temples with Your Temples",
        aomScenarioData.NA_4,
        aomLocationType.OBJECTIVE,
    )
    NA_4_OBJ_2 = (
        global_location_id(aomScenarioData.NA_4.id, 3),
        "Move Kastor close to Odin's Tower",
        aomScenarioData.NA_4,
        aomLocationType.OBJECTIVE,
    )
    NA_4_OBJ_3 = (
        global_location_id(aomScenarioData.NA_4.id, 4),
        "Deconstruct Odin's Wonder",
        aomScenarioData.NA_4,
        aomLocationType.OBJECTIVE,
    )

    # NA_5: The Ancient Relics
    NA_5_VICTORY = (
        global_location_id(aomScenarioData.NA_5.id, 0),
        "Victory",
        aomScenarioData.NA_5,
        aomLocationType.VICTORY,
    )
    NA_5_COMPLETION = (
        global_location_id(aomScenarioData.NA_5.id, 1),
        "Completion",
        aomScenarioData.NA_5,
        aomLocationType.COMPLETION,
    )
    NA_5_OBJ_1 = (
        global_location_id(aomScenarioData.NA_5.id, 2),
        "Garrison all four Relics into the Temple",
        aomScenarioData.NA_5,
        aomLocationType.OBJECTIVE,
    )
    NA_5_OBJ_2 = (
        global_location_id(aomScenarioData.NA_5.id, 3),
        "Protect Kronos Temple",
        aomScenarioData.NA_5,
        aomLocationType.OBJECTIVE,
    )

    # NA_6: Mount Olympus
    NA_6_VICTORY = (
        global_location_id(aomScenarioData.NA_6.id, 0),
        "Victory",
        aomScenarioData.NA_6,
        aomLocationType.VICTORY,
    )
    NA_6_COMPLETION = (
        global_location_id(aomScenarioData.NA_6.id, 1),
        "Completion",
        aomScenarioData.NA_6,
        aomLocationType.COMPLETION,
    )
    NA_6_OBJ_1 = (
        global_location_id(aomScenarioData.NA_6.id, 2),
        "Bring soldiers to the northern Temple",
        aomScenarioData.NA_6,
        aomLocationType.OBJECTIVE,
    )
    NA_6_OBJ_2 = (
        global_location_id(aomScenarioData.NA_6.id, 3),
        "Reach the flagged area to the east",
        aomScenarioData.NA_6,
        aomLocationType.OBJECTIVE,
    )
    NA_6_OBJ_3 = (
        global_location_id(aomScenarioData.NA_6.id, 4),
        "Bring Kastor to the peak of Olympus",
        aomScenarioData.NA_6,
        aomLocationType.OBJECTIVE,
    )
    NA_6_OBJ_4 = (
        global_location_id(aomScenarioData.NA_6.id, 5),
        "Protect the Underworld Passage",
        aomScenarioData.NA_6,
        aomLocationType.OBJECTIVE,
    )

    # NA_7: Betrayal at Sikyos
    NA_7_VICTORY = (
        global_location_id(aomScenarioData.NA_7.id, 0),
        "Victory",
        aomScenarioData.NA_7,
        aomLocationType.VICTORY,
    )
    NA_7_COMPLETION = (
        global_location_id(aomScenarioData.NA_7.id, 1),
        "Completion",
        aomScenarioData.NA_7,
        aomLocationType.COMPLETION,
    )
    NA_7_OBJ_1 = (
        global_location_id(aomScenarioData.NA_7.id, 2),
        "Survive the Titan's onslaught",
        aomScenarioData.NA_7,
        aomLocationType.OBJECTIVE,
    )
    NA_7_OBJ_2 = (
        global_location_id(aomScenarioData.NA_7.id, 3),
        "Send three Rocs to Kastor's Town Center",
        aomScenarioData.NA_7,
        aomLocationType.OBJECTIVE,
    )

    # NA_8: Cerberus
    NA_8_VICTORY = (
        global_location_id(aomScenarioData.NA_8.id, 0),
        "Victory",
        aomScenarioData.NA_8,
        aomLocationType.VICTORY,
    )
    NA_8_COMPLETION = (
        global_location_id(aomScenarioData.NA_8.id, 1),
        "Completion",
        aomScenarioData.NA_8,
        aomLocationType.COMPLETION,
    )
    NA_8_OBJ_1 = (
        global_location_id(aomScenarioData.NA_8.id, 2),
        "Protect the Son of Osiris while he recharges the Guardian",
        aomScenarioData.NA_8,
        aomLocationType.OBJECTIVE,
    )
    NA_8_OBJ_2 = (
        global_location_id(aomScenarioData.NA_8.id, 3),
        "Destroy Cerberus",
        aomScenarioData.NA_8,
        aomLocationType.OBJECTIVE,
    )

    # NA_9: Rampage
    NA_9_VICTORY = (
        global_location_id(aomScenarioData.NA_9.id, 0),
        "Victory",
        aomScenarioData.NA_9,
        aomLocationType.VICTORY,
    )
    NA_9_COMPLETION = (
        global_location_id(aomScenarioData.NA_9.id, 1),
        "Completion",
        aomScenarioData.NA_9,
        aomLocationType.COMPLETION,
    )
    NA_9_OBJ_1 = (
        global_location_id(aomScenarioData.NA_9.id, 2),
        "Construct a Town Center",
        aomScenarioData.NA_9,
        aomLocationType.OBJECTIVE,
    )
    NA_9_OBJ_2 = (
        global_location_id(aomScenarioData.NA_9.id, 3),
        "Kill Ymir",
        aomScenarioData.NA_9,
        aomLocationType.OBJECTIVE,
    )

    # NA_10: Making Amends
    NA_10_VICTORY = (
        global_location_id(aomScenarioData.NA_10.id, 0),
        "Victory",
        aomScenarioData.NA_10,
        aomLocationType.VICTORY,
    )
    NA_10_COMPLETION = (
        global_location_id(aomScenarioData.NA_10.id, 1),
        "Completion",
        aomScenarioData.NA_10,
        aomLocationType.COMPLETION,
    )
    NA_10_OBJ_1 = (
        global_location_id(aomScenarioData.NA_10.id, 2),
        "Build four Town Centers and spread Gaia's Lush",
        aomScenarioData.NA_10,
        aomLocationType.OBJECTIVE,
    )
    NA_10_OBJ_2 = (
        global_location_id(aomScenarioData.NA_10.id, 3),
        "Destroy Prometheus",
        aomScenarioData.NA_10,
        aomLocationType.OBJECTIVE,
    )

    # NA_11: Atlantis Betrayed
    NA_11_VICTORY = (
        global_location_id(aomScenarioData.NA_11.id, 0),
        "Victory",
        aomScenarioData.NA_11,
        aomLocationType.VICTORY,
    )
    NA_11_COMPLETION = (
        global_location_id(aomScenarioData.NA_11.id, 1),
        "Completion",
        aomScenarioData.NA_11,
        aomLocationType.COMPLETION,
    )
    NA_11_OBJ_1 = (
        global_location_id(aomScenarioData.NA_11.id, 2),
        "Destroy the Automatons attacking the South Atlanteans",
        aomScenarioData.NA_11,
        aomLocationType.OBJECTIVE,
    )
    NA_11_OBJ_2 = (
        global_location_id(aomScenarioData.NA_11.id, 3),
        "Destroy the Automatons attacking the West Atlanteans",
        aomScenarioData.NA_11,
        aomLocationType.OBJECTIVE,
    )
    NA_11_OBJ_3 = (
        global_location_id(aomScenarioData.NA_11.id, 4),
        "Destroy the Automatons attacking the North Atlanteans",
        aomScenarioData.NA_11,
        aomLocationType.OBJECTIVE,
    )
    NA_11_OBJ_4 = (
        global_location_id(aomScenarioData.NA_11.id, 5),
        "Garrison Kastor, Amanra, and Ajax in Krios' Sky Passage",
        aomScenarioData.NA_11,
        aomLocationType.OBJECTIVE,
    )

    # NA_12: War of the Titans
    NA_12_VICTORY = (
        global_location_id(aomScenarioData.NA_12.id, 0),
        "Victory",
        aomScenarioData.NA_12,
        aomLocationType.VICTORY,
    )
    NA_12_COMPLETION = (
        global_location_id(aomScenarioData.NA_12.id, 1),
        "Completion",
        aomScenarioData.NA_12,
        aomLocationType.COMPLETION,
    )
    NA_12_OBJ_1 = (
        global_location_id(aomScenarioData.NA_12.id, 2),
        "Invoke Seed of Gaia on all four Pools",
        aomScenarioData.NA_12,
        aomLocationType.OBJECTIVE,
    )
    NA_12_OBJ_2 = (
        global_location_id(aomScenarioData.NA_12.id, 3),
        "Protect a Summoning Tree until Gaia appears",
        aomScenarioData.NA_12,
        aomLocationType.OBJECTIVE,
    )
    NA_12_OBJ_3 = (
        global_location_id(aomScenarioData.NA_12.id, 4),
        "Use Gaia to defeat Kronos",
        aomScenarioData.NA_12,
        aomLocationType.OBJECTIVE,
    )

    # ===========================================================================
    # THE GOLDEN GIFT (APScenarioIDs 601-604)
    # ===========================================================================

    # GG_1: Brokk's Journey
    GG_1_VICTORY = (
        global_location_id(aomScenarioData.GG_1.id, 0),
        "Victory",
        aomScenarioData.GG_1,
        aomLocationType.VICTORY,
    )
    GG_1_COMPLETION = (
        global_location_id(aomScenarioData.GG_1.id, 1),
        "Completion",
        aomScenarioData.GG_1,
        aomLocationType.COMPLETION,
    )
    GG_1_OBJ_1 = (
        global_location_id(aomScenarioData.GG_1.id, 2),
        "Bring Brokk and four Ox Carts to the tunnel entrance",
        aomScenarioData.GG_1,
        aomLocationType.OBJECTIVE,
    )

    # GG_2: Eitri's Journey
    GG_2_VICTORY = (
        global_location_id(aomScenarioData.GG_2.id, 0),
        "Victory",
        aomScenarioData.GG_2,
        aomLocationType.VICTORY,
    )
    GG_2_COMPLETION = (
        global_location_id(aomScenarioData.GG_2.id, 1),
        "Completion",
        aomScenarioData.GG_2,
        aomLocationType.COMPLETION,
    )
    GG_2_OBJ_1 = (
        global_location_id(aomScenarioData.GG_2.id, 2),
        "Build a Dock",
        aomScenarioData.GG_2,
        aomLocationType.OBJECTIVE,
    )
    GG_2_OBJ_2 = (
        global_location_id(aomScenarioData.GG_2.id, 3),
        "Bring Eitri and six Villagers to the mine entrance",
        aomScenarioData.GG_2,
        aomLocationType.OBJECTIVE,
    )

    # GG_3: Fight at the Forge
    GG_3_VICTORY = (
        global_location_id(aomScenarioData.GG_3.id, 0),
        "Victory",
        aomScenarioData.GG_3,
        aomLocationType.VICTORY,
    )
    GG_3_COMPLETION = (
        global_location_id(aomScenarioData.GG_3.id, 1),
        "Completion",
        aomScenarioData.GG_3,
        aomLocationType.COMPLETION,
    )
    GG_3_OBJ_1 = (
        global_location_id(aomScenarioData.GG_3.id, 2),
        "Capture the Plenty Vault",
        aomScenarioData.GG_3,
        aomLocationType.OBJECTIVE,
    )
    GG_3_OBJ_2 = (
        global_location_id(aomScenarioData.GG_3.id, 3),
        "Hold the Dwarven Forge until the timer expires",
        aomScenarioData.GG_3,
        aomLocationType.OBJECTIVE,
    )

    # GG_4: Loki's Temples
    GG_4_VICTORY = (
        global_location_id(aomScenarioData.GG_4.id, 0),
        "Victory",
        aomScenarioData.GG_4,
        aomLocationType.VICTORY,
    )
    GG_4_COMPLETION = (
        global_location_id(aomScenarioData.GG_4.id, 1),
        "Completion",
        aomScenarioData.GG_4,
        aomLocationType.COMPLETION,
    )
    GG_4_OBJ_1 = (
        global_location_id(aomScenarioData.GG_4.id, 2),
        "Destroy Loki's Temple near your Town Center",
        aomScenarioData.GG_4,
        aomLocationType.OBJECTIVE,
    )
    GG_4_OBJ_2 = (
        global_location_id(aomScenarioData.GG_4.id, 3),
        "Bring Brokk and Eitri to the Battle Boar",
        aomScenarioData.GG_4,
        aomLocationType.OBJECTIVE,
    )

    # ===========================================================================
    # PILLARS OF THE GODS (APScenarioIDs 701-709)
    # ===========================================================================
    # POTG_1: Shennong's Chosen
    POTG_1_VICTORY = (
        global_location_id(aomScenarioData.POTG_1.id, 0),
        "Victory",
        aomScenarioData.POTG_1,
        aomLocationType.VICTORY,
    )
    POTG_1_COMPLETION = (
        global_location_id(aomScenarioData.POTG_1.id, 1),
        "Completion",
        aomScenarioData.POTG_1,
        aomLocationType.COMPLETION,
    )
    POTG_1_OBJ_1 = (
        global_location_id(aomScenarioData.POTG_1.id, 2),
        "Rescue the army",
        aomScenarioData.POTG_1,
        aomLocationType.OBJECTIVE,
    )
    POTG_1_OBJ_ = (
        global_location_id(aomScenarioData.POTG_1.id, 3),
        "Find the imprisoned hero",
        aomScenarioData.POTG_1,
        aomLocationType.OBJECTIVE,
    )
    POTG_1_OBJ_3 = (
        global_location_id(aomScenarioData.POTG_1.id, 4),
        "Kill the Taoties",
        aomScenarioData.POTG_1,
        aomLocationType.OBJECTIVE,
    )
    POTG_1_OBJ_4 = (
        global_location_id(aomScenarioData.POTG_1.id, 5),
        "Save allied soldiers",
        aomScenarioData.POTG_1,
        aomLocationType.OBJECTIVE,
    )
    POTG_1_OBJ_5 = (
        global_location_id(aomScenarioData.POTG_1.id, 6),
        "Use the Pioneer's lantern to discover what is behind the wall",
        aomScenarioData.POTG_1,
        aomLocationType.OBJECTIVE,
    )
    #POTG_2 - Houyi's Pride
    POTG_2_VICTORY = (
        global_location_id(aomScenarioData.POTG_2.id, 0),
        "Victory",
        aomScenarioData.POTG_2,
        aomLocationType.VICTORY,
    )
    POTG_2_COMPLETION = (
        global_location_id(aomScenarioData.POTG_2.id, 1),
        "Completion",
        aomScenarioData.POTG_2,
        aomLocationType.COMPLETION,
    )
    POTG_2_OBJ_1 = (
        global_location_id(aomScenarioData.POTG_2.id, 2),
        "Save the village",
        aomScenarioData.POTG_2,
        aomLocationType.OBJECTIVE,
    )
    POTG_2_OBJ_ = (
        global_location_id(aomScenarioData.POTG_2.id, 3),
        "Build up and defeat Huang Zhaowu's Army",
        aomScenarioData.POTG_2,
        aomLocationType.OBJECTIVE,
    )
    #POTG_3 - Stronger Together
    POTG_3_VICTORY = (
        global_location_id(aomScenarioData.POTG_3.id, 0),
        "Victory",
        aomScenarioData.POTG_3,
        aomLocationType.VICTORY,
    )
    POTG_3_COMPLETION = (
        global_location_id(aomScenarioData.POTG_3.id, 1),
        "Completion",
        aomScenarioData.POTG_3,
        aomLocationType.COMPLETION,
    )
    POTG_3_OBJ_1 = (
        global_location_id(aomScenarioData.POTG_3.id, 1),
        "Reach Nuchou.",
        aomScenarioData.POTG_3,
        aomLocationType.OBJECTIVE,
    )
    #POTG_4 - The God Trap
    POTG_4_VICTORY = (
        global_location_id(aomScenarioData.POTG_4.id, 0),
        "Victory",
        aomScenarioData.POTG_4,
        aomLocationType.VICTORY,
    )
    POTG_4_COMPLETION = (
        global_location_id(aomScenarioData.POTG_4.id, 1),
        "Completion",
        aomScenarioData.POTG_4,
        aomLocationType.COMPLETION,
    )
    POTG_4_OBJ_1 = (
        global_location_id(aomScenarioData.POTG_4.id, 1),
        "Find the ancient Temple.",
        aomScenarioData.POTG_4,
        aomLocationType.OBJECTIVE,
    )
    POTG_4_OBJ_2 = (
        global_location_id(aomScenarioData.POTG_4.id, 1),
        "Defeat Chiyou's army to reach the Northern Pillar.",
        aomScenarioData.POTG_4,
        aomLocationType.OBJECTIVE,
    )
    #POTG_5 - Overcoming Fixations
    POTG_5_VICTORY = (
        global_location_id(aomScenarioData.POTG_5.id, 0),
        "Victory",
        aomScenarioData.POTG_5,
        aomLocationType.VICTORY,
    )
    POTG_5_COMPLETION = (
        global_location_id(aomScenarioData.POTG_5.id, 1),
        "Completion",
        aomScenarioData.POTG_5,
        aomLocationType.COMPLETION,
    )
    POTG_5_OBJ_1 = (
        global_location_id(aomScenarioData.POTG_5.id, 1),
        "Protect the Southern Pillar.",
        aomScenarioData.POTG_5,
        aomLocationType.OBJECTIVE,
    )
    POTG_5_OBJ_2 = (
        global_location_id(aomScenarioData.POTG_5.id, 1),
        "Select a Settlement to Start the mission.",
        aomScenarioData.POTG_5,
        aomLocationType.OBJECTIVE,
    )
    POTG_5_OBJ_3 = (
        global_location_id(aomScenarioData.POTG_5.id, 1),
        "Destroy the Giant Siege Crossbows.",
        aomScenarioData.POTG_5,
        aomLocationType.OBJECTIVE,
    )
    POTG_5_OBJ_4 = (
        global_location_id(aomScenarioData.POTG_5.id, 1),
        "Defeat Nuchou.",
        aomScenarioData.POTG_5,
        aomLocationType.OBJECTIVE,
    )
    #POTG_6 - Reality's Collapse
    POTG_6_VICTORY = (
        global_location_id(aomScenarioData.POTG_6.id, 0),
        "Victory",
        aomScenarioData.POTG_6,
        aomLocationType.VICTORY,
    )
    POTG_6_COMPLETION = (
        global_location_id(aomScenarioData.POTG_6.id, 1),
        "Completion",
        aomScenarioData.POTG_6,
        aomLocationType.COMPLETION,
    )
    POTG_6_OBJ_1 = (
        global_location_id(aomScenarioData.POTG_6.id, 1),
        "Prevent Huang Zhaowu from destroying the pillar.",
        aomScenarioData.POTG_6,
        aomLocationType.OBJECTIVE,
    )
    POTG_6_OBJ_2 = (
        global_location_id(aomScenarioData.POTG_6.id, 1),
        "Bring Yan Feifeng to the Pillar before Huang Zhaowu destroys it.",
        aomScenarioData.POTG_6,
        aomLocationType.OBJECTIVE,
    )
    #POTG_7 - Shattered Underworlds
    POTG_7_VICTORY = (
        global_location_id(aomScenarioData.POTG_7.id, 0),
        "Victory",
        aomScenarioData.POTG_7,
        aomLocationType.VICTORY,
    )
    POTG_7_COMPLETION = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Completion",
        aomScenarioData.POTG_7,
        aomLocationType.COMPLETION,
    )
    POTG_7_OBJ_1 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Find the Red Stone (Greek).",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    POTG_7_OBJ_2 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Find the Black Stone (Atlantean).",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    POTG_7_OBJ_3 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Find the Blue Stone (Norse).",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    POTG_7_OBJ_4 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Find the Yellow Stone (Egyptian).",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    POTG_7_OBJ_5 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Find the White Stone (Chinese).",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    POTG_7_OBJ_6 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Defeat Xiaoli to retrieve the White Stone.",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    POTG_7_OBJ_7 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Protect the Mirror Tower to get the Black Stone.",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    POTG_7_OBJ_8 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Defeat Halogi to collect the Blue Stone.",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    POTG_7_OBJ_9 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Defeat the defenders of the enemy fortress to capture the Yellow Stone.",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    POTG_7_OBJ_10 = (
        global_location_id(aomScenarioData.POTG_7.id, 1),
        "Destroy statues to find the Red Stone.",
        aomScenarioData.POTG_7,
        aomLocationType.OBJECTIVE,
    )
    #POTG_8 - Divine Intervention
    POTG_8_VICTORY = (
        global_location_id(aomScenarioData.POTG_8.id, 0),
        "Victory",
        aomScenarioData.POTG_8,
        aomLocationType.VICTORY,
    )
    POTG_8_COMPLETION = (
        global_location_id(aomScenarioData.POTG_8.id, 1),
        "Completion",
        aomScenarioData.POTG_8,
        aomLocationType.COMPLETION,
    )
    POTG_8_OBJ_1 = (
        global_location_id(aomScenarioData.POTG_8.id, 1),
        "Request Nuwa's help by rebuilding her wonder.",
        aomScenarioData.POTG_8,
        aomLocationType.OBJECTIVE,
    )
    POTG_8_OBJ_2 = (
        global_location_id(aomScenarioData.POTG_8.id, 1),
        "Nuwa's Wonder must not be destroyed.",
        aomScenarioData.POTG_8,
        aomLocationType.OBJECTIVE,
    )
    #POTG_9 - Duel of the Deathless
    POTG_9_VICTORY = (
        global_location_id(aomScenarioData.POTG_9.id, 0),
        "Victory",
        aomScenarioData.POTG_9,
        aomLocationType.VICTORY,
    )
    POTG_9_COMPLETION = (
        global_location_id(aomScenarioData.POTG_9.id, 1),
        "Completion",
        aomScenarioData.POTG_9,
        aomLocationType.COMPLETION,
    )
    POTG_9_OBJ_1 = (
        global_location_id(aomScenarioData.POTG_9.id, 1),
        "Nuwa's Wonder must not be destroyed.",
        aomScenarioData.POTG_9,
        aomLocationType.OBJECTIVE,
    )
    POTG_9_OBJ_2 = (
        global_location_id(aomScenarioData.POTG_9.id, 1),
        "Empower the Titan Gate with Sages to summon Xingtian.",
        aomScenarioData.POTG_9,
        aomLocationType.OBJECTIVE,
    )
    POTG_9_OBJ_3 = (
        global_location_id(aomScenarioData.POTG_9.id, 1),
        "Defeat Chiyou.",
        aomScenarioData.POTG_9,
        aomLocationType.OBJECTIVE,
    )
    POTG_9_OBJ_4 = (
        global_location_id(aomScenarioData.POTG_9.id, 1),
        "Defeat Huang Zhaowu.",
        aomScenarioData.POTG_9,
        aomLocationType.OBJECTIVE,
    )
    # ===========================================================================
    # RELICSANITY — one location per garrisoned relic.
    # local_id starts at 10 to leave a buffer above the highest objective local_id.
    # 174 total: FoTT 103, New Atlantis 51, Golden Gift 20.
    # ===========================================================================

    # FOTT 3 relics
    FOTT_3_RELIC_1  = (global_location_id(aomScenarioData.FOTT_3.id, 10), "Relic 1: Near Stone Pillars at Camp", aomScenarioData.FOTT_3, aomLocationType.RELIC)
    FOTT_3_RELIC_2  = (global_location_id(aomScenarioData.FOTT_3.id, 11), "Relic 2: End of North Valley", aomScenarioData.FOTT_3, aomLocationType.RELIC)
    FOTT_3_RELIC_3  = (global_location_id(aomScenarioData.FOTT_3.id, 12), "Relic 3: End of North-East Beach", aomScenarioData.FOTT_3, aomLocationType.RELIC)

    # FOTT 4 relics
    FOTT_4_RELIC_1  = (global_location_id(aomScenarioData.FOTT_4.id, 10), "Relic 1: End of West Beach", aomScenarioData.FOTT_4, aomLocationType.RELIC)
    FOTT_4_RELIC_2  = (global_location_id(aomScenarioData.FOTT_4.id, 11), "Relic 2: North-West Shrine", aomScenarioData.FOTT_4, aomLocationType.RELIC)
    FOTT_4_RELIC_3  = (global_location_id(aomScenarioData.FOTT_4.id, 12), "Relic 3: Stone Pillars at the Valley", aomScenarioData.FOTT_4, aomLocationType.RELIC)
    FOTT_4_RELIC_4  = (global_location_id(aomScenarioData.FOTT_4.id, 13), "Relic 4: Shrine at Pink Enemy Base", aomScenarioData.FOTT_4, aomLocationType.RELIC)

    # FOTT 5 relics
    FOTT_5_RELIC_1  = (global_location_id(aomScenarioData.FOTT_5.id, 10), "Relic 1: Stone Pillars on Way to Camp", aomScenarioData.FOTT_5, aomLocationType.RELIC)
    FOTT_5_RELIC_2  = (global_location_id(aomScenarioData.FOTT_5.id, 11), "Relic 2: North of Market", aomScenarioData.FOTT_5, aomLocationType.RELIC)

    # FOTT 6 relics
    FOTT_6_RELIC_1  = (global_location_id(aomScenarioData.FOTT_6.id, 10), "Relic 1: East of Camp", aomScenarioData.FOTT_6, aomLocationType.RELIC)
    FOTT_6_RELIC_2  = (global_location_id(aomScenarioData.FOTT_6.id, 11), "Relic 2: West of Camp", aomScenarioData.FOTT_6, aomLocationType.RELIC)
    FOTT_6_RELIC_3  = (global_location_id(aomScenarioData.FOTT_6.id, 12), "Relic 3: Just South Near Pillars", aomScenarioData.FOTT_6, aomLocationType.RELIC)
    FOTT_6_RELIC_4  = (global_location_id(aomScenarioData.FOTT_6.id, 13), "Relic 4: Far South Near Wrecked Buildings", aomScenarioData.FOTT_6, aomLocationType.RELIC)
    FOTT_6_RELIC_5  = (global_location_id(aomScenarioData.FOTT_6.id, 14), "Relic 5: Far South Near Beach", aomScenarioData.FOTT_6, aomLocationType.RELIC)

    # FOTT 7 relics
    FOTT_7_RELIC_1  = (global_location_id(aomScenarioData.FOTT_7.id, 10), "Relic 1: Bay Before Centaurs", aomScenarioData.FOTT_7, aomLocationType.RELIC)
    FOTT_7_RELIC_2  = (global_location_id(aomScenarioData.FOTT_7.id, 11), "Relic 2: Shrine North of Second Prison", aomScenarioData.FOTT_7, aomLocationType.RELIC)
    FOTT_7_RELIC_3  = (global_location_id(aomScenarioData.FOTT_7.id, 12), "Relic 3: At Bay, Far South of Imprisoned Temple", aomScenarioData.FOTT_7, aomLocationType.RELIC)
    FOTT_7_RELIC_4  = (global_location_id(aomScenarioData.FOTT_7.id, 13), "Relic 4: Shrine North of Imprisoned Temple", aomScenarioData.FOTT_7, aomLocationType.RELIC)

    # FOTT 8 relics
    FOTT_8_RELIC_1  = (global_location_id(aomScenarioData.FOTT_8.id, 10), "Relic 1: South Forest of East Camp", aomScenarioData.FOTT_8, aomLocationType.RELIC)
    FOTT_8_RELIC_2  = (global_location_id(aomScenarioData.FOTT_8.id, 11), "Relic 2: West Camp North of Cliffs", aomScenarioData.FOTT_8, aomLocationType.RELIC)

    # FOTT 12 relics
    FOTT_12_RELIC_1 = (global_location_id(aomScenarioData.FOTT_12.id, 10), "Relic 1: At World Wonder North of Base", aomScenarioData.FOTT_12, aomLocationType.RELIC)

    # FOTT 13 relics
    FOTT_13_RELIC_1 = (global_location_id(aomScenarioData.FOTT_13.id, 10), "Relic 1: At Starting Temple #1", aomScenarioData.FOTT_13, aomLocationType.RELIC)
    FOTT_13_RELIC_2 = (global_location_id(aomScenarioData.FOTT_13.id, 11), "Relic 2: At Starting Temple #2", aomScenarioData.FOTT_13, aomLocationType.RELIC)
    FOTT_13_RELIC_3 = (global_location_id(aomScenarioData.FOTT_13.id, 12), "Relic 3: At Starting Temple #3", aomScenarioData.FOTT_13, aomLocationType.RELIC)
    FOTT_13_RELIC_4 = (global_location_id(aomScenarioData.FOTT_13.id, 13), "Relic 4: Shrine Northeast of River", aomScenarioData.FOTT_13, aomLocationType.RELIC)
    FOTT_13_RELIC_5 = (global_location_id(aomScenarioData.FOTT_13.id, 14), "Relic 5: Shrine Far North of River", aomScenarioData.FOTT_13, aomLocationType.RELIC)
    FOTT_13_RELIC_6 = (global_location_id(aomScenarioData.FOTT_13.id, 15), "Relic 6: Stone Pillars at First U-Turn", aomScenarioData.FOTT_13, aomLocationType.RELIC)
    FOTT_13_RELIC_7 = (global_location_id(aomScenarioData.FOTT_13.id, 16), "Relic 7: Stone Pillars at End of Shortcut", aomScenarioData.FOTT_13, aomLocationType.RELIC)

    # FOTT 14 relics
    FOTT_14_RELIC_1 = (global_location_id(aomScenarioData.FOTT_14.id, 10), "Relic 1: At Sphinx East of Base", aomScenarioData.FOTT_14, aomLocationType.RELIC)

    # FOTT 15 relics
    FOTT_15_RELIC_1 = (global_location_id(aomScenarioData.FOTT_15.id, 10), "Relic 1: In the North River", aomScenarioData.FOTT_15, aomLocationType.RELIC)
    FOTT_15_RELIC_2 = (global_location_id(aomScenarioData.FOTT_15.id, 11), "Relic 2: At Pink Temple #1", aomScenarioData.FOTT_15, aomLocationType.RELIC)
    FOTT_15_RELIC_3 = (global_location_id(aomScenarioData.FOTT_15.id, 12), "Relic 3: At Pink Temple #2", aomScenarioData.FOTT_15, aomLocationType.RELIC)
    FOTT_15_RELIC_4 = (global_location_id(aomScenarioData.FOTT_15.id, 13), "Relic 4: Far North at Pink Lighthouse #1", aomScenarioData.FOTT_15, aomLocationType.RELIC)
    FOTT_15_RELIC_5 = (global_location_id(aomScenarioData.FOTT_15.id, 14), "Relic 5: Far North at Pink Lighthouse #2", aomScenarioData.FOTT_15, aomLocationType.RELIC)
    FOTT_15_RELIC_6 = (global_location_id(aomScenarioData.FOTT_15.id, 15), "Relic 6: Southwest of Final Wall", aomScenarioData.FOTT_15, aomLocationType.RELIC)
    FOTT_15_RELIC_7 = (global_location_id(aomScenarioData.FOTT_15.id, 16), "Relic 7: At Enemy World Wonder", aomScenarioData.FOTT_15, aomLocationType.RELIC)
    FOTT_15_RELIC_8 = (global_location_id(aomScenarioData.FOTT_15.id, 17), "Relic 8: Yellow Houses at Far East", aomScenarioData.FOTT_15, aomLocationType.RELIC)
    FOTT_15_RELIC_9 = (global_location_id(aomScenarioData.FOTT_15.id, 18), "Relic 9: At Enemy Citadel Far North", aomScenarioData.FOTT_15, aomLocationType.RELIC)

    # FOTT 16 relics
    FOTT_16_RELIC_1  = (global_location_id(aomScenarioData.FOTT_16.id, 10), "Relic 1: Part 2 - Beach of Starting Island", aomScenarioData.FOTT_16, aomLocationType.RELIC)
    FOTT_16_RELIC_2  = (global_location_id(aomScenarioData.FOTT_16.id, 11), "Relic 2: Part 2 - South of Starting Island", aomScenarioData.FOTT_16, aomLocationType.RELIC)
    FOTT_16_RELIC_3  = (global_location_id(aomScenarioData.FOTT_16.id, 12), "Relic 3: Part 2 - Stone Pillar at Base", aomScenarioData.FOTT_16, aomLocationType.RELIC)
    FOTT_16_RELIC_4  = (global_location_id(aomScenarioData.FOTT_16.id, 13), "Relic 4: Part 2 - Wreck at South Beach", aomScenarioData.FOTT_16, aomLocationType.RELIC)
    FOTT_16_RELIC_5  = (global_location_id(aomScenarioData.FOTT_16.id, 14), "Relic 5: Part 2 - Southwest of Beach", aomScenarioData.FOTT_16, aomLocationType.RELIC)
    FOTT_16_RELIC_6  = (global_location_id(aomScenarioData.FOTT_16.id, 15), "Relic 6: Part 2 - East of Beach", aomScenarioData.FOTT_16, aomLocationType.RELIC)
    FOTT_16_RELIC_7  = (global_location_id(aomScenarioData.FOTT_16.id, 16), "Relic 7: Part 2 - West of Northern Settlement", aomScenarioData.FOTT_16, aomLocationType.RELIC)
    FOTT_16_RELIC_8  = (global_location_id(aomScenarioData.FOTT_16.id, 17), "Relic 8: Part 2 - East of Northern Settlement", aomScenarioData.FOTT_16, aomLocationType.RELIC)
    FOTT_16_RELIC_9  = (global_location_id(aomScenarioData.FOTT_16.id, 18), "Relic 9: Part 2 - On Cliff at Enemy Entrance", aomScenarioData.FOTT_16, aomLocationType.RELIC)
    FOTT_16_RELIC_10 = (global_location_id(aomScenarioData.FOTT_16.id, 19), "Relic 10: Part 2 - Under Cliff at Enemy Entrance", aomScenarioData.FOTT_16, aomLocationType.RELIC)

    # FOTT 17 relics
    FOTT_17_RELIC_1  = (global_location_id(aomScenarioData.FOTT_17.id, 10), "Relic 1: Stone Pillars North of Start", aomScenarioData.FOTT_17, aomLocationType.RELIC)
    FOTT_17_RELIC_2  = (global_location_id(aomScenarioData.FOTT_17.id, 11), "Relic 2: South of Start Near Tent", aomScenarioData.FOTT_17, aomLocationType.RELIC)
    FOTT_17_RELIC_3  = (global_location_id(aomScenarioData.FOTT_17.id, 12), "Relic 3: Ra Statue at North of Southeast Settlement", aomScenarioData.FOTT_17, aomLocationType.RELIC)
    FOTT_17_RELIC_4  = (global_location_id(aomScenarioData.FOTT_17.id, 13), "Relic 4: Ra Statue at South Village", aomScenarioData.FOTT_17, aomLocationType.RELIC)
    FOTT_17_RELIC_5  = (global_location_id(aomScenarioData.FOTT_17.id, 14), "Relic 5: Stone Pillars at Half-Island", aomScenarioData.FOTT_17, aomLocationType.RELIC)
    FOTT_17_RELIC_6  = (global_location_id(aomScenarioData.FOTT_17.id, 15), "Relic 6: Osiris Statue at Mini Island", aomScenarioData.FOTT_17, aomLocationType.RELIC)
    FOTT_17_RELIC_7  = (global_location_id(aomScenarioData.FOTT_17.id, 16), "Relic 7: Entrance of Northern Bay", aomScenarioData.FOTT_17, aomLocationType.RELIC)
    FOTT_17_RELIC_8  = (global_location_id(aomScenarioData.FOTT_17.id, 17), "Relic 8: Secret Oasis at Northern Bay #1", aomScenarioData.FOTT_17, aomLocationType.RELIC)
    FOTT_17_RELIC_9  = (global_location_id(aomScenarioData.FOTT_17.id, 18), "Relic 9: Secret Oasis of Northern Bay #2", aomScenarioData.FOTT_17, aomLocationType.RELIC)
    FOTT_17_RELIC_10 = (global_location_id(aomScenarioData.FOTT_17.id, 19), "Relic 10: Secret Oasis of Northern Bay #3", aomScenarioData.FOTT_17, aomLocationType.RELIC)

    # FOTT 18 relics
    FOTT_18_RELIC_1 = (global_location_id(aomScenarioData.FOTT_18.id, 10), "Relic 1: Far South of Map", aomScenarioData.FOTT_18, aomLocationType.RELIC)
    FOTT_18_RELIC_2 = (global_location_id(aomScenarioData.FOTT_18.id, 11), "Relic 2: Far West Near Mummy Temple #1", aomScenarioData.FOTT_18, aomLocationType.RELIC)
    FOTT_18_RELIC_3 = (global_location_id(aomScenarioData.FOTT_18.id, 12), "Relic 3: Far West Near Mummy Temple #2", aomScenarioData.FOTT_18, aomLocationType.RELIC)
    FOTT_18_RELIC_4 = (global_location_id(aomScenarioData.FOTT_18.id, 13), "Relic 4: Osiris Statue Near Base", aomScenarioData.FOTT_18, aomLocationType.RELIC)
    FOTT_18_RELIC_5 = (global_location_id(aomScenarioData.FOTT_18.id, 14), "Relic 5: In Front of Eastern Enemy Outpost", aomScenarioData.FOTT_18, aomLocationType.RELIC)

    # FOTT 19 relics
    FOTT_19_RELIC_1 = (global_location_id(aomScenarioData.FOTT_19.id, 10), "Relic 1: West of Far Southern Island", aomScenarioData.FOTT_19, aomLocationType.RELIC)
    FOTT_19_RELIC_2 = (global_location_id(aomScenarioData.FOTT_19.id, 11), "Relic 2: East of Far Southern Island", aomScenarioData.FOTT_19, aomLocationType.RELIC)
    FOTT_19_RELIC_3 = (global_location_id(aomScenarioData.FOTT_19.id, 12), "Relic 3: Shipwreck at North of Enemy Harbor", aomScenarioData.FOTT_19, aomLocationType.RELIC)

    # FOTT 20 relics
    FOTT_20_RELIC_1 = (global_location_id(aomScenarioData.FOTT_20.id, 10), "Relic 1: Far South of Map", aomScenarioData.FOTT_20, aomLocationType.RELIC)
    FOTT_20_RELIC_2 = (global_location_id(aomScenarioData.FOTT_20.id, 11), "Relic 2: Trees Between Bases", aomScenarioData.FOTT_20, aomLocationType.RELIC)
    FOTT_20_RELIC_3 = (global_location_id(aomScenarioData.FOTT_20.id, 12), "Relic 3: Enemy Temple at Lake", aomScenarioData.FOTT_20, aomLocationType.RELIC)
    FOTT_20_RELIC_4 = (global_location_id(aomScenarioData.FOTT_20.id, 13), "Relic 4: At Far Eastern Settlement", aomScenarioData.FOTT_20, aomLocationType.RELIC)
    FOTT_20_RELIC_5 = (global_location_id(aomScenarioData.FOTT_20.id, 14), "Relic 5: North of Far Eastern Settlement", aomScenarioData.FOTT_20, aomLocationType.RELIC)

    # FOTT 21 relics
    FOTT_21_RELIC_1 = (global_location_id(aomScenarioData.FOTT_21.id, 10), "Relic 1: Shipwreck West of Zeus Temple", aomScenarioData.FOTT_21, aomLocationType.RELIC)
    FOTT_21_RELIC_2 = (global_location_id(aomScenarioData.FOTT_21.id, 11), "Relic 2: Lion Statue Far South of Western Settlement", aomScenarioData.FOTT_21, aomLocationType.RELIC)
    FOTT_21_RELIC_3 = (global_location_id(aomScenarioData.FOTT_21.id, 12), "Relic 3: Stone Pillars Southwest of Island", aomScenarioData.FOTT_21, aomLocationType.RELIC)
    FOTT_21_RELIC_4 = (global_location_id(aomScenarioData.FOTT_21.id, 13), "Relic 4: Shipwreck North of Eastern Settlement", aomScenarioData.FOTT_21, aomLocationType.RELIC)
    FOTT_21_RELIC_5 = (global_location_id(aomScenarioData.FOTT_21.id, 14), "Relic 5: South Stone Pillars of Eastern Settlement", aomScenarioData.FOTT_21, aomLocationType.RELIC)
    FOTT_21_RELIC_6 = (global_location_id(aomScenarioData.FOTT_21.id, 15), "Relic 6: East of Eastern Settlement", aomScenarioData.FOTT_21, aomLocationType.RELIC)

    # FOTT 22 relics
    FOTT_22_RELIC_1 = (global_location_id(aomScenarioData.FOTT_22.id, 10), "Relic 1: Far South of Western Settlement", aomScenarioData.FOTT_22, aomLocationType.RELIC)
    FOTT_22_RELIC_2 = (global_location_id(aomScenarioData.FOTT_22.id, 11), "Relic 2: West of Ice Lake", aomScenarioData.FOTT_22, aomLocationType.RELIC)
    FOTT_22_RELIC_3 = (global_location_id(aomScenarioData.FOTT_22.id, 12), "Relic 3: Statue at North of Ice Lake", aomScenarioData.FOTT_22, aomLocationType.RELIC)
    FOTT_22_RELIC_4 = (global_location_id(aomScenarioData.FOTT_22.id, 13), "Relic 4: Stone Pillars East of Eastern Settlement", aomScenarioData.FOTT_22, aomLocationType.RELIC)

    # FOTT 23 relics
    FOTT_23_RELIC_1 = (global_location_id(aomScenarioData.FOTT_23.id, 10), "Relic 1: Crumbling Wall Eastern Cave #1", aomScenarioData.FOTT_23, aomLocationType.RELIC)
    FOTT_23_RELIC_2 = (global_location_id(aomScenarioData.FOTT_23.id, 11), "Relic 2: Crumbling Wall Eastern Cave #2", aomScenarioData.FOTT_23, aomLocationType.RELIC)
    FOTT_23_RELIC_3 = (global_location_id(aomScenarioData.FOTT_23.id, 12), "Relic 3: Crumbling Wall Eastern Cave #3", aomScenarioData.FOTT_23, aomLocationType.RELIC)

    # FOTT 27 relics
    FOTT_27_RELIC_1 = (global_location_id(aomScenarioData.FOTT_27.id, 10), "Relic 1: At Western Lake", aomScenarioData.FOTT_27, aomLocationType.RELIC)
    FOTT_27_RELIC_2 = (global_location_id(aomScenarioData.FOTT_27.id, 11), "Relic 2: Stone Pillars at Southwest of Well of Urd", aomScenarioData.FOTT_27, aomLocationType.RELIC)
    FOTT_27_RELIC_3 = (global_location_id(aomScenarioData.FOTT_27.id, 12), "Relic 3: Far East of Map", aomScenarioData.FOTT_27, aomLocationType.RELIC)
    FOTT_27_RELIC_4 = (global_location_id(aomScenarioData.FOTT_27.id, 13), "Relic 4: Within Enemy Temple", aomScenarioData.FOTT_27, aomLocationType.RELIC)

    # FOTT 28 relics
    FOTT_28_RELIC_1 = (global_location_id(aomScenarioData.FOTT_28.id, 10), "Relic 1: Broken Buildings in Northwest", aomScenarioData.FOTT_28, aomLocationType.RELIC)
    FOTT_28_RELIC_2 = (global_location_id(aomScenarioData.FOTT_28.id, 11), "Relic 2: Far South of Settlement", aomScenarioData.FOTT_28, aomLocationType.RELIC)
    FOTT_28_RELIC_3 = (global_location_id(aomScenarioData.FOTT_28.id, 12), "Relic 3: At South in Underworld Entrance", aomScenarioData.FOTT_28, aomLocationType.RELIC)
    FOTT_28_RELIC_4 = (global_location_id(aomScenarioData.FOTT_28.id, 13), "Relic 4: North of Underworld Entrance", aomScenarioData.FOTT_28, aomLocationType.RELIC)
    FOTT_28_RELIC_5 = (global_location_id(aomScenarioData.FOTT_28.id, 14), "Relic 5: Far North of Underworld Entrance", aomScenarioData.FOTT_28, aomLocationType.RELIC)

    # FOTT 30 relics
    FOTT_30_RELIC_1 = (global_location_id(aomScenarioData.FOTT_30.id, 10), "Relic 1: West of Temple", aomScenarioData.FOTT_30, aomLocationType.RELIC)
    FOTT_30_RELIC_2 = (global_location_id(aomScenarioData.FOTT_30.id, 11), "Relic 2: Southern Settlement", aomScenarioData.FOTT_30, aomLocationType.RELIC)
    FOTT_30_RELIC_3 = (global_location_id(aomScenarioData.FOTT_30.id, 12), "Relic 3: North of Eastern Walls", aomScenarioData.FOTT_30, aomLocationType.RELIC)
    FOTT_30_RELIC_4 = (global_location_id(aomScenarioData.FOTT_30.id, 13), "Relic 4: At Western Lake", aomScenarioData.FOTT_30, aomLocationType.RELIC)
    FOTT_30_RELIC_5 = (global_location_id(aomScenarioData.FOTT_30.id, 14), "Relic 5: East of Eastern Lake", aomScenarioData.FOTT_30, aomLocationType.RELIC)
    FOTT_30_RELIC_6 = (global_location_id(aomScenarioData.FOTT_30.id, 15), "Relic 6: Stone Pillars in Orange Base", aomScenarioData.FOTT_30, aomLocationType.RELIC)

    # FOTT 31 relics
    FOTT_31_RELIC_1 = (global_location_id(aomScenarioData.FOTT_31.id, 10), "Relic 1: Starting Island", aomScenarioData.FOTT_31, aomLocationType.RELIC)
    FOTT_31_RELIC_2 = (global_location_id(aomScenarioData.FOTT_31.id, 11), "Relic 2: Far East Valley", aomScenarioData.FOTT_31, aomLocationType.RELIC)

    # FOTT 32 relics
    FOTT_32_RELIC_1 = (global_location_id(aomScenarioData.FOTT_32.id, 10), "Relic 1: Stone Pillars of Blue Village", aomScenarioData.FOTT_32, aomLocationType.RELIC)
    FOTT_32_RELIC_2 = (global_location_id(aomScenarioData.FOTT_32.id, 11), "Relic 2: North of Western Plenty Vault", aomScenarioData.FOTT_32, aomLocationType.RELIC)
    FOTT_32_RELIC_3 = (global_location_id(aomScenarioData.FOTT_32.id, 12), "Relic 3: Southeast Lake at Enemy Outpost", aomScenarioData.FOTT_32, aomLocationType.RELIC)

    # NA 2 relics (special: trigger condition checks Temple OR Overgrown Temple)
    NA_2_RELIC_1 = (global_location_id(aomScenarioData.NA_2.id, 10), "Relic 1: Starting Oranos Temple", aomScenarioData.NA_2, aomLocationType.RELIC)
    NA_2_RELIC_2 = (global_location_id(aomScenarioData.NA_2.id, 11), "Relic 2: Western Beach", aomScenarioData.NA_2, aomLocationType.RELIC)
    NA_2_RELIC_3 = (global_location_id(aomScenarioData.NA_2.id, 12), "Relic 3: Central Lake Southeast Temple", aomScenarioData.NA_2, aomLocationType.RELIC)
    NA_2_RELIC_4 = (global_location_id(aomScenarioData.NA_2.id, 13), "Relic 4: Central Lake Southwest Temple", aomScenarioData.NA_2, aomLocationType.RELIC)
    NA_2_RELIC_5 = (global_location_id(aomScenarioData.NA_2.id, 14), "Relic 5: Central Forest", aomScenarioData.NA_2, aomLocationType.RELIC)
    NA_2_RELIC_6 = (global_location_id(aomScenarioData.NA_2.id, 15), "Relic 6: Southwest Beach #1", aomScenarioData.NA_2, aomLocationType.RELIC)
    NA_2_RELIC_7 = (global_location_id(aomScenarioData.NA_2.id, 16), "Relic 7: Southwest Beach #2", aomScenarioData.NA_2, aomLocationType.RELIC)
    NA_2_RELIC_8 = (global_location_id(aomScenarioData.NA_2.id, 17), "Relic 8: Burning West Forest", aomScenarioData.NA_2, aomLocationType.RELIC)
    NA_2_RELIC_9 = (global_location_id(aomScenarioData.NA_2.id, 18), "Relic 9: Far South Island", aomScenarioData.NA_2, aomLocationType.RELIC)

    # NA 3 relics
    NA_3_RELIC_1 = (global_location_id(aomScenarioData.NA_3.id, 10), "Relic 1: In Center of 3 Scyllas", aomScenarioData.NA_3, aomLocationType.RELIC)
    NA_3_RELIC_2 = (global_location_id(aomScenarioData.NA_3.id, 11), "Relic 2: Center Plenty Vault", aomScenarioData.NA_3, aomLocationType.RELIC)
    NA_3_RELIC_3 = (global_location_id(aomScenarioData.NA_3.id, 12), "Relic 3: Northwest Cave #1", aomScenarioData.NA_3, aomLocationType.RELIC)
    NA_3_RELIC_4 = (global_location_id(aomScenarioData.NA_3.id, 13), "Relic 4: Northwest Cave #2", aomScenarioData.NA_3, aomLocationType.RELIC)

    # NA 4 relics
    NA_4_RELIC_1 = (global_location_id(aomScenarioData.NA_4.id, 10), "Relic 1: West Hill from Start", aomScenarioData.NA_4, aomLocationType.RELIC)
    NA_4_RELIC_2 = (global_location_id(aomScenarioData.NA_4.id, 11), "Relic 2: Center Statue of Red's Base", aomScenarioData.NA_4, aomLocationType.RELIC)
    NA_4_RELIC_3 = (global_location_id(aomScenarioData.NA_4.id, 12), "Relic 3: Stone Pillars North of Red's Base", aomScenarioData.NA_4, aomLocationType.RELIC)
    NA_4_RELIC_4 = (global_location_id(aomScenarioData.NA_4.id, 13), "Relic 4: Northern Statue of Purple's Base", aomScenarioData.NA_4, aomLocationType.RELIC)
    NA_4_RELIC_5 = (global_location_id(aomScenarioData.NA_4.id, 14), "Relic 5: Southern Statue of Purple's Base", aomScenarioData.NA_4, aomLocationType.RELIC)
    NA_4_RELIC_6 = (global_location_id(aomScenarioData.NA_4.id, 15), "Relic 6: Cliff Between Purple and Pink", aomScenarioData.NA_4, aomLocationType.RELIC)
    NA_4_RELIC_7 = (global_location_id(aomScenarioData.NA_4.id, 16), "Relic 7: Statue at Center of Pink's Base", aomScenarioData.NA_4, aomLocationType.RELIC)

    # NA 5 relics (these doubly serve as the main objective; both fire when garrisoned)
    NA_5_RELIC_1 = (global_location_id(aomScenarioData.NA_5.id, 10), "Relic 1: Orange's Base", aomScenarioData.NA_5, aomLocationType.RELIC)
    NA_5_RELIC_2 = (global_location_id(aomScenarioData.NA_5.id, 11), "Relic 2: Pink's Base", aomScenarioData.NA_5, aomLocationType.RELIC)
    NA_5_RELIC_3 = (global_location_id(aomScenarioData.NA_5.id, 12), "Relic 3: Yellow's Base", aomScenarioData.NA_5, aomLocationType.RELIC)
    NA_5_RELIC_4 = (global_location_id(aomScenarioData.NA_5.id, 13), "Relic 4: Red's Base", aomScenarioData.NA_5, aomLocationType.RELIC)

    # NA 7 relics
    NA_7_RELIC_1 = (global_location_id(aomScenarioData.NA_7.id, 10), "Relic 1: West of Start", aomScenarioData.NA_7, aomLocationType.RELIC)
    NA_7_RELIC_2 = (global_location_id(aomScenarioData.NA_7.id, 11), "Relic 2: East of Start", aomScenarioData.NA_7, aomLocationType.RELIC)

    # NA 8 relics
    NA_8_RELIC_1 = (global_location_id(aomScenarioData.NA_8.id, 10), "Relic 1: West of Starting Lake #1", aomScenarioData.NA_8, aomLocationType.RELIC)
    NA_8_RELIC_2 = (global_location_id(aomScenarioData.NA_8.id, 11), "Relic 2: West of Starting Lake #2", aomScenarioData.NA_8, aomLocationType.RELIC)
    NA_8_RELIC_3 = (global_location_id(aomScenarioData.NA_8.id, 12), "Relic 3: Cliff by Southern Temple", aomScenarioData.NA_8, aomLocationType.RELIC)
    NA_8_RELIC_4 = (global_location_id(aomScenarioData.NA_8.id, 13), "Relic 4: Cliff East of Guardian", aomScenarioData.NA_8, aomLocationType.RELIC)
    NA_8_RELIC_5 = (global_location_id(aomScenarioData.NA_8.id, 14), "Relic 5: Statue South of Guardian", aomScenarioData.NA_8, aomLocationType.RELIC)
    NA_8_RELIC_6 = (global_location_id(aomScenarioData.NA_8.id, 15), "Relic 6: Stone Pillars Far Southeast", aomScenarioData.NA_8, aomLocationType.RELIC)
    NA_8_RELIC_7 = (global_location_id(aomScenarioData.NA_8.id, 16), "Relic 7: Statue at Western River", aomScenarioData.NA_8, aomLocationType.RELIC)

    # NA 9 relics
    NA_9_RELIC_1 = (global_location_id(aomScenarioData.NA_9.id, 10), "Relic 1: East Corner Forest", aomScenarioData.NA_9, aomLocationType.RELIC)
    NA_9_RELIC_2 = (global_location_id(aomScenarioData.NA_9.id, 11), "Relic 2: Stone Pillars South Corner of Map", aomScenarioData.NA_9, aomLocationType.RELIC)

    # NA 10 relics
    NA_10_RELIC_1 = (global_location_id(aomScenarioData.NA_10.id, 10), "Relic 1: Southeast of Starting Settlement", aomScenarioData.NA_10, aomLocationType.RELIC)
    NA_10_RELIC_2 = (global_location_id(aomScenarioData.NA_10.id, 11), "Relic 2: Stone Pillars at Southeast Settlement", aomScenarioData.NA_10, aomLocationType.RELIC)
    NA_10_RELIC_3 = (global_location_id(aomScenarioData.NA_10.id, 12), "Relic 3: Shrine at Eastern Settlement", aomScenarioData.NA_10, aomLocationType.RELIC)

    # NA 11 relics
    NA_11_RELIC_1 = (global_location_id(aomScenarioData.NA_11.id, 10), "Relic 1: Eastern Fountain at Start", aomScenarioData.NA_11, aomLocationType.RELIC)
    NA_11_RELIC_2 = (global_location_id(aomScenarioData.NA_11.id, 11), "Relic 2: Western Harbor", aomScenarioData.NA_11, aomLocationType.RELIC)
    NA_11_RELIC_3 = (global_location_id(aomScenarioData.NA_11.id, 12), "Relic 3: Shrine Island at East of Western Harbor", aomScenarioData.NA_11, aomLocationType.RELIC)
    NA_11_RELIC_4 = (global_location_id(aomScenarioData.NA_11.id, 13), "Relic 4: Northeast Entrance to Center", aomScenarioData.NA_11, aomLocationType.RELIC)
    NA_11_RELIC_5 = (global_location_id(aomScenarioData.NA_11.id, 14), "Relic 5: West Fountain Near Sky Passage", aomScenarioData.NA_11, aomLocationType.RELIC)
    NA_11_RELIC_6 = (global_location_id(aomScenarioData.NA_11.id, 15), "Relic 6: In Enemy Base", aomScenarioData.NA_11, aomLocationType.RELIC)

    # NA 12 relics
    NA_12_RELIC_1 = (global_location_id(aomScenarioData.NA_12.id, 10), "Relic 1: East of Gaia", aomScenarioData.NA_12, aomLocationType.RELIC)
    NA_12_RELIC_2 = (global_location_id(aomScenarioData.NA_12.id, 11), "Relic 2: Stone Pillars Northeast From Start", aomScenarioData.NA_12, aomLocationType.RELIC)
    NA_12_RELIC_3 = (global_location_id(aomScenarioData.NA_12.id, 12), "Relic 3: Stone Pillars Far Northeast From Start", aomScenarioData.NA_12, aomLocationType.RELIC)
    NA_12_RELIC_4 = (global_location_id(aomScenarioData.NA_12.id, 13), "Relic 4: North of East Fountain", aomScenarioData.NA_12, aomLocationType.RELIC)
    NA_12_RELIC_5 = (global_location_id(aomScenarioData.NA_12.id, 14), "Relic 5: Southwest of North Fountain", aomScenarioData.NA_12, aomLocationType.RELIC)
    NA_12_RELIC_6 = (global_location_id(aomScenarioData.NA_12.id, 15), "Relic 6: North Fountain #1", aomScenarioData.NA_12, aomLocationType.RELIC)
    NA_12_RELIC_7 = (global_location_id(aomScenarioData.NA_12.id, 16), "Relic 7: North Fountain #2", aomScenarioData.NA_12, aomLocationType.RELIC)
    NA_12_RELIC_8 = (global_location_id(aomScenarioData.NA_12.id, 17), "Relic 8: North Fountain #3", aomScenarioData.NA_12, aomLocationType.RELIC)
    NA_12_RELIC_9 = (global_location_id(aomScenarioData.NA_12.id, 18), "Relic 9: North Fountain #4", aomScenarioData.NA_12, aomLocationType.RELIC)

    # GG 1 relics
    GG_1_RELIC_1 = (global_location_id(aomScenarioData.GG_1.id, 10), "Relic 1: At the Southern River", aomScenarioData.GG_1, aomLocationType.RELIC)
    GG_1_RELIC_2 = (global_location_id(aomScenarioData.GG_1.id, 11), "Relic 2: North of Healing Spring", aomScenarioData.GG_1, aomLocationType.RELIC)
    GG_1_RELIC_3 = (global_location_id(aomScenarioData.GG_1.id, 12), "Relic 3: North Small Island", aomScenarioData.GG_1, aomLocationType.RELIC)
    GG_1_RELIC_4 = (global_location_id(aomScenarioData.GG_1.id, 13), "Relic 4: East of Northern Settlement", aomScenarioData.GG_1, aomLocationType.RELIC)
    GG_1_RELIC_5 = (global_location_id(aomScenarioData.GG_1.id, 14), "Relic 5: Center Hill Through Forest", aomScenarioData.GG_1, aomLocationType.RELIC)
    GG_1_RELIC_6 = (global_location_id(aomScenarioData.GG_1.id, 15), "Relic 6: Behind Folstag's Eastern Hillfort", aomScenarioData.GG_1, aomLocationType.RELIC)

    # GG 2 relics
    GG_2_RELIC_1 = (global_location_id(aomScenarioData.GG_2.id, 10), "Relic 1: East on Starting Island", aomScenarioData.GG_2, aomLocationType.RELIC)
    GG_2_RELIC_2 = (global_location_id(aomScenarioData.GG_2.id, 11), "Relic 2: Northwest Goldmine Island", aomScenarioData.GG_2, aomLocationType.RELIC)
    GG_2_RELIC_3 = (global_location_id(aomScenarioData.GG_2.id, 12), "Relic 3: Northeast Goldmine Island", aomScenarioData.GG_2, aomLocationType.RELIC)

    # GG 3 relics
    GG_3_RELIC_1 = (global_location_id(aomScenarioData.GG_3.id, 10), "Relic 1: East of Start", aomScenarioData.GG_3, aomLocationType.RELIC)
    GG_3_RELIC_2 = (global_location_id(aomScenarioData.GG_3.id, 11), "Relic 2: East Side of Northern Lake", aomScenarioData.GG_3, aomLocationType.RELIC)
    GG_3_RELIC_3 = (global_location_id(aomScenarioData.GG_3.id, 12), "Relic 3: East Side of Central Lake", aomScenarioData.GG_3, aomLocationType.RELIC)
    GG_3_RELIC_4 = (global_location_id(aomScenarioData.GG_3.id, 13), "Relic 4: East of Southeast Minecircle", aomScenarioData.GG_3, aomLocationType.RELIC)
    GG_3_RELIC_5 = (global_location_id(aomScenarioData.GG_3.id, 14), "Relic 5: Northern Troll Temple", aomScenarioData.GG_3, aomLocationType.RELIC)
    GG_3_RELIC_6 = (global_location_id(aomScenarioData.GG_3.id, 15), "Relic 6: Southern Troll Temple", aomScenarioData.GG_3, aomLocationType.RELIC)

    # GG 4 relics
    GG_4_RELIC_1 = (global_location_id(aomScenarioData.GG_4.id, 10), "Relic 1: North of Start", aomScenarioData.GG_4, aomLocationType.RELIC)
    GG_4_RELIC_2 = (global_location_id(aomScenarioData.GG_4.id, 11), "Relic 2: North of Start Mountain Giant Temple", aomScenarioData.GG_4, aomLocationType.RELIC)
    GG_4_RELIC_3 = (global_location_id(aomScenarioData.GG_4.id, 12), "Relic 3: South Troll Temple", aomScenarioData.GG_4, aomLocationType.RELIC)
    GG_4_RELIC_4 = (global_location_id(aomScenarioData.GG_4.id, 13), "Relic 4: Shrine West of South Troll Temple", aomScenarioData.GG_4, aomLocationType.RELIC)
    GG_4_RELIC_5 = (global_location_id(aomScenarioData.GG_4.id, 14), "Relic 5: Center Lake Temple", aomScenarioData.GG_4, aomLocationType.RELIC)
    GG_4_RELIC_6 = (global_location_id(aomScenarioData.GG_4.id, 15), "Relic 6: Shrine West of Center Lake Temple", aomScenarioData.GG_4, aomLocationType.RELIC)

    # ===========================================================================
    # OPTIONAL OBJECTIVES — secondary in-mission objectives, one location each.
    # Only generated when the `optional_objectives_are_locations` YAML option is on
    # (Regions.py filters OPTIONAL_OBJECTIVE locations out otherwise).  Like every
    # other scenario-anchored location, these are automatically dropped for any
    # campaign disabled via the campaign toggles.
    #
    # PER-SCENARIO local_id BANDS (the 0..99 slot inside each scenario's 100-id
    # block — see global_location_id at the top of this file).  Keep new members
    # inside their band so the ranges never collide as more content is added:
    #     0       VICTORY
    #     1       COMPLETION
    #     2  - 9  primary objectives        (aomLocationType.OBJECTIVE,           up to 8)
    #     10 - 39 relicsanity relics        (aomLocationType.RELIC,               up to 30)
    #     40 - 99 optional objectives       (aomLocationType.OPTIONAL_OBJECTIVE,  up to 60)
    # Relics historically used 10-19; the band is reserved through 39 so a
    # relic-heavy scenario can grow without ever reaching the optional band.
    #
    # Ordering here is purely cosmetic: Fall of the Trident, then Golden Gift,
    # then New Atlantis.  The lookup tables / region wiring iterate the whole
    # enum, so declaration order does not affect behavior.
    #
    # ADDING OPTIONAL OBJECTIVES FOR A NEW (OR EXISTING) CAMPAIGN:
    #   1. Make sure the scenario exists in locations/Scenarios.py (its `id`
    #      gives the 100-id block these local_ids slot into).
    #   2. Add `<SCEN>_OPT_<n>` members below, numbering local_id from 40 upward
    #      and contiguously per scenario (no gaps — fill_slot_data counts these).
    #   3. Mirror the human-readable text in archipelago.xs::APGetCheckText so
    #      the in-game toast shows the objective name (see that file's
    #      "Optional objectives (local_id >= 40)" block).  The AI bridge
    #      `APCheck_<id>` is auto-generated for every non-COMPLETION location, so
    #      no client change is needed there.
    #   4. Give the player an editor trigger that fires the check — see the
    #      generated "Optional Objectives XS Snippets" doc for the exact pattern.
    #   No Options/Regions change is required: the option gate and campaign gate
    #   already cover any new OPTIONAL_OBJECTIVE location automatically.
    # ===========================================================================

    # FOTT_1: 1. Omens
    FOTT_1_OPT_1 = (global_location_id(aomScenarioData.FOTT_1.id, 40), "Train Archers.", aomScenarioData.FOTT_1, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_1_OPT_2 = (global_location_id(aomScenarioData.FOTT_1.id, 41), "Train Infantry.", aomScenarioData.FOTT_1, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_1_OPT_3 = (global_location_id(aomScenarioData.FOTT_1.id, 42), "Upgrade your units using the Armory.", aomScenarioData.FOTT_1, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_2: 2. Consequences
    FOTT_2_OPT_1 = (global_location_id(aomScenarioData.FOTT_2.id, 40), "Task an idle Villager to gather Food.", aomScenarioData.FOTT_2, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_2_OPT_2 = (global_location_id(aomScenarioData.FOTT_2.id, 41), "Build a Dock.", aomScenarioData.FOTT_2, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_4: 4. A Fine Plan
    FOTT_4_OPT_1 = (global_location_id(aomScenarioData.FOTT_4.id, 40), "Destroy Trojan mining camps to loot Gold.", aomScenarioData.FOTT_4, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_4_OPT_2 = (global_location_id(aomScenarioData.FOTT_4.id, 41), "Destroy Troy's caravans and Market to cut its Gold supply and weaken its forces.", aomScenarioData.FOTT_4, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_6: 6. I Hope This Works
    FOTT_6_OPT_1 = (global_location_id(aomScenarioData.FOTT_6.id, 40), "Prevent Trojan scouts from giving away your location.", aomScenarioData.FOTT_6, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_6_OPT_2 = (global_location_id(aomScenarioData.FOTT_6.id, 41), "Kill the Cyclops guard to steal the Helepolis siege towers.", aomScenarioData.FOTT_6, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_6_OPT_3 = (global_location_id(aomScenarioData.FOTT_6.id, 42), "Use the Helepolis siege towers to destroy the Trojan gate.", aomScenarioData.FOTT_6, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_7: 7. More Bandits
    FOTT_7_OPT_1 = (global_location_id(aomScenarioData.FOTT_7.id, 40), "Find additional resources in Ioklos.", aomScenarioData.FOTT_7, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_9: 9. Revelation
    FOTT_9_OPT_1 = (global_location_id(aomScenarioData.FOTT_9.id, 40), "Block tunnels to slow enemy attacks.", aomScenarioData.FOTT_9, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_10: 10. Strangers
    FOTT_10_OPT_1 = (global_location_id(aomScenarioData.FOTT_10.id, 40), "Rescue any Greek soldiers trapped by the cave-in.", aomScenarioData.FOTT_10, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_14: 14. Isis, Hear My Plea
    FOTT_14_OPT_1 = (global_location_id(aomScenarioData.FOTT_14.id, 40), "Take control of allied Monuments by bringing Amanra to them.", aomScenarioData.FOTT_14, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_14_OPT_2 = (global_location_id(aomScenarioData.FOTT_14.id, 41), "Take control of allied Temples by bringing Amanra to them.", aomScenarioData.FOTT_14, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_15: 15. Let's Go
    FOTT_15_OPT_1 = (global_location_id(aomScenarioData.FOTT_15.id, 40), "Destroy the Lighthouse at the entrance to Abydos' harbor.", aomScenarioData.FOTT_15, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_17: 17. The Jackal's Stronghold
    FOTT_17_OPT_1 = (global_location_id(aomScenarioData.FOTT_17.id, 40), "Bring Amanra to any allied buildings or Laborers to convert them to your cause.", aomScenarioData.FOTT_17, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_18: 18. A Long Way From Home
    FOTT_18_OPT_1 = (global_location_id(aomScenarioData.FOTT_18.id, 40), "Destroy the old tombs in the desert to stop the Mummy attacks.", aomScenarioData.FOTT_18, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_19: 19. Watch That First Step
    FOTT_19_OPT_1 = (global_location_id(aomScenarioData.FOTT_19.id, 40), "Stay behind the large forest to remain undetected until you are ready to attack.", aomScenarioData.FOTT_19, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_20: 20. Where They Belong
    FOTT_20_OPT_1 = (global_location_id(aomScenarioData.FOTT_20.id, 40), "Bring all Osiris Piece Carts to the Pyramid before Kemsyt opens the Underworld passage.", aomScenarioData.FOTT_20, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_20_OPT_2 = (global_location_id(aomScenarioData.FOTT_20.id, 41), "Destroy Kemsyt's Tower to liberate the fishing village.", aomScenarioData.FOTT_20, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_21: 21. Old Friends
    FOTT_21_OPT_1 = (global_location_id(aomScenarioData.FOTT_21.id, 40), "Search for and rescue more pigs.", aomScenarioData.FOTT_21, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_21_OPT_2 = (global_location_id(aomScenarioData.FOTT_21.id, 41), "Rescue and restore as many pigs as you can to human form.", aomScenarioData.FOTT_21, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_21_OPT_3 = (global_location_id(aomScenarioData.FOTT_21.id, 42), "Capture Circe's outlying Docks by defeating their guards.", aomScenarioData.FOTT_21, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_25: 25. Welcoming Committee
    FOTT_25_OPT_1 = (global_location_id(aomScenarioData.FOTT_25.id, 40), "Create an ambush - build at least five Towers.", aomScenarioData.FOTT_25, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_27: 27. The Well of Urd
    FOTT_27_OPT_1 = (global_location_id(aomScenarioData.FOTT_27.id, 40), "Find and raid the enemy town to the west.", aomScenarioData.FOTT_27, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_29: 29. Unlikely Heroes
    FOTT_29_OPT_1 = (global_location_id(aomScenarioData.FOTT_29.id, 40), "Mine Gold to receive reinforcements from the surface.", aomScenarioData.FOTT_29, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_29_OPT_2 = (global_location_id(aomScenarioData.FOTT_29.id, 41), "Rescue captured Norsemen.", aomScenarioData.FOTT_29, aomLocationType.OPTIONAL_OBJECTIVE)
    # FOTT_32: 32. A Place in My Dreams
    FOTT_32_OPT_1 = (global_location_id(aomScenarioData.FOTT_32.id, 40), "Destroy Temples of Poseidon for Meteor god powers.", aomScenarioData.FOTT_32, aomLocationType.OPTIONAL_OBJECTIVE)
    FOTT_32_OPT_2 = (global_location_id(aomScenarioData.FOTT_32.id, 41), "Recapture Atlantis' Plenty Vaults for more resources.", aomScenarioData.FOTT_32, aomLocationType.OPTIONAL_OBJECTIVE)
    # GG_1: GG 1. Brokk's Journey
    GG_1_OPT_1 = (global_location_id(aomScenarioData.GG_1.id, 40), "Rescue Arngrim's cows.", aomScenarioData.GG_1, aomLocationType.OPTIONAL_OBJECTIVE)
    # GG_3: GG 3. Fight at the Forge
    GG_3_OPT_1 = (global_location_id(aomScenarioData.GG_3.id, 40), "Find and destroy Eitri's Docks to capture his Fishing Ships.", aomScenarioData.GG_3, aomLocationType.OPTIONAL_OBJECTIVE)
    # GG_4: GG 4. Loki's Temples
    GG_4_OPT_1 = (global_location_id(aomScenarioData.GG_4.id, 40), "Destroy all of Loki's Temples (Orange).", aomScenarioData.GG_4, aomLocationType.OPTIONAL_OBJECTIVE)
    # NA_2: NA 2. Atlantis Reborn
    NA_2_OPT_1 = (global_location_id(aomScenarioData.NA_2.id, 40), "Repair all remaining Temples.", aomScenarioData.NA_2, aomLocationType.OPTIONAL_OBJECTIVE)
    NA_2_OPT_2 = (global_location_id(aomScenarioData.NA_2.id, 41), "Destroy the four Military Academies beyond the pass.", aomScenarioData.NA_2, aomLocationType.OPTIONAL_OBJECTIVE)
    # NA_3: NA 3. Greetings From Greece
    NA_3_OPT_1 = (global_location_id(aomScenarioData.NA_3.id, 40), "Claim Plenty Vaults to gain resources.", aomScenarioData.NA_3, aomLocationType.OPTIONAL_OBJECTIVE)
    NA_3_OPT_2 = (global_location_id(aomScenarioData.NA_3.id, 41), "Destroy Statues of Melagius for various rewards.", aomScenarioData.NA_3, aomLocationType.OPTIONAL_OBJECTIVE)
    NA_3_OPT_3 = (global_location_id(aomScenarioData.NA_3.id, 42), "Capture the Greek fishing village.", aomScenarioData.NA_3, aomLocationType.OPTIONAL_OBJECTIVE)
    # NA_6: NA 6. Mount Olympus
    NA_6_OPT_1 = (global_location_id(aomScenarioData.NA_6.id, 40), "Destroy Shrines of Olympus for different rewards.", aomScenarioData.NA_6, aomLocationType.OPTIONAL_OBJECTIVE)
    # NA_8: NA 8. Cerberus
    NA_8_OPT_1 = (global_location_id(aomScenarioData.NA_8.id, 40), "Find stray Camel caravans.", aomScenarioData.NA_8, aomLocationType.OPTIONAL_OBJECTIVE)
    # NA_9: NA 9. Rampage
    NA_9_OPT_1 = (global_location_id(aomScenarioData.NA_9.id, 40), "Protect Folstag's Temples to receive Frost Giants.", aomScenarioData.NA_9, aomLocationType.OPTIONAL_OBJECTIVE)




# --- Lookup tables built once at import time ---
# All four maps are built by walking `aomLocationData`.  Adding a new location
# member auto-registers it everywhere — no extra wiring is needed.

# UNUSED: never read outside this module. Kept (commented) for ad-hoc id→enum lookups.
# # global location id → enum member
# location_from_id: dict[int, aomLocationData] = {
#     location.id: location for location in aomLocationData
# }

# AP display name → global id (consumed by AP framework via aomWorld)
location_name_to_id: dict[str, int] = {
    location.global_name(): location.id for location in aomLocationData
}

# global id → AP display name
location_id_to_name: dict[int, str] = {
    location.id: location.global_name() for location in aomLocationData
}

# scenario → all locations belonging to it (insertion-ordered)
SCENARIO_TO_LOCATIONS: dict[aomScenarioData, list[aomLocationData]] = {
    scenario: [] for scenario in aomScenarioData
}
for location in aomLocationData:
    SCENARIO_TO_LOCATIONS[location.scenario].append(location)

# Same payload as SCENARIO_TO_LOCATIONS but only contains scenarios that
# actually have locations (skip entries with empty lists).  This is what
# regions/Regions.py iterates so it doesn't try to attach empty location
# lists to a Region.
REGION_TO_LOCATIONS: dict[aomScenarioData, list[aomLocationData]] = {}
for location in aomLocationData:
    REGION_TO_LOCATIONS.setdefault(location.scenario, []).append(location)

# location type → all locations of that type.  Used by Rules.py to bulk-place
# Gem and Victory items.
TYPE_TO_LOCATIONS: dict[aomLocationType, list[aomLocationData]] = {}
for location in aomLocationData:
    TYPE_TO_LOCATIONS.setdefault(location.type, []).append(location)

# scenario → its single VICTORY check.  Used by Rules.py for forced placements
# (Victory item at scenario 32; Gems at every other Victory when gem_shop is on).
VICTORY_LOCATIONS: dict[aomScenarioData, aomLocationData] = {
    location.scenario: location
    for location in TYPE_TO_LOCATIONS.get(aomLocationType.VICTORY, [])
}

# UNUSED: never read outside this module. Kept (commented) — comment claims Rules.py
# uses it but Rules.py iterates TYPE_TO_LOCATIONS directly.
# # scenario → its single COMPLETION event.  Used by Rules.py to place locked
# # event items (used as access flags by downstream rules).
# COMPLETION_LOCATIONS: dict[aomScenarioData, aomLocationData] = {
#     location.scenario: location
#     for location in TYPE_TO_LOCATIONS.get(aomLocationType.COMPLETION, [])
# }



# -----------------------------------------------------------------------
# Shop system
# -----------------------------------------------------------------------
# When the `gem_shop` YAML option is on, the player gains access to a shop
# scenario (APScenarioID 0) where Gems collected from victories can be
# spent at obelisks for items and progressive hints.
#
# Topology:
#   * 4 shop tiers (A=Marsh, B=Desert, C=Grass, D=Hades).
#   * Each tier has N item-obelisks and M hint-obelisks (see SHOP_TIER_CONFIGS).
#   * All 60 item slots (15 per tier) are AP locations that can hold any
#     item.  They are addressable as TIER_ITEM_IDS[tier][index].
#   * 4 hint slots (one per tier) are PROGRESSIVE_INFO locations — locked
#     by Rules.py to ProgressiveShopInfo items.
#
# Slot mapping ↔ XS:
#   `SHOP_SLOT_ORDER` and `SHOP_SLOT_TO_INDEX` produce a 1-indexed slot
#   number that must match `APShopSlotFromIndex` in archipelago.xs.  Don't
#   change the order without updating the XS function.
#
# Adding a tier or shop:
#   * Append a row to SHOP_TIER_CONFIGS.  The tier's obelisks count is
#     consumed by the obelisk-distribution logic in
#     `aomWorld._generate_shop_assignments`.
#   * Reserve more ID space if needed — `SHOP_BASE_ID + 0..59` is items,
#     `+60..63` is progressive info.  Keep new IDs above 3920100 to avoid
#     collision risk with future scenario IDs.
# -----------------------------------------------------------------------

SHOP_BASE_ID = 3920000  # First shop location id; well above any per-scenario id
ITEMS_PER_SHOP = 15     # Number of item-bearing locations per tier

# Tier configs: (internal_name, display_name, item_obelisks, hint_obelisks).
# `item_obelisks` controls how many physical obelisks the editor places at the
# tier (so 15 items get distributed across N obelisks, min 1 each).
# `hint_obelisks` is the number of hint slots — slot 1 is always the
# progressive-info hint; slots 2..N are mission hints chosen at fill time.
SHOP_TIER_CONFIGS = [
    ("A", "Shop A", 6, 3),
    ("B", "Shop B", 4, 3),
    ("C", "Shop C", 3, 2),
    ("D", "Shop D", 2, 1),
]

# Tiers that get a Progressive Shop Info hint slot at HINT_1.  Every shop
# now has a PSI button — Shop A's HINT_1 is PSI; HINT_2..N are mission hints.
PROGRESSIVE_INFO_TIERS: tuple = ("A", "B", "C", "D")

# Slot order — matches APShopSlotFromIndex in archipelago.xs (1-indexed).
# Concatenates all item slots first, then all hint slots.  Editing this list
# REQUIRES updating the XS dispatch function in lock-step.
SHOP_SLOT_ORDER: list[str] = (
    [f"{t}_ITEM_{i}" for t, _, obs, _ in SHOP_TIER_CONFIGS for i in range(1, obs+1)] +
    [f"{t}_HINT_{i}" for t, _, _, hobs in SHOP_TIER_CONFIGS for i in range(1, hobs+1)]
)
# UNUSED: comment claims GameClient.py uses it but no caller exists. Kept (commented).
# # Reverse map: slot string ("A_ITEM_3") → 1-based index.  Consumed by GameClient.py
# # when emitting per-slot assignments to aom_state.xs.
# SHOP_SLOT_TO_INDEX: dict[str, int] = {s: i+1 for i, s in enumerate(SHOP_SLOT_ORDER)}

# Progressive Shop Info location IDs.  Reserves a stable slot for every tier
# at the same offset as before (so older seeds keep working), but only B/C/D
# are actually used; A's slot is intentionally unused since Shop A has no PSI
# button.
_PROGRESSIVE_INFO_IDS_ALL: dict[str, int] = {
    tier: SHOP_BASE_ID + 60 + i + 1
    for i, (tier, *_) in enumerate(SHOP_TIER_CONFIGS)
}
PROGRESSIVE_INFO_IDS: dict[str, int] = {
    tier: _PROGRESSIVE_INFO_IDS_ALL[tier] for tier in PROGRESSIVE_INFO_TIERS
}

# Item location IDs per tier: each tier gets ITEMS_PER_SHOP (15) locations.
# Layout: A=3920001-3920015, B=3920016-3920030, C=3920031-3920045, D=3920046-3920060.
TIER_ITEM_IDS: dict[str, list[int]] = {}
_ptr = SHOP_BASE_ID
for _tier, *_ in SHOP_TIER_CONFIGS:
    TIER_ITEM_IDS[_tier] = list(range(_ptr + 1, _ptr + ITEMS_PER_SHOP + 1))
    _ptr += ITEMS_PER_SHOP

# All shop item location IDs (flat list, 60 total).  Region wiring iterates this.
ALL_SHOP_ITEM_IDS: list[int] = [loc_id for ids in TIER_ITEM_IDS.values() for loc_id in ids]

# All progressive info location IDs (4 total).  Rules.py iterates these to
# install the place_progressive_shop_info forced placements.
ALL_PROGRESSIVE_INFO_IDS: list[int] = list(PROGRESSIVE_INFO_IDS.values())

# Register shop locations in the global lookup tables so AP can look them up
# by display name (just like scenario locations).  Shop locations are NOT
# in `aomLocationData` — they're computed dynamically only when gem_shop is on.
# Item slot display name format: "<tier display>: Item <i>"
for _tier, _display, *_ in SHOP_TIER_CONFIGS:
    for _i, _loc_id in enumerate(TIER_ITEM_IDS[_tier], start=1):
        _name = f"{_display}: Item {_i}"
        location_name_to_id[_name] = _loc_id
        location_id_to_name[_loc_id] = _name

# Progressive info display name format: "<tier display>: Progressive Shop Info"
# Only registered for tiers that actually have a PSI slot (B, C, D).
for _tier, _display, *_ in SHOP_TIER_CONFIGS:
    _loc_id = PROGRESSIVE_INFO_IDS.get(_tier)
    if _loc_id is None:
        continue
    _name   = f"{_display}: Progressive Shop Info"
    location_name_to_id[_name] = _loc_id
    location_id_to_name[_loc_id] = _name

# -----------------------------------------------------------------------
# Shop E — gem sink (4 decks of 12 "cards", revealed top-down).
# Only spawned when the gem pool can afford all of A-D plus all of E.
# Lives in a separate ID range above KEY_DELIVERY (which starts at 3920100).
# -----------------------------------------------------------------------
SHOP_E_BASE_ID            = 3921000
SHOP_E_DECK_COUNT         = 4
SHOP_E_DEFAULT_DECK_DEPTH = 12   # historical default — what the player gets on most seeds
# Cap reserved per deck.  We register a large block of location IDs up front so
# generation can scale Shop E up well past 48 cards when a future seed has very
# many gems (e.g. extra campaigns), without having to thread a new schema.
SHOP_E_MAX_DECK_DEPTH     = 50
SHOP_E_MAX_TOTAL_CARDS    = SHOP_E_DECK_COUNT * SHOP_E_MAX_DECK_DEPTH   # 200

SHOP_E_LOCATION_IDS: list[int] = list(
    range(SHOP_E_BASE_ID, SHOP_E_BASE_ID + SHOP_E_MAX_TOTAL_CARDS)
)
for _i, _loc_id in enumerate(SHOP_E_LOCATION_IDS):
    _name = f"Shop E: Card {_i + 1:03d}"
    location_name_to_id[_name] = _loc_id
    location_id_to_name[_loc_id] = _name


# -----------------------------------------------------------------------
# Key delivery locations — used by the Key Ring system (max_keys_on_keyrings >= 2)
# -----------------------------------------------------------------------
# When a player receives a Key Ring item from the multiworld, the client
# auto-checks the corresponding `Key for ...` location for each scenario the
# ring carries.  Server then delivers each individual Scenario Key item back
# to the player and broadcasts a standard `ItemSend` event, so every player
# in the room sees one chat line per delivered Scenario Key (mirroring how
# the gem shop announces purchases).
#
# IDs start at KEY_DELIVERY_BASE_ID and allocate one slot per scenario in
# `aomScenarioData`.  Locations whose scenario lives in a disabled campaign
# are still registered in the global lookup tables (so id maps stay stable)
# but are NOT added to the region graph in Regions.py.
# -----------------------------------------------------------------------
KEY_DELIVERY_BASE_ID = 3920100  # well above shop ids, below per-scenario ids
KEY_DELIVERY_LOCATION_NAMES: dict[int, str] = {}      # scenario global_number → location name
KEY_DELIVERY_SCENARIO_TO_LOC_ID: dict[int, int] = {}  # scenario global_number → location id
KEY_DELIVERY_LOC_ID_TO_SCENARIO: dict[int, int] = {}  # reverse

def _key_delivery_short_label(scen) -> str:
    """Return the short label used in Key delivery location names.
    FotT campaigns (Greek/Egyptian/Norse/Final, campaign.value 1-4) use the
    scenario's global_number prefixed with 'FotT'.  Other campaigns use the
    campaign mnemonic and the per-campaign chapter."""
    if scen.campaign.value <= 4:
        return f"FotT {scen.global_number}"
    return f"{scen.campaign.mnemonic} {scen.chapter}"

from .Scenarios import aomScenarioData as _ScenForKeys
for _i, _scen in enumerate(_ScenForKeys):
    _kd_id   = KEY_DELIVERY_BASE_ID + _i
    _kd_name = f"Key for {_key_delivery_short_label(_scen)}"
    KEY_DELIVERY_LOCATION_NAMES[_scen.global_number] = _kd_name
    KEY_DELIVERY_SCENARIO_TO_LOC_ID[_scen.global_number] = _kd_id
    KEY_DELIVERY_LOC_ID_TO_SCENARIO[_kd_id] = _scen.global_number
    location_name_to_id[_kd_name] = _kd_id
    location_id_to_name[_kd_id]   = _kd_name

ALL_KEY_DELIVERY_LOC_IDS: list[int] = list(KEY_DELIVERY_LOC_ID_TO_SCENARIO.keys())

