from dataclasses import dataclass
import enum

from BaseClasses import ItemClassification
from ..locations.Campaigns import aomCampaignData


# -----------------------------------------------------------------------
# Tuning constants
# -----------------------------------------------------------------------

BASE_ID = 0x3B0000  # 3866624 — AP location/item ID offset
BASE_RESOURCE = 30
REINFORCEMENT_AMOUNT = 2


# -----------------------------------------------------------------------
# Item type dataclasses
# -----------------------------------------------------------------------

@dataclass
class Victory:
    pass


@dataclass
class Campaign:
    vanilla_campaign: aomCampaignData


@dataclass
class AgeUnlock:
    culture: str  # "Greek", "Egyptian", or "Norse"


@dataclass
class FinalUnlock:
    pass


@dataclass
class Gem:
    """Currency earned by beating scenarios, spent in the shop."""
    pass


@dataclass
class ProgressiveShopInfo:
    """Unlocks additional label detail in the Gem Shop. One per shop tier."""
    pass

@dataclass
class Trap:
    """A trap sent to the AoM player that activates mid-scenario."""
    trap_type: int  # matches cAPTrap* constants in ap_ai_runtime.xs



@dataclass
class StartingResources:
    type: "Resource"
    amount: int


@dataclass
class StartingResourcesLarge:
    type: "Resource"
    amount: int


@dataclass
class PassiveIncome:
    resource: "Resource"
    amount_per_minute: int


@dataclass
class PassiveIncomeLarge:
    resource: "Resource"
    amount_per_minute: int


@dataclass
class Reinforcement:
    unit_name: str
    amount: int


# Useful variant of Reinforcement — classified as useful instead of filler.
# Must be defined before the classification dict.
class ReinforcementUseful(Reinforcement):
    pass


@dataclass
class UnitStatBonus:
    unit_name: str
    stat: str
    amount: int


@dataclass
class UnitUnlockProgression:
    unit_name: str
    culture: str


@dataclass
class UnitUnlockUseful:
    unit_name: str
    culture: str


@dataclass
class MythUnitUnlockProgression:
    units: list  # proto unit names forbidden until received
    culture: str
    age: str


@dataclass
class MythUnitUnlockUseful:
    units: list
    culture: str
    age: str


@dataclass
class MythUnitUnlockFiller:
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
class HeroStatBoost:
    hero: str          # proto unit name e.g. "Arkantos", "AjaxSPC"
    stat: str          # e.g. "Hitpoints", "HandAttack", "RechargeTime", "UnitRegenRate"
    amount: float      # positive = add, negative = subtract
    attack_type: str = ""  # action name used for attack boosts e.g. "HandAttack", "RangedAttack"


# Filler variant of HeroStatBoost — small incremental boosts.
# Must be defined before the classification dict.
class HeroStatBoostFiller(HeroStatBoost):
    pass


@dataclass
class HeroSpecialEffect:
    hero: str
    description: str   # internal description of the effect (see comments at each item)


@dataclass
class HeroActionBoost:
    hero: str          # proto unit name e.g. "Arkantos"
    action: str        # action name e.g. "HandAttack", "Gore", "ChargedRangedAttack"
    effect: int        # cXSActionEffect* constant (see MythTRConstants.txt)
    amount: float      # value to apply


@dataclass
class ArkantosHousing:
    pass               # gives Arkantos -10 pop count, providing 10 free population capacity


@dataclass
class GenericVillagerDiscount:
    """Reduces food cost for all villager types (Greek, Egyptian, Norse, Atlantean)."""
    reduction: int  # food cost reduction applied to each villager type

@dataclass
class VillagerCarryCapacity:
    unit_name: str    # proto unit name e.g. "VillagerGreek"
    resource: str     # "food", "wood", or "gold"
    amount: int       # carry capacity increase


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
    Reinforcement,
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
    FinalUnlock:            ItemClassification.progression,
    Gem:                    ItemClassification.filler,
    ProgressiveShopInfo:    ItemClassification.useful,
    Trap:                   ItemClassification.trap,
    UnitUnlockProgression:  ItemClassification.progression,
    StartingResources:      ItemClassification.filler,
    PassiveIncome:          ItemClassification.filler,
    Reinforcement:          ItemClassification.filler,
    HeroStatBoostFiller:    ItemClassification.filler,
    StartingResourcesLarge: ItemClassification.filler,
    PassiveIncomeLarge:     ItemClassification.filler,
    ReinforcementUseful:    ItemClassification.useful,
    UnitStatBonus:          ItemClassification.useful,
    UnitUnlockUseful:       ItemClassification.useful,
    HeroStatBoost:          ItemClassification.useful,
    HeroSpecialEffect:      ItemClassification.useful,
    HeroActionBoost:        ItemClassification.useful,
    ArkantosHousing:        ItemClassification.useful,
    VillagerCarryCapacity:   ItemClassification.filler,
    GenericVillagerDiscount: ItemClassification.filler,
    MythUnitUnlockProgression:   ItemClassification.progression,
    MythUnitUnlockUseful:        ItemClassification.progression,
    MythUnitUnlockFiller:        ItemClassification.progression,
    AtlanteanUnitUnlockProgression: ItemClassification.progression,
    AtlanteanUnitUnlockUseful:      ItemClassification.useful,
    AtlanteanMythUnitUnlock:        ItemClassification.progression,
    StartingEconomyTech:            ItemClassification.useful,
    StartingMilitaryTech:           ItemClassification.useful,
    StartingDockTech:               ItemClassification.filler,
    StartingBuildingsTech:          ItemClassification.filler,
}


# -----------------------------------------------------------------------
# Resource helpers
# -----------------------------------------------------------------------

def _res(multiplier: float, favor: bool = False) -> int:
    amount = int(BASE_RESOURCE * multiplier)
    if favor:
        amount = amount // 2
    return amount


def _passive(multiplier: float, favor: bool = False) -> int:
    base = BASE_RESOURCE // 5
    amount = int(base * multiplier)
    if favor:
        amount = amount // 2
    return amount


# -----------------------------------------------------------------------
# Item definitions
# -----------------------------------------------------------------------

class aomItemData(enum.IntEnum):
    def __new__(cls, id: int, name: str, type: ItemType) -> "aomItemData":
        value = id
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    def __init__(self, id: int, name: str, type: ItemType) -> None:
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

    # -----------------------------------------------------------------------
    # Starting Resources
    # Filler: small grants (BASE_RESOURCE x1).
    # Useful: large grants (BASE_RESOURCE x4).
    # -----------------------------------------------------------------------
    STARTING_WOOD_SMALL   = 1,  f"+{_res(1)} Starting Wood",              StartingResources(Resource.WOOD,  _res(1))
    STARTING_FOOD_SMALL   = 2,  f"+{_res(1)} Starting Food",              StartingResources(Resource.FOOD,  _res(1))
    STARTING_GOLD_SMALL   = 3,  f"+{_res(1)} Starting Gold",              StartingResources(Resource.GOLD,  _res(1))
    STARTING_FAVOR_SMALL  = 4,  f"+{_res(1, favor=True)} Starting Favor", StartingResources(Resource.FAVOR, _res(1, favor=True))

    STARTING_WOOD_LARGE   = 9,  f"+{_res(4)} Starting Wood",              StartingResourcesLarge(Resource.WOOD,  _res(4))
    STARTING_FOOD_LARGE   = 10, f"+{_res(4)} Starting Food",              StartingResourcesLarge(Resource.FOOD,  _res(4))
    STARTING_GOLD_LARGE   = 11, f"+{_res(4)} Starting Gold",              StartingResourcesLarge(Resource.GOLD,  _res(4))
    STARTING_FAVOR_LARGE  = 12, f"+{_res(4, favor=True)} Starting Favor", StartingResourcesLarge(Resource.FAVOR, _res(4, favor=True))

    # -----------------------------------------------------------------------
    # Passive Income
    # Filler: small rate (BASE//5 x1). Granted every 60s (favor: every 20s).
    # Useful: large rate (BASE//5 x4).
    # -----------------------------------------------------------------------
    PASSIVE_WOOD_SMALL    = 13, f"+{_passive(1)} Wood/min",              PassiveIncome(Resource.WOOD,  _passive(1))
    PASSIVE_FOOD_SMALL    = 14, f"+{_passive(1)} Food/min",              PassiveIncome(Resource.FOOD,  _passive(1))
    PASSIVE_GOLD_SMALL    = 15, f"+{_passive(1)} Gold/min",              PassiveIncome(Resource.GOLD,  _passive(1))
    PASSIVE_FAVOR_SMALL   = 16, f"+{_passive(1, favor=True)} Favor/min", PassiveIncome(Resource.FAVOR, _passive(1, favor=True))

    PASSIVE_WOOD_LARGE    = 21, f"+{_passive(4)} Wood/min",              PassiveIncomeLarge(Resource.WOOD,  _passive(4))
    PASSIVE_FOOD_LARGE    = 22, f"+{_passive(4)} Food/min",              PassiveIncomeLarge(Resource.FOOD,  _passive(4))
    PASSIVE_GOLD_LARGE    = 23, f"+{_passive(4)} Gold/min",              PassiveIncomeLarge(Resource.GOLD,  _passive(4))
    PASSIVE_FAVOR_LARGE   = 24, f"+{_passive(4, favor=True)} Favor/min", PassiveIncomeLarge(Resource.FAVOR, _passive(4, favor=True))

    # -----------------------------------------------------------------------
    # Reinforcements — Filler
    # Each item spawns REINFORCEMENT_AMOUNT (2) units near the spawn point.
    # -----------------------------------------------------------------------
    REINFORCEMENT_ANUBITES        = 4000, f"{REINFORCEMENT_AMOUNT} Anubites",          Reinforcement("Anubite",          REINFORCEMENT_AMOUNT)
    REINFORCEMENT_HOPLITE         = 4001, f"{REINFORCEMENT_AMOUNT} Hoplites",          Reinforcement("Hoplite",          REINFORCEMENT_AMOUNT)
    REINFORCEMENT_DWARF           = 4002, f"{REINFORCEMENT_AMOUNT} Dwarves",           Reinforcement("Dwarf",            REINFORCEMENT_AMOUNT)
    REINFORCEMENT_MERCENARY       = 4003, f"{REINFORCEMENT_AMOUNT} Mercenaries",       Reinforcement("Mercenary",        REINFORCEMENT_AMOUNT)
    REINFORCEMENT_MERCENARY_CAV   = 4004, f"{REINFORCEMENT_AMOUNT} Mercenary Cavalry", Reinforcement("MercenaryCavalry", REINFORCEMENT_AMOUNT)
    REINFORCEMENT_AUTOMATON       = 4006, f"{REINFORCEMENT_AMOUNT} Automatons",        Reinforcement("Automaton",        REINFORCEMENT_AMOUNT)
    REINFORCEMENT_WADJET          = 4007, f"{REINFORCEMENT_AMOUNT} Wadjets",           Reinforcement("Wadjet",           REINFORCEMENT_AMOUNT)
    REINFORCEMENT_ULFSARK         = 4008, f"{REINFORCEMENT_AMOUNT} Berserks",          Reinforcement("Berserk",          REINFORCEMENT_AMOUNT)
    REINFORCEMENT_SLINGER         = 4009, f"{REINFORCEMENT_AMOUNT} Slingers",          Reinforcement("Slinger",          REINFORCEMENT_AMOUNT)
    REINFORCEMENT_TURMA           = 4010, f"{REINFORCEMENT_AMOUNT} Turmas",            Reinforcement("Turma",            REINFORCEMENT_AMOUNT)
    REINFORCEMENT_KATASKOPOS      = 4011, f"{REINFORCEMENT_AMOUNT} Kataskopos",        Reinforcement("Kataskopos",       REINFORCEMENT_AMOUNT)
    REINFORCEMENT_VILLAGER        = 4013, f"{REINFORCEMENT_AMOUNT} Greek Villagers",   Reinforcement("VillagerGreek",    REINFORCEMENT_AMOUNT)
    REINFORCEMENT_BATTLE_BOAR     = 4015, f"{REINFORCEMENT_AMOUNT} Battle Boars",      Reinforcement("BattleBoar",       REINFORCEMENT_AMOUNT)
    REINFORCEMENT_RAIDING_CAVALRY = 4020, f"{REINFORCEMENT_AMOUNT} Raiding Cavalry",   Reinforcement("RaidingCavalry",   REINFORCEMENT_AMOUNT)
    REINFORCEMENT_ORACLE          = 4021, f"{REINFORCEMENT_AMOUNT} Oracles",           Reinforcement("Oracle",           REINFORCEMENT_AMOUNT)
    REINFORCEMENT_CYCLOPS         = 4022, f"{REINFORCEMENT_AMOUNT} Cyclopes",          Reinforcement("Cyclops",          REINFORCEMENT_AMOUNT)
    REINFORCEMENT_TROLL           = 4023, f"{REINFORCEMENT_AMOUNT} Trolls",            Reinforcement("Troll",            REINFORCEMENT_AMOUNT)
    REINFORCEMENT_BEHEMOTH        = 4024, f"{REINFORCEMENT_AMOUNT} Behemoths",         Reinforcement("Behemoth",         REINFORCEMENT_AMOUNT)

    # -----------------------------------------------------------------------
    # Reinforcements — Useful
    # Strong units or workers that provide meaningful advantage.
    # -----------------------------------------------------------------------
    REINFORCEMENT_FIRE_GIANT      = 4012, f"{REINFORCEMENT_AMOUNT} Fire Giants",       ReinforcementUseful("FireGiant",         REINFORCEMENT_AMOUNT)
    REINFORCEMENT_CITIZEN         = 4014, f"{REINFORCEMENT_AMOUNT} Citizens",          Reinforcement("VillagerAtlantean", REINFORCEMENT_AMOUNT)
    REINFORCEMENT_ROC             = 4017, f"{REINFORCEMENT_AMOUNT} Rocs",              ReinforcementUseful("Roc",               REINFORCEMENT_AMOUNT)
    REINFORCEMENT_PRIEST          = 4018, f"{REINFORCEMENT_AMOUNT} Priests",           Reinforcement("Priest",            REINFORCEMENT_AMOUNT)
    REINFORCEMENT_CALADRIA        = 4019, f"{REINFORCEMENT_AMOUNT} Caladrias",         Reinforcement("Caladria",          REINFORCEMENT_AMOUNT)
    REINFORCEMENT_LAMPADES        = 4025, f"{REINFORCEMENT_AMOUNT} Lampades",          ReinforcementUseful("Lampades",          REINFORCEMENT_AMOUNT)
    REINFORCEMENT_PHOENIX         = 4026, f"{REINFORCEMENT_AMOUNT} Phoenixes",         ReinforcementUseful("Phoenix",           REINFORCEMENT_AMOUNT)
    REINFORCEMENT_COLOSSUS        = 4027, f"{REINFORCEMENT_AMOUNT} Colossi",           ReinforcementUseful("Colossus",          REINFORCEMENT_AMOUNT)

    # Special: spawns exactly 1 Reginleif (not REINFORCEMENT_AMOUNT)
    REGINLEIF_JOINS               = 4028, "Reginleif Joins the Campaign",              ReinforcementUseful("Reginleif", 1)
    ODYSSEUS_JOINS                = 5015, "Odysseus Joins the Campaign",               ReinforcementUseful("OdysseusSPC", 1)
    KASTOR_JOINS                  = 4035, "Kastor Joins the Campaign",                 ReinforcementUseful("Kastor", 1)

    # Myth unit tier unlocks — forbidden at start, unlocked by item
    GREEK_CLASSICAL_MYTH_UNITS               = 5016, "Can train Greek Classical Myth Units", MythUnitUnlockProgression(['Centaur', 'Minotaur', 'Cyclops', 'Lykaon'], "Greek", "Classical")
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

    # -----------------------------------------------------------------------
    # Reinforcements — Additional Filler
    # Added to cover pool shortfall when hero abilities or age unlocks are
    # removed from the pool via player options.
    # -----------------------------------------------------------------------
    REINFORCEMENT_RELIC_MONKEY    = 4029, f"{REINFORCEMENT_AMOUNT} Relic Monkeys",     Reinforcement("RelicMonkey",    REINFORCEMENT_AMOUNT)
    REINFORCEMENT_PEGASUS         = 4030, f"{REINFORCEMENT_AMOUNT} Pegasi",            Reinforcement("Pegasus",        REINFORCEMENT_AMOUNT)
    REINFORCEMENT_HYENA           = 4031, f"{REINFORCEMENT_AMOUNT} Hyenas of Set",     Reinforcement("Hyena",          REINFORCEMENT_AMOUNT)
    REINFORCEMENT_HIPPO           = 4032, f"{REINFORCEMENT_AMOUNT} Hippos of Set",     Reinforcement("Hippopotamus",   REINFORCEMENT_AMOUNT)
    REINFORCEMENT_GOLDEN_LION     = 4033, f"{REINFORCEMENT_AMOUNT} Golden Lions",      Reinforcement("GoldenLion",     REINFORCEMENT_AMOUNT)
    REINFORCEMENT_NORSE_GATHERER  = 4034, f"{REINFORCEMENT_AMOUNT} Norse Gatherers",   Reinforcement("VillagerNorse",  REINFORCEMENT_AMOUNT)

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

    # -----------------------------------------------------------------------
    # Generic Villager Food Cost Reduction — ID 5009
    # Reduces the food cost to train ALL villager types by 5.
    # Applied via trModifyProtounitResource (cXSPUResourceEffectCost=0).
    # Generic — not civ-specific; always in pool regardless of enabled civs.
    # -----------------------------------------------------------------------
    VILLAGER_DISCOUNT = 5009, "Villagers Cost -5 Food", GenericVillagerDiscount(5)


# -----------------------------------------------------------------------
# Lookup tables
# -----------------------------------------------------------------------

NAME_TO_ITEM: dict[str, aomItemData] = {}
ID_TO_ITEM: dict[int, aomItemData] = {}
CATEGORY_TO_ITEMS: dict[type, list[aomItemData]] = {}
filler_items: list[aomItemData] = []
item_id_to_name: dict[int, str] = {}
item_name_to_id: dict[str, int] = {}

for item in aomItemData:
    assert item.item_name not in item_name_to_id, f"Duplicate item name: {item.item_name}"
    assert item.id not in item_id_to_name, f"Duplicate item ID: {item.id}"

    NAME_TO_ITEM[item.item_name] = item
    ID_TO_ITEM[item.id] = item

    if item_type_to_classification[item.type_data] == ItemClassification.filler:
        filler_items.append(item)

    item_id_to_name[item.id] = item.item_name
    item_name_to_id[item.item_name] = item.id
    CATEGORY_TO_ITEMS.setdefault(item.type_data, []).append(item)