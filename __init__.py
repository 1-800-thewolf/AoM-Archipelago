# world/aom/__init__.py
#
# =============================================================================
# Age of Mythology Retold — Archipelago World Definition
# =============================================================================
#
# Entry point for the AoMR Archipelago world.  Defines:
#   * aomWorld   — the Archipelago World subclass (item pool, regions, rules)
#   * AoMSettings— per-user host settings (game install path)
#   * aomWebWorld— web template / YAML option grouping for the website
#   * Vanilla data tables — _VANILLA_GODS, _MINOR_GOD_TECHS, _AGE_BASE_TECHS,
#                            _SCENARIO_STARTING_AGE, _VANILLA_MINOR_GOD_TECHS,
#                            _GOD_SPECIFIC_ARCHAIC_UNITS, _CIV_ARCHAIC_UNITS
#
# Architecture overview (data flow):
#   YAML options ─► Options.py ─► aomWorld.generate_early()
#                                        │
#                                        ├─► god_assignments        (random major gods)
#                                        ├─► minor_god_assignments  (floor age techs)
#                                        ├─► minor_god_full         (all 3 tiers)
#                                        ├─► archaic_forbids        (units to disable)
#                                        ├─► shop_obelisk_assignments (gem shop)
#                                        └─► god_power_assignments  (random GPs)
#                                        │
#                                  create_regions ─► regions/Regions.py
#                                  create_items   ─► items/Items.py
#                                  set_rules      ─► rules/Rules.py
#                                  fill_slot_data ─► sent to ApClient at game start
#                                        │
#                                        ▼
#                                  Archipelago server stores result, then at game-time
#                                  the AP client (client/ApClient.py) connects and
#                                  passes slot_data to GameClient.py which generates
#                                  triggers/aom_state.xs that the running game reads.
#
# =============================================================================
# EXTENDING THE WORLD — Quick-reference for adding more content
# =============================================================================
#
# ### Adding a new CAMPAIGN (e.g. The Titans expansion):
#   1. Pick a contiguous APScenarioID range that doesn't collide with existing
#      blocks.  Current blocks: 1-32 (FotT), 501-512 (New Atlantis), 601-604
#      (Golden Gift), 0 (Shop), 12 (FotT12 — Roc-bug-quirked).  Suggest 701+
#      for the next campaign.
#   2. Add a member to locations/Campaigns.py::aomCampaignData (and ensure its
#      `id` does not collide).
#   3. Define each scenario in locations/Scenarios.py::aomScenarioData with
#      .global_number set to your APScenarioID range.
#   4. Add scenario locations (objectives, relics, COMPLETION) in
#      locations/Locations.py.
#   5. Map each scenario's vanilla god in `_VANILLA_GODS` below and its starting
#      age in `_SCENARIO_STARTING_AGE`.
#   6. Add a vanilla minor god tech list per scenario in `_VANILLA_MINOR_GOD_TECHS`
#      so the non-random_major_gods path mirrors AoM defaults.
#   7. In the AoMR scenario editor, every scenario in the new campaign needs:
#        * `xsEnableRule("APActivateScenario");` early in its Game Start trigger
#        * `trQuestVarSet("APScenarioID", <your_id>);` before the rule fires
#        * Reinforcement spawn flag (Player 12 unit named "APSpawn" or similar
#          marker — see triggers/archipelago.xs::APFindReinforcementSpawn)
#        * Trap revealer (Player 12 Revealer set to LOS 1000 by editor trigger)
#        * Whatever per-scenario flags are required by the scenario's victory
#          conditions (these are scenario-specific — examine the existing FotT
#          scenarios in the editor for reference).
#   8. Create a YAML option in Options.py to opt the campaign in/out, mirror
#      the on/off pattern of FottGreekCampaign / NewAtlantis / GoldenGift.
#   9. Surface that option in `aomWebWorld.option_groups` and respect it in
#      `generate_early()` -> `disabled_campaigns`.
#  10. Add a Campaign item in items/Items.py that grants section access if
#      campaigns are gated.
#
# ### Adding a new MAJOR GOD (e.g. a 13th god):
#   1. Pick the next free numeric ID (current top is 12 = Gaia).
#   2. Add it to `_GOD_NAMES` and to the appropriate civ frozenset
#      (`_GREEK_GODS` etc.) — or make a new civ frozenset (see "new pantheon"
#      below).
#   3. Add three entries to `_MINOR_GOD_TECHS` for tiers (id,1), (id,2),
#      (id,3) — each a `[option_A, option_B]` of minor god tech consts.
#   4. If god-specific archaic units exist (e.g. unique heroes), list them in
#      `_GOD_SPECIFIC_ARCHAIC_UNITS` so they get forbidden when the god is
#      reassigned away from a vanilla scenario.
#   5. In triggers/archipelago.xs:
#        * Add `cAPMajorXxx` constants (top of file).
#        * Extend the major-god dispatch in APSetPlayerCiv (calls
#          trPlayerSetCiv with the new god name string).
#        * Extend APApplyAgeUnlocks branches to dispatch to the right civ's
#          APApply*MinorGods.
#        * Extend APInitGodPowers / APAnnounceGod / any other god switchboard.
#   6. Add the god to GameClient.py's god name maps if any.
#   7. Make sure the Archipelago YAML option list (Options.py
#      `Greek_Major_Gods` etc., or a new option for a new pantheon) covers it.
#
# ### Adding a new MINOR GOD (e.g. an alternate Athena):
#   1. Add new `cTechClassicalAge<NewMinor>` etc. age tech constants to the
#      relevant `cTech*` const list at the top of triggers/archipelago.xs.
#   2. Append to the relevant `_MINOR_GOD_TECHS[(major, tier)]` list (length 2).
#   3. Add to all four `APForceDisableAll<Civ>AgeTechs` and
#      `APDisableAll<Civ>AgeTechs` functions in triggers/archipelago.xs so the
#      tech can be force-cleared between switches.
#   4. The free sample myth unit is granted by the tech itself — no extra code
#      unless you want a custom spawn.
#
# ### Adding a whole new PANTHEON (e.g. Aztec):
#   This is the largest extension and crosses every major file.
#   1. Add the civ to `_civ_of_god`, `_civ_of_god_name`, create a new frozenset
#      `_AZTEC_GODS = frozenset({13,14,15})`, fold into `_ALL_GODS_WITH_ATLANTIS`
#      (or add a new aggregate set if needed).
#   2. Add `_AGE_BASE_TECHS["Aztec"] = {1:..., 2:..., 3:...}`.
#   3. Add per-god minor god lists in `_MINOR_GOD_TECHS`.
#   4. Add scenarios using these gods (see "new campaign" above).
#   5. In Options.py: add `AztecMajorGods` boolean and wire it into
#      `excluded_civs` in `generate_early()` of aomWorld.
#   6. In Items.py: add `<Aztec>AgeUnlock` item, civ-tagged units/myth units
#      and any culture-tagged items.  Make sure `culture` field is set so the
#      civ-exclusion logic in `create_items()` filters correctly.
#   7. In triggers/archipelago.xs:
#        * Add `cAPMajor*` constants for each new god.
#        * Add `APForceDisableAllAztecAgeTechs` / `APDisableAllAztecAgeTechs`.
#        * Add `APApplyAztecMinorGods` mirroring the existing Greek/Egyptian/
#          Norse/Atlantean variants.
#        * Extend `APApplyAgeUnlocks` to dispatch to the new civ.
#        * Extend `APSetPlayerCiv` to switch on the new civ.
#        * Add `cAZTEC_AGE_UNLOCK` item ID and counting branch.
#   8. In GameClient.py: add the civ's age tech IDs to the dispatch tables and
#      any per-civ unit unlocks emitted into the generated XS state.
#
# ### Adding a new CIVILIZATION-SPECIFIC item or location:
#   1. Items: add an entry in items/Items.py with `culture="<Civ>"` so the
#      `create_items()` exclusion logic filters when that civ is disabled.
#   2. Locations: add to locations/Locations.py.  If it's tied to a specific
#      scenario, set `scenario` to that scenario; the campaign disable check
#      in `create_items()` will hide locations in disabled campaigns.
#   3. Reinforce with a region-and-rules entry if it has prerequisites.
#
# =============================================================================

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

from .Options import (Random_Major_Gods, ForceDifferentGod, ExtraFinalMissionAgeUnlocks,
    AomOptions,
    FinalScenarios,
    HeroAbilities,
    StartingScenarios,
    XScenarios,
    GreekMajorGods,
    EgyptianMajorGods,
    NorseMajorGods,
    AtlanteanMajorGods,
    NewAtlantis,
    GoldenGift,
    Relicsanity,
    GemShop,
    WinsToOpenShop,
    MaxAdvancementItemsInEachShop,
    ForceLocalFiller,
    FottGreekCampaign,
    FottEgyptianCampaign,
    FottNorseCampaign,
    UpdateBuildingsForRandomGod,
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
        OptionGroup("Shop", [
            GemShop,
            WinsToOpenShop,
            MaxAdvancementItemsInEachShop,
        ]),
        OptionGroup("Campaigns", [
            FottGreekCampaign,
            FottEgyptianCampaign,
            FottNorseCampaign,
            NewAtlantis,
            GoldenGift,
            Relicsanity,
        ]),
        OptionGroup("Random Major Gods", [
            Random_Major_Gods,
            ForceDifferentGod,
            GreekMajorGods,
            EgyptianMajorGods,
            NorseMajorGods,
            AtlanteanMajorGods,
            UpdateBuildingsForRandomGod,
        ]),
        OptionGroup("Starting Setup", [
            StartingScenarios,
        ]),
        OptionGroup("Final Section", [
            FinalScenarios,
            XScenarios,
        ]),
        OptionGroup("Item Pool", [
            ExtraFinalMissionAgeUnlocks,
            HeroAbilities,
            ForceLocalFiller,
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
    # New Atlantis (APScenarioIDs 501-512)
    501: 11, 502: 10, 503: 10, 504: 10, 505: 10, 506: 10,
    507:  5, 508:  6, 509:  8, 510: 12, 511: 11, 512: 12,
    # The Golden Gift (APScenarioIDs 601-604)
    601: 8, 602: 9, 603: 9, 604: 8,
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
    """Return the frozenset of god ids belonging to the same civilization
    as `god`.  Used by `_generate_god_assignments` (force_different_god
    branch) when we want to exclude the entire vanilla civ from the
    candidate pool."""
    if god in _GREEK_GODS:     return _GREEK_GODS
    if god in _EGYPTIAN_GODS:  return _EGYPTIAN_GODS
    if god in _ATLANTEAN_GODS: return _ATLANTEAN_GODS
    return _NORSE_GODS

def _civ_of_god_name(god: int) -> str:
    """Return the civilization label ("Greek"/"Egyptian"/"Norse"/"Atlantean")
    for a god id.  Used wherever we need the civ as a string key — e.g. into
    `_AGE_BASE_TECHS`, into `_CIV_ARCHAIC_UNITS`, or for slot_data emission."""
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
    # Fall of the Trident
    1:1, 2:0, 3:0, 10:0, 11:0, 12:0, 21:1, 22:0, 25:1,
    4:1, 8:1, 15:1, 18:1, 23:1, 24:1, 26:1, 27:1, 29:1, 30:1,
    5:2, 6:2, 7:2, 13:2, 14:2, 17:2, 19:2, 20:2, 28:2, 31:2, 32:2,
    9:3, 16:3,
    # New Atlantis (501-512)
    501:2, 502:0, 503:2, 504:2, 505:2, 506:3,
    507:2, 508:2, 509:2, 510:2, 511:3, 512:3,
    # The Golden Gift (601-604)
    601:2, 602:2, 603:2, 604:3,
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
    21: ["cTechClassicalAgeGreek",    "cTechClassicalAgeHermes"],  # Zeus (vanilla god for scen 21)
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
    # ---------------------------------------------------------------------------
    # New Atlantis (APScenarioIDs 501-512)
    # ---------------------------------------------------------------------------
    501: ["cTechClassicalAgeAtlantean", "cTechClassicalAgePrometheus",
          "cTechHeroicAgeAtlantean",    "cTechHeroicAgeHyperion"],
    503: ["cTechClassicalAgeAtlantean", "cTechClassicalAgePrometheus",
          "cTechHeroicAgeAtlantean",    "cTechHeroicAgeHyperion"],
    504: ["cTechClassicalAgeAtlantean", "cTechClassicalAgePrometheus",
          "cTechHeroicAgeAtlantean",    "cTechHeroicAgeHyperion"],
    505: ["cTechClassicalAgeAtlantean", "cTechClassicalAgeLeto",
          "cTechHeroicAgeAtlantean",    "cTechHeroicAgeRheia"],
    506: ["cTechClassicalAgeAtlantean", "cTechClassicalAgePrometheus",
          "cTechHeroicAgeAtlantean",    "cTechHeroicAgeRheia",
          "cTechMythicAgeAtlantean",    "cTechMythicAgeAtlas"],
    507: ["cTechClassicalAgeEgyptian",  "cTechClassicalAgeBast",
          "cTechHeroicAgeEgyptian",     "cTechHeroicAgeSobek"],
    508: ["cTechClassicalAgeEgyptian",  "cTechClassicalAgeAnubis",
          "cTechHeroicAgeEgyptian",     "cTechHeroicAgeNephthys"],
    509: ["cTechClassicalAgeNorse",     "cTechClassicalAgeForseti",
          "cTechHeroicAgeNorse",        "cTechHeroicAgeSkadi"],
    510: ["cTechClassicalAgeAtlantean", "cTechClassicalAgeLeto",
          "cTechHeroicAgeAtlantean",    "cTechHeroicAgeRheia"],
    511: ["cTechClassicalAgeAtlantean", "cTechClassicalAgeOceanus",
          "cTechHeroicAgeAtlantean",    "cTechHeroicAgeHyperion",
          "cTechMythicAgeAtlantean",    "cTechMythicAgeHelios"],
    512: ["cTechClassicalAgeAtlantean", "cTechClassicalAgeOceanus",
          "cTechHeroicAgeAtlantean",    "cTechHeroicAgeRheia",
          "cTechMythicAgeAtlantean",    "cTechMythicAgeAtlas"],
    # ---------------------------------------------------------------------------
    # The Golden Gift (APScenarioIDs 601-604) — all start Heroic or Mythic
    # GG1 Thor:  Heroic start — Classical=Freyja, Heroic=Skadi
    601: ["cTechClassicalAgeNorse",    "cTechClassicalAgeFreyja",
          "cTechHeroicAgeNorse",       "cTechHeroicAgeSkadi"],
    # GG2 Loki:  Heroic start — Classical=Forseti, Heroic=Njord
    602: ["cTechClassicalAgeNorse",    "cTechClassicalAgeForseti",
          "cTechHeroicAgeNorse",       "cTechHeroicAgeNjord"],
    # GG3 Loki:  Heroic start — Classical=Heimdall, Heroic=Njord
    603: ["cTechClassicalAgeNorse",    "cTechClassicalAgeHeimdall",
          "cTechHeroicAgeNorse",       "cTechHeroicAgeNjord"],
    # GG4 Thor:  Mythic start — Classical=Freyja, Heroic=Skadi, Mythic=Tyr
    604: ["cTechClassicalAgeNorse",    "cTechClassicalAgeFreyja",
          "cTechHeroicAgeNorse",       "cTechHeroicAgeSkadi",
          "cTechMythicAgeNorse",       "cTechMythicAgeTyr"],
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
    location_names = set(location.global_name() for location in Locations.aomLocationData)

    item_name_to_id = Items.item_name_to_id
    item_id_to_name = Items.item_id_to_name
    location_name_to_id = Locations.location_name_to_id
    location_id_to_name = Locations.location_id_to_name

    def create_regions(self) -> None:
        """Archipelago hook — delegates to `regions/Regions.py::create_regions`,
        which builds the menu/region/location graph for this player slot."""
        Regions.create_regions(self.multiworld, self.player)

    def _starting_campaign(self) -> Campaigns.aomCampaignData:
        """Resolve which campaign the player begins with — used by
        `create_items()` to precollect that campaign's section unlock and by
        Rules.py to gate Final-section access in beat_x mode.
        Honors `_fallback_start_campaign` if `generate_early()` redirected
        away from a disabled-by-YAML campaign."""
        fallback = getattr(self, "_fallback_start_campaign", None)
        if fallback is not None:
            return fallback
        value = int(self.options.starting_scenarios.value)
        mapping = {
            StartingScenarios.option_greek:        Campaigns.aomCampaignData.FOTT_GREEK,
            StartingScenarios.option_egyptian:     Campaigns.aomCampaignData.FOTT_EGYPTIAN,
            StartingScenarios.option_norse:        Campaigns.aomCampaignData.FOTT_NORSE,
            StartingScenarios.option_new_atlantis: Campaigns.aomCampaignData.NEW_ATLANTIS,
        }
        return mapping.get(value, Campaigns.aomCampaignData.FOTT_GREEK)

    def _final_mode(self) -> int:
        """Return the FinalScenarios option value — controls whether the Final
        section is gated by the Atlantis Key item or by completion-count of
        non-final scenarios.  Read by `create_items()` and `Rules.py`."""
        return int(self.options.final_scenarios.value)

    def create_item(self, name: str) -> Item:
        """Archipelago hook — convert an item name string into an `Item`
        object owned by this player.  Looks up classification from
        `Items.item_type_to_classification` and id from the item's data
        record.  Called from many places — `create_items` for the main pool,
        and by Rules.py for forced placements (Victory, Gem, ProgressiveShopInfo)."""
        item = Items.NAME_TO_ITEM[name]
        return Item(
            item.item_name,
            Items.item_type_to_classification[item.type_data],
            item.id,
            self.player,
        )

    def get_filler_item_name(self) -> str:
        """Archipelago hook — return the name of an arbitrary filler item.
        Called by the multiworld when it needs to pad an item pool.
        Excludes Gem because gems are locked to Victory locations by
        `Rules.place_gems()` and must not appear at non-victory slots."""
        # Exclude Gem: gems are locked to Victory locations by place_gems() and
        # should never appear as padding filler at objective/relic locations.
        non_gem = [item.item_name for item in Items.filler_items
                   if not isinstance(item.type, Items.Gem)]
        return self.random.choice(non_gem)

    def generate_early(self) -> None:
        """Archipelago hook — runs once before regions/items/rules are built.
        Reads YAML options and produces all derived per-world tables that
        downstream stages and the slot_data payload depend on:

          * `excluded_civs`            — civs the player opted out of
          * `_allowed_god_ids`         — gods available for random_major_gods
          * `god_assignments`          — random major god per scenario
          * `minor_god_assignments`    — floor base+minor age techs per scenario
          * `minor_god_full`           — chosen+rejected per tier per scenario
          * `archaic_forbids`          — archaic units to forbid at scenario start
          * `gem_shop_enabled` + assignments
          * `relicsanity_enabled`
          * `disabled_campaigns`
          * `_fallback_start_campaign` (only if starting campaign was disabled)
          * `god_power_assignments`    — random GP per tier per scenario

        Order matters — the random-driven generators are deterministic with
        respect to `self.random`, and re-ordering would invalidate existing
        seeds for in-progress runs."""
        _rmg_on = bool(self.options.random_major_gods.value)

        # Compute excluded civilizations from per-pantheon boolean options.
        # Only applies when random_major_gods is enabled.
        _CIV_GODS = {"Greek": {1,2,3}, "Egyptian": {4,5,6}, "Norse": {7,8,9}, "Atlantean": {10,11,12}}
        if _rmg_on:
            self.excluded_civs: frozenset[str] = frozenset(
                civ for civ, opt in [
                    ("Greek",    self.options.shuffle_greek_major_gods),
                    ("Egyptian", self.options.shuffle_egyptian_major_gods),
                    ("Norse",    self.options.shuffle_norse_major_gods),
                    ("Atlantean",self.options.shuffle_atlantean_major_gods),
                ] if not bool(opt.value)
            )
            # Validation: at least one pantheon must be active
            if len(self.excluded_civs) == 4:
                raise Exception(
                    "AoMR Archipelago: All pantheons are disabled. "
                    "Set at least one pantheon to true in your options YAML "
                    "(shuffle_greek_major_gods, shuffle_egyptian_major_gods, "
                    "shuffle_norse_major_gods, or shuffle_atlantean_major_gods)."
                )
        else:
            self.excluded_civs = frozenset()
        self._allowed_god_ids: set[int] = set(range(1, 13)) - {
            g for civ in self.excluded_civs for g in _CIV_GODS.get(civ, set())
        }

        if _rmg_on:
            self.god_assignments: dict[int, int] = self._generate_god_assignments()
        else:
            self.god_assignments = {}
        self.minor_god_assignments: dict[int, list] = self._generate_minor_god_assignments()
        self.minor_god_full: dict[int, dict]        = self._generate_minor_god_full()
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

        # Relicsanity flag — read once so Regions/Rules/create_items can branch on it.
        self.relicsanity_enabled: bool = bool(self.options.relicsanity.value)

        # Force all filler items to be placed locally (this player's own world only).
        if bool(self.options.force_local_filler.value):
            filler_names = {item.item_name for item in Items.filler_items}
            self.multiworld.local_items[self.player].value |= filler_names

        # Disabled-campaign set: campaigns can be opted out via YAML.
        # FOTT_FINAL is always enabled (its scenarios are the goal).
        from .locations.Campaigns import aomCampaignData
        self.disabled_campaigns: set[aomCampaignData] = set()
        if not bool(self.options.fott_greek_campaign.value):
            self.disabled_campaigns.add(aomCampaignData.FOTT_GREEK)
        if not bool(self.options.fott_egyptian_campaign.value):
            self.disabled_campaigns.add(aomCampaignData.FOTT_EGYPTIAN)
        if not bool(self.options.fott_norse_campaign.value):
            self.disabled_campaigns.add(aomCampaignData.FOTT_NORSE)
        if not bool(self.options.new_atlantis_campaign.value):
            self.disabled_campaigns.add(aomCampaignData.NEW_ATLANTIS)
        if not bool(self.options.golden_gift_campaign.value):
            self.disabled_campaigns.add(aomCampaignData.GOLDEN_GIFT)

        # If the chosen starting campaign is disabled, fall back to the first
        # enabled FOTT campaign so the player has somewhere to start.
        _start = self._starting_campaign()
        if _start in self.disabled_campaigns:
            for _fallback in (aomCampaignData.FOTT_GREEK,
                               aomCampaignData.FOTT_EGYPTIAN,
                               aomCampaignData.FOTT_NORSE):
                if _fallback not in self.disabled_campaigns:
                    self._fallback_start_campaign = _fallback
                    break

        # Pre-determined random god powers per scenario per tier (uses self.random
        # for deterministic regeneration). Must run after disabled_campaigns is set.
        self.god_power_assignments: dict[int, list[str]] = self._generate_god_power_assignments()



    def _generate_shop_assignments(self) -> tuple:
        """
        Randomly distributes 60 shop items across 14 obelisks (15 per shop).
        Exactly 1 progression slot per shop. ~half of remaining slots are filler-only.
        Returns (obelisk_assignments, progression_slots, filler_only_locations).
        """
        from .locations.Locations import SHOP_TIER_CONFIGS, TIER_ITEM_IDS, ITEMS_PER_SHOP
        assignments: dict[str, list[int]] = {}
        progression_slots: dict[str, set[int]] = {}
        filler_only_locs: set[int] = set()

        max_adv = int(self.options.max_advancement_items_in_each_shop.value)
        max_adv = max(0, min(ITEMS_PER_SHOP, max_adv))

        for tier_name, _display, item_obs, _hint_obs in SHOP_TIER_CONFIGS:
            locs = list(TIER_ITEM_IDS[tier_name])  # 15 location IDs for this tier
            self.random.shuffle(locs)

            # Marsh (tier A) never allows progression regardless of the option.
            n_prog = 0 if tier_name == "A" else max_adv
            progression_slots[tier_name] = set(locs[:n_prog])

            # Of the remaining slots, randomly pick ~80% to be filler-only.
            non_prog = locs[n_prog:]
            n_filler_only = round(len(non_prog) * 0.8)
            if n_filler_only > 0:
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
        """Randomly assign a major god to each scenario using the world seed.
        Respects self._allowed_god_ids to exclude disabled civilizations."""
        force = bool(self.options.force_different_god.value)
        allowed = frozenset(self._allowed_god_ids)
        assignments: dict[int, int] = {}
        # Iterate all scenario IDs that have vanilla god assignments:
        # FotT (1-32), New Atlantis (501-512), Golden Gift (601-604)
        for scenario_id in sorted(sid for sid in _VANILLA_GODS):
            vanilla = _VANILLA_GODS[scenario_id]
            if force:
                if self.random.random() < 0.5:
                    candidates = list(allowed - _civ_of_god(vanilla))
                else:
                    candidates = list(allowed - {vanilla})
            else:
                candidates = list(allowed)
            if not candidates:
                # Fallback: if exclusions eliminated all candidates, use full allowed set
                candidates = list(allowed)
            if not candidates:
                candidates = [vanilla]  # absolute fallback
            assignments[scenario_id] = self.random.choice(candidates)
        return assignments

    # UNUSED: never called. Kept (commented) as a manual-debug helper for RNG drift.
    # def _log_god_assignments(self, assignments: dict[int, int]) -> None:
    #     """Diagnostic log dump of every scenario's assigned god — useful when
    #     debugging seed/RNG drift between generations.  Currently not called
    #     from a production code path; left in for manual debugging.
    #
    #     Args:
    #         assignments: scenario_id -> god_id (1-12) mapping.
    #     """
    #     from .locations.Scenarios import aomScenarioData
    #     lines = ["Random_Major_Gods god assignments:"]
    #     for scenario in aomScenarioData:
    #         n   = scenario.global_number
    #         god = _GOD_NAMES.get(assignments.get(n, 0), "Unknown")
    #         lines.append(f"  {scenario.display_name}: {god}")
    #     logger.info("\n".join(lines))

    def _generate_archaic_forbids(self) -> dict[int, list]:
        """Returns {scenario_id: [unit_name, ...]} of units to forbid at
        scenario start because they belong to the vanilla god/civ but the
        assigned god is different."""
        result: dict[int, list] = {}
        for scenario_id in _VANILLA_GODS:
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
        for scenario_id in _VANILLA_GODS:
            god_id       = self.god_assignments.get(scenario_id, _VANILLA_GODS[scenario_id])
            starting_age = _SCENARIO_STARTING_AGE.get(scenario_id, 0)
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

    def _generate_minor_god_full(self) -> dict[int, dict]:
        """
        Returns {scenario_id: {tier: [chosen_tech, rejected_tech, is_floor]}}
        for ALL tiers (1-3) of every scenario.

        Floor-tier choices (tier <= starting_age) are extracted from the already-
        generated minor_god_assignments so the RNG sequence for those tiers is not
        disturbed.  Above-floor tiers use self.random (random_major_gods mode) or
        always option-A (vanilla mode) so no existing item-placement seeds are
        broken when random_major_gods is off.
        """
        result: dict[int, dict] = {}
        for scenario_id in sorted(_VANILLA_GODS.keys()):
            god_id       = self.god_assignments.get(scenario_id, _VANILLA_GODS[scenario_id])
            starting_age = _SCENARIO_STARTING_AGE.get(scenario_id, 0)
            floor_techs  = self.minor_god_assignments.get(scenario_id, [])
            tier_data: dict[int, list] = {}
            for tier in range(1, 4):
                options = _MINOR_GOD_TECHS.get((god_id, tier), [])
                if len(options) < 2:
                    continue
                if tier <= starting_age:
                    # Floor tier: extract the pre-made choice from minor_god_assignments.
                    # Format is [base_tech, minor_god_tech, base_tech, minor_god_tech, ...]
                    # so minor god for tier T is at odd index (T-1)*2 + 1.
                    idx = (tier - 1) * 2 + 1
                    if idx < len(floor_techs):
                        chosen   = floor_techs[idx]
                        rejected = options[1] if options[0] == chosen else options[0]
                        tier_data[tier] = [chosen, rejected, True]
                else:
                    # Above-floor tier: new seeded choice (or deterministic option-A).
                    if self.options.random_major_gods:
                        chosen = self.random.choice(options)
                    else:
                        chosen = options[0]
                    rejected = options[1] if options[0] == chosen else options[0]
                    tier_data[tier] = [chosen, rejected, False]
            if tier_data:
                result[scenario_id] = tier_data
        return result

    def _generate_god_power_assignments(self) -> dict[int, list[str]]:
        """
        Pre-determine 4 random god powers, one per tier, for every scenario in
        every active campaign. Scenarios in disabled campaigns get an empty list.

        Returns {APScenarioID: [tier1, tier2, tier3, tier4]}
        """
        from .locations.Scenarios import aomScenarioData

        TIER_POOLS = [
            ["Bolt", "Deconstruction", "LocustSwarm", "GreatHunt", "Shockwave", "GaiaForest"],
            ["Restoration", "Carnivora", "SpiderLair", "Pestilence", "Eclipse",
            "ShiftingSands", "PlagueOfSerpents", "Undermine", "HealingSpring"],
            ["Traitor", "FlamingWeapons", "UnderworldPassage", "Bronze", "Curse",
            "Ancestors", "WalkingWoods", "Frost", "Chaos", "HesperidesTree"],
            ["LightningStorm", "Earthquake", "Meteor", "Tornado", "Nidhogg",
            "Implode", "TartarianGate"],
        ]

        result: dict[int, list[str]] = {}

        for scenario in aomScenarioData:
            scenario_id = scenario.global_number

            if scenario.campaign in self.disabled_campaigns:
                result[scenario_id] = []
                continue

            result[scenario_id] = [self.random.choice(pool) for pool in TIER_POOLS]

        return result

    def create_items(self) -> None:
        """
        Build the item pool.

        Pool tiers (in order):
        1. Progression items — section unlocks, age unlocks, unit progression
        2. Atlantis Key — in pool for atlantis_key mode only; beat_x mode gates
           the Final section directly on completion count (no key item needed)
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
        random_major_gods_on        = bool(self.options.random_major_gods.value)

        # Age unlocks are never precollected — players use start_inventory or
        # start_inventory_from_pool in their YAML if they want starting unlocks.
        starting_age_unlocks = {
            "Greek": 0, "Egyptian": 0, "Norse": 0, "Atlantean": 0,
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
                if item.type.vanilla_campaign in self.disabled_campaigns:
                    continue  # campaign disabled — no unlock item
                ap_item = self.create_item(item.item_name)
                if item.type.vanilla_campaign == start_campaign:
                    self.multiworld.push_precollected(ap_item)
                else:
                    progression_pool.append(ap_item)
                continue

            # Atlantis Key — always in pool EXCEPT in beat_x mode where Rules.py
            # beat_x mode gates the Final section on completion count instead
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

            # Kastor items — removed when New Atlantis campaign is disabled,
            # except KASTOR_JOINS, which is always in pool unless the ONLY
            # enabled campaign is New Atlantis (Kastor is already there).
            _is_kastor_joins = (item == Items.aomItemData.KASTOR_JOINS)
            _is_kastor_item = _is_kastor_joins or (
                getattr(item.type, "hero", "") == "Kastor"
                or item.item_name.startswith("Kastor ")
                or item.item_name == "Kastor is a Manor"
            )
            if _is_kastor_item:
                from .locations.Campaigns import aomCampaignData as _C
                _na_disabled = _C.NEW_ATLANTIS in self.disabled_campaigns
                _enabled_campaigns = {c for c in _C if c not in self.disabled_campaigns
                                       and c != _C.FOTT_FINAL}
                _only_na = (_enabled_campaigns == {_C.NEW_ATLANTIS})
                if _is_kastor_joins:
                    if _only_na:
                        continue
                else:
                    if _na_disabled:
                        continue

            # Odysseus items — removed when FotT Greek campaign is disabled,
            # except ODYSSEUS_JOINS which follows the same logic as KASTOR_JOINS.
            _is_odysseus_joins = (item == Items.aomItemData.ODYSSEUS_JOINS)
            _is_odysseus_item = _is_odysseus_joins or (
                getattr(item.type, "hero", "") in ("Odysseus", "OdysseusSPC")
                or item.item_name.startswith("Odysseus ")
            )
            if _is_odysseus_item:
                from .locations.Campaigns import aomCampaignData as _C
                _greek_disabled = _C.FOTT_GREEK in self.disabled_campaigns
                if _greek_disabled:
                    continue

            # Reginleif items — removed when FotT Norse campaign is disabled.
            _is_reginleif_joins = (item == Items.aomItemData.REGINLEIF_JOINS)
            _is_reginleif_item = _is_reginleif_joins or (
                getattr(item.type, "hero", "") == "Reginleif"
                or item.item_name.startswith("Reginleif ")
            )
            if _is_reginleif_item:
                from .locations.Campaigns import aomCampaignData as _C
                _norse_disabled = _C.FOTT_NORSE in self.disabled_campaigns
                if _norse_disabled:
                    continue

            # Arkantos/Chiron items — removed when ALL FotT campaigns (Greek,
            # Egyptian, Norse) are disabled (i.e. only new campaigns enabled).
            _is_arkantos_item = (
                getattr(item.type, "hero", "") == "Arkantos"
                or item.item_name.startswith("Arkantos ")
                or isinstance(item.type, Items.ArkantosHousing)
            )
            _is_chiron_item = (
                getattr(item.type, "hero", "") == "Chiron"
                or item.item_name.startswith("Chiron ")
            )
            if _is_arkantos_item or _is_chiron_item:
                from .locations.Campaigns import aomCampaignData as _C
                _all_fott_disabled = (
                    _C.FOTT_GREEK in self.disabled_campaigns
                    and _C.FOTT_EGYPTIAN in self.disabled_campaigns
                    and _C.FOTT_NORSE in self.disabled_campaigns
                )
                if _all_fott_disabled:
                    continue

            if item == Items.aomItemData.AJAX_AMANRA_DREAMS:
                from .locations.Campaigns import aomCampaignData as _C
                _all_fott_disabled = (
                    _C.FOTT_GREEK in self.disabled_campaigns
                    and _C.FOTT_EGYPTIAN in self.disabled_campaigns
                    and _C.FOTT_NORSE in self.disabled_campaigns
                )
                if _all_fott_disabled:
                    continue

            # Atlantean items — skip if random_major_gods is off (Atlantis not in the pool)
            if isinstance(item.type, atlantean_types) and not random_major_gods_on:
                continue

            # Civ-specific items — skip if that civ is excluded (only when random_major_gods is on)
            # Generic items (reinforcements, heroes, resources) are never skipped.
            if random_major_gods_on and self.excluded_civs:
                # Primary: items with a culture field (unit unlocks, myth unlocks, age unlocks)
                _item_civ = getattr(item.type, "culture", None)
                # Secondary: VillagerCarryCapacity encodes civ in unit_name ("VillagerGreek" etc.)
                if not _item_civ:
                    _unit_name = getattr(item.type, "unit_name", "")
                    if   "Greek"    in _unit_name: _item_civ = "Greek"
                    elif "Egyptian" in _unit_name: _item_civ = "Egyptian"
                    elif "Norse"    in _unit_name: _item_civ = "Norse"
                    elif "Atlantean"in _unit_name: _item_civ = "Atlantean"
                if _item_civ and _item_civ in self.excluded_civs:
                    continue

            # Starting tech items are added explicitly below (1 copy each)
            if isinstance(item.type, (Items.StartingEconomyTech, Items.StartingMilitaryTech,
                                       Items.StartingDockTech, Items.StartingBuildingsTech)):
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
        _new_atlantis_disabled = Campaigns.aomCampaignData.NEW_ATLANTIS in self.disabled_campaigns
        for item_data, culture, count in age_unlock_config:
            # Skip age unlocks for civs excluded from the random major god pool,
            # EXCEPT Atlantean: NA scenarios always use Atlantean mechanics even
            # when shuffle_atlantean_major_gods is off, so Atlantean age unlocks
            # are always needed for age-gating NA scenarios (e.g. NA 2 requires
            # Classical Age). Skip only if New Atlantis campaign is fully disabled.
            if culture in self.excluded_civs:
                if culture != "Atlantean" or _new_atlantis_disabled:
                    continue
            precollect_n = starting_age_unlocks[culture]
            for i in range(count):
                ap_item = self.create_item(item_data.item_name)
                if i < precollect_n:
                    self.multiworld.push_precollected(ap_item)
                else:
                    progression_pool.append(ap_item)

        # Starting Tech items — 1 copy each.
        # Economy and Military are Useful; Dock and Buildings are Filler.
        # Each item grants all techs of that category up to the scenario's starting age.
        for tech_item in [
            Items.aomItemData.STARTING_ECONOMY_TECH,
            Items.aomItemData.STARTING_MILITARY_TECH,
        ]:
            useful_groups.setdefault(type(tech_item.type), []).append(tech_item.item_name)
        for tech_item in [
            Items.aomItemData.STARTING_DOCK_TECH,
            Items.aomItemData.STARTING_BUILDINGS_TECH,
        ]:
            filler_groups.setdefault(type(tech_item.type), []).append(tech_item.item_name)

        # Visible location count:
        #   Campaign non-COMPLETION locations minus the locations Rules.py locks
        #   to fixed items (which therefore can't hold pool items).
        #
        # Always-locked: scenario 32 Victory is locked to the Victory item.
        # Gem-shop-locked (when enabled): every other Victory location holds a
        #   Gem (place_gems) and every Progressive Info hint slot holds a
        #   Progressive Shop Info item (place_progressive_shop_info).
        # The 60 shop item slots remain free fill targets.
        gem_shop_on = self.gem_shop_enabled
        disabled_campaigns = self.disabled_campaigns
        relicsanity_on = self.relicsanity_enabled
        visible_location_count = (
            sum(1 for loc in Locations.aomLocationData
                if loc.type != Locations.aomLocationType.COMPLETION
                and loc.scenario.campaign not in disabled_campaigns
                and (relicsanity_on or loc.type != Locations.aomLocationType.RELIC))
            - 1  # scenario 32 Victory is always locked to the Victory item
        )
        if gem_shop_on:
            # Subtract the remaining Victory locations — Rules.place_gems locks
            # every Victory except scenario 32 (which is already subtracted above).
            locked_gem_count = sum(
                1 for loc in Locations.aomLocationData
                if loc.type == Locations.aomLocationType.VICTORY
                and loc.scenario.campaign not in disabled_campaigns
            ) - 1
            visible_location_count -= locked_gem_count
            # 60 shop item slots are free fill targets.
            visible_location_count += len(Locations.ALL_SHOP_ITEM_IDS)
            # Progressive Shop Info hint slots are locked by
            # Rules.place_progressive_shop_info — do NOT add them.

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
            Items.aomItemData.TRAP_LIGHTNING_STORM.item_name,
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
            Items.aomItemData.TRAP_CARNIVORA.item_name,
            # Items.aomItemData.TRAP_SPIDER_LAIR.item_name,  # disabled: buggy
            Items.aomItemData.TRAP_DECONSTRUCTION.item_name,
            Items.aomItemData.TRAP_FIMBULWINTER.item_name,
            # Items.aomItemData.TRAP_FLAMING_WEAPONS.item_name,  # disabled: fails to cast
            Items.aomItemData.TRAP_ANCESTORS.item_name,
            Items.aomItemData.TRAP_PESTILENCE.item_name,
            # Items.aomItemData.TRAP_BRONZE.item_name,  # disabled: can't cast on allies
            Items.aomItemData.TRAP_NIDHOGG.item_name,
            Items.aomItemData.TRAP_SHOCKWAVE.item_name,
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
        # Infinite padding pool: non-reinforcement filler items plus a curated
        # set of stackable useful items (relic trickle and LOS/Regen/Speed/HP
        # effects) whose XS handlers correctly accumulate multiple copies.
        # "Joins the Campaign" items are intentionally excluded — they must
        # appear at most once and are not present in either list below.
        _repeatable_useful_names = [
            Items.aomItemData.RELIC_TRICKLE_FOOD.item_name,
            Items.aomItemData.RELIC_TRICKLE_WOOD.item_name,
            Items.aomItemData.RELIC_TRICKLE_GOLD.item_name,
            Items.aomItemData.RELIC_TRICKLE_FAVOR.item_name,
            Items.aomItemData.RELIC_EFFECT_LOS.item_name,
            Items.aomItemData.RELIC_EFFECT_REGEN.item_name,
            Items.aomItemData.RELIC_EFFECT_SPEED.item_name,
            Items.aomItemData.RELIC_EFFECT_HP.item_name,
        ]
        # Build from filler_groups (already filtered by campaign/civ/hero-ability
        # exclusions in the main item loop) rather than iterating Items.aomItemData
        # directly — otherwise Chiron/Arkantos/Kastor/etc. filler items would leak
        # into the infinite padding pool even when their campaigns are disabled.
        all_nonreinf_filler_inf = [
            name
            for type_, names in filler_groups.items()
            for name in names
            if not issubclass(type_, Items.Reinforcement)
        ] + _repeatable_useful_names

        # Cap "Joins the Campaign" items at exactly 1 copy in the pool.
        # They appear once via all_useful (each is a unique enum member), but
        # this deduplication makes the cap explicit and robust against future changes.
        _joins_item_names = frozenset({
            Items.aomItemData.REGINLEIF_JOINS.item_name,
            Items.aomItemData.ODYSSEUS_JOINS.item_name,
            Items.aomItemData.KASTOR_JOINS.item_name,
        })
        _seen_joins: set = set()
        _deduped_useful = []
        for _name in all_useful:
            if _name in _joins_item_names:
                if _name in _seen_joins:
                    continue
                _seen_joins.add(_name)
            _deduped_useful.append(_name)
        all_useful = _deduped_useful

        self.random.shuffle(all_useful)
        self.random.shuffle(all_filler)
        self.random.shuffle(all_nonreinf_filler_inf)

        # Fill remaining slots in two phases:
        #   Unique phase  (while either pool has items): 1:1 useful:filler alternation.
        #     Useful exhausted mid-phase → draw filler that turn instead.
        #     Filler exhausted mid-phase → cycle infinite non-reinforcement filler.
        #   Padding phase (both pools exhausted):        5:1 filler:useful from infinite pools.
        #     Filler draws cycle all_nonreinf_filler_inf; useful draws cycle _repeatable_useful_names.
        # Trap replacement: filler/overflow turns roll against trap_pct; useful turns roll
        # against useful_trap_pct (10% of trap_pct).
        itempool: list[Item] = []
        itempool.extend(progression_pool)
        remaining_slots = visible_location_count - len(itempool)

        u_idx = f_idx = inf_idx = 0
        useful_trap_pct = trap_pct // 10  # 10% of the filler trap rate
        want_useful = True   # unique phase: alternates each slot
        pad_slot = 0         # padding phase: 0-4 = filler, 5 = useful, then repeats
        pad_useful_idx = 0   # padding phase: cycles through _repeatable_useful_names
        for _ in range(remaining_slots):
            both_exhausted = (u_idx >= len(all_useful)) and (f_idx >= len(all_filler))

            if both_exhausted:
                # Padding phase: 5 filler then 1 useful, repeating
                if pad_slot == 5:
                    pad_name  = _repeatable_useful_names[pad_useful_idx % len(_repeatable_useful_names)]
                    pad_useful_idx += 1
                    trap_roll = useful_trap_pct
                else:
                    pad_name  = all_nonreinf_filler_inf[inf_idx % len(all_nonreinf_filler_inf)]
                    inf_idx  += 1
                    trap_roll = trap_pct
                if trap_roll > 0 and self.random.randint(1, 100) <= trap_roll:
                    itempool.append(self.create_item(_next_trap()))
                else:
                    itempool.append(self.create_item(pad_name))
                pad_slot = (pad_slot + 1) % 6
            else:
                # Unique phase: 1:1 useful:filler
                if want_useful:
                    if u_idx < len(all_useful):
                        useful_name = all_useful[u_idx]; u_idx += 1
                        if useful_trap_pct > 0 and self.random.randint(1, 100) <= useful_trap_pct:
                            itempool.append(self.create_item(_next_trap()))
                        else:
                            itempool.append(self.create_item(useful_name))
                    else:
                        # Useful exhausted — draw filler instead
                        if f_idx < len(all_filler):
                            filler_name = all_filler[f_idx]; f_idx += 1
                        else:
                            filler_name = all_nonreinf_filler_inf[inf_idx % len(all_nonreinf_filler_inf)]
                            inf_idx += 1
                        if trap_pct > 0 and self.random.randint(1, 100) <= trap_pct:
                            itempool.append(self.create_item(_next_trap()))
                        else:
                            itempool.append(self.create_item(filler_name))
                else:
                    # Filler turn — never fall back to useful
                    if f_idx < len(all_filler):
                        filler_name = all_filler[f_idx]; f_idx += 1
                    else:
                        filler_name = all_nonreinf_filler_inf[inf_idx % len(all_nonreinf_filler_inf)]
                        inf_idx += 1
                    if trap_pct > 0 and self.random.randint(1, 100) <= trap_pct:
                        itempool.append(self.create_item(_next_trap()))
                    else:
                        itempool.append(self.create_item(filler_name))
                want_useful = not want_useful

        if len(itempool) != visible_location_count:
            raise ValueError(
                f"Item pool size mismatch after padding. "
                f"Visible locations: {visible_location_count}, "
                f"items in pool: {len(itempool)}."
            )

        self.multiworld.itempool += itempool

    def set_rules(self) -> None:
        """Archipelago hook — install access/completion rules and forced
        placements (Victory, Gem, Progressive Shop Info).  Delegates to
        `rules/Rules.py::set_rules`."""
        Rules.set_rules(self)


    def fill_slot_data(self) -> Mapping[str, Any]:
        """Archipelago hook — produce the per-slot data blob that the
        Archipelago server stores and ships to the client at connect time.

        Everything the running game needs to know up-front lives here:
        version stamps, disabled campaigns, world id, final-mode flag,
        random_major_gods state and god/minor-god/archaic/godpower
        assignments, plus shop assignments + per-slot item details when
        gem_shop is enabled.

        Receiver: client/ApClient.py — copies fields into `self.game_ctx`
        (see `_load_slot_data`) which then feeds GameClient.py for XS
        emission.

        Bumping schema: increment `version_minor` for additive changes;
        bump `version_major` only when older clients can't read the new
        payload (then update ApClient.py compatibility checks)."""
        data: dict = {
            "version_public": 0,
            "version_major":  2,
            "version_minor":  2,
            "disabled_campaigns": [c.id for c in self.disabled_campaigns],
            "world_id":       ((time.time_ns() >> 17) + self.player) & 0x7FFF_FFFF,
            "final_mode":     int(self.options.final_scenarios.value),
            "x_scenarios":    int(self.options.x_scenarios.value),
            "random_major_gods":      bool(self.options.random_major_gods.value),
            "update_buildings_for_random_god": bool(self.options.update_buildings_for_random_god.value),
            "gem_shop":       self.gem_shop_enabled,
            "relicsanity":    self.relicsanity_enabled,
        }
        if self.options.random_major_gods:
            data["god_assignments"] = self.god_assignments
        data["minor_god_assignments"] = self.minor_god_assignments
        data["minor_god_full"]        = self.minor_god_full
        data["archaic_forbids"]       = self.archaic_forbids
        data["god_power_assignments"] = self.god_power_assignments

        if self.gem_shop_enabled:
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
    """Archipelago Launcher entry point — invoked when the user clicks
    "Age Of Mythology Retold Client" in the AP Launcher.  Spawns the AP
    client (client/ApClient.py::main) in its own subprocess so the
    Launcher's event loop is not blocked.  *args are forwarded by the
    Launcher and currently unused — kept for forward compatibility."""
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