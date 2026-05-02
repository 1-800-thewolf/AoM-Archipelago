// archipelago.xs
// Archipelago Multiworld integration script for Age of Mythology: Retold
// aom_state.xs is included near the top so all globals are declared first.
// Do not include this directly. Use ap_init.xs instead.
// In each gameplay scenario, add ONE XS Code Snippet effect near mission start:
//   trQuestVarSet("APScenarioID", <scenario_number>);
//   xsEnableRule("APActivateScenario");

// extern globals — visible across all XS source files including aom_state.xs
extern int gAPItemCount = 0;
// Pre-determined random god powers for the current scenario, populated by
// APInitGodPowers() in aom_state.xs from slot_data on every scenario load.
extern string gAPRandGP1 = "";
extern string gAPRandGP2 = "";
extern string gAPRandGP3 = "";
extern string gAPRandGP4 = "";
extern int[] gAPItems = default;

// Shop globals — declared before include so aom_state.xs (APShopStateInit) can reference them
extern int    gAPShopAvailableGems        = 0;
extern int    gAPShopTierThreshold        = 4;
extern bool   gAPShopPurchased_A_ITEM_1        = false;
extern bool   gAPShopPurchased_A_ITEM_2        = false;
extern bool   gAPShopPurchased_A_ITEM_3        = false;
extern bool   gAPShopPurchased_A_ITEM_4        = false;
extern bool   gAPShopPurchased_A_ITEM_5        = false;
extern bool   gAPShopPurchased_B_ITEM_1       = false;
extern bool   gAPShopPurchased_B_ITEM_2       = false;
extern bool   gAPShopPurchased_B_ITEM_3       = false;
extern bool   gAPShopPurchased_B_ITEM_4       = false;
extern bool   gAPShopPurchased_C_ITEM_1        = false;
extern bool   gAPShopPurchased_C_ITEM_2        = false;
extern bool   gAPShopPurchased_C_ITEM_3        = false;
extern bool   gAPShopPurchased_D_ITEM_1        = false;
extern bool   gAPShopPurchased_D_ITEM_2        = false;
extern bool   gAPShopPurchased_A_HINT_1        = false;
extern bool   gAPShopPurchased_A_HINT_2        = false;
extern bool   gAPShopPurchased_A_HINT_3        = false;
extern bool   gAPShopPurchased_A_HINT_4        = false;
extern bool   gAPShopPurchased_B_HINT_1       = false;
extern bool   gAPShopPurchased_B_HINT_2       = false;
extern bool   gAPShopPurchased_B_HINT_3       = false;
extern bool   gAPShopPurchased_C_HINT_1        = false;
extern bool   gAPShopPurchased_C_HINT_2        = false;
extern bool   gAPShopPurchased_D_HINT_1        = false;
extern string gAPShopLabel_A_ITEM_1            = "Loading...";
extern string gAPShopLabel_A_ITEM_2            = "Loading...";
extern string gAPShopLabel_A_ITEM_3            = "Loading...";
extern string gAPShopLabel_A_ITEM_4            = "Loading...";
extern string gAPShopLabel_A_ITEM_5            = "Loading...";
extern string gAPShopLabel_B_ITEM_1           = "Loading...";
extern string gAPShopLabel_B_ITEM_2           = "Loading...";
extern string gAPShopLabel_B_ITEM_3           = "Loading...";
extern string gAPShopLabel_B_ITEM_4           = "Loading...";
extern string gAPShopLabel_C_ITEM_1            = "Loading...";
extern string gAPShopLabel_C_ITEM_2            = "Loading...";
extern string gAPShopLabel_C_ITEM_3            = "Loading...";
extern string gAPShopLabel_D_ITEM_1            = "Loading...";
extern string gAPShopLabel_D_ITEM_2            = "Loading...";
extern string gAPShopLabel_A_HINT_1            = "Loading...";
extern string gAPShopLabel_A_HINT_2            = "Loading...";
extern string gAPShopLabel_A_HINT_3            = "Loading...";
extern string gAPShopLabel_A_HINT_4            = "Loading...";
extern string gAPShopLabel_B_HINT_1           = "Loading...";
extern string gAPShopLabel_B_HINT_2           = "Loading...";
extern string gAPShopLabel_B_HINT_3           = "Loading...";
extern string gAPShopLabel_C_HINT_1            = "Loading...";
extern string gAPShopLabel_C_HINT_2            = "Loading...";
extern string gAPShopLabel_D_HINT_1            = "Loading...";

// Trap queue globals — declared before include so aom_state.xs can set them
extern int   gAPTrapQueueSize   = 0;
extern int[] gAPTrapQueue       = default;
extern bool  gAPTrapPending     = false;
extern float gAPTrapFireTime    = 0.0;

// Relic-trickle running totals — per resource, current applied trickle delta.
// Used by APRelicTrickleEnforce to compute deltas without double-applying.
extern float gAPRelicTrickleAppliedFood  = 0.0;
extern float gAPRelicTrickleAppliedWood  = 0.0;
extern float gAPRelicTrickleAppliedGold  = 0.0;
extern float gAPRelicTrickleAppliedFavor = 0.0;

// Relic-effect "applied count" trackers — number of relic stacks of each
// effect already applied to player 1. Each tick we re-count owned relics and
// apply (target - applied) more invocations of the underlying tr* call.
extern int gAPRelicEffAppliedLOS        = 0;
extern int gAPRelicEffAppliedRegen      = 0;
extern int gAPRelicEffAppliedSpeed      = 0;
extern int gAPRelicEffAppliedHP         = 0;
extern int gAPRelicEffAppliedPop        = 0;
extern int gAPRelicEffAppliedGoldCost   = 0;
extern int gAPRelicEffAppliedWoodCost   = 0;
extern int gAPRelicEffAppliedFavorCost  = 0;
extern int gAPRelicEffAppliedFoodCost   = 0;
extern int gAPRelicEffAppliedBuildSpeed = 0;
extern int gAPRelicLastCount           = -1;
int          gAPTrapsFiredCount  = 0;  // increments each fire; client reads via quest var
vector       gAPTrapPos         = vector(0, 0, 0);
// Building transform data — populated by APLoadBuildingTransforms() in aom_state.xs

include "aom_state.xs";

// -----------------------------------------------------------------------
// Item ID constants — raw IDs matching Items.py (no BASE_ID offset)
// -----------------------------------------------------------------------

const int cSTARTING_WOOD_SMALL           = 1;
const int cSTARTING_FOOD_SMALL           = 2;
const int cSTARTING_GOLD_SMALL           = 3;
const int cSTARTING_FAVOR_SMALL          = 4;
const int cSTARTING_WOOD_MEDIUM          = 5;
const int cSTARTING_FOOD_MEDIUM          = 6;
const int cSTARTING_GOLD_MEDIUM          = 7;
const int cSTARTING_FAVOR_MEDIUM         = 8;
const int cSTARTING_WOOD_LARGE           = 9;
const int cSTARTING_FOOD_LARGE           = 10;
const int cSTARTING_GOLD_LARGE           = 11;
const int cSTARTING_FAVOR_LARGE          = 12;

const int cPASSIVE_WOOD_SMALL            = 13;
const int cPASSIVE_FOOD_SMALL            = 14;
const int cPASSIVE_GOLD_SMALL            = 15;
const int cPASSIVE_FAVOR_SMALL           = 16;

const int cPASSIVE_WOOD_LARGE            = 21;
const int cPASSIVE_FOOD_LARGE            = 22;
const int cPASSIVE_GOLD_LARGE            = 23;
const int cPASSIVE_FAVOR_LARGE           = 24;

// Relic Trickle item IDs — useful (per-owned-relic resource trickle)
const int cRELIC_TRICKLE_FOOD            = 25;
const int cRELIC_TRICKLE_WOOD            = 26;
const int cRELIC_TRICKLE_GOLD            = 27;
const int cRELIC_TRICKLE_FAVOR           = 28;

// Relic Effect item IDs — useful (per-owned-relic stat / cost / build modifiers)
const int cRELIC_EFFECT_LOS              = 29;
const int cRELIC_EFFECT_REGEN            = 30;
const int cRELIC_EFFECT_SPEED            = 31;
const int cRELIC_EFFECT_HP               = 32;
const int cRELIC_EFFECT_POP              = 33;
const int cRELIC_EFFECT_GOLD_COST        = 34;
const int cRELIC_EFFECT_WOOD_COST        = 35;
const int cRELIC_EFFECT_FAVOR_COST       = 36;
const int cRELIC_EFFECT_FOOD_COST        = 37;
const int cRELIC_EFFECT_BUILD_SPEED      = 38;

// Reinforcement item IDs — filler
const int cREINFORCEMENT_ANUBITES        = 4000;
const int cREINFORCEMENT_HOPLITE         = 4001;
const int cREINFORCEMENT_DWARF           = 4002;
const int cREINFORCEMENT_MERCENARY       = 4003;
const int cREINFORCEMENT_MERCENARY_CAV   = 4004;
const int cREINFORCEMENT_AUTOMATON       = 4006;
const int cREINFORCEMENT_WADJET          = 4007;
const int cREINFORCEMENT_BERSERK         = 4008;
const int cREINFORCEMENT_SLINGER         = 4009;
const int cREINFORCEMENT_TURMA           = 4010;
const int cREINFORCEMENT_KATASKOPOS      = 4011;
// Reinforcement item IDs — useful
const int cREINFORCEMENT_FIRE_GIANT      = 4012;
const int cREINFORCEMENT_VILLAGER        = 4013;
const int cREINFORCEMENT_CITIZEN         = 4014;
const int cREINFORCEMENT_BATTLE_BOAR     = 4015;
const int cREINFORCEMENT_ROC             = 4017;
const int cREINFORCEMENT_PRIEST          = 4018;
const int cREINFORCEMENT_CALADRIA        = 4019;
const int cREINFORCEMENT_RAIDING_CAVALRY = 4020;
const int cREINFORCEMENT_ORACLE          = 4021;
const int cREINFORCEMENT_CYCLOPS         = 4022;
const int cREINFORCEMENT_TROLL           = 4023;
const int cREINFORCEMENT_BEHEMOTH        = 4024;
const int cREINFORCEMENT_LAMPADES        = 4025;
const int cREINFORCEMENT_PHOENIX         = 4026;
const int cREINFORCEMENT_COLOSSUS        = 4027;
const int cREGINLEIF_JOINS               = 4028;
const int cODYSSEUS_JOINS                = 5015;
const int cKASTOR_JOINS                  = 4035;

// Kastor stat items
const int cKASTOR_HP_25             = 3400;
const int cKASTOR_HP_200            = 3402;
const int cKASTOR_ATK_1             = 3403;
const int cKASTOR_ATK_10            = 3405;
const int cKASTOR_RECHARGE_1        = 3406;
const int cKASTOR_RECHARGE_3_5      = 3407;
const int cKASTOR_REGEN_1           = 3408;
const int cKASTOR_REGEN_5           = 3409;
const int cKASTOR_UNDERMINE_ATTACKS = 3300;
const int cKASTOR_SUMMON_SOLDIERS   = 3301;
const int cKASTOR_IS_A_MANOR        = 3302;
const int cREINFORCEMENT_RELIC_MONKEY    = 4029;
const int cREINFORCEMENT_PEGASUS         = 4030;
const int cREINFORCEMENT_HYENA           = 4031;
const int cREINFORCEMENT_HIPPO           = 4032;
const int cREINFORCEMENT_GOLDEN_LION     = 4033;
const int cREINFORCEMENT_NORSE_GATHERER  = 4034;

// cXSPUResourceEffectCost=0, cXSPUResourceEffectCarryCapacity=1
const int cGREEK_CARRY_FOOD              = 5000;
const int cGREEK_CARRY_WOOD              = 5001;
const int cGREEK_CARRY_GOLD              = 5002;
const int cEGYPTIAN_CARRY_FOOD           = 5003;
const int cEGYPTIAN_CARRY_WOOD           = 5004;
const int cEGYPTIAN_CARRY_GOLD           = 5005;
const int cNORSE_CARRY_FOOD              = 5006;
const int cNORSE_CARRY_WOOD              = 5007;
const int cNORSE_CARRY_GOLD              = 5008;
const int cVILLAGER_DISCOUNT             = 5009;  // generic: -5 food cost for all villager types
// Atlantean unit unlock item IDs (only active when godsanity is enabled)
const int cCAN_TRAIN_MURMILLO       = 3240;
const int cCAN_TRAIN_KATAPELTES     = 3241;
const int cCAN_TRAIN_TURMA          = 3242;
const int cCAN_TRAIN_CHEIROBALLISTA = 3243;
const int cCAN_TRAIN_CONTARIUS      = 3244;
const int cCAN_TRAIN_ARCUS          = 3245;
const int cCAN_TRAIN_FANATIC        = 3246;
const int cCAN_TRAIN_DESTROYER      = 3247;


const int cATLANTEAN_CLASSICAL_MYTH_UNITS = 5025;
const int cATLANTEAN_HEROIC_MYTH_UNITS    = 5026;
const int cATLANTEAN_MYTHIC_MYTH_UNITS    = 5027;

// Myth unit tier unlock item IDs
const int cGREEK_CLASSICAL_MYTH_UNITS                      = 5016;
const int cGREEK_HEROIC_MYTH_UNITS                         = 5017;
const int cGREEK_MYTHIC_MYTH_UNITS                         = 5018;
const int cEGYPTIAN_CLASSICAL_MYTH_UNITS                   = 5019;
const int cEGYPTIAN_HEROIC_MYTH_UNITS                      = 5020;
const int cEGYPTIAN_MYTHIC_MYTH_UNITS                      = 5021;
const int cNORSE_CLASSICAL_MYTH_UNITS                      = 5022;
const int cNORSE_HEROIC_MYTH_UNITS                         = 5023;
const int cNORSE_MYTHIC_MYTH_UNITS                         = 5024;

const int cGREEK_SCENARIOS               = 3500;  // "Unlock FotT Greek Campaign"
const int cEGYPTIAN_SCENARIOS            = 3501;  // "Unlock FotT Egyptian Campaign"
const int cNORSE_SCENARIOS               = 3502;  // "Unlock FotT Norse Campaign"
const int cNEW_ATLANTIS_SCENARIOS        = 3503;  // "Unlock New Atlantis Campaign"
const int cGOLDEN_GIFT_SCENARIOS         = 3504;  // "Unlock The Golden Gift Campaign"
// cFINAL_SCENARIOS removed (stale) -- Final section uses ATLANTIS_KEY (3510) as unlock signal
const int cATLANTIS_KEY                  = 3510;

// Age unlock item IDs — raw values matching Items.py
const int cGREEK_AGE_UNLOCK              = 1002;
const int cEGYPTIAN_AGE_UNLOCK           = 1005;
const int cNORSE_AGE_UNLOCK              = 1008;
const int cATLANTEAN_AGE_UNLOCK          = 1011;

// Progressive tech upgrade item IDs — raw values matching Items.py
const int cSTARTING_ECONOMY_TECH         = 5100;
const int cSTARTING_MILITARY_TECH        = 5101;
const int cSTARTING_DOCK_TECH            = 5102;
const int cSTARTING_BUILDINGS_TECH       = 5103;


// -----------------------------------------------------------------------
// Unit unlock item IDs — raw values matching Items.py
// -----------------------------------------------------------------------

// Progression
const int cCAN_TRAIN_HOPLITE          = 3200;
const int cCAN_TRAIN_SPEARMAN         = 3201;
const int cCAN_TRAIN_BERSERK          = 3202;
const int cCAN_TRAIN_HIRDMAN          = 3203;
// Greek useful
const int cCAN_TRAIN_HYPASPIST        = 3210;
const int cCAN_TRAIN_PELTAST          = 3212;
const int cCAN_TRAIN_HIPPEUS          = 3213;
const int cCAN_TRAIN_TOXOTES          = 3214;
const int cCAN_TRAIN_PRODROMOS        = 3215;
// Egyptian useful
const int cCAN_TRAIN_AXEMAN           = 3220;
const int cCAN_TRAIN_SLINGER          = 3221;
const int cCAN_TRAIN_CHARIOT_ARCHER   = 3222;
const int cCAN_TRAIN_CAMEL_RIDER      = 3223;
const int cCAN_TRAIN_WAR_ELEPHANT     = 3224;
// Norse useful
const int cCAN_TRAIN_THROWING_AXEMAN  = 3230;
const int cCAN_TRAIN_HUSKARL          = 3231;
const int cCAN_TRAIN_RAIDING_CAVALRY  = 3232;
const int cCAN_TRAIN_JARL             = 3233;

// -----------------------------------------------------------------------
// Hero stat item IDs — raw values matching Items.py
// Stat boosts: IDs 2000-2599, Special effects: IDs 2600-3199
// -----------------------------------------------------------------------

// MythTRConstants values used below:
// cXSProtoEffectHitpoints = 0, cXSProtoEffectRechargeTime = 9, cXSProtoEffectUnitRegenRate = 17
// cXSActionEffectDamageHack = 13, cXSActionEffectDamagePierce = 14, cXSActionEffectROF = 4
// cXSRelativityAbsolute = 0, cXSRelativityAssign = 1
// cOnHitEffectStun=0, cOnHitEffectStatModify=1, cOnHitEffectSnare=2, cOnHitEffectDamageOverTime=3
// cOnHitEffectLifesteal=4, cOnHitEffectReincarnation=5, cOnHitEffectThrow=6, cOnHitEffectProgFreezeROF=18
// cModifyTypeROF=11, cModifyTypeMaxHP=1, cModifyTypeVisualScale=49, cModifyTypeSpeed=0

// Arkantos stat items
const int cARKANTOS_HP_25       = 2000;
const int cARKANTOS_HP_100      = 2001;
const int cARKANTOS_HP_200      = 2002;
const int cARKANTOS_ATK_1       = 2003;
const int cARKANTOS_ATK_3       = 2004;
const int cARKANTOS_ATK_10      = 2005;
const int cARKANTOS_RECHARGE_2       = 2006;
const int cARKANTOS_RECHARGE_5       = 2007;
const int cARKANTOS_REGEN_1     = 2008;
const int cARKANTOS_REGEN_5     = 2009;

// Ajax stat items
const int cAJAX_HP_25           = 2100;
const int cAJAX_HP_100          = 2101;
const int cAJAX_HP_200          = 2102;
const int cAJAX_ATK_1           = 2103;
const int cAJAX_ATK_3           = 2104;
const int cAJAX_ATK_10          = 2105;
const int cAJAX_RECHARGE_2           = 2106;
const int cAJAX_RECHARGE_5           = 2107;
const int cAJAX_REGEN_1         = 2108;
const int cAJAX_REGEN_5         = 2109;

// Chiron stat items
const int cCHIRON_HP_25         = 2200;
const int cCHIRON_HP_100        = 2201;
const int cCHIRON_HP_200        = 2202;
const int cCHIRON_ATK_1         = 2203;
const int cCHIRON_ATK_3         = 2204;
const int cCHIRON_ATK_10        = 2205;
const int cCHIRON_RECHARGE_2         = 2206;
const int cCHIRON_RECHARGE_5         = 2207;
const int cCHIRON_REGEN_1       = 2208;
const int cCHIRON_REGEN_5       = 2209;

// Amanra stat items
const int cAMANRA_HP_25         = 2300;
const int cAMANRA_HP_100        = 2301;
const int cAMANRA_HP_200        = 2302;
const int cAMANRA_ATK_1         = 2303;
const int cAMANRA_ATK_3         = 2304;
const int cAMANRA_ATK_10        = 2305;
const int cAMANRA_RECHARGE_2         = 2306;
const int cAMANRA_RECHARGE_5         = 2307;
const int cAMANRA_REGEN_1       = 2308;
const int cAMANRA_REGEN_5       = 2309;

// Odysseus stat items
const int cODYSSEUS_HP_25       = 2400;
const int cODYSSEUS_HP_100      = 2401;
const int cODYSSEUS_HP_200      = 2402;
const int cODYSSEUS_ATK_1       = 2403;
const int cODYSSEUS_ATK_3       = 2404;
const int cODYSSEUS_ATK_10      = 2405;
const int cODYSSEUS_RECHARGE_2       = 2406;
const int cODYSSEUS_RECHARGE_5       = 2407;
const int cODYSSEUS_REGEN_1     = 2408;
const int cODYSSEUS_REGEN_5     = 2409;

// Reginleif stat items
const int cREGINLEIF_HP_25      = 2500;
const int cREGINLEIF_HP_100     = 2501;
const int cREGINLEIF_HP_200     = 2502;
const int cREGINLEIF_ATK_1      = 2503;
const int cREGINLEIF_ATK_3      = 2504;
const int cREGINLEIF_ATK_10     = 2505;
const int cREGINLEIF_REGEN_1    = 2508;
const int cREGINLEIF_REGEN_5    = 2509;

// Special effect items
const int cARKANTOS_LIFESTEAL        = 2600;
const int cARKANTOS_PETRIFYING_SHOUT  = 2601;
const int cARKANTOS_HOUSING            = 2602;
const int cARKANTOS_ATTACK_SPEED      = 2603;

const int cAJAX_SHIELD_BASH_AOE       = 2702;

const int cCHIRON_SHOTGUN_SPECIAL     = 2802;

const int cAMANRA_DIVINE_SMITE        = 2902;

const int cODYSSEUS_PERFECT_ACCURACY  = 3002;
const int cAJAX_STUNNING_BLOW        = 2700;
const int cAJAX_SMITING_STRIKES      = 2701;
const int cCHIRON_POISON_ARROW       = 2800;
const int cCHIRON_CRIPPLING_FIRE     = 2801;
const int cAMANRA_SHOCKWAVE_JUMP     = 2900;
const int cAMANRA_ARMY_OF_THE_DEAD   = 2901;
const int cODYSSEUS_ENTANGLING_SHOT  = 3000;
const int cODYSSEUS_SWIFT_ESCAPE     = 3001;
const int cREGINLEIF_FROST_STRIKE    = 3100;
const int cREGINLEIF_PROJECTILE    = 2510;

// Reinforcement spawn unit ID — set per-scenario via trQuestVarSet("ReinforcementSpawnID", <unit_id>)

// -----------------------------------------------------------------------
// Arkantos unit ID — resolved dynamically so it works across all scenarios
// -----------------------------------------------------------------------

int gReinforcementSpawnID = -1;

void APFindReinforcementSpawn()
{
    // Arkantos ID is set per-scenario via a game-start trigger:
    //   trQuestVarSet("ReinforcementSpawnID", <unit_id>);
    // Look up Arkantos's unit ID in the editor by clicking on him.
    gReinforcementSpawnID = trQuestVarGet("ReinforcementSpawnID");
}

// -----------------------------------------------------------------------
// Campaign ID and passive income accumulators
// -----------------------------------------------------------------------


int gAPScenarioId  = 0;
int gAPCampaignId  = 0;
int gAPMajorGod    = 0;
bool gAPRandomMajorGods  = false;
bool gHasGreek     = false;
bool gHasEgyptian  = false;
bool gHasNorse     = false;
bool gHasAtlantis  = false;
bool gHasNewAtlantis = false;
bool gHasGoldenGift  = false;

const int cAPMajorNone      = 0;
const int cAPMajorZeus      = 1;
const int cAPMajorPoseidon  = 2;
const int cAPMajorHades     = 3;
const int cAPMajorIsis      = 4;
const int cAPMajorRa        = 5;
const int cAPMajorSet       = 6;
const int cAPMajorOdin      = 7;
const int cAPMajorThor      = 8;
const int cAPMajorLoki      = 9;
const int cAPMajorKronos    = 10;
const int cAPMajorOranos    = 11;
const int cAPMajorGaia      = 12;


// -----------------------------------------------------------------------
// Scenario activation helpers
// -----------------------------------------------------------------------

int APGetCampaignForScenario(int scenarioId = 0)
{
    if (scenarioId >= 1 && scenarioId <= 10) { return 1; }
    if (scenarioId >= 11 && scenarioId <= 20) { return 2; }
    if (scenarioId >= 21 && scenarioId <= 30) { return 3; }
    if (scenarioId >= 31 && scenarioId <= 32) { return 4; }
    if (scenarioId >= 501 && scenarioId <= 512) { return 5; }  // New Atlantis
    if (scenarioId >= 601 && scenarioId <= 604) { return 6; }  // The Golden Gift
    return 0;
}

int APGetMajorGodForScenario(int scenarioId = 0)
{
    if (scenarioId == 1)  { return cAPMajorPoseidon; }
    if (scenarioId == 2)  { return cAPMajorPoseidon; }
    if (scenarioId == 3)  { return cAPMajorPoseidon; }
    if (scenarioId == 4)  { return cAPMajorPoseidon; }
    if (scenarioId == 5)  { return cAPMajorZeus; }
    if (scenarioId == 6)  { return cAPMajorZeus; }
    if (scenarioId == 7)  { return cAPMajorZeus; }
    if (scenarioId == 8)  { return cAPMajorZeus; }
    if (scenarioId == 9)  { return cAPMajorZeus; }
    if (scenarioId == 10) { return cAPMajorZeus; }

    if (scenarioId == 11) { return cAPMajorIsis; }
    if (scenarioId == 12) { return cAPMajorRa; }
    if (scenarioId == 13) { return cAPMajorSet; }
    if (scenarioId == 14) { return cAPMajorIsis; }
    if (scenarioId == 15) { return cAPMajorIsis; }
    if (scenarioId == 16) { return cAPMajorHades; }
    if (scenarioId == 17) { return cAPMajorRa; }
    if (scenarioId == 18) { return cAPMajorRa; }
    if (scenarioId == 19) { return cAPMajorIsis; }
    if (scenarioId == 20) { return cAPMajorIsis; }

    if (scenarioId == 21) { return cAPMajorZeus; }
    if (scenarioId == 22) { return cAPMajorThor; }
    if (scenarioId == 23) { return cAPMajorThor; }
    if (scenarioId == 24) { return cAPMajorLoki; }
    if (scenarioId == 25) { return cAPMajorLoki; }
    if (scenarioId == 26) { return cAPMajorOdin; }
    if (scenarioId == 27) { return cAPMajorOdin; }
    if (scenarioId == 28) { return cAPMajorOdin; }
    if (scenarioId == 29) { return cAPMajorThor; }
    if (scenarioId == 30) { return cAPMajorThor; }

    if (scenarioId == 31) { return cAPMajorZeus; }
    if (scenarioId == 32) { return cAPMajorZeus; }

    // New Atlantis (501-512)
    if (scenarioId == 501) { return cAPMajorOranos; }
    if (scenarioId == 502) { return cAPMajorKronos; }
    if (scenarioId == 503) { return cAPMajorKronos; }
    if (scenarioId == 504) { return cAPMajorKronos; }
    if (scenarioId == 505) { return cAPMajorKronos; }
    if (scenarioId == 506) { return cAPMajorKronos; }
    if (scenarioId == 507) { return cAPMajorRa;     }
    if (scenarioId == 508) { return cAPMajorSet;    }
    if (scenarioId == 509) { return cAPMajorThor;   }
    if (scenarioId == 510) { return cAPMajorGaia;   }
    if (scenarioId == 511) { return cAPMajorOranos; }
    if (scenarioId == 512) { return cAPMajorGaia;   }

    // The Golden Gift (601-604)
    if (scenarioId == 601) { return cAPMajorThor; }
    if (scenarioId == 602) { return cAPMajorLoki; }
    if (scenarioId == 603) { return cAPMajorLoki; }
    if (scenarioId == 604) { return cAPMajorThor; }

    return cAPMajorNone;
}

void APForceDisableAllGreekAgeTechs()
{
    trTechSetStatus(1, cTechClassicalAgeAthena, 0);  trTechSetStatus(1, cTechClassicalAgeHermes, 0);
    trTechSetStatus(1, cTechClassicalAgeAres, 0);    trTechSetStatus(1, cTechClassicalAgeGreek, 0);
    trTechSetStatus(1, cTechHeroicAgeApollo, 0);     trTechSetStatus(1, cTechHeroicAgeDionysus, 0);
    trTechSetStatus(1, cTechHeroicAgeAphrodite, 0);  trTechSetStatus(1, cTechHeroicAgeGreek, 0);
    trTechSetStatus(1, cTechMythicAgeHera, 0);       trTechSetStatus(1, cTechMythicAgeHephaestus, 0);
    trTechSetStatus(1, cTechMythicAgeArtemis, 0);    trTechSetStatus(1, cTechMythicAgeGreek, 0);
}

void APForceDisableAllEgyptianAgeTechs()
{
    trTechSetStatus(1, cTechClassicalAgeAnubis, 0);  trTechSetStatus(1, cTechClassicalAgeBast, 0);
    trTechSetStatus(1, cTechClassicalAgePtah, 0);    trTechSetStatus(1, cTechClassicalAgeEgyptian, 0);
    trTechSetStatus(1, cTechHeroicAgeSekhmet, 0);    trTechSetStatus(1, cTechHeroicAgeSobek, 0);
    trTechSetStatus(1, cTechHeroicAgeNephthys, 0);   trTechSetStatus(1, cTechHeroicAgeEgyptian, 0);
    trTechSetStatus(1, cTechMythicAgeOsiris, 0);     trTechSetStatus(1, cTechMythicAgeHorus, 0);
    trTechSetStatus(1, cTechMythicAgeThoth, 0);      trTechSetStatus(1, cTechMythicAgeEgyptian, 0);
}

void APForceDisableAllNorseAgeTechs()
{
    trTechSetStatus(1, cTechClassicalAgeFreyja, 0);  trTechSetStatus(1, cTechClassicalAgeForseti, 0);
    trTechSetStatus(1, cTechClassicalAgeHeimdall, 0); trTechSetStatus(1, cTechClassicalAgeUllr, 0);
    trTechSetStatus(1, cTechClassicalAgeNorse, 0);
    trTechSetStatus(1, cTechHeroicAgeBragi, 0);      trTechSetStatus(1, cTechHeroicAgeNjord, 0);
    trTechSetStatus(1, cTechHeroicAgeSkadi, 0);      trTechSetStatus(1, cTechHeroicAgeAegir, 0);
    trTechSetStatus(1, cTechHeroicAgeNorse, 0);
    trTechSetStatus(1, cTechMythicAgeBaldr, 0);      trTechSetStatus(1, cTechMythicAgeTyr, 0);
    trTechSetStatus(1, cTechMythicAgeHel, 0);        trTechSetStatus(1, cTechMythicAgeVidar, 0);
    trTechSetStatus(1, cTechMythicAgeNorse, 0);
}

void APForceDisableAllAtlanteanAgeTechs()
{
    trTechSetStatus(1, cTechClassicalAgePrometheus, 0); trTechSetStatus(1, cTechClassicalAgeLeto, 0);
    trTechSetStatus(1, cTechClassicalAgeOceanus, 0);    trTechSetStatus(1, cTechClassicalAgeAtlantean, 0);
    trTechSetStatus(1, cTechHeroicAgeHyperion, 0);      trTechSetStatus(1, cTechHeroicAgeRheia, 0);
    trTechSetStatus(1, cTechHeroicAgeTheia, 0);         trTechSetStatus(1, cTechHeroicAgeAtlantean, 0);
    trTechSetStatus(1, cTechMythicAgeHelios, 0);         trTechSetStatus(1, cTechMythicAgeAtlas, 0);
    trTechSetStatus(1, cTechMythicAgeHekate, 0);         trTechSetStatus(1, cTechMythicAgeAtlantean, 0);
}

void APSetPlayerCiv()
{
    // Set civ first, then force-disable all age techs for non-assigned civs.
    // Force-disable (no guard) clears any pre-set vanilla scenario age techs.
    // We also force-disable the ASSIGNED civ's own techs because trPlayerSetCiv
    // auto-enables that civ's full age tech tree (status 1). Without this,
    // APDisableAllNorseAgeTechs (etc.) would see them as "active" and skip
    // them, leaving Mythic available even when the player lacks those unlocks.
    if (gAPMajorGod == cAPMajorZeus || gAPMajorGod == cAPMajorPoseidon || gAPMajorGod == cAPMajorHades)
    {
        if (gAPMajorGod == cAPMajorZeus)     { trPlayerSetCiv(1, "Zeus"); }
        if (gAPMajorGod == cAPMajorPoseidon) { trPlayerSetCiv(1, "Poseidon"); }
        if (gAPMajorGod == cAPMajorHades)    { trPlayerSetCiv(1, "Hades"); }
        APForceDisableAllGreekAgeTechs();
        APForceDisableAllEgyptianAgeTechs();
        APForceDisableAllNorseAgeTechs();
        APForceDisableAllAtlanteanAgeTechs();
    }
    if (gAPMajorGod == cAPMajorIsis || gAPMajorGod == cAPMajorRa || gAPMajorGod == cAPMajorSet)
    {
        if (gAPMajorGod == cAPMajorIsis) { trPlayerSetCiv(1, "Isis"); }
        if (gAPMajorGod == cAPMajorRa)   { trPlayerSetCiv(1, "Ra"); }
        if (gAPMajorGod == cAPMajorSet)  { trPlayerSetCiv(1, "Set"); }
        APForceDisableAllGreekAgeTechs();
        APForceDisableAllEgyptianAgeTechs();
        APForceDisableAllNorseAgeTechs();
        APForceDisableAllAtlanteanAgeTechs();
    }
    if (gAPMajorGod == cAPMajorOdin || gAPMajorGod == cAPMajorThor || gAPMajorGod == cAPMajorLoki)
    {
        if (gAPMajorGod == cAPMajorOdin) { trPlayerSetCiv(1, "Odin"); }
        if (gAPMajorGod == cAPMajorThor) { trPlayerSetCiv(1, "Thor"); }
        if (gAPMajorGod == cAPMajorLoki) { trPlayerSetCiv(1, "Loki"); }
        APForceDisableAllGreekAgeTechs();
        APForceDisableAllEgyptianAgeTechs();
        APForceDisableAllNorseAgeTechs();
        APForceDisableAllAtlanteanAgeTechs();
    }
    if (gAPMajorGod == cAPMajorKronos || gAPMajorGod == cAPMajorOranos || gAPMajorGod == cAPMajorGaia)
    {
        if (gAPMajorGod == cAPMajorKronos) { trPlayerSetCiv(1, "Kronos"); }
        if (gAPMajorGod == cAPMajorOranos) { trPlayerSetCiv(1, "Oranos"); }
        if (gAPMajorGod == cAPMajorGaia)   { trPlayerSetCiv(1, "Gaia"); }
        APForceDisableAllGreekAgeTechs();
        APForceDisableAllEgyptianAgeTechs();
        APForceDisableAllNorseAgeTechs();
        APForceDisableAllAtlanteanAgeTechs();
    }
}

void APReadRandomGod()
{
    if (gAPScenarioId == 1) { int g = trQuestVarGet("APGod1"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 2) { int g = trQuestVarGet("APGod2"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 3) { int g = trQuestVarGet("APGod3"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 4) { int g = trQuestVarGet("APGod4"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 5) { int g = trQuestVarGet("APGod5"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 6) { int g = trQuestVarGet("APGod6"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 7) { int g = trQuestVarGet("APGod7"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 8) { int g = trQuestVarGet("APGod8"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 9) { int g = trQuestVarGet("APGod9"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 10) { int g = trQuestVarGet("APGod10"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 11) { int g = trQuestVarGet("APGod11"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 12) { int g = trQuestVarGet("APGod12"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 13) { int g = trQuestVarGet("APGod13"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 14) { int g = trQuestVarGet("APGod14"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 15) { int g = trQuestVarGet("APGod15"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 16) { int g = trQuestVarGet("APGod16"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 17) { int g = trQuestVarGet("APGod17"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 18) { int g = trQuestVarGet("APGod18"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 19) { int g = trQuestVarGet("APGod19"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 20) { int g = trQuestVarGet("APGod20"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 21) { int g = trQuestVarGet("APGod21"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 22) { int g = trQuestVarGet("APGod22"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 23) { int g = trQuestVarGet("APGod23"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 24) { int g = trQuestVarGet("APGod24"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 25) { int g = trQuestVarGet("APGod25"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 26) { int g = trQuestVarGet("APGod26"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 27) { int g = trQuestVarGet("APGod27"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 28) { int g = trQuestVarGet("APGod28"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 29) { int g = trQuestVarGet("APGod29"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 30) { int g = trQuestVarGet("APGod30"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 31) { int g = trQuestVarGet("APGod31"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 32) { int g = trQuestVarGet("APGod32"); if (g > 0) { gAPMajorGod = g; } }
    // New Atlantis (501-512)
    if (gAPScenarioId == 501) { int g = trQuestVarGet("APGod501"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 502) { int g = trQuestVarGet("APGod502"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 503) { int g = trQuestVarGet("APGod503"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 504) { int g = trQuestVarGet("APGod504"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 505) { int g = trQuestVarGet("APGod505"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 506) { int g = trQuestVarGet("APGod506"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 507) { int g = trQuestVarGet("APGod507"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 508) { int g = trQuestVarGet("APGod508"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 509) { int g = trQuestVarGet("APGod509"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 510) { int g = trQuestVarGet("APGod510"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 511) { int g = trQuestVarGet("APGod511"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 512) { int g = trQuestVarGet("APGod512"); if (g > 0) { gAPMajorGod = g; } }
    // The Golden Gift (601-604)
    if (gAPScenarioId == 601) { int g = trQuestVarGet("APGod601"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 602) { int g = trQuestVarGet("APGod602"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 603) { int g = trQuestVarGet("APGod603"); if (g > 0) { gAPMajorGod = g; } }
    if (gAPScenarioId == 604) { int g = trQuestVarGet("APGod604"); if (g > 0) { gAPMajorGod = g; } }
}

// -----------------------------------------------------------------------
// God announcement — called from APApplyItems when godsanity is on.
// -----------------------------------------------------------------------

void APAnnounceGod()
{
    if (gAPRandomMajorGods == false) { return; }

    string godName   = "";
    string colorOpen = "";

    if (gAPMajorGod == cAPMajorZeus)     { godName = "Zeus";     colorOpen = "<color0.3,0.3,1>"; }
    if (gAPMajorGod == cAPMajorPoseidon) { godName = "Poseidon"; colorOpen = "<color0.3,0.3,1>"; }
    if (gAPMajorGod == cAPMajorHades)    { godName = "Hades";    colorOpen = "<color0.3,0.3,1>"; }
    if (gAPMajorGod == cAPMajorIsis)     { godName = "Isis";     colorOpen = "<color1,1,0>"; }
    if (gAPMajorGod == cAPMajorRa)       { godName = "Ra";       colorOpen = "<color1,1,0>"; }
    if (gAPMajorGod == cAPMajorSet)      { godName = "Set";      colorOpen = "<color1,1,0>"; }
    if (gAPMajorGod == cAPMajorOdin)     { godName = "Odin";     colorOpen = "<color0.53,0.31,0.31>"; }
    if (gAPMajorGod == cAPMajorThor)     { godName = "Thor";     colorOpen = "<color0.53,0.31,0.31>"; }
    if (gAPMajorGod == cAPMajorLoki)     { godName = "Loki";     colorOpen = "<color0.53,0.31,0.31>"; }
    if (gAPMajorGod == cAPMajorKronos)   { godName = "Kronos";   colorOpen = "<color0,1,1>"; }
    if (gAPMajorGod == cAPMajorOranos)   { godName = "Oranos";   colorOpen = "<color0,1,1>"; }
    if (gAPMajorGod == cAPMajorGaia)     { godName = "Gaia";     colorOpen = "<color0,1,1>"; }

    if (godName != "")
    {
        trMessageSetText("Major God:\n" + colorOpen + godName + "</color>", 5);
        trSoundPlayFN("ui\\thunder3.wav");
    }
}

// ── Static shop functions (available at trigger-compile time) ───────────
// All shop globals are extern-declared before the include at the top of this file.

int APGetAvailableGems()
{
    return gAPShopAvailableGems;
}

bool APIsSlotPurchased(string slotId = "")
{
    if (slotId == "A_ITEM_1") { return gAPShopPurchased_A_ITEM_1; }
    if (slotId == "A_ITEM_2") { return gAPShopPurchased_A_ITEM_2; }
    if (slotId == "A_ITEM_3") { return gAPShopPurchased_A_ITEM_3; }
    if (slotId == "A_ITEM_4") { return gAPShopPurchased_A_ITEM_4; }
    if (slotId == "A_ITEM_5") { return gAPShopPurchased_A_ITEM_5; }
    if (slotId == "B_ITEM_1") { return gAPShopPurchased_B_ITEM_1; }
    if (slotId == "B_ITEM_2") { return gAPShopPurchased_B_ITEM_2; }
    if (slotId == "B_ITEM_3") { return gAPShopPurchased_B_ITEM_3; }
    if (slotId == "B_ITEM_4") { return gAPShopPurchased_B_ITEM_4; }
    if (slotId == "C_ITEM_1") { return gAPShopPurchased_C_ITEM_1; }
    if (slotId == "C_ITEM_2") { return gAPShopPurchased_C_ITEM_2; }
    if (slotId == "C_ITEM_3") { return gAPShopPurchased_C_ITEM_3; }
    if (slotId == "D_ITEM_1") { return gAPShopPurchased_D_ITEM_1; }
    if (slotId == "D_ITEM_2") { return gAPShopPurchased_D_ITEM_2; }
    if (slotId == "A_HINT_1") { return gAPShopPurchased_A_HINT_1; }
    if (slotId == "A_HINT_2") { return gAPShopPurchased_A_HINT_2; }
    if (slotId == "A_HINT_3") { return gAPShopPurchased_A_HINT_3; }
    if (slotId == "A_HINT_4") { return gAPShopPurchased_A_HINT_4; }
    if (slotId == "B_HINT_1") { return gAPShopPurchased_B_HINT_1; }
    if (slotId == "B_HINT_2") { return gAPShopPurchased_B_HINT_2; }
    if (slotId == "B_HINT_3") { return gAPShopPurchased_B_HINT_3; }
    if (slotId == "C_HINT_1") { return gAPShopPurchased_C_HINT_1; }
    if (slotId == "C_HINT_2") { return gAPShopPurchased_C_HINT_2; }
    if (slotId == "D_HINT_1") { return gAPShopPurchased_D_HINT_1; }
    return false;
}

string APShopGetLabel(string slotId = "")
{
    if (slotId == "A_ITEM_1") { return gAPShopLabel_A_ITEM_1; }
    if (slotId == "A_ITEM_2") { return gAPShopLabel_A_ITEM_2; }
    if (slotId == "A_ITEM_3") { return gAPShopLabel_A_ITEM_3; }
    if (slotId == "A_ITEM_4") { return gAPShopLabel_A_ITEM_4; }
    if (slotId == "A_ITEM_5") { return gAPShopLabel_A_ITEM_5; }
    if (slotId == "B_ITEM_1") { return gAPShopLabel_B_ITEM_1; }
    if (slotId == "B_ITEM_2") { return gAPShopLabel_B_ITEM_2; }
    if (slotId == "B_ITEM_3") { return gAPShopLabel_B_ITEM_3; }
    if (slotId == "B_ITEM_4") { return gAPShopLabel_B_ITEM_4; }
    if (slotId == "C_ITEM_1") { return gAPShopLabel_C_ITEM_1; }
    if (slotId == "C_ITEM_2") { return gAPShopLabel_C_ITEM_2; }
    if (slotId == "C_ITEM_3") { return gAPShopLabel_C_ITEM_3; }
    if (slotId == "D_ITEM_1") { return gAPShopLabel_D_ITEM_1; }
    if (slotId == "D_ITEM_2") { return gAPShopLabel_D_ITEM_2; }
    if (slotId == "A_HINT_1") { return gAPShopLabel_A_HINT_1; }
    if (slotId == "A_HINT_2") { return gAPShopLabel_A_HINT_2; }
    if (slotId == "A_HINT_3") { return gAPShopLabel_A_HINT_3; }
    if (slotId == "A_HINT_4") { return gAPShopLabel_A_HINT_4; }
    if (slotId == "B_HINT_1") { return gAPShopLabel_B_HINT_1; }
    if (slotId == "B_HINT_2") { return gAPShopLabel_B_HINT_2; }
    if (slotId == "B_HINT_3") { return gAPShopLabel_B_HINT_3; }
    if (slotId == "C_HINT_1") { return gAPShopLabel_C_HINT_1; }
    if (slotId == "C_HINT_2") { return gAPShopLabel_C_HINT_2; }
    if (slotId == "D_HINT_1") { return gAPShopLabel_D_HINT_1; }
    return "Unknown Slot";
}

void APShopPurchase(string slotId = "")
{
        if (APIsSlotPurchased(slotId)) { return; }
        if (APGetAvailableGems() < 1)  { return; }

        // Set quest var immediately for kill-on-reload triggers
        if (slotId == "A_ITEM_1") { trQuestVarSet("APPurchased_A_ITEM_1", 1); }
        if (slotId == "A_ITEM_2") { trQuestVarSet("APPurchased_A_ITEM_2", 1); }
        if (slotId == "A_ITEM_3") { trQuestVarSet("APPurchased_A_ITEM_3", 1); }
        if (slotId == "A_ITEM_4") { trQuestVarSet("APPurchased_A_ITEM_4", 1); }
        if (slotId == "A_ITEM_5") { trQuestVarSet("APPurchased_A_ITEM_5", 1); }
        if (slotId == "B_ITEM_1") { trQuestVarSet("APPurchased_B_ITEM_1", 1); }
        if (slotId == "B_ITEM_2") { trQuestVarSet("APPurchased_B_ITEM_2", 1); }
        if (slotId == "B_ITEM_3") { trQuestVarSet("APPurchased_B_ITEM_3", 1); }
        if (slotId == "B_ITEM_4") { trQuestVarSet("APPurchased_B_ITEM_4", 1); }
        if (slotId == "C_ITEM_1") { trQuestVarSet("APPurchased_C_ITEM_1", 1); }
        if (slotId == "C_ITEM_2") { trQuestVarSet("APPurchased_C_ITEM_2", 1); }
        if (slotId == "C_ITEM_3") { trQuestVarSet("APPurchased_C_ITEM_3", 1); }
        if (slotId == "D_ITEM_1") { trQuestVarSet("APPurchased_D_ITEM_1", 1); }
        if (slotId == "D_ITEM_2") { trQuestVarSet("APPurchased_D_ITEM_2", 1); }
        if (slotId == "A_HINT_1") { trQuestVarSet("APPurchased_A_HINT_1", 1); }
        if (slotId == "A_HINT_2") { trQuestVarSet("APPurchased_A_HINT_2", 1); }
        if (slotId == "A_HINT_3") { trQuestVarSet("APPurchased_A_HINT_3", 1); }
        if (slotId == "A_HINT_4") { trQuestVarSet("APPurchased_A_HINT_4", 1); }
        if (slotId == "B_HINT_1") { trQuestVarSet("APPurchased_B_HINT_1", 1); }
        if (slotId == "B_HINT_2") { trQuestVarSet("APPurchased_B_HINT_2", 1); }
        if (slotId == "B_HINT_3") { trQuestVarSet("APPurchased_B_HINT_3", 1); }
        if (slotId == "C_HINT_1") { trQuestVarSet("APPurchased_C_HINT_1", 1); }
        if (slotId == "C_HINT_2") { trQuestVarSet("APPurchased_C_HINT_2", 1); }
        if (slotId == "D_HINT_1") { trQuestVarSet("APPurchased_D_HINT_1", 1); }

        // Single generic signal — slot index read from APShopBuySlot quest var
        trExecuteOnAI(12, "APShopSignal");

        if (slotId == "A_HINT_1") { xsEnableRule("APShopRestartDelay"); }
        if (slotId == "B_HINT_1") { xsEnableRule("APShopRestartDelay"); }
        if (slotId == "C_HINT_1") { xsEnableRule("APShopRestartDelay"); }
        if (slotId == "D_HINT_1") { xsEnableRule("APShopRestartDelay"); }
        trPlayerGrantResources(1, "Gold", -1);
}

void APShopScenarioInit()
{
    APShopStateInit();
    trPlayerGrantResources(1, "Gold", APGetAvailableGems());

    // Kill purchased obelisks on reload
    if (gAPShopPurchased_A_ITEM_1) { trUnitSelectByID(trQuestVarGet("APOb_A_ITEM_1")); trUnitDestroy(false); }
    if (gAPShopPurchased_A_ITEM_2) { trUnitSelectByID(trQuestVarGet("APOb_A_ITEM_2")); trUnitDestroy(false); }
    if (gAPShopPurchased_A_ITEM_3) { trUnitSelectByID(trQuestVarGet("APOb_A_ITEM_3")); trUnitDestroy(false); }
    if (gAPShopPurchased_A_ITEM_4) { trUnitSelectByID(trQuestVarGet("APOb_A_ITEM_4")); trUnitDestroy(false); }
    if (gAPShopPurchased_A_ITEM_5) { trUnitSelectByID(trQuestVarGet("APOb_A_ITEM_5")); trUnitDestroy(false); }
    if (gAPShopPurchased_B_ITEM_1) { trUnitSelectByID(trQuestVarGet("APOb_B_ITEM_1")); trUnitDestroy(false); }
    if (gAPShopPurchased_B_ITEM_2) { trUnitSelectByID(trQuestVarGet("APOb_B_ITEM_2")); trUnitDestroy(false); }
    if (gAPShopPurchased_B_ITEM_3) { trUnitSelectByID(trQuestVarGet("APOb_B_ITEM_3")); trUnitDestroy(false); }
    if (gAPShopPurchased_B_ITEM_4) { trUnitSelectByID(trQuestVarGet("APOb_B_ITEM_4")); trUnitDestroy(false); }
    if (gAPShopPurchased_C_ITEM_1) { trUnitSelectByID(trQuestVarGet("APOb_C_ITEM_1")); trUnitDestroy(false); }
    if (gAPShopPurchased_C_ITEM_2) { trUnitSelectByID(trQuestVarGet("APOb_C_ITEM_2")); trUnitDestroy(false); }
    if (gAPShopPurchased_C_ITEM_3) { trUnitSelectByID(trQuestVarGet("APOb_C_ITEM_3")); trUnitDestroy(false); }
    if (gAPShopPurchased_D_ITEM_1) { trUnitSelectByID(trQuestVarGet("APOb_D_ITEM_1")); trUnitDestroy(false); }
    if (gAPShopPurchased_D_ITEM_2) { trUnitSelectByID(trQuestVarGet("APOb_D_ITEM_2")); trUnitDestroy(false); }
    if (gAPShopPurchased_A_HINT_1) { trUnitSelectByID(trQuestVarGet("APOb_A_HINT_1")); trUnitDestroy(false); }
    if (gAPShopPurchased_A_HINT_2) { trUnitSelectByID(trQuestVarGet("APOb_A_HINT_2")); trUnitDestroy(false); }
    if (gAPShopPurchased_A_HINT_3) { trUnitSelectByID(trQuestVarGet("APOb_A_HINT_3")); trUnitDestroy(false); }
    if (gAPShopPurchased_A_HINT_4) { trUnitSelectByID(trQuestVarGet("APOb_A_HINT_4")); trUnitDestroy(false); }
    if (gAPShopPurchased_B_HINT_1) { trUnitSelectByID(trQuestVarGet("APOb_B_HINT_1")); trUnitDestroy(false); }
    if (gAPShopPurchased_B_HINT_2) { trUnitSelectByID(trQuestVarGet("APOb_B_HINT_2")); trUnitDestroy(false); }
    if (gAPShopPurchased_B_HINT_3) { trUnitSelectByID(trQuestVarGet("APOb_B_HINT_3")); trUnitDestroy(false); }
    if (gAPShopPurchased_C_HINT_1) { trUnitSelectByID(trQuestVarGet("APOb_C_HINT_1")); trUnitDestroy(false); }
    if (gAPShopPurchased_C_HINT_2) { trUnitSelectByID(trQuestVarGet("APOb_C_HINT_2")); trUnitDestroy(false); }
    if (gAPShopPurchased_D_HINT_1) { trUnitSelectByID(trQuestVarGet("APOb_D_HINT_1")); trUnitDestroy(false); }

    // Show labels (hide if purchased or tier locked)
    if (gAPShopPurchased_A_ITEM_1 || (false)) { trWorldSpacePromptHide("APLabel_A_ITEM_1"); }
    else { trWorldSpacePrompt("APLabel_A_ITEM_1", trQuestVarGet("APOb_A_ITEM_1"), false, APShopGetLabel("A_ITEM_1"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_A_ITEM_2 || (false)) { trWorldSpacePromptHide("APLabel_A_ITEM_2"); }
    else { trWorldSpacePrompt("APLabel_A_ITEM_2", trQuestVarGet("APOb_A_ITEM_2"), false, APShopGetLabel("A_ITEM_2"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_A_ITEM_3 || (false)) { trWorldSpacePromptHide("APLabel_A_ITEM_3"); }
    else { trWorldSpacePrompt("APLabel_A_ITEM_3", trQuestVarGet("APOb_A_ITEM_3"), false, APShopGetLabel("A_ITEM_3"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_A_ITEM_4 || (false)) { trWorldSpacePromptHide("APLabel_A_ITEM_4"); }
    else { trWorldSpacePrompt("APLabel_A_ITEM_4", trQuestVarGet("APOb_A_ITEM_4"), false, APShopGetLabel("A_ITEM_4"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_A_ITEM_5 || (false)) { trWorldSpacePromptHide("APLabel_A_ITEM_5"); }
    else { trWorldSpacePrompt("APLabel_A_ITEM_5", trQuestVarGet("APOb_A_ITEM_5"), false, APShopGetLabel("A_ITEM_5"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_B_ITEM_1 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 1)) { trWorldSpacePromptHide("APLabel_B_ITEM_1"); }
    else { trWorldSpacePrompt("APLabel_B_ITEM_1", trQuestVarGet("APOb_B_ITEM_1"), false, APShopGetLabel("B_ITEM_1"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_B_ITEM_2 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 1)) { trWorldSpacePromptHide("APLabel_B_ITEM_2"); }
    else { trWorldSpacePrompt("APLabel_B_ITEM_2", trQuestVarGet("APOb_B_ITEM_2"), false, APShopGetLabel("B_ITEM_2"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_B_ITEM_3 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 1)) { trWorldSpacePromptHide("APLabel_B_ITEM_3"); }
    else { trWorldSpacePrompt("APLabel_B_ITEM_3", trQuestVarGet("APOb_B_ITEM_3"), false, APShopGetLabel("B_ITEM_3"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_B_ITEM_4 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 1)) { trWorldSpacePromptHide("APLabel_B_ITEM_4"); }
    else { trWorldSpacePrompt("APLabel_B_ITEM_4", trQuestVarGet("APOb_B_ITEM_4"), false, APShopGetLabel("B_ITEM_4"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_C_ITEM_1 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 2)) { trWorldSpacePromptHide("APLabel_C_ITEM_1"); }
    else { trWorldSpacePrompt("APLabel_C_ITEM_1", trQuestVarGet("APOb_C_ITEM_1"), false, APShopGetLabel("C_ITEM_1"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_C_ITEM_2 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 2)) { trWorldSpacePromptHide("APLabel_C_ITEM_2"); }
    else { trWorldSpacePrompt("APLabel_C_ITEM_2", trQuestVarGet("APOb_C_ITEM_2"), false, APShopGetLabel("C_ITEM_2"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_C_ITEM_3 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 2)) { trWorldSpacePromptHide("APLabel_C_ITEM_3"); }
    else { trWorldSpacePrompt("APLabel_C_ITEM_3", trQuestVarGet("APOb_C_ITEM_3"), false, APShopGetLabel("C_ITEM_3"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_D_ITEM_1 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 3)) { trWorldSpacePromptHide("APLabel_D_ITEM_1"); }
    else { trWorldSpacePrompt("APLabel_D_ITEM_1", trQuestVarGet("APOb_D_ITEM_1"), false, APShopGetLabel("D_ITEM_1"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_D_ITEM_2 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 3)) { trWorldSpacePromptHide("APLabel_D_ITEM_2"); }
    else { trWorldSpacePrompt("APLabel_D_ITEM_2", trQuestVarGet("APOb_D_ITEM_2"), false, APShopGetLabel("D_ITEM_2"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_A_HINT_1 || (false)) { trWorldSpacePromptHide("APLabel_A_HINT_1"); }
    else { trWorldSpacePrompt("APLabel_A_HINT_1", trQuestVarGet("APOb_A_HINT_1"), false, APShopGetLabel("A_HINT_1"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_A_HINT_2 || (false)) { trWorldSpacePromptHide("APLabel_A_HINT_2"); }
    else { trWorldSpacePrompt("APLabel_A_HINT_2", trQuestVarGet("APOb_A_HINT_2"), false, APShopGetLabel("A_HINT_2"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_A_HINT_3 || (false)) { trWorldSpacePromptHide("APLabel_A_HINT_3"); }
    else { trWorldSpacePrompt("APLabel_A_HINT_3", trQuestVarGet("APOb_A_HINT_3"), false, APShopGetLabel("A_HINT_3"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_A_HINT_4 || (false)) { trWorldSpacePromptHide("APLabel_A_HINT_4"); }
    else { trWorldSpacePrompt("APLabel_A_HINT_4", trQuestVarGet("APOb_A_HINT_4"), false, APShopGetLabel("A_HINT_4"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_B_HINT_1 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 1)) { trWorldSpacePromptHide("APLabel_B_HINT_1"); }
    else { trWorldSpacePrompt("APLabel_B_HINT_1", trQuestVarGet("APOb_B_HINT_1"), false, APShopGetLabel("B_HINT_1"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_B_HINT_2 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 1)) { trWorldSpacePromptHide("APLabel_B_HINT_2"); }
    else { trWorldSpacePrompt("APLabel_B_HINT_2", trQuestVarGet("APOb_B_HINT_2"), false, APShopGetLabel("B_HINT_2"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_B_HINT_3 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 1)) { trWorldSpacePromptHide("APLabel_B_HINT_3"); }
    else { trWorldSpacePrompt("APLabel_B_HINT_3", trQuestVarGet("APOb_B_HINT_3"), false, APShopGetLabel("B_HINT_3"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_C_HINT_1 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 2)) { trWorldSpacePromptHide("APLabel_C_HINT_1"); }
    else { trWorldSpacePrompt("APLabel_C_HINT_1", trQuestVarGet("APOb_C_HINT_1"), false, APShopGetLabel("C_HINT_1"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_C_HINT_2 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 2)) { trWorldSpacePromptHide("APLabel_C_HINT_2"); }
    else { trWorldSpacePrompt("APLabel_C_HINT_2", trQuestVarGet("APOb_C_HINT_2"), false, APShopGetLabel("C_HINT_2"), vector(0,0,0), "vfx_top", true); }
    if (gAPShopPurchased_D_HINT_1 || (trQuestVarGet("APBeatenScenarios") < gAPShopTierThreshold * 3)) { trWorldSpacePromptHide("APLabel_D_HINT_1"); }
    else { trWorldSpacePrompt("APLabel_D_HINT_1", trQuestVarGet("APOb_D_HINT_1"), false, APShopGetLabel("D_HINT_1"), vector(0,0,0), "vfx_top", true); }
}

// -----------------------------------------------------------------------
// APShopRestartDelay — fires after Progressive Shop Info purchase to reload
// the shop scenario so labels refresh at the new info level.
// -----------------------------------------------------------------------

rule APShopRestartDelay
minInterval 1
inactive
{
    trRestartScenario();
    xsDisableSelf();
}

// -----------------------------------------------------------------------
// Shop purchase polling rule
// Purchase triggers set APShopBuySlot (slot index) and increment
// APShopBuyNonce. This rule detects the nonce change and dispatches
// to APShopPurchase — same pattern as APProcessQueuedCheck.
// Slot index → slot ID mapping mirrors SHOP_SLOT_ORDER in Locations.py.
// -----------------------------------------------------------------------

int gAPLastShopBuyNonce = 0;

string APShopSlotFromIndex(int idx = 0)
{
    if (idx ==  1) { return "A_ITEM_1"; }
    if (idx ==  2) { return "A_ITEM_2"; }
    if (idx ==  3) { return "A_ITEM_3"; }
    if (idx ==  4) { return "A_ITEM_4"; }
    if (idx ==  5) { return "A_ITEM_5"; }
    if (idx ==  6) { return "B_ITEM_1"; }
    if (idx ==  7) { return "B_ITEM_2"; }
    if (idx ==  8) { return "B_ITEM_3"; }
    if (idx ==  9) { return "B_ITEM_4"; }
    if (idx == 10) { return "C_ITEM_1"; }
    if (idx == 11) { return "C_ITEM_2"; }
    if (idx == 12) { return "C_ITEM_3"; }
    if (idx == 13) { return "D_ITEM_1"; }
    if (idx == 14) { return "D_ITEM_2"; }
    if (idx == 15) { return "A_HINT_1"; }
    if (idx == 16) { return "A_HINT_2"; }
    if (idx == 17) { return "A_HINT_3"; }
    if (idx == 18) { return "A_HINT_4"; }
    if (idx == 19) { return "B_HINT_1"; }
    if (idx == 20) { return "B_HINT_2"; }
    if (idx == 21) { return "B_HINT_3"; }
    if (idx == 22) { return "C_HINT_1"; }
    if (idx == 23) { return "C_HINT_2"; }
    if (idx == 24) { return "D_HINT_1"; }
    return "";
}

rule APProcessShopBuy
highFrequency
inactive
{
    int nonce = trQuestVarGet("APShopBuyNonce");
    if (nonce > gAPLastShopBuyNonce)
    {
        gAPLastShopBuyNonce = nonce;
        int idx     = trQuestVarGet("APShopBuySlot");
        string slotId = APShopSlotFromIndex(idx);
        if (slotId != "") { APShopPurchase(slotId); }
    }
}

// -----------------------------------------------------------------------
// Shop tier unlock polling rule
// Sets quest variable "APShopTier" to 1/2/3/4 as the player beats more
// scenarios. In the shop scenario editor, create triggers with condition:
//   Quest Variable Value  "APShopTier"  >=  2   (for Shop B opening)
//   Quest Variable Value  "APShopTier"  >=  3   (for Shop C opening)
//   Quest Variable Value  "APShopTier"  >=  4   (for Shop D opening)
// Effects on those triggers: remove walls, convert revealers, etc.
// APShopTierThreshold is written by the client into aom_state.xs as a
// generated global from the wins_to_open_shop option.
// -----------------------------------------------------------------------

rule APShopTierCheck
highFrequency
inactive
{
    int beaten = trQuestVarGet("APBeatenScenarios");
    int tier   = 1;
    if (gAPShopTierThreshold <= 0)
    {
        tier = 4;  // wins_to_open_shop = 0 means all shops always open
    }
    else
    {
        if (beaten >= gAPShopTierThreshold * 3) { tier = 4; }
        else if (beaten >= gAPShopTierThreshold * 2) { tier = 3; }
        else if (beaten >= gAPShopTierThreshold) { tier = 2; }
    }
    trQuestVarSet("APShopTier", tier);
}

// -----------------------------------------------------------------------
// Queued location check display helpers
// Trigger snippets should NOT call APCheckLocation() directly from trigtemp.xs.
// Instead, they should set:
//   trQuestVarSet("APQueuedCheckID", <location_id>);
//   trQuestVarSet("APQueuedCheckNonce", 1 + trQuestVarGet("APQueuedCheckNonce"));
//   trExecuteOnAI(12, "APCheck_<location_id>");
// This file polls the quest vars and owns centralized popup formatting.
// -----------------------------------------------------------------------

int gAPLastProcessedCheckNonce = 0;

string APGetCheckText(int id = 0)
{
    if (id == 3876724) { return "Scenario Victory"; }
    if (id == 3876726) { return "Kill the Kraken."; }
    if (id == 3876727) { return "Train reinforcements to defend the harbor."; }
    if (id == 3876824) { return "Scenario Victory"; }
    if (id == 3876826) { return "Advance to the Classical Age."; }
    if (id == 3876827) { return "Gather 400 Food"; }
    if (id == 3876828) { return "Build a House"; }
    if (id == 3876829) { return "Build a Temple"; }
    if (id == 3876830) { return "Destroy the pirate Town Center."; }
    if (id == 3876924) { return "Scenario Victory"; }
    if (id == 3876926) { return "Reach the unclaimed Settlement."; }
    if (id == 3876927) { return "Build a Town Center."; }
    if (id == 3876928) { return "Destroy the Trojan docks."; }
    if (id == 3876929) { return "Destroy the last Trojan dock."; }
    if (id == 3877024) { return "Scenario Victory"; }
    if (id == 3877026) { return "Find and take a Gold Mine from the Trojans."; }
    if (id == 3877027) { return "Destroy the Trojan West Gate."; }
    if (id == 3877124) { return "Scenario Victory"; }
    if (id == 3877126) { return "Defeat the cavalry attacking Ajax."; }
    if (id == 3877127) { return "Reach Ajax's Town Center."; }
    if (id == 3877128) { return "Destroy all buildings in the Trojan forward base."; }
    if (id == 3877224) { return "Scenario Victory"; }
    if (id == 3877226) { return "Accumulate 1000 Wood."; }
    if (id == 3877227) { return "Build the Trojan Horse."; }
    if (id == 3877228) { return "Destroy the Trojan gate."; }
    if (id == 3877229) { return "Destroy the three Fortresses within Troy's walls."; }
    if (id == 3877324) { return "Scenario Victory"; }
    if (id == 3877326) { return "Reach the prison area."; }
    if (id == 3877327) { return "Defeat the bandits guarding the prison."; }
    if (id == 3877328) { return "Destroy the enemy Watch Tower and Barracks."; }
    if (id == 3877329) { return "Destroy the enemy Watch Tower and Temple."; }
    if (id == 3877330) { return "Destroy the Migdol Stronghold."; }
    if (id == 3877424) { return "Scenario Victory"; }
    if (id == 3877426) { return "Fight your way to the mine."; }
    if (id == 3877524) { return "Scenario Victory"; }
    if (id == 3877526) { return "Destroy the ram before it breaks down the Gate."; }
    if (id == 3877624) { return "Scenario Victory"; }
    if (id == 3877626) { return "Seek the Shades."; }
    if (id == 3877627) { return "Scout forward with the Shades."; }
    if (id == 3877628) { return "Kill the Minotaur."; }
    if (id == 3877629) { return "Collect the three relics of Hades."; }
    if (id == 3877630) { return "Bring the three relics to the temple complex."; }
    if (id == 3886724) { return "Scenario Victory"; }
    if (id == 3886726) { return "Dig out the artifact."; }
    if (id == 3886824) { return "Scenario Victory"; }
    if (id == 3886826) { return "Kill the guards watching the Laborers."; }
    if (id == 3886827) { return "Bring at least five Villagers safely to their Town Center."; }
    if (id == 3886828) { return "Bring the Sword Bearer to the Guardian."; }
    if (id == 3886829) { return "Use the Guardian to destroy Kemsyt's army."; }
    if (id == 3886924) { return "Scenario Victory"; }
    if (id == 3886926) { return "Move the Osiris Piece Cart into your city."; }
    if (id == 3887024) { return "Scenario Victory"; }
    if (id == 3887026) { return "Destroy Gargarensis' Migdol Stronghold."; }
    if (id == 3887027) { return "Amanra must reach the Transport Ship."; }
    if (id == 3887028) { return "Bring Amanra to the Abydos harbor."; }
    if (id == 3887029) { return "Break Amanra into the prison."; }
    if (id == 3887124) { return "Scenario Victory"; }
    if (id == 3887126) { return "Survive until Setna's transports arrive from the southwest."; }
    if (id == 3887127) { return "Move your troops to the allied purple town."; }
    if (id == 3887128) { return "Capture the Osiris Piece Cart and move it outside the city's south gate."; }
    if (id == 3887224) { return "Scenario Victory"; }
    if (id == 3887226) { return "Follow Kastor."; }
    if (id == 3887227) { return "Garrison the Relic into the Temple, and defend the Temple."; }
    if (id == 3887228) { return "Defeat the guardians of the Shrine."; }
    if (id == 3887229) { return "Destroy the large boulder."; }
    if (id == 3887230) { return "Transport Arkantos and Kastor to the white flag beach."; }
    if (id == 3887231) { return "Destroy the enemy wonder."; }
    if (id == 3887324) { return "Scenario Victory"; }
    if (id == 3887326) { return "Bring Amanra to the village."; }
    if (id == 3887327) { return "Bring Amanra to the Osiris Piece Box."; }
    if (id == 3887424) { return "Scenario Victory"; }
    if (id == 3887426) { return "Reach the desert nomad camp."; }
    if (id == 3887427) { return "Recover the head of Osiris from the Tamarisk tree."; }
    if (id == 3887524) { return "Scenario Victory"; }
    if (id == 3887526) { return "Destroy the forward base to capture the Black Sails."; }
    if (id == 3887527) { return "Claim a Settlement."; }
    if (id == 3887528) { return "Siege Kamos' base."; }
    if (id == 3887529) { return "Eliminate Kamos' guards and defeat him."; }
    if (id == 3887624) { return "Scenario Victory"; }
    if (id == 3887626) { return "Survive until Arkantos arrives."; }
    if (id == 3887627) { return "Bring all three Osiris pieces to the Obelisk."; }
    if (id == 3896724) { return "Scenario Victory"; }
    if (id == 3896726) { return "Save the pigs from being slaughtered."; }
    if (id == 3896727) { return "Bring the Boars and Pigs past the gates to the Temple of Zeus."; }
    if (id == 3896728) { return "Destroy Circe's Fortress."; }
    if (id == 3896824) { return "Scenario Victory"; }
    if (id == 3896826) { return "Claim a Settlement."; }
    if (id == 3896827) { return "Destroy all three enemy Temples."; }
    if (id == 3896924) { return "Scenario Victory"; }
    if (id == 3896926) { return "Build a Town Center."; }
    if (id == 3896927) { return "Eliminate the Giants and Trolls near the Dwarven Forge."; }
    if (id == 3896928) { return "Defend the Dwarven Forge until the Giants retreat!"; }
    if (id == 3897024) { return "Scenario Victory"; }
    if (id == 3897026) { return "Protect Skult and the Folstag Flag Bearer."; }
    if (id == 3897027) { return "Bring Skult and the Flag Bearer to the far north."; }
    if (id == 3897028) { return "Advance to the Heroic Age."; }
    if (id == 3897029) { return "Break through the boulder wall."; }
    if (id == 3897030) { return "Move Skult and the Flag Bearer to the north end of the pass."; }
    if (id == 3897124) { return "Scenario Victory"; }
    if (id == 3897126) { return "Protect Skult and the Folstag Flag Bearer."; }
    if (id == 3897127) { return "Eliminate all three clan leaders."; }
    if (id == 3897224) { return "Scenario Victory"; }
    if (id == 3897226) { return "Follow the trail to the first Norse clan."; }
    if (id == 3897227) { return "Defeat the Trolls in the mines to the west."; }
    if (id == 3897228) { return "Exit the mines and find two more Norse clans."; }
    if (id == 3897229) { return "Build five towers near the flagged sites around Lothbrok's village."; }
    if (id == 3897230) { return "Destroy the Southern Watch Tower."; }
    if (id == 3897324) { return "Scenario Victory"; }
    if (id == 3897326) { return "Destroy the gate to the Well of Urd."; }
    if (id == 3897327) { return "Defeat all myth units at the Well of Urd."; }
    if (id == 3897424) { return "Scenario Victory"; }
    if (id == 3897426) { return "Kill the Fire Giants guarding the ram."; }
    if (id == 3897427) { return "The Well of Urd must not be destroyed"; }
    if (id == 3897524) { return "Scenario Victory"; }
    if (id == 3897526) { return "Protect the Dwarves while they cut the hammer haft from the taproot."; }
    if (id == 3897527) { return "Bring the two pieces of Thor's hammer together."; }
    if (id == 3897624) { return "Scenario Victory"; }
    if (id == 3897626) { return "Build a Town Center in the abandoned mining town."; }
    if (id == 3897627) { return "Build up your defenses before Gargarensis attacks."; }
    if (id == 3897628) { return "Survive for 20 minutes until help arrives."; }
    if (id == 3897629) { return "Fight your way northward to Gargarensis."; }
    if (id == 3906724) { return "Scenario Victory"; }
    if (id == 3906726) { return "Claim a Settlement on Atlantis."; }
    if (id == 3906727) { return "Transport 15 Atlantean Prisoners to the flagged island."; }
    if (id == 3906824) { return "Scenario Victory"; }
    if (id == 3906826) { return "Advance to the Mythic Age and construct a Wonder."; }
    if (id == 3906827) { return "Use the Blessing of Zeus God Power on Arkantos."; }
    if (id == 3906828) { return "Defeat the Living Statue of Poseidon."; }
    // ---- New Atlantis ----
    if (id == 3916724) { return "Scenario Victory"; }
    if (id == 3916726) { return "Build an army of at least ten soldiers."; }
    if (id == 3916727) { return "Find the Sky Passage."; }
    if (id == 3916728) { return "Defeat the barbarians guarding the Sky Passage."; }
    if (id == 3916729) { return "Garrison five Citizens into the Sky Passage."; }
    if (id == 3916730) { return "Build a Town Center beyond the Sky Passage."; }
    if (id == 3916824) { return "Scenario Victory"; }
    if (id == 3916826) { return "Repair the ancient Temples to Kronos and Oranos."; }
    if (id == 3916827) { return "Advance to the Classical Age."; }
    if (id == 3916828) { return "Destroy the Greek Town Center."; }
    if (id == 3916924) { return "Scenario Victory"; }
    if (id == 3916926) { return "Kill General Melagius."; }
    if (id == 3917024) { return "Scenario Victory"; }
    if (id == 3917026) { return "Replace all Norse Temples with Atlantean Temples."; }
    if (id == 3917027) { return "Move Kastor close to Odin's Tower."; }
    if (id == 3917028) { return "Deconstruct Odin's Wonder."; }
    if (id == 3917124) { return "Scenario Victory"; }
    if (id == 3917126) { return "Garrison all four sacred Relics into Kronos Temple."; }
    if (id == 3917127) { return "Protect Kronos Temple."; }
    if (id == 3917224) { return "Scenario Victory"; }
    if (id == 3917226) { return "Bring soldiers to the Temple to the north."; }
    if (id == 3917227) { return "Reach the flagged area to the east."; }
    if (id == 3917228) { return "Bring Kastor to the peak of Mount Olympus."; }
    if (id == 3917229) { return "Protect the Underworld Passage."; }
    if (id == 3917324) { return "Scenario Victory"; }
    if (id == 3917326) { return "Build up a base and survive the Titan's onslaught."; }
    if (id == 3917327) { return "Send three Rocs to Kastor's Town Center."; }
    if (id == 3917424) { return "Scenario Victory"; }
    if (id == 3917426) { return "Protect the Son of Osiris while he recharges the Guardian."; }
    if (id == 3917427) { return "Destroy the Titan Cerberus."; }
    if (id == 3917524) { return "Scenario Victory"; }
    if (id == 3917526) { return "Construct a Town Center."; }
    if (id == 3917527) { return "Kill the Titan Ymir."; }
    if (id == 3917624) { return "Scenario Victory"; }
    if (id == 3917626) { return "Build four Town Centers and spread Gaia's Lush."; }
    if (id == 3917627) { return "Destroy the Titan Prometheus."; }
    if (id == 3917724) { return "Scenario Victory"; }
    if (id == 3917726) { return "Destroy the Automatons attacking the South Atlanteans."; }
    if (id == 3917727) { return "Destroy the Automatons attacking the West Atlanteans."; }
    if (id == 3917728) { return "Destroy the Automatons attacking the North Atlanteans."; }
    if (id == 3917729) { return "Kastor, Amanra, and Ajax must enter Krios's Sky Passage."; }
    if (id == 3917824) { return "Scenario Victory"; }
    if (id == 3917826) { return "Invoke the Seed of Gaia on all four sacred Gaia Pools."; }
    if (id == 3917827) { return "Protect at least one Summoning Tree until Gaia appears."; }
    if (id == 3917828) { return "Use Gaia to defeat Kronos."; }
    // ---- The Golden Gift ----
    if (id == 3926724) { return "Scenario Victory"; }
    if (id == 3926726) { return "Bring Brokk and four Ox Carts to the flagged tunnel entrance."; }
    if (id == 3926824) { return "Scenario Victory"; }
    if (id == 3926826) { return "Build a Dock."; }
    if (id == 3926827) { return "Bring Eitri and six Dwarves to the entrance to the mines."; }
    if (id == 3926924) { return "Scenario Victory"; }
    if (id == 3926926) { return "Capture the Plenty Vault."; }
    if (id == 3926927) { return "Hold the Dwarven Forge until the timer expires."; }
    if (id == 3927024) { return "Scenario Victory"; }
    if (id == 3927026) { return "Destroy Loki's Temple near your Town Center."; }
    if (id == 3927027) { return "Bring Brokk and Eitri to the Battle Boar."; }
    return "Unknown Location";
}

void APCheckLocation(string objectiveText = "")
{
    trMessageSetText(
        "Checked <color1,1,0>" + objectiveText + "</color>\n\nComplete or quit the mission to send or receive items",
        -1
    );
    trSoundPlayFN("campaign\fott\cinematics\fott07\clearedcity.wav");
}

void APShowQueuedCheckMessage(int id = 0)
{
    string objectiveText = APGetCheckText(id);

    if (objectiveText == "Scenario Victory")
    {
        if (gAPItemCount > 6 && gAPItems[6] == 9010)
        {
            trMessageSetText("<color0,1,0><icon=(25)(resources\egyptian\static_color\technologies\funeral_rites_icon.png)> Gem Received</color>", 5);
        }
        else
        {
            trMessageSetText("<color0,1,0>Checked <color1,1,0>Scenario Victory</color>\n\nComplete or quit the mission to send or receive items.", 5);
        }
    }
    else
    {
        trMessageSetText(
            "Checked <color1,1,0>" + objectiveText + "</color>\n\nComplete or quit the mission to send or receive items.",
            -1
        );
    }
    trSoundPlayFN("campaign\fott\cinematics\fott07\clearedcity.wav");
}

// Legacy helper retained for compatibility if called from within this XS file.

// -----------------------------------------------------------------------
// Main scenario activation rule — enabled by the Gameplay_Starts trigger
void APTransformBuildings()
{
    int scenId = trQuestVarGet("APScenarioID");
    int matched = 0;
    int i = 0;
    while (i < gAPBldgTransformCount)
    {
        if (gAPBldgScen[i] == scenId)
        {
            int    _tp     = gAPBldgPlayer[i];
            string _from   = gAPBldgFrom[i];
            string _t1     = gAPBldgTo1[i];
            string _t2     = gAPBldgTo2[i];
            string _target = _t1;
            if (_t2 != "" && xsRandInt(0, 1) == 1) { _target = _t2; }
            trPlayerChangeProtoUnit(_tp, _from, _target, false);
            matched++;
        }
        i++;
    }
}

// -----------------------------------------------------------------------
// Targeting helpers (KB queries work in trigger XS with xsSetContextPlayer)
// -----------------------------------------------------------------------
bool APTrapIsLivestock(int uid = -1)
{
    string pname = kbProtoUnitGetName(kbUnitGetProtoUnitID(uid));
    if (pname == "Goat")             { return (true); }
    if (pname == "Pig")              { return (true); }
    if (pname == "PigSPC")           { return (true); }
    if (pname == "Cow")              { return (true); }
    if (pname == "Chicken")          { return (true); }
    if (pname == "ChickenOfSet")     { return (true); }
    if (pname == "ChickenEvil")      { return (true); }
    if (pname == "ChickenExploding") { return (true); }
    if (pname == "ChickenBlood")     { return (true); }
    return (false);
}

int APTrapQueryRandom(int playerID = 1, string protoName = "default")
{
    xsSetContextPlayer(playerID);
    int qid = kbUnitQueryCreate("APTrapQ");
    kbUnitQuerySetPlayerID(qid, playerID);
    if (protoName != "default")
        kbUnitQuerySetUnitType(qid, kbGetUnitTypeID(protoName));
    else
        kbUnitQuerySetUnitType(qid, cUnitTypeUnit);
    kbUnitQuerySetIgnoreKnockedOutUnits(qid, true);
    kbUnitQuerySetState(qid, cUnitStateAlive);
    kbUnitQueryExecute(qid);
    int[] res = kbUnitQueryGetResults(qid);
    kbUnitQueryDestroy(qid);
    xsSetContextPlayer(12);
    int sz = res.size();
    if (sz <= 0) { return (-1); }
    // Pick randomly, retry up to sz times to avoid livestock
    int attempt = 0;
    while (attempt < sz)
    {
        int candidate = res[xsRandInt(0, sz - 1)];
        xsSetContextPlayer(playerID);
        bool isLive = APTrapIsLivestock(candidate);
        xsSetContextPlayer(12);
        if (!isLive) { return (candidate); }
        attempt++;
    }
    // All results are livestock — return first one as fallback
    return (res[0]);
}

// Query a random alive building for a player (for Pestilence).
// Returns any alive building for the given player.
int APTrapQueryBuilding(int playerID = 1)
{
    xsSetContextPlayer(playerID);
    int qid = kbUnitQueryCreate("APTrapBldQ");
    kbUnitQuerySetPlayerID(qid, playerID);
    kbUnitQuerySetUnitType(qid, cUnitTypeBuilding);
    kbUnitQuerySetState(qid, cUnitStateAlive);
    kbUnitQueryExecute(qid);
    int[] res = kbUnitQueryGetResults(qid);
    kbUnitQueryDestroy(qid);
    xsSetContextPlayer(12);
    if (res.size() > 0) { return (res[xsRandInt(0, res.size() - 1)]); }
    return (-1);
}

// Query a building target for Deconstruction:
//   1st priority — Sentry Tower
//   2nd priority — Temple
//   Fallback     — any P1 building that is not a Town Center
int APTrapQueryDeconBuilding()
{
    // Try Sentry Tower first
    int _uid = APTrapQueryRandom(1, "SentryTower");
    if (_uid >= 0) { return (_uid); }
    // Try Temple
    _uid = APTrapQueryRandom(1, "Temple");
    if (_uid >= 0) { return (_uid); }
    // Fallback: any alive P1 building except Town Center
    xsSetContextPlayer(1);
    int qid = kbUnitQueryCreate("APDeconBldQ");
    kbUnitQuerySetPlayerID(qid, 1);
    kbUnitQuerySetUnitType(qid, cUnitTypeBuilding);
    kbUnitQuerySetState(qid, cUnitStateAlive);
    kbUnitQueryExecute(qid);
    int[] res = kbUnitQueryGetResults(qid);
    kbUnitQueryDestroy(qid);
    xsSetContextPlayer(12);
    int sz = res.size();
    if (sz <= 0) { return (-1); }
    // Shuffle through candidates, skip Town Centers
    int attempt = 0;
    while (attempt < sz)
    {
        int candidate = res[xsRandInt(0, sz - 1)];
        string pname = kbProtoUnitGetName(kbUnitGetProtoUnitID(candidate));
        if (pname != "TownCenter" && pname != "TownCenterAbandoned")
        {
            return (candidate);
        }
        attempt++;
    }
    return (-1);
}



// Prefer myth units for single-unit targeted powers (Bolt, Traitor).
// Falls back to cUnitTypeUnit if no myth units found.
int APTrapQueryMythOrUnit(int playerID = 1)
{
    xsSetContextPlayer(playerID);
    int qid = kbUnitQueryCreate("APTrapMythQ");
    kbUnitQuerySetPlayerID(qid, playerID);
    kbUnitQuerySetUnitType(qid, cUnitTypeMythUnit);
    kbUnitQuerySetState(qid, cUnitStateAlive);
    kbUnitQueryExecute(qid);
    int[] res = kbUnitQueryGetResults(qid);
    kbUnitQueryDestroy(qid);
    xsSetContextPlayer(12);
    if (res.size() > 0) { return (res[xsRandInt(0, res.size() - 1)]); }
    // No myth units — fall back to any military unit
    return (APTrapQueryRandom(playerID, "default"));
}

string APTrapGetName(int trapType = 0)
{
    if (trapType == 1)  { return ("Meteor"); }
    if (trapType == 2)  { return ("Lightning Storm"); }
    if (trapType == 3)  { return ("Locust Swarm"); }
    if (trapType == 4)  { return ("Bolt"); }
    if (trapType == 7)  { return ("Restoration"); }
    if (trapType == 8)  { return ("Citadel"); }
    if (trapType == 9)  { return ("Tornado"); }
    if (trapType == 10) { return ("Earthquake"); }
    if (trapType == 11) { return ("Curse"); }
    if (trapType == 12) { return ("Plague of Serpents"); }
    if (trapType == 13) { return ("Implode"); }
    if (trapType == 14) { return ("Tartarian Gate"); }
    if (trapType == 15) { return ("Chaos"); }
    if (trapType == 16) { return ("Traitor"); }
    if (trapType == 17) { return ("Carnivora"); }
    if (trapType == 18) { return ("Spider Lair"); }
    if (trapType == 19) { return ("Deconstruction"); }
    if (trapType == 20) { return ("Fimbulwinter"); }
    if (trapType == 21) { return ("Flaming Weapons"); }
    if (trapType == 22) { return ("Ancestors"); }
    if (trapType == 23) { return ("Pestilence"); }
    if (trapType == 25) { return ("Nidhogg"); }
    if (trapType == 26) { return ("Shockwave"); }
    return ("Unknown Trap");
}

void APTrapExecuteTrap(int trapType = 0)
{
    // Announcement
    string _name = APTrapGetName(trapType);
    trMessageSetText("<color0.788,0.412,0.373>" + _name + " trap triggered</color>", 6);

    // Targeting
    int _uid  = -1;
    int _buid = -1;  // building target (Citadel, Deconstruction, Pestilence)
    gAPTrapPos = vector(0, 0, 0);

    // Friendly powers target P2; unit-targeted powers pick cUnitTypeUnit;
    // hostile area powers pick random P1 cUnitTypeUnit
    if (trapType == 7)
    {
        // Restoration → random P2 unit
        _uid = APTrapQueryRandom(2, "default");
    }
    else if (trapType == 8)
    {
        // Citadel → hostile Town Center: try P2 then P4, P5, P6
        _uid = APTrapQueryRandom(2, "Town Center");
        if (_uid < 0) { _uid = APTrapQueryRandom(4, "Town Center"); }
        if (_uid < 0) { _uid = APTrapQueryRandom(5, "Town Center"); }
        if (_uid < 0) { _uid = APTrapQueryRandom(6, "Town Center"); }
        // No fallback to generic unit — Citadel must target a TC or skip
    }
    else if (trapType == 23)
    {
        // Pestilence → random P1 building
        _uid = APTrapQueryBuilding(1);
        if (_uid < 0) { _uid = APTrapQueryRandom(1, "default"); }
    }
    else if (trapType == 19)
    {
        // Deconstruction → Sentry Tower, then Temple, then any non-TC P1 building
        _uid = APTrapQueryDeconBuilding();
        // No unit fallback — Deconstruction must hit a building or skip
    }
    else if (trapType == 4 || trapType == 16)
    {
        // Bolt / Traitor → prefer myth units, fall back to military units
        _uid = APTrapQueryMythOrUnit(1);
    }
    else
    {
        // All other traps → random P1 military unit
        _uid = APTrapQueryRandom(1, "default");
    }

    if (_uid >= 0) { gAPTrapPos = trUnitGetPosition(_uid); }

    // Debug: show trap type and coordinates
    trMessageSetText("<color0.788,0.412,0.373>" + APTrapGetName(trapType) + " Trap!</color>", 6);

    // Disable god power blocking before invoke, re-enable after
    trGodPowerEnableBlocking(false);

    trUnitSelectClear();

    if (trapType == 1)  { trGodPowerGrant(12, "Meteor",             1, 0, false, false); trGodPowerInvoke(12, "Meteor",             gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 2)  { trGodPowerGrant(12, "LightningStorm",    1, 0, false, false); trGodPowerInvoke(12, "LightningStorm",    gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 3)
    {
        // Locust Swarm: pos1=start, pos2=direction. Pick a random cardinal offset.
        int _lsDir = xsRandInt(0, 3);
        vector _lsEnd = gAPTrapPos;
        if (_lsDir == 0) { _lsEnd = gAPTrapPos + vector(30, 0, 0); }
        if (_lsDir == 1) { _lsEnd = gAPTrapPos + vector(-30, 0, 0); }
        if (_lsDir == 2) { _lsEnd = gAPTrapPos + vector(0, 0, 30); }
        if (_lsDir == 3) { _lsEnd = gAPTrapPos + vector(0, 0, -30); }
        trGodPowerGrant(12, "LocustSwarm", 1, 0, false, false);
        trGodPowerInvoke(12, "LocustSwarm", gAPTrapPos, _lsEnd, true);
    }
    if (trapType == 4)  { trGodPowerGrant(12, "Bolt",               1, 0, false, false); trGodPowerInvoke(12, "Bolt",               gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 7)  { trGodPowerGrant(12, "Restoration",        1, 0, false, false); trGodPowerInvoke(12, "Restoration",        gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 8)  { trGodPowerGrant(12, "Citadel",            1, 0, false, false); trGodPowerInvoke(12, "Citadel",            gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 9)  { trGodPowerGrant(12, "Tornado",            1, 0, false, false); trGodPowerInvoke(12, "Tornado",            gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 10) { trGodPowerGrant(12, "Earthquake",         1, 0, false, false); trGodPowerInvoke(12, "Earthquake",         gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 11) { trGodPowerGrant(12, "Curse",              1, 0, false, false); trGodPowerInvoke(12, "Curse",              gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 12) { trGodPowerGrant(12, "PlagueOfSerpents", 1, 0, false, false); trGodPowerInvoke(12, "PlagueOfSerpents", gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 13) { trGodPowerGrant(12, "Implode",            1, 0, false, false); trGodPowerInvoke(12, "Implode",            gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 14) { trGodPowerGrant(12, "TartarianGate",     1, 0, false, false); trGodPowerInvoke(12, "TartarianGate",     gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 15) { trGodPowerGrant(12, "Chaos",              1, 0, false, false); trGodPowerInvoke(12, "Chaos",              gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 16) { trGodPowerGrant(12, "Traitor",            1, 0, false, false); trGodPowerInvoke(12, "Traitor",            gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 17) { trGodPowerGrant(12, "Carnivora",          1, 0, false, false); trGodPowerInvoke(12, "Carnivora",          gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 18) { trGodPowerGrant(12, "SpiderLair",         1, 0, false, false); trGodPowerInvoke(12, "SpiderLair",         gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 19) { trGodPowerGrant(12, "Deconstruction",     1, 0, false, false); trGodPowerInvoke(12, "Deconstruction",     gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 20) { trGodPowerGrant(12, "Fimbulwinter",       1, 0, false, false); trGodPowerInvoke(12, "Fimbulwinter",       gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 21) { trGodPowerGrant(12, "FlamingWeapons",    1, 0, false, false); trGodPowerInvoke(12, "FlamingWeapons",    gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 22) { trGodPowerGrant(12, "Ancestors",          1, 0, false, false); trGodPowerInvoke(12, "Ancestors",          gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 23) { trGodPowerGrant(12, "Pestilence",         1, 0, false, false); trGodPowerInvoke(12, "Pestilence",         gAPTrapPos, gAPTrapPos, true); }
    if (trapType == 25)
    {
        // Nidhogg: boost LOS so it can see target, then invoke at P1 unit position
        trModifyProtounitData("Nidhogg", 12, 2, 50, 1);  // field 2=LOS, delta=50, relativity=1 (add)
        trGodPowerGrant(12, "Nidhogg", 1, 0, false, false);
        trGodPowerInvoke(12, "Nidhogg", gAPTrapPos, gAPTrapPos, true);
    }
    if (trapType == 26) { trGodPowerGrant(12, "Shockwave",          1, 0, false, false); trGodPowerInvoke(12, "Shockwave",          gAPTrapPos, gAPTrapPos, true); }

    trGodPowerEnableBlocking(true);

    // Signal client — log flushed at scenario end, client counts these
    trExecuteOnAI(12, "APTrapFiredSignal");
}


// Returns the starting age (0=Archaic, 1=Classical, 2=Heroic, 3=Mythic)
// for the current scenario, used to gate progressive tech upgrades.
int APGetScenarioStartingAge()
{
    int s = gAPScenarioId;
    // Mythic start
    if (s == 9 || s == 16) { return (3); }
    // Heroic start
    if (s == 5  || s == 6  || s == 7  || s == 13 || s == 14 || s == 17 ||
        s == 19 || s == 20 || s == 28 || s == 31 || s == 32) { return (2); }
    // Archaic start
    if (s == 2 || s == 3 || s == 10 || s == 11 || s == 12 ||
        s == 22 || s == 502) { return (0); }
    // Mythic start
    if (s == 506 || s == 511 || s == 512 || s == 604) { return (3); }
    // Heroic start (New Atlantis: 501,503-505,507-510; Golden Gift: 601-603)
    if (s == 501 || s == 503 || s == 504 || s == 505 ||
        s == 507 || s == 508 || s == 509 || s == 510 ||
        s == 601 || s == 602 || s == 603) { return (2); }
    // Classical start (FotT default + NA502 handled above)
    return (1);
}

// Apply progressive economy and military tech upgrades.
// Must be called AFTER APSetPlayerCiv() — changing civilization wipes researched techs.
// Tier X techs are awarded when: playerCount >= X AND scenarioStartingAge >= X.
// Grant starting tech packages based on the scenario's starting age.
// econHas/milHas/dockHas/bldgsHas are 1 if the player has that item, 0 otherwise.
// Each category grants ALL technologies up to and including the scenario's starting age.
// Archaic (age 0) still grants Archaic-tier economy techs (Hand Axe, Pickaxe, Husbandry)
// since every scenario starts in at least the Archaic age.
void APApplyStartingTechs(int econHas = 0, int milHas = 0, int dockHas = 0, int bldgsHas = 0)
{
    int age = APGetScenarioStartingAge();

    // --- Starting Economy Tech ---
    // Archaic techs always granted (every scenario starts at Archaic or later)
    if (econHas >= 1)
    {
        trTechSetStatus(1, cTechHandAxe,    2);
        trTechSetStatus(1, cTechPickaxe,    2);
        trTechSetStatus(1, cTechHusbandry,  2);
    }
    if (econHas >= 1 && age >= 1)  // Classical+
    {
        trTechSetStatus(1, cTechPlow,       2);
        trTechSetStatus(1, cTechBowSaw,     2);
        trTechSetStatus(1, cTechShaftMine,  2);
    }
    if (econHas >= 1 && age >= 2)  // Heroic+
    {
        trTechSetStatus(1, cTechIrrigation, 2);
        trTechSetStatus(1, cTechCarpenters, 2);
        trTechSetStatus(1, cTechQuarry,     2);
    }
    if (econHas >= 1 && age >= 3)  // Mythic
    {
        trTechSetStatus(1, cTechFloodControl, 2);
    }

    // --- Starting Military Tech ---
    if (milHas >= 1 && age >= 1)  // Classical+
    {
        trTechSetStatus(1, cTechCopperWeapons,  2);
        trTechSetStatus(1, cTechCopperArmor,    2);
        trTechSetStatus(1, cTechCopperShields,  2);
        trTechSetStatus(1, cTechMediumInfantry, 2);
        trTechSetStatus(1, cTechMediumArchers,  2);
        trTechSetStatus(1, cTechMediumCavalry,  2);
        trTechSetStatus(1, cTechMediumAxemen,   2);
        trTechSetStatus(1, cTechMediumSlingers, 2);
        trTechSetStatus(1, cTechMediumSpearmen, 2);
    }
    if (milHas >= 1 && age >= 2)  // Heroic+
    {
        trTechSetStatus(1, cTechBronzeWeapons,        2);
        trTechSetStatus(1, cTechBronzeArmor,          2);
        trTechSetStatus(1, cTechBronzeShields,        2);
        trTechSetStatus(1, cTechHeavyInfantry,        2);
        trTechSetStatus(1, cTechHeavyArchers,         2);
        trTechSetStatus(1, cTechHeavyCavalry,         2);
        trTechSetStatus(1, cTechHeavyAxemen,          2);
        trTechSetStatus(1, cTechHeavySlingers,        2);
        trTechSetStatus(1, cTechHeavySpearmen,        2);
        trTechSetStatus(1, cTechHeavyChariotArchers,  2);
        trTechSetStatus(1, cTechHeavyCamelRiders,     2);
        trTechSetStatus(1, cTechHeavyWarElephants,    2);
    }
    if (milHas >= 1 && age >= 3)  // Mythic
    {
        trTechSetStatus(1, cTechIronWeapons,             2);
        trTechSetStatus(1, cTechIronArmor,               2);
        trTechSetStatus(1, cTechIronShields,             2);
        trTechSetStatus(1, cTechChampionInfantry,        2);
        trTechSetStatus(1, cTechChampionArchers,         2);
        trTechSetStatus(1, cTechChampionCavalry,         2);
        trTechSetStatus(1, cTechChampionAxemen,          2);
        trTechSetStatus(1, cTechChampionSlingers,        2);
        trTechSetStatus(1, cTechChampionSpearmen,        2);
        trTechSetStatus(1, cTechChampionChariotArchers,  2);
        trTechSetStatus(1, cTechChampionCamelRiders,     2);
        trTechSetStatus(1, cTechChampionWarElephants,    2);
    }

    // --- Starting Dock Tech ---
    if (dockHas >= 1 && age >= 1)  // Classical+
    {
        trTechSetStatus(1, cTechPurseSeine,   2);
        trTechSetStatus(1, cTechEnclosedDeck, 2);
        trTechSetStatus(1, cTechHeroicFleet,  2);
    }
    if (dockHas >= 1 && age >= 2)  // Heroic+
    {
        trTechSetStatus(1, cTechSaltAmphora,   2);
        trTechSetStatus(1, cTechHeavyWarships, 2);
    }
    if (dockHas >= 1 && age >= 3)  // Mythic
    {
        trTechSetStatus(1, cTechChampionWarships,  2);
        trTechSetStatus(1, cTechConscriptSailors,  2);
    }

    // --- Starting Buildings Tech ---
    // Civ-specific techs gated on gAPMajorGod.
    // Greek: 1,2,3   Egyptian: 4,5,6   Norse: 7,8,9   Atlantean: 10,11,12
    bool _isGreek     = (gAPMajorGod == cAPMajorZeus || gAPMajorGod == cAPMajorPoseidon || gAPMajorGod == cAPMajorHades);
    bool _isEgyptian  = (gAPMajorGod == cAPMajorIsis  || gAPMajorGod == cAPMajorRa      || gAPMajorGod == cAPMajorSet);
    bool _isNorse     = (gAPMajorGod == cAPMajorOdin  || gAPMajorGod == cAPMajorThor    || gAPMajorGod == cAPMajorLoki);
    bool _isAtlantean = (gAPMajorGod == cAPMajorKronos || gAPMajorGod == cAPMajorOranos || gAPMajorGod == cAPMajorGaia);

    if (bldgsHas >= 1 && age >= 1)  // Classical+ (all civs)
    {
        trTechSetStatus(1, cTechCrenellations, 2);
        trTechSetStatus(1, cTechBoilingOil,    2);
        trTechSetStatus(1, cTechSignalFires,   2);
        trTechSetStatus(1, cTechMasons,        2);
        trTechSetStatus(1, cTechStoneWall,     2);
        trTechSetStatus(1, cTechWatchTower,    2);
    }
    if (bldgsHas >= 1 && age >= 1 && _isAtlantean)  // Classical+ Atlantean only
    {
        trTechSetStatus(1, cTechBronzeWall, 2);
    }
    if (bldgsHas >= 1 && age >= 1 && (_isGreek || _isEgyptian))  // Classical+ Greek/Egyptian only
    {
        trTechSetStatus(1, cTechFortifiedWall, 2);
    }
    if (bldgsHas >= 1 && age >= 2)  // Heroic+ (all civs)
    {
        trTechSetStatus(1, cTechCarrierPigeons,     2);
        trTechSetStatus(1, cTechArchitects,         2);
        trTechSetStatus(1, cTechFortifiedTownCenter, 2);
    }
    if (bldgsHas >= 1 && age >= 2 && (_isGreek || _isEgyptian || _isAtlantean))  // Heroic+ non-Norse
    {
        trTechSetStatus(1, cTechGuardTower, 2);
    }
    if (bldgsHas >= 1 && age >= 2 && _isAtlantean)  // Heroic+ Atlantean only
    {
        trTechSetStatus(1, cTechIronWall, 2);
    }
    if (bldgsHas >= 1 && age >= 3)  // Mythic (all civs)
    {
        trTechSetStatus(1, cTechOrichalcumWall, 2);
    }
    if (bldgsHas >= 1 && age >= 3 && _isEgyptian)  // Mythic Egyptian only
    {
        trTechSetStatus(1, cTechCitadelWall,  2);
        trTechSetStatus(1, cTechBallistaTower, 2);
    }
}

// in each scenario via: xsEnableRule("APActivateScenario")
// -----------------------------------------------------------------------


void APTrapScheduleNext(bool firstInScenario = false)
{
    if (gAPTrapQueueSize <= 0) { gAPTrapPending = false; return; }
    // 45-600 seconds (45s to 10 minutes)
    float delay = xsRandInt(45, 600);
    gAPTrapFireTime = xsGetTime() + delay;
    gAPTrapPending  = true;
}

void APTrapPop()
{
    if (gAPTrapQueueSize <= 0) { return; }
    // Shift queue left
    int i = 0;
    while (i < gAPTrapQueueSize - 1)
    {
        gAPTrapQueue[i] = gAPTrapQueue[i + 1];
        i++;
    }
    gAPTrapQueueSize--;
    gAPTrapPending = false;
}


rule APActivateScenario
highFrequency
inactive
runImmediately
{
    gAPScenarioId = trQuestVarGet("APScenarioID");
    gAPCampaignId = APGetCampaignForScenario(gAPScenarioId);
    gAPMajorGod   = APGetMajorGodForScenario(gAPScenarioId);
    APInitItems();               // populate gAPItems array first
    trQuestVarSet("APRandomMajorGods", gAPItems[5] == 9010 ? 1 : 0);

    // Shop scenario (ID 0)
    if (gAPScenarioId == 0)
    {
        // gem_shop disabled flag is at index 6 (9010=enabled, 9000=disabled)
        if (gAPItemCount > 6 && gAPItems[6] != 9010)
        {
            trMessageSetText("The Shop was Disabled in the Options yaml.", 8);
            trLeaveGame();
            xsDisableSelf();
            return;
        }
        APShopScenarioInit();
        xsEnableRule("APProcessShopBuy");
        xsEnableRule("APShopTierCheck");
        trMusicPlayCurrent();
        xsDisableSelf();
        return;
    }

    APInitGods();
    APReadRandomGod();
    APSetPlayerCiv();
    APForbidVanillaArchaicUnits();
    APInitGodPowers();
    // Reset random god power QVs at the start of each scenario.
    trQuestVarSet("rand_gp_1", 0);
    trQuestVarSet("rand_gp_2", 0);
    trQuestVarSet("rand_gp_3", 0);
    trQuestVarSet("rand_gp_4", 0);
    xsEnableRule("APRandGP1");
    xsEnableRule("APRandGP2");
    xsEnableRule("APRandGP3");
    xsEnableRule("APRandGP4");
    // APInitStartingAgeTechs() sets the seed-determined minor god tech to status 2
    // for each floor age tier. APApply*MinorGods only sets the BASE age tech to
    // status 2 in its floor block — minor god selection is handled here.
    APInitStartingAgeTechs();
    APForbidItemGatedUnits();

    // Apply progressive tech upgrades now — must come after APSetPlayerCiv()
    // because changing civilization wipes any previously researched technologies.
    // gAPItems is already populated by APInitItems() above.
    int _econTechCount = 0;
    int _milTechCount  = 0;
    int _dockTechCount = 0;
    int _bldgTechCount = 0;
    int _pti = 0;
    while (_pti < gAPItemCount)
    {
        int _ptid = gAPItems[_pti];
        if (_ptid == cSTARTING_ECONOMY_TECH)    { _econTechCount++;  }
        if (_ptid == cSTARTING_MILITARY_TECH)   { _milTechCount++;  }
        if (_ptid == cSTARTING_DOCK_TECH)       { _dockTechCount++; }
        if (_ptid == cSTARTING_BUILDINGS_TECH)  { _bldgTechCount++; }
        _pti++;
    }
    APApplyStartingTechs(_econTechCount, _milTechCount, _dockTechCount, _bldgTechCount);

    // SPC campaign heroes
    trForbidProtounit(1, "Ajax");
    trForbidProtounit(1, "Chiron");
    trForbidProtounit(1, "Odysseus");

    // Scenario 12: Roc causes a game-breaking bug
    if (gAPScenarioId == 12) { trForbidProtounit(1, "Roc"); }

    // Scenario 6: The Trojan Horse can only be built by Greek Villagers.
    // Forbid all other villager types regardless of assigned god, and
    // explicitly allow Greek Villagers in case a non-Greek god was assigned.
    if (gAPScenarioId == 6)
    {
        trForbidProtounit(1, "VillagerEgyptian");
        trForbidProtounit(1, "VillagerNorse");
        trForbidProtounit(1, "VillagerAtlantean");
        trUnforbidProtounit(1, "VillagerGreek");
    }

    // Scenarios that start at Classical Age or later get Sentry Tower ranged attack
    // and the Watch Tower tech pre-researched. Archaic-start scenarios (2,3,10,11,12,21,22)
    // are excluded — the player hasn't advanced far enough for towers to fire yet.
    bool _classicalPlus = (gAPScenarioId != 2  && gAPScenarioId != 3  &&
                           gAPScenarioId != 10 && gAPScenarioId != 11 &&
                           gAPScenarioId != 12 && gAPScenarioId != 22);
    if (_classicalPlus)
    {
        trProtoUnitActionSetEnabled("SentryTower", 1, "RangedAttack", true);
        trTechSetStatus(1, cTechWatchTower, 2);
    }

    // Egyptian major gods get Watch Tower on every scenario regardless of starting age,
    // since their tower playstyle is civ-core and shouldn't depend on scenario gating.
    if (gAPMajorGod == cAPMajorIsis || gAPMajorGod == cAPMajorRa || gAPMajorGod == cAPMajorSet)
    {
        trTechSetStatus(1, cTechWatchTower, 2);
    }

    // Allow TartarianGate and Carnivora to place anywhere — removes terrain
    // restrictions that prevent these god powers from invoking in some scenarios.
    trProtoUnitSetFlag(12, "TartarianGatePlacement", "PlaceAnywhere", true);
    trProtoUnitSetFlag(12, "Carnivora",     "PlaceAnywhere", true);

    gAPRandomMajorGods = (gAPItemCount > 5 && gAPItems[5] == 9010);

    // NA 2 (Atlantis Reborn): configure TempleOvergrown to train the full set
    // of units that a normal temple can train, based on the assigned major god.
    if (gAPScenarioId == 502)
    {
        // Greek
        if (gAPMajorGod == cAPMajorZeus || gAPMajorGod == cAPMajorPoseidon || gAPMajorGod == cAPMajorHades)
        {
            trProtounitAddTrain("TempleOvergrown", 1, "Pegasus",        0, 0);
            trProtounitAddTrain("TempleOvergrown", 1, "Minotaur",       0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Centaur",        0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Cyclops",        0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "LykaonVillager", 0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "NemeanLion",     0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "Manticore",      0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "Hydra",          0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "Hamadryad",      0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "Chimera",        0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "Colossus",       0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "Medusa",         0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "Siren",          0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "HarpyMyth",      0, 4);
        }
        // Egyptian
        if (gAPMajorGod == cAPMajorIsis || gAPMajorGod == cAPMajorRa || gAPMajorGod == cAPMajorSet)
        {
            trProtounitAddTrain("TempleOvergrown", 1, "Priest",         0, 0);
            trProtounitAddTrain("TempleOvergrown", 1, "Wadjet",         0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Anubite",        0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Sphinx",         0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Scarab",         0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "Petsuchos",      0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "ScorpionMan",    0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "Phoenix",        0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "Avenger",        0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "Mummy",          0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "Roc",            0, 4);
        }
        // Norse
        if (gAPMajorGod == cAPMajorOdin || gAPMajorGod == cAPMajorThor || gAPMajorGod == cAPMajorLoki)
        {
            trProtounitAddTrain("TempleOvergrown", 1, "Hersir",         0, 0);
            trProtounitAddTrain("TempleOvergrown", 1, "Troll",          0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Valkyrie",       0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Einheri",        0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Draugr",         0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "BattleBoar",     0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "RockGiant",      0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "FrostGiant",     0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "MountainGiant",  0, 4);
            trProtounitAddTrain("TempleOvergrown", 1, "FireGiant",      0, 5);
            trProtounitAddTrain("TempleOvergrown", 1, "FenrisWolfBrood",0, 5);
            trProtounitAddTrain("TempleOvergrown", 1, "Fafnir",         0, 5);
        }
        // Atlantean
        if (gAPMajorGod == cAPMajorKronos || gAPMajorGod == cAPMajorOranos || gAPMajorGod == cAPMajorGaia)
        {
            trProtounitAddTrain("TempleOvergrown", 1, "Oracle",         0, 0);
            trProtounitAddTrain("TempleOvergrown", 1, "Automaton",      0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Promethean",     0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Caladria",       0, 1);
            trProtounitAddTrain("TempleOvergrown", 1, "Satyr",          0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "Behemoth",       0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "StymphalianBird",0, 2);
            trProtounitAddTrain("TempleOvergrown", 1, "Centimanus",     0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "Lampades",       0, 3);
            trProtounitAddTrain("TempleOvergrown", 1, "Argus",          0, 3);
        }

    }

    xsEnableRule("APApplyItems");
    xsEnableRule("APAnnounceGod");
    //xsEnableRule("APEnforceAgeLocks");
    xsEnableRule("APAnnounceMaxAge");
    // Reset per-scenario relic-trickle and relic-effect accumulators, then
    // start the unified enforcement rule.
    gAPRelicTrickleAppliedFood  = 0.0;
    gAPRelicTrickleAppliedWood  = 0.0;
    gAPRelicTrickleAppliedGold  = 0.0;
    gAPRelicTrickleAppliedFavor = 0.0;
    gAPRelicEffAppliedLOS        = 0;
    gAPRelicEffAppliedRegen      = 0;
    gAPRelicEffAppliedSpeed      = 0;
    gAPRelicEffAppliedHP         = 0;
    gAPRelicEffAppliedPop        = 0;
    gAPRelicEffAppliedGoldCost   = 0;
    gAPRelicEffAppliedWoodCost   = 0;
    gAPRelicEffAppliedFavorCost  = 0;
    gAPRelicEffAppliedFoodCost   = 0;
    gAPRelicEffAppliedBuildSpeed = 0;
    gAPRelicLastCount            = -1;
    xsEnableRule("APRelicTrickleEnforce");
    // Initialize trap queue from aom_state.xs generated state
    // Transform buildings to match random god's civilization (if enabled)
    APLoadBuildingTransforms();
    if (gAPBldgTransformCount > 0)
    {
        APTransformBuildings();
    }

    // Set Player 12 as ally with players 2-11 so god powers only damage Player 1
    int _dp = 2;
    while (_dp <= 11)
    {
        trPlayerSetDiplomacy(12, _dp, "ally", true);
        _dp++;
    }

    // Give Player 12 full map vision for trap targeting via a Revealer unit.
    // Each scenario editor should also have a Protounit Modify Data trigger
    // increasing Revealer LOS to 1000 for Player 12.
    trCreateRevealer(12, "APTrapRevealer", vector(0, 0, 0), 500.0, false);
    trPlayerTechTreeEnabledGodPowers(12, true);  // ensure P12 can invoke all powers
    
    APTrapQueueInit();
    // Enable trap timer if traps are queued
    if (gAPTrapQueueSize > 0)
    {
        xsEnableRule("APTrapTimer");
        trQuestVarSet("APTrapActive", 1);
        APTrapScheduleNext(true);
    }
    trMusicPlayCurrent();
    xsDisableSelf();
}

rule APInitQueuedCheckState
highFrequency
active
runImmediately
{
    gAPLastProcessedCheckNonce = 0;
    trQuestVarSet("APQueuedCheckID", 0);
    trQuestVarSet("APQueuedCheckNonce", 0);
    xsDisableSelf();
}

rule APProcessQueuedCheck
highFrequency
active
runImmediately
{
    int nonce = trQuestVarGet("APQueuedCheckNonce");

    if (nonce > gAPLastProcessedCheckNonce)
    {
        int id = trQuestVarGet("APQueuedCheckID");
        APShowQueuedCheckMessage(id);
        gAPLastProcessedCheckNonce = nonce;
    }
}

// -----------------------------------------------------------------------
// Campaign lock check
// -----------------------------------------------------------------------

void APCheckCampaignLock()
{
    // Campaign ID 0 means not yet derived — don't lock
    if (gAPCampaignId == 0) { return; }

    bool hasUnlock = false;
    if (gAPCampaignId == 1 && gHasGreek == true) { hasUnlock = true; }
    if (gAPCampaignId == 2 && gHasEgyptian == true) { hasUnlock = true; }
    if (gAPCampaignId == 3 && gHasNorse == true) { hasUnlock = true; }
    if (gAPCampaignId == 4 && gHasAtlantis == true) { hasUnlock = true; }
    if (gAPCampaignId == 5 && gHasNewAtlantis == true) { hasUnlock = true; }
    if (gAPCampaignId == 6 && gHasGoldenGift  == true) { hasUnlock = true; }

    if (hasUnlock == false)
    {
        string neededItem = "UNKNOWN ITEM";
        if (gAPCampaignId == 1) { neededItem = "Greek Scenarios"; }
        if (gAPCampaignId == 2) { neededItem = "Egyptian Scenarios"; }
        if (gAPCampaignId == 3) { neededItem = "Norse Scenarios"; }
        if (gAPCampaignId == 4) { neededItem = "Atlantis Key"; }
        if (gAPCampaignId == 5) { neededItem = "Unlock New Atlantis Campaign"; }
        if (gAPCampaignId == 6) { neededItem = "Unlock The Golden Gift Campaign"; }

        string msg = "You need " + neededItem + " to play this";
        trShowWinPopup(msg, "taunts\037 not a wise decision but a decision nonetheless.mp3", true);

        if (gAPCampaignId == 1) { trExecuteOnAI(12, "APLocked_Greek"); }
        if (gAPCampaignId == 2) { trExecuteOnAI(12, "APLocked_Egyptian"); }
        if (gAPCampaignId == 3) { trExecuteOnAI(12, "APLocked_Norse"); }
        if (gAPCampaignId == 4) { trExecuteOnAI(12, "APLocked_Final"); }
        if (gAPCampaignId == 5) { trExecuteOnAI(12, "APLocked_NewAtlantis"); }
        if (gAPCampaignId == 6) { trExecuteOnAI(12, "APLocked_GoldenGift"); }

        xsEnableRule("APLockedDelay");
    }
}

// -----------------------------------------------------------------------
// Delayed campaign loss — fires 8 seconds after lock message is shown
// -----------------------------------------------------------------------

rule APLockedDelay
minInterval 8
inactive
runImmediately
{
    trLeaveGame();
    xsDisableSelf();
}

// -----------------------------------------------------------------------
// Legacy helper retained for compatibility.
// Current scenario identity is driven by APScenarioID + APActivateScenario.
// -----------------------------------------------------------------------

void APSetCampaignId(int id = 0)
{
    gAPCampaignId = id;
}

// -----------------------------------------------------------------------
// Age unlock helpers — block/unblock age advancement and minor gods
// -----------------------------------------------------------------------

void APDisableAllGreekAgeTechs()
{
    if (trTechStatusActive(1, cTechClassicalAgeAthena) == false) { trTechSetStatus(1, cTechClassicalAgeAthena, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeHermes) == false) { trTechSetStatus(1, cTechClassicalAgeHermes, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeAres) == false) { trTechSetStatus(1, cTechClassicalAgeAres, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeGreek) == false) { trTechSetStatus(1, cTechClassicalAgeGreek, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeApollo) == false) { trTechSetStatus(1, cTechHeroicAgeApollo, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeDionysus) == false) { trTechSetStatus(1, cTechHeroicAgeDionysus, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeAphrodite) == false) { trTechSetStatus(1, cTechHeroicAgeAphrodite, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeGreek) == false) { trTechSetStatus(1, cTechHeroicAgeGreek, 0); }
    if (trTechStatusActive(1, cTechMythicAgeHera) == false) { trTechSetStatus(1, cTechMythicAgeHera, 0); }
    if (trTechStatusActive(1, cTechMythicAgeHephaestus) == false) { trTechSetStatus(1, cTechMythicAgeHephaestus, 0); }
    if (trTechStatusActive(1, cTechMythicAgeArtemis) == false) { trTechSetStatus(1, cTechMythicAgeArtemis, 0); }
    if (trTechStatusActive(1, cTechMythicAgeGreek) == false) { trTechSetStatus(1, cTechMythicAgeGreek, 0); }
}

void APDisableAllEgyptianAgeTechs()
{
    if (trTechStatusActive(1, cTechClassicalAgeAnubis) == false) { trTechSetStatus(1, cTechClassicalAgeAnubis, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeBast) == false) { trTechSetStatus(1, cTechClassicalAgeBast, 0); }
    if (trTechStatusActive(1, cTechClassicalAgePtah) == false) { trTechSetStatus(1, cTechClassicalAgePtah, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeEgyptian) == false) { trTechSetStatus(1, cTechClassicalAgeEgyptian, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeSekhmet) == false) { trTechSetStatus(1, cTechHeroicAgeSekhmet, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeSobek) == false) { trTechSetStatus(1, cTechHeroicAgeSobek, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeNephthys) == false) { trTechSetStatus(1, cTechHeroicAgeNephthys, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeEgyptian) == false) { trTechSetStatus(1, cTechHeroicAgeEgyptian, 0); }
    if (trTechStatusActive(1, cTechMythicAgeOsiris) == false) { trTechSetStatus(1, cTechMythicAgeOsiris, 0); }
    if (trTechStatusActive(1, cTechMythicAgeHorus) == false) { trTechSetStatus(1, cTechMythicAgeHorus, 0); }
    if (trTechStatusActive(1, cTechMythicAgeThoth) == false) { trTechSetStatus(1, cTechMythicAgeThoth, 0); }
    if (trTechStatusActive(1, cTechMythicAgeEgyptian) == false) { trTechSetStatus(1, cTechMythicAgeEgyptian, 0); }
}

void APDisableAllNorseAgeTechs()
{
    if (trTechStatusActive(1, cTechClassicalAgeFreyja) == false) { trTechSetStatus(1, cTechClassicalAgeFreyja, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeForseti) == false) { trTechSetStatus(1, cTechClassicalAgeForseti, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeHeimdall) == false) { trTechSetStatus(1, cTechClassicalAgeHeimdall, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeUllr) == false) { trTechSetStatus(1, cTechClassicalAgeUllr, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeNorse) == false) { trTechSetStatus(1, cTechClassicalAgeNorse, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeBragi) == false) { trTechSetStatus(1, cTechHeroicAgeBragi, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeNjord) == false) { trTechSetStatus(1, cTechHeroicAgeNjord, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeSkadi) == false) { trTechSetStatus(1, cTechHeroicAgeSkadi, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeAegir) == false) { trTechSetStatus(1, cTechHeroicAgeAegir, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeNorse) == false) { trTechSetStatus(1, cTechHeroicAgeNorse, 0); }
    if (trTechStatusActive(1, cTechMythicAgeBaldr) == false) { trTechSetStatus(1, cTechMythicAgeBaldr, 0); }
    if (trTechStatusActive(1, cTechMythicAgeTyr) == false) { trTechSetStatus(1, cTechMythicAgeTyr, 0); }
    if (trTechStatusActive(1, cTechMythicAgeHel) == false) { trTechSetStatus(1, cTechMythicAgeHel, 0); }
    if (trTechStatusActive(1, cTechMythicAgeVidar) == false) { trTechSetStatus(1, cTechMythicAgeVidar, 0); }
    if (trTechStatusActive(1, cTechMythicAgeNorse) == false) { trTechSetStatus(1, cTechMythicAgeNorse, 0); }
}

void APApplyGreekMinorGods(int majorGod = 0, int ageCount = 0, int startingFloor = 0)
{
    // Force-disable all Greek age techs. APInitStartingAgeTechs has already set
    // floor tiers to status 2 (active); we only set tiers ABOVE the floor to
    // status 1 (researchable), based on the player's age unlock count.
    APForceDisableAllGreekAgeTechs();

    // Re-activate floor tiers (force-disable cleared them)
    // For floor tiers: only set the base age tech to status 2.
    // The seed-determined minor god tech is activated by APInitStartingAgeTechs().
    if (startingFloor >= 1) { trTechSetStatus(1, cTechClassicalAgeGreek, 2); }
    if (startingFloor >= 2) { trTechSetStatus(1, cTechHeroicAgeGreek,    2); }
    if (startingFloor >= 3) { trTechSetStatus(1, cTechMythicAgeGreek,    2); }

    // Set researchable (status 1) only for tiers above the starting floor
    if (ageCount >= 1 && startingFloor < 1)
    {
        trTechSetStatus(1, cTechClassicalAgeGreek, 1);
        if (majorGod == cAPMajorZeus)     { trTechSetStatus(1, cTechClassicalAgeAthena, 1); trTechSetStatus(1, cTechClassicalAgeHermes, 1); }
        if (majorGod == cAPMajorPoseidon) { trTechSetStatus(1, cTechClassicalAgeHermes, 1); trTechSetStatus(1, cTechClassicalAgeAres, 1);   }
        if (majorGod == cAPMajorHades)    { trTechSetStatus(1, cTechClassicalAgeAthena, 1); trTechSetStatus(1, cTechClassicalAgeAres, 1);    }
    }
    if (ageCount >= 2 && startingFloor < 2)
    {
        trTechSetStatus(1, cTechHeroicAgeGreek, 1);
        if (majorGod == cAPMajorZeus)     { trTechSetStatus(1, cTechHeroicAgeApollo, 1);     trTechSetStatus(1, cTechHeroicAgeDionysus, 1);   }
        if (majorGod == cAPMajorPoseidon) { trTechSetStatus(1, cTechHeroicAgeDionysus, 1);   trTechSetStatus(1, cTechHeroicAgeAphrodite, 1);  }
        if (majorGod == cAPMajorHades)    { trTechSetStatus(1, cTechHeroicAgeApollo, 1);     trTechSetStatus(1, cTechHeroicAgeAphrodite, 1);  }
    }
    if (ageCount >= 3 && startingFloor < 3)
    {
        trTechSetStatus(1, cTechMythicAgeGreek, 1);
        if (majorGod == cAPMajorZeus)     { trTechSetStatus(1, cTechMythicAgeHera, 1);        trTechSetStatus(1, cTechMythicAgeHephaestus, 1); }
        if (majorGod == cAPMajorPoseidon) { trTechSetStatus(1, cTechMythicAgeHephaestus, 1); trTechSetStatus(1, cTechMythicAgeArtemis, 1);    }
        if (majorGod == cAPMajorHades)    { trTechSetStatus(1, cTechMythicAgeHera, 1);        trTechSetStatus(1, cTechMythicAgeArtemis, 1);    }
    }
}

void APApplyEgyptianMinorGods(int majorGod = 0, int ageCount = 0, int startingFloor = 0)
{
    APForceDisableAllEgyptianAgeTechs();

    if (startingFloor >= 1) { trTechSetStatus(1, cTechClassicalAgeEgyptian, 2); }
    if (startingFloor >= 2) { trTechSetStatus(1, cTechHeroicAgeEgyptian,  2); }
    if (startingFloor >= 3) { trTechSetStatus(1, cTechMythicAgeEgyptian,  2); }

    if (ageCount >= 1 && startingFloor < 1)
    {
        trTechSetStatus(1, cTechClassicalAgeEgyptian, 1);
        if (majorGod == cAPMajorRa)   { trTechSetStatus(1, cTechClassicalAgeBast, 1);   trTechSetStatus(1, cTechClassicalAgePtah, 1);   }
        if (majorGod == cAPMajorIsis) { trTechSetStatus(1, cTechClassicalAgeAnubis, 1); trTechSetStatus(1, cTechClassicalAgeBast, 1);   }
        if (majorGod == cAPMajorSet)  { trTechSetStatus(1, cTechClassicalAgeAnubis, 1); trTechSetStatus(1, cTechClassicalAgeBast, 1);   }
    }
    if (ageCount >= 2 && startingFloor < 2)
    {
        trTechSetStatus(1, cTechHeroicAgeEgyptian, 1);
        if (majorGod == cAPMajorRa)   { trTechSetStatus(1, cTechHeroicAgeSekhmet, 1);   trTechSetStatus(1, cTechHeroicAgeSobek, 1);     }
        if (majorGod == cAPMajorIsis) { trTechSetStatus(1, cTechHeroicAgeSobek, 1);     trTechSetStatus(1, cTechHeroicAgeNephthys, 1);  }
        if (majorGod == cAPMajorSet)  { trTechSetStatus(1, cTechHeroicAgeSekhmet, 1);   trTechSetStatus(1, cTechHeroicAgeNephthys, 1);  }
    }
    if (ageCount >= 3 && startingFloor < 3)
    {
        trTechSetStatus(1, cTechMythicAgeEgyptian, 1);
        if (majorGod == cAPMajorRa)   { trTechSetStatus(1, cTechMythicAgeOsiris, 1);    trTechSetStatus(1, cTechMythicAgeHorus, 1);     }
        if (majorGod == cAPMajorIsis) { trTechSetStatus(1, cTechMythicAgeHorus, 1);     trTechSetStatus(1, cTechMythicAgeThoth, 1);     }
        if (majorGod == cAPMajorSet)  { trTechSetStatus(1, cTechMythicAgeOsiris, 1);    trTechSetStatus(1, cTechMythicAgeThoth, 1);     }
    }
}

void APApplyNorseMinorGods(int majorGod = 0, int ageCount = 0, int startingFloor = 0)
{
    APForceDisableAllNorseAgeTechs();

    if (startingFloor >= 1) { trTechSetStatus(1, cTechClassicalAgeNorse, 2); }
    if (startingFloor >= 2) { trTechSetStatus(1, cTechHeroicAgeNorse,    2); }
    if (startingFloor >= 3) { trTechSetStatus(1, cTechMythicAgeNorse,    2); }

    if (ageCount >= 1 && startingFloor < 1)
    {
        trTechSetStatus(1, cTechClassicalAgeNorse, 1);
        if (majorGod == cAPMajorOdin) { trTechSetStatus(1, cTechClassicalAgeFreyja, 1);   trTechSetStatus(1, cTechClassicalAgeHeimdall, 1); }
        if (majorGod == cAPMajorThor) { trTechSetStatus(1, cTechClassicalAgeFreyja, 1);   trTechSetStatus(1, cTechClassicalAgeForseti, 1);  }
        if (majorGod == cAPMajorLoki) { trTechSetStatus(1, cTechClassicalAgeForseti, 1);  trTechSetStatus(1, cTechClassicalAgeHeimdall, 1); }
    }
    if (ageCount >= 2 && startingFloor < 2)
    {
        trTechSetStatus(1, cTechHeroicAgeNorse, 1);
        if (majorGod == cAPMajorOdin) { trTechSetStatus(1, cTechHeroicAgeNjord, 1);  trTechSetStatus(1, cTechHeroicAgeSkadi, 1); }
        if (majorGod == cAPMajorThor) { trTechSetStatus(1, cTechHeroicAgeBragi, 1);  trTechSetStatus(1, cTechHeroicAgeSkadi, 1); }
        if (majorGod == cAPMajorLoki) { trTechSetStatus(1, cTechHeroicAgeBragi, 1);  trTechSetStatus(1, cTechHeroicAgeNjord, 1); }
    }
    if (ageCount >= 3 && startingFloor < 3)
    {
        trTechSetStatus(1, cTechMythicAgeNorse, 1);
        if (majorGod == cAPMajorOdin) { trTechSetStatus(1, cTechMythicAgeBaldr, 1); trTechSetStatus(1, cTechMythicAgeTyr, 1); }
        if (majorGod == cAPMajorThor) { trTechSetStatus(1, cTechMythicAgeBaldr, 1); trTechSetStatus(1, cTechMythicAgeTyr, 1); }
        if (majorGod == cAPMajorLoki) { trTechSetStatus(1, cTechMythicAgeTyr, 1);   trTechSetStatus(1, cTechMythicAgeHel, 1); }
    }
}

void APDisableAllAtlanteanAgeTechs()
{
    if (trTechStatusActive(1, cTechClassicalAgeAtlantean) == false) { trTechSetStatus(1, cTechClassicalAgeAtlantean, 0); }
    if (trTechStatusActive(1, cTechClassicalAgePrometheus) == false) { trTechSetStatus(1, cTechClassicalAgePrometheus, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeLeto) == false) { trTechSetStatus(1, cTechClassicalAgeLeto, 0); }
    if (trTechStatusActive(1, cTechClassicalAgeOceanus) == false) { trTechSetStatus(1, cTechClassicalAgeOceanus, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeAtlantean) == false) { trTechSetStatus(1, cTechHeroicAgeAtlantean, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeHyperion) == false) { trTechSetStatus(1, cTechHeroicAgeHyperion, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeRheia) == false) { trTechSetStatus(1, cTechHeroicAgeRheia, 0); }
    if (trTechStatusActive(1, cTechHeroicAgeTheia) == false) { trTechSetStatus(1, cTechHeroicAgeTheia, 0); }
    if (trTechStatusActive(1, cTechMythicAgeAtlantean) == false) { trTechSetStatus(1, cTechMythicAgeAtlantean, 0); }
    if (trTechStatusActive(1, cTechMythicAgeHelios) == false) { trTechSetStatus(1, cTechMythicAgeHelios, 0); }
    if (trTechStatusActive(1, cTechMythicAgeAtlas) == false) { trTechSetStatus(1, cTechMythicAgeAtlas, 0); }
    if (trTechStatusActive(1, cTechMythicAgeHekate) == false) { trTechSetStatus(1, cTechMythicAgeHekate, 0); }
}

void APApplyAtlanteanMinorGods(int majorGod = 0, int ageCount = 0, int startingFloor = 0)
{
    APForceDisableAllAtlanteanAgeTechs();

    if (startingFloor >= 1) { trTechSetStatus(1, cTechClassicalAgeAtlantean, 2); }
    if (startingFloor >= 2) { trTechSetStatus(1, cTechHeroicAgeAtlantean,  2); }
    if (startingFloor >= 3) { trTechSetStatus(1, cTechMythicAgeAtlantean,  2); }

    if (ageCount >= 1 && startingFloor < 1)
    {
        trTechSetStatus(1, cTechClassicalAgeAtlantean, 1);
        if (majorGod == cAPMajorKronos) { trTechSetStatus(1, cTechClassicalAgePrometheus, 1); trTechSetStatus(1, cTechClassicalAgeLeto, 1);    }
        if (majorGod == cAPMajorOranos) { trTechSetStatus(1, cTechClassicalAgePrometheus, 1); trTechSetStatus(1, cTechClassicalAgeOceanus, 1);  }
        if (majorGod == cAPMajorGaia)   { trTechSetStatus(1, cTechClassicalAgeLeto, 1);        trTechSetStatus(1, cTechClassicalAgeOceanus, 1);  }
    }
    if (ageCount >= 2 && startingFloor < 2)
    {
        trTechSetStatus(1, cTechHeroicAgeAtlantean, 1);
        if (majorGod == cAPMajorKronos) { trTechSetStatus(1, cTechHeroicAgeHyperion, 1); trTechSetStatus(1, cTechHeroicAgeRheia, 1);  }
        if (majorGod == cAPMajorOranos) { trTechSetStatus(1, cTechHeroicAgeHyperion, 1); trTechSetStatus(1, cTechHeroicAgeTheia, 1);  }
        if (majorGod == cAPMajorGaia)   { trTechSetStatus(1, cTechHeroicAgeRheia, 1);    trTechSetStatus(1, cTechHeroicAgeTheia, 1);  }
    }
    if (ageCount >= 3 && startingFloor < 3)
    {
        trTechSetStatus(1, cTechMythicAgeAtlantean, 1);
        if (majorGod == cAPMajorKronos) { trTechSetStatus(1, cTechMythicAgeHelios, 1); trTechSetStatus(1, cTechMythicAgeAtlas, 1);   }
        if (majorGod == cAPMajorOranos) { trTechSetStatus(1, cTechMythicAgeHelios, 1); trTechSetStatus(1, cTechMythicAgeHekate, 1);  }
        if (majorGod == cAPMajorGaia)   { trTechSetStatus(1, cTechMythicAgeAtlas, 1);  trTechSetStatus(1, cTechMythicAgeHekate, 1);  }
    }
}

int APGetStartingAgeCount(int scenarioId = 0)
{
    if (scenarioId == 1) { return 1; }
    if (scenarioId == 2) { return 0; }
    if (scenarioId == 3) { return 0; }
    if (scenarioId == 4) { return 1; }
    if (scenarioId == 5) { return 2; }
    if (scenarioId == 6) { return 2; }
    if (scenarioId == 7) { return 2; }
    if (scenarioId == 8) { return 1; }
    if (scenarioId == 9) { return 3; }
    if (scenarioId == 10) { return 0; }
    if (scenarioId == 11) { return 0; }
    if (scenarioId == 12) { return 0; }
    if (scenarioId == 13) { return 2; }
    if (scenarioId == 14) { return 2; }
    if (scenarioId == 15) { return 1; }
    if (scenarioId == 16) { return 3; }
    if (scenarioId == 17) { return 2; }
    if (scenarioId == 18) { return 1; }
    if (scenarioId == 19) { return 2; }
    if (scenarioId == 20) { return 2; }
    if (scenarioId == 21) { return 1; }
    if (scenarioId == 22) { return 0; }
    if (scenarioId == 23) { return 1; }
    if (scenarioId == 24) { return 1; }
    if (scenarioId == 25) { return 1; }
    if (scenarioId == 26) { return 1; }
    if (scenarioId == 27) { return 1; }
    if (scenarioId == 28) { return 2; }
    if (scenarioId == 29) { return 1; }
    if (scenarioId == 30) { return 1; }
    if (scenarioId == 31) { return 2; }
    if (scenarioId == 32) { return 2; }
    // New Atlantis (APScenarioIDs 501-512)
    if (scenarioId == 501) { return 2; }  // Heroic start
    if (scenarioId == 502) { return 0; }  // Archaic start
    if (scenarioId == 503) { return 2; }  // Heroic (no TC)
    if (scenarioId == 504) { return 2; }  // Heroic
    if (scenarioId == 505) { return 2; }  // Heroic
    if (scenarioId == 506) { return 3; }  // Mythic (no TC)
    if (scenarioId == 507) { return 2; }  // Heroic
    if (scenarioId == 508) { return 2; }  // Heroic
    if (scenarioId == 509) { return 2; }  // Heroic
    if (scenarioId == 510) { return 2; }  // Heroic
    if (scenarioId == 511) { return 3; }  // Mythic
    if (scenarioId == 512) { return 3; }  // Mythic (no TC)
    // The Golden Gift (APScenarioIDs 601-604)
    if (scenarioId == 601) { return 2; }  // Heroic
    if (scenarioId == 602) { return 2; }  // Heroic
    if (scenarioId == 603) { return 2; }  // Heroic
    if (scenarioId == 604) { return 3; }  // Mythic
    return 0;
}



void APApplyAgeUnlocks()
{
    int greekCount     = 0;
    int egyptianCount  = 0;
    int norseCount     = 0;
    int atlanteanCount = 0;
    int i = 0;
    int id = 0;

    for (i = 9; i < gAPItemCount; i++)
    {
        id = gAPItems[i];
        if (id == cGREEK_AGE_UNLOCK)      { greekCount++;     }
        if (id == cEGYPTIAN_AGE_UNLOCK)   { egyptianCount++;  }
        if (id == cNORSE_AGE_UNLOCK)      { norseCount++;     }
        if (id == cATLANTEAN_AGE_UNLOCK)  { atlanteanCount++; }
    }

    // scenarioFloor = the age tiers already active at scenario start.
    // APApply*MinorGods will:
    //   - Re-activate floor tiers as status 2 (after the force-disable clears them)
    //   - Set tiers above the floor as status 1 (researchable) only if playerCount allows
    //   - Leave everything else at status 0
    int scenarioFloor = APGetStartingAgeCount(gAPScenarioId);
    if (gAPMajorGod == cAPMajorZeus || gAPMajorGod == cAPMajorPoseidon || gAPMajorGod == cAPMajorHades)
    {
        APApplyGreekMinorGods(gAPMajorGod, greekCount, scenarioFloor);
        APForceDisableAllEgyptianAgeTechs();
        APForceDisableAllNorseAgeTechs();
        APForceDisableAllAtlanteanAgeTechs();
    }
    if (gAPMajorGod == cAPMajorIsis || gAPMajorGod == cAPMajorRa || gAPMajorGod == cAPMajorSet)
    {
        APApplyEgyptianMinorGods(gAPMajorGod, egyptianCount, scenarioFloor);
        APForceDisableAllGreekAgeTechs();
        APForceDisableAllNorseAgeTechs();
        APForceDisableAllAtlanteanAgeTechs();
    }
    if (gAPMajorGod == cAPMajorOdin || gAPMajorGod == cAPMajorThor || gAPMajorGod == cAPMajorLoki)
    {
        APApplyNorseMinorGods(gAPMajorGod, norseCount, scenarioFloor);
        APForceDisableAllGreekAgeTechs();
        APForceDisableAllEgyptianAgeTechs();
        APForceDisableAllAtlanteanAgeTechs();
    }
    if (gAPMajorGod == cAPMajorKronos || gAPMajorGod == cAPMajorOranos || gAPMajorGod == cAPMajorGaia)
    {
        APApplyAtlanteanMinorGods(gAPMajorGod, atlanteanCount, scenarioFloor);
        APForceDisableAllGreekAgeTechs();
        APForceDisableAllEgyptianAgeTechs();
        APForceDisableAllNorseAgeTechs();
    }


}


void APApplyHeroBoosts()
{
    int i   = 0;
    int id  = 0;

    // --- Accumulate stat totals ---
    int arkHp = 0; int arkAtk = 0; int arkRecharge = 0; int arkRegen = 0;
    int ajxHp = 0; int ajxAtk = 0; int ajxRecharge = 0; int ajxRegen = 0;
    int chiHp = 0; int chiAtk = 0; int chiRecharge = 0; int chiRegen = 0;
    int amHp  = 0; int amAtk  = 0; int amRecharge  = 0; int amRegen  = 0;
    int odyHp = 0; int odyAtk = 0; int odyRecharge = 0; int odyRegen  = 0;
    int regHp = 0; int regAtk = 0; int regRegen  = 0;

    // Special effect and action boost flags
    bool arkLifesteal        = false;
    bool arkPetrifyingShout  = false;
    bool arkAttackSpeed      = false;
    bool arkantosHousing     = false;
    bool ajxStunningBlow     = false;
    bool ajxSmitingStrikes   = false;
    bool ajxShieldBashAOE    = false;
    bool chiPoisonArrow      = false;
    bool chiCripplingFire    = false;
    bool chiShotgunSpecial   = false;
    bool amShockwaveJump     = false;
    bool amArmyOfTheDead     = false;
    bool amDivineSmite       = false;
    bool odyEntanglingShot   = false;
    bool odySwiftEscape      = false;
    bool odyPerfectAccuracy  = false;
    bool regFrostStrike       = false;
    bool regProjectile        = false;
    // Kastor
    int  kasHp            = 0;
    int  kasAtk           = 0;
    float kasRecharge     = 0.0;
    int  kasRegen         = 0;
    bool kasUndermineAttacks = false;
    bool kasSummonSoldiers   = false;
    bool kasIsAManor         = false;

    // Start at 6 — indices 0-5 are flags (campaign unlocks, campaign ID, godsanity)
    for (i = 9; i < gAPItemCount; i++)
    {
        id = gAPItems[i];

        // Arkantos
        if (id == cARKANTOS_HP_25)      { arkHp   += 25;  }
        if (id == cARKANTOS_HP_100)     { arkHp   += 100; }
        if (id == cARKANTOS_HP_200)     { arkHp   += 200; }
        if (id == cARKANTOS_ATK_1)      { arkAtk  += 1;   }
        if (id == cARKANTOS_ATK_3)      { arkAtk  += 3;   }
        if (id == cARKANTOS_ATK_10)     { arkAtk  += 10;  }
        if (id == cARKANTOS_RECHARGE_2)      { arkRecharge += 2;   }
        if (id == cARKANTOS_RECHARGE_5)      { arkRecharge += 5;   }
        if (id == cARKANTOS_REGEN_1)    { arkRegen += 1;  }
        if (id == cARKANTOS_REGEN_5)    { arkRegen += 5;  }
        if (id == cARKANTOS_LIFESTEAL)         { arkLifesteal       = true; }
        if (id == cARKANTOS_PETRIFYING_SHOUT)  { arkPetrifyingShout = true; }
        if (id == cARKANTOS_ATTACK_SPEED)      { arkAttackSpeed     = true; }
        if (id == cARKANTOS_HOUSING)               { arkantosHousing    = true; }

        // Ajax
        if (id == cAJAX_HP_25)          { ajxHp   += 25;  }
        if (id == cAJAX_HP_100)         { ajxHp   += 100; }
        if (id == cAJAX_HP_200)         { ajxHp   += 200; }
        if (id == cAJAX_ATK_1)          { ajxAtk  += 1;   }
        if (id == cAJAX_ATK_3)          { ajxAtk  += 3;   }
        if (id == cAJAX_ATK_10)         { ajxAtk  += 10;  }
        if (id == cAJAX_RECHARGE_2)          { ajxRecharge += 2;   }
        if (id == cAJAX_RECHARGE_5)          { ajxRecharge += 5;   }
        if (id == cAJAX_REGEN_1)        { ajxRegen += 1;  }
        if (id == cAJAX_REGEN_5)        { ajxRegen += 5;  }
        if (id == cAJAX_STUNNING_BLOW)    { ajxStunningBlow   = true; }
        if (id == cAJAX_SMITING_STRIKES)  { ajxSmitingStrikes = true; }
        if (id == cAJAX_SHIELD_BASH_AOE)  { ajxShieldBashAOE  = true; }

        // Chiron
        if (id == cCHIRON_HP_25)        { chiHp   += 25;  }
        if (id == cCHIRON_HP_100)       { chiHp   += 100; }
        if (id == cCHIRON_HP_200)       { chiHp   += 200; }
        if (id == cCHIRON_ATK_1)        { chiAtk  += 1;   }
        if (id == cCHIRON_ATK_3)        { chiAtk  += 3;   }
        if (id == cCHIRON_ATK_10)       { chiAtk  += 10;  }
        if (id == cCHIRON_RECHARGE_2)        { chiRecharge += 2;   }
        if (id == cCHIRON_RECHARGE_5)        { chiRecharge += 5;   }
        if (id == cCHIRON_REGEN_1)      { chiRegen += 1;  }
        if (id == cCHIRON_REGEN_5)      { chiRegen += 5;  }
        if (id == cCHIRON_POISON_ARROW)    { chiPoisonArrow   = true; }
        if (id == cCHIRON_CRIPPLING_FIRE)  { chiCripplingFire = true; }
        if (id == cCHIRON_SHOTGUN_SPECIAL) { chiShotgunSpecial = true; }

        // Amanra
        if (id == cAMANRA_HP_25)        { amHp   += 25;  }
        if (id == cAMANRA_HP_100)       { amHp   += 100; }
        if (id == cAMANRA_HP_200)       { amHp   += 200; }
        if (id == cAMANRA_ATK_1)        { amAtk  += 1;   }
        if (id == cAMANRA_ATK_3)        { amAtk  += 3;   }
        if (id == cAMANRA_ATK_10)       { amAtk  += 10;  }
        if (id == cAMANRA_RECHARGE_2)        { amRecharge += 2;   }
        if (id == cAMANRA_RECHARGE_5)        { amRecharge += 5;   }
        if (id == cAMANRA_REGEN_1)      { amRegen += 1;  }
        if (id == cAMANRA_REGEN_5)      { amRegen += 5;  }
        if (id == cAMANRA_SHOCKWAVE_JUMP)    { amShockwaveJump   = true; }
        if (id == cAMANRA_ARMY_OF_THE_DEAD)  { amArmyOfTheDead   = true; }
        if (id == cAMANRA_DIVINE_SMITE)      { amDivineSmite     = true; }

        // Odysseus
        if (id == cODYSSEUS_HP_25)      { odyHp   += 25;  }
        if (id == cODYSSEUS_HP_100)     { odyHp   += 100; }
        if (id == cODYSSEUS_HP_200)     { odyHp   += 200; }
        if (id == cODYSSEUS_ATK_1)      { odyAtk  += 1;   }
        if (id == cODYSSEUS_ATK_3)      { odyAtk  += 3;   }
        if (id == cODYSSEUS_ATK_10)     { odyAtk  += 10;  }
        if (id == cODYSSEUS_RECHARGE_2)      { odyRecharge += 2;   }
        if (id == cODYSSEUS_RECHARGE_5)      { odyRecharge += 5;   }
        if (id == cODYSSEUS_REGEN_1)    { odyRegen += 1;  }
        if (id == cODYSSEUS_REGEN_5)    { odyRegen += 5;  }
        if (id == cODYSSEUS_ENTANGLING_SHOT)  { odyEntanglingShot  = true; }
        if (id == cODYSSEUS_SWIFT_ESCAPE)     { odySwiftEscape     = true; }
        if (id == cODYSSEUS_PERFECT_ACCURACY) { odyPerfectAccuracy = true; }

        // Reginleif
        if (id == cREGINLEIF_HP_25)     { regHp   += 25;  }
        if (id == cREGINLEIF_HP_100)    { regHp   += 100; }
        if (id == cREGINLEIF_HP_200)    { regHp   += 200; }
        if (id == cREGINLEIF_ATK_1)     { regAtk  += 1;   }
        if (id == cREGINLEIF_ATK_3)     { regAtk  += 3;   }
        if (id == cREGINLEIF_ATK_10)    { regAtk  += 10;  }
        if (id == cREGINLEIF_REGEN_1)   { regRegen += 1;  }
        if (id == cREGINLEIF_REGEN_5)   { regRegen += 5;  }
        if (id == cREGINLEIF_FROST_STRIKE) { regFrostStrike = true; }
        if (id == cREGINLEIF_PROJECTILE)   { regProjectile  = true; }
        // Kastor
        if (id == cKASTOR_HP_25)            { kasHp      += 25;  }
        if (id == cKASTOR_HP_200)           { kasHp      += 200; }
        if (id == cKASTOR_ATK_1)            { kasAtk     += 1;   }
        if (id == cKASTOR_ATK_10)           { kasAtk     += 10;  }
        if (id == cKASTOR_RECHARGE_1)       { kasRecharge += 1.0; }
        if (id == cKASTOR_RECHARGE_3_5)     { kasRecharge += 3.5; }
        if (id == cKASTOR_REGEN_1)          { kasRegen   += 1;   }
        if (id == cKASTOR_REGEN_5)          { kasRegen   += 5;   }
        if (id == cKASTOR_UNDERMINE_ATTACKS){ kasUndermineAttacks = true; }
        if (id == cKASTOR_SUMMON_SOLDIERS)  { kasSummonSoldiers  = true; }
        if (id == cKASTOR_IS_A_MANOR)       { kasIsAManor        = true; }
    }

    // --- Apply stat boosts ---
    // Arkantos (hack)
    if (arkHp   > 0) { trModifyProtounitData("Arkantos",   1, 0,  arkHp,   0); }
    if (arkAtk  > 0) { trModifyProtounitAction("Arkantos",   "HandAttack", 1, 13, arkAtk,  0); }
    if (arkRecharge > 0) { trModifyProtounitData("Arkantos",   1, 9, -arkRecharge, 0); }
    if (arkRegen > 0){ trModifyProtounitData("Arkantos",   1, 17, arkRegen, 0); }

    // Ajax (SPC and Older variants)
    if (ajxHp   > 0) { trModifyProtounitData("AjaxSPC",   1, 0,  ajxHp,       0); trModifyProtounitData("AjaxOlder",   1, 0,  ajxHp,       0); }
    if (ajxAtk  > 0) { trModifyProtounitAction("AjaxSPC",  "HandAttack", 1, 13, ajxAtk, 0); trModifyProtounitAction("AjaxOlder", "HandAttack", 1, 13, ajxAtk, 0); }
    if (ajxRecharge > 0) { trModifyProtounitData("AjaxSPC", 1, 9, -ajxRecharge, 0); trModifyProtounitData("AjaxOlder", 1, 9, -ajxRecharge, 0); }
    if (ajxRegen > 0){ trModifyProtounitData("AjaxSPC",   1, 17, ajxRegen,    0); trModifyProtounitData("AjaxOlder",   1, 17, ajxRegen,    0); }

    // Chiron (pierce)
    if (chiHp   > 0) { trModifyProtounitData("ChironSPC",  1, 0,  chiHp,   0); }
    if (chiAtk  > 0) { trModifyProtounitAction("ChironSPC",  "RangedAttack", 1, 14, chiAtk, 0); }
    if (chiRecharge > 0) { trModifyProtounitData("ChironSPC",  1, 9, -chiRecharge, 0); }
    if (chiRegen > 0){ trModifyProtounitData("ChironSPC",  1, 17, chiRegen, 0); }

    // Amanra (both Amanra and AmanraOlder)
    if (amHp    > 0) { trModifyProtounitData("Amanra",     1, 0,  amHp,       0); trModifyProtounitData("AmanraOlder",     1, 0,  amHp,       0); }
    if (amAtk   > 0) { trModifyProtounitAction("Amanra",    "HandAttack", 1, 13, amAtk, 0); trModifyProtounitAction("AmanraOlder", "HandAttack", 1, 13, amAtk, 0); }
    if (amRecharge > 0) { trModifyProtounitData("Amanra",   1, 9, -amRecharge, 0); trModifyProtounitData("AmanraOlder",   1, 9, -amRecharge, 0); }
    if (amRegen  > 0){ trModifyProtounitData("Amanra",     1, 17, amRegen,    0); trModifyProtounitData("AmanraOlder",     1, 17, amRegen,    0); }

    // Odysseus (pierce)
    if (odyHp   > 0) { trModifyProtounitData("OdysseusSPC", 1, 0,  odyHp,   0); }
    if (odyAtk  > 0) { trModifyProtounitAction("OdysseusSPC", "RangedAttack", 1, 14, odyAtk, 0); }
    if (odyRecharge > 0) { trModifyProtounitData("OdysseusSPC", 1, 9, -odyRecharge, 0); }
    if (odyRegen > 0){ trModifyProtounitData("OdysseusSPC", 1, 17, odyRegen, 0); }

    // Reginleif (pierce)
    if (regHp   > 0) { trModifyProtounitData("Reginleif",  1, 0,  regHp,   0); }
    if (regAtk  > 0) { trModifyProtounitAction("Reginleif",  "RangedAttack", 1, 14, regAtk, 0); }
    if (regRegen > 0){ trModifyProtounitData("Reginleif",  1, 17, regRegen, 0); }

    // --- Apply special effects ---

    // Arkantos: Lifesteal (HandAttack, rate=150% of damage)
    if (arkLifesteal == true)
    {
        trProtounitActionSpecialEffect("Arkantos", "HandAttack", 1, 4, "Units", -1, 0.0, 1.5);
    }
    // Arkantos: Petrifying Shout (AutoBoost, FreezeStone+damage on hit, Unit, Divine damage, duration 2s, value 10)
    if (arkPetrifyingShout == true)
    {
        trProtounitActionSpecialEffect("Arkantos", "AutoBoost", 1, 103, "Unit", -1, 2.0, 10.0);
    }
    // Arkantos: Attack Speed (HandAttack ROF -0.25)
    if (arkAttackSpeed == true)
    {
        trModifyProtounitAction("Arkantos", "HandAttack", 1, 4, -0.25, 0);
    }
    // Arkantos is a House: gives Arkantos +10 Pop Cap Addition (increases population cap by 10)
    if (arkantosHousing == true)
    {
        trModifyProtounitData("Arkantos", 1, 7, 10, 0);
    }

    // Ajax: Stunning Blow (Gore action, stun duration 10s)
    if (ajxStunningBlow == true)
    {
        trProtounitActionSpecialEffect("AjaxSPC", "Gore", 1, 0, "All", -1, 10.0, 10.0);
        trProtounitActionSpecialEffect("AjaxOlder", "Gore", 1, 0, "All", -1, 10.0, 10.0);
    }
    // Ajax: Smiting Strikes (HandAttack, MaxHP modifier + VisualScale)
    if (ajxSmitingStrikes == true)
    {
        //HAX HP
        trProtounitActionSpecialEffectModifier("AjaxSPC",   "HandAttack", 1, 1, "Unit", 0.5, 1, -1);
        trProtounitActionSpecialEffectModifier("AjaxSPC",   "HandAttack", 1, 1, "Unit", -0.3, 49, 0);
        //VISUAL SCALE (AjaxOlder)
        trProtounitActionSpecialEffectModifier("AjaxOlder", "HandAttack", 1, 1, "Unit", 0.5, 1, -1);
        trProtounitActionSpecialEffectModifier("AjaxOlder", "HandAttack", 1, 1, "Unit", -0.3, 49, 0);
    }
    // Ajax: Shield Bash AOE (Gore, DamageArea +10)
    if (ajxShieldBashAOE == true)
    {
        trModifyProtounitAction("AjaxSPC",   "Gore", 1, 3, 10.0, 0);
        trModifyProtounitAction("AjaxOlder", "Gore", 1, 3, 10.0, 0);
    }

    // Chiron: Poison Arrow (RangedAttack, DamageOverTime duration 20s, value 20)
    if (chiPoisonArrow == true)
    {
        trProtounitActionSpecialEffect("ChironSPC", "RangedAttack", 1, 3, "All", -1, 20.0, 20.0);
    }
    // Chiron: Crippling Fire (RangedAttack, ROF StatModify on target duration 3s, value 3x slower)
    if (chiCripplingFire == true)
    {
        trProtounitActionSpecialEffectModifier("ChironSPC", "RangedAttack", 1, 1, "All", 3.0, 11, -1);
    }
    // Chiron: Shotgun Special (ChargedRangedAttack, NumProjectiles +15)
    if (chiShotgunSpecial == true)
    {
        trModifyProtounitAction("ChironSPC", "ChargedRangedAttack", 1, 8, 15.0, 0);
    }

    // Amanra: Shockwave Jump (JumpAttack, Throw duration 10s)
    if (amShockwaveJump == true)
    {
        trProtounitActionSpecialEffect("Amanra",      "JumpAttack", 1, 6, "All", -1, 10.0, 10.0);
        trProtounitActionSpecialEffect("AmanraOlder", "JumpAttack", 1, 6, "All", -1, 10.0, 10.0);
    }
    // Amanra: Army of the Dead (HandAttack, Reincarnation into Minion)
    if (amArmyOfTheDead == true)
    {
        trProtounitActionSpecialEffectProtoUnit("Amanra",      "HandAttack", 1, 5, "All", "Minion", 1.0, 1.0);
        trProtounitActionSpecialEffectProtoUnit("AmanraOlder", "HandAttack", 1, 5, "All", "Minion", 1.0, 1.0);
    }
    // Amanra: Divine Smite (HandAttack, DamageDivine +5)
    if (amDivineSmite == true)
    {
        trModifyProtounitAction("Amanra",      "HandAttack", 1, 16, 5.0, 0);
        trModifyProtounitAction("AmanraOlder", "HandAttack", 1, 16, 5.0, 0);
    }

    // Odysseus: Entangling Shot (ChargedRangedAttack, Stun duration 5s, value 5)
    if (odyEntanglingShot == true)
    {
        trProtounitActionSpecialEffect("OdysseusSPC", "ChargedRangedAttack", 1, 0, "All", -1, 5.0, 5.0);
    }
    // Odysseus: Swift Escape (RangedAttack, Speed StatModify on self duration 0.5s)
    if (odySwiftEscape == true)
    {
        trProtounitActionSpecialEffectModifier("OdysseusSPC", "RangedAttack", 1, 1, "All", 0.5, 0, -1);
    }
    // Odysseus: Perfect Accuracy (RangedAttack, PerfectAccuracy +5)
    if (odyPerfectAccuracy == true)
    {
        trModifyProtounitAction("OdysseusSPC", "RangedAttack", 1, 10, 5.0, 0);
    }

// Reginleif: Frost Strike (RangedAttack, Progressive ROF Freeze duration 3s, value 3)
    if (regFrostStrike == true)
    {
        trProtounitActionSpecialEffect("Reginleif", "RangedAttack", 1, 18, "All", -1, 3.0, 3.0);
    }
    // Reginleif: +1 Projectile (RangedAttack, NumProjectiles +1)
    if (regProjectile == true)
    {
        trModifyProtounitAction("Reginleif", "RangedAttack", 1, 8, 1.0, 0);
    }

    // --- Kastor ---
    // Stat boosts
    if (kasHp       > 0) { trModifyProtounitData("Kastor", 1, 0,  kasHp,       0); }
    if (kasAtk      > 0) { trModifyProtounitAction("Kastor", "HandAttack", 1, 13, kasAtk, 0); }
    if (kasRecharge > 0.0) { trModifyProtounitData("Kastor", 1, 9, -kasRecharge, 0); }
    if (kasRegen    > 0) { trModifyProtounitData("Kastor", 1, 17, kasRegen,    0); }

    // Kastor Undermines with Attacks: HandAttack applies DamageOverTime (Crush) to Buildings
    if (kasUndermineAttacks == true)
    {
        trProtounitActionSpecialEffect("Kastor", "HandAttack", 1, 3, "Building", -1, 13.0, 22.0);
        trProtounitActionSpecialEffectProtoUnit("Kastor", "HandAttack", 1, 14, "Building", "UndermineDamage", 1.0, 1.0);
    }

    // Kastor Can Summon Soldiers: adds Hoplite, Spearman, Berserk, Murmillo to Kastor's train list
    if (kasSummonSoldiers == true)
    {
        trProtounitAddTrain("Kastor", 1, "Hoplite",   2, 0);
        trProtounitAddTrain("Kastor", 1, "Spearman",  2, 1);
        trProtounitAddTrain("Kastor", 1, "Berserk",   2, 2);
        trProtounitAddTrain("Kastor", 1, "Murmillo",  2, 3);
    }

    // Kastor is a Manor: gives Kastor +20 population cap (double Arkantos is a House)
    if (kasIsAManor == true)
    {
        trModifyProtounitData("Kastor", 1, 7, 20, 0);
    }

}

// -----------------------------------------------------------------------
// Apply items rule
// -----------------------------------------------------------------------

rule APApplyItems
highFrequency
inactive
runImmediately
{
    APInitItems();

    // Extract campaign unlock flags and campaign ID from indices 0-4:
    //   [0]: 9001 = has Greek Scenarios,    9000 = no
    //   [1]: 9002 = has Egyptian Scenarios, 9000 = no
    //   [2]: 9003 = has Norse Scenarios,    9000 = no
    //   [3]: 9004 = has Atlantis Key,       9000 = no
    //   [4]: 9100 + campaign_id (for age unlock logic)
    //   [5]: 9010 = godsanity on,           9000 = no
    //   [6]: 9010 = gem_shop enabled,        9000 = no
    gHasGreek    = false;
    gHasEgyptian = false;
    gHasNorse    = false;
    gHasAtlantis = false;
    gHasNewAtlantis = false;
    gHasGoldenGift  = false;
    gAPRandomMajorGods = false;
    if (gAPItemCount > 6)
    {
        if (gAPItems[0] == 9001) { gHasGreek    = true; }
        if (gAPItems[1] == 9002) { gHasEgyptian = true; }
        if (gAPItems[2] == 9003) { gHasNorse    = true; }
        if (gAPItems[3] == 9004) { gHasAtlantis = true; }
        if (gAPItems[5] == 9010) { gAPRandomMajorGods = true; }
        // Scenario identity is driven by APScenarioID + APActivateScenario.
        // Keep slot 4 for compatibility, but do not overwrite gAPCampaignId here.
    }
    if (gAPItemCount > 8)
    {
        if (gAPItems[7] == 9005) { gHasNewAtlantis = true; }
        if (gAPItems[8] == 9006) { gHasGoldenGift  = true; }
    }

    APCheckCampaignLock();
    APAnnounceGod();
    APFindReinforcementSpawn();
    APApplyAgeUnlocks();
    APApplyHeroBoosts();

    int wood  = 0;
    int food  = 0;
    int gold  = 0;
    int favor = 0;

    // Villager carry capacity counters (stacks with multiple copies)
    int grkCarryFood = 0; int grkCarryWood = 0; int grkCarryGold = 0;
    int egyCarryFood = 0; int egyCarryWood = 0; int egyCarryGold = 0;
    int norCarryFood = 0; int norCarryWood = 0; int norCarryGold = 0;
    // Generic villager food cost reduction counter
    int villagerDiscount = 0;

    int itemId = 0;
    int i = 0;
    int j = 0;
    // Start at 6 — indices 0-5 are flags (campaign unlocks, campaign ID, godsanity)
    for (i = 9; i < gAPItemCount; i++)
    {
        itemId = gAPItems[i];

        if (itemId == cSTARTING_WOOD_SMALL)    { wood  += 30;  }
        if (itemId == cSTARTING_FOOD_SMALL)    { food  += 30;  }
        if (itemId == cSTARTING_GOLD_SMALL)    { gold  += 30;  }
        if (itemId == cSTARTING_FAVOR_SMALL)   { favor += 15;  }
        if (itemId == cSTARTING_WOOD_MEDIUM)   { wood  += 60;  }
        if (itemId == cSTARTING_FOOD_MEDIUM)   { food  += 60;  }
        if (itemId == cSTARTING_GOLD_MEDIUM)   { gold  += 60;  }
        if (itemId == cSTARTING_FAVOR_MEDIUM)  { favor += 30;  }
        if (itemId == cSTARTING_WOOD_LARGE)    { wood  += 120; }
        if (itemId == cSTARTING_FOOD_LARGE)    { food  += 120; }
        if (itemId == cSTARTING_GOLD_LARGE)    { gold  += 120; }
        if (itemId == cSTARTING_FAVOR_LARGE)   { favor += 60;  }

        if (itemId == cPASSIVE_WOOD_SMALL)    { trPlayerModifyResourceData(1, 2, 1, 0.5,  0); }
        if (itemId == cPASSIVE_FOOD_SMALL)    { trPlayerModifyResourceData(1, 2, 2, 0.5,  0); }
        if (itemId == cPASSIVE_GOLD_SMALL)    { trPlayerModifyResourceData(1, 2, 0, 0.5,  0); }
        if (itemId == cPASSIVE_FAVOR_SMALL)   { trPlayerModifyResourceData(1, 2, 3, 0.25, 0); }
        if (itemId == cPASSIVE_WOOD_LARGE)    { trPlayerModifyResourceData(1, 2, 1, 2.0,  0); }
        if (itemId == cPASSIVE_FOOD_LARGE)    { trPlayerModifyResourceData(1, 2, 2, 2.0,  0); }
        if (itemId == cPASSIVE_GOLD_LARGE)    { trPlayerModifyResourceData(1, 2, 0, 2.0,  0); }
        if (itemId == cPASSIVE_FAVOR_LARGE)   { trPlayerModifyResourceData(1, 2, 3, 1.0,  0); }

        if (itemId == cREINFORCEMENT_ANUBITES)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Anubite", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_HOPLITE)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Hoplite", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_DWARF)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Dwarf", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_MERCENARY)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Mercenary", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_MERCENARY_CAV)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("MercenaryCavalry", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_AUTOMATON)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Automaton", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_WADJET)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Wadjet", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_BERSERK)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Berserk", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_SLINGER)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Slinger", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_TURMA)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Turma", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_KATASKOPOS)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Kataskopos", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_FIRE_GIANT)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("FireGiant", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_VILLAGER)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("VillagerGreek", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_CITIZEN)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("VillagerAtlantean", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_BATTLE_BOAR)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("BattleBoar", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_ROC)
        {
            if (gAPScenarioId != 12)
            {
                for (j = 0; j < 2; j++)
                {
                    trUnitCreateFromSource("Roc", gReinforcementSpawnID, gReinforcementSpawnID, 1);
                }
            }
        }
        if (itemId == cREINFORCEMENT_PRIEST)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Priest", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_CALADRIA)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Caladria", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_RAIDING_CAVALRY)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("RaidingCavalry", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_ORACLE)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Oracle", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_CYCLOPS)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Cyclops", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_TROLL)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Troll", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_BEHEMOTH)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Behemoth", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_LAMPADES)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Lampades", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_PHOENIX)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Phoenix", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_COLOSSUS)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Colossus", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREGINLEIF_JOINS)
        {
            // Reginleif joins naturally on scenarios 26-30; skip spawn there
            if (gAPScenarioId < 26 || gAPScenarioId > 30)
            {
                trUnitCreateFromSource("Reginleif", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cODYSSEUS_JOINS)
        {
            // Odysseus joins naturally on scenarios 4, 5, 6, 30; skip spawn there
            if (gAPScenarioId != 4 && gAPScenarioId != 5 && gAPScenarioId != 6 && gAPScenarioId != 30)
            {
                trUnitCreateFromSource("OdysseusSPC", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cKASTOR_JOINS)
        {
            // Kastor is already present in The New Atlantis scenarios 1-4 and 6-12;
            // only NA5 (505) lacks him. Spawn him in every scenario except those.
            if (gAPScenarioId != 501 && gAPScenarioId != 502 && gAPScenarioId != 503 &&
                gAPScenarioId != 504 && gAPScenarioId != 506 && gAPScenarioId != 507 &&
                gAPScenarioId != 508 && gAPScenarioId != 509 && gAPScenarioId != 510 &&
                gAPScenarioId != 511 && gAPScenarioId != 512)
            {
                trUnitCreateFromSource("Kastor", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_RELIC_MONKEY)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("RelicMonkey", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_PEGASUS)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Pegasus", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_HYENA)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("HyenaOfSet", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_HIPPO)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("HippopotamusOfSet", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_GOLDEN_LION)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("RelicGoldenLion", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }
        if (itemId == cREINFORCEMENT_NORSE_GATHERER)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("VillagerNorse", gReinforcementSpawnID, gReinforcementSpawnID, 1);
            }
        }


        // Villager carry capacity
        if (itemId == cGREEK_CARRY_FOOD)    { grkCarryFood++; }
        if (itemId == cGREEK_CARRY_WOOD)    { grkCarryWood++; }
        if (itemId == cGREEK_CARRY_GOLD)    { grkCarryGold++; }
        if (itemId == cEGYPTIAN_CARRY_FOOD) { egyCarryFood++; }
        if (itemId == cEGYPTIAN_CARRY_WOOD) { egyCarryWood++; }
        if (itemId == cEGYPTIAN_CARRY_GOLD) { egyCarryGold++; }
        if (itemId == cNORSE_CARRY_FOOD)    { norCarryFood++; }
        if (itemId == cNORSE_CARRY_WOOD)    { norCarryWood++; }
        if (itemId == cNORSE_CARRY_GOLD)    { norCarryGold++; }
        // Generic villager food cost discount (all villager types)
        if (itemId == cVILLAGER_DISCOUNT) { villagerDiscount++; }
    }


    if (wood  > 0) { trPlayerGrantResources(1, "Wood",  wood);  }
    if (food  > 0) { trPlayerGrantResources(1, "Food",  food);  }
    if (gold  > 0) { trPlayerGrantResources(1, "Gold",  gold);  }
    if (favor > 0) { trPlayerGrantResources(1, "Favor", favor); }

    // Villager carry capacity — cXSPUResourceEffectCarryCapacity=1
    if (grkCarryFood > 0) { trModifyProtounitResource("VillagerGreek",    "food", 1, 1, 10.0 * grkCarryFood, 0); }
    if (grkCarryWood > 0) { trModifyProtounitResource("VillagerGreek",    "wood", 1, 1, 10.0 * grkCarryWood, 0); }
    if (grkCarryGold > 0) { trModifyProtounitResource("VillagerGreek",    "gold", 1, 1, 10.0 * grkCarryGold, 0); }
    if (egyCarryFood > 0) { trModifyProtounitResource("VillagerEgyptian", "food", 1, 1, 10.0 * egyCarryFood, 0); }
    if (egyCarryWood > 0) { trModifyProtounitResource("VillagerEgyptian", "wood", 1, 1, 10.0 * egyCarryWood, 0); }
    if (egyCarryGold > 0) { trModifyProtounitResource("VillagerEgyptian", "gold", 1, 1, 10.0 * egyCarryGold, 0); }
    if (norCarryFood > 0) { trModifyProtounitResource("VillagerNorse",    "food", 1, 1, 10.0 * norCarryFood, 0); }
    if (norCarryWood > 0) { trModifyProtounitResource("VillagerNorse",    "wood", 1, 1, 10.0 * norCarryWood, 0); }
    if (norCarryGold > 0) { trModifyProtounitResource("VillagerNorse",    "gold", 1, 1, 10.0 * norCarryGold, 0); }

    // Generic villager food cost reduction — applies -5 per copy to all 4 villager types
    // cXSPUResourceEffectCost=0
    if (villagerDiscount > 0)
    {
        float _disc = -5.0 * villagerDiscount;
        trModifyProtounitResource("VillagerGreek",      "food", 1, 0, _disc, 0);
        trModifyProtounitResource("VillagerEgyptian",   "food", 1, 0, _disc, 0);
        trModifyProtounitResource("VillagerNorse",      "food", 1, 0, _disc, 0);
        trModifyProtounitResource("VillagerAtlantean",  "food", 1, 0, _disc, 0);
    }

    xsDisableSelf();
}

// -----------------------------------------------------------------------
// APRelicTrickleEnforce relicfix_v3 - adjusts player 1 trickle rates based on the
// FIXED v2: avoids the previous short delta variable name and unary-negative loop bounds.
// number of relics currently captured (garrisoned in any p1 temple, or
// being held by a hero — both states count as "captured" for this item).
// Per-relic contributions stack across all four trickle items received.
// We re-compute the desired trickle each tick and apply only the delta
// from the previously-applied amount via trPlayerModifyResourceData
// (relativity=0 is additive). Includes Relic, AbstractRelic and any
// SPC relic variants visible to AOM:Retold's unit-type lookup.
// -----------------------------------------------------------------------

int APCountPlayer1RelicsByType(string relicType = "")
{
    xsSetContextPlayer(1);

    int tid = kbGetUnitTypeID(relicType);
    if (tid <= 0)
    {
        xsSetContextPlayer(12);
        return (0);
    }

    int qid = kbUnitQueryCreate("APRelicCountQ" + relicType);
    kbUnitQuerySetPlayerID(qid, 1);
    kbUnitQuerySetUnitType(qid, tid);
    kbUnitQuerySetState(qid, cUnitStateAlive);
    kbUnitQueryExecute(qid);

    int[] res = kbUnitQueryGetResults(qid);
    int count = res.size();
    kbUnitQueryDestroy(qid);

    xsSetContextPlayer(12);
    return (count);
}

int APCountPlayer1Relics()
{
    int abstractCount = APCountPlayer1RelicsByType("AbstractRelic");
    if (abstractCount > 0)
    {
        return (abstractCount);
    }

    int total = 0;
    total = total + APCountPlayer1RelicsByType("Relic");
    total = total + APCountPlayer1RelicsByType("RelicMinor");
    total = total + APCountPlayer1RelicsByType("RelicSPC");

    return (total);
}

// Formats a float to at most 1 decimal place, stripping trailing zero decimals.
// Used for trickle amounts in the relic notification chat.
string APFormatFloat(float val = 0.0)
{
    // XS has no cast operators. Extract integer part via subtraction loop.
    // Safe for the small trickle totals this function is called with.
    int   _i   = 0;
    float _rem = val;
    while (_rem >= 1.0) { _rem = _rem - 1.0; _i = _i + 1; }
    // All trickle values are multiples of 0.5, so _rem is either ~0 or ~0.5.
    if (_rem > 0.25)
    {
        return ("" + _i + ".5");
    }
    return ("" + _i);
}

rule APRelicTrickleEnforce
highFrequency
inactive
{
    if (gAPItemCount <= 9) { return; }

    // Sum per-resource per-relic amounts from received items.
    float perFood  = 0.0;
    float perWood  = 0.0;
    float perGold  = 0.0;
    float perFavor = 0.0;

    // Boolean "have-item" flags for the relic effects. Multiple copies of a
    // given effect item are not distinguished — having the item enables the
    // per-relic effect; extra copies do not multiply.
    bool hasLOS        = false;
    bool hasRegen      = false;
    bool hasSpeed      = false;
    bool hasHP         = false;
    bool hasPop        = false;
    bool hasGoldCost   = false;
    bool hasWoodCost   = false;
    bool hasFavorCost  = false;
    bool hasFoodCost   = false;
    bool hasBuildSpeed = false;

    int j = 0;
    int id = 0;
    for (j = 9; j < gAPItemCount; j++)
    {
        id = gAPItems[j];
        if (id == cRELIC_TRICKLE_FOOD)  { perFood  = perFood  + 2.0; }
        if (id == cRELIC_TRICKLE_WOOD)  { perWood  = perWood  + 2.0; }
        if (id == cRELIC_TRICKLE_GOLD)  { perGold  = perGold  + 2.0; }
        if (id == cRELIC_TRICKLE_FAVOR) { perFavor = perFavor + 1.0; }
        if (id == cRELIC_EFFECT_LOS)         { hasLOS        = true; }
        if (id == cRELIC_EFFECT_REGEN)       { hasRegen      = true; }
        if (id == cRELIC_EFFECT_SPEED)       { hasSpeed      = true; }
        if (id == cRELIC_EFFECT_HP)          { hasHP         = true; }
        if (id == cRELIC_EFFECT_POP)         { hasPop        = true; }
        if (id == cRELIC_EFFECT_GOLD_COST)   { hasGoldCost   = true; }
        if (id == cRELIC_EFFECT_WOOD_COST)   { hasWoodCost   = true; }
        if (id == cRELIC_EFFECT_FAVOR_COST)  { hasFavorCost  = true; }
        if (id == cRELIC_EFFECT_FOOD_COST)   { hasFoodCost   = true; }
        if (id == cRELIC_EFFECT_BUILD_SPEED) { hasBuildSpeed = true; }
    }

    int relicCount = APCountPlayer1Relics();

    // ----- Resource trickles (additive trickle rate) -----
    float wantFood  = perFood  * relicCount;
    float wantWood  = perWood  * relicCount;
    float wantGold  = perGold  * relicCount;
    float wantFavor = perFavor * relicCount;

    float dFood  = wantFood  - gAPRelicTrickleAppliedFood;
    float dWood  = wantWood  - gAPRelicTrickleAppliedWood;
    float dGold  = wantGold  - gAPRelicTrickleAppliedGold;
    float dFavor = wantFavor - gAPRelicTrickleAppliedFavor;

    // Resource IDs: GOLD=0, WOOD=1, FOOD=2, FAVOR=3. Field=2 = trickle rate.
    if (dFood  != 0.0) { trPlayerModifyResourceData(1, 2, 2, dFood,  0); gAPRelicTrickleAppliedFood  = wantFood;  }
    if (dWood  != 0.0) { trPlayerModifyResourceData(1, 2, 1, dWood,  0); gAPRelicTrickleAppliedWood  = wantWood;  }
    if (dGold  != 0.0) { trPlayerModifyResourceData(1, 2, 0, dGold,  0); gAPRelicTrickleAppliedGold  = wantGold;  }
    if (dFavor != 0.0) { trPlayerModifyResourceData(1, 2, 3, dFavor, 0); gAPRelicTrickleAppliedFavor = wantFavor; }

    // ----- Per-relic stat / cost / build effects -----
    // For each effect, the desired "applied count" is relicCount when the item
    // is owned, else 0. We then drive the applied count toward the target by
    // replaying the underlying tr* call (additive: scale by apRelicDelta; multiplicative:
    // call apRelicDelta times, or call the inverse value when reducing).

    int targLOS        = 0; if (hasLOS)        { targLOS        = relicCount; }
    int targRegen      = 0; if (hasRegen)      { targRegen      = relicCount; }
    int targSpeed      = 0; if (hasSpeed)      { targSpeed      = relicCount; }
    int targHP         = 0; if (hasHP)         { targHP         = relicCount; }
    int targPop        = 0; if (hasPop)        { targPop        = relicCount; }
    int targGoldCost   = 0; if (hasGoldCost)   { targGoldCost   = relicCount; }
    int targWoodCost   = 0; if (hasWoodCost)   { targWoodCost   = relicCount; }
    int targFavorCost  = 0; if (hasFavorCost)  { targFavorCost  = relicCount; }
    int targFoodCost   = 0; if (hasFoodCost)   { targFoodCost   = relicCount; }
    int targBuildSpeed = 0; if (hasBuildSpeed) { targBuildSpeed = relicCount; }

    int apRelicDelta = 0;
    int k = 0;
    int undoCount = 0;

    // Additive: LOS +4 per relic. Field 2 = LOS.
    apRelicDelta = targLOS - gAPRelicEffAppliedLOS;
    if (apRelicDelta != 0)
    {
        trModifyProtounitData("All", 1, 2, 4.0 * apRelicDelta, 0);
        gAPRelicEffAppliedLOS = targLOS;
    }

    // Additive: Regen +1 per relic. Field 17 = regen rate.
    apRelicDelta = targRegen - gAPRelicEffAppliedRegen;
    if (apRelicDelta != 0)
    {
        trModifyProtounitData("All", 1, 17, 1.0 * apRelicDelta, 0);
        gAPRelicEffAppliedRegen = targRegen;
    }

    // Multiplicative: Speed x1.05 per relic. Field 1 = speed. Apply 1.05^apRelicDelta
    // (or 1/1.05 when reducing) by repeated invocation.
    apRelicDelta = targSpeed - gAPRelicEffAppliedSpeed;
    if (apRelicDelta > 0)
    {
        k = 0;
        while (k < apRelicDelta)
        {
            trModifyProtounitData("Unit", 1, 1, 1.05, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedSpeed = targSpeed;
    }
    else if (apRelicDelta < 0)
    {
        k = 0;
        undoCount = 0 - apRelicDelta;
        while (k < undoCount)
        {
            trModifyProtounitData("Unit", 1, 1, 1.0 / 1.05, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedSpeed = targSpeed;
    }

    // Multiplicative: Max HP x1.10 per relic. Field 0 = max hitpoints.
    apRelicDelta = targHP - gAPRelicEffAppliedHP;
    if (apRelicDelta > 0)
    {
        k = 0;
        while (k < apRelicDelta)
        {
            trModifyProtounitData("All", 1, 0, 1.10, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedHP = targHP;
    }
    else if (apRelicDelta < 0)
    {
        k = 0;
        undoCount = 0 - apRelicDelta;
        while (k < undoCount)
        {
            trModifyProtounitData("All", 1, 0, 1.0 / 1.10, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedHP = targHP;
    }

    // Additive: Population -1 per relic. Two related fields (6 and 7) per the
    // requested triggers — apply both each tick so the population display and
    // cap accounting stay in sync.
    apRelicDelta = targPop - gAPRelicEffAppliedPop;
    if (apRelicDelta != 0)
    {
        trModifyProtounitData("Unit", 1, 7, 0.0 - (1.0 * apRelicDelta), 0);
        trModifyProtounitData("Unit", 1, 6, 0.0 - (1.0 * apRelicDelta), 0);
        gAPRelicEffAppliedPop = targPop;
    }

    // Multiplicative cost reductions: x0.95 per relic on Gold / Wood / Favor /
    // Food; field index 0 on resource means "cost".
    apRelicDelta = targGoldCost - gAPRelicEffAppliedGoldCost;
    if (apRelicDelta > 0)
    {
        k = 0;
        while (k < apRelicDelta)
        {
            trModifyProtounitResource("All", "Gold", 1, 0, 0.95, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedGoldCost = targGoldCost;
    }
    else if (apRelicDelta < 0)
    {
        k = 0;
        undoCount = 0 - apRelicDelta;
        while (k < undoCount)
        {
            trModifyProtounitResource("All", "Gold", 1, 0, 1.0 / 0.95, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedGoldCost = targGoldCost;
    }

    apRelicDelta = targWoodCost - gAPRelicEffAppliedWoodCost;
    if (apRelicDelta > 0)
    {
        k = 0;
        while (k < apRelicDelta)
        {
            trModifyProtounitResource("All", "Wood", 1, 0, 0.95, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedWoodCost = targWoodCost;
    }
    else if (apRelicDelta < 0)
    {
        k = 0;
        undoCount = 0 - apRelicDelta;
        while (k < undoCount)
        {
            trModifyProtounitResource("All", "Wood", 1, 0, 1.0 / 0.95, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedWoodCost = targWoodCost;
    }

    apRelicDelta = targFavorCost - gAPRelicEffAppliedFavorCost;
    if (apRelicDelta > 0)
    {
        k = 0;
        while (k < apRelicDelta)
        {
            trModifyProtounitResource("All", "Favor", 1, 0, 0.95, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedFavorCost = targFavorCost;
    }
    else if (apRelicDelta < 0)
    {
        k = 0;
        undoCount = 0 - apRelicDelta;
        while (k < undoCount)
        {
            trModifyProtounitResource("All", "Favor", 1, 0, 1.0 / 0.95, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedFavorCost = targFavorCost;
    }

    apRelicDelta = targFoodCost - gAPRelicEffAppliedFoodCost;
    if (apRelicDelta > 0)
    {
        k = 0;
        while (k < apRelicDelta)
        {
            trModifyProtounitResource("All", "Food", 1, 0, 0.95, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedFoodCost = targFoodCost;
    }
    else if (apRelicDelta < 0)
    {
        k = 0;
        undoCount = 0 - apRelicDelta;
        while (k < undoCount)
        {
            trModifyProtounitResource("All", "Food", 1, 0, 1.0 / 0.95, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedFoodCost = targFoodCost;
    }

    // Multiplicative: Build time x0.90 per relic on Building. Field 4 = build
    // points / build time multiplier.
    apRelicDelta = targBuildSpeed - gAPRelicEffAppliedBuildSpeed;
    if (apRelicDelta > 0)
    {
        k = 0;
        while (k < apRelicDelta)
        {
            trModifyProtounitData("Building", 1, 4, 0.9, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedBuildSpeed = targBuildSpeed;
    }
    else if (apRelicDelta < 0)
    {
        k = 0;
        undoCount = 0 - apRelicDelta;
        while (k < undoCount)
        {
            trModifyProtounitData("Building", 1, 4, 1.0 / 0.9, 2);
            k = k + 1;
        }
        gAPRelicEffAppliedBuildSpeed = targBuildSpeed;
    }

    // ----- Relic count change notification -----
    if (relicCount != gAPRelicLastCount)
    {
        gAPRelicLastCount = relicCount;

        bool _anyEffect = false;
        if (perFood  > 0.0) { _anyEffect = true; }
        if (perWood  > 0.0) { _anyEffect = true; }
        if (perGold  > 0.0) { _anyEffect = true; }
        if (perFavor > 0.0) { _anyEffect = true; }
        if (hasLOS)        { _anyEffect = true; }
        if (hasRegen)      { _anyEffect = true; }
        if (hasSpeed)      { _anyEffect = true; }
        if (hasHP)         { _anyEffect = true; }
        if (hasPop)        { _anyEffect = true; }
        if (hasGoldCost)   { _anyEffect = true; }
        if (hasWoodCost)   { _anyEffect = true; }
        if (hasFavorCost)  { _anyEffect = true; }
        if (hasFoodCost)   { _anyEffect = true; }
        if (hasBuildSpeed) { _anyEffect = true; }

        if (_anyEffect && relicCount > 0)
        {
            string _msg   = "";
            bool   _first = true;
            string _pfx   = "You have " + relicCount + " relic(s) ";
            string _and   = "\nand ";
            string _line  = "";

            if (perFood > 0.0)
            {
                _line = "granting +" + APFormatFloat(perFood * relicCount) + " Food Trickle";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (perWood > 0.0)
            {
                _line = "granting +" + APFormatFloat(perWood * relicCount) + " Wood Trickle";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (perGold > 0.0)
            {
                _line = "granting +" + APFormatFloat(perGold * relicCount) + " Gold Trickle";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (perFavor > 0.0)
            {
                _line = "granting +" + APFormatFloat(perFavor * relicCount) + " Favor Trickle";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasLOS)
            {
                _line = "granting +" + (relicCount * 4) + " Line of Sight to everything";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasRegen)
            {
                _line = "granting +" + relicCount + " Regeneration to everything";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasSpeed)
            {
                _line = "granting all units +" + (relicCount * 5) + "% Speed";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasHP)
            {
                _line = "granting everything +" + (relicCount * 10) + "% Max HP";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasPop)
            {
                _line = "reducing all unit population slots by " + relicCount;
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasGoldCost)
            {
                _line = "reducing all Gold costs by " + (relicCount * 5) + "%";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasWoodCost)
            {
                _line = "reducing all Wood costs by " + (relicCount * 5) + "%";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasFavorCost)
            {
                _line = "reducing all Favor costs by " + (relicCount * 5) + "%";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasFoodCost)
            {
                _line = "reducing all Food costs by " + (relicCount * 5) + "%";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }
            if (hasBuildSpeed)
            {
                _line = "making buildings build " + (relicCount * 10) + "% faster";
                if (_first) { _msg = _pfx + _line; _first = false; } else { _msg = _msg + _and + _line; }
            }

            trChatSend(0, _msg);
        }
    }
}

// -----------------------------------------------------------------------
// APEnforceAgeLocks — continuously re-applies age unlock state.
// AOM auto-enables next-tier age techs once prereqs are met (researching
// Classical re-enables Heroic). One-shot disable in APApplyItems isn't
// enough; we re-disable each tick.
// APEnforceAgeLocks is intentionally unused.
// APApplyAgeUnlocks() must only run once, from APApplyItems.
// Re-running it re-applies generic age techs and stacks effects like Berserk LOS
// and dock myth-unit samples.
// -----------------------------------------------------------------------
rule APEnforceAgeLocks
inactive
minInterval 1
{
    APApplyAgeUnlocks();
    xsDisableSelf();
    //trDisableTrigger(APEnforceAgeLocks);
}

// -----------------------------------------------------------------------
// APAnnounceMaxAge — debug chat showing the max age the player can reach
// for their assigned civilization. Fires once at scenario start.
// -----------------------------------------------------------------------
rule APAnnounceMaxAge
highFrequency
inactive
{
    int _ageCount = 0;
    int _ai = 0;
    int _aid = 0;
    string _civ = "";
    if (gAPMajorGod == cAPMajorZeus || gAPMajorGod == cAPMajorPoseidon || gAPMajorGod == cAPMajorHades) { _civ = "Greek"; }
    if (gAPMajorGod == cAPMajorIsis || gAPMajorGod == cAPMajorRa       || gAPMajorGod == cAPMajorSet)   { _civ = "Egyptian"; }
    if (gAPMajorGod == cAPMajorOdin || gAPMajorGod == cAPMajorThor     || gAPMajorGod == cAPMajorLoki)  { _civ = "Norse"; }
    if (gAPMajorGod == cAPMajorKronos || gAPMajorGod == cAPMajorOranos || gAPMajorGod == cAPMajorGaia)  { _civ = "Atlantean"; }

    for (_ai = 9; _ai < gAPItemCount; _ai++)
    {
        _aid = gAPItems[_ai];
        if (_civ == "Greek"     && _aid == cGREEK_AGE_UNLOCK)     { _ageCount++; }
        if (_civ == "Egyptian"  && _aid == cEGYPTIAN_AGE_UNLOCK)  { _ageCount++; }
        if (_civ == "Norse"     && _aid == cNORSE_AGE_UNLOCK)     { _ageCount++; }
        if (_civ == "Atlantean" && _aid == cATLANTEAN_AGE_UNLOCK) { _ageCount++; }
    }

    int _floor = APGetStartingAgeCount(gAPScenarioId);
    int _max = _floor;
    if (_ageCount > _max) { _max = _ageCount; }
    if (_max > 3) { _max = 3; }

    string _ageName = "Archaic";
    if (_max == 1) { _ageName = "Classical"; }
    if (_max == 2) { _ageName = "Heroic"; }
    if (_max == 3) { _ageName = "Mythic"; }

    trChatSend(0, "AP DEBUG: Max reachable age = " + _ageName + " (civ=" + _civ + ", floor=" + _floor + ", unlocks=" + _ageCount + ")");
    xsDisableSelf();
}

// -----------------------------------------------------------------------
// Trap queue — populated by APTrapQueueInit() in aom_state.xs.
// Persists across scenarios; client counts AP_TRAP_FIRED echoes at scenario
// end to know how many traps to pop from its queue.
// All targeting and execution happens here in trigger XS context.
// -----------------------------------------------------------------------


// -----------------------------------------------------------------------
// Building transformation for Random Major Gods
// Data is loaded from aom_state.xs APLoadBuildingTransforms().
// Execution uses tr* functions available in trigger XS context.
// -----------------------------------------------------------------------

rule APTrapTimer
highFrequency
inactive
{
    if (gAPTrapPending == false) { return; }
    if (gAPTrapQueueSize <= 0)  { gAPTrapPending = false; return; }
    if (xsGetTime() < gAPTrapFireTime) { return; }

    int trapType = gAPTrapQueue[0];
    APTrapPop();
    APTrapScheduleNext(false);
    APTrapExecuteTrap(trapType);
    gAPTrapsFiredCount++;
    trQuestVarSet("APTrapsFiredThisScenario", gAPTrapsFiredCount);
}

// -----------------------------------------------------------------------
// Random God Power tier system
// Quest vars rand_gp_1..4 are set in scenario editor (or by external triggers).
// When a QV > 0, grant the predetermined god power for that tier `n` times,
// then clear the QV. The chosen god powers are populated per scenario by
// APInitGodPowers() in aom_state.xs from generation-time slot_data.
// Cooldown scales with tier: 45s, 90s, 135s, 180s.
// repeatable=true, useCost=true.
// -----------------------------------------------------------------------

void APGrantRandGP(string powerName = "", int count = 0, int cooldown = 45)
{
    if (powerName == "" || count <= 0)
    {
        return;
    }

    trPlayerTechTreeEnabledGodPowers(1, true);
    trGodPowerEnableBlocking(false);
    trGodPowerGrant(1, powerName, count, cooldown, true, true);
    trGodPowerEnableBlocking(true);
}

rule APRandGP1
minInterval 1
inactive
{
    int n = trQuestVarGet("rand_gp_1");
    if (n <= 0) { return; }
    if (gAPRandGP1 == "")
    {
        trQuestVarSet("rand_gp_1", 0);
        return;
    }
    APGrantRandGP(gAPRandGP1, n, 45);
    trQuestVarSet("rand_gp_1", 0);
}

rule APRandGP2
minInterval 1
inactive
{
    int n = trQuestVarGet("rand_gp_2");
    if (n <= 0) { return; }
    if (gAPRandGP2 == "")
    {
        trQuestVarSet("rand_gp_2", 0);
        return;
    }
    APGrantRandGP(gAPRandGP2, n, 90);
    trQuestVarSet("rand_gp_2", 0);
}

rule APRandGP3
minInterval 1
inactive
{
    int n = trQuestVarGet("rand_gp_3");
    if (n <= 0) { return; }
    if (gAPRandGP3 == "")
    {
        trQuestVarSet("rand_gp_3", 0);
        return;
    }
    APGrantRandGP(gAPRandGP3, n, 135);
    trQuestVarSet("rand_gp_3", 0);
}

rule APRandGP4
minInterval 1
inactive
{
    int n = trQuestVarGet("rand_gp_4");
    if (n <= 0) { return; }
    if (gAPRandGP4 == "")
    {
        trQuestVarSet("rand_gp_4", 0);
        return;
    }
    APGrantRandGP(gAPRandGP4, n, 180);
    trQuestVarSet("rand_gp_4", 0);
}