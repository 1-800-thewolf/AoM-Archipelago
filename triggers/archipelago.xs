// archipelago.xs
// Archipelago Multiworld integration script for Age of Mythology: Retold
// aom_state.xs is included near the top so all globals are declared first.
// Do not include this directly. Use ap_init.xs instead.
// In each gameplay scenario, add ONE XS Code Snippet effect near mission start:
//   trQuestVarSet("APScenarioID", <scenario_number>);
//   xsEnableRule("APActivateScenario");

// extern globals — visible across all XS source files including aom_state.xs
extern int gAPItemCount = 0;
extern int[] gAPItems = default;

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
const int cPASSIVE_WOOD_MEDIUM           = 17;
const int cPASSIVE_FOOD_MEDIUM           = 18;
const int cPASSIVE_GOLD_MEDIUM           = 19;
const int cPASSIVE_FAVOR_MEDIUM          = 20;
const int cPASSIVE_WOOD_LARGE            = 21;
const int cPASSIVE_FOOD_LARGE            = 22;
const int cPASSIVE_GOLD_LARGE            = 23;
const int cPASSIVE_FAVOR_LARGE           = 24;

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
const int cGREEK_VILLAGER_CHEAPER        = 5009;
const int cEGYPTIAN_VILLAGER_CHEAPER     = 5010;
const int cNORSE_VILLAGER_CHEAPER        = 5011;
const int cGREEK_VILLAGER_CHEAPER_2      = 5012;
const int cEGYPTIAN_VILLAGER_CHEAPER_2   = 5013;
const int cNORSE_VILLAGER_CHEAPER_2      = 5014;
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

const int cGREEK_SCENARIOS               = 3500;
const int cEGYPTIAN_SCENARIOS            = 3501;
const int cNORSE_SCENARIOS               = 3502;
// cFINAL_SCENARIOS removed (stale) -- Final section uses ATLANTIS_KEY (3510) as unlock signal
const int cATLANTIS_KEY                  = 3510;

// Age unlock item IDs — raw values matching Items.py
const int cGREEK_AGE_UNLOCK              = 1002;
const int cEGYPTIAN_AGE_UNLOCK           = 1005;
const int cNORSE_AGE_UNLOCK              = 1008;
const int cATLANTEAN_AGE_UNLOCK          = 1011;


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
bool gAPGodsanity  = false;
bool gHasGreek     = false;
bool gHasEgyptian  = false;
bool gHasNorse     = false;
bool gHasAtlantis  = false;
int gPassiveWood       = 0;
int gPassiveFood       = 0;
int gPassiveGold       = 0;
int gPassiveFavor      = 0;
int gPassiveFavorSlow  = 0;  // granted every 20s (small favor passive)

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
    if (gAPMajorGod == cAPMajorZeus || gAPMajorGod == cAPMajorPoseidon || gAPMajorGod == cAPMajorHades)
    {
        if (gAPMajorGod == cAPMajorZeus)     { trPlayerSetCiv(1, "Zeus"); }
        if (gAPMajorGod == cAPMajorPoseidon) { trPlayerSetCiv(1, "Poseidon"); }
        if (gAPMajorGod == cAPMajorHades)    { trPlayerSetCiv(1, "Hades"); }
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
}

rule APActivateScenario
highFrequency
inactive
runImmediately
{
    gAPScenarioId = trQuestVarGet("APScenarioID");
    gAPCampaignId = APGetCampaignForScenario(gAPScenarioId);
    gAPMajorGod = APGetMajorGodForScenario(gAPScenarioId);
    APInitItems();               // populate gAPItems array first — needed by reads below
    APInitGods();                // populate APGod1..APGod32 quest vars
    APReadRandomGod();           // override gAPMajorGod if godsanity is active
    APSetPlayerCiv();            // change civ + force-clear old civ age techs
    APForbidVanillaArchaicUnits(); // forbid archaic units from vanilla god/civ if changed
    APInitStartingAgeTechs();    // grant pre-computed starting age techs for this scenario
    APForbidItemGatedUnits();    // forbid all units whose unlock items have not been received

    // SPC campaign heroes — never player-trainable regardless of god or items
    trForbidProtounit(1, "Ajax");
    trForbidProtounit(1, "Chiron");
    trForbidProtounit(1, "Odysseus");

    xsEnableRule("APApplyItems");
    trMusicPlayCurrent();
    xsDisableSelf();
}

// -----------------------------------------------------------------------
// God announcement — called from APApplyItems when godsanity is on.
// Fires at the same time as APCheckCampaignLock, after the cinematic ends.
// -----------------------------------------------------------------------

void APAnnounceGod()
{
    if (gAPGodsanity == false) { return; }

    string godName   = "";
    string colorOpen = "";

    if (gAPMajorGod == cAPMajorZeus)     { godName = "Zeus";     colorOpen = "<color0,0,255>"; }
    if (gAPMajorGod == cAPMajorPoseidon) { godName = "Poseidon"; colorOpen = "<color0,0,255>"; }
    if (gAPMajorGod == cAPMajorHades)    { godName = "Hades";    colorOpen = "<color0,0,255>"; }
    if (gAPMajorGod == cAPMajorIsis)     { godName = "Isis";     colorOpen = "<color255,255,0>"; }
    if (gAPMajorGod == cAPMajorRa)       { godName = "Ra";       colorOpen = "<color255,255,0>"; }
    if (gAPMajorGod == cAPMajorSet)      { godName = "Set";      colorOpen = "<color255,255,0>"; }
    if (gAPMajorGod == cAPMajorOdin)     { godName = "Odin";     colorOpen = "<color136,8,8>"; }
    if (gAPMajorGod == cAPMajorThor)     { godName = "Thor";     colorOpen = "<color136,8,8>"; }
    if (gAPMajorGod == cAPMajorLoki)     { godName = "Loki";     colorOpen = "<color136,8,8>"; }
    if (gAPMajorGod == cAPMajorKronos)   { godName = "Kronos";   colorOpen = "<color0,255,255>"; }
    if (gAPMajorGod == cAPMajorOranos)   { godName = "Oranos";   colorOpen = "<color0,255,255>"; }
    if (gAPMajorGod == cAPMajorGaia)     { godName = "Gaia";     colorOpen = "<color0,255,255>"; }

    if (godName != "")
    {
        trMessageSetText("Major God:\n" + colorOpen + godName + "</color>", 5);
        trSoundPlayFN("ui\thunder3.wav");
    }
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
    return "Unknown Location";
}

void APShowQueuedCheckMessage(int id = 0)
{
    string objectiveText = APGetCheckText(id);

    trMessageSetText(
        "Checked <color1,1,0>" + objectiveText + "</color>\n\nComplete or quit the mission to send or receive items.",
        -1
    );
    trSoundPlayFN("campaign\fott\cinematics\fott07\clearedcity.wav");
}

// Legacy helper retained for compatibility if called from within this XS file.
void APCheckLocation(string objectiveText = "")
{
    trMessageSetText(
        "Checked <color1,1,0>" + objectiveText + "</color>\n\nComplete or quit the mission to send or receive items",
        -1
    );
    trSoundPlayFN("campaign\fott\cinematics\fott07\clearedcity.wav");
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

    if (hasUnlock == false)
    {
        string neededItem = "UNKNOWN ITEM";
        if (gAPCampaignId == 1) { neededItem = "Greek Scenarios"; }
        if (gAPCampaignId == 2) { neededItem = "Egyptian Scenarios"; }
        if (gAPCampaignId == 3) { neededItem = "Norse Scenarios"; }
        if (gAPCampaignId == 4) { neededItem = "Atlantis Key"; }

        string msg = "You need " + neededItem + " to play this";
        trShowWinPopup(msg, "taunts\037 not a wise decision but a decision nonetheless.mp3", true);

        if (gAPCampaignId == 1) { trExecuteOnAI(12, "APLocked_Greek"); }
        if (gAPCampaignId == 2) { trExecuteOnAI(12, "APLocked_Egyptian"); }
        if (gAPCampaignId == 3) { trExecuteOnAI(12, "APLocked_Norse"); }
        if (gAPCampaignId == 4) { trExecuteOnAI(12, "APLocked_Final"); }

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

void APApplyGreekMinorGods(int majorGod = 0, int ageCount = 0)
{
    APDisableAllGreekAgeTechs();

    if (ageCount >= 1)
    {
        if (trTechStatusActive(1, cTechClassicalAgeGreek) == false) { trTechSetStatus(1, cTechClassicalAgeGreek, 1); }
        if (majorGod == cAPMajorZeus) { if (trTechStatusActive(1, cTechClassicalAgeAthena) == false) { trTechSetStatus(1, cTechClassicalAgeAthena, 1); } if (trTechStatusActive(1, cTechClassicalAgeHermes) == false) { trTechSetStatus(1, cTechClassicalAgeHermes, 1); } }
        if (majorGod == cAPMajorPoseidon) { if (trTechStatusActive(1, cTechClassicalAgeHermes) == false) { trTechSetStatus(1, cTechClassicalAgeHermes, 1); } if (trTechStatusActive(1, cTechClassicalAgeAres) == false) { trTechSetStatus(1, cTechClassicalAgeAres, 1); } }
        if (majorGod == cAPMajorHades) { if (trTechStatusActive(1, cTechClassicalAgeAthena) == false) { trTechSetStatus(1, cTechClassicalAgeAthena, 1); } if (trTechStatusActive(1, cTechClassicalAgeAres) == false) { trTechSetStatus(1, cTechClassicalAgeAres, 1); } }
    }
    if (ageCount >= 2)
    {
        if (trTechStatusActive(1, cTechHeroicAgeGreek) == false) { trTechSetStatus(1, cTechHeroicAgeGreek, 1); }
        if (majorGod == cAPMajorZeus) { if (trTechStatusActive(1, cTechHeroicAgeApollo) == false) { trTechSetStatus(1, cTechHeroicAgeApollo, 1); } if (trTechStatusActive(1, cTechHeroicAgeDionysus) == false) { trTechSetStatus(1, cTechHeroicAgeDionysus, 1); } }
        if (majorGod == cAPMajorPoseidon) { if (trTechStatusActive(1, cTechHeroicAgeDionysus) == false) { trTechSetStatus(1, cTechHeroicAgeDionysus, 1); } if (trTechStatusActive(1, cTechHeroicAgeAphrodite) == false) { trTechSetStatus(1, cTechHeroicAgeAphrodite, 1); } }
        if (majorGod == cAPMajorHades) { if (trTechStatusActive(1, cTechHeroicAgeApollo) == false) { trTechSetStatus(1, cTechHeroicAgeApollo, 1); } if (trTechStatusActive(1, cTechHeroicAgeAphrodite) == false) { trTechSetStatus(1, cTechHeroicAgeAphrodite, 1); } }
    }
    if (ageCount >= 3)
    {
        if (trTechStatusActive(1, cTechMythicAgeGreek) == false) { trTechSetStatus(1, cTechMythicAgeGreek, 1); }
        if (majorGod == cAPMajorZeus) { if (trTechStatusActive(1, cTechMythicAgeHera) == false) { trTechSetStatus(1, cTechMythicAgeHera, 1); } if (trTechStatusActive(1, cTechMythicAgeHephaestus) == false) { trTechSetStatus(1, cTechMythicAgeHephaestus, 1); } }
        if (majorGod == cAPMajorPoseidon) { if (trTechStatusActive(1, cTechMythicAgeHephaestus) == false) { trTechSetStatus(1, cTechMythicAgeHephaestus, 1); } if (trTechStatusActive(1, cTechMythicAgeArtemis) == false) { trTechSetStatus(1, cTechMythicAgeArtemis, 1); } }
        if (majorGod == cAPMajorHades) { if (trTechStatusActive(1, cTechMythicAgeHera) == false) { trTechSetStatus(1, cTechMythicAgeHera, 1); } if (trTechStatusActive(1, cTechMythicAgeArtemis) == false) { trTechSetStatus(1, cTechMythicAgeArtemis, 1); } }
    }
}

void APApplyEgyptianMinorGods(int majorGod = 0, int ageCount = 0)
{
    APDisableAllEgyptianAgeTechs();

    if (ageCount >= 1)
    {
        if (trTechStatusActive(1, cTechClassicalAgeEgyptian) == false) { trTechSetStatus(1, cTechClassicalAgeEgyptian, 1); }
        if (majorGod == cAPMajorRa) { if (trTechStatusActive(1, cTechClassicalAgeBast) == false) { trTechSetStatus(1, cTechClassicalAgeBast, 1); } if (trTechStatusActive(1, cTechClassicalAgePtah) == false) { trTechSetStatus(1, cTechClassicalAgePtah, 1); } }
        if (majorGod == cAPMajorIsis) { if (trTechStatusActive(1, cTechClassicalAgeAnubis) == false) { trTechSetStatus(1, cTechClassicalAgeAnubis, 1); } if (trTechStatusActive(1, cTechClassicalAgePtah) == false) { trTechSetStatus(1, cTechClassicalAgePtah, 1); } }
        if (majorGod == cAPMajorSet) { if (trTechStatusActive(1, cTechClassicalAgeAnubis) == false) { trTechSetStatus(1, cTechClassicalAgeAnubis, 1); } if (trTechStatusActive(1, cTechClassicalAgeBast) == false) { trTechSetStatus(1, cTechClassicalAgeBast, 1); } }
    }
    if (ageCount >= 2)
    {
        if (trTechStatusActive(1, cTechHeroicAgeEgyptian) == false) { trTechSetStatus(1, cTechHeroicAgeEgyptian, 1); }
        if (majorGod == cAPMajorRa) { if (trTechStatusActive(1, cTechHeroicAgeSekhmet) == false) { trTechSetStatus(1, cTechHeroicAgeSekhmet, 1); } if (trTechStatusActive(1, cTechHeroicAgeSobek) == false) { trTechSetStatus(1, cTechHeroicAgeSobek, 1); } }
        if (majorGod == cAPMajorIsis) { if (trTechStatusActive(1, cTechHeroicAgeSobek) == false) { trTechSetStatus(1, cTechHeroicAgeSobek, 1); } if (trTechStatusActive(1, cTechHeroicAgeNephthys) == false) { trTechSetStatus(1, cTechHeroicAgeNephthys, 1); } }
        if (majorGod == cAPMajorSet) { if (trTechStatusActive(1, cTechHeroicAgeSekhmet) == false) { trTechSetStatus(1, cTechHeroicAgeSekhmet, 1); } if (trTechStatusActive(1, cTechHeroicAgeNephthys) == false) { trTechSetStatus(1, cTechHeroicAgeNephthys, 1); } }
    }
    if (ageCount >= 3)
    {
        if (trTechStatusActive(1, cTechMythicAgeEgyptian) == false) { trTechSetStatus(1, cTechMythicAgeEgyptian, 1); }
        if (majorGod == cAPMajorRa) { if (trTechStatusActive(1, cTechMythicAgeOsiris) == false) { trTechSetStatus(1, cTechMythicAgeOsiris, 1); } if (trTechStatusActive(1, cTechMythicAgeHorus) == false) { trTechSetStatus(1, cTechMythicAgeHorus, 1); } }
        if (majorGod == cAPMajorIsis) { if (trTechStatusActive(1, cTechMythicAgeHorus) == false) { trTechSetStatus(1, cTechMythicAgeHorus, 1); } if (trTechStatusActive(1, cTechMythicAgeThoth) == false) { trTechSetStatus(1, cTechMythicAgeThoth, 1); } }
        if (majorGod == cAPMajorSet) { if (trTechStatusActive(1, cTechMythicAgeOsiris) == false) { trTechSetStatus(1, cTechMythicAgeOsiris, 1); } if (trTechStatusActive(1, cTechMythicAgeThoth) == false) { trTechSetStatus(1, cTechMythicAgeThoth, 1); } }
    }
}

void APApplyNorseMinorGods(int majorGod = 0, int ageCount = 0)
{
    APDisableAllNorseAgeTechs();

    if (ageCount >= 1)
    {
        if (trTechStatusActive(1, cTechClassicalAgeNorse) == false) { trTechSetStatus(1, cTechClassicalAgeNorse, 1); }
        if (majorGod == cAPMajorOdin) { if (trTechStatusActive(1, cTechClassicalAgeFreyja) == false) { trTechSetStatus(1, cTechClassicalAgeFreyja, 1); } if (trTechStatusActive(1, cTechClassicalAgeHeimdall) == false) { trTechSetStatus(1, cTechClassicalAgeHeimdall, 1); } }
        if (majorGod == cAPMajorThor) { if (trTechStatusActive(1, cTechClassicalAgeFreyja) == false) { trTechSetStatus(1, cTechClassicalAgeFreyja, 1); } if (trTechStatusActive(1, cTechClassicalAgeForseti) == false) { trTechSetStatus(1, cTechClassicalAgeForseti, 1); } }
        if (majorGod == cAPMajorLoki) { if (trTechStatusActive(1, cTechClassicalAgeForseti) == false) { trTechSetStatus(1, cTechClassicalAgeForseti, 1); } if (trTechStatusActive(1, cTechClassicalAgeHeimdall) == false) { trTechSetStatus(1, cTechClassicalAgeHeimdall, 1); } }
    }
    if (ageCount >= 2)
    {
        if (trTechStatusActive(1, cTechHeroicAgeNorse) == false) { trTechSetStatus(1, cTechHeroicAgeNorse, 1); }
        if (majorGod == cAPMajorOdin) { if (trTechStatusActive(1, cTechHeroicAgeNjord) == false) { trTechSetStatus(1, cTechHeroicAgeNjord, 1); } if (trTechStatusActive(1, cTechHeroicAgeSkadi) == false) { trTechSetStatus(1, cTechHeroicAgeSkadi, 1); } }
        if (majorGod == cAPMajorThor) { if (trTechStatusActive(1, cTechHeroicAgeBragi) == false) { trTechSetStatus(1, cTechHeroicAgeBragi, 1); } if (trTechStatusActive(1, cTechHeroicAgeSkadi) == false) { trTechSetStatus(1, cTechHeroicAgeSkadi, 1); } }
        if (majorGod == cAPMajorLoki) { if (trTechStatusActive(1, cTechHeroicAgeBragi) == false) { trTechSetStatus(1, cTechHeroicAgeBragi, 1); } if (trTechStatusActive(1, cTechHeroicAgeNjord) == false) { trTechSetStatus(1, cTechHeroicAgeNjord, 1); } }
    }
    if (ageCount >= 3)
    {
        if (trTechStatusActive(1, cTechMythicAgeNorse) == false) { trTechSetStatus(1, cTechMythicAgeNorse, 1); }
        if (majorGod == cAPMajorOdin) { if (trTechStatusActive(1, cTechMythicAgeBaldr) == false) { trTechSetStatus(1, cTechMythicAgeBaldr, 1); } if (trTechStatusActive(1, cTechMythicAgeTyr) == false) { trTechSetStatus(1, cTechMythicAgeTyr, 1); } }
        if (majorGod == cAPMajorThor) { if (trTechStatusActive(1, cTechMythicAgeBaldr) == false) { trTechSetStatus(1, cTechMythicAgeBaldr, 1); } if (trTechStatusActive(1, cTechMythicAgeTyr) == false) { trTechSetStatus(1, cTechMythicAgeTyr, 1); } }
        if (majorGod == cAPMajorLoki) { if (trTechStatusActive(1, cTechMythicAgeTyr) == false) { trTechSetStatus(1, cTechMythicAgeTyr, 1); } if (trTechStatusActive(1, cTechMythicAgeHel) == false) { trTechSetStatus(1, cTechMythicAgeHel, 1); } }
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

void APApplyAtlanteanMinorGods(int majorGod = 0, int ageCount = 0)
{
    APDisableAllAtlanteanAgeTechs();
    if (ageCount >= 1)
    {
        if (trTechStatusActive(1, cTechClassicalAgeAtlantean) == false) { trTechSetStatus(1, cTechClassicalAgeAtlantean, 1); }
        if (majorGod == cAPMajorKronos) { if (trTechStatusActive(1, cTechClassicalAgePrometheus) == false) { trTechSetStatus(1, cTechClassicalAgePrometheus, 1); } if (trTechStatusActive(1, cTechClassicalAgeLeto) == false) { trTechSetStatus(1, cTechClassicalAgeLeto, 1); } }
        if (majorGod == cAPMajorOranos) { if (trTechStatusActive(1, cTechClassicalAgePrometheus) == false) { trTechSetStatus(1, cTechClassicalAgePrometheus, 1); } if (trTechStatusActive(1, cTechClassicalAgeOceanus) == false) { trTechSetStatus(1, cTechClassicalAgeOceanus, 1); } }
        if (majorGod == cAPMajorGaia)   { if (trTechStatusActive(1, cTechClassicalAgeLeto) == false) { trTechSetStatus(1, cTechClassicalAgeLeto, 1); } if (trTechStatusActive(1, cTechClassicalAgeOceanus) == false) { trTechSetStatus(1, cTechClassicalAgeOceanus, 1); } }
    }
    if (ageCount >= 2)
    {
        if (trTechStatusActive(1, cTechHeroicAgeAtlantean) == false) { trTechSetStatus(1, cTechHeroicAgeAtlantean, 1); }
        if (majorGod == cAPMajorKronos) { if (trTechStatusActive(1, cTechHeroicAgeHyperion) == false) { trTechSetStatus(1, cTechHeroicAgeHyperion, 1); } if (trTechStatusActive(1, cTechHeroicAgeRheia) == false) { trTechSetStatus(1, cTechHeroicAgeRheia, 1); } }
        if (majorGod == cAPMajorOranos) { if (trTechStatusActive(1, cTechHeroicAgeHyperion) == false) { trTechSetStatus(1, cTechHeroicAgeHyperion, 1); } if (trTechStatusActive(1, cTechHeroicAgeTheia) == false) { trTechSetStatus(1, cTechHeroicAgeTheia, 1); } }
        if (majorGod == cAPMajorGaia)   { if (trTechStatusActive(1, cTechHeroicAgeRheia) == false) { trTechSetStatus(1, cTechHeroicAgeRheia, 1); } if (trTechStatusActive(1, cTechHeroicAgeTheia) == false) { trTechSetStatus(1, cTechHeroicAgeTheia, 1); } }
    }
    if (ageCount >= 3)
    {
        if (trTechStatusActive(1, cTechMythicAgeAtlantean) == false) { trTechSetStatus(1, cTechMythicAgeAtlantean, 1); }
        if (majorGod == cAPMajorKronos) { if (trTechStatusActive(1, cTechMythicAgeHelios) == false) { trTechSetStatus(1, cTechMythicAgeHelios, 1); } if (trTechStatusActive(1, cTechMythicAgeAtlas) == false) { trTechSetStatus(1, cTechMythicAgeAtlas, 1); } }
        if (majorGod == cAPMajorOranos) { if (trTechStatusActive(1, cTechMythicAgeHelios) == false) { trTechSetStatus(1, cTechMythicAgeHelios, 1); } if (trTechStatusActive(1, cTechMythicAgeHekate) == false) { trTechSetStatus(1, cTechMythicAgeHekate, 1); } }
        if (majorGod == cAPMajorGaia)   { if (trTechStatusActive(1, cTechMythicAgeAtlas) == false) { trTechSetStatus(1, cTechMythicAgeAtlas, 1); } if (trTechStatusActive(1, cTechMythicAgeHekate) == false) { trTechSetStatus(1, cTechMythicAgeHekate, 1); } }
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
    if (scenarioId == 21) { return 0; }
    if (scenarioId == 22) { return 0; }
    if (scenarioId == 23) { return 1; }
    if (scenarioId == 24) { return 1; }
    if (scenarioId == 25) { return 0; }
    if (scenarioId == 26) { return 1; }
    if (scenarioId == 27) { return 1; }
    if (scenarioId == 28) { return 2; }
    if (scenarioId == 29) { return 1; }
    if (scenarioId == 30) { return 1; }
    if (scenarioId == 31) { return 2; }
    if (scenarioId == 32) { return 2; }
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

    for (i = 6; i < gAPItemCount; i++)
    {
        id = gAPItems[i];
        if (id == cGREEK_AGE_UNLOCK)      { greekCount++;     }
        if (id == cEGYPTIAN_AGE_UNLOCK)   { egyptianCount++;  }
        if (id == cNORSE_AGE_UNLOCK)      { norseCount++;     }
        if (id == cATLANTEAN_AGE_UNLOCK)  { atlanteanCount++; }
    }

    if (gAPMajorGod == cAPMajorZeus || gAPMajorGod == cAPMajorPoseidon || gAPMajorGod == cAPMajorHades)
    {
        APApplyGreekMinorGods(gAPMajorGod, greekCount);
        APDisableAllEgyptianAgeTechs();
        APDisableAllNorseAgeTechs();
    }
    if (gAPMajorGod == cAPMajorIsis || gAPMajorGod == cAPMajorRa || gAPMajorGod == cAPMajorSet)
    {
        APApplyEgyptianMinorGods(gAPMajorGod, egyptianCount);
        APDisableAllGreekAgeTechs();
        APDisableAllNorseAgeTechs();
    }
    if (gAPMajorGod == cAPMajorOdin || gAPMajorGod == cAPMajorThor || gAPMajorGod == cAPMajorLoki)
    {
        APApplyNorseMinorGods(gAPMajorGod, norseCount);
        APDisableAllGreekAgeTechs();
        APDisableAllEgyptianAgeTechs();
    }
    if (gAPMajorGod == cAPMajorKronos || gAPMajorGod == cAPMajorOranos || gAPMajorGod == cAPMajorGaia)
    {
        APApplyAtlanteanMinorGods(gAPMajorGod, atlanteanCount);
        APDisableAllGreekAgeTechs();
        APDisableAllEgyptianAgeTechs();
        APDisableAllNorseAgeTechs();
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

    // Start at 6 — indices 0-5 are flags (campaign unlocks, campaign ID, godsanity)
    for (i = 6; i < gAPItemCount; i++)
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
    }

    // --- Apply stat boosts ---
    // Arkantos (hack)
    if (arkHp   > 0) { trModifyProtounitData("Arkantos",   1, 0,  arkHp,   0); }
    if (arkAtk  > 0) { trModifyProtounitAction("Arkantos",   "HandAttack", 1, 13, arkAtk,  0); }
    if (arkRecharge > 0) { trModifyProtounitData("Arkantos",   1, 9, -arkRecharge, 0); }
    if (arkRegen > 0){ trModifyProtounitData("Arkantos",   1, 17, arkRegen, 0); }

    // Ajax (hack)
    if (ajxHp   > 0) { trModifyProtounitData("AjaxSPC",    1, 0,  ajxHp,   0); }
    if (ajxAtk  > 0) { trModifyProtounitAction("AjaxSPC",    "HandAttack", 1, 13, ajxAtk,  0); }
    if (ajxRecharge > 0) { trModifyProtounitData("AjaxSPC",    1, 9, -ajxRecharge, 0); }
    if (ajxRegen > 0){ trModifyProtounitData("AjaxSPC",    1, 17, ajxRegen, 0); }

    // Chiron (pierce)
    if (chiHp   > 0) { trModifyProtounitData("ChironSPC",  1, 0,  chiHp,   0); }
    if (chiAtk  > 0) { trModifyProtounitAction("ChironSPC",  "RangedAttack", 1, 14, chiAtk, 0); }
    if (chiRecharge > 0) { trModifyProtounitData("ChironSPC",  1, 9, -chiRecharge, 0); }
    if (chiRegen > 0){ trModifyProtounitData("ChironSPC",  1, 17, chiRegen, 0); }

    // Amanra (hack)
    if (amHp    > 0) { trModifyProtounitData("Amanra",     1, 0,  amHp,    0); }
    if (amAtk   > 0) { trModifyProtounitAction("Amanra",     "HandAttack", 1, 13, amAtk,   0); }
    if (amRecharge  > 0) { trModifyProtounitData("Amanra",     1, 9, -amRecharge,  0); }
    if (amRegen  > 0){ trModifyProtounitData("Amanra",     1, 17, amRegen,  0); }

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
    }
    // Ajax: Smiting Strikes (HandAttack, MaxHP modifier + VisualScale)
    if (ajxSmitingStrikes == true)
    {
        //HAX HP
        trProtounitActionSpecialEffectModifier("AjaxSPC", "HandAttack", 1, 1, "Unit", 0.5, 1, -1);
        //VISUAL SCALE
        trProtounitActionSpecialEffectModifier("AjaxSPC", "HandAttack", 1, 1, "Unit", -0.3, 49, 0);
    }
    // Ajax: Shield Bash AOE (Gore, DamageArea +10)
    if (ajxShieldBashAOE == true)
    {
        trModifyProtounitAction("AjaxSPC", "Gore", 1, 3, 10.0, 0);
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
        trProtounitActionSpecialEffect("Amanra", "JumpAttack", 1, 6, "All", -1, 10.0, 10.0);
    }
    // Amanra: Army of the Dead (HandAttack, Reincarnation into Minion)
    if (amArmyOfTheDead == true)
    {
        trProtounitActionSpecialEffectProtoUnit("Amanra", "HandAttack", 1, 5, "All", "Minion", 1.0, 1.0);
    }
    // Amanra: Divine Smite (HandAttack, DamageDivine +5)
    if (amDivineSmite == true)
    {
        trModifyProtounitAction("Amanra", "HandAttack", 1, 16, 5.0, 0);
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
    gHasGreek    = false;
    gHasEgyptian = false;
    gHasNorse    = false;
    gHasAtlantis = false;
    gAPGodsanity = false;
    if (gAPItemCount > 5)
    {
        if (gAPItems[0] == 9001) { gHasGreek    = true; }
        if (gAPItems[1] == 9002) { gHasEgyptian = true; }
        if (gAPItems[2] == 9003) { gHasNorse    = true; }
        if (gAPItems[3] == 9004) { gHasAtlantis = true; }
        if (gAPItems[5] == 9010) { gAPGodsanity = true; }
        // Scenario identity is driven by APScenarioID + APActivateScenario.
        // Keep slot 4 for compatibility, but do not overwrite gAPCampaignId here.
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
    // Villager food cost reduction counters
    int grkCheaper = 0; int egyCheaper = 0; int norCheaper = 0;
    int grkCheaper2 = 0; int egyCheaper2 = 0; int norCheaper2 = 0;

    int itemId = 0;
    int i = 0;
    int j = 0;
    // Start at 6 — indices 0-5 are flags (campaign unlocks, campaign ID, godsanity)
    for (i = 6; i < gAPItemCount; i++)
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

        if (itemId == cPASSIVE_WOOD_SMALL)    { gPassiveWood  += 1;  }
        if (itemId == cPASSIVE_FOOD_SMALL)    { gPassiveFood  += 1;  }
        if (itemId == cPASSIVE_GOLD_SMALL)    { gPassiveGold  += 1;  }
        if (itemId == cPASSIVE_FAVOR_SMALL)   { gPassiveFavorSlow += 1; }
        if (itemId == cPASSIVE_WOOD_MEDIUM)   { gPassiveWood  += 2;  }
        if (itemId == cPASSIVE_FOOD_MEDIUM)   { gPassiveFood  += 2;  }
        if (itemId == cPASSIVE_GOLD_MEDIUM)   { gPassiveGold  += 2;  }
        if (itemId == cPASSIVE_FAVOR_MEDIUM)  { gPassiveFavor += 1;  }
        if (itemId == cPASSIVE_WOOD_LARGE)    { gPassiveWood  += 4;  }
        if (itemId == cPASSIVE_FOOD_LARGE)    { gPassiveFood  += 4;  }
        if (itemId == cPASSIVE_GOLD_LARGE)    { gPassiveGold  += 4;  }
        if (itemId == cPASSIVE_FAVOR_LARGE)   { gPassiveFavor += 2;  }

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
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Roc", gReinforcementSpawnID, gReinforcementSpawnID, 1);
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
        // Villager food cost reduction
        if (itemId == cGREEK_VILLAGER_CHEAPER)      { grkCheaper++;  }
        if (itemId == cEGYPTIAN_VILLAGER_CHEAPER)   { egyCheaper++;  }
        if (itemId == cNORSE_VILLAGER_CHEAPER)      { norCheaper++;  }
        if (itemId == cGREEK_VILLAGER_CHEAPER_2)    { grkCheaper2++; }
        if (itemId == cEGYPTIAN_VILLAGER_CHEAPER_2) { egyCheaper2++; }
        if (itemId == cNORSE_VILLAGER_CHEAPER_2)    { norCheaper2++; }
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

    // Villager food cost reduction — cXSPUResourceEffectCost=0
    if (grkCheaper  > 0) { trModifyProtounitResource("VillagerGreek",    "food", 1, 0, -3.0 * grkCheaper,  0); }
    if (egyCheaper  > 0) { trModifyProtounitResource("VillagerEgyptian", "food", 1, 0, -3.0 * egyCheaper,  0); }
    if (norCheaper  > 0) { trModifyProtounitResource("VillagerNorse",    "food", 1, 0, -3.0 * norCheaper,  0); }
    if (grkCheaper2 > 0) { trModifyProtounitResource("VillagerGreek",    "food", 1, 0, -2.0 * grkCheaper2, 0); }
    if (egyCheaper2 > 0) { trModifyProtounitResource("VillagerEgyptian", "food", 1, 0, -2.0 * egyCheaper2, 0); }
    if (norCheaper2 > 0) { trModifyProtounitResource("VillagerNorse",    "food", 1, 0, -2.0 * norCheaper2, 0); }

    if (gPassiveWood > 0 || gPassiveFood > 0 || gPassiveGold > 0 || gPassiveFavor > 0)
    {
        xsEnableRule("APPassiveIncome");
    }
    if (gPassiveFavorSlow > 0)
    {
        xsEnableRule("APPassiveFavorSlow");
    }

    xsDisableSelf();
}

// -----------------------------------------------------------------------
// Passive income — fires every 60 seconds
// -----------------------------------------------------------------------

rule APPassiveIncome
minInterval 10
inactive
{
    if (gPassiveWood  > 0) { trPlayerGrantResources(1, "Wood",  gPassiveWood);  }
    if (gPassiveFood  > 0) { trPlayerGrantResources(1, "Food",  gPassiveFood);  }
    if (gPassiveGold  > 0) { trPlayerGrantResources(1, "Gold",  gPassiveGold);  }
    if (gPassiveFavor > 0) { trPlayerGrantResources(1, "Favor", gPassiveFavor); }
}

// -----------------------------------------------------------------------
// Passive favor (small tier) — fires every 20 seconds = 3/min
// -----------------------------------------------------------------------

rule APPassiveFavorSlow
minInterval 20
inactive
{
    if (gPassiveFavorSlow > 0) { trPlayerGrantResources(1, "Favor", gPassiveFavorSlow); }
}
