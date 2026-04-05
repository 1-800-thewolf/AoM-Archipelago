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
const int cREINFORCEMENT_ULFSARK         = 4008;
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

const int cGREEK_SCENARIOS               = 3500;
const int cEGYPTIAN_SCENARIOS            = 3501;
const int cNORSE_SCENARIOS               = 3502;
// cFINAL_SCENARIOS removed (stale) -- Final section uses ATLANTIS_KEY (3510) as unlock signal
const int cATLANTIS_KEY                  = 3510;

// Age unlock item IDs — raw values matching Items.py
const int cGREEK_AGE_UNLOCK_1            = 1002;
const int cGREEK_AGE_UNLOCK_2            = 1003;
const int cGREEK_AGE_UNLOCK_3            = 1004;
const int cEGYPTIAN_AGE_UNLOCK_1         = 1005;
const int cEGYPTIAN_AGE_UNLOCK_2         = 1006;
const int cEGYPTIAN_AGE_UNLOCK_3         = 1007;
const int cNORSE_AGE_UNLOCK_1            = 1008;
const int cNORSE_AGE_UNLOCK_2            = 1009;
const int cNORSE_AGE_UNLOCK_3            = 1010;

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

rule APActivateScenario
highFrequency
inactive
runImmediately
{
    gAPScenarioId = trQuestVarGet("APScenarioID");
    gAPCampaignId = APGetCampaignForScenario(gAPScenarioId);
    gAPMajorGod = APGetMajorGodForScenario(gAPScenarioId);

    // Forbid all unlockable units at scenario start — unforbidden by received items below
    trForbidProtounit(1, "Hoplite");
    trForbidProtounit(1, "Spearman");
    trForbidProtounit(1, "Berserk");
    trForbidProtounit(1, "Hirdman");
    trForbidProtounit(1, "Hypaspist");
    trForbidProtounit(1, "Peltast");
    trForbidProtounit(1, "Hippeus");
    trForbidProtounit(1, "Toxotes");
    trForbidProtounit(1, "Prodromos");
    trForbidProtounit(1, "Axeman");
    trForbidProtounit(1, "Slinger");
    trForbidProtounit(1, "ChariotArcher");
    trForbidProtounit(1, "CamelRider");
    trForbidProtounit(1, "WarElephant");
    trForbidProtounit(1, "ThrowingAxeman");
    trForbidProtounit(1, "Huskarl");
    trForbidProtounit(1, "RaidingCavalry");
    trForbidProtounit(1, "Jarl");

    xsEnableRule("APApplyItems");
    xsDisableSelf();
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
    if (id == 3876726) { return "Protect Atlantis by killing the Kraken."; }
    if (id == 3876727) { return "Train reinforcements to defend the harbor until the Atlantean Army arrives."; }
    if (id == 3876824) { return "Scenario Victory"; }
    if (id == 3876826) { return "Advance to the Classical Age and explore the island."; }
    if (id == 3876827) { return "Gather 400 Food"; }
    if (id == 3876828) { return "Build a House"; }
    if (id == 3876829) { return "Build a Temple"; }
    if (id == 3876830) { return "Train an army and destroy the pirate Town Center."; }
    if (id == 3876924) { return "Scenario Victory"; }
    if (id == 3876926) { return "Lead your men to the unclaimed Settlement."; }
    if (id == 3876927) { return "Build a Town Center."; }
    if (id == 3876928) { return "Destroy the Trojan docks."; }
    if (id == 3876929) { return "Destroy the last Trojan dock."; }
    if (id == 3877024) { return "Scenario Victory"; }
    if (id == 3877026) { return "Find and take a Gold Mine from the Trojans."; }
    if (id == 3877027) { return "Train an army and destroy the Trojan West Gate."; }
    if (id == 3877124) { return "Scenario Victory"; }
    if (id == 3877126) { return "Defeat the cavalry attacking Ajax."; }
    if (id == 3877127) { return "Bring Arkantos and your army to Ajax's Town Center to the southwest."; }
    if (id == 3877128) { return "Build up a stronger army and destroy all the buildings in the Trojan forward military base area."; }
    if (id == 3877224) { return "Scenario Victory"; }
    if (id == 3877226) { return "Accumulate 1000 Wood to build the Trojan Horse."; }
    if (id == 3877227) { return "Build the Trojan Horse."; }
    if (id == 3877228) { return "Sneak your Heroes through Troy toward the Trojan gate and find a way to destroy it."; }
    if (id == 3877229) { return "Defeat Troy by destroying the three Fortresses within its walls."; }
    if (id == 3877324) { return "Scenario Victory"; }
    if (id == 3877326) { return "Bring Arkantos and Ajax to the prison area to rescue the hostages."; }
    if (id == 3877327) { return "Defeat the bandits guarding the prison to free the prisoners."; }
    if (id == 3877328) { return "Destroy the enemy Watch Tower and Barracks."; }
    if (id == 3877329) { return "Destroy the enemy Watch Tower and Temple."; }
    if (id == 3877330) { return "Destroy the Migdol Stronghold to free Chiron."; }
    if (id == 3877424) { return "Scenario Victory"; }
    if (id == 3877426) { return "Build up Ajax and Arkantos' bases and fight your way to the mine."; }
    if (id == 3877524) { return "Scenario Victory"; }
    if (id == 3877526) { return "Destroy the ram before it breaks down the Gate."; }
    if (id == 3877624) { return "Scenario Victory"; }
    if (id == 3877626) { return "Seek the Shades."; }
    if (id == 3877627) { return "Scout forward. Shades are invisible to enemy units and can see farther than your other units."; }
    if (id == 3877628) { return "Kill the Minotaur."; }
    if (id == 3877629) { return "Collect the three lost relics of Hades."; }
    if (id == 3877630) { return "Bring the three relics to the temple complex."; }
    if (id == 3886724) { return "Scenario Victory"; }
    if (id == 3886726) { return "Defend against attacks from the three passes long enough for your Laborers to dig out the artifact."; }
    if (id == 3886824) { return "Scenario Victory"; }
    if (id == 3886826) { return "Kill the guards watching over the Laborers mining gold."; }
    if (id == 3886827) { return "Bring at least five Villagers safely to their Town Center."; }
    if (id == 3886828) { return "Bring the Sword Bearer to the Guardian, before Kemsyt's army reaches it."; }
    if (id == 3886829) { return "Use the Guardian to destroy Kemsyt's army."; }
    if (id == 3886924) { return "Scenario Victory"; }
    if (id == 3886926) { return "Recover the Osiris Piece Cart and move it into your city before Kemsyt brings it to his."; }
    if (id == 3887024) { return "Scenario Victory"; }
    if (id == 3887026) { return "Destroy Gargarensis' Migdol Stronghold."; }
    if (id == 3887027) { return "Amanra must reach the Transport Ship."; }
    if (id == 3887028) { return "Send Amanra to the Abydos harbor to convert a navy."; }
    if (id == 3887029) { return "Use your navy to break Amanra into the prison."; }
    if (id == 3887124) { return "Scenario Victory"; }
    if (id == 3887126) { return "Survive until Setna's transports arrive from the southwest."; }
    if (id == 3887127) { return "Use the Transports to move your troops to the flag in the allied purple town to the southwest."; }
    if (id == 3887128) { return "Capture the Osiris Piece Cart and move it outside the city's south gate."; }
    if (id == 3887224) { return "Scenario Victory"; }
    if (id == 3887226) { return "Follow Kastor."; }
    if (id == 3887227) { return "Garrison the Relic into the Temple, and defend the Temple."; }
    if (id == 3887228) { return "Defeat the guardians of the Shrine just ahead."; }
    if (id == 3887229) { return "Destroy the large boulder to escape the Underworld."; }
    if (id == 3887230) { return "Safely transport Arkantos and Kastor to the beach marked with white flags."; }
    if (id == 3887231) { return "Train an army and destroy the enemy wonder."; }
    if (id == 3887324) { return "Scenario Victory"; }
    if (id == 3887326) { return "Bring Amanra to the village."; }
    if (id == 3887327) { return "Bring Amanra to the Osiris Piece Box."; }
    if (id == 3887424) { return "Scenario Victory"; }
    if (id == 3887426) { return "Seek help from the desert nomad camp to the east."; }
    if (id == 3887427) { return "Send Laborers to cut down the Tamarisk tree and recover the head of Osiris."; }
    if (id == 3887524) { return "Scenario Victory"; }
    if (id == 3887526) { return "Capture the Black Sail ships to the east by destroying the forward base that guards them."; }
    if (id == 3887527) { return "Use the Black Sail ships to transport your army past Kamos' defenses and claim a Settlement."; }
    if (id == 3887528) { return "Quickly build up a large force and siege Kamos' base."; }
    if (id == 3887529) { return "Eliminate Kamos' guards and defeat him."; }
    if (id == 3887624) { return "Scenario Victory"; }
    if (id == 3887626) { return "Build up and fight toward the Osiris pyramid. Survive until Arkantos arrives with his Osiris piece."; }
    if (id == 3887627) { return "Arkantos has arrived with the last Osiris piece! Bring all three Osiris pieces to the Obelisk near Osiris' Pyramid."; }
    if (id == 3896724) { return "Scenario Victory"; }
    if (id == 3896726) { return "Save the pigs from being slaughtered."; }
    if (id == 3896727) { return "Bring the Boars and Pigs past the gates to the Temple of Zeus."; }
    if (id == 3896728) { return "Build up an army and defeat Circe by destroying the Fortress at the heart of her citadel."; }
    if (id == 3896824) { return "Scenario Victory"; }
    if (id == 3896826) { return "Reunite your forces and claim a Settlement."; }
    if (id == 3896827) { return "Destroy all three enemy Temples."; }
    if (id == 3896924) { return "Scenario Victory"; }
    if (id == 3896926) { return "Find a Settlement and build a Town Center."; }
    if (id == 3896927) { return "Eliminate the Giants and Trolls near the Dwarven Forge to recapture it."; }
    if (id == 3896928) { return "Defend the Dwarven Forge until the Giants retreat!"; }
    if (id == 3897024) { return "Scenario Victory"; }
    if (id == 3897026) { return "Protect Skult and the Folstag Flag Bearer."; }
    if (id == 3897027) { return "Skult and the Folstag Flag Bearer must reach the flagged site in the far north."; }
    if (id == 3897028) { return "Build up a defensive base near the boulder wall and advance to the Heroic Age."; }
    if (id == 3897029) { return "Break through the boulder wall."; }
    if (id == 3897030) { return "Escape the enemy armies. Move Skult and the Flag Bearer to the flag at the north end of the pass."; }
    if (id == 3897124) { return "Scenario Victory"; }
    if (id == 3897126) { return "Protect Skult and the Folstag Flag Bearer."; }
    if (id == 3897127) { return "Use the Folstag Flag Bearer to lure the clan leaders into an ambush. Eliminate all three leaders."; }
    if (id == 3897224) { return "Scenario Victory"; }
    if (id == 3897226) { return "Follow the trail to the first Norse clan."; }
    if (id == 3897227) { return "Defeat the Trolls in the mines to the west."; }
    if (id == 3897228) { return "Exit the mines and find two more Norse clans."; }
    if (id == 3897229) { return "Build five towers near the flagged sites around Lothbrok's village."; }
    if (id == 3897230) { return "Destroy the Watch Tower to free Forkbeard's daughter."; }
    if (id == 3897324) { return "Scenario Victory"; }
    if (id == 3897326) { return "Destroy the gate to the Well of Urd."; }
    if (id == 3897327) { return "Defeat all of the myth units defending the Well of Urd."; }
    if (id == 3897424) { return "Scenario Victory"; }
    if (id == 3897426) { return "Kill the Fire Giants guarding the ram before the gate to Tartarus opens."; }
    if (id == 3897427) { return "The Well of Urd must not be destroyed"; }
    if (id == 3897524) { return "Scenario Victory"; }
    if (id == 3897526) { return "Protect the Dwarves while they cut the hammer haft from the taproot."; }
    if (id == 3897527) { return "Finish cutting the haft from the taproot and bring the two pieces of Thor's hammer together."; }
    if (id == 3897624) { return "Scenario Victory"; }
    if (id == 3897626) { return "Find the abandoned mining town and build a Town Center there."; }
    if (id == 3897627) { return "You have 10 minutes to build up your defenses before Gargarensis attacks."; }
    if (id == 3897628) { return "Survive for 20 minutes until help arrives."; }
    if (id == 3897629) { return "Fight your way northward to Gargarensis."; }
    if (id == 3906724) { return "Scenario Victory"; }
    if (id == 3906726) { return "Land your troops on Atlantis' shores. Begin construction of a base by claiming a Settlement."; }
    if (id == 3906727) { return "Rescue and transport 15 Atlantean Prisoners to the flagged island to the west."; }
    if (id == 3906824) { return "Scenario Victory"; }
    if (id == 3906826) { return "Advance to the Mythic Age and construct a Wonder to receive Zeus' blessing."; }
    if (id == 3906827) { return "Use the Blessing of Zeus God Power on Arkantos."; }
    if (id == 3906828) { return "Defeat the Living Statue of Poseidon guarding Gargarensis and the final gate to Tartarus."; }
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

void APApplyAgeUnlocks()
{
    int greekCount = 0;
    int egyptianCount = 0;
    int norseCount = 0;
    int i = 0;
    int id = 0;

    for (i = 5; i < gAPItemCount; i++)
    {
        id = gAPItems[i];
        if (id == cGREEK_AGE_UNLOCK_1 || id == cGREEK_AGE_UNLOCK_2 || id == cGREEK_AGE_UNLOCK_3) { greekCount++; }
        if (id == cEGYPTIAN_AGE_UNLOCK_1 || id == cEGYPTIAN_AGE_UNLOCK_2 || id == cEGYPTIAN_AGE_UNLOCK_3) { egyptianCount++; }
        if (id == cNORSE_AGE_UNLOCK_1 || id == cNORSE_AGE_UNLOCK_2 || id == cNORSE_AGE_UNLOCK_3) { norseCount++; }
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

    // Start at 5 — indices 0-4 are flags/campaign ID
    for (i = 5; i < gAPItemCount; i++)
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
        trProtounitActionSpecialEffectModifier("AjaxSPC", "HandAttack", 1, 1, "Unit", 0.5, 1, -1);
        trProtounitActionSpecialEffectModifier("AjaxSPC", "HandAttack", 1, 1, "Unit", 0.5, 49, 0.5);
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
    gHasGreek    = false;
    gHasEgyptian = false;
    gHasNorse    = false;
    gHasAtlantis = false;
    if (gAPItemCount > 4)
    {
        if (gAPItems[0] == 9001) { gHasGreek    = true; }
        if (gAPItems[1] == 9002) { gHasEgyptian = true; }
        if (gAPItems[2] == 9003) { gHasNorse    = true; }
        if (gAPItems[3] == 9004) { gHasAtlantis = true; }
        // Scenario identity is driven by APScenarioID + APActivateScenario.
        // Keep slot 4 for compatibility, but do not overwrite gAPCampaignId here.
    }

    APCheckCampaignLock();
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
    // Start at 5 — indices 0-4 are flags/campaign ID
    for (i = 5; i < gAPItemCount; i++)
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
        if (itemId == cREINFORCEMENT_ULFSARK)
        {
            for (j = 0; j < 2; j++)
            {
                trUnitCreateFromSource("Ulfsark", gReinforcementSpawnID, gReinforcementSpawnID, 1);
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
            trUnitCreateFromSource("Reginleif", gReinforcementSpawnID, gReinforcementSpawnID, 1);
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
                trUnitCreateFromSource("Gatherer", gReinforcementSpawnID, gReinforcementSpawnID, 1);
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

        // Unit unlocks
        if (itemId == cCAN_TRAIN_HOPLITE)         { trUnforbidProtounit(1, "Hoplite"); }
        if (itemId == cCAN_TRAIN_SPEARMAN)        { trUnforbidProtounit(1, "Spearman"); }
        if (itemId == cCAN_TRAIN_BERSERK)         { trUnforbidProtounit(1, "Berserk"); }
        if (itemId == cCAN_TRAIN_HIRDMAN)         { trUnforbidProtounit(1, "Hirdman"); }
        if (itemId == cCAN_TRAIN_HYPASPIST)       { trUnforbidProtounit(1, "Hypaspist"); }
        if (itemId == cCAN_TRAIN_PELTAST)         { trUnforbidProtounit(1, "Peltast"); }
        if (itemId == cCAN_TRAIN_HIPPEUS)         { trUnforbidProtounit(1, "Hippeus"); }
        if (itemId == cCAN_TRAIN_TOXOTES)         { trUnforbidProtounit(1, "Toxotes"); }
        if (itemId == cCAN_TRAIN_PRODROMOS)       { trUnforbidProtounit(1, "Prodromos"); }
        if (itemId == cCAN_TRAIN_AXEMAN)          { trUnforbidProtounit(1, "Axeman"); }
        if (itemId == cCAN_TRAIN_SLINGER)         { trUnforbidProtounit(1, "Slinger"); }
        if (itemId == cCAN_TRAIN_CHARIOT_ARCHER)  { trUnforbidProtounit(1, "ChariotArcher"); }
        if (itemId == cCAN_TRAIN_CAMEL_RIDER)     { trUnforbidProtounit(1, "CamelRider"); }
        if (itemId == cCAN_TRAIN_WAR_ELEPHANT)    { trUnforbidProtounit(1, "WarElephant"); }
        if (itemId == cCAN_TRAIN_THROWING_AXEMAN) { trUnforbidProtounit(1, "ThrowingAxeman"); }
        if (itemId == cCAN_TRAIN_HUSKARL)         { trUnforbidProtounit(1, "Huskarl"); }
        if (itemId == cCAN_TRAIN_RAIDING_CAVALRY) { trUnforbidProtounit(1, "RaidingCavalry"); }
        if (itemId == cCAN_TRAIN_JARL)            { trUnforbidProtounit(1, "Jarl"); }

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
