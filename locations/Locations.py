import enum

from .Scenarios import aomScenarioData
from ..items.Items import BASE_ID


class aomLocationType(enum.Flag):
    VICTORY    = enum.auto()
    COMPLETION = enum.auto()
    OBJECTIVE  = enum.auto()


def global_location_id(scenario_id: int, local_location_id: int) -> int:
    # Apply BASE_ID offset so location IDs are globally unique in the AP namespace.
    return BASE_ID + scenario_id * 100 + local_location_id


class aomLocationData(enum.IntEnum):
    def __new__(cls, id: int, *args, **kwargs):
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
        self.id = id
        self.location_name = location_name
        self.scenario = scenario
        self.type = type

    def global_name(self) -> str:
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
        "Bring all three Osiris pieces to the Obelisk.",
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




# -----------------------------------------------------------------------
# Special meta-location: "The Way to Atlantis"
# This location lives in the Menu region (not inside any scenario).
# In beat_x_scenarios mode, the Atlantis Key is locked here and the
# location requires X scenario completions to access.
# In other modes, this is a regular free location.
# -----------------------------------------------------------------------
WAY_TO_ATLANTIS_LOCATION_ID   = BASE_ID + 99000
WAY_TO_ATLANTIS_LOCATION_NAME = "The Way to Atlantis"

location_from_id: dict[int, aomLocationData] = {
    location.id: location for location in aomLocationData
}

location_name_to_id: dict[str, int] = {
    location.global_name(): location.id for location in aomLocationData
}

location_id_to_name: dict[int, str] = {
    location.id: location.global_name() for location in aomLocationData
}

SCENARIO_TO_LOCATIONS: dict[aomScenarioData, list[aomLocationData]] = {
    scenario: [] for scenario in aomScenarioData
}
for location in aomLocationData:
    SCENARIO_TO_LOCATIONS[location.scenario].append(location)

REGION_TO_LOCATIONS: dict[aomScenarioData, list[aomLocationData]] = {}
for location in aomLocationData:
    REGION_TO_LOCATIONS.setdefault(location.scenario, []).append(location)

TYPE_TO_LOCATIONS: dict[aomLocationType, list[aomLocationData]] = {}
for location in aomLocationData:
    TYPE_TO_LOCATIONS.setdefault(location.type, []).append(location)

VICTORY_LOCATIONS: dict[aomScenarioData, aomLocationData] = {
    location.scenario: location
    for location in TYPE_TO_LOCATIONS.get(aomLocationType.VICTORY, [])
}

COMPLETION_LOCATIONS: dict[aomScenarioData, aomLocationData] = {
    location.scenario: location
    for location in TYPE_TO_LOCATIONS.get(aomLocationType.COMPLETION, [])
}

# Register the special meta-location in the global lookup tables
location_name_to_id[WAY_TO_ATLANTIS_LOCATION_NAME] = WAY_TO_ATLANTIS_LOCATION_ID
location_id_to_name[WAY_TO_ATLANTIS_LOCATION_ID]   = WAY_TO_ATLANTIS_LOCATION_NAME


# -----------------------------------------------------------------------
# Shop system (redesigned)
# -----------------------------------------------------------------------

# This will be appended to Locations.py to replace the old shop section

SHOP_BASE_ID = 3920000
ITEMS_PER_SHOP = 15

# Tier configs: (internal_name, display_name, item_obelisks, hint_obelisks)
SHOP_TIER_CONFIGS = [
    ("A", "Marsh Shop",  5, 4),
    ("B", "Desert Shop", 4, 3),
    ("C", "Grass Shop",  3, 2),
    ("D", "Hades Shop",  2, 1),
]

# Slot order — matches APShopSlotFromIndex in archipelago.xs (1-indexed)
SHOP_SLOT_ORDER: list[str] = (
    [f"{t}_ITEM_{i}" for t, _, obs, _ in SHOP_TIER_CONFIGS for i in range(1, obs+1)] +
    [f"{t}_HINT_{i}" for t, _, _, hobs in SHOP_TIER_CONFIGS for i in range(1, hobs+1)]
)
SHOP_SLOT_TO_INDEX: dict[str, int] = {s: i+1 for i, s in enumerate(SHOP_SLOT_ORDER)}

# Progressive Shop Info location IDs — one per shop tier, after the 60 item locations
PROGRESSIVE_INFO_IDS: dict[str, int] = {
    tier: SHOP_BASE_ID + 60 + i + 1
    for i, (tier, *_) in enumerate(SHOP_TIER_CONFIGS)
}  # Marsh→3920061, Desert→3920062, Grass→3920063, Hades→3920064

# Item location IDs per tier: each tier gets ITEMS_PER_SHOP locations
TIER_ITEM_IDS: dict[str, list[int]] = {}
_ptr = SHOP_BASE_ID
for _tier, *_ in SHOP_TIER_CONFIGS:
    TIER_ITEM_IDS[_tier] = list(range(_ptr + 1, _ptr + ITEMS_PER_SHOP + 1))
    _ptr += ITEMS_PER_SHOP

# All shop item location IDs (flat list, 60 total)
ALL_SHOP_ITEM_IDS: list[int] = [loc_id for ids in TIER_ITEM_IDS.values() for loc_id in ids]

# All progressive info location IDs (4 total)
ALL_PROGRESSIVE_INFO_IDS: list[int] = list(PROGRESSIVE_INFO_IDS.values())

# Register all shop locations in the global lookup tables
# Item locations
for _tier, _display, *_ in SHOP_TIER_CONFIGS:
    for _i, _loc_id in enumerate(TIER_ITEM_IDS[_tier], start=1):
        _name = f"{_display}: Item {_i}"
        location_name_to_id[_name] = _loc_id
        location_id_to_name[_loc_id] = _name

# Progressive Info locations
for _tier, _display, *_ in SHOP_TIER_CONFIGS:
    _loc_id = PROGRESSIVE_INFO_IDS[_tier]
    _name   = f"{_display}: Progressive Shop Info"
    location_name_to_id[_name] = _loc_id
    location_id_to_name[_loc_id] = _name

