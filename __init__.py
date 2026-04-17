# world/aom/__init__.py

from __future__ import annotations

import logging
import time
from typing import Any, ClassVar, Mapping

import settings
from BaseClasses import Item, ItemClassification
try:
    from Options import OptionGroup
except ImportError:
    OptionGroup = None
from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, Type, components, launch as launch_subprocess
import worlds.LauncherComponents as components_module

from .Options import (Random_Major_Gods, ForceDifferentGod, MythUnitSanity, ExtraFinalMissionAgeUnlocks, 
    AomOptions,
    FinalScenarios,
    HeroAbilities,
    StartingScenarios,
    StartingGreekAgeUnlocks,
    StartingEgyptianAgeUnlocks,
    StartingNorseAgeUnlocks,
    XScenarios,
)
from .items import Items
from .locations import Campaigns, Locations
from .regions import Regions
from .rules import Rules

logger = logging.getLogger(__name__)

AOMR = "Age Of Mythology Retold"


class AoMSettings(settings.Group):
    class UserDirectory(settings.UserFolderPath):
        """The user's local Age Of Mythology Retold user folder."""
        description = "Age Of Mythology Retold User Directory"

    user_folder: UserDirectory = UserDirectory(AOMR)


class aomWebWorld(WebWorld):
    """Web settings and YAML template configuration for Age of Mythology Retold."""
    icon = "worlds/aom/aom_icon.png"
    option_groups = [
        OptionGroup("Starting Setup", [
            StartingScenarios,
            StartingGreekAgeUnlocks,
            StartingEgyptianAgeUnlocks,
            StartingNorseAgeUnlocks,
        ]),
        OptionGroup("Final Section", [
            FinalScenarios,
            XScenarios,
        ]),
        OptionGroup("Item Pool", [
            ExtraFinalMissionAgeUnlocks,
            HeroAbilities,
        ]),
    ] if OptionGroup is not None else []



# ---------------------------------------------------------------------------
# Random_Major_Gods — vanilla god per scenario and civ groupings
# ---------------------------------------------------------------------------
_VANILLA_GODS: dict = {
    1: 2, 2: 2, 3: 2, 4: 2,               # Poseidon
    5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,  # Zeus
    11: 4, 12: 5, 13: 6, 14: 4, 15: 4,    # Isis, Ra, Set
    16: 3,                                  # Hades
    17: 5, 18: 5, 19: 4, 20: 4,            # Ra, Isis
    21: 1,                                  # Zeus
    22: 8, 23: 8,                           # Thor
    24: 9, 25: 9,                           # Loki
    26: 7, 27: 7, 28: 7,                    # Odin
    29: 8, 30: 8,                           # Thor
    31: 1, 32: 1,                           # Zeus
}
_GREEK_GODS      = frozenset({1, 2, 3})
_EGYPTIAN_GODS   = frozenset({4, 5, 6})
_NORSE_GODS      = frozenset({7, 8, 9})
_ATLANTEAN_GODS  = frozenset({10, 11, 12})  # Kronos, Oranos, Gaia
_ALL_GODS        = _GREEK_GODS | _EGYPTIAN_GODS | _NORSE_GODS
_ALL_GODS_WITH_ATLANTIS = _ALL_GODS | _ATLANTEAN_GODS
_GOD_NAMES     = {
    1: "Zeus",   2: "Poseidon", 3: "Hades",
    4: "Isis",   5: "Ra",       6: "Set",
    7: "Odin",   8: "Thor",     9: "Loki",
    10: "Kronos", 11: "Oranos", 12: "Gaia",
}

def _civ_of_god(god: int) -> frozenset:
    if god in _GREEK_GODS:     return _GREEK_GODS
    if god in _EGYPTIAN_GODS:  return _EGYPTIAN_GODS
    if god in _ATLANTEAN_GODS: return _ATLANTEAN_GODS
    return _NORSE_GODS

def _civ_of_god_name(god: int) -> str:
    if god in _GREEK_GODS:     return "Greek"
    if god in _EGYPTIAN_GODS:  return "Egyptian"
    if god in _ATLANTEAN_GODS: return "Atlantean"
    return "Norse"


# ---------------------------------------------------------------------------
# Random_Major_Gods — minor god tech choices per (major_god_id, age_tier)
# Each entry lists [option_A, option_B]; one is chosen randomly at generation.
# age_tier: 1=Classical 2=Heroic 3=Mythic
# ---------------------------------------------------------------------------
_MINOR_GOD_TECHS: dict[tuple, list] = {
    (1,1): ["cTechClassicalAgeAthena",  "cTechClassicalAgeHermes"],
    (1,2): ["cTechHeroicAgeApollo",     "cTechHeroicAgeDionysus"],
    (1,3): ["cTechMythicAgeHera",       "cTechMythicAgeHephaestus"],
    (2,1): ["cTechClassicalAgeHermes",  "cTechClassicalAgeAres"],
    (2,2): ["cTechHeroicAgeDionysus",   "cTechHeroicAgeAphrodite"],
    (2,3): ["cTechMythicAgeHephaestus", "cTechMythicAgeArtemis"],
    (3,1): ["cTechClassicalAgeAthena",  "cTechClassicalAgeAres"],
    (3,2): ["cTechHeroicAgeApollo",     "cTechHeroicAgeAphrodite"],
    (3,3): ["cTechMythicAgeHera",       "cTechMythicAgeArtemis"],
    (4,1): ["cTechClassicalAgeAnubis",  "cTechClassicalAgePtah"],
    (4,2): ["cTechHeroicAgeSobek",      "cTechHeroicAgeNephthys"],
    (4,3): ["cTechMythicAgeHorus",      "cTechMythicAgeThoth"],
    (5,1): ["cTechClassicalAgeBast",    "cTechClassicalAgePtah"],
    (5,2): ["cTechHeroicAgeSekhmet",    "cTechHeroicAgeSobek"],
    (5,3): ["cTechMythicAgeOsiris",     "cTechMythicAgeHorus"],
    (6,1): ["cTechClassicalAgeAnubis",  "cTechClassicalAgeBast"],
    (6,2): ["cTechHeroicAgeSekhmet",    "cTechHeroicAgeNephthys"],
    (6,3): ["cTechMythicAgeOsiris",     "cTechMythicAgeThoth"],
    (7,1): ["cTechClassicalAgeFreyja",  "cTechClassicalAgeHeimdall"],
    (7,2): ["cTechHeroicAgeNjord",      "cTechHeroicAgeSkadi"],
    (7,3): ["cTechMythicAgeBaldr",      "cTechMythicAgeTyr"],
    (8,1): ["cTechClassicalAgeFreyja",  "cTechClassicalAgeForseti"],
    (8,2): ["cTechHeroicAgeBragi",      "cTechHeroicAgeSkadi"],
    (8,3): ["cTechMythicAgeBaldr",      "cTechMythicAgeTyr"],
    (9,1): ["cTechClassicalAgeForseti", "cTechClassicalAgeHeimdall"],
    (9,2): ["cTechHeroicAgeBragi",      "cTechHeroicAgeNjord"],
    (9,3): ["cTechMythicAgeTyr",        "cTechMythicAgeHel"],
    (10,1): ["cTechClassicalAgePrometheus", "cTechClassicalAgeLeto"],
    (10,2): ["cTechHeroicAgeHyperion",      "cTechHeroicAgeRheia"],
    (10,3): ["cTechMythicAgeHelios",        "cTechMythicAgeAtlas"],
    (11,1): ["cTechClassicalAgePrometheus", "cTechClassicalAgeOceanus"],
    (11,2): ["cTechHeroicAgeHyperion",      "cTechHeroicAgeTheia"],
    (11,3): ["cTechMythicAgeHelios",        "cTechMythicAgeHekate"],
    (12,1): ["cTechClassicalAgeLeto",       "cTechClassicalAgeOceanus"],
    (12,2): ["cTechHeroicAgeRheia",         "cTechHeroicAgeTheia"],
    (12,3): ["cTechMythicAgeAtlas",         "cTechMythicAgeHekate"],
}

_AGE_BASE_TECHS: dict[str, dict] = {
    "Greek":     {1:"cTechClassicalAgeGreek",     2:"cTechHeroicAgeGreek",     3:"cTechMythicAgeGreek"},
    "Egyptian":  {1:"cTechClassicalAgeEgyptian",  2:"cTechHeroicAgeEgyptian",  3:"cTechMythicAgeEgyptian"},
    "Norse":     {1:"cTechClassicalAgeNorse",     2:"cTechHeroicAgeNorse",     3:"cTechMythicAgeNorse"},
    "Atlantean": {1:"cTechClassicalAgeAtlantean", 2:"cTechHeroicAgeAtlantean", 3:"cTechMythicAgeAtlantean"},
}

_SCENARIO_STARTING_AGE: dict[int, int] = {
    1:1, 2:0, 3:0, 10:0, 11:0, 12:0, 21:0, 22:0, 25:1,
    4:1, 8:1, 15:1, 18:1, 23:1, 24:1, 26:1, 27:1, 29:1, 30:1,
    5:2, 6:2, 7:2, 13:2, 14:2, 17:2, 19:2, 20:2, 28:2, 31:2, 32:2,
    9:3, 16:3,
}


# Vanilla minor god tech assignments per scenario (for non-random_major_gods runs).
# Includes base age tech + chosen minor god tech, in order: Classical, Heroic, Mythic.
_VANILLA_MINOR_GOD_TECHS: dict[int, list] = {
    1:  ["cTechClassicalAgeGreek",    "cTechClassicalAgeHermes"],
    4:  ["cTechClassicalAgeGreek",    "cTechClassicalAgeHermes"],
    5:  ["cTechClassicalAgeGreek",    "cTechClassicalAgeAthena",
         "cTechHeroicAgeGreek",       "cTechHeroicAgeDionysus"],
    6:  ["cTechClassicalAgeGreek",    "cTechClassicalAgeAthena"],
    7:  ["cTechClassicalAgeGreek",    "cTechClassicalAgeHermes",
         "cTechHeroicAgeGreek",       "cTechHeroicAgeDionysus"],
    8:  ["cTechClassicalAgeGreek",    "cTechClassicalAgeAthena"],
    9:  ["cTechClassicalAgeGreek",    "cTechClassicalAgeAthena",
         "cTechHeroicAgeGreek",       "cTechHeroicAgeDionysus",
         "cTechMythicAgeGreek",       "cTechMythicAgeHera"],
    13: ["cTechClassicalAgeEgyptian", "cTechClassicalAgeAnubis",
         "cTechHeroicAgeEgyptian",    "cTechHeroicAgeNephthys"],
    14: ["cTechClassicalAgeEgyptian", "cTechClassicalAgeBast",
         "cTechHeroicAgeEgyptian",    "cTechHeroicAgeSobek"],
    15: ["cTechClassicalAgeEgyptian", "cTechClassicalAgeAnubis"],
    16: ["cTechClassicalAgeGreek",    "cTechClassicalAgeAres",
         "cTechHeroicAgeGreek",       "cTechHeroicAgeAphrodite",
         "cTechMythicAgeGreek",       "cTechMythicAgeArtemis"],
    17: ["cTechClassicalAgeEgyptian", "cTechClassicalAgeBast",
         "cTechHeroicAgeEgyptian",    "cTechHeroicAgeSekhmet"],
    18: ["cTechClassicalAgeEgyptian", "cTechClassicalAgeBast"],
    19: ["cTechClassicalAgeEgyptian", "cTechClassicalAgeBast",
         "cTechHeroicAgeEgyptian",    "cTechHeroicAgeSobek"],
    20: ["cTechClassicalAgeEgyptian", "cTechClassicalAgeBast",
         "cTechHeroicAgeEgyptian",    "cTechHeroicAgeNephthys"],
    23: ["cTechClassicalAgeNorse",    "cTechClassicalAgeFreyja"],
    24: ["cTechClassicalAgeNorse",    "cTechClassicalAgeForseti"],
    25: ["cTechClassicalAgeNorse",    "cTechClassicalAgeForseti"],
    26: ["cTechClassicalAgeNorse",    "cTechClassicalAgeHeimdall"],
    27: ["cTechClassicalAgeNorse",    "cTechClassicalAgeFreyja"],
    28: ["cTechClassicalAgeNorse",    "cTechClassicalAgeFreyja",
         "cTechHeroicAgeNorse",       "cTechHeroicAgeSkadi"],
    29: ["cTechClassicalAgeNorse",    "cTechClassicalAgeForseti"],
    30: ["cTechClassicalAgeNorse",    "cTechClassicalAgeForseti"],
    31: ["cTechClassicalAgeGreek",    "cTechClassicalAgeAthena",
         "cTechHeroicAgeGreek",       "cTechHeroicAgeApollo"],
    32: ["cTechClassicalAgeGreek",    "cTechClassicalAgeAthena",
         "cTechHeroicAgeGreek",       "cTechHeroicAgeDionysus"],
}


# ---------------------------------------------------------------------------
# Archaic-age units enabled by the scenario editor per vanilla god/civ.
# These need to be explicitly forbidden if the assigned god differs.
# ---------------------------------------------------------------------------

# Units specific to a particular Greek major god (not available to other Greek gods)
_GOD_SPECIFIC_ARCHAIC_UNITS: dict[int, list] = {
    1: ["Jason"],    # Zeus
    2: ["Theseus"],  # Poseidon
    3: ["Ajax"],     # Hades
}

# Civ-wide archaic units (available for any major god of that civ)
_CIV_ARCHAIC_UNITS: dict[str, list] = {
    "Greek":     ["Pegasus", "VillagerGreek"],
    "Egyptian":  ["Mercenary", "Priest", "Pharaoh", "VillagerEgyptian"],
    "Norse":     ["Berserk", "Hersir", "VillagerDwarf", "VillagerNorse"],
    "Atlantean": ["Oracle", "VillagerAtlantean"],
}

def _compute_archaic_forbids(vanilla_god_id: int, assigned_god_id: int) -> list:
    """Returns the list of proto unit names to forbid when the assigned god
    differs from the vanilla god."""
    vanilla_civ  = _civ_of_god_name(vanilla_god_id)
    assigned_civ = _civ_of_god_name(assigned_god_id)
    forbid: list = []

    # Forbid vanilla god-specific units if god changed
    if assigned_god_id != vanilla_god_id:
        forbid.extend(_GOD_SPECIFIC_ARCHAIC_UNITS.get(vanilla_god_id, []))

    # Forbid all vanilla civ-wide archaic units if civ changed
    if assigned_civ != vanilla_civ:
        forbid.extend(_CIV_ARCHAIC_UNITS.get(vanilla_civ, []))

    return forbid

class aomWorld(World):
    web = aomWebWorld()
    """
    Age of Mythology Retold — Fall of the Trident Archipelago world.

    32 scenarios across Greek, Egyptian, Norse, and Final campaign sections.
    Sections unlock independently. Each scenario has its own age and point
    requirements. Beat scenarios to earn items and advance toward Atlantis.
    """

    game = AOMR
    settings: ClassVar[type[AoMSettings]] = AoMSettings
    options_dataclass = AomOptions
    options: AomOptions
    topology_present = True

    item_names = set(item.item_name for item in Items.aomItemData)
    location_names = (
        set(location.global_name() for location in Locations.aomLocationData)
        | {Locations.WAY_TO_ATLANTIS_LOCATION_NAME}
    )

    item_name_to_id = Items.item_name_to_id
    item_id_to_name = Items.item_id_to_name
    location_name_to_id = Locations.location_name_to_id
    location_id_to_name = Locations.location_id_to_name

    def create_regions(self) -> None:
        Regions.create_regions(self.multiworld, self.player)

    def _starting_campaign(self) -> Campaigns.aomCampaignData:
        value = int(self.options.starting_scenarios.value)
        mapping = {
            StartingScenarios.option_greek:    Campaigns.aomCampaignData.FOTT_GREEK,
            StartingScenarios.option_egyptian: Campaigns.aomCampaignData.FOTT_EGYPTIAN,
            StartingScenarios.option_norse:    Campaigns.aomCampaignData.FOTT_NORSE,
        }
        return mapping.get(value, Campaigns.aomCampaignData.FOTT_GREEK)

    def _final_mode(self) -> int:
        return int(self.options.final_scenarios.value)

    def create_item(self, name: str) -> Item:
        item = Items.NAME_TO_ITEM[name]
        return Item(
            item.item_name,
            Items.item_type_to_classification[item.type_data],
            item.id,
            self.player,
        )

    def get_filler_item_name(self) -> str:
        return self.random.choice([item.item_name for item in Items.filler_items])

    def generate_early(self) -> None:
        if self.options.random_major_gods:
            self.god_assignments: dict[int, int] = self._generate_god_assignments()
        else:
            self.god_assignments = {}
        self.minor_god_assignments: dict[int, list] = self._generate_minor_god_assignments()
        self.archaic_forbids: dict[int, list]       = self._generate_archaic_forbids()
        # Shop generation (only when gem_shop is enabled)
        self.gem_shop_enabled: bool = bool(self.options.gem_shop.value)
        if self.gem_shop_enabled:
            self.shop_obelisk_assignments, self.shop_progression_slots, self.shop_filler_only = (
                self._generate_shop_assignments()
            )
        else:
            self.shop_obelisk_assignments = {}
            self.shop_progression_slots   = {}
            self.shop_filler_only         = set()



    def _generate_shop_assignments(self) -> tuple:
        """
        Randomly distributes 60 shop items across 14 obelisks (15 per shop).
        Exactly 1 progression slot per shop. ~half of remaining slots are filler-only.
        Returns (obelisk_assignments, progression_slots, filler_only_locations).
        """
        from .locations.Locations import SHOP_TIER_CONFIGS, TIER_ITEM_IDS, ITEMS_PER_SHOP
        assignments: dict[str, list[int]] = {}
        progression_slots: dict[str, int] = {}
        filler_only_locs: set[int] = set()

        for tier_name, _display, item_obs, _hint_obs in SHOP_TIER_CONFIGS:
            locs = list(TIER_ITEM_IDS[tier_name])  # 15 location IDs for this tier
            self.random.shuffle(locs)

            # locs[0] is the one progression-allowed slot (after shuffle = random)
            progression_slots[tier_name] = locs[0]

            # Of the remaining 14, randomly pick ~half to be filler-only
            non_prog = locs[1:]
            n_filler_only = round(len(non_prog) * 0.8)  # ~11 of 14
            filler_only_locs.update(self.random.sample(non_prog, n_filler_only))

            # Distribute 15 items across item_obs obelisks, min 1 each
            counts = self._random_distribute(ITEMS_PER_SHOP, item_obs)
            self.random.shuffle(counts)

            ptr = 0
            for i, count in enumerate(counts, start=1):
                obelisk_id = f"{tier_name}_ITEM_{i}"
                assignments[obelisk_id] = locs[ptr:ptr + count]
                ptr += count

        return assignments, progression_slots, filler_only_locs

    def _random_distribute(self, total: int, bins: int) -> list:
        """Distribute total items across bins, minimum 1 per bin."""
        counts = [1] * bins
        for _ in range(total - bins):
            counts[self.random.randrange(bins)] += 1
        return counts

    def _generate_god_assignments(self) -> dict[int, int]:
        """Randomly assign a major god to each scenario using the world seed."""
        force = bool(self.options.force_different_god.value)
        assignments: dict[int, int] = {}
        for scenario_id in range(1, 33):
            vanilla = _VANILLA_GODS[scenario_id]
            if force:
                if self.random.random() < 0.5:
                    candidates = list(_ALL_GODS_WITH_ATLANTIS - _civ_of_god(vanilla))
                else:
                    candidates = list(_ALL_GODS_WITH_ATLANTIS - {vanilla})
            else:
                candidates = list(_ALL_GODS_WITH_ATLANTIS)
            assignments[scenario_id] = self.random.choice(candidates)
        return assignments

    def _log_god_assignments(self, assignments: dict[int, int]) -> None:
        from .locations.Scenarios import aomScenarioData
        lines = ["Random_Major_Gods god assignments:"]
        for scenario in aomScenarioData:
            n   = scenario.global_number
            god = _GOD_NAMES.get(assignments.get(n, 0), "Unknown")
            lines.append(f"  {scenario.display_name}: {god}")
        logger.info("\n".join(lines))

    def _generate_archaic_forbids(self) -> dict[int, list]:
        """Returns {scenario_id: [unit_name, ...]} of units to forbid at
        scenario start because they belong to the vanilla god/civ but the
        assigned god is different."""
        result: dict[int, list] = {}
        for scenario_id in range(1, 33):
            vanilla_god  = _VANILLA_GODS[scenario_id]
            assigned_god = self.god_assignments.get(scenario_id, vanilla_god)
            forbids      = _compute_archaic_forbids(vanilla_god, assigned_god)
            if forbids:
                result[scenario_id] = forbids
        return result

    def _generate_minor_god_assignments(self) -> dict[int, list]:
        """
        Returns {scenario_id: [tech_const, ...]} listing age techs to activate
        at scenario start, in order (Classical base, Classical minor, Heroic base...).

        When random_major_gods is on: picks randomly from valid minor gods for the
        assigned major god up to the scenario's starting age.
        When random_major_gods is off: uses the vanilla campaign minor god table.
        """
        if not self.options.random_major_gods:
            return dict(_VANILLA_MINOR_GOD_TECHS)

        result: dict[int, list] = {}
        for scenario_id in range(1, 33):
            god_id       = self.god_assignments.get(scenario_id, _VANILLA_GODS[scenario_id])
            starting_age = _SCENARIO_STARTING_AGE[scenario_id]
            god_civ      = _civ_of_god_name(god_id)
            techs: list  = []
            for tier in range(1, starting_age + 1):
                base = _AGE_BASE_TECHS[god_civ].get(tier)
                if base:
                    techs.append(base)
                options = _MINOR_GOD_TECHS.get((god_id, tier), [])
                if options:
                    techs.append(self.random.choice(options))
            if techs:
                result[scenario_id] = techs
        return result

    def create_items(self) -> None:
        """
        Build the item pool.

        Pool tiers (in order):
        1. Progression items — section unlocks, age unlocks, unit progression
        2. Atlantis Key — always in pool unless beat_x mode (where it is locked
           to "The Way to Atlantis" by Rules.py and not counted here)
        3. Useful items — round-robined evenly across types
        4. Filler items — pad any remaining slots; also absorbs items removed
           by options (starting age unlocks, hero abilities disabled)

        Starting age unlocks and the starting section are precollected and do
        not occupy location slots. Hero abilities items are skipped entirely
        when hero_abilities is disabled; dynamic filler padding covers the gap.
        """
        start_campaign = self._starting_campaign()
        final_mode     = self._final_mode()

        hero_abilities_on = bool(self.options.hero_abilities.value)
        hero_ability_types = (Items.HeroSpecialEffect, Items.HeroActionBoost, Items.ArkantosHousing)
        myth_unit_types    = (Items.MythUnitUnlockProgression, Items.MythUnitUnlockUseful,
                               Items.MythUnitUnlockFiller, Items.AtlanteanMythUnitUnlock)
        atlantean_types    = (Items.AtlanteanUnitUnlockProgression, Items.AtlanteanUnitUnlockUseful,
                               Items.AtlanteanMythUnitUnlock)
        myth_unit_sanity_on = bool(self.options.myth_unit_sanity.value)
        random_major_gods_on        = bool(self.options.random_major_gods.value)

        # How many age unlocks to precollect per civ
        starting_age_unlocks = {
            "Greek":     int(self.options.starting_greek_age_unlocks.value),
            "Egyptian":  int(self.options.starting_egyptian_age_unlocks.value),
            "Norse":     int(self.options.starting_norse_age_unlocks.value),
            "Atlantean": 0,  # no starting Atlantean unlocks option
        }
        age_unlock_counts: dict[str, int] = {"Greek": 0, "Egyptian": 0, "Norse": 0}

        progression_pool: list[Item] = []
        useful_groups: dict[type, list[str]] = {}
        filler_groups: dict[type, list[str]] = {}

        for item in Items.aomItemData:
            item_type = item.type_data
            classification = Items.item_type_to_classification[item_type]

            # Victory, Gem, and ProgressiveShopInfo are locked to specific locations by Rules.py.
            if item_type in (Items.Victory, Items.Gem, Items.ProgressiveShopInfo):
                continue
            if item_type == Items.Trap or (isinstance(item_type, type) and issubclass(item_type, Items.Trap)):
                continue  # traps placed via trap_count option below

            # Section unlock items
            if item_type == Items.Campaign:
                if item.type.vanilla_campaign == Campaigns.aomCampaignData.FOTT_FINAL:
                    continue  # Final section has no Campaign item
                ap_item = self.create_item(item.item_name)
                if item.type.vanilla_campaign == start_campaign:
                    self.multiworld.push_precollected(ap_item)
                else:
                    progression_pool.append(ap_item)
                continue

            # Atlantis Key — always in pool EXCEPT in beat_x mode where Rules.py
            # locks it to "The Way to Atlantis" (which is excluded from pool math)
            if item_type == Items.FinalUnlock:
                if final_mode != FinalScenarios.option_beat_x_scenarios:
                    progression_pool.append(self.create_item(item.item_name))
                continue

            # Age unlock items — add 3 base copies per civ + extras for Greek
            # Each civ has exactly one AgeUnlock item now; create_items adds
            # multiple copies explicitly rather than via the enum.
            if item_type == Items.AgeUnlock:
                continue  # handled explicitly below after the item loop

            # Hero ability items — skip if disabled; filler padding covers the gap
            if isinstance(item.type, hero_ability_types) and not hero_abilities_on:
                continue

            # Myth unit items — skip if myth_unit_sanity is off
            if isinstance(item.type, myth_unit_types) and not myth_unit_sanity_on:
                continue

            # Atlantean items — skip if random_major_gods is off (Atlantis not in the pool)
            if isinstance(item.type, atlantean_types) and not random_major_gods_on:
                continue

            # All remaining items bucketed by classification
            if classification == ItemClassification.progression:
                progression_pool.append(self.create_item(item.item_name))
            elif classification == ItemClassification.useful:
                useful_groups.setdefault(item_type, []).append(item.item_name)
            elif classification == ItemClassification.filler:
                filler_groups.setdefault(item_type, []).append(item.item_name)
            else:
                raise ValueError(
                    f"Unhandled classification for {item.item_name}: {classification}"
                )

        # Age unlock items — 3 base copies per civ, precollecting starting unlocks
        # Extra copies go to whichever civ is assigned to scenario 32
        extra_final = int(self.options.extra_final_mission_age_unlocks.value)
        scen32_god = self.god_assignments.get(32, 1) if self.god_assignments else 1
        if scen32_god in (1, 2, 3):       # Greek
            greek_extra, egyptian_extra, norse_extra, atlantean_extra = extra_final, 0, 0, 0
        elif scen32_god in (4, 5, 6):     # Egyptian
            greek_extra, egyptian_extra, norse_extra, atlantean_extra = 0, extra_final, 0, 0
        elif scen32_god in (10, 11, 12):  # Atlantean
            greek_extra, egyptian_extra, norse_extra, atlantean_extra = 0, 0, 0, extra_final
        else:                              # Norse
            greek_extra, egyptian_extra, norse_extra, atlantean_extra = 0, 0, extra_final, 0
        age_unlock_config = [
            (Items.aomItemData.GREEK_AGE_UNLOCK,    "Greek",    3 + greek_extra),
            (Items.aomItemData.EGYPTIAN_AGE_UNLOCK, "Egyptian", 3 + egyptian_extra),
            (Items.aomItemData.NORSE_AGE_UNLOCK,    "Norse",    3 + norse_extra),
        ]
        # Atlantean age unlocks only added when random_major_gods is on
        if random_major_gods_on:
            age_unlock_config.append(
                (Items.aomItemData.ATLANTEAN_AGE_UNLOCK, "Atlantean", 3 + atlantean_extra)
            )
        for item_data, culture, count in age_unlock_config:
            precollect_n = starting_age_unlocks[culture]
            for i in range(count):
                ap_item = self.create_item(item_data.item_name)
                if i < precollect_n:
                    self.multiworld.push_precollected(ap_item)
                else:
                    progression_pool.append(ap_item)

        # Visible location count:
        #   Campaign non-COMPLETION locations minus all 32 Victory locations
        #   Plus shop locations if gem_shop is enabled (60 item + 4 progressive info)
        #   Plus "The Way to Atlantis" when key is in pool (added below)
        gem_shop_on = self.gem_shop_enabled
        visible_location_count = (
            sum(1 for loc in Locations.aomLocationData
                if loc.type != Locations.aomLocationType.COMPLETION)
            - 32  # all Victory locations are locked (31 Gems + 1 Victory item)
        )
        if gem_shop_on:
            visible_location_count += len(Locations.ALL_SHOP_ITEM_IDS)           # 60
            visible_location_count += len(Locations.ALL_PROGRESSIVE_INFO_IDS)    # 4

        if final_mode != FinalScenarios.option_beat_x_scenarios:
            visible_location_count += 1  # Way to Atlantis is a free fill slot

        if len(progression_pool) > visible_location_count:
            raise ValueError(
                f"Progression pool ({len(progression_pool)} items) exceeds "
                f"visible location count ({visible_location_count})."
            )

        # Trap cycle — all 12 trap types, repeated indefinitely when drawing traps
        # Deck-of-cards trap pool: cycle through all trap types in shuffled order,
        # never repeating a type until all have been used once.
        # Types 5 (Spawn Units) and 6 (Transform Drops) excluded until implemented.
        _trap_deck_base = [
            Items.aomItemData.TRAP_METEOR.item_name,
            # Items.aomItemData.TRAP_LIGHTNING_STORM.item_name,  # disabled: fails to cast
            # Items.aomItemData.TRAP_LOCUST_SWARM.item_name,  # disabled: buggy
            Items.aomItemData.TRAP_BOLT.item_name,
            Items.aomItemData.TRAP_RESTORATION.item_name,
            Items.aomItemData.TRAP_CITADEL.item_name,
            Items.aomItemData.TRAP_TORNADO.item_name,
            Items.aomItemData.TRAP_EARTHQUAKE.item_name,
            Items.aomItemData.TRAP_CURSE.item_name,
            Items.aomItemData.TRAP_PLAGUE_SERPENTS.item_name,
            Items.aomItemData.TRAP_IMPLODE.item_name,
            Items.aomItemData.TRAP_TARTARIAN_GATE.item_name,
            Items.aomItemData.TRAP_CHAOS.item_name,
            Items.aomItemData.TRAP_TRAITOR.item_name,
            # Items.aomItemData.TRAP_CARNIVORA.item_name,  # disabled: buggy
            # Items.aomItemData.TRAP_SPIDER_LAIR.item_name,  # disabled: buggy
            Items.aomItemData.TRAP_DECONSTRUCTION.item_name,
            Items.aomItemData.TRAP_FIMBULWINTER.item_name,
            # Items.aomItemData.TRAP_FLAMING_WEAPONS.item_name,  # disabled: fails to cast
            Items.aomItemData.TRAP_ANCESTORS.item_name,
            Items.aomItemData.TRAP_PESTILENCE.item_name,
            Items.aomItemData.TRAP_BRONZE.item_name,
            Items.aomItemData.TRAP_ECLIPSE.item_name,
        ]
        # Build infinite deck: reshuffle each time a full cycle completes
        _trap_deck: list[str] = []
        def _next_trap() -> str:
            nonlocal _trap_deck
            if not _trap_deck:
                _trap_deck = list(_trap_deck_base)
                self.random.shuffle(_trap_deck)
            return _trap_deck.pop()

        trap_pct = int(self.options.trap_percentage.value)  # 0-100

        # Flatten useful and filler into shuffled lists
        all_useful  = [n for names in useful_groups.values() for n in names]
        all_filler  = [n for names in filler_groups.values() for n in names]
        all_filler_inf = [
            item.item_name for item in Items.aomItemData
            if Items.item_type_to_classification[item.type_data] == ItemClassification.filler
        ]
        self.random.shuffle(all_useful)
        self.random.shuffle(all_filler)
        self.random.shuffle(all_filler_inf)

        # Fill remaining slots with 1:1 useful:filler ratio.
        # When a filler item is drawn, roll against trap_pct — if hit, replace with a trap.
        # If useful exhausted → use filler instead (no trap replacement for those).
        # If filler exhausted → use useful instead (no trap replacement for those).
        # If both exhausted → infinite filler padding (no trap replacement).
        itempool: list[Item] = []
        itempool.extend(progression_pool)
        remaining_slots = visible_location_count - len(itempool)

        u_idx = f_idx = inf_idx = 0
        want_useful = True  # alternates between useful and filler
        for _ in range(remaining_slots):
            placed_filler_slot = False
            if want_useful:
                if u_idx < len(all_useful):
                    itempool.append(self.create_item(all_useful[u_idx])); u_idx += 1
                elif f_idx < len(all_filler):
                    placed_filler_slot = True  # exhausted useful, using filler
                    filler_name = all_filler[f_idx]; f_idx += 1
                    if trap_pct > 0 and self.random.randint(1, 100) <= trap_pct:
                        itempool.append(self.create_item(_next_trap()))
                    else:
                        itempool.append(self.create_item(filler_name))
                else:
                    itempool.append(self.create_item(all_filler_inf[inf_idx % len(all_filler_inf)]))
                    inf_idx += 1
            else:
                if f_idx < len(all_filler):
                    placed_filler_slot = True
                    filler_name = all_filler[f_idx]; f_idx += 1
                    if trap_pct > 0 and self.random.randint(1, 100) <= trap_pct:
                        itempool.append(self.create_item(_next_trap()))
                    else:
                        itempool.append(self.create_item(filler_name))
                elif u_idx < len(all_useful):
                    itempool.append(self.create_item(all_useful[u_idx])); u_idx += 1
                else:
                    itempool.append(self.create_item(all_filler_inf[inf_idx % len(all_filler_inf)]))
                    inf_idx += 1
            want_useful = not want_useful

        if len(itempool) != visible_location_count:
            raise ValueError(
                f"Item pool size mismatch after padding. "
                f"Visible locations: {visible_location_count}, "
                f"items in pool: {len(itempool)}."
            )

        # Pre-collect starting gems (only when gem_shop is enabled)
        if self.gem_shop_enabled:
            for _ in range(int(self.options.starting_gems.value)):
                self.multiworld.push_precollected(self.create_item(Items.aomItemData.GEM.item_name))

        self.multiworld.itempool += itempool

    def set_rules(self) -> None:
        Rules.set_rules(self)

    def write_spoiler_header(self, spoiler_handle) -> None:
        """Write random_major_gods god assignments to the spoiler log."""
        if not self.options.random_major_gods or not self.god_assignments:
            return
        from .locations.Scenarios import aomScenarioData
        spoiler_handle.write(f"\nRandom_Major_Gods God Assignments ({self.multiworld.get_player_name(self.player)}):\n")
        for scenario in aomScenarioData:
            n   = scenario.global_number
            god = _GOD_NAMES.get(self.god_assignments.get(n, 0), "Unknown")
            spoiler_handle.write(f"  {scenario.display_name}: {god}\n")
        spoiler_handle.write("\n")

    def fill_slot_data(self) -> Mapping[str, Any]:
        data: dict = {
            "version_public": 0,
            "version_major":  2,
            "version_minor":  2,
            "world_id":       ((time.time_ns() >> 17) + self.player) & 0x7FFF_FFFF,
            "final_mode":     int(self.options.final_scenarios.value),
            "x_scenarios":    int(self.options.x_scenarios.value),
            "random_major_gods":      bool(self.options.random_major_gods.value),
            "update_buildings_for_random_god": bool(self.options.update_buildings_for_random_god.value),
            "gem_shop":       self.gem_shop_enabled,
        }
        if self.options.random_major_gods:
            data["god_assignments"] = self.god_assignments
        data["minor_god_assignments"] = self.minor_god_assignments
        data["archaic_forbids"]       = self.archaic_forbids

        if self.gem_shop_enabled:
            data["starting_gems"]       = int(self.options.starting_gems.value)
            data["wins_to_open_shop"]   = int(self.options.wins_to_open_shop.value)

            # Obelisk → location_id list (determined at generation)
            data["shop_obelisk_assignments"] = {
                k: list(v) for k, v in self.shop_obelisk_assignments.items()
            }

            # Per-location item details (populated after fill)
            shop_item_details: dict[int, dict] = {}
            for loc_id in Locations.ALL_SHOP_ITEM_IDS:
                name = Locations.location_id_to_name.get(loc_id)
                if name:
                    location = self.multiworld.get_location(name, self.player)
                    if location and location.item:
                        shop_item_details[loc_id] = {
                            "player":         location.item.player,
                            "player_name":    self.multiworld.get_player_name(location.item.player),
                            "item_name":      location.item.name,
                            "classification": location.item.classification.name.lower(),
                        }
            data["shop_item_details"] = shop_item_details

            # Hint slot configs
            shop_hint_config: dict[str, dict] = {}
            for tier, _display, _item_obs, hint_obs in Locations.SHOP_TIER_CONFIGS:
                for h in range(1, hint_obs + 1):
                    slot_id = f"{tier}_HINT_{h}"
                    if h == 1:
                        shop_hint_config[slot_id] = {
                            "type":       "progressive_info",
                            "loc_id":     Locations.PROGRESSIVE_INFO_IDS[tier],
                        }
                    else:
                        # A→1-2 missions, B→2-3 missions, C→3-4 missions (D has no mission hints)
                        if tier == "A":
                            missions_range = (1, 2)
                        elif tier == "B":
                            missions_range = (2, 3)
                        else:  # C (Grass)
                            missions_range = (3, 4)
                        shop_hint_config[slot_id] = {
                            "type":           "mission_hints",
                            "missions_range": missions_range,
                        }
            data["shop_hint_config"] = shop_hint_config

        return data

def run_client(*args: Any) -> None:
    print("Running Age Of Mythology Retold Client")
    from .client.ApClient import main
    launch_subprocess(main, name="aomClient")


components.append(
    Component(
        "Age Of Mythology Retold Client",
        func=run_client,
        component_type=Type.CLIENT,
        icon="aomr",
    )
)
components_module.icon_paths["aomr"] = f"ap:{__name__}/aom_icon.png"