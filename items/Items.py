# =============================================================================
# Age of Mythology Retold — Item catalog
# =============================================================================
#
# The full set of items the AoMR randomizer can place into a multiworld.  Every
# item is declared as a member of the `aomItemData` IntEnum at the bottom of
# this file.  Each member carries:
#
#   * a numeric `id` (the AP item code, plus `BASE_ID` when serialized)
#   * a display `item_name`
#   * a `type` payload — one of the @dataclass classes defined above
#
# The `type`'s class is what `item_type_to_classification` keys on to decide
# `progression` / `useful` / `filler` / `trap`.
#
# Lifecycle:
#   * `aomWorld.create_items()` (in __init__.py) iterates `aomItemData`, applies
#     option-driven filters (campaign / civ / hero ability), and builds the
#     itempool.
#   * Locked-placement items (Victory, Gem, ProgressiveShopInfo) are placed by
#     `rules/Rules.py` instead of bucketed into the random pool.
#   * On the game side, each item id eventually maps to an XS handler in
#     `triggers/archipelago.xs` (see `APApplyItems` and the helper functions
#     it dispatches to).  GameClient.py emits the per-slot state that those
#     handlers consume.
#
# -----------------------------------------------------------------------------
# CULTURE / CIV TAGGING
# -----------------------------------------------------------------------------
# Civ-specific items must carry a `culture` field on their payload dataclass
# (or a recognizable substring in `unit_name`) so `aomWorld.create_items()`'s
# civ-exclusion logic can drop the item when the player's YAML excludes that
# civilization.  Generic items (resources, traps, hero items shared across
# civs) never need this tag.
#
# -----------------------------------------------------------------------------
# ID RANGES — keep new items inside an unused band to avoid silent IntEnum
# collisions.  Existing bands:
#     1-99      Starting Resources / Passive Income                (filler)
#     1002-1011 Progressive Age Unlocks                             (progression)
#     2000-3199 Hero stat / action / special ability boosts        (mostly useful)
#     3200-3299 Unit unlocks (Can Train Hoplite etc.)              (progression/useful)
#     3300-3499 Kastor specials/stats                               (mixed)
#     3500-3504 Campaign / section unlocks                          (progression)
#     3510      Atlantis Key                                        (progression)
#     4000-4099 StartingArmys                                      (filler/useful)
#     5000-5009 Villager carry / cost                               (filler)
#     5015-5027 Hero "Joins" + myth unit unlocks                    (useful/progression)
#     5100-5103 Starting tech grants                                (useful/filler)
#     9950-9995 Traps                                               (trap)
#     9997-9999 Special: ProgressiveShopInfo, Gem, Victory          (locked placements)
#
# When adding a new item, pick the next free id within the matching band — and
# remember `aomItemData` is an IntEnum, so two members with the same numeric
# value silently alias and the second one disappears.  See the KASTOR comment
# block for the exact bug we hit by reusing 3200-3209.
#
# -----------------------------------------------------------------------------
# EXTENDING
# -----------------------------------------------------------------------------
#   * New civ-specific unit unlock: add a `UnitUnlockUseful(unit_name, culture)`
#     entry, then ensure XS code unforbids the unit when the item is received
#     (see APApplyItems' unit-unlock dispatch in archipelago.xs).
#   * New hero: define stat / special / action items with `hero=` set to the
#     scenario-editor proto unit name; XS already dispatches generically off
#     the hero name.
#   * New trap: add a Trap dataclass entry with the next `trap_type` int and
#     mirror the constant in ap_ai_runtime.xs (`cAPTrap*`).
#   * New campaign: add a `Campaign(campaign=...)` entry whose `vanilla_campaign`
#     points at the new `aomCampaignData` enum member.  Section-unlock semantics
#     (precollect when starting / progression otherwise) are inherited.
#   * New age-tier myth unlock: extend `MythUnitUnlockProgression`/`Useful`/`Filler`
#     with the new culture's unit list.  Match `culture` to civ string used
#     elsewhere ("Greek"/"Egyptian"/"Norse"/"Atlantean") so create_items filters
#     consistently.
# =============================================================================

from dataclasses import dataclass
import enum

from BaseClasses import ItemClassification
from ..locations.Campaigns import aomCampaignData


# -----------------------------------------------------------------------
# Tuning constants
# -----------------------------------------------------------------------

BASE_ID = 0x3B0000  # 3866624 — AP location/item ID offset (added by Archipelago when serializing)
BASE_RESOURCE = 50  # Base unit count for the small starting-resource items (Medium = 2x, Large = 5x)
STARTING_ARMY_AMOUNT = 2  # Default count of units that starting-army items spawn at the spawn marker


# -----------------------------------------------------------------------
# Item type dataclasses
# -----------------------------------------------------------------------
# Each dataclass corresponds to a *kind* of item.  The class itself is the
# routing key in `item_type_to_classification` (below) which tells AP whether
# the item is progression / useful / filler / trap.  The instance carries
# whatever runtime parameters the XS handler will need (resource type, unit
# name, hero name, etc.).
#
# Most dataclass names map directly to a branch in `archipelago.xs`'s item
# dispatcher.  When adding a new dataclass, also:
#   * add a row to `item_type_to_classification`
#   * extend `ItemType` Union if it should be referenced via the alias
#   * implement an XS handler in archipelago.xs's APApplyItems / friends
# -----------------------------------------------------------------------

@dataclass
class Victory:
    """Singleton victory item — placed by Rules.py at FOTT_32's victory location.
    Receiving it triggers AP victory; not in the random pool."""
    pass


@dataclass
class Campaign:
    """Campaign-section unlock.  `vanilla_campaign` points at the enum member
    in `aomCampaignData`, which `aomWorld.generate_early()` uses to decide
    which Campaign item to precollect (the player's starting campaign)."""
    vanilla_campaign: aomCampaignData


@dataclass
class AgeUnlock:
    """Progressive age unlock — Classical / Heroic / Mythic / Titan, in order, by
    stack count (1=Classical, 2=Heroic, 3=Mythic, 4=Titan).  The 4th copy lifts
    the Titan lock (Secrets of the Titans + Titan Gate) for the civ, replacing
    the retired per-civ TitanAgeUnlock item.  `culture` controls which
    civilization is unlocked ("Greek" / "Egyptian" / "Norse" / "Atlantean")."""
    culture: str


@dataclass
class TitanAgeUnlock:
    """RETIRED — no longer placed into the multiworld.  The Titan Age is now the
    4th tier of the Progressive Age Unlock (see `AgeUnlock`).  This class and its
    items are kept ONLY for backwards compatibility: games generated before the
    overhaul still contain these items, and the XS watcher / Rules.py still honor
    a held legacy item so those seeds keep working.  Do not add it to the pool.
    `culture` is the civ string ("Greek"/"Egyptian"/.../"Aztec")."""
    culture: str


@dataclass
class FinalUnlock:
    """Atlantis Key — gates the Final section in atlantis_key mode (FinalScenarios
    option).  Placed in the random pool; in beat_x mode it is omitted entirely."""
    pass


@dataclass
class ScenarioKey:
    """Per-scenario unlock used when `max_keys_on_keyrings` == 1.  Each
    Scenario Key unlocks exactly one scenario, with a stable friendly name
    ("4. A Fine Plan Scenario Key", "NA 2. Atlantis Reborn Scenario Key")
    registered at module load via SCENARIO_TO_KEY_ID.  When
    `max_keys_on_keyrings` >= 2, scenario keys are bundled onto KeyRing
    items instead and ScenarioKey items are not placed into the multiworld
    (the registry still exists so name/id lookups don't break).
    """
    bundle_index: int


@dataclass
class KeyRing:
    """Container item used when `max_keys_on_keyrings` >= 2.  Each KeyRing
    carries 1..max scenario keys (size rolled per ring).  Receiving a
    KeyRing delivers all carried scenario keys to the player at once.
    Bundle contents are seed-deterministic and emitted to the client via
    slot_data (`ring_to_scenarios`)."""
    ring_index: int


@dataclass
class Gem:
    """Currency earned by beating scenarios, spent in the gem shop.  Locked to
    Victory locations by Rules.place_gems() when `gem_shop` option is on."""
    pass


@dataclass
class ProgressiveShopInfo:
    """Unlocks additional label detail in the Gem Shop. One per shop tier.
    Locked by Rules.place_progressive_shop_info() to specific hint slots."""
    pass

@dataclass
class Trap:
    """A trap sent to the AoMR player that activates mid-scenario.  `trap_type`
    must match a `cAPTrap*` const in `ap_ai_runtime.xs` so the running game
    knows which god-power-style negative effect to fire."""
    trap_type: int



@dataclass
class StartingResources:
    """Filler-tier resource grant applied at scenario start.  `type` is a
    `Resource` enum; `amount` is the integer to add to the player's starting
    bank.  Handled by APApplyItems' resource accumulator."""
    type: "Resource"
    amount: int


@dataclass
class StartingResourcesLarge:
    """Same as StartingResources but with a 4x amount.  Splitting into two
    classes lets us tune classification (filler/useful) per tier."""
    type: "Resource"
    amount: int


@dataclass
class PassiveIncome:
    """Per-minute resource trickle (per-20s for FAVOR).  Stacks with multiple
    copies — XS sums the per-minute totals into a single ticker rule."""
    resource: "Resource"
    amount_per_minute: int


@dataclass
class PassiveIncomeLarge:
    """4x variant of PassiveIncome — see comment on PassiveIncome."""
    resource: "Resource"
    amount_per_minute: int


@dataclass
class RelicTrickle:
    """Per-owned-relic resource trickle.  XS multiplies `amount_per_relic` by
    the player's current relic count to produce the effective passive income.
    Stackable: multiple copies sum amounts."""
    resource: "Resource"
    amount_per_relic: float


@dataclass
class RelicEffect:
    """Per-owned-relic stat / cost / build-speed multiplier applied to all
    P1 protounits.  `effect_id` is the dispatch key consumed by
    APRelicEnforce in archipelago.xs (see RELIC_EFFECT_* item entries below
    for the supported keys)."""
    effect_id: str


@dataclass
class StartingArmy:
    """Spawn `amount` copies of a proto unit at the scenario's spawn marker.
    `unit_name` must match an in-game proto unit name (e.g. "Hoplite",
    "Berserk").  Filler-tier; StartingArmyUseful is the useful-tier variant."""
    unit_name: str
    amount: int


# Useful variant of StartingArmy — classified as useful instead of filler.
# Must be defined before the classification dict.
class StartingArmyUseful(StartingArmy):
    """Useful-tier starting-army — same payload as StartingArmy; the class
    identity is the only difference, which routes it to the useful slot in
    `item_type_to_classification`."""
    pass


@dataclass
class UnitStatBonus:
    """Adjust a single stat on a single proto unit.  Useful-tier."""
    unit_name: str
    stat: str  # see MythTRConstants.txt for valid stat names
    amount: int


@dataclass
class UnitUnlockProgression:
    """Progression-tier unit unlock — one per civ.  Required for chunk of
    scenarios to be solvable, so it counts towards reachability."""
    unit_name: str
    culture: str


@dataclass
class UnitUnlockUseful:
    """Useful-tier unit unlock — civ-tagged via `culture` so create_items can
    drop it when the civ is excluded."""
    unit_name: str
    culture: str


@dataclass
class MythUnitUnlockProgression:
    """Progression-tier myth unit unlock for one age tier of one civ.
    `units` lists every proto unit forbidden until this item is received."""
    units: list
    culture: str
    age: str  # "Classical" / "Heroic" / "Mythic"


@dataclass
class MythUnitUnlockUseful:
    """Useful-tier variant of MythUnitUnlockProgression — same payload."""
    units: list
    culture: str
    age: str


@dataclass
class MythUnitUnlockFiller:
    """Filler-tier variant of MythUnitUnlockProgression — same payload."""
    units: list
    culture: str
    age: str


@dataclass
class AtlanteanUnitUnlockProgression:
    """Atlantean unit unlock — only in pool when random_major_gods is enabled."""
    unit_name: str
    culture: str


@dataclass
class AtlanteanUnitUnlockUseful:
    """Atlantean unit unlock — only in pool when random_major_gods is enabled."""
    unit_name: str
    culture: str


@dataclass
class AtlanteanMythUnitUnlock:
    """Atlantean myth unit unlock — only in pool when random_major_gods is enabled."""
    units: list
    culture: str
    age: str


@dataclass
class ChineseUnitUnlockProgression:
    """Chinese unit unlock — only in pool when random_major_gods is enabled."""
    unit_name: str
    culture: str


@dataclass
class ChineseUnitUnlockUseful:
    """Chinese unit unlock — only in pool when random_major_gods is enabled."""
    unit_name: str
    culture: str


@dataclass
class ChineseMythUnitUnlock:
    """Chinese myth unit unlock — only in pool when random_major_gods is enabled."""
    units: list
    culture: str
    age: str


@dataclass
class JapaneseUnitUnlockProgression:
    """Japanese unit unlock — only in pool when random_major_gods is enabled."""
    unit_name: str
    culture: str


@dataclass
class JapaneseUnitUnlockUseful:
    """Japanese unit unlock — only in pool when random_major_gods is enabled."""
    unit_name: str
    culture: str


@dataclass
class JapaneseMythUnitUnlock:
    """Japanese myth unit unlock — only in pool when random_major_gods is enabled."""
    units: list
    culture: str
    age: str


@dataclass
class AztecUnitUnlockProgression:
    """Aztec unit unlock — only in pool when random_major_gods is enabled."""
    unit_name: str
    culture: str


@dataclass
class AztecUnitUnlockUseful:
    """Aztec unit unlock — only in pool when random_major_gods is enabled."""
    unit_name: str
    culture: str


@dataclass
class AztecMythUnitUnlock:
    """Aztec myth unit unlock — only in pool when random_major_gods is enabled."""
    units: list
    culture: str
    age: str


@dataclass
class HeroStatBoost:
    """Useful-tier additive stat boost on a hero.  HeroStatBoostFiller is the
    same shape with filler classification.

    Args:
        hero:        proto unit name (e.g. "Arkantos", "AjaxSPC")
        stat:        stat name (e.g. "Hitpoints", "HandAttack",
                     "RechargeTime", "UnitRegenRate")
        amount:      delta — positive adds, negative subtracts
        attack_type: action name when boosting attack damage
                     (e.g. "HandAttack", "RangedAttack")
    """
    hero: str
    stat: str
    amount: float
    attack_type: str = ""


# Filler variant of HeroStatBoost — small incremental boosts.
# Must be defined before the classification dict.
class HeroStatBoostFiller(HeroStatBoost):
    """Filler-tier variant of HeroStatBoost.  Identical fields — class identity
    is what `item_type_to_classification` keys on."""
    pass


@dataclass
class HeroSpecialEffect:
    """Bind a special on-hit / on-cast effect to a hero ability.  XS reads
    `description` as a space-separated mini-DSL — see archipelago.xs's
    APApplySpecialEffects for the parser.  Removed from pool when the
    `hero_abilities` YAML option is off."""
    hero: str
    description: str


@dataclass
class HeroActionBoost:
    """Tweak a single XSActionEffect parameter on a hero ability.

    Args:
        hero:   proto unit name (e.g. "Arkantos")
        action: action name (e.g. "HandAttack", "Gore", "ChargedRangedAttack")
        effect: `cXSActionEffect*` constant — see MythTRConstants.txt for the
                full list.  Determines what the value tunes (damage, AOE, etc.).
        amount: value the engine applies to the effect.
    """
    hero: str
    action: str
    effect: int
    amount: float


@dataclass
class ArkantosHousing:
    """Negative pop count on a hero so they provide free population capacity.
    Reused for both Arkantos (-10 pop = +10 capacity) and Kastor-as-a-Manor
    (-20 pop = +20 capacity)."""
    pass


@dataclass
class GenericVillagerDiscount:
    """Reduces food cost for all villager types (Greek, Egyptian, Norse,
    Atlantean) by `reduction`.  Generic — never civ-filtered."""
    reduction: int


@dataclass
class ChironSwimmingLessons:
    """One-shot useful: gives ChironSPC the Amphibious movement type so he can
    swim across water as well as walk on land.  Detected by item id; XS reads
    no fields off this instance."""
    pass


@dataclass
class FavorOnHumanKill:
    """Killing any enemy HumanSoldier-class unit grants the player favor.
    XS loops players 2-7 so every enemy slot triggers."""
    pass


@dataclass
class FavorOnMythKill:
    """Killing any enemy MythUnit-class unit grants the player favor.
    XS loops players 2-7 so every enemy slot triggers."""
    pass

@dataclass
class VillagerCarryCapacity:
    """Civ-specific villager carry boost.  Civ encoded via `unit_name`
    (e.g. "VillagerGreek") so create_items's substring check filters it
    against `excluded_civs` correctly.

    Args:
        unit_name: proto unit name (e.g. "VillagerGreek")
        resource:  "food" / "wood" / "gold" — note string, not Resource enum
        amount:    carry capacity increase
    """
    unit_name: str
    resource: str
    amount: int


@dataclass
class StartingEconomyTech:
    """Grants all economy technologies up to and including the scenario's starting age."""
    pass


@dataclass
class StartingMilitaryTech:
    """Grants all military technologies up to and including the scenario's starting age."""
    pass


@dataclass
class StartingDockTech:
    """Grants all dock technologies up to and including the scenario's starting age."""
    pass


@dataclass
class StartingBuildingsTech:
    """Grants all building technologies up to and including the scenario's starting age,
    filtered by the assigned civilization for civ-specific techs."""
    pass


@dataclass
class ProgressiveWonder:
    """Progressive Wonder — stackable Useful item.  Up to 6 copies in the
    pool.  Each copy the player owns unlocks one tier of wonder-related perks:
        1: Wonders can be built once the player reaches the Mythic Age.
        2: Wonders cost 20% less (percent resource reduction).
        3: Wonders build 35% faster (RelicTreasureOfTlacopan-style BuildPoints).
        4: Wonders can be built anywhere (PlaceAnywhere flag, like Tartarian Gate).
        5: Wonders can be built in any age (unforbid Wonder + enable WonderAge*).
        6: Wonders cost 40% less (extra 20% on top of tier 2).
    """
    pass


class Resource(enum.Enum):
    FOOD = 1
    WOOD = 2
    GOLD = 3
    FAVOR = 4


from typing import Union
ItemType = Union[
    Victory,
    Campaign,
    AgeUnlock,
    FinalUnlock,
    StartingResources,
    StartingResourcesLarge,
    PassiveIncome,
    PassiveIncomeLarge,
    RelicTrickle,
    RelicEffect,
    StartingArmy,
    UnitStatBonus,
    UnitUnlockProgression,
    UnitUnlockUseful,
    HeroStatBoost,
    HeroSpecialEffect,
    HeroActionBoost,
    ArkantosHousing,
    VillagerCarryCapacity,
]

item_type_to_classification: dict[type, ItemClassification] = {
    Victory:                ItemClassification.progression,
    Campaign:               ItemClassification.progression,
    AgeUnlock:              ItemClassification.progression,
    TitanAgeUnlock:         ItemClassification.useful,
    FinalUnlock:            ItemClassification.progression,
    ScenarioKey:            ItemClassification.progression,
    KeyRing:                ItemClassification.progression,
    Gem:                    ItemClassification.useful,
    ProgressiveShopInfo:    ItemClassification.useful,
    Trap:                   ItemClassification.trap,
    UnitUnlockProgression:  ItemClassification.progression,
    StartingResources:      ItemClassification.filler,
    PassiveIncome:          ItemClassification.filler,
    StartingArmy:          ItemClassification.filler,
    HeroStatBoostFiller:    ItemClassification.filler,
    StartingResourcesLarge: ItemClassification.filler,
    PassiveIncomeLarge:     ItemClassification.filler,
    RelicTrickle:           ItemClassification.useful,
    RelicEffect:            ItemClassification.useful,
    StartingArmyUseful:    ItemClassification.useful,
    UnitStatBonus:          ItemClassification.useful,
    UnitUnlockUseful:       ItemClassification.useful,
    HeroStatBoost:          ItemClassification.useful,
    HeroSpecialEffect:      ItemClassification.useful,
    HeroActionBoost:        ItemClassification.useful,
    ArkantosHousing:        ItemClassification.useful,
    VillagerCarryCapacity:   ItemClassification.filler,
    GenericVillagerDiscount: ItemClassification.filler,
    ChironSwimmingLessons:   ItemClassification.useful,
    FavorOnHumanKill:        ItemClassification.useful,
    FavorOnMythKill:         ItemClassification.useful,
    MythUnitUnlockProgression:   ItemClassification.progression,
    MythUnitUnlockUseful:        ItemClassification.progression,
    MythUnitUnlockFiller:        ItemClassification.progression,
    AtlanteanUnitUnlockProgression: ItemClassification.progression,
    AtlanteanUnitUnlockUseful:      ItemClassification.useful,
    AtlanteanMythUnitUnlock:        ItemClassification.progression,
    ChineseUnitUnlockProgression:   ItemClassification.progression,
    ChineseUnitUnlockUseful:        ItemClassification.useful,
    ChineseMythUnitUnlock:          ItemClassification.progression,
    JapaneseUnitUnlockProgression:  ItemClassification.progression,
    JapaneseUnitUnlockUseful:       ItemClassification.useful,
    JapaneseMythUnitUnlock:         ItemClassification.progression,
    AztecUnitUnlockProgression:     ItemClassification.progression,
    AztecUnitUnlockUseful:          ItemClassification.useful,
    AztecMythUnitUnlock:            ItemClassification.progression,
    StartingEconomyTech:            ItemClassification.useful,
    StartingMilitaryTech:           ItemClassification.useful,
    StartingDockTech:               ItemClassification.filler,
    StartingBuildingsTech:          ItemClassification.filler,
    ProgressiveWonder:              ItemClassification.useful,
}


# -----------------------------------------------------------------------
# Resource helpers
# -----------------------------------------------------------------------

def _res(multiplier: float, favor: bool = False) -> int:
    """Compute the integer amount for a starting-resource item.

    Args:
        multiplier: scale factor applied to BASE_RESOURCE.  Convention is
                    1.0 for the SMALL filler tier and 4.0 for the LARGE
                    useful tier.
        favor:      Favor's per-item amount is halved relative to the other
                    resources to keep its in-game weight balanced.
    """
    amount = int(BASE_RESOURCE * multiplier)
    if favor:
        amount = amount // 2
    return amount


# UNUSED: passive-income amounts are hard-coded; helper kept (commented) for symmetry with _res.
# def _passive(multiplier: float, favor: bool = False) -> int:
#     """Compute the per-minute trickle amount for a passive-income item.
#
#     Identical pattern to `_res` but anchored at `BASE_RESOURCE // 5` so the
#     trickle scale is independent of the upfront grant scale.  Currently
#     unused at runtime — per-minute amounts on PassiveIncome items are
#     hard-coded for clarity but the helper is retained for symmetry.
#     """
#     base = BASE_RESOURCE // 5
#     amount = int(base * multiplier)
#     if favor:
#         amount = amount // 2
#     return amount


# -----------------------------------------------------------------------
# Item definitions
# -----------------------------------------------------------------------

class aomItemData(enum.IntEnum):
    """The complete catalog of items the AoMR randomizer can place into the
    item pool.  Each member is an IntEnum value (the AP item id) with three
    extra attributes assigned in `__init__`:

      * `id`         — same as the enum value; AP item code (no BASE_ID offset)
      * `item_name`  — display name used by the multiworld
      * `type`       — the dataclass instance carrying runtime parameters
      * `type_data`  — `type(self.type)`; routing key for classification

    IntEnum collision warning: two members with the same numeric id silently
    alias and the second member becomes inaccessible.  See the KASTOR comment
    block below — we hit this bug by reusing the 3200-3209 range that
    CAN_TRAIN_HOPLITE/SPEARMAN/BERSERK already occupied.
    """
    def __new__(cls, id: int, name: str, type: ItemType) -> "aomItemData":
        """IntEnum constructor — sets the numeric value used for lookup and
        deduplication."""
        value = id
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    def __init__(self, id: int, name: str, type: ItemType) -> None:
        """Attach extra metadata fields to the enum member after IntEnum's
        own __init__ is done.  `type_data` lets `aomWorld.create_items()`
        look up classification with a single dict access."""
        self.id = id
        self.item_name = name
        self.type = type
        self.type_data = self.type.__class__

    # -----------------------------------------------------------------------
    # Victory — locked to FOTT_32's Victory location by Rules.py
    # -----------------------------------------------------------------------
    VICTORY = 9999, "Victory", Victory()
    GEM                  = 9998, "Gem",                  Gem()
    PROGRESSIVE_SHOP_INFO = 9997, "Progressive Shop Info", ProgressiveShopInfo()
    TRAP_METEOR          = 9980, "Trap: Meteor",           Trap(trap_type=1)
    TRAP_LIGHTNING_STORM = 9981, "Trap: Lightning Storm",  Trap(trap_type=2)
    TRAP_LOCUST_SWARM    = 9982, "Trap: Locust Swarm",     Trap(trap_type=3)
    TRAP_BOLT            = 9983, "Trap: Bolt",             Trap(trap_type=4)
    TRAP_SPAWN_UNITS     = 9984, "Trap: Spawn Units",      Trap(trap_type=5)
    TRAP_TRANSFORM_DROP  = 9985, "Trap: Transform Drops",  Trap(trap_type=6)
    TRAP_RESTORATION     = 9986, "Trap: Restoration",      Trap(trap_type=7)
    TRAP_CITADEL         = 9987, "Trap: Citadel",          Trap(trap_type=8)
    TRAP_TORNADO         = 9988, "Trap: Tornado",          Trap(trap_type=9)
    TRAP_EARTHQUAKE      = 9989, "Trap: Earthquake",       Trap(trap_type=10)
    TRAP_CURSE           = 9990, "Trap: Curse",            Trap(trap_type=11)
    TRAP_PLAGUE_SERPENTS = 9991, "Trap: Plague of Serpents", Trap(trap_type=12)
    TRAP_IMPLODE         = 9992, "Trap: Implode",          Trap(trap_type=13)
    TRAP_TARTARIAN_GATE  = 9993, "Trap: Tartarian Gate",   Trap(trap_type=14)
    TRAP_CHAOS           = 9994, "Trap: Chaos",            Trap(trap_type=15)
    TRAP_TRAITOR         = 9995, "Trap: Traitor",          Trap(trap_type=16)
    TRAP_CARNIVORA       = 9950, "Trap: Carnivora",        Trap(trap_type=17)
    TRAP_SPIDER_LAIR     = 9951, "Trap: Spider Lair",      Trap(trap_type=18)
    TRAP_DECONSTRUCTION  = 9952, "Trap: Deconstruction",   Trap(trap_type=19)
    TRAP_FIMBULWINTER    = 9953, "Trap: Fimbulwinter",     Trap(trap_type=20)
    TRAP_FLAMING_WEAPONS = 9954, "Trap: Flaming Weapons",  Trap(trap_type=21)
    TRAP_ANCESTORS       = 9955, "Trap: Ancestors",        Trap(trap_type=22)
    TRAP_PESTILENCE      = 9956, "Trap: Pestilence",       Trap(trap_type=23)
    TRAP_BRONZE          = 9957, "Trap: Bronze",           Trap(trap_type=24)
    TRAP_NIDHOGG         = 9958, "Trap: Nidhogg",          Trap(trap_type=25)
    TRAP_SHOCKWAVE       = 9959, "Trap: Shockwave",         Trap(trap_type=26)
    TRAP_TEMPEST         = 9960, "Trap: Tempest",           Trap(trap_type=27)
    TRAP_INFERNO         = 9961, "Trap: Inferno",           Trap(trap_type=28)
    TRAP_CORRUPTED_GROUND= 9962, "Trap: Corrupted Ground",  Trap(trap_type=29)
    TRAP_YINGLONGS_WRATH = 9963, "Trap: Yinglong's Wrath",  Trap(trap_type=30)
    TRAP_KUSANAGI        = 9964, "Trap: Kusanagi",          Trap(trap_type=31)
    TRAP_SWAMPLAND       = 9965, "Trap: Swampland",         Trap(trap_type=32)
    TRAP_THUNDER_BURST   = 9966, "Trap: Thunder Burst",     Trap(trap_type=33)
    TRAP_SMITING_GUST    = 9967, "Trap: Smiting Gust",      Trap(trap_type=34)
    TRAP_DIVINE_SLASH    = 9968, "Trap: Divine Slash",      Trap(trap_type=35)
    TRAP_DRAGON_TYPHOON  = 9969, "Trap: Dragon Typhoon",    Trap(trap_type=36)
    TRAP_INFESTATION     = 9970, "Trap: Infestation",       Trap(trap_type=37)
    TRAP_LULLABY         = 9971, "Trap: Lullaby",           Trap(trap_type=38)
    TRAP_PURGE           = 9972, "Trap: Purge",             Trap(trap_type=39)
    TRAP_EARTH_MONSTER   = 9973, "Trap: Earth Monster",     Trap(trap_type=40)
    TRAP_STARFALL        = 9974, "Trap: Starfall",          Trap(trap_type=41)
    TRAP_CHICKEN_STORM   = 9975, "Trap: Chicken Storm",     Trap(trap_type=42)
    TRAP_UNDERMINE       = 9976, "Trap: Undermine",         Trap(trap_type=43)
    TRAP_DROUGHT_LAND    = 9977, "Trap: Drought Land",      Trap(trap_type=44)
    TRAP_GREAT_FLOOD     = 9978, "Trap: Great Flood",       Trap(trap_type=45)
    TRAP_VOLCANO         = 9979, "Trap: Volcano",           Trap(trap_type=46)
    TRAP_VANISH          = 9940, "Trap: Vanish",            Trap(trap_type=47)


    # -----------------------------------------------------------------------
    # Campaign / Section unlocks (progression)
    # One item per campaign section; receiving it allows the player to enter
    # that section's scenarios. ATLANTIS_KEY unlocks the final two scenarios.
    # -----------------------------------------------------------------------
    GREEK_SCENARIOS    = 3500, "Unlock FotT Greek Campaign",    Campaign(aomCampaignData.FOTT_GREEK)
    EGYPTIAN_SCENARIOS = 3501, "Unlock FotT Egyptian Campaign", Campaign(aomCampaignData.FOTT_EGYPTIAN)
    NORSE_SCENARIOS    = 3502, "Unlock FotT Norse Campaign",    Campaign(aomCampaignData.FOTT_NORSE)
    UNLOCK_NEW_ATLANTIS = 3503, "Unlock New Atlantis Campaign",    Campaign(aomCampaignData.NEW_ATLANTIS)
    UNLOCK_GOLDEN_GIFT  = 3504, "Unlock The Golden Gift Campaign", Campaign(aomCampaignData.GOLDEN_GIFT)
    UNLOCK_PILLARS_OF_THE_GODS = 3505, "Unlock the Pillars of the Gods Campaign", Campaign(aomCampaignData.PILLARS_OF_THE_GODS)
    ATLANTIS_KEY       = 3510, "Atlantis Key",       FinalUnlock()

    # -----------------------------------------------------------------------
    # Age Unlocks (progression)
    # Three items per civilization unlock Classical -> Heroic -> Mythic Age.
    # Items within each civ are visually identical to the player; the Unicode
    # zero-width characters keep names unique in the AP item tables.
    # -----------------------------------------------------------------------
    GREEK_AGE_UNLOCK      = 1002, "Progressive Greek Age Unlock",      AgeUnlock("Greek")

    EGYPTIAN_AGE_UNLOCK   = 1005, "Progressive Egyptian Age Unlock",      AgeUnlock("Egyptian")

    NORSE_AGE_UNLOCK      = 1008, "Progressive Norse Age Unlock",      AgeUnlock("Norse")
    ATLANTEAN_AGE_UNLOCK  = 1011, "Progressive Atlantean Age Unlock", AgeUnlock("Atlantean")  # only in pool when random_major_gods is on
    CHINESE_AGE_UNLOCK    = 1014, "Progressive Chinese Age Unlock",   AgeUnlock("Chinese")  # only in pool when random_major_gods is on
    JAPANESE_AGE_UNLOCK   = 1017, "Progressive Japanese Age Unlock",  AgeUnlock("Japanese")  # only in pool when random_major_gods is on
    AZTEC_AGE_UNLOCK      = 1020, "Progressive Aztec Age Unlock",     AgeUnlock("Aztec")     # only in pool when random_major_gods is on

    # -----------------------------------------------------------------------
    # Titan Age unlocks (IDs 1100-1106) — RETIRED, NO LONGER PLACED.
    # The Titan Age is now the 4th tier of the Progressive Age Unlock above
    # (4 copies = Titan).  These items remain defined so their IDs/names still
    # resolve for backwards compatibility: pre-overhaul seeds still carry them,
    # and APEnforceTitanLock / Rules._titan_buildable honor a held legacy item.
    # New generations must NOT add these to the pool.
    # -----------------------------------------------------------------------
    GREEK_TITAN_UNLOCK     = 1100, "Unlock Greek Titan Age",     TitanAgeUnlock("Greek")
    EGYPTIAN_TITAN_UNLOCK  = 1101, "Unlock Egyptian Titan Age",  TitanAgeUnlock("Egyptian")
    NORSE_TITAN_UNLOCK     = 1102, "Unlock Norse Titan Age",     TitanAgeUnlock("Norse")
    ATLANTEAN_TITAN_UNLOCK = 1103, "Unlock Atlantean Titan Age", TitanAgeUnlock("Atlantean")
    CHINESE_TITAN_UNLOCK   = 1104, "Unlock Chinese Titan Age",   TitanAgeUnlock("Chinese")
    JAPANESE_TITAN_UNLOCK  = 1105, "Unlock Japanese Titan Age",  TitanAgeUnlock("Japanese")
    AZTEC_TITAN_UNLOCK     = 1106, "Unlock Aztec Titan Age",     TitanAgeUnlock("Aztec")

    # -----------------------------------------------------------------------
    # Unit Unlocks
    # Unlockable units are forbidden at scenario start and unforbidden when
    # the corresponding item is received (see APActivateScenario in xs).
    # Progression: one per civ, required for scenario access logic.
    # Useful: culture-appropriate units that improve combat options.
    # -----------------------------------------------------------------------

    # Progression — one per civilization
    CAN_TRAIN_HOPLITE         = 3200, "Can train Hoplite",         UnitUnlockProgression("Hoplite", "Greek")
    CAN_TRAIN_SPEARMAN        = 3201, "Can train Spearman",        UnitUnlockProgression("Spearman", "Egyptian")
    CAN_TRAIN_BERSERK         = 3202, "Can train Berserk",         UnitUnlockProgression("Berserk", "Norse")

    # Useful — Greek
    CAN_TRAIN_HYPASPIST       = 3210, "Can train Hypaspist",       UnitUnlockUseful("Hypaspist", "Greek")
    CAN_TRAIN_PELTAST         = 3212, "Can train Peltast",         UnitUnlockUseful("Peltast", "Greek")
    CAN_TRAIN_HIPPEUS         = 3213, "Can train Hippeus",         UnitUnlockUseful("Hippeus", "Greek")
    CAN_TRAIN_TOXOTES         = 3214, "Can train Toxotes",         UnitUnlockUseful("Toxotes", "Greek")
    CAN_TRAIN_PRODROMOS       = 3215, "Can train Prodromos",       UnitUnlockUseful("Prodromos", "Greek")

    # Useful — Egyptian
    CAN_TRAIN_AXEMAN          = 3220, "Can train Axeman",          UnitUnlockUseful("Axeman", "Egyptian")
    CAN_TRAIN_SLINGER         = 3221, "Can train Slinger",         UnitUnlockUseful("Slinger", "Egyptian")
    CAN_TRAIN_CHARIOT_ARCHER  = 3222, "Can train Chariot Archer",  UnitUnlockUseful("ChariotArcher", "Egyptian")
    CAN_TRAIN_CAMEL_RIDER     = 3223, "Can train Camel Rider",     UnitUnlockUseful("CamelRider", "Egyptian")
    CAN_TRAIN_WAR_ELEPHANT    = 3224, "Can train War Elephant",    UnitUnlockUseful("WarElephant", "Egyptian")

    # Useful — Norse
    CAN_TRAIN_THROWING_AXEMAN = 3230, "Can train Throwing Axeman", UnitUnlockUseful("ThrowingAxeman", "Norse")
    CAN_TRAIN_HIRDMAN         = 3234, "Can train Hirdman",         UnitUnlockUseful("Hirdman", "Norse")
    CAN_TRAIN_HUSKARL         = 3231, "Can train Huskarl",         UnitUnlockUseful("Huskarl", "Norse")
    CAN_TRAIN_RAIDING_CAVALRY = 3232, "Can train Raiding Cavalry", UnitUnlockUseful("RaidingCavalry", "Norse")
    CAN_TRAIN_JARL            = 3233, "Can train Jarl",            UnitUnlockUseful("Jarl", "Norse")

    # Atlantean unit unlocks — only added to pool when random_major_gods is enabled
    CAN_TRAIN_MURMILLO        = 3240, "Can train Murmillo",        AtlanteanUnitUnlockProgression("Murmillo", "Atlantean")
    CAN_TRAIN_KATAPELTES      = 3241, "Can train Katapeltes",      AtlanteanUnitUnlockUseful("Katapeltes", "Atlantean")
    CAN_TRAIN_TURMA           = 3242, "Can train Turma",           AtlanteanUnitUnlockUseful("Turma", "Atlantean")
    CAN_TRAIN_CHEIROBALLISTA  = 3243, "Can train Cheiroballista",  AtlanteanUnitUnlockUseful("Cheiroballista", "Atlantean")
    CAN_TRAIN_CONTARIUS       = 3244, "Can train Contarius",       AtlanteanUnitUnlockUseful("Contarius", "Atlantean")
    CAN_TRAIN_ARCUS           = 3245, "Can train Arcus",           AtlanteanUnitUnlockUseful("Arcus", "Atlantean")
    CAN_TRAIN_FANATIC         = 3246, "Can train Fanatic",         AtlanteanUnitUnlockUseful("Fanatic", "Atlantean")
    CAN_TRAIN_DESTROYER       = 3247, "Can train Destroyer",       AtlanteanUnitUnlockUseful("Destroyer", "Atlantean")

    # Chinese unit unlocks — only added to pool when random_major_gods is enabled
    CAN_TRAIN_DAO_SWORDSMAN   = 3250, "Can train Dao Swordsman",   ChineseUnitUnlockProgression("DaoSwordsman", "Chinese")
    CAN_TRAIN_GE_HALBERDIER   = 3251, "Can train Ge Halberdier",   ChineseUnitUnlockUseful("GeHalberdier", "Chinese")
    CAN_TRAIN_WUZU_JAVELINEER = 3252, "Can train Wuzu Javelineer", ChineseUnitUnlockUseful("WuzuJavelineer", "Chinese")
    CAN_TRAIN_FIRE_ARCHER     = 3253, "Can train Fire Archer",     ChineseUnitUnlockUseful("FireArcher", "Chinese")
    CAN_TRAIN_CHU_KO_NU       = 3254, "Can train Chu Ko Nu",       ChineseUnitUnlockUseful("ChuKoNu", "Chinese")
    CAN_TRAIN_WHITE_HORSE_CAVALRY = 3255, "Can train White Horse Cavalry", ChineseUnitUnlockUseful("WhiteHorseCavalry", "Chinese")
    CAN_TRAIN_TIGER_CAVALRY   = 3256, "Can train Tiger Cavalry",   ChineseUnitUnlockUseful("TigerCavalry", "Chinese")

    # Japanese unit unlocks — only added to pool when random_major_gods is enabled
    CAN_TRAIN_YARI_SPEARMAN   = 3260, "Can train Yari Spearman",   JapaneseUnitUnlockProgression("YariSpearman", "Japanese")
    CAN_TRAIN_YUMI_ARCHER     = 3261, "Can train Yumi Archer",     JapaneseUnitUnlockUseful("YumiArcher", "Japanese")
    CAN_TRAIN_SAMURAI         = 3262, "Can train Samurai",         JapaneseUnitUnlockUseful("Samurai", "Japanese")
    CAN_TRAIN_NAGINATA_RIDER  = 3263, "Can train Naginata Rider",  JapaneseUnitUnlockUseful("NaginataRider", "Japanese")
    CAN_TRAIN_YUMI_HORSE_ARCHER = 3264, "Can train Yumi Horse Archer", JapaneseUnitUnlockUseful("YumiHorseArcher", "Japanese")
    CAN_TRAIN_SHINOBI         = 3265, "Can train Shinobi",         JapaneseUnitUnlockUseful("Shinobi", "Japanese")

    # Aztec unit unlocks — only added to pool when random_major_gods is enabled
    CAN_TRAIN_TLAMANIH_SPEARMAN = 3270, "Can train Tlamanih Spearman", AztecUnitUnlockProgression("TlamanihSpearman", "Aztec")
    CAN_TRAIN_QUIMICHIN_SPY    = 3271, "Can train Quimichin Spy",     AztecUnitUnlockUseful("QuimichinSpy", "Aztec")
    CAN_TRAIN_TEQUIHUA_ARCHER  = 3272, "Can train Tequihua Archer",   AztecUnitUnlockUseful("TequihuaArcher", "Aztec")
    CAN_TRAIN_COYOTE_WARRIOR   = 3273, "Can train Coyote Warrior",    AztecUnitUnlockUseful("CoyoteWarrior", "Aztec")
    CAN_TRAIN_OCELOTL_WARRIOR  = 3274, "Can train Ocelotl Warrior",   AztecUnitUnlockUseful("OcelotlWarrior", "Aztec")
    CAN_TRAIN_EAGLE_WARRIOR    = 3275, "Can train Eagle Warrior",     AztecUnitUnlockUseful("EagleWarrior", "Aztec")
    CAN_TRAIN_OTONTIN          = 3276, "Can train Otontin",           AztecUnitUnlockUseful("Otontin", "Aztec")
    CAN_TRAIN_SHORN_ONE        = 3277, "Can train Shorn One",         AztecUnitUnlockUseful("ShornOne", "Aztec")
    CAN_TRAIN_JAGUAR_RIDER     = 3278, "Can train Jaguar Rider",      AztecUnitUnlockUseful("JaguarRider", "Aztec")

    # -----------------------------------------------------------------------
    # Starting Resources
    # Filler: small/medium grants (BASE_RESOURCE x1 / x2).
    # Large grants (BASE_RESOURCE x5) use StartingResourcesLarge.
    # Favor is set explicitly (small +5, medium +10, large +20).
    # -----------------------------------------------------------------------
    STARTING_WOOD_SMALL   = 1,  f"+{_res(1)} Starting Wood",  StartingResources(Resource.WOOD,  _res(1))
    STARTING_FOOD_SMALL   = 2,  f"+{_res(1)} Starting Food",  StartingResources(Resource.FOOD,  _res(1))
    STARTING_GOLD_SMALL   = 3,  f"+{_res(1)} Starting Gold",  StartingResources(Resource.GOLD,  _res(1))
    STARTING_FAVOR_SMALL  = 4,  "+5 Starting Favor",          StartingResources(Resource.FAVOR, 5)

    STARTING_WOOD_MEDIUM  = 5,  f"+{_res(2)} Starting Wood",  StartingResources(Resource.WOOD,  _res(2))
    STARTING_FOOD_MEDIUM  = 6,  f"+{_res(2)} Starting Food",  StartingResources(Resource.FOOD,  _res(2))
    STARTING_GOLD_MEDIUM  = 7,  f"+{_res(2)} Starting Gold",  StartingResources(Resource.GOLD,  _res(2))
    STARTING_FAVOR_MEDIUM = 8,  "+10 Starting Favor",         StartingResources(Resource.FAVOR, 10)

    STARTING_WOOD_LARGE   = 9,  f"+{_res(5)} Starting Wood",  StartingResourcesLarge(Resource.WOOD,  _res(5))
    STARTING_FOOD_LARGE   = 10, f"+{_res(5)} Starting Food",  StartingResourcesLarge(Resource.FOOD,  _res(5))
    STARTING_GOLD_LARGE   = 11, f"+{_res(5)} Starting Gold",  StartingResourcesLarge(Resource.GOLD,  _res(5))
    STARTING_FAVOR_LARGE  = 12, "+20 Starting Favor",         StartingResourcesLarge(Resource.FAVOR, 20)

    # -----------------------------------------------------------------------
    # Passive Income
    # Filler: small rate (BASE//5 x1). Granted every 60s (favor: every 20s).
    # Useful: large rate (BASE//5 x4).
    # -----------------------------------------------------------------------
    PASSIVE_WOOD_SMALL    = 13, "+0.5 Wood trickle rate",  PassiveIncome(Resource.WOOD,  1)
    PASSIVE_FOOD_SMALL    = 14, "+0.5 Food trickle rate",  PassiveIncome(Resource.FOOD,  1)
    PASSIVE_GOLD_SMALL    = 15, "+0.5 Gold trickle rate",  PassiveIncome(Resource.GOLD,  1)
    PASSIVE_FAVOR_SMALL   = 16, "+0.1 Favor trickle rate", PassiveIncome(Resource.FAVOR, 0)

    PASSIVE_WOOD_LARGE    = 21, "+2 Wood trickle rate",    PassiveIncomeLarge(Resource.WOOD,  3)
    PASSIVE_FOOD_LARGE    = 22, "+2 Food trickle rate",    PassiveIncomeLarge(Resource.FOOD,  3)
    PASSIVE_GOLD_LARGE    = 23, "+2 Gold trickle rate",    PassiveIncomeLarge(Resource.GOLD,  3)
    PASSIVE_FAVOR_LARGE   = 24, "+0.2 Favor trickle rate", PassiveIncomeLarge(Resource.FAVOR, 0)

    # -----------------------------------------------------------------------
    # Relic Trickle — Useful
    # Each garrisoned relic in any player 1 temple grants the listed trickle.
    # -----------------------------------------------------------------------
    RELIC_TRICKLE_FOOD    = 25, "Each Owned Relic Grants 1 Food Trickle",   RelicTrickle(Resource.FOOD, 1.0)
    RELIC_TRICKLE_WOOD    = 26, "Each Owned Relic Grants 1 Wood Trickle",   RelicTrickle(Resource.WOOD, 1.0)
    RELIC_TRICKLE_GOLD    = 27, "Each Owned Relic Grants 1 Gold Trickle",   RelicTrickle(Resource.GOLD, 1.0)
    RELIC_TRICKLE_FAVOR   = 28, "Each Owned Relic Grants 0.1 Favor Trickle",  RelicTrickle(Resource.FAVOR, 0.1)

    # -----------------------------------------------------------------------
    # Relic Effects — Useful
    # Per-owned-relic stat / cost / build-speed modifiers that apply to all
    # player 1 protounits. Implemented in APRelicEnforce by replaying the
    # underlying tr* call once per relic delta (or once with delta-multiplied
    # value for additive effects).
    # -----------------------------------------------------------------------
    RELIC_EFFECT_LOS          = 29, "Each Owned Relic Grants Buildings +4 and Units +2 Line of Sight", RelicEffect("los")
    RELIC_EFFECT_REGEN        = 30, "Each Owned Relic Grants Everything +0.5 Regeneration",        RelicEffect("regen")
    RELIC_EFFECT_SPEED        = 31, "Each Owned Relic Grants All Units +5% Speed",                  RelicEffect("speed")
    RELIC_EFFECT_HP           = 32, "Each Owned Relic Grants Everything +3% Max Hitpoints",         RelicEffect("hp")
    RELIC_EFFECT_POP          = 33, "Each Owned Relic Increases House and Manor Population Capacity by 1", RelicEffect("pop")
    RELIC_EFFECT_GOLD_COST    = 34, "Each Owned Relic Reduces the Gold Cost of Everything 4%",      RelicEffect("gold_cost")
    RELIC_EFFECT_WOOD_COST    = 35, "Each Owned Relic Reduces the Wood Cost of Everything 4%",      RelicEffect("wood_cost")
    RELIC_EFFECT_FAVOR_COST   = 36, "Each Owned Relic Reduces the Favor Cost of Units and Buildings 4%", RelicEffect("favor_cost")
    RELIC_EFFECT_FOOD_COST    = 37, "Each Owned Relic Reduces the Food Cost of Everything 4%",      RelicEffect("food_cost")
    RELIC_EFFECT_BUILD_SPEED  = 38, "Each Owned Relic Makes Buildings Build 8% faster",            RelicEffect("build_speed")

    # -----------------------------------------------------------------------
    # StartingArmys — Filler
    # Each item spawns STARTING_ARMY_AMOUNT (2) units near the spawn point.
    # -----------------------------------------------------------------------
    STARTING_ARMY_ANUBITES        = 4000, "1 Anubite",                                 StartingArmy("Anubite",          1)
    STARTING_ARMY_HOPLITE         = 4001, f"{STARTING_ARMY_AMOUNT} Hoplites",          StartingArmy("Hoplite",          STARTING_ARMY_AMOUNT)
    STARTING_ARMY_DWARF           = 4002, f"{STARTING_ARMY_AMOUNT} Dwarves",           StartingArmy("Dwarf",            STARTING_ARMY_AMOUNT)
    STARTING_ARMY_MERCENARY       = 4003, f"{STARTING_ARMY_AMOUNT} Mercenaries",       StartingArmy("Mercenary",        STARTING_ARMY_AMOUNT)
    STARTING_ARMY_MERCENARY_CAV   = 4004, f"{STARTING_ARMY_AMOUNT} Mercenary Cavalry", StartingArmy("MercenaryCavalry", STARTING_ARMY_AMOUNT)
    STARTING_ARMY_AUTOMATON       = 4006, f"{STARTING_ARMY_AMOUNT} Automatons",        StartingArmy("Automaton",        STARTING_ARMY_AMOUNT)
    STARTING_ARMY_WADJET          = 4007, "1 Wadjet",                                  StartingArmy("Wadjet",           1)
    STARTING_ARMY_ULFSARK         = 4008, f"{STARTING_ARMY_AMOUNT} Berserks",          StartingArmy("Berserk",          STARTING_ARMY_AMOUNT)
    STARTING_ARMY_SLINGER         = 4009, f"{STARTING_ARMY_AMOUNT} Slingers",          StartingArmy("Slinger",          STARTING_ARMY_AMOUNT)
    STARTING_ARMY_TURMA           = 4010, f"{STARTING_ARMY_AMOUNT} Turmas",            StartingArmy("Turma",            STARTING_ARMY_AMOUNT)
    STARTING_ARMY_KATASKOPOS      = 4011, f"{STARTING_ARMY_AMOUNT} Kataskopos",        StartingArmy("Kataskopos",       STARTING_ARMY_AMOUNT)
    STARTING_ARMY_VILLAGER        = 4013, f"{STARTING_ARMY_AMOUNT} Greek Villagers",   StartingArmy("VillagerGreek",    STARTING_ARMY_AMOUNT)
    STARTING_ARMY_BATTLE_BOAR     = 4015, "1 Battle Boar",                             StartingArmy("BattleBoar",       1)
    STARTING_ARMY_RAIDING_CAVALRY = 4020, f"{STARTING_ARMY_AMOUNT} Raiding Cavalry",   StartingArmy("RaidingCavalry",   STARTING_ARMY_AMOUNT)
    STARTING_ARMY_ORACLE          = 4021, f"{STARTING_ARMY_AMOUNT} Oracles",           StartingArmy("Oracle",           STARTING_ARMY_AMOUNT)
    STARTING_ARMY_CYCLOPS         = 4022, "1 Cyclops",                                 StartingArmy("Cyclops",          1)
    STARTING_ARMY_TROLL           = 4023, "1 Troll",                                   StartingArmy("Troll",            1)
    STARTING_ARMY_BEHEMOTH        = 4024, "1 Behemoth",                                StartingArmy("Behemoth",         1)
    STARTING_ARMY_HAMADRYAD       = 4037, "1 Hamadryad",                               StartingArmy("Hamadryad",        1)
    STARTING_ARMY_DRAUGR          = 4038, "1 Draugr",                                  StartingArmy("Draugr",           1)

    # -----------------------------------------------------------------------
    # StartingArmys — Useful
    # Strong units or workers that provide meaningful advantage.
    # -----------------------------------------------------------------------
    STARTING_ARMY_FIRE_GIANT      = 4012, "1 Fire Giant",                              StartingArmyUseful("FireGiant",         1)
    STARTING_ARMY_CITIZEN         = 4014, f"{STARTING_ARMY_AMOUNT} Citizens",          StartingArmy("VillagerAtlantean", STARTING_ARMY_AMOUNT)
    STARTING_ARMY_ROC             = 4017, "1 Roc",                                     StartingArmyUseful("Roc",               1)
    STARTING_ARMY_PRIEST          = 4018, f"{STARTING_ARMY_AMOUNT} Priests",           StartingArmy("Priest",            STARTING_ARMY_AMOUNT)
    STARTING_ARMY_CALADRIA        = 4019, "1 Caladria",                                StartingArmy("Caladria",          1)
    STARTING_ARMY_SIREN           = 4039, "1 Siren",                                   StartingArmyUseful("Siren",             1)
    STARTING_ARMY_LAMPADES        = 4025, "1 Lampades",                                StartingArmyUseful("Lampades",          1)
    STARTING_ARMY_PHOENIX         = 4026, "1 Phoenix",                                 StartingArmyUseful("Phoenix",           1)
    STARTING_ARMY_COLOSSUS        = 4027, "1 Colossus",                                StartingArmyUseful("Colossus",          1)

    # Special: spawns exactly 1 Reginleif (not STARTING_ARMY_AMOUNT)
    REGINLEIF_JOINS               = 4028, "Reginleif Joins the Campaign",              StartingArmyUseful("Reginleif", 1)
    ODYSSEUS_JOINS                = 5015, "Odysseus Joins the Campaign",               StartingArmyUseful("OdysseusSPC", 1)
    KASTOR_JOINS                  = 4035, "Kastor Joins the Campaign",                 StartingArmyUseful("Kastor", 1)
    AJAX_AMANRA_DREAMS            = 4036, "Ajax and Amanra join you for A Place in My Dreams", StartingArmyUseful("AjaxSPC", 1)
    # Chiron-survives item: spawns ChironSPC at scenario start in FotT 29/30/31/32.
    CHIRON_DIDNT_DIE              = 4053, "Chiron didn't die",                         StartingArmyUseful("ChironSPC", 1)

    # Myth unit tier unlocks — forbidden at start, unlocked by item
    GREEK_CLASSICAL_MYTH_UNITS               = 5016, "Can train Greek Classical Myth Units", MythUnitUnlockProgression(['Centaur', 'Minotaur', 'Cyclops', 'LykaonVillager'], "Greek", "Classical")
    GREEK_HEROIC_MYTH_UNITS                  = 5017, "Can train Greek Heroic Myth Units", MythUnitUnlockProgression(['Hydra', 'Manticore', 'NemeanLion', 'Hamadryad', 'Scylla'], "Greek", "Heroic")
    GREEK_MYTHIC_MYTH_UNITS                  = 5018, "Can train Greek Mythic Myth Units", MythUnitUnlockProgression(['Medusa', 'Colossus', 'Chimera', 'Siren', 'Harpy', 'Carcinos'], "Greek", "Mythic")
    EGYPTIAN_CLASSICAL_MYTH_UNITS            = 5019, "Can train Egyptian Classical Myth Units", MythUnitUnlockProgression(['Sphinx', 'Wadjet', 'Anubite'], "Egyptian", "Classical")
    EGYPTIAN_HEROIC_MYTH_UNITS               = 5020, "Can train Egyptian Heroic Myth Units", MythUnitUnlockProgression(['Petsuchos', 'Scarab', 'ScorpionMan', 'Roc', 'Leviathan'], "Egyptian", "Heroic")
    EGYPTIAN_MYTHIC_MYTH_UNITS               = 5021, "Can train Egyptian Mythic Myth Units", MythUnitUnlockProgression(['Mummy', 'Avenger', 'Phoenix', 'WarTurtle'], "Egyptian", "Mythic")
    NORSE_CLASSICAL_MYTH_UNITS               = 5022, "Can train Norse Classical Myth Units", MythUnitUnlockProgression(['Valkyrie', 'Troll', 'Einheri', 'Draugr'], "Norse", "Classical")
    NORSE_HEROIC_MYTH_UNITS                  = 5023, "Can train Norse Heroic Myth Units", MythUnitUnlockProgression(['FrostGiant', 'BattleBoar', 'MountainGiant', 'RockGiant', 'Kraken'], "Norse", "Heroic")
    NORSE_MYTHIC_MYTH_UNITS                  = 5024, "Can train Norse Mythic Myth Units", MythUnitUnlockProgression(['FireGiant', 'FenrisWolfBrood', 'Fafnir', 'JormunElver'], "Norse", "Mythic")

    # Atlantean myth unit unlocks — only added to pool when random_major_gods is enabled
    ATLANTEAN_CLASSICAL_MYTH_UNITS = 5025, "Can train Atlantean Classical Myth Units", AtlanteanMythUnitUnlock(['Promethean', 'Automaton', 'Caladria', 'Servant'], "Atlantean", "Classical")
    ATLANTEAN_HEROIC_MYTH_UNITS    = 5026, "Can train Atlantean Heroic Myth Units",    AtlanteanMythUnitUnlock(['Behemoth', 'Satyr', 'StymphalianBird', 'Nereid'], "Atlantean", "Heroic")
    ATLANTEAN_MYTHIC_MYTH_UNITS    = 5027, "Can train Atlantean Mythic Myth Units",    AtlanteanMythUnitUnlock(['Centimanus', 'Argus', 'Lampades', 'ManOWar'], "Atlantean", "Mythic")

    # Chinese myth unit unlocks — only added to pool when random_major_gods is enabled
    CHINESE_CLASSICAL_MYTH_UNITS   = 5028, "Can train Chinese Classical Myth Units",   ChineseMythUnitUnlock(['QiLin', 'YaZi', 'QiongQi'], "Chinese", "Classical")
    CHINESE_HEROIC_MYTH_UNITS      = 5029, "Can train Chinese Heroic Myth Units",      ChineseMythUnitUnlock(['TaoWu', 'TaoTie', 'BaiHu', 'PiXiu', 'ChiWen', 'Fei'], "Chinese", "Heroic")
    CHINESE_MYTHIC_MYTH_UNITS      = 5030, "Can train Chinese Mythic Myth Units",      ChineseMythUnitUnlock(['QingLong', 'HunDun', 'ZhuQue', 'YingLong', 'XuanWu'], "Chinese", "Mythic")

    # Japanese myth unit unlocks — only added to pool when random_major_gods is enabled
    JAPANESE_CLASSICAL_MYTH_UNITS  = 5031, "Can train Japanese Classical Myth Units",  JapaneseMythUnitUnlock(['Kamaitachi', 'Wanyudo', 'Jorogumo'], "Japanese", "Classical")
    JAPANESE_HEROIC_MYTH_UNITS     = 5032, "Can train Japanese Heroic Myth Units",     JapaneseMythUnitUnlock(['Tengu', 'Raiju', 'Oni', 'Honengyo'], "Japanese", "Heroic")
    JAPANESE_MYTHIC_MYTH_UNITS     = 5033, "Can train Japanese Mythic Myth Units",     JapaneseMythUnitUnlock(['Asura', 'Shinigami', 'Onmoraki', 'Umibozu'], "Japanese", "Mythic")

    # Aztec myth unit unlocks — only added to pool when random_major_gods is enabled
    AZTEC_CLASSICAL_MYTH_UNITS     = 5034, "Can train Aztec Classical Myth Units",     AztecMythUnitUnlock(['Chaneque', 'CentzonTotochtin', 'Maquizcoatl'], "Aztec", "Classical")
    AZTEC_HEROIC_MYTH_UNITS        = 5035, "Can train Aztec Heroic Myth Units",        AztecMythUnitUnlock(['ObsidianButterfly', 'Ayotochtli', 'Tzitzimitl', 'Axolotl'], "Aztec", "Heroic")
    AZTEC_MYTHIC_MYTH_UNITS        = 5036, "Can train Aztec Mythic Myth Units",        AztecMythUnitUnlock(['Tunkuluchu', 'Ahuizotl', 'SoulGuide', 'AxolotlMutant', 'Quinametzin'], "Aztec", "Mythic")

    # -----------------------------------------------------------------------
    # Starting Tech items — IDs 5100-5103
    # 1 copy of each placed in the pool.
    # StartingEconomyTech / StartingMilitaryTech: Useful — grants all techs
    #   up to and including the scenario's starting age.
    # StartingDockTech / StartingBuildingsTech: Filler — same behaviour.
    # -----------------------------------------------------------------------
    STARTING_ECONOMY_TECH   = 5100, "Starting Economy Tech",    StartingEconomyTech()
    STARTING_MILITARY_TECH  = 5101, "Starting Military Tech",   StartingMilitaryTech()
    STARTING_DOCK_TECH      = 5102, "Starting Dock Tech",       StartingDockTech()
    STARTING_BUILDINGS_TECH = 5103, "Starting Buildings Tech",  StartingBuildingsTech()

    # Progressive Wonder — useful, stackable; up to 6 copies in pool.
    # Each one collected unlocks the next tier of wonder perks.  See
    # `aom.items.Items.ProgressiveWonder` for tier semantics and
    # `triggers/archipelago.xs::APApplyProgressiveWonder` for runtime effects.
    PROGRESSIVE_WONDER       = 5104, "Progressive Wonder",   ProgressiveWonder()

    # -----------------------------------------------------------------------
    # StartingArmys — Additional Filler
    # Added to cover pool shortfall when hero abilities or age unlocks are
    # removed from the pool via player options.
    # -----------------------------------------------------------------------
    STARTING_ARMY_RELIC_MONKEY    = 4029, f"{STARTING_ARMY_AMOUNT} Relic Monkeys",     StartingArmy("RelicMonkey",    STARTING_ARMY_AMOUNT)
    STARTING_ARMY_PEGASUS         = 4030, f"{STARTING_ARMY_AMOUNT} Pegasi",            StartingArmy("Pegasus",        STARTING_ARMY_AMOUNT)
    STARTING_ARMY_HYENA           = 4031, f"{STARTING_ARMY_AMOUNT} Hyenas of Set",     StartingArmy("Hyena",          STARTING_ARMY_AMOUNT)
    STARTING_ARMY_HIPPO           = 4032, f"{STARTING_ARMY_AMOUNT} Hippos of Set",     StartingArmy("Hippopotamus",   STARTING_ARMY_AMOUNT)
    STARTING_ARMY_GOLDEN_LION     = 4033, f"{STARTING_ARMY_AMOUNT} Golden Lions",      StartingArmy("GoldenLion",     STARTING_ARMY_AMOUNT)
    STARTING_ARMY_NORSE_GATHERER  = 4034, f"{STARTING_ARMY_AMOUNT} Norse Gatherers",   StartingArmy("VillagerNorse",  STARTING_ARMY_AMOUNT)
    # Chinese starting army units
    STARTING_ARMY_DAO_SWORDSMAN   = 4040, f"{STARTING_ARMY_AMOUNT} Dao Swordsmen",     StartingArmy("DaoSwordsman",    STARTING_ARMY_AMOUNT)
    STARTING_ARMY_QILIN           = 4041, "1 QiLin",                                   StartingArmy("QiLin",           1)
    STARTING_ARMY_KUAFU           = 4052, "1 Kuafu",                                   StartingArmy("Kuafu",           1)
    STARTING_ARMY_BAIHU           = 4042, "1 BaiHu",                                   StartingArmy("BaiHu",           1)
    STARTING_ARMY_QINGLONG        = 4043, "1 QingLong",                                StartingArmyUseful("QingLong",  1)
    STARTING_ARMY_PIXIU           = 4054, "1 Pixiu",                                   StartingArmy("PiXiu",           1)
    STARTING_ARMY_TAOTIE          = 4055, "1 Taotie",                                  StartingArmy("TaoTie",          1)
    # Japanese starting army units
    STARTING_ARMY_YUMI_ARCHER     = 4044, f"{STARTING_ARMY_AMOUNT} Yumi Archers",      StartingArmy("YumiArcher",      STARTING_ARMY_AMOUNT)
    STARTING_ARMY_JOROGUMO        = 4045, "1 Jorogumo",                                StartingArmy("Jorogumo",        1)
    STARTING_ARMY_ONI             = 4046, "1 Oni",                                     StartingArmy("Oni",             1)
    STARTING_ARMY_UMIBOZU         = 4047, "1 Umibozu",                                 StartingArmyUseful("Umibozu",   1)
    # Aztec starting army units
    STARTING_ARMY_EAGLE_WARRIOR   = 4048, f"{STARTING_ARMY_AMOUNT} Eagle Warriors",    StartingArmy("EagleWarrior",    STARTING_ARMY_AMOUNT)
    # Chaneque retained only for back-compat with already-generated seeds (XS
    # still spawns Chaneque for id 4049).  New generation excludes it from the
    # pool (see create_items) and uses Centzon Totochtin instead.
    STARTING_ARMY_CHANEQUE        = 4049, "1 Chaneque",                                StartingArmy("Chaneque",        1)
    STARTING_ARMY_CENTZON         = 4057, "1 Centzon Totochtin",                       StartingArmy("CentzonTotochtin", 1)
    STARTING_ARMY_TZITZIMITL      = 4050, "1 Tzitzimitl",                              StartingArmy("Tzitzimitl",      1)
    STARTING_ARMY_AHUIZOTL        = 4051, "1 Ahuizotl",                                StartingArmyUseful("Ahuizotl",  1)
    STARTING_ARMY_OBSIDIAN_BUTTERFLY = 4056, "1 Obsidian Butterfly",                   StartingArmy("ObsidianButterfly", 1)

    # -----------------------------------------------------------------------
    # Hero Stat Boosts — IDs 2000-2599
    # Applied via trModifyProtounitData / trModifyProtounitAction on load.
    # Filler (HeroStatBoostFiller): small incremental improvements.
    # Useful (HeroStatBoost): large improvements.
    #
    # Attack damage type depends on the hero:
    #   Hack (cXSActionEffectDamageHack=13): Arkantos, Ajax, Amanra
    #   Pierce (cXSActionEffectDamagePierce=14): Chiron, Odysseus, Reginleif
    # -----------------------------------------------------------------------

    # --- Arkantos — 2000-2099 ---
    ARKANTOS_HP_25       = 2000, "Arkantos +25 HP",           HeroStatBoostFiller("Arkantos", "Hitpoints", 25)
    ARKANTOS_HP_200      = 2002, "Arkantos +200 HP",          HeroStatBoostFiller("Arkantos", "Hitpoints", 200)
    ARKANTOS_ATK_1       = 2003, "Arkantos +1 Attack",        HeroStatBoostFiller("Arkantos", "HandAttack", 1, "HandAttack")
    ARKANTOS_ATK_10      = 2005, "Arkantos +10 Attack",       HeroStatBoost("Arkantos", "HandAttack", 10, "HandAttack")
    ARKANTOS_RECHARGE_2  = 2006, "Arkantos -2 Recharge Time", HeroStatBoostFiller("Arkantos", "RechargeTime", -2)
    ARKANTOS_RECHARGE_5  = 2007, "Arkantos -5 Recharge Time", HeroStatBoost("Arkantos", "RechargeTime", -5)
    ARKANTOS_REGEN_1     = 2008, "Arkantos +1 Regen",         HeroStatBoostFiller("Arkantos", "UnitRegenRate", 1)
    ARKANTOS_REGEN_5     = 2009, "Arkantos +5 Regen",         HeroStatBoost("Arkantos", "UnitRegenRate", 5)

    # --- Ajax — 2100-2199 ---
    AJAX_HP_25           = 2100, "Ajax +25 HP",               HeroStatBoostFiller("Ajax", "Hitpoints", 25)
    AJAX_HP_200          = 2102, "Ajax +200 HP",              HeroStatBoostFiller("Ajax", "Hitpoints", 200)
    AJAX_ATK_1           = 2103, "Ajax +1 Attack",            HeroStatBoostFiller("Ajax", "HandAttack", 1, "HandAttack")
    AJAX_ATK_10          = 2105, "Ajax +10 Attack",           HeroStatBoost("Ajax", "HandAttack", 10, "HandAttack")
    AJAX_RECHARGE_2      = 2106, "Ajax -2 Recharge Time",     HeroStatBoostFiller("Ajax", "RechargeTime", -2)
    AJAX_RECHARGE_5      = 2107, "Ajax -5 Recharge Time",     HeroStatBoost("Ajax", "RechargeTime", -5)
    AJAX_REGEN_1         = 2108, "Ajax +1 Regen",             HeroStatBoostFiller("Ajax", "UnitRegenRate", 1)
    AJAX_REGEN_5         = 2109, "Ajax +5 Regen",             HeroStatBoost("Ajax", "UnitRegenRate", 5)

    # --- Chiron — 2200-2299 ---
    CHIRON_HP_25         = 2200, "Chiron +25 HP",             HeroStatBoostFiller("Chiron", "Hitpoints", 25)
    CHIRON_HP_200        = 2202, "Chiron +200 HP",            HeroStatBoostFiller("Chiron", "Hitpoints", 200)
    CHIRON_ATK_1         = 2203, "Chiron +1 Attack",          HeroStatBoostFiller("Chiron", "RangedAttack", 1, "RangedAttack")
    CHIRON_ATK_10        = 2205, "Chiron +10 Attack",         HeroStatBoost("Chiron", "RangedAttack", 10, "RangedAttack")
    CHIRON_RECHARGE_2    = 2206, "Chiron -2 Recharge Time",   HeroStatBoostFiller("Chiron", "RechargeTime", -2)
    CHIRON_RECHARGE_5    = 2207, "Chiron -5 Recharge Time",   HeroStatBoost("Chiron", "RechargeTime", -5)
    CHIRON_REGEN_1       = 2208, "Chiron +1 Regen",           HeroStatBoostFiller("Chiron", "UnitRegenRate", 1)
    CHIRON_REGEN_5       = 2209, "Chiron +5 Regen",           HeroStatBoost("Chiron", "UnitRegenRate", 5)

    # --- Amanra — 2300-2399 ---
    AMANRA_HP_25         = 2300, "Amanra +25 HP",             HeroStatBoostFiller("Amanra", "Hitpoints", 25)
    AMANRA_HP_200        = 2302, "Amanra +200 HP",            HeroStatBoostFiller("Amanra", "Hitpoints", 200)
    AMANRA_ATK_1         = 2303, "Amanra +1 Attack",          HeroStatBoostFiller("Amanra", "HandAttack", 1, "HandAttack")
    AMANRA_ATK_10        = 2305, "Amanra +10 Attack",         HeroStatBoost("Amanra", "HandAttack", 10, "HandAttack")
    AMANRA_RECHARGE_2    = 2306, "Amanra -2 Recharge Time",   HeroStatBoostFiller("Amanra", "RechargeTime", -2)
    AMANRA_RECHARGE_5    = 2307, "Amanra -5 Recharge Time",   HeroStatBoost("Amanra", "RechargeTime", -5)
    AMANRA_REGEN_1       = 2308, "Amanra +1 Regen",           HeroStatBoostFiller("Amanra", "UnitRegenRate", 1)
    AMANRA_REGEN_5       = 2309, "Amanra +5 Regen",           HeroStatBoost("Amanra", "UnitRegenRate", 5)

    # --- Odysseus — 2400-2499 ---
    ODYSSEUS_HP_25       = 2400, "Odysseus +25 HP",           HeroStatBoostFiller("Odysseus", "Hitpoints", 25)
    ODYSSEUS_HP_200      = 2402, "Odysseus +200 HP",          HeroStatBoostFiller("Odysseus", "Hitpoints", 200)
    ODYSSEUS_ATK_1       = 2403, "Odysseus +1 Attack",        HeroStatBoostFiller("Odysseus", "RangedAttack", 1, "RangedAttack")
    ODYSSEUS_ATK_10      = 2405, "Odysseus +10 Attack",       HeroStatBoost("Odysseus", "RangedAttack", 10, "RangedAttack")
    ODYSSEUS_RECHARGE_2  = 2406, "Odysseus -2 Recharge Time", HeroStatBoostFiller("Odysseus", "RechargeTime", -2)
    ODYSSEUS_RECHARGE_5  = 2407, "Odysseus -5 Recharge Time", HeroStatBoost("Odysseus", "RechargeTime", -5)
    ODYSSEUS_REGEN_1     = 2408, "Odysseus +1 Regen",         HeroStatBoostFiller("Odysseus", "UnitRegenRate", 1)
    ODYSSEUS_REGEN_5     = 2409, "Odysseus +5 Regen",         HeroStatBoost("Odysseus", "UnitRegenRate", 5)

    # --- Reginleif — 2500-2599 ---
    # Note: Reginleif has no rechargeable special attack, so no RECHARGE items.
    REGINLEIF_HP_25      = 2500, "Reginleif +25 HP",          HeroStatBoostFiller("Reginleif", "Hitpoints", 25)
    REGINLEIF_HP_200     = 2502, "Reginleif +200 HP",         HeroStatBoostFiller("Reginleif", "Hitpoints", 200)
    REGINLEIF_ATK_1      = 2503, "Reginleif +1 Attack",       HeroStatBoostFiller("Reginleif", "RangedAttack", 1, "RangedAttack")
    REGINLEIF_ATK_10     = 2505, "Reginleif +10 Attack",      HeroStatBoost("Reginleif", "RangedAttack", 10, "RangedAttack")
    REGINLEIF_REGEN_1    = 2508, "Reginleif +1 Regen",        HeroStatBoostFiller("Reginleif", "UnitRegenRate", 1)
    REGINLEIF_REGEN_5    = 2509, "Reginleif +5 Regen",        HeroStatBoost("Reginleif", "UnitRegenRate", 5)

    # -----------------------------------------------------------------------
    # Hero Special Abilities and Action Boosts — IDs 2600-3199
    # Applied via trProtounitActionSpecialEffect* and trModifyProtounitAction
    # on scenario load. All classified as useful.
    # -----------------------------------------------------------------------

    # --- Arkantos — 2600-2699 ---

    # Lifesteal: Each HandAttack hit heals Arkantos for a portion of the damage dealt.
    ARKANTOS_LIFESTEAL        = 2600, "Arkantos Lifesteal",          HeroSpecialEffect("Arkantos", "HandAttack Lifesteal All 1 10")

    # Petrifying Shout: Arkantos's AutoBoost (shout ability) petrifies nearby
    # enemy units on activation, dealing divine damage and turning them to stone.
    ARKANTOS_PETRIFYING_SHOUT = 2601, "Arkantos Petrifying Shout",   HeroSpecialEffect("Arkantos", "AutoBoost FreezeStone Unit Divine 3 10")

    # Arkantos is a House: Arkantos's presence on the map provides 10 free
    # population capacity by reducing his own pop count to -10.
    ARKANTOS_HOUSING          = 2602, "Arkantos is a House",          ArkantosHousing()

    # Attack Speed: Reduces Arkantos's HandAttack rate of fire by 0.25,
    # making his standard attacks faster.
    ARKANTOS_ATTACK_SPEED     = 2603, "Arkantos Attack Speed",        HeroActionBoost("Arkantos", "HandAttack", 4, -0.25)

    # --- Ajax — 2700-2799 ---

    # Stunning Blow: Ajax's Gore (shield bash) stuns the target for 10 seconds.
    AJAX_STUNNING_BLOW        = 2700, "Ajax Stunning Blow",           HeroSpecialEffect("Ajax", "Gore Stun All 10 10")

    # Smiting Strikes: Ajax's HandAttack temporarily reduces the target's
    # MaxHP and visually shrinks them on hit.
    AJAX_SMITING_STRIKES      = 2701, "Ajax Smiting Strikes",         HeroSpecialEffect("Ajax", "HandAttack StatModify+VisualScale Unit 0.5 MaxHP")

    # Shield Bash AOE: Increases the area of effect of Ajax's Gore (shield bash)
    # by 10, hitting multiple nearby enemies simultaneously.
    AJAX_SHIELD_BASH_AOE      = 2702, "Ajax Shield Bash AOE",         HeroActionBoost("AjaxSPC", "Gore", 3, 10.0)

    # --- Chiron — 2800-2899 ---

    # Poison Arrow: Chiron's RangedAttack applies a damage-over-time poison
    # effect to targets, dealing additional damage over 5 seconds.
    CHIRON_POISON_ARROW       = 2800, "Chiron Poison Arrow",          HeroSpecialEffect("Chiron", "RangedAttack DamageOverTime All 5 10")

    # Crippling Fire: Chiron's RangedAttack slows the target's attack rate
    # for 3 seconds, reducing their offensive output.
    CHIRON_CRIPPLING_FIRE     = 2801, "Chiron Crippling Fire",        HeroSpecialEffect("Chiron", "RangedAttack StatModify Unit 3 ROF")

    # Shotgun Special: Chiron's ChargedRangedAttack (special shot) fires
    # 15 additional projectiles simultaneously.
    CHIRON_SHOTGUN_SPECIAL    = 2802, "Chiron Shotgun Special",       HeroActionBoost("ChironSPC", "ChargedRangedAttack", 8, 15.0)

    # --- Amanra — 2900-2999 ---

    # Whirlwind Throw: Amanra's JumpAttack (leap strike) throws the target
    # unit through the air on hit.
    AMANRA_SHOCKWAVE_JUMP     = 2900, "Amanra Shockwave Jump",        HeroSpecialEffect("Amanra", "JumpAttack Throw All 10 10")

    # Army of the Dead: Units slain by Amanra's HandAttack are reincarnated
    # as allied Minions that fight for the player.
    AMANRA_ARMY_OF_THE_DEAD   = 2901, "Amanra Army of the Dead",      HeroSpecialEffect("Amanra", "HandAttack Reincarnation Unit minion 1 1")

    # Divine Smite: Amanra's HandAttack deals +5 divine damage on each hit,
    # effective against myth units with high pierce/hack resistance.
    AMANRA_DIVINE_SMITE       = 2902, "Amanra Divine Smite",          HeroActionBoost("Amanra", "HandAttack", 16, 5.0)

    # --- Odysseus — 3000-3099 ---

    # Entangling Shot: Odysseus's ChargedRangedAttack snares the target,
    # reducing their movement speed for 10 seconds.
    ODYSSEUS_ENTANGLING_SHOT  = 3000, "Odysseus Entangling Shot",     HeroSpecialEffect("Odysseus", "ChargedRangedAttack Snare All 10 10")

    # Swift Escape: Odysseus's RangedAttack temporarily boosts his own
    # movement speed after firing, helping him reposition.
    ODYSSEUS_SWIFT_ESCAPE     = 3001, "Odysseus Swift Escape",        HeroSpecialEffect("Odysseus", "RangedAttack StatModify Unit 0.5 Speed")

    # Perfect Accuracy: Odysseus's RangedAttack gains +5 perfect accuracy,
    # reducing projectile spread so more shots land on target.
    ODYSSEUS_PERFECT_ACCURACY = 3002, "Odysseus Perfect Accuracy",    HeroActionBoost("OdysseusSPC", "RangedAttack", 10, 5.0)

    # --- Reginleif — 3100-3199 ---

    # Frost Strike: Reginleif's RangedAttack progressively slows the target's
    # attack rate over multiple hits, eventually freezing it entirely.
    REGINLEIF_FROST_STRIKE    = 3100, "Reginleif Frost Strike",       HeroSpecialEffect("Reginleif", "RangedAttack ProgressiveFreeze All 3 3")

    # +1 Projectile: Reginleif's RangedAttack fires one additional projectile
    # per shot, increasing her damage output per attack.
    # Note: ID 2510 falls in the stat boost range but is an action boost;
    # placed here for readability alongside Reginleif's other abilities.
    REGINLEIF_PROJECTILE      = 2510, "Reginleif +1 Projectile",      HeroActionBoost("Reginleif", "RangedAttack", 8, 1.0)

    # ---------------------------------------------------------------------------
    # Kastor Hero Items — IDs 3400-3409 (stats), 3300-3302 (specials)
    # Kastor appears in New Atlantis. Stat boosts follow the same rarity pattern
    # as other heroes. Special abilities require hero_abilities=True.
    # NOTE: stat boost IDs use 3400-3409 — the 3200-3209 range collides with
    # the CAN_TRAIN_* unit unlocks (3200 Hoplite, 3201 Spearman, 3202 Berserk),
    # which would silently alias the colliding Kastor entries inside the IntEnum
    # and remove them from the world entirely.
    # ---------------------------------------------------------------------------
    # Stat Boosts (Filler)
    KASTOR_HP_25        = 3400, "Kastor +25 HP",           HeroStatBoostFiller("Kastor", "Hitpoints", 25)
    KASTOR_HP_200       = 3402, "Kastor +200 HP",          HeroStatBoostFiller("Kastor", "Hitpoints", 200)
    KASTOR_ATK_1        = 3403, "Kastor +1 Attack",        HeroStatBoostFiller("Kastor", "HandAttack", 1, "HandAttack")
    KASTOR_RECHARGE_1   = 3406, "Kastor -1 Recharge Time", HeroStatBoostFiller("Kastor", "RechargeTime", -1)
    KASTOR_REGEN_1      = 3408, "Kastor +1 Regen",         HeroStatBoostFiller("Kastor", "UnitRegenRate", 1)
    # Stat Boosts (Useful)
    KASTOR_ATK_10       = 3405, "Kastor +10 Attack",       HeroStatBoost("Kastor", "HandAttack", 10, "HandAttack")
    KASTOR_RECHARGE_3_5 = 3407, "Kastor -3.5 Recharge Time", HeroStatBoost("Kastor", "RechargeTime", -3.5)
    KASTOR_REGEN_5      = 3409, "Kastor +5 Regen",         HeroStatBoost("Kastor", "UnitRegenRate", 5)
    # Special Abilities (Useful, removed if hero_abilities=False)
    KASTOR_UNDERMINE_ATTACKS = 3300, "Kastor Undermines with Attacks", HeroSpecialEffect("Kastor", "HandAttack DamageOverTime Building Crush 13 25")
    KASTOR_SUMMON_SOLDIERS   = 3301, "Kastor Can Summon Soldiers",     HeroSpecialEffect("Kastor", "AddTrain Hoplite Spearman Berserk Murmillo")
    KASTOR_IS_A_MANOR        = 3302, "Kastor is a Manor",              ArkantosHousing()  # 20 pop cap

    # -----------------------------------------------------------------------
    # Villager Carry Capacity — IDs 5000-5008
    # Increases how much of a resource each villager type can carry per trip.
    # Applied via trModifyProtounitResource (cXSPUResourceEffectCarryCapacity=1).
    # -----------------------------------------------------------------------
    GREEK_CARRY_FOOD    = 5000, "Greek Villagers Carry +10 Food",    VillagerCarryCapacity("VillagerGreek",    "food",  10)
    GREEK_CARRY_WOOD    = 5001, "Greek Villagers Carry +10 Wood",    VillagerCarryCapacity("VillagerGreek",    "wood",  10)
    GREEK_CARRY_GOLD    = 5002, "Greek Villagers Carry +10 Gold",    VillagerCarryCapacity("VillagerGreek",    "gold",  10)
    EGYPTIAN_CARRY_FOOD = 5003, "Egyptian Villagers Carry +10 Food", VillagerCarryCapacity("VillagerEgyptian", "food",  10)
    EGYPTIAN_CARRY_WOOD = 5004, "Egyptian Villagers Carry +10 Wood", VillagerCarryCapacity("VillagerEgyptian", "wood",  10)
    EGYPTIAN_CARRY_GOLD = 5005, "Egyptian Villagers Carry +10 Gold", VillagerCarryCapacity("VillagerEgyptian", "gold",  10)
    NORSE_CARRY_FOOD    = 5006, "Norse Villagers Carry +10 Food",    VillagerCarryCapacity("VillagerNorse",    "food",  10)
    NORSE_CARRY_WOOD    = 5007, "Norse Villagers Carry +10 Wood",    VillagerCarryCapacity("VillagerNorse",    "wood",  10)
    NORSE_CARRY_GOLD    = 5008, "Norse Villagers Carry +10 Gold",    VillagerCarryCapacity("VillagerNorse",    "gold",  10)
    CHINESE_CARRY_FOOD   = 5010, "Chinese Villagers Carry +10 Food",   VillagerCarryCapacity("VillagerChinese",  "food",  10)
    CHINESE_CARRY_WOOD   = 5011, "Chinese Villagers Carry +10 Wood",   VillagerCarryCapacity("VillagerChinese",  "wood",  10)
    CHINESE_CARRY_GOLD   = 5012, "Chinese Villagers Carry +10 Gold",   VillagerCarryCapacity("VillagerChinese",  "gold",  10)
    JAPANESE_CARRY_FOOD  = 5013, "Japanese Villagers Carry +10 Food",  VillagerCarryCapacity("VillagerJapanese", "food",  10)
    JAPANESE_CARRY_WOOD  = 5014, "Japanese Villagers Carry +10 Wood",  VillagerCarryCapacity("VillagerJapanese", "wood",  10)
    JAPANESE_CARRY_GOLD  = 5037, "Japanese Villagers Carry +10 Gold",  VillagerCarryCapacity("VillagerJapanese", "gold",  10)
    AZTEC_CARRY_FOOD     = 5038, "Aztec Villagers Carry +10 Food",     VillagerCarryCapacity("VillagerAztec",    "food",  10)
    AZTEC_CARRY_WOOD     = 5039, "Aztec Villagers Carry +10 Wood",     VillagerCarryCapacity("VillagerAztec",    "wood",  10)
    AZTEC_CARRY_GOLD     = 5040, "Aztec Villagers Carry +10 Gold",     VillagerCarryCapacity("VillagerAztec",    "gold",  10)

    # -----------------------------------------------------------------------
    # Generic Villager Food Cost Reduction — ID 5009
    # Reduces the food cost to train ALL villager types by 5.
    # Applied via trModifyProtounitResource (cXSPUResourceEffectCost=0).
    # Generic — not civ-specific; always in pool regardless of enabled civs.
    # -----------------------------------------------------------------------
    VILLAGER_DISCOUNT = 5009, "Villagers Cost -5 Food", GenericVillagerDiscount(5)

    # One-shot generic useful effects.  Applied per scenario start by
    # APApplyAllItems in archipelago.xs; the dataclasses carry no fields and
    # are detected purely by item id.
    CHIRON_SWIMMING_LESSONS = 5010, "Chiron's Swimming Lessons", ChironSwimmingLessons()
    FAVOR_ON_HUMAN_KILL     = 5011, "Killing Enemy Human Soldiers Grants Favor", FavorOnHumanKill()
    FAVOR_ON_MYTH_KILL      = 5012, "Killing Enemy Myth Units Grants Favor",     FavorOnMythKill()


# -----------------------------------------------------------------------
# Lookup tables
# -----------------------------------------------------------------------
# Built once at import time from `aomItemData`.  Anything outside this
# module (the world class, Rules.py, the AP framework) consumes one of
# these maps rather than scanning the enum.  Adding a new aomItemData
# member auto-registers in all of these — no additional plumbing needed.

NAME_TO_ITEM: dict[str, aomItemData] = {}                # display name → enum member
ID_TO_ITEM: dict[int, aomItemData] = {}                  # AP item id  → enum member
# UNUSED: never read outside this module. Kept (commented) for future grouping queries.
# CATEGORY_TO_ITEMS: dict[type, list[aomItemData]] = {}    # dataclass type → all items of that kind
filler_items: list[aomItemData] = []                     # pre-filtered list of filler-classified items
item_id_to_name: dict[int, str] = {}                     # AP item id → display name (mirror used by AP framework)
item_name_to_id: dict[str, int] = {}                     # display name → AP item id (mirror used by AP framework)

for item in aomItemData:
    assert item.item_name not in item_name_to_id, f"Duplicate item name: {item.item_name}"
    assert item.id not in item_id_to_name, f"Duplicate item ID: {item.id}"

    NAME_TO_ITEM[item.item_name] = item
    ID_TO_ITEM[item.id] = item

    if item_type_to_classification[item.type_data] == ItemClassification.filler:
        filler_items.append(item)

    item_id_to_name[item.id] = item.item_name
    item_name_to_id[item.item_name] = item.id
    # CATEGORY_TO_ITEMS.setdefault(item.type_data, []).append(item)  # disabled with CATEGORY_TO_ITEMS above


# -----------------------------------------------------------------------
# Scenario Keys — one item per scenario (IDs 3600+)
# -----------------------------------------------------------------------
# Each scenario in `aomScenarioData` gets its own AP item with a friendly
# name like "4. A Fine Plan Scenario Key" or "NA 2. Atlantis Reborn Scenario Key".
# When `max_keys_on_keyrings == 1`, each Scenario Key is placed directly in
# the multiworld (announced individually as "Player1 found their X. Foo
# Scenario Key"). When `max_keys_on_keyrings >= 2`, Scenario Key items are
# NOT placed; KeyRing items carry them instead and `aomWorld._generate_
# keyring_assignments` decides which scenarios share a ring.
#
# `SCENARIO_TO_KEY_ID[global_number] → AP item id`.  IDs are assigned in
# `aomScenarioData` enum order starting from `SCENARIO_KEY_BASE_ID`, so they
# are stable across slots and seeds.  Items are duck-typed (not enum members)
# because the rest of the codebase only reads `.id`/`.item_name`/`.type`/
# `.type_data`.
# -----------------------------------------------------------------------
from ..locations.Scenarios import aomScenarioData as _aomScenarioData

SCENARIO_KEY_BASE_ID    = 3600

class _ScenarioKeyItem:
    """Lightweight stand-in for an `aomItemData` enum member.  Has the same
    duck-typed surface (`id`, `item_name`, `type`, `type_data`) so existing
    code paths (`create_item`, fill, classification) work unchanged."""
    __slots__ = ("id", "item_name", "type", "type_data")
    def __init__(self, id: int, item_name: str, bundle_index: int) -> None:
        self.id        = id
        self.item_name = item_name
        self.type      = ScenarioKey(bundle_index)
        self.type_data = ScenarioKey

SCENARIO_TO_KEY_ID: dict[int, int] = {}
SCENARIO_KEY_ID_TO_GLOBAL_NUMBER: dict[int, int] = {}

for _idx, _scen in enumerate(_aomScenarioData):
    _kid  = SCENARIO_KEY_BASE_ID + _idx
    _name = f"{_scen.display_name} Scenario Key"
    _obj  = _ScenarioKeyItem(_kid, _name, _idx + 1)
    NAME_TO_ITEM[_name]      = _obj
    ID_TO_ITEM[_kid]         = _obj
    item_id_to_name[_kid]    = _name
    item_name_to_id[_name]   = _kid
    SCENARIO_TO_KEY_ID[_scen.global_number]    = _kid
    SCENARIO_KEY_ID_TO_GLOBAL_NUMBER[_kid]     = _scen.global_number


# -----------------------------------------------------------------------
# Key Rings — bundle items used when `max_keys_on_keyrings` >= 2 (IDs 3700+)
# -----------------------------------------------------------------------
# Stable AP items "Scenario Key Ring 1" .. "Scenario Key Ring N", one per
# possible ring slot.  Per seed only ceil(active_scenarios / max) of them
# are actually placed; the rest sit dormant in the registry so item IDs
# stay stable across seeds.  Per-seed contents (ring_id -> list of
# scenario global numbers) are computed in
# `aomWorld._generate_keyring_assignments` and emitted via slot_data so
# the client can fan a single ring receipt out into per-scenario unlocks
# and notifications.
# -----------------------------------------------------------------------
KEY_RING_BASE_ID    = 3700
MAX_KEY_RINGS       = len(list(_aomScenarioData))  # worst case = 1 ring per scenario

class _KeyRingItem:
    """Duck-typed KeyRing AP item (parallels _ScenarioKeyItem)."""
    __slots__ = ("id", "item_name", "type", "type_data")
    def __init__(self, id: int, item_name: str, ring_index: int) -> None:
        self.id        = id
        self.item_name = item_name
        self.type      = KeyRing(ring_index)
        self.type_data = KeyRing

RING_INDEX_TO_ITEM_ID: dict[int, int] = {}
RING_ITEM_ID_TO_INDEX: dict[int, int] = {}

for _i in range(MAX_KEY_RINGS):
    _ring_index = _i + 1
    _rid        = KEY_RING_BASE_ID + _i
    _ring_name  = f"Scenario Key Ring {_ring_index}"
    _ring_obj   = _KeyRingItem(_rid, _ring_name, _ring_index)
    NAME_TO_ITEM[_ring_name]      = _ring_obj
    ID_TO_ITEM[_rid]              = _ring_obj
    item_id_to_name[_rid]         = _ring_name
    item_name_to_id[_ring_name]   = _rid
    RING_INDEX_TO_ITEM_ID[_ring_index] = _rid
    RING_ITEM_ID_TO_INDEX[_rid]        = _ring_index