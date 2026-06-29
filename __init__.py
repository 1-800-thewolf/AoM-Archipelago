# world/aom/__init__.py
#
# =============================================================================
# Age of Mythology Retold — Archipelago World Definition
# =============================================================================
#
# Entry point for the AoMR Archipelago world.  Defines:
#   * aomWorld   — the Archipelago World subclass (item pool, regions, rules)
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
#        * StartingArmy spawn flag (Player 12 unit named "APSpawn" or similar
#          marker — see triggers/archipelago.xs::APFindStartingArmySpawn)
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
from typing import Any, Mapping

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
    ChineseMajorGods,
    JapaneseMajorGods,
    AztecMajorGods,
    # MoreFrequentDLCGods,  # hidden from players; uncomment to re-expose
    NewAtlantis,
    GoldenGift,
    PillarsOfTheGods,
    Relicsanity,
    OptionalObjectivesAreLocations,
    ExcludeScenario30,
    GemsAsFiller,
    GemShop,
    WinsToOpenShop,
    MaxProgressionItemsInEachShop,
    LocalFillerFrequency,
    FottGreekCampaign,
    FottEgyptianCampaign,
    FottNorseCampaign,
    MaxKeysOnKeyrings,
)
from .items import Items
from .locations import Campaigns, Locations
from .regions import Regions
from .rules import Rules

logger = logging.getLogger(__name__)

AOMR = "Age Of Mythology Retold"


class aomWebWorld(WebWorld):
    """Web settings and YAML template configuration for Age of Mythology Retold."""
    icon = "worlds/aom/aom_icon.png"
    option_groups = [
        OptionGroup("Shop", [
            GemShop,
            WinsToOpenShop,
            MaxProgressionItemsInEachShop,
        ]),
        OptionGroup("Campaigns", [
            FottGreekCampaign,
            FottEgyptianCampaign,
            FottNorseCampaign,
            NewAtlantis,
            GoldenGift,
            # HOTFIX: PillarsOfTheGods + OptionalObjectivesAreLocations hidden
            # (Visibility.none) until fully wired — restore here when ready.
            Relicsanity,
            ExcludeScenario30,
            MaxKeysOnKeyrings,
        ]),
        OptionGroup("Starting Campaign", [
            StartingScenarios,
        ]),
        OptionGroup("Final Section", [
            FinalScenarios,
            XScenarios,
        ]),
        OptionGroup("Random Major Gods", [
            Random_Major_Gods,
            ForceDifferentGod,
            GreekMajorGods,
            EgyptianMajorGods,
            NorseMajorGods,
            AtlanteanMajorGods,
            ChineseMajorGods,
            JapaneseMajorGods,
            AztecMajorGods,
            # MoreFrequentDLCGods,  # hidden from players; uncomment to re-expose
        ]),
        OptionGroup("Item Pool", [
            ExtraFinalMissionAgeUnlocks,
            HeroAbilities,
            LocalFillerFrequency,
            GemsAsFiller,
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
    # Pillars of the Gods (APScenarioIDs 701-709)
    701: 17, 702: 16, 703: 15, 704: 17, 705: 17, 706: 16, 707: 17,
    708: 15, 709: 17,
}
_GREEK_GODS      = frozenset({1, 2, 3, 13})
_EGYPTIAN_GODS   = frozenset({4, 5, 6})
_NORSE_GODS      = frozenset({7, 8, 9, 14})
_ATLANTEAN_GODS  = frozenset({10, 11, 12})  # Kronos, Oranos, Gaia
_CHINESE_GODS    = frozenset({15, 16, 17})  # Nuwa, Fuxi, Shennong
_JAPANESE_GODS   = frozenset({18, 19, 20})  # Amaterasu, Tsukuyomi, Susanoo
_AZTEC_GODS      = frozenset({21, 22, 23})  # Huitzilopochtli, Tezcatlipoca, Quetzalcoatl
_ALL_GODS        = _GREEK_GODS | _EGYPTIAN_GODS | _NORSE_GODS
_ALL_GODS_WITH_ATLANTIS = _ALL_GODS | _ATLANTEAN_GODS | _CHINESE_GODS | _JAPANESE_GODS | _AZTEC_GODS
_GOD_NAMES     = {
    1: "Zeus",   2: "Poseidon", 3: "Hades",
    4: "Isis",   5: "Ra",       6: "Set",
    7: "Odin",   8: "Thor",     9: "Loki",
    10: "Kronos", 11: "Oranos", 12: "Gaia",
    13: "Demeter", 14: "Freyr",
    15: "Nuwa", 16: "Fuxi", 17: "Shennong",
    18: "Amaterasu", 19: "Tsukuyomi", 20: "Susanoo",
    21: "Huitzilopochtli", 22: "Tezcatlipoca", 23: "Quetzalcoatl",
}

def _civ_of_god(god: int) -> frozenset:
    """Return the frozenset of god ids belonging to the same civilization
    as `god`.  Used by `_generate_god_assignments` (force_different_god
    branch) when we want to exclude the entire vanilla civ from the
    candidate pool."""
    if god in _GREEK_GODS:     return _GREEK_GODS
    if god in _EGYPTIAN_GODS:  return _EGYPTIAN_GODS
    if god in _ATLANTEAN_GODS: return _ATLANTEAN_GODS
    if god in _CHINESE_GODS:   return _CHINESE_GODS
    if god in _JAPANESE_GODS:  return _JAPANESE_GODS
    if god in _AZTEC_GODS:     return _AZTEC_GODS
    return _NORSE_GODS

def _civ_of_god_name(god: int) -> str:
    """Return the civilization label ("Greek"/"Egyptian"/"Norse"/"Atlantean"/"Chinese"/"Japanese"/"Aztec")
    for a god id.  Used wherever we need the civ as a string key — e.g. into
    `_AGE_BASE_TECHS`, into `_CIV_ARCHAIC_UNITS`, or for slot_data emission."""
    if god in _GREEK_GODS:     return "Greek"
    if god in _EGYPTIAN_GODS:  return "Egyptian"
    if god in _ATLANTEAN_GODS: return "Atlantean"
    if god in _CHINESE_GODS:   return "Chinese"
    if god in _JAPANESE_GODS:  return "Japanese"
    if god in _AZTEC_GODS:     return "Aztec"
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
    (3,3): ["cTechMythicAgeHephaestus", "cTechMythicAgeArtemis"],
    (4,1): ["cTechClassicalAgeAnubis",  "cTechClassicalAgeBast"],
    (4,2): ["cTechHeroicAgeSobek",      "cTechHeroicAgeNephthys"],
    (4,3): ["cTechMythicAgeOsiris",     "cTechMythicAgeThoth"],
    (5,1): ["cTechClassicalAgeBast",    "cTechClassicalAgePtah"],
    (5,2): ["cTechHeroicAgeSekhmet",    "cTechHeroicAgeSobek"],
    (5,3): ["cTechMythicAgeOsiris",     "cTechMythicAgeHorus"],
    (6,1): ["cTechClassicalAgePtah",    "cTechClassicalAgeAnubis"],
    (6,2): ["cTechHeroicAgeSekhmet",    "cTechHeroicAgeNephthys"],
    (6,3): ["cTechMythicAgeHorus",      "cTechMythicAgeThoth"],
    (7,1): ["cTechClassicalAgeFreyja",  "cTechClassicalAgeHeimdall"],
    (7,2): ["cTechHeroicAgeNjord",      "cTechHeroicAgeSkadi"],
    (7,3): ["cTechMythicAgeBaldr",      "cTechMythicAgeTyr"],
    (8,1): ["cTechClassicalAgeFreyja",  "cTechClassicalAgeForseti"],
    (8,2): ["cTechHeroicAgeBragi",      "cTechHeroicAgeSkadi"],
    (8,3): ["cTechMythicAgeBaldr",      "cTechMythicAgeTyr"],
    (9,1): ["cTechClassicalAgeForseti", "cTechClassicalAgeHeimdall"],
    (9,2): ["cTechHeroicAgeBragi",      "cTechHeroicAgeNjord"],
    (9,3): ["cTechMythicAgeTyr",        "cTechMythicAgeHel"],
    (13,1): ["cTechClassicalAgeAres",   "cTechClassicalAgePan"],
    (13,2): ["cTechHeroicAgeAphrodite", "cTechHeroicAgeHestia"],
    (13,3): ["cTechMythicAgeHera",      "cTechMythicAgePersephone"],
    (14,1): ["cTechClassicalAgeUllr",   "cTechClassicalAgeFreyja"],
    (14,2): ["cTechHeroicAgeAegir",     "cTechHeroicAgeBragi"],
    (14,3): ["cTechMythicAgeVidar",     "cTechMythicAgeHel"],
    (10,1): ["cTechClassicalAgePrometheus", "cTechClassicalAgeLeto"],
    (10,2): ["cTechHeroicAgeHyperion",      "cTechHeroicAgeRheia"],
    (10,3): ["cTechMythicAgeHelios",        "cTechMythicAgeAtlas"],
    (11,1): ["cTechClassicalAgePrometheus", "cTechClassicalAgeOceanus"],
    (11,2): ["cTechHeroicAgeHyperion",      "cTechHeroicAgeTheia"],
    (11,3): ["cTechMythicAgeHelios",        "cTechMythicAgeHekate"],
    (12,1): ["cTechClassicalAgeLeto",       "cTechClassicalAgeOceanus"],
    (12,2): ["cTechHeroicAgeRheia",         "cTechHeroicAgeTheia"],
    (12,3): ["cTechMythicAgeAtlas",         "cTechMythicAgeHekate"],
    # Chinese — Nuwa (15) / Fuxi (16) / Shennong (17)
    # Per Memory Files\major_and_minor_gods.docx:
    #   Fuxi:     Xuannu/Chiyou, Goumang/Nuba,   Gonggong/Huangdi
    #   Nuwa:     Xuannu/Houtu,  Goumang/Rushou, Gonggong/Zhurong
    #   Shennong: Houtu/Chiyou,  Rushou/Nuba,    Huangdi/Zhurong
    (15,1): ["cTechClassicalAgeXuannu",     "cTechClassicalAgeHoutu"],
    (15,2): ["cTechHeroicAgeGoumang",       "cTechHeroicAgeRushou"],
    (15,3): ["cTechMythicAgeGonggong",      "cTechMythicAgeZhurong"],
    (16,1): ["cTechClassicalAgeXuannu",     "cTechClassicalAgeChiyou"],
    (16,2): ["cTechHeroicAgeGoumang",       "cTechHeroicAgeNuba"],
    (16,3): ["cTechMythicAgeGonggong",      "cTechMythicAgeHuangdi"],
    (17,1): ["cTechClassicalAgeHoutu",      "cTechClassicalAgeChiyou"],
    (17,2): ["cTechHeroicAgeRushou",        "cTechHeroicAgeNuba"],
    (17,3): ["cTechMythicAgeHuangdi",       "cTechMythicAgeZhurong"],
    # Japanese — Amaterasu (18) / Tsukuyomi (19) / Susanoo (20)
    # Per Memory Files\major_and_minor_gods.docx:
    #   Amaterasu: AmeNoUzume/Minakatatomi, Hachiman/Raijin,  Takemikazuchi/Okuninushi
    #   Tsukuyomi: AmeNoUzume/InariOkami,   Hachiman/Fujin,   Watatsumi/Okuninushi
    #   Susanoo:   Minakatatomi/InariOkami, Fujin/Raijin,     Takemikazuchi/Watatsumi
    (18,1): ["cTechClassicalAgeAmeNoUzume",   "cTechClassicalAgeMinakatatomi"],
    (18,2): ["cTechHeroicAgeHachiman",        "cTechHeroicAgeRaijin"],
    (18,3): ["cTechMythicAgeTakemikazuchi",   "cTechMythicAgeOkuninushi"],
    (19,1): ["cTechClassicalAgeAmeNoUzume",   "cTechClassicalAgeInariOkami"],
    (19,2): ["cTechHeroicAgeHachiman",        "cTechHeroicAgeFujin"],
    (19,3): ["cTechMythicAgeWatatsumi",       "cTechMythicAgeOkuninushi"],
    (20,1): ["cTechClassicalAgeMinakatatomi", "cTechClassicalAgeInariOkami"],
    (20,2): ["cTechHeroicAgeFujin",           "cTechHeroicAgeRaijin"],
    (20,3): ["cTechMythicAgeTakemikazuchi",   "cTechMythicAgeWatatsumi"],
    # Aztec — Huitzilopochtli (21) / Tezcatlipoca (22) / Quetzalcoatl (23)
    # Per Memory Files\major_and_minor_gods.docx:
    #   Huitzilopochtli: Patecatl/Malinalxochitl,  Coatlicue/Itzpapalotl,   Tlaloc/Mictlantecutli
    #   Tezcatlipoca:    Malinalxochitl/Huehuecoyotl, Coyolxauhqui/Itzpapalotl, Xolotl/Mictlantecutli
    #   Quetzalcoatl:    Patecatl/Huehuecoyotl,    Coatlicue/Coyolxauhqui,  Tlaloc/Xolotl
    (21,1): ["cTechClassicalAgePatecatl",       "cTechClassicalAgeMalinalxochitl"],
    (21,2): ["cTechHeroicAgeCoatlicue",         "cTechHeroicAgeItzpapalotl"],
    (21,3): ["cTechMythicAgeTlaloc",            "cTechMythicAgeMictlantecutli"],
    (22,1): ["cTechClassicalAgeMalinalxochitl", "cTechClassicalAgeHuehuecoyotl"],
    (22,2): ["cTechHeroicAgeCoyolxauhqui",      "cTechHeroicAgeItzpapalotl"],
    (22,3): ["cTechMythicAgeXolotl",            "cTechMythicAgeMictlantecutli"],
    (23,1): ["cTechClassicalAgePatecatl",       "cTechClassicalAgeHuehuecoyotl"],
    (23,2): ["cTechHeroicAgeCoatlicue",         "cTechHeroicAgeCoyolxauhqui"],
    (23,3): ["cTechMythicAgeTlaloc",            "cTechMythicAgeXolotl"],
}

_AGE_BASE_TECHS: dict[str, dict] = {
    "Greek":     {1:"cTechClassicalAgeGreek",     2:"cTechHeroicAgeGreek",     3:"cTechMythicAgeGreek"},
    "Egyptian":  {1:"cTechClassicalAgeEgyptian",  2:"cTechHeroicAgeEgyptian",  3:"cTechMythicAgeEgyptian"},
    "Norse":     {1:"cTechClassicalAgeNorse",     2:"cTechHeroicAgeNorse",     3:"cTechMythicAgeNorse"},
    "Atlantean": {1:"cTechClassicalAgeAtlantean", 2:"cTechHeroicAgeAtlantean", 3:"cTechMythicAgeAtlantean"},
    "Chinese":   {1:"cTechClassicalAgeChinese",   2:"cTechHeroicAgeChinese",   3:"cTechMythicAgeChinese"},
    "Japanese":  {1:"cTechClassicalAgeJapanese",  2:"cTechHeroicAgeJapanese",  3:"cTechMythicAgeJapanese"},
    "Aztec":     {1:"cTechClassicalAgeAztec",     2:"cTechHeroicAgeAztec",     3:"cTechMythicAgeAztec"},
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
    # Pillars of the Gods (701-709)
    701:1, 702:1, 703:0, 704:2, 705:1, 706:2, 707:2, 708:3, 709:3,
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
    # ---------------------------------------------------------------------------
    # Pillars of the Gods (APScenarioIDs 701-709) — Chinese pantheon
    # Best-effort vanilla picks (option A from _MINOR_GOD_TECHS); only consulted
    # when random_major_gods is off. 703 starts Archaic so takes no minor techs.
    # ---------------------------------------------------------------------------
    701: ["cTechClassicalAgeChinese",  "cTechClassicalAgeHoutu"],
    702: ["cTechClassicalAgeChinese",  "cTechClassicalAgeXuannu"],
    704: ["cTechClassicalAgeChinese",  "cTechClassicalAgeHoutu",
          "cTechHeroicAgeChinese",     "cTechHeroicAgeRushou"],
    705: ["cTechClassicalAgeChinese",  "cTechClassicalAgeHoutu"],
    706: ["cTechClassicalAgeChinese",  "cTechClassicalAgeXuannu",
          "cTechHeroicAgeChinese",     "cTechHeroicAgeGoumang"],
    707: ["cTechClassicalAgeChinese",  "cTechClassicalAgeHoutu",
          "cTechHeroicAgeChinese",     "cTechHeroicAgeRushou"],
    708: ["cTechClassicalAgeChinese",  "cTechClassicalAgeXuannu",
          "cTechHeroicAgeChinese",     "cTechHeroicAgeGoumang",
          "cTechMythicAgeChinese",     "cTechMythicAgeGonggong"],
    709: ["cTechClassicalAgeChinese",  "cTechClassicalAgeHoutu",
          "cTechHeroicAgeChinese",     "cTechHeroicAgeRushou",
          "cTechMythicAgeChinese",     "cTechMythicAgeHuangdi"],
}


# ---------------------------------------------------------------------------
# Scenario-key bundling — sphere-1 scenarios (no logical requirements) per
# campaign. Used to seed the precollected starter bundle so the player
# always has something they can immediately play.
# ---------------------------------------------------------------------------
_SPHERE_ONE_BY_CAMPAIGN: dict[str, list[int]] = {
    "FOTT_GREEK":    [1, 9, 10],
    "FOTT_EGYPTIAN": [11, 16],
    "FOTT_NORSE":    [25, 29],
    "FOTT_FINAL":    [],
    "NEW_ATLANTIS":  [506, 507],
    "GOLDEN_GIFT":   [604],
}


# ---------------------------------------------------------------------------
# Archaic-age units enabled by the scenario editor per vanilla god/civ.
# These need to be explicitly forbidden if the assigned god differs.
# ---------------------------------------------------------------------------

# Units specific to a particular Greek major god (not available to other Greek gods)
_GOD_SPECIFIC_ARCHAIC_UNITS: dict[int, list] = {
    1: ["Jason", "Myrmidon"],          # Zeus
    2: ["Theseus", "Hetairos"],        # Poseidon
    3: ["Ajax", "Gastraphetoros"],     # Hades
    13: ["Orpheus", "Iolaus", "Icarus", "Midas", "AmazonArcher", "HarpyMyth"],  # Demeter
}

# Civ-wide archaic units (available for any major god of that civ)
_CIV_ARCHAIC_UNITS: dict[str, list] = {
    "Greek":     ["Pegasus", "VillagerGreek"],
    "Egyptian":  ["Mercenary", "Priest", "Pharaoh", "VillagerEgyptian"],
    "Norse":     ["Berserk", "Hersir", "VillagerDwarf", "VillagerNorse"],
    "Atlantean": ["Oracle", "VillagerAtlantean"],
    "Chinese":   ["Pioneer", "Sage", "Kuafu", "SkyLantern", "VillagerChinese"],
    "Japanese":  ["Miko", "Bushi", "OnnaMusha", "Daimyo", "Onmyoji", "VillagerJapanese"],
    "Aztec":     ["WarriorPriest", "VillagerAztec"],
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
        # gems_as_filler (opt-in) lets Gems pad framework-level filler requests
        # (start_inventory_from_pool swaps, item_links, other slots pulling
        # filler) — only meaningful when the Gem Shop is on so the Gem has value.
        gems_as_filler = bool(
            getattr(self.options, "gems_as_filler", None)
            and self.options.gems_as_filler.value
        )
        if gems_as_filler and getattr(self, "gem_shop_enabled", False):
            return self.random.choice(non_gem + [Items.aomItemData.GEM.item_name])
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
        _CIV_GODS = {"Greek": set(_GREEK_GODS), "Egyptian": set(_EGYPTIAN_GODS), "Norse": set(_NORSE_GODS), "Atlantean": set(_ATLANTEAN_GODS), "Chinese": set(_CHINESE_GODS), "Japanese": set(_JAPANESE_GODS), "Aztec": set(_AZTEC_GODS)}
        if _rmg_on:
            self.excluded_civs: frozenset[str] = frozenset(
                civ for civ, opt in [
                    ("Greek",    self.options.shuffle_greek_major_gods),
                    ("Egyptian", self.options.shuffle_egyptian_major_gods),
                    ("Norse",    self.options.shuffle_norse_major_gods),
                    ("Atlantean",self.options.shuffle_atlantean_major_gods),
                    ("Chinese",  self.options.shuffle_chinese_major_gods),
                    ("Japanese", self.options.shuffle_japanese_major_gods),
                    ("Aztec",    self.options.shuffle_aztec_major_gods),
                ] if not bool(opt.value)
            )
            # Validation: at least one pantheon must be active
            if len(self.excluded_civs) == 7:
                raise Exception(
                    "AoMR Archipelago: All pantheons are disabled. "
                    "Set at least one pantheon to true in your options YAML "
                    "(shuffle_greek_major_gods, shuffle_egyptian_major_gods, "
                    "shuffle_norse_major_gods, shuffle_atlantean_major_gods, "
                    "shuffle_chinese_major_gods, shuffle_japanese_major_gods, "
                    "or shuffle_aztec_major_gods)."
                )
        else:
            self.excluded_civs = frozenset()
        self._allowed_god_ids: set[int] = set(_ALL_GODS_WITH_ATLANTIS) - {
            g for civ in self.excluded_civs for g in _CIV_GODS.get(civ, set())
        }

        if _rmg_on:
            self.god_assignments: dict[int, int] = self._generate_god_assignments()
        else:
            self.god_assignments = {}

        # Effective civ exclusion: union of YAML-opted-out civs and civs that
        # rolled zero scenario assignments under random_major_gods.  A civ with
        # no scenarios assigned can still have its progression items (age
        # unlocks, myth-unit progression, unit unlocks) added to the pool by
        # the existing create_items logic — those items would be pure dead
        # weight, eating progression-legal slots and tightening the squeeze.
        # Treating those civs the same as YAML-excluded civs drops their
        # items from the pool automatically.
        if _rmg_on and self.god_assignments:
            _assigned_civs = {
                _civ_of_god_name(g) for g in self.god_assignments.values()
            }
            _all_civs = {"Greek", "Egyptian", "Norse", "Atlantean",
                         "Chinese", "Japanese", "Aztec"}
            _auto_excluded = (_all_civs - _assigned_civs) - set(self.excluded_civs)
            self.effective_excluded_civs: frozenset[str] = frozenset(
                self.excluded_civs | (_all_civs - _assigned_civs)
            )
            if _auto_excluded:
                logger.info(
                    "AoMR: auto-excluded civs with zero scenario assignments "
                    f"under random_major_gods: {sorted(_auto_excluded)}. "
                    "Their age unlocks, myth-unit progression, and unit "
                    "items are dropped from the pool."
                )
        else:
            self.effective_excluded_civs = frozenset(self.excluded_civs)
        self.minor_god_assignments: dict[int, list] = self._generate_minor_god_assignments()
        self.minor_god_full: dict[int, dict]        = self._generate_minor_god_full()
        self.archaic_forbids: dict[int, list]       = self._generate_archaic_forbids()
        # Shop generation (only when gem_shop is enabled)
        self.gem_shop_enabled: bool = bool(self.options.gem_shop.value)
        if self.gem_shop_enabled:
            self.shop_obelisk_assignments, self.shop_progression_slots, self.shop_filler_only = (
                self._generate_shop_assignments()
            )
            # Pre-pick the EXCLUDED shop slots here (rather than lazily in Rules.py)
            # so create_items can size useful capacity correctly.  EXCLUDED slots
            # accept only filler/trap, so they shrink the useful-pool ceiling
            # alongside strict filler-only slots.
            from .locations.Locations import ALL_SHOP_ITEM_IDS as _ALL_SHOP_IDS
            _all_prog = set()
            for _ids in self.shop_progression_slots.values():
                _all_prog.update(_ids)
            _excludable = [lid for lid in _ALL_SHOP_IDS if lid not in _all_prog]
            self.random.shuffle(_excludable)
            self.shop_excluded_ids: set[int] = set(_excludable[: self.random.randint(8, 11)])
        else:
            self.shop_obelisk_assignments = {}
            self.shop_progression_slots   = {}
            self.shop_filler_only         = set()
            self.shop_excluded_ids: set[int] = set()

        # Relicsanity flag — read once so Regions/Rules/create_items can branch on it.
        self.relicsanity_enabled: bool = bool(self.options.relicsanity.value)

        # Optional-objective-sanity flag — Regions.py filters OPTIONAL_OBJECTIVE
        # locations out when off, and the location counts below honor it.
        # HOTFIX: optional objectives are not fully wired yet — force OFF
        # regardless of the YAML option.  Revert to the line below when ready.
        # self.optional_objectives_enabled: bool = bool(
        #     self.options.optional_objectives_are_locations.value
        # )
        self.optional_objectives_enabled: bool = False

        # Local-filler staging list: filler items destined for local-only
        # placement are collected here during create_items, then placed by
        # pre_fill via fast_fill into this player's own unfilled locations.
        self.local_filler_items: list[Item] = []

        # Disabled-campaign set: campaigns can be opted out via YAML.
        # FOTT_FINAL is always enabled (its scenarios are the goal).
        #
        # ADDING A CAMPAIGN — every optional campaign MUST be wired here.  This
        # set is the single source of truth that Regions.py, Locations.py,
        # Rules.py, create_items (pool sizing), the keyring assignment and
        # fill_slot_data all consult to skip a campaign's scenarios/locations.
        # A campaign that has a `<name>_campaign` YAML toggle but is NOT added
        # to this set will be force-generated regardless of the option (its
        # scenarios, locations, keys and pool slots all materialize), inflating
        # item-placement load and silently ignoring the player's choice.  Add a
        # matching `if not bool(self.options.<opt>.value): ...add(<CAMPAIGN>)`
        # line below, then make sure the campaign appears in aomCampaignData,
        # aomScenarioData and the location tables.
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
        # HOTFIX: Pillars of the Gods is not fully wired yet — force-disable
        # regardless of the YAML option.  Revert to the option check below
        # (uncomment) when the campaign is ready to ship.
        # if not bool(self.options.pillars_of_the_gods.value):
        #     self.disabled_campaigns.add(aomCampaignData.PILLARS_OF_THE_GODS)
        self.disabled_campaigns.add(aomCampaignData.PILLARS_OF_THE_GODS)

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

        # Per-scenario exclusion set (global_numbers).  An excluded scenario
        # behaves like one in a disabled campaign: no region, no locations, no
        # scenario key, no completion event.  Every aomScenarioData loop that
        # honors disabled_campaigns also skips these numbers.  Currently only
        # scenario 30 ("All Is Not Lost") — the highest point gate — via the
        # exclude_scenario_30 option (default on).
        from .locations.Scenarios import aomScenarioData as _ScenData
        self.excluded_scenarios: set[int] = set()
        # Scenario 30 ("All Is Not Lost") is the highest point gate.  When
        # exclude_scenario_30 is on we keep it out of progression, but HOW
        # depends on whether scenario keys are in use:
        #   * keys on  -> no key is generated for it, so it is unreachable;
        #     fully exclude it (no region/locations/completion/key).
        #   * keys off -> access is governed only by the campaign-unlock item,
        #     which can't gate a single scenario, so the player can always
        #     launch it.  Keep its locations but force them filler-only (see
        #     filler_only_scenarios) so no progression is ever required behind
        #     it and beating it just yields filler.
        self.filler_only_scenarios: set[int] = set()
        if bool(self.options.exclude_scenario_30.value) and \
                _ScenData.FOTT_30.campaign not in self.disabled_campaigns:
            if int(self.options.max_keys_on_keyrings.value) > 0:
                self.excluded_scenarios.add(_ScenData.FOTT_30.global_number)
            else:
                self.filler_only_scenarios.add(_ScenData.FOTT_30.global_number)

        # Multiworld-size point-threshold scale: eases per-scenario point gates
        # in large asyncs (where filler point items are spread thin) while
        # preserving the gradient.  Read by Rules.set_scenario_age_and_point_rules
        # and the client's reachability replica (via slot_data).
        self.points_scale: float = Rules._multiworld_scale_factor(self.multiworld.players)

        # Auto-clamp x_scenarios to the number of enabled non-final scenarios.
        # If beat_x_scenarios mode asks the player to beat more scenarios than
        # exist in the active campaigns, the Final section can never unlock and
        # generation will fail downstream. Clamp + warn.
        if int(self.options.final_scenarios.value) == FinalScenarios.option_beat_x_scenarios:
            from .locations.Scenarios import aomScenarioData
            enabled_scenario_count = sum(
                1 for s in aomScenarioData
                if s.campaign not in self.disabled_campaigns
                and s.campaign != aomCampaignData.FOTT_FINAL
                and s.global_number not in self.excluded_scenarios
            )
            requested = int(self.options.x_scenarios.value)
            if requested > enabled_scenario_count:
                logger.warning(
                    f"AoMR: x_scenarios={requested} exceeds the number of "
                    f"enabled non-final scenarios ({enabled_scenario_count}). "
                    f"Clamping x_scenarios to {enabled_scenario_count} so the "
                    "Final section can actually unlock."
                )
                self.options.x_scenarios.value = enabled_scenario_count

            # Feasibility clamp (coarse pre-pass).  Replay the per-scenario
            # reachability rules with EVERY catalog item held (99 copies each) —
            # an upper bound on what fill could ever make completable.  Scenarios
            # still out of logic here can NEVER be completed no matter how fill
            # places items (e.g. a god draw whose scenario-32 civ can't reach the
            # age its gate needs), so clamp x down to that ceiling instead of
            # failing hours into fill with an opaque "Game appears as unbeatable".
            #
            # This pass OVERCOUNTS: 99-of-everything feeds count_points far more
            # points than the finite real pool grants, so point-gated scenarios
            # the real pool can't satisfy still read reachable.  A second,
            # authoritative clamp in create_items() (see _reclamp_x_scenarios)
            # re-runs this with the ACTUAL pool counts once the pool exists and
            # tightens x further.  This pass stays as a cheap early reject for the
            # structurally-impossible cases (bad god draw) that don't need the
            # pool to detect.
            from .items import Items as _Items
            _max_state = {name: 99 for name in _Items.item_name_to_id}
            max_reach = self._max_reachable_nonfinal_scenarios(_max_state)
            current_x = int(self.options.x_scenarios.value)
            if current_x > max_reach:
                logger.warning(
                    f"AoMR: only {max_reach} scenarios are completable even "
                    "with every item under this seed's god assignment "
                    f"(x_scenarios={current_x}). Clamping x_scenarios to "
                    f"{max_reach} so the Final section can actually unlock."
                )
                self.options.x_scenarios.value = max_reach

        # Pre-determined random god powers per scenario per tier (uses self.random
        # for deterministic regeneration). Must run after disabled_campaigns is set.
        self.god_power_assignments: dict[int, list[str]] = self._generate_god_power_assignments()

        # Scenario-key bundling — must run after disabled_campaigns is set (so we
        # only bundle scenarios in active campaigns) and after god_assignments
        # (not strictly needed but keeps RNG ordering predictable).
        self._generate_keyring_assignments()

        # `start_inventory_from_pool: Gem: N` support — Gems are force-placed
        # by Rules.place_gems and never live in itempool, so AP's default
        # processing emits a "tried to remove items that don't exist" warning
        # and does nothing.  We intercept here: precollect N Gems via
        # create_items + skip N Victory placements via place_gems so the
        # economy stays balanced (N earned gems get swapped for filler in the
        # pool, player starts with those N gems instead).
        self.starting_gems_from_pool: int = 0
        if self.gem_shop_enabled:
            sifp = getattr(self.options, "start_inventory_from_pool", None)
            sifp_val = getattr(sifp, "value", None) if sifp else None
            if isinstance(sifp_val, dict):
                _n = int(sifp_val.get("Gem", 0) or 0)
                if _n > 0:
                    self.starting_gems_from_pool = _n
                    # Pop the entry so AP's own start_inventory_from_pool pass
                    # doesn't warn about a non-pool item — we handle precollect
                    # + Victory swap ourselves below.
                    sifp_val.pop("Gem", None)

        # Shop E (gem sink) — only enabled when the gem pool can afford every
        # A-D slot plus every E card.  Must run after gem_shop_enabled and
        # disabled_campaigns are settled.
        self._generate_shop_e()


    def _generate_shop_e(self) -> None:
        """Generate Shop E deck composition and gem-budget gate.

        Shop E is the post-A-D gem sink.  48 cards distributed across 4 decks
        of 12, with progressive top-down reveal in the AP client UI.

        Card kinds per spec:
          * 4 "useful-or-worse" cards    — may hold useful/filler/trap
          * 4 "mission-hint" cards        — when purchased, client broadcasts a
                                            hint for one unbeaten scenario
          * 40 "filler-only" cards        — filler/trap only

        Shuffle (per user spec):
          1. Combine 40 filler + 4 hint = 44 cards, shuffle → `big`.
          2. Take big[:8].  Add 4 useful → `small` of 12.  Shuffle small.
          3. Big remainder = big[8:] = 36 cards.  Slice into 4 decks of 9.
          4. Distribute small evenly: 3 cards per deck, prepended to its 9.

        Result: each of the 4 decks = 12 ordered cards; top 3 positions of
        any deck draw from `small`, so useful cards always land near the top.

        Gem-budget gate: gems_in_pool >= cost(A-D) + cost(E).  When the gate
        fails, Shop E stays disabled — no locations registered, no items added,
        no UI tab.
        """
        # Attributes always defined so downstream code can branch cleanly.
        self.shop_e_enabled: bool                  = False
        self.shop_e_decks:   list[list[int]]       = []   # 4 lists of 12 loc_ids
        self.shop_e_card_kind: dict[int, str]      = {}   # loc_id -> "useful"|"hint"|"filler"
        self.shop_e_useful_ids: set[int]           = set()
        self.shop_e_hint_ids:   set[int]           = set()
        self.shop_e_filler_ids: set[int]           = set()

        if not self.gem_shop_enabled:
            return

        from .locations.Locations import (
            SHOP_E_LOCATION_IDS, SHOP_E_DECK_COUNT,
            SHOP_E_DEFAULT_DECK_DEPTH, SHOP_E_MAX_DECK_DEPTH,
            ALL_SHOP_ITEM_IDS, ALL_PROGRESSIVE_INFO_IDS,
        )
        from .locations.Scenarios import aomScenarioData
        from .locations.Campaigns import aomCampaignData as _C

        # ---- Gem budget --------------------------------------------------
        # Gems = 1 per active scenario victory except FOTT_32 (which is the goal).
        active_scenarios = [
            s for s in aomScenarioData
            if s.campaign not in self.disabled_campaigns
            and not (s.campaign == _C.FOTT_FINAL and s.global_number == 32)
        ]
        gems_in_pool = len(active_scenarios)

        # A-D buyable buttons:
        #   A = 6 items + 2 mission hints                     = 8
        #   B = 4 items + 1 PSI + 2 mission hints              = 7
        #   C = 3 items + 1 PSI + 1 mission hint               = 5
        #   D = 2 items + 1 PSI                                = 3
        # Total = 23.  Shop E unlocks at >= 24 gems (i.e. >= 1 excess).
        from .locations.Locations import SHOP_SLOT_ORDER
        ad_cost = len(SHOP_SLOT_ORDER)
        excess  = gems_in_pool - ad_cost
        if excess < 1:
            return

        # ---- Per-deck depth -------------------------------------------------
        # Player can buy `excess` cards from Shop E in total.  We size each deck
        # so the shop can absorb the excess (and a bit more) without going
        # absurdly deep on small-excess seeds:
        #   excess in [1, default-1]   → depth = excess           (1..11)
        #   excess in [default, 4*default] → depth = default      (12)
        #   excess > 4*default         → depth = ceil(excess / 4) (≥ 13)
        # Always clamped to [1, SHOP_E_MAX_DECK_DEPTH].
        if excess >= SHOP_E_DECK_COUNT * SHOP_E_DEFAULT_DECK_DEPTH:
            from math import ceil
            per_deck_depth = ceil(excess / SHOP_E_DECK_COUNT)
        else:
            per_deck_depth = min(excess, SHOP_E_DEFAULT_DECK_DEPTH)
        per_deck_depth = max(1, min(per_deck_depth, SHOP_E_MAX_DECK_DEPTH))

        total_cards = SHOP_E_DECK_COUNT * per_deck_depth

        # ---- Card-kind composition ------------------------------------------
        # 4 useful (always — 1 per deck minimum), then up to 4 hints, then
        # filler fills the rest.  Drop filler first, then hints, when total
        # is small.
        useful_count = SHOP_E_DECK_COUNT                                    # 4
        hint_count   = max(0, min(SHOP_E_DECK_COUNT, total_cards - useful_count))
        filler_count = max(0, total_cards - useful_count - hint_count)

        ids = list(SHOP_E_LOCATION_IDS[:total_cards])
        useful_ids = set(ids[:useful_count])
        hint_ids   = set(ids[useful_count:useful_count + hint_count])
        filler_ids = set(ids[useful_count + hint_count:])

        # ---- Shuffle so useful cards land near the top of every deck --------
        #
        # We carve `top_per_deck = min(3, depth)` slots off the top of each
        # deck.  All 4 useful cards plus enough hint/filler to fill the
        # top region go into the "top pool", which is shuffled then sliced
        # `top_per_deck` cards into each of the 4 output decks.  The rest of
        # the cards go into a "bottom pool", shuffled and sliced into the
        # bottom of each deck.  This guarantees useful cards are always within
        # the first `top_per_deck` positions of some deck — even when depth=1
        # (each deck IS just the useful card).
        top_per_deck     = min(3, per_deck_depth)
        bottom_per_deck  = per_deck_depth - top_per_deck
        top_pool_size    = SHOP_E_DECK_COUNT * top_per_deck
        bottom_pool_size = SHOP_E_DECK_COUNT * bottom_per_deck

        non_useful = list(hint_ids) + list(filler_ids)
        self.random.shuffle(non_useful)
        top_non_useful_needed = top_pool_size - useful_count
        top_non_useful        = non_useful[:top_non_useful_needed]
        bottom_pool           = non_useful[top_non_useful_needed:top_non_useful_needed + bottom_pool_size]

        top_pool = list(useful_ids) + top_non_useful
        self.random.shuffle(top_pool)

        decks: list[list[int]] = []
        for d in range(SHOP_E_DECK_COUNT):
            top    = top_pool[d * top_per_deck:(d + 1) * top_per_deck]
            bottom = bottom_pool[d * bottom_per_deck:(d + 1) * bottom_per_deck]
            decks.append(top + bottom)
            assert len(decks[-1]) == per_deck_depth, "Shop E deck size mismatch"

        # ---- Stash --------------------------------------------------------
        self.shop_e_enabled        = True
        self.shop_e_decks          = decks
        self.shop_e_useful_ids     = useful_ids
        self.shop_e_hint_ids       = hint_ids
        self.shop_e_filler_ids     = filler_ids
        self.shop_e_per_deck_depth = per_deck_depth
        self.shop_e_active_ids     = set(ids)   # subset of SHOP_E_LOCATION_IDS we actually use
        kind_map = {}
        for lid in useful_ids: kind_map[lid] = "useful"
        for lid in hint_ids:   kind_map[lid] = "hint"
        for lid in filler_ids: kind_map[lid] = "filler"
        self.shop_e_card_kind = kind_map


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

        max_prog = int(self.options.max_progression_items_in_each_shop.value)
        max_prog = max(0, min(ITEMS_PER_SHOP, max_prog))

        # Gem-shop softlock guard.  Only relevant when gem_shop is on (this
        # function is only called in that case).  When shops are
        # immediately accessible and key rings carry few keys (i.e. there
        # are many small ring items in the pool), progression items in
        # shops can be paid for in the wrong order and soft-lock the
        # seed.  Two layers:
        #   * Hard clamp — auto-zero progression-in-shops on the worst
        #     combination, so the seed stays solvable no matter how the
        #     player spends gems.  Scenario keys must be enabled
        #     (max_keys_on_keyrings > 0) for this branch to apply;
        #     a value of 0 disables scenario keys entirely and removes
        #     that specific softlock vector.
        #   * Advisory warning — emit on a looser set of risky combos so
        #     players get a heads-up without forcing a behaviour change.
        wins_to_open = int(self.options.wins_to_open_shop.value)
        ring_cap     = int(self.options.max_keys_on_keyrings.value)
        if max_prog > 0:
            if wins_to_open <= 1 and 0 < ring_cap <= 2:
                logger.warning(
                    "AoMR: gem-shop softlock risk detected "
                    f"(wins_to_open_shop={wins_to_open}, "
                    f"max_keys_on_keyrings={ring_cap}, "
                    f"max_progression_items_in_each_shop={max_prog}). "
                    "With shops opening immediately and very small key "
                    "rings, gems spent on the wrong shop slots can "
                    "soft-lock the seed. Auto-clamping "
                    "max_progression_items_in_each_shop to 0."
                )
                max_prog = 0
            elif wins_to_open <= 2 or 0 < ring_cap <= 3:
                logger.warning(
                    "AoMR: gem-shop softlock risk "
                    f"(wins_to_open_shop={wins_to_open}, "
                    f"max_keys_on_keyrings={ring_cap}, "
                    f"max_progression_items_in_each_shop={max_prog}). "
                    "Shops open quickly and/or key rings carry few keys. "
                    "Spending gems on the wrong progression slots "
                    "may soft-lock progress. Generation continues."
                )

        for tier_name, _display, item_obs, _hint_obs in SHOP_TIER_CONFIGS:
            locs = list(TIER_ITEM_IDS[tier_name])  # 15 location IDs for this tier
            self.random.shuffle(locs)

            # Marsh (tier A) never allows progression regardless of the option.
            n_prog = 0 if tier_name == "A" else max_prog
            progression_slots[tier_name] = set(locs[:n_prog])

            # Of the remaining slots, randomly pick ~50% to be filler-only
            # (only `filler` classification allowed).  The other ~50% accept
            # `useful` items as well as filler/traps, giving the pool more
            # breathing room when the useful list is large.
            non_prog = locs[n_prog:]
            n_filler_only = round(len(non_prog) * 0.5)
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
        Respects self._allowed_god_ids to exclude disabled civilizations.
        When more_frequent_dlc_gods is enabled, biases each Greek pick toward
        Demeter (id 13) and each Norse pick toward Freyr (id 14) at 50%."""
        force    = bool(self.options.force_different_god.value)
        # more_frequent_dlc_gods is hidden from players; treat as always off.
        dlc_bias = False
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
            assignments[scenario_id] = self._weighted_god_choice(candidates, dlc_bias)
        return assignments

    def _weighted_god_choice(self, candidates: list, dlc_bias: bool = False) -> int:
        """Pick one god from `candidates`. When `dlc_bias` is on, each civ
        present in `candidates` first rolls 50/50 between its DLC god and the
        rest of that civ's gods; then a civ is picked, then a god within it.
        Without the bias this is just a uniform random choice (legacy behavior)."""
        if not dlc_bias:
            return self.random.choice(candidates)
        cand_set = set(candidates)
        # Group candidates by civ, partitioning Greek/Norse into DLC vs base.
        # `_DLC_GOD_BY_CIV` lists the DLC major per civ; if it's not in the
        # candidate pool (e.g. excluded by force_different_god), no bias applies.
        _DLC_GOD_BY_CIV = {"Greek": 13, "Norse": 14}
        civs_present = sorted({_civ_of_god_name(g) for g in cand_set})
        chosen_civ = self.random.choice(civs_present)
        civ_pool = [g for g in cand_set if _civ_of_god_name(g) == chosen_civ]
        dlc_id = _DLC_GOD_BY_CIV.get(chosen_civ)
        if dlc_id is not None and dlc_id in civ_pool:
            others = [g for g in civ_pool if g != dlc_id]
            if others and self.random.random() < 0.5:
                return dlc_id
            if not others:
                return dlc_id
            return self.random.choice(others)
        return self.random.choice(civ_pool)

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
            ["Bolt", "Deconstruction", "LocustSwarm", "GreatHunt", "Shockwave", "GaiaForest",
             "Creation", "SolarShield", "BloodPact", "Tailwind"],
            ["Restoration", "Carnivora", "SpiderLair", "Eclipse",
            "ShiftingSands", "PlagueOfSerpents", "Undermine", "HealingSpring",
            "AsgardianBastion", "Vanish", "LightningWeapons", "EarthWall",
            "Swampland", "Goshinboku", "Infestation", "AgaveBloom", "Lullaby"],
            ["Traitor", "FlamingWeapons", "UnderworldPassage", "Bronze", "Curse",
            "Ancestors", "WalkingWoods", "Frost", "Chaos", "HesperidesTree",
            "Tempest", "ForestProtection", "DroughtLand", "VenomBeast",
            "ThunderBurst", "SmitingGust", "Purge", "EarthMonster", "Starfall"],
            ["LightningStorm", "Earthquake", "Meteor", "Tornado", "Nidhogg",
            "Implode", "TartarianGate", "Inferno", "GreatFlood", "YinglongsWrath",
            "BlazingPrairie", "DivineSlash", "DragonTyphoon", "Volcano",
            "MonolithOfTlaloc"],
        ]

        result: dict[int, list[str]] = {}

        for scenario in aomScenarioData:
            scenario_id = scenario.global_number

            if scenario.campaign in self.disabled_campaigns:
                result[scenario_id] = []
                continue

            result[scenario_id] = [self.random.choice(pool) for pool in TIER_POOLS]

        return result

    def _generate_keyring_assignments(self) -> None:
        """Compute scenario-key Key Ring assignments per the
        `max_keys_on_keyrings` option.

        Semantics:
          * max = 0  -> feature disabled. No keys at all; scenarios are not
            gated by Scenario Keys.
          * max = 1  -> individual Scenario Key items (one per scenario)
            shuffled directly into the multiworld. No Key Ring items.
          * max >= 2 -> scenarios bundled onto Key Ring items.  Each ring
            carries 1..max scenario keys, size rolled with a discrete
            binomial(n=max-1, p=0.5) + 1 distribution (mode near (max+1)/2).
            The starter ring (precollected) carries exactly ceil(max/2)
            scenarios and is guaranteed to include at least one sphere-1
            scenario so the player has something to play immediately.
            Receiving any ring delivers every scenario key it carries.

        Result attributes (always set, even when feature disabled):
          * `max_keys_on_keyrings` (int)
          * `scenario_bundles` (list[list[int]]) — ring index → scenario IDs
                (index 0 = starter ring; matches order of rings)
          * `scenario_to_key_id` (dict[int, int]) — scenario global → AP key id
          * `scenario_to_ring_item_id` (dict[int, int]) — scenario global → AP
                ring item id that carries it (empty when max <= 1)
          * `ring_item_id_to_scenarios` (dict[int, list[int]]) — AP ring item id
                → list of scenario global numbers (empty when max <= 1)
          * `ring_display_names` (dict[int, str]) — AP ring item id → friendly
                name ("Scenario Key Ring 3") (empty when max <= 1)
          * `starter_ring_item_id` (int | None) — the precollected ring item id
                when max >= 2 (None otherwise)
          * `starter_scenario_key_ids` (list[int]) — precollected individual
                Scenario Key item ids when max == 1 (mirrors old behavior)
        """
        from .locations.Scenarios import aomScenarioData

        N = int(self.options.max_keys_on_keyrings.value)
        self.max_keys_on_keyrings = N
        self.scenario_bundles: list[list[int]] = []
        self.scenario_to_key_id: dict[int, int] = {}
        self.scenario_to_ring_item_id: dict[int, int] = {}
        self.ring_item_id_to_scenarios: dict[int, list[int]] = {}
        self.ring_display_names: dict[int, str] = {}
        self.starter_ring_item_id: int | None = None
        self.starter_scenario_key_ids: list[int] = []

        if N <= 0:
            return

        # All active scenario IDs (in active campaigns).  FOTT_FINAL (31 & 32)
        # is excluded: access to the final scenarios is governed solely by the
        # final_scenarios option (always_open / beat_x / atlantis_key), never by
        # scenario keys or key rings, regardless of max_keys_on_keyrings.
        from .locations.Campaigns import aomCampaignData as _C_keys
        active_scenarios: list[int] = [
            s.global_number for s in aomScenarioData
            if s.campaign not in self.disabled_campaigns
            and s.campaign != _C_keys.FOTT_FINAL
            and s.global_number not in self.excluded_scenarios
        ]
        if not active_scenarios:
            return

        # Per-scenario key id map is always populated so other code paths
        # (slot_data, debugging) can still resolve scenario -> key item id
        # even when keys are bundled onto rings.
        for sid in active_scenarios:
            kid = Items.SCENARIO_TO_KEY_ID.get(sid)
            if kid is not None:
                self.scenario_to_key_id[sid] = kid

        # Starter sphere-1 seed: at least one scenario the player can attempt
        # immediately (matches starting campaign when possible).
        start_campaign = self._starting_campaign()
        sphere_ones = [
            sid for sid in _SPHERE_ONE_BY_CAMPAIGN.get(start_campaign.name, [])
            if sid in active_scenarios
        ]
        if not sphere_ones:
            for camp_name, ids in _SPHERE_ONE_BY_CAMPAIGN.items():
                sphere_ones = [sid for sid in ids if sid in active_scenarios]
                if sphere_ones:
                    break

        remaining_pool = list(active_scenarios)
        self.random.shuffle(remaining_pool)

        # ---- max == 1: per-scenario keys, no rings ----
        if N == 1:
            # Starter "bundle" is still ceil(1/2) = 1 scenario for symmetry.
            starter: list[int] = []
            if sphere_ones:
                seed_sid = self.random.choice(sphere_ones)
                starter.append(seed_sid)
                remaining_pool.remove(seed_sid)
            self.scenario_bundles = [starter] + [[sid] for sid in remaining_pool]
            self.starter_scenario_key_ids = [
                self.scenario_to_key_id[sid]
                for sid in starter if sid in self.scenario_to_key_id
            ]
            return

        # ---- max >= 2: bundle onto Key Ring items ----
        # Starter ring size = ceil(N/2), always (no binomial roll for starter).
        starter_size = (N + 1) // 2
        starter_size = min(starter_size, len(active_scenarios))

        starter: list[int] = []
        if sphere_ones:
            seed_sid = self.random.choice(sphere_ones)
            starter.append(seed_sid)
            remaining_pool.remove(seed_sid)
        while len(starter) < starter_size and remaining_pool:
            starter.append(remaining_pool.pop())

        bundles: list[list[int]] = [starter]

        # Non-starter rings: size ~ 1 + Binomial(n=max-1, p=0.5).
        # Range [1, max], mode near (max+1)/2; max-sized rings rare.
        # self.random has no binomialvariate, so sample via sum of fair coins.
        while remaining_pool:
            roll_size = 1 + sum(
                1 for _ in range(N - 1) if self.random.random() < 0.5
            )
            roll_size = max(1, min(roll_size, len(remaining_pool)))
            bundles.append(remaining_pool[:roll_size])
            remaining_pool = remaining_pool[roll_size:]

        self.scenario_bundles = [list(b) for b in bundles]

        # Allocate stable ring item ids from the static registry, one per
        # ring index (index 0 = starter -> ring 1, index 1 -> ring 2, ...).
        for ring_idx, scenarios in enumerate(self.scenario_bundles):
            ring_index_1based = ring_idx + 1
            ring_item_id = Items.RING_INDEX_TO_ITEM_ID.get(ring_index_1based)
            if ring_item_id is None:
                # Safety: more rings than pre-allocated.  Should not happen
                # because MAX_KEY_RINGS == total scenarios across all campaigns.
                raise RuntimeError(
                    f"AoMR: more key rings ({len(self.scenario_bundles)}) than "
                    f"pre-allocated ring item IDs ({len(Items.RING_INDEX_TO_ITEM_ID)})."
                )
            self.ring_item_id_to_scenarios[ring_item_id] = list(scenarios)
            self.ring_display_names[ring_item_id] = Items.item_id_to_name[ring_item_id]
            for sid in scenarios:
                self.scenario_to_ring_item_id[sid] = ring_item_id

        # Index 0 is the starter ring.
        if self.scenario_bundles:
            self.starter_ring_item_id = Items.RING_INDEX_TO_ITEM_ID[1]

    def _max_reachable_nonfinal_scenarios(self, received_counts: dict) -> int:
        """Number of non-Final scenarios completable when the player holds the
        item counts in `received_counts`.  Used by both feasibility clamps:
        generate_early passes 99-of-everything (coarse upper bound); create_items
        passes the actual pool tally (authoritative).  max_keys=0 so the key gate
        never blocks — keys are obtainable items, not a structural ceiling."""
        from .locations.Scenarios import aomScenarioData
        _campaign_unlocked = {
            c.id: (c not in self.disabled_campaigns) for c in Campaigns.aomCampaignData
        }
        _reach = Rules.compute_scenarios_in_logic(
            received_counts=received_counts,
            god_assignments=self.god_assignments,
            campaign_unlocked_by_id=_campaign_unlocked,
            scenario_to_gate_id={},
            held_gate_ids=set(),
            max_keys_on_keyrings=0,
            disabled_campaign_ids={c.id for c in self.disabled_campaigns},
            minor_god_assignments=getattr(self, "minor_god_assignments", {}),
            trap_percentage=int(self.options.trap_percentage.value),
            excluded_scenario_numbers=self.excluded_scenarios,
            multiworld_scale=self.points_scale,
        )
        _final_ids = {
            s.global_number for s in aomScenarioData
            if s.campaign == Campaigns.aomCampaignData.FOTT_FINAL
        }
        return sum(1 for n, ok in _reach.items() if ok and n not in _final_ids)

    def _reclamp_x_scenarios(self, itempool: list) -> None:
        """Authoritative feasibility clamp using the REAL pool counts.

        The generate_early clamp uses 99-of-everything and overcounts points, so
        vanilla-god seeds with x near the enabled count can still abort fill
        "Game appears as unbeatable".  Once create_items has built the actual
        pool we know exactly how many point-bearing copies the player can ever
        hold, so re-run the reachability sweep with those counts and clamp x down
        to what is genuinely completable.  Runs before set_rules (Final gate) and
        fill_slot_data, so the tightened value propagates to both."""
        if int(self.options.final_scenarios.value) != FinalScenarios.option_beat_x_scenarios:
            return
        received_counts: dict = {}
        for it in itempool:
            received_counts[it.name] = received_counts.get(it.name, 0) + 1
        for it in self.multiworld.precollected_items.get(self.player, []):
            received_counts[it.name] = received_counts.get(it.name, 0) + 1
        max_reach = self._max_reachable_nonfinal_scenarios(received_counts)
        current_x = int(self.options.x_scenarios.value)
        if current_x > max_reach:
            logger.warning(
                f"AoMR: with the actual item pool only {max_reach} scenarios are "
                f"completable under this seed's god assignment (x_scenarios="
                f"{current_x}). Clamping x_scenarios to {max_reach} so the Final "
                "section can actually unlock."
            )
            self.options.x_scenarios.value = max_reach

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
                               Items.MythUnitUnlockFiller, Items.AtlanteanMythUnitUnlock,
                               Items.ChineseMythUnitUnlock, Items.JapaneseMythUnitUnlock,
                               Items.AztecMythUnitUnlock)
        atlantean_types    = (Items.AtlanteanUnitUnlockProgression, Items.AtlanteanUnitUnlockUseful,
                               Items.AtlanteanMythUnitUnlock)
        chinese_types      = (Items.ChineseUnitUnlockProgression, Items.ChineseUnitUnlockUseful,
                               Items.ChineseMythUnitUnlock)
        japanese_types     = (Items.JapaneseUnitUnlockProgression, Items.JapaneseUnitUnlockUseful,
                               Items.JapaneseMythUnitUnlock)
        aztec_types        = (Items.AztecUnitUnlockProgression, Items.AztecUnitUnlockUseful,
                               Items.AztecMythUnitUnlock)
        random_major_gods_on        = bool(self.options.random_major_gods.value)
        # Native-DLC-civ campaigns: their scenarios are played as that civ, so the
        # civ's unit items must be in the pool whenever the campaign is enabled,
        # even with random_major_gods off (otherwise those scenarios are
        # unbeatable — see the Atlantean/Chinese skip guards below).
        _new_atlantis_in_pool = Campaigns.aomCampaignData.NEW_ATLANTIS not in self.disabled_campaigns
        _pillars_in_pool      = Campaigns.aomCampaignData.PILLARS_OF_THE_GODS not in self.disabled_campaigns

        # Age unlocks are never precollected — players use start_inventory or
        # start_inventory_from_pool in their YAML if they want starting unlocks.
        starting_age_unlocks = {
            "Greek": 0, "Egyptian": 0, "Norse": 0, "Atlantean": 0, "Chinese": 0,
            "Japanese": 0, "Aztec": 0,
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

            # Chaneque starting-army item is retained only for back-compat with
            # already-generated seeds (XS still spawns Chaneque for its id).
            # New generation uses Centzon Totochtin instead, so keep it out of the pool.
            if item == Items.aomItemData.STARTING_ARMY_CHANEQUE:
                continue

            # Scenario Keys and Key Ring items are not aomItemData enum
            # members (registered as duck-typed objects in items/Items.py).
            # They are pushed explicitly below depending on
            # `self.max_keys_on_keyrings`: 0 -> none, 1 -> per-scenario keys,
            # >=2 -> Key Ring items only.

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

            # Titan Age unlocks — added explicitly below (one per activated civ,
            # gated by random_major_gods + civ exclusion).  Skip here so they
            # aren't also bucketed by the generic useful path (which would
            # duplicate every civ's Titan Age item in the pool).
            if item_type == Items.TitanAgeUnlock:
                continue

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

            # Amanra items — removed when BOTH FotT Egyptian and FotT Norse
            # campaigns are disabled (Amanra is the Egyptian campaign hero and
            # also features in Norse scenarios; without either campaign she
            # never appears in active gameplay, so her ability items are dead
            # weight in the pool).
            _is_amanra_item = (
                getattr(item.type, "hero", "") == "Amanra"
                or item.item_name.startswith("Amanra ")
            )
            if _is_amanra_item:
                from .locations.Campaigns import aomCampaignData as _C
                _egypt_disabled = _C.FOTT_EGYPTIAN in self.disabled_campaigns
                _norse_disabled = _C.FOTT_NORSE in self.disabled_campaigns
                if _egypt_disabled and _norse_disabled:
                    continue

            # Arkantos/Chiron items — removed when ALL FotT campaigns (Greek,
            # Egyptian, Norse) are disabled (i.e. only new campaigns enabled).
            # "Chiron didn't die" — Norse-specific carve-out (must come before
            # the generic Chiron exclusion below).  This item spawns ChironSPC
            # only in FotT 29/30/31/32, so it's dead weight if Norse is off,
            # but has value as long as Norse is on (independent of Greek /
            # Egyptian state).
            if item == Items.aomItemData.CHIRON_DIDNT_DIE:
                from .locations.Campaigns import aomCampaignData as _C
                if _C.FOTT_NORSE in self.disabled_campaigns:
                    continue
                # Skip the generic Chiron block below — its all-FotT-disabled
                # rule would also be true if Norse is on, but the override
                # logic should NOT fall through, since this item is already
                # being kept by the check above.
                pass  # fall through to classification bucket

            _is_arkantos_item = (
                getattr(item.type, "hero", "") == "Arkantos"
                or item.item_name.startswith("Arkantos ")
                or isinstance(item.type, Items.ArkantosHousing)
            )
            _is_chiron_item = (
                getattr(item.type, "hero", "") == "Chiron"
                or item.item_name.startswith("Chiron ")
            )
            if (_is_arkantos_item or _is_chiron_item) \
                    and item != Items.aomItemData.CHIRON_DIDNT_DIE:
                from .locations.Campaigns import aomCampaignData as _C
                _all_fott_disabled = (
                    _C.FOTT_GREEK in self.disabled_campaigns
                    and _C.FOTT_EGYPTIAN in self.disabled_campaigns
                    and _C.FOTT_NORSE in self.disabled_campaigns
                )
                if _all_fott_disabled:
                    continue

            # "Chiron didn't die" only has gameplay effect in FotT 29/30/31/32.
            # Scenarios 29 and 30 are Norse; 31 and 32 are the Final section.
            # Drop the item when FotT Norse is disabled — the Final section
            # alone (without prior Chiron storyline) doesn't justify keeping it.
            if item == Items.aomItemData.CHIRON_DIDNT_DIE:
                from .locations.Campaigns import aomCampaignData as _C
                if _C.FOTT_NORSE in self.disabled_campaigns:
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

            # Atlantean items — needed when random_major_gods is on OR the New
            # Atlantis campaign (natively Atlantean) is enabled.  Without them the
            # Atlantean NA scenarios (501-505,510-512) have ZERO trainable-unit
            # items, so their per-scenario rules can never be satisfied (the
            # rule requires at least one "Can train <civ unit>") and the
            # scenarios are unbeatable — and a vanilla NA player can't field any
            # Atlantean army.  Skip only when neither condition holds.
            if isinstance(item.type, atlantean_types) \
                    and not random_major_gods_on and _new_atlantis_in_pool is False:
                continue

            # Chinese items — needed when random_major_gods is on OR the Pillars
            # of the Gods campaign (natively Chinese) is enabled (same reasoning
            # as Atlantean/New Atlantis above).
            if isinstance(item.type, chinese_types) \
                    and not random_major_gods_on and _pillars_in_pool is False:
                continue

            # Japanese items — skip if random_major_gods is off (Japanese not in the pool)
            if isinstance(item.type, japanese_types) and not random_major_gods_on:
                continue

            # Aztec items — skip if random_major_gods is off (Aztec not in the pool)
            if isinstance(item.type, aztec_types) and not random_major_gods_on:
                continue

            # Civ-specific items — skip if that civ is excluded (YAML opt-out)
            # OR if random_major_gods rolled zero scenarios for that civ
            # (dead-weight progression items eat scenario slots for nothing).
            # Generic items (starting-armys, heroes, resources) are never skipped.
            if random_major_gods_on and self.effective_excluded_civs:
                # Primary: items with a culture field (unit unlocks, myth unlocks, age unlocks)
                _item_civ = getattr(item.type, "culture", None)
                # Secondary: VillagerCarryCapacity encodes civ in unit_name ("VillagerGreek" etc.)
                # Starting-army items are generic and must never be civ-excluded
                # (e.g. "VillagerGreek"/"VillagerNorse" starting armies spawn for
                # any civ), so the unit_name heuristic skips them.
                if not _item_civ and not isinstance(item.type, Items.StartingArmy):
                    _unit_name = getattr(item.type, "unit_name", "")
                    if   "Greek"    in _unit_name: _item_civ = "Greek"
                    elif "Egyptian" in _unit_name: _item_civ = "Egyptian"
                    elif "Norse"    in _unit_name: _item_civ = "Norse"
                    elif "Atlantean"in _unit_name: _item_civ = "Atlantean"
                    elif "Chinese"  in _unit_name: _item_civ = "Chinese"
                    elif "Japanese" in _unit_name: _item_civ = "Japanese"
                    elif "Aztec"    in _unit_name: _item_civ = "Aztec"
                if _item_civ and _item_civ in self.effective_excluded_civs:
                    continue

            # Starting tech items are added explicitly below (1 copy each)
            if isinstance(item.type, (Items.StartingEconomyTech, Items.StartingMilitaryTech,
                                       Items.StartingDockTech, Items.StartingBuildingsTech)):
                continue

            # "Joins the Campaign" items are catalogued StartingArmyUseful but
            # are treated as progression: each grants a flat +2 points on every
            # scenario (see Rules.count_points), so guaranteeing them reachable
            # raises the guaranteed-points floor that gates high-threshold
            # scenarios under accessibility=full.
            if item in (Items.aomItemData.KASTOR_JOINS,
                        Items.aomItemData.ODYSSEUS_JOINS,
                        Items.aomItemData.REGINLEIF_JOINS):
                _join_item = self.create_item(item.item_name)
                _join_item.classification = ItemClassification.progression
                progression_pool.append(_join_item)
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

        # Myth-unit starting-army throttle.  Too many strong starting myth
        # units gives the player a runaway opening army.  Cap Heroic-age
        # myth starting-armys at 4 and Mythic-age at 2 (Classical and human
        # starting-armys are uncapped — they're not strong enough to matter).
        # Surplus items are dropped from the pool; the existing
        # padding/sizing logic backfills the slots with infinite-filler items.
        # Ages sourced from techtree.xml (which tech enables the proto unit).
        _HEROIC_MYTH_REINF_PROTOS: frozenset = frozenset({
            "BattleBoar", "Behemoth", "Hamadryad", "Roc",
            "BaiHu", "Oni", "Tzitzimitl",
            "PiXiu", "TaoTie", "ObsidianButterfly",
        })
        _MYTHIC_MYTH_REINF_PROTOS: frozenset = frozenset({
            "FireGiant", "Siren", "Lampades", "Phoenix", "Colossus",
            "QingLong", "Umibozu", "Ahuizotl",
        })
        _CLASSICAL_MYTH_REINF_PROTOS: frozenset = frozenset({
            "Cyclops", "Wadjet", "Anubite", "Troll", "Draugr",
            "Automaton", "Caladria", "QiLin", "Jorogumo",
            "Chaneque", "CentzonTotochtin",
        })
        _MAX_HEROIC_MYTH_REINF  = 5
        _MAX_MYTHIC_MYTH_REINF  = 3
        _MAX_CLASSICAL_MYTH_REINF = 6

        def _trim_myth_reinf(age_protos: frozenset, cap: int) -> None:
            """Walk useful_groups and filler_groups; collect (type_, name) for
            starting-army items whose proto is in `age_protos`.  If count > cap,
            randomly drop the surplus from the groups."""
            hits: list[tuple] = []
            for _group in (useful_groups, filler_groups):
                for _type, _names in _group.items():
                    if not issubclass(_type, Items.StartingArmy):
                        continue
                    for _name in _names:
                        _data = Items.NAME_TO_ITEM.get(_name)
                        if _data is None:
                            continue
                        _proto = getattr(_data.type, "unit_name", "") or ""
                        if _proto in age_protos:
                            hits.append((_group, _type, _name))
            if len(hits) <= cap:
                return
            self.random.shuffle(hits)
            for _group, _type, _name in hits[cap:]:
                if _name in _group.get(_type, []):
                    _group[_type].remove(_name)
            logger.info(
                f"AoMR: myth-unit starting-army throttle — kept {cap} of "
                f"{len(hits)} candidates (dropped {len(hits) - cap})."
            )

        _trim_myth_reinf(_HEROIC_MYTH_REINF_PROTOS, _MAX_HEROIC_MYTH_REINF)
        _trim_myth_reinf(_MYTHIC_MYTH_REINF_PROTOS, _MAX_MYTHIC_MYTH_REINF)
        _trim_myth_reinf(_CLASSICAL_MYTH_REINF_PROTOS, _MAX_CLASSICAL_MYTH_REINF)

        # Progressive Wonder — 6 stackable copies, useful classification.
        # Each one the player owns unlocks one wonder-perk tier (see
        # `Items.ProgressiveWonder` docstring and XS APApplyProgressiveWonder).
        # The catalog entry is already added to `useful_groups` once via the
        # main item loop; bump the count to 6 by appending 5 more copies.
        _PROG_WONDER_COPIES = 6
        _pw_type = Items.ProgressiveWonder
        _pw_name = Items.aomItemData.PROGRESSIVE_WONDER.item_name
        _existing = useful_groups.get(_pw_type, []).count(_pw_name)
        _extras = max(0, _PROG_WONDER_COPIES - _existing)
        if _extras > 0:
            useful_groups.setdefault(_pw_type, []).extend([_pw_name] * _extras)

        # Age unlock items — 3 base copies per civ, precollecting starting unlocks
        # Extra copies go to whichever civ is assigned to scenario 32
        extra_final = int(self.options.extra_final_mission_age_unlocks.value)
        scen32_god = self.god_assignments.get(32, 1) if self.god_assignments else 1
        greek_extra = egyptian_extra = norse_extra = atlantean_extra = chinese_extra = japanese_extra = aztec_extra = 0
        if scen32_god in (1, 2, 3, 13):       # Greek
            greek_extra = extra_final
        elif scen32_god in (4, 5, 6):         # Egyptian
            egyptian_extra = extra_final
        elif scen32_god in (10, 11, 12):      # Atlantean
            atlantean_extra = extra_final
        elif scen32_god in (15, 16, 17):      # Chinese
            chinese_extra = extra_final
        elif scen32_god in (18, 19, 20):      # Japanese
            japanese_extra = extra_final
        elif scen32_god in (21, 22, 23):      # Aztec
            aztec_extra = extra_final
        else:                                  # Norse (7, 8, 9, 14)
            norse_extra = extra_final
        # 4 base copies per civ: 1=Classical, 2=Heroic, 3=Mythic, 4=Titan.
        # The 4th copy is the former per-civ Titan Age item, now folded into the
        # progressive track (see Items.AgeUnlock / Items.TitanAgeUnlock).
        age_unlock_config = [
            (Items.aomItemData.GREEK_AGE_UNLOCK,    "Greek",    4 + greek_extra),
            (Items.aomItemData.EGYPTIAN_AGE_UNLOCK, "Egyptian", 4 + egyptian_extra),
            (Items.aomItemData.NORSE_AGE_UNLOCK,    "Norse",    4 + norse_extra),
        ]
        # DLC-civ age unlocks.  Added when random_major_gods is on, OR when that
        # civ's native campaign is enabled — the New Atlantis scenarios are
        # vanilla Atlantean and Pillars of the Gods is vanilla Chinese, so those
        # campaigns need their age unlocks to gate Classical/Heroic/Mythic even
        # with random_major_gods off (without them, age-advancing NA/PoTG
        # scenarios like 502/510 are unbeatable).  Japanese/Aztec have no native
        # campaign, so they ride solely on random_major_gods.
        if random_major_gods_on or _new_atlantis_in_pool:
            age_unlock_config.append(
                (Items.aomItemData.ATLANTEAN_AGE_UNLOCK, "Atlantean", 4 + atlantean_extra)
            )
        if random_major_gods_on or _pillars_in_pool:
            age_unlock_config.append(
                (Items.aomItemData.CHINESE_AGE_UNLOCK, "Chinese", 4 + chinese_extra)
            )
        if random_major_gods_on:
            age_unlock_config.append(
                (Items.aomItemData.JAPANESE_AGE_UNLOCK, "Japanese", 4 + japanese_extra)
            )
            age_unlock_config.append(
                (Items.aomItemData.AZTEC_AGE_UNLOCK, "Aztec", 4 + aztec_extra)
            )
        _new_atlantis_disabled = Campaigns.aomCampaignData.NEW_ATLANTIS in self.disabled_campaigns
        for item_data, culture, count in age_unlock_config:
            # Skip age unlocks for civs excluded from the random major god pool.
            #
            # Atlantean carve-out: only needed when random_major_gods is OFF.
            # With random_major_gods OFF, NA scenarios stay vanilla Atlantean and
            # need Atlantean Age Unlocks to gate Classical/Heroic/Mythic — but in
            # that mode `excluded_civs` is empty anyway, so this branch is a
            # belt-and-suspenders no-op.  With random_major_gods ON, NA scenarios
            # get assigned a god from the active civ pool (never Atlantean if
            # Atlantean is excluded), and their rules use that god's age-unlock
            # names — so Atlantean unlocks are dead weight and must be skipped.
            if culture in self.effective_excluded_civs:
                if not random_major_gods_on and culture == "Atlantean" and not _new_atlantis_disabled:
                    pass  # keep Atlantean for NA when random gods are off
                else:
                    continue
            precollect_n = starting_age_unlocks[culture]
            for i in range(count):
                ap_item = self.create_item(item_data.item_name)
                if i < precollect_n:
                    self.multiworld.push_precollected(ap_item)
                else:
                    progression_pool.append(ap_item)

        # Titan Age unlocks — RETIRED.  The Titan Age is now the 4th copy of the
        # Progressive Age Unlock added above, so no standalone Titan items are
        # placed into the pool anymore (the TitanAgeUnlock items remain defined
        # only for backwards compatibility with pre-overhaul seeds).

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
        optional_objectives_on = self.optional_objectives_enabled
        excluded_scenarios = self.excluded_scenarios
        filler_only_scenarios = self.filler_only_scenarios
        visible_location_count = (
            sum(1 for loc in Locations.aomLocationData
                if loc.type != Locations.aomLocationType.COMPLETION
                and loc.scenario.campaign not in disabled_campaigns
                and loc.scenario.global_number not in excluded_scenarios
                and (relicsanity_on or loc.type != Locations.aomLocationType.RELIC)
                and (optional_objectives_on or loc.type != Locations.aomLocationType.OPTIONAL_OBJECTIVE))
            - 1  # scenario 32 Victory is always locked to the Victory item
        )
        if gem_shop_on:
            # Subtract the remaining Victory locations — Rules.place_gems locks
            # every Victory except scenario 32 (which is already subtracted above).
            # When start_inventory_from_pool requested N Gems, place_gems skips
            # N Victories so they become free-fill — reduce the locked count
            # by N to keep visible_location_count consistent.
            locked_gem_count = sum(
                1 for loc in Locations.aomLocationData
                if loc.type == Locations.aomLocationType.VICTORY
                and loc.scenario.campaign not in disabled_campaigns
                and loc.scenario.global_number not in excluded_scenarios
                and loc.scenario.global_number not in filler_only_scenarios
            ) - 1
            _n_starting_gems = int(getattr(self, "starting_gems_from_pool", 0))
            locked_gem_count = max(0, locked_gem_count - _n_starting_gems)
            visible_location_count -= locked_gem_count
            # 60 shop item slots are free fill targets.
            visible_location_count += len(Locations.ALL_SHOP_ITEM_IDS)
            # Progressive Shop Info hint slots are locked by
            # Rules.place_progressive_shop_info — do NOT add them.
            # Shop E card locations are fully force-placed by
            # `Rules.place_shop_e_items` (4 useful + 44 filler drawn off the
            # top of the useful/filler pools) so they do NOT contribute to
            # visible_location_count and their items don't enter `itempool`.

        if len(progression_pool) > visible_location_count:
            raise ValueError(
                f"Progression pool ({len(progression_pool)} items) exceeds "
                f"visible location count ({visible_location_count})."
            )

        # Progression-legal location count: scenario locations that can host
        # progression items, plus only the shop slots that allow progression
        # (per max_progression_items_in_each_shop; Marsh tier never allows
        # progression). visible_location_count above includes ALL 60 shop
        # slots, which masks the real squeeze when shops forbid progression —
        # so we re-check here with the tighter count and fail early with a
        # clear message instead of dying inside Fill.
        progression_legal_count = (
            sum(1 for loc in Locations.aomLocationData
                if loc.type != Locations.aomLocationType.COMPLETION
                and loc.scenario.campaign not in disabled_campaigns
                and loc.scenario.global_number not in excluded_scenarios
                and (relicsanity_on or loc.type != Locations.aomLocationType.RELIC)
                and (optional_objectives_on or loc.type != Locations.aomLocationType.OPTIONAL_OBJECTIVE))
            - 1  # scenario 32 Victory locked to Victory item
        )
        if gem_shop_on:
            progression_legal_count -= locked_gem_count
            progression_legal_count += sum(
                len(slots) for slots in self.shop_progression_slots.values()
            )

        # Filler-only scenarios (exclude_scenario_30 with scenario keys off):
        # their fillable locations are forced filler-only in Rules.py, so they
        # can never host progression — drop them from the progression budget.
        if filler_only_scenarios:
            progression_legal_count -= sum(
                1 for loc in Locations.aomLocationData
                if loc.type != Locations.aomLocationType.COMPLETION
                and loc.scenario.global_number in filler_only_scenarios
                and loc.scenario.campaign not in disabled_campaigns
                and (relicsanity_on or loc.type != Locations.aomLocationType.RELIC)
                and (optional_objectives_on or loc.type != Locations.aomLocationType.OPTIONAL_OBJECTIVE))

        # Scenario unlock items.
        #   max_keys_on_keyrings == 0 -> nothing pushed (feature disabled).
        #   max_keys_on_keyrings == 1 -> one Scenario Key per active scenario
        #       pushed individually (classic per-scenario-key behavior); the
        #       sphere-1 starter key (if any) is precollected.
        #   max_keys_on_keyrings >= 2 -> one Scenario Key Ring per bundle
        #       pushed instead; the starter ring is precollected. Receiving a
        #       ring unlocks every scenario it carries (handled client-side).
        if self.max_keys_on_keyrings == 1:
            starter_ids = set(self.starter_scenario_key_ids)
            for sid, kid in self.scenario_to_key_id.items():
                key_name = Items.item_id_to_name[kid]
                ap_item = self.create_item(key_name)
                if kid in starter_ids:
                    self.multiworld.push_precollected(ap_item)
                else:
                    progression_pool.append(ap_item)
        elif self.max_keys_on_keyrings >= 2:
            for ring_item_id, ring_name in self.ring_display_names.items():
                ap_item = self.create_item(ring_name)
                if ring_item_id == self.starter_ring_item_id:
                    self.multiworld.push_precollected(ap_item)
                else:
                    progression_pool.append(ap_item)

        if len(progression_pool) > progression_legal_count:
            raise ValueError(
                f"AoMR: progression pool ({len(progression_pool)} items) "
                f"exceeds the number of locations that can legally hold "
                f"progression items ({progression_legal_count}). "
                f"Causes: too few enabled campaigns, per-scenario keys "
                f"(max_keys_on_keyrings=1) inflating the pool, "
                f"max_progression_items_in_each_shop=0 blocking shop slots, "
                f"or random_major_gods adding civ items without enough "
                f"scenario locations to host them. "
                f"Fixes: enable more campaigns, raise max_keys_on_keyrings "
                f"so keys bundle onto rings, "
                f"raise max_progression_items_in_each_shop, enable relicsanity, "
                f"or disable random_major_gods."
            )

        # Full-accessibility fill needs spare reachable slots to seed sphere
        # expansion: a pool that nearly fills every progression-legal slot can
        # pass the count check above yet still deadlock Fill, because it can
        # place the items but not ORDER them so every location stays reachable.
        # This bites hardest with per-scenario keys (max_keys_on_keyrings == 1),
        # which turn every scenario into its own gated progression item. Detect
        # that regime and fail early with the actionable message instead of a
        # late, opaque "FillError: No more spots to place N items". Gated to
        # keys==1 + accessibility==full so configs that fill fine under minimal
        # or with bundled keys (>=2) are never rejected.
        _acc = getattr(self.options.accessibility, "current_key", "")
        if _acc == "full" and self.max_keys_on_keyrings == 1:
            _slack = progression_legal_count - len(progression_pool)
            _need = max(2, progression_legal_count // 10)
            if _slack < _need:
                raise ValueError(
                    f"AoMR: accessibility=full with max_keys_on_keyrings=1 leaves "
                    f"only {_slack} spare progression-legal location(s) "
                    f"(progression pool {len(progression_pool)} of "
                    f"{progression_legal_count}; needs >= {_need}). Fill would "
                    f"deadlock placing per-scenario keys. Fixes: raise "
                    f"max_keys_on_keyrings to bundle keys onto rings, enable "
                    f"relicsanity / optional objectives / more campaigns to add "
                    f"locations, or set accessibility=minimal."
                )

        # Trap cycle — deck-of-cards pool: every enabled trap type is shuffled,
        # popped one at a time, then the deck is reshuffled when empty so no
        # trap type repeats until every other type has been drawn.
        #
        # Adding a NEW TRAP is automatic from this list's perspective:
        #   1. Add a `TRAP_<NAME>` entry in items/Items.py (Trap(trap_type=N)).
        #   2. Add the matching trapType case in triggers/archipelago.xs:
        #        APTrapGetName, the targeting `else if` block (only for
        #        non-default targets), and the execution dispatch.
        #   3. Confirm the GP name exists in Memory Files/god powers/
        #      all_god_power_names.txt.
        # The trap is auto-included here on next generation; no edit to this
        # file needed.  To EXCLUDE a trap (buggy / non-castable in current
        # build), add its item_name to `_DISABLED_TRAPS` below — keeps the
        # item in the catalog (so existing seeds don't break) but removes it
        # from the active trap pool.
        _DISABLED_TRAPS: set = {
            "Trap: Spawn Units",      # not implemented (trap_type 5)
            "Trap: Transform Drops",  # not implemented (trap_type 6)
            "Trap: Spider Lair",      # buggy
            "Trap: Flaming Weapons",  # fails to cast
            "Trap: Bronze",           # can't cast on allies
        }
        _trap_deck_base = [
            it.item_name for it in Items.aomItemData
            if it.type_data == Items.Trap
            and it.item_name not in _DISABLED_TRAPS
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
        # Infinite padding pool: filler items only (never useful — useful
        # classification can't land in filler-only shop slots, which are
        # typically the last slots standing when fill reaches the padding phase).
        # Build from filler_groups (already filtered by campaign/civ/hero-ability
        # exclusions in the main item loop) rather than iterating Items.aomItemData
        # directly — otherwise Chiron/Arkantos/Kastor/etc. filler items would leak
        # into the infinite padding pool even when their campaigns are disabled.
        all_nonreinf_filler_inf = [
            name
            for type_, names in filler_groups.items()
            for name in names
            if not issubclass(type_, Items.StartingArmy)
        ]

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

        # Shop E force-placement reservation.  When Shop E is enabled, reserve
        # 4 useful-or-worse names + 44 filler names off the top of the shuffled
        # pools so `Rules.place_shop_e_items` can place them on the 48 card
        # locations.  These items do NOT enter `itempool`, so the locations are
        # invisible to AP's fill — necessary because adding 48 EXCLUDED slots
        # plus 48 padding filler crowded out progression placement on
        # all-campaigns + relicsanity + key-rings + random-major-gods configs.
        self.shop_e_forced_items: dict[int, str] = {}
        if getattr(self, "shop_e_enabled", False):
            e_useful_ids = set(getattr(self, "shop_e_useful_ids", set()))
            e_hint_ids   = set(getattr(self, "shop_e_hint_ids", set()))
            e_active_ids = list(getattr(self, "shop_e_active_ids", set()))
            # Shop E filler cards roll traps at HALF the YAML trap rate, so even
            # at trap_percentage=100 only ~half of Shop E filler becomes traps.
            shop_e_trap_pct = trap_pct // 2

            def _e_placeholder() -> str:
                # Non-draining filler from the infinite pool — used where a card
                # has no real reward (hint cards) so the meaningful filler pool
                # is not consumed.
                return all_nonreinf_filler_inf[
                    len(self.shop_e_forced_items) % len(all_nonreinf_filler_inf)
                ]

            # Useful slots first.
            for _lid in e_useful_ids:
                if all_useful:
                    self.shop_e_forced_items[_lid] = all_useful.pop()
                elif all_filler:
                    self.shop_e_forced_items[_lid] = all_filler.pop()
                else:
                    self.shop_e_forced_items[_lid] = _e_placeholder()
            # Remaining active slots: hint cards hold no real reward (the client
            # fires a mission hint and never checks the location); filler cards
            # hold filler, or a trap at half the YAML trap rate.
            for _lid in e_active_ids:
                if _lid in e_useful_ids:
                    continue
                if _lid in e_hint_ids:
                    self.shop_e_forced_items[_lid] = _e_placeholder()
                elif shop_e_trap_pct > 0 and self.random.randint(1, 100) <= shop_e_trap_pct:
                    self.shop_e_forced_items[_lid] = _next_trap()
                elif all_filler:
                    self.shop_e_forced_items[_lid] = all_filler.pop()
                else:
                    self.shop_e_forced_items[_lid] = _e_placeholder()

        # Useful-pool capacity guard.  `useful` items cannot land in
        # filler-only shop slots (~half of the non-Marsh shop slots).  Marsh
        # slots and the rest accept useful, so exclude Marsh-tier members
        # from the filler-only count when sizing capacity.  If the useful
        # list is longer than that capacity, Fill's remaining_fill phase
        # errors with "No more spots to place N items".  Trim the surplus
        # from the unique-useful list and let the infinite filler padding
        # loop downstream cover those slots with filler/traps instead.
        # This is the "swap to filler when squeezed" behavior.
        from .locations.Locations import TIER_ITEM_IDS as _TIER_IDS
        _marsh_ids = set(_TIER_IDS.get("A", []))
        _filler_only_locs = getattr(self, "shop_filler_only", set())
        _excluded_locs    = getattr(self, "shop_excluded_ids", set())
        # Marsh slots accept useful (per Rules.py dispatch order: is_marsh
        # check fires before filler_only check), so exclude them from the
        # filler-only reduction.  EXCLUDED slots take precedence over Marsh
        # and reject useful regardless, so they always shrink capacity.
        _strict_filler_only_count = sum(
            1 for lid in _filler_only_locs
            if lid not in _marsh_ids and lid not in _excluded_locs
        )
        _excluded_count = len(_excluded_locs)
        # Safety buffer: AP's fill is not optimal — useful items can fail to
        # place even when the raw count fits, because filler items might grab
        # useful-capable slots before the last few useful items are placed.
        # Reserve ~10% of capacity as slack so the filler pool always has more
        # room than the strict filler-only demand.
        _safety = max(18, (visible_location_count - len(progression_pool)) // 6)
        useful_capacity = max(
            0,
            visible_location_count
            - _strict_filler_only_count
            - _excluded_count
            - len(progression_pool)
            - _safety,
        )
        if len(all_useful) > useful_capacity:
            _trimmed = len(all_useful) - useful_capacity
            logger.warning(
                f"AoMR: useful pool ({len(all_useful)}) exceeds useful-capable "
                f"slot count ({useful_capacity} = {visible_location_count} slots "
                f"- {_strict_filler_only_count} strict-filler-only - "
                f"{_excluded_count} excluded - {len(progression_pool)} "
                f"progression). Dropping {_trimmed} useful items; filler "
                "padding will cover those slots."
            )
            all_useful = all_useful[:useful_capacity]

        # Fill remaining slots in two phases:
        #   Unique phase  (while either pool has items): 1:1 useful:filler alternation.
        #     Useful exhausted mid-phase → draw filler that turn instead.
        #     Filler exhausted mid-phase → cycle infinite non-starting-army filler.
        #   Padding phase (both pools exhausted): pure filler from the infinite
        #     filler pool.  No useful items in padding — useful classification
        #     cannot land in filler-only shop slots, which are typically the
        #     last slots remaining when fill reaches the padding phase.
        # Trap replacement: filler/overflow turns roll against trap_pct; useful turns roll
        # against useful_trap_pct (10% of trap_pct).
        itempool: list[Item] = []
        itempool.extend(progression_pool)
        remaining_slots = visible_location_count - len(itempool)

        u_idx = f_idx = inf_idx = 0
        useful_trap_pct = trap_pct // 10  # 10% of the filler trap rate
        want_useful = True   # unique phase: alternates each slot
        for _ in range(remaining_slots):
            both_exhausted = (u_idx >= len(all_useful)) and (f_idx >= len(all_filler))

            if both_exhausted:
                # Padding phase: pure filler (trap-substituted at trap_pct).
                pad_name = all_nonreinf_filler_inf[inf_idx % len(all_nonreinf_filler_inf)]
                inf_idx += 1
                if trap_pct > 0 and self.random.randint(1, 100) <= trap_pct:
                    itempool.append(self.create_item(_next_trap()))
                else:
                    itempool.append(self.create_item(pad_name))
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

        # Authoritative feasibility clamp — now that the real pool exists, tighten
        # x_scenarios against actual point-item counts (the generate_early clamp
        # overcounts with 99-of-everything). Runs before set_rules/slot_data.
        self._reclamp_x_scenarios(itempool)

        # Pre-collected starting Gems (from start_inventory_from_pool: Gem: N).
        # Pushed here so they aren't part of itempool — place_gems already
        # skipped N Victory locations to free up the equivalent free-fill
        # slots, which itempool padding above filled with filler/useful.
        _n_pre_gems = int(getattr(self, "starting_gems_from_pool", 0))
        if _n_pre_gems > 0:
            for _ in range(_n_pre_gems):
                self.multiworld.push_precollected(
                    self.create_item(Items.aomItemData.GEM.item_name)
                )

        # Split itempool: route a percentage of filler items into
        # self.local_filler_items so pre_fill can place them locally.
        local_pct = self.options.local_filler_frequency.value  # 0-75
        if local_pct > 0 and self.multiworld.players > 1:
            filler_item_names = {item.item_name for item in Items.filler_items}
            filler_indices = [i for i, it in enumerate(itempool)
                              if it.name in filler_item_names]
            n_local = int(len(filler_indices) * (local_pct / 100))
            self.random.shuffle(filler_indices)
            local_indices = set(filler_indices[:n_local])
            for i, it in enumerate(itempool):
                if i in local_indices:
                    self.local_filler_items.append(it)
                else:
                    self.multiworld.itempool.append(it)
        else:
            self.multiworld.itempool += itempool

    def set_rules(self) -> None:
        """Archipelago hook — install access/completion rules and forced
        placements (Victory, Gem, Progressive Shop Info).  Delegates to
        `rules/Rules.py::set_rules`."""
        Rules.set_rules(self)

    def pre_fill(self) -> None:
        """Pre-fill phase.  Two responsibilities:

          1. When `max_keys_on_keyrings >= 2`, plando each scenario's
             individual Scenario Key item onto its `Key for ...` virtual
             location on this player's own slot.  When the player later
             receives a Key Ring item, the client auto-checks those
             locations and the server broadcasts standard `ItemSend`
             events for every Scenario Key the ring delivers — matching
             the gem-shop UX.

          2. Place locally-staged filler items into this player's own
             unfilled locations using `fast_fill` (only when
             `local_filler_frequency > 0` and the multiworld has more
             than one player).
        """
        from BaseClasses import Item as _Item, ItemClassification as _IC

        # --- Key delivery plando (max >= 2) ---
        if int(getattr(self, "max_keys_on_keyrings", 0)) >= 2:
            from .locations.Locations import (
                KEY_DELIVERY_SCENARIO_TO_LOC_ID as _KD_S2L,
                location_id_to_name as _lid2name,
            )
            from .locations.Scenarios import aomScenarioData
            disabled = self.disabled_campaigns
            for scen in aomScenarioData:
                if scen.campaign in disabled:
                    continue
                sid = scen.global_number
                key_iid = self.scenario_to_key_id.get(sid)
                loc_id  = _KD_S2L.get(sid)
                if key_iid is None or loc_id is None:
                    continue
                loc_name = _lid2name.get(loc_id)
                if not loc_name:
                    continue
                try:
                    loc = self.multiworld.get_location(loc_name, self.player)
                except KeyError:
                    continue
                if loc.item is not None:
                    continue  # already filled (shouldn't happen)
                key_name = Items.item_id_to_name.get(key_iid, f"key_{key_iid}")
                # Match the ScenarioKey catalog classification (progression) so
                # the AP client renders the per-scenario delivery as purple,
                # matching the Key Ring that produced it — not teal/filler.
                ap_item = _Item(key_name, _IC.progression, key_iid, self.player)
                loc.place_locked_item(ap_item)

        # --- Local-filler fast_fill (unchanged) ---
        if self.local_filler_items:
            from Fill import fast_fill
            unfilled = self.multiworld.get_unfilled_locations(self.player)
            self.random.shuffle(unfilled)
            self.random.shuffle(self.local_filler_items)
            fast_fill(self.multiworld, self.local_filler_items, unfilled)


    def write_spoiler(self, spoiler_handle) -> None:
        """Emit Key Ring legend into the spoiler log so the player can see
        which scenarios each ring carries.  Only emits when
        `max_keys_on_keyrings >= 2` (rings are actually in use)."""
        if int(getattr(self, "max_keys_on_keyrings", 0)) < 2:
            return
        if not self.ring_item_id_to_scenarios:
            return
        from .locations.Scenarios import aomScenarioData
        sid_to_display = {s.global_number: s.display_name for s in aomScenarioData}

        slot_label = f"Player {self.player}"
        try:
            player_name = self.multiworld.get_player_name(self.player)
            slot_label = f"{slot_label} ({player_name})"
        except Exception:
            pass

        spoiler_handle.write(
            f"\n\nAge of Mythology Retold — Key Ring contents ({slot_label}):\n"
        )
        # Order rings by their index (1, 2, 3, ...).
        ordered = sorted(
            self.ring_item_id_to_scenarios.items(),
            key=lambda kv: Items.RING_ITEM_ID_TO_INDEX.get(kv[0], kv[0]),
        )
        starter_id = self.starter_ring_item_id
        for ring_item_id, scenarios in ordered:
            ring_name = self.ring_display_names.get(
                ring_item_id, Items.item_id_to_name.get(ring_item_id, str(ring_item_id))
            )
            tag = " [starter]" if ring_item_id == starter_id else ""
            spoiler_handle.write(f"  {ring_name}{tag}:\n")
            for sid in scenarios:
                key_name = Items.item_id_to_name.get(
                    self.scenario_to_key_id.get(sid, -1),
                    f"{sid_to_display.get(sid, sid)} Scenario Key",
                )
                spoiler_handle.write(f"    - {key_name}\n")


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
            "version_minor":  3,
            "disabled_campaigns": [c.id for c in self.disabled_campaigns],
            "excluded_scenarios": sorted(getattr(self, "excluded_scenarios", set())),
            "points_scale":   float(getattr(self, "points_scale", 1.0)),
            "world_id":       ((time.time_ns() >> 17) + self.player) & 0x7FFF_FFFF,
            "final_mode":     int(self.options.final_scenarios.value),
            "x_scenarios":    int(self.options.x_scenarios.value),
            "random_major_gods":      bool(self.options.random_major_gods.value),
            "gem_shop":       self.gem_shop_enabled,
            "relicsanity":    self.relicsanity_enabled,
            "optional_objectives": self.optional_objectives_enabled,
            "excluded_civs":  sorted(self.excluded_civs),
        }
        if self.options.random_major_gods:
            data["god_assignments"] = self.god_assignments
        data["minor_god_assignments"] = self.minor_god_assignments
        data["minor_god_full"]        = self.minor_god_full
        data["archaic_forbids"]       = self.archaic_forbids
        data["god_power_assignments"] = self.god_power_assignments
        data["trap_percentage"]       = int(self.options.trap_percentage.value)

        # Scenario unlock items: per-scenario keys (max==1) or Key Rings (max>=2).
        data["max_keys_on_keyrings"]      = int(self.max_keys_on_keyrings)
        data["scenario_to_key_id"]        = dict(self.scenario_to_key_id)
        data["scenario_to_ring_item_id"]  = dict(self.scenario_to_ring_item_id)
        # ring_item_id_to_scenarios uses int keys here -> stringify for JSON
        data["ring_item_id_to_scenarios"] = {
            str(rid): list(sids)
            for rid, sids in self.ring_item_id_to_scenarios.items()
        }
        data["ring_display_names"]        = {
            str(rid): name for rid, name in self.ring_display_names.items()
        }
        data["starter_ring_item_id"]      = self.starter_ring_item_id
        data["starter_scenario_key_ids"]  = list(self.starter_scenario_key_ids)
        # Key delivery locations (max >= 2): client auto-checks these on ring
        # receipt so the server broadcasts standard ItemSend events for each
        # bundled Scenario Key.
        if int(self.max_keys_on_keyrings) >= 2:
            from .locations.Locations import KEY_DELIVERY_SCENARIO_TO_LOC_ID as _KD_S2L
            from .locations.Scenarios import aomScenarioData
            data["scenario_to_key_delivery_loc_id"] = {
                s.global_number: _KD_S2L[s.global_number]
                for s in aomScenarioData
                if s.campaign not in self.disabled_campaigns
                and s.global_number in _KD_S2L
            }
        else:
            data["scenario_to_key_delivery_loc_id"] = {}
        # Per-scenario display label keyed by global_number.  Lets the client
        # render /progress from structured data rather than parsing item-name
        # strings — avoids the "NA " double-prefix / missing-prefix bug.
        from .locations.Scenarios import aomScenarioData
        data["scenario_display_names"]   = {
            s.global_number: s.display_name
            for s in aomScenarioData
            if s.campaign not in self.disabled_campaigns
        }

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

            # Hint slot configs.  Per-tier hint composition:
            #   A — every HINT slot is a mission-hint button (no PSI).
            #         A_HINT_1, A_HINT_2  each hint  random(1..4) missions
            #   B — HINT_1 is PSI; remaining hints                  random(1..3)
            #   C — HINT_1 is PSI; remaining hints                  random(1..2)
            #   D — HINT_1 is PSI; no other hints
            # Mission count is rolled once at gen time so it appears as a
            # static value on the button.
            _MISSION_RANGES = {"A": (1, 4), "B": (1, 3), "C": (1, 2)}
            shop_hint_config: dict[str, dict] = {}
            for tier, _display, _item_obs, hint_obs in Locations.SHOP_TIER_CONFIGS:
                psi_used = False
                for h in range(1, hint_obs + 1):
                    slot_id = f"{tier}_HINT_{h}"
                    if tier in Locations.PROGRESSIVE_INFO_TIERS and not psi_used:
                        # PSI always at HINT_1 for tiers that have one.
                        shop_hint_config[slot_id] = {
                            "type":   "progressive_info",
                            "loc_id": Locations.PROGRESSIVE_INFO_IDS[tier],
                        }
                        psi_used = True
                        continue
                    rng = _MISSION_RANGES.get(tier)
                    if rng is None:
                        # D has no mission hints; shouldn't reach here.
                        continue
                    count = self.random.randint(rng[0], rng[1])
                    shop_hint_config[slot_id] = {
                        "type":           "mission_hints",
                        "missions_count": count,
                        # Preserve the original range field for clients that
                        # still read it; new code should prefer missions_count.
                        "missions_range": (count, count),
                    }
            data["shop_hint_config"] = shop_hint_config

            # Shop E (gem sink) — 4 decks of 12 cards, ordered.  Only present
            # when the budget gate passed in generate_early.  Client uses the
            # deck order to control top-card reveal; card_kind tells it whether
            # purchase should also broadcast a mission hint.
            data["shop_e_enabled"] = bool(getattr(self, "shop_e_enabled", False))
            if self.shop_e_enabled:
                # Serialise deck contents with full per-card item details so
                # the client can render obfuscated previews identical to A-D.
                e_decks_serialised: list[list[dict]] = []
                for deck in self.shop_e_decks:
                    deck_out: list[dict] = []
                    for loc_id in deck:
                        kind = self.shop_e_card_kind.get(loc_id, "filler")
                        entry: dict = {"loc_id": loc_id, "kind": kind}
                        name = Locations.location_id_to_name.get(loc_id)
                        if name:
                            location = self.multiworld.get_location(name, self.player)
                            if location and location.item:
                                entry["item_name"]      = location.item.name
                                entry["player"]         = location.item.player
                                entry["player_name"]    = self.multiworld.get_player_name(location.item.player)
                                entry["classification"] = location.item.classification.name.lower()
                        deck_out.append(entry)
                    e_decks_serialised.append(deck_out)
                data["shop_e_decks"] = e_decks_serialised

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