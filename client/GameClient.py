import asyncio
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from ..locations.Locations import aomLocationData, aomLocationType, location_id_to_name, SHOP_SLOT_ORDER
from ..items.Items import (
    aomItemData,
    AtlanteanMythUnitUnlock,
    AtlanteanUnitUnlockProgression,
    AtlanteanUnitUnlockUseful,
    MythUnitUnlockFiller,
    MythUnitUnlockProgression,
    MythUnitUnlockUseful,
    UnitUnlockProgression,
    UnitUnlockUseful,
)

logger = logging.getLogger("Client")

# -----------------------------------------------------------------------
# Item → proto unit name mapping
# Used by write_aom_state to generate APForbidItemGatedUnits().
# Only items that gate trainable units are included; resource/hero/etc.
# items have no entry here.
# -----------------------------------------------------------------------

_ITEM_TO_UNITS: dict[int, list[str]] = {}
for _item in aomItemData:
    _t = _item.type
    if isinstance(_t, (UnitUnlockProgression, UnitUnlockUseful,
                       AtlanteanUnitUnlockProgression, AtlanteanUnitUnlockUseful)):
        _ITEM_TO_UNITS[_item.id] = [_t.unit_name]
    elif isinstance(_t, (MythUnitUnlockProgression, MythUnitUnlockUseful,
                         MythUnitUnlockFiller, AtlanteanMythUnitUnlock)):
        _ITEM_TO_UNITS[_item.id] = list(_t.units)

# -----------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------

AI_OUTPUT_FILENAME = "MythRetoldAIOutputPlayer12.txt"

MOD_AI_DIR_NAME = "fott_ap_campaign"
APAI_INIT_FILENAME = "ap_ai_init.xs"
APAI_RUNTIME_FILENAME = "ap_ai_runtime.xs"

TRIGGER_FOLDER_NAME  = "trigger"
CACHE_DIR_NAME       = "ap_randomizer_cache"
AOM_STATE_FILENAME   = "aom_state.xs"

AP_CHECK_PREFIX  = "AP_CHECK:"
AP_LOCKED_PREFIX = "AP_LOCKED:"
AP_SHOP_PREFIX   = "AP_SHOP:"
AP_TRAP_PREFIX   = "AP_TRAP_FIRED:"

GEM_ITEM_ID = 9998  # aomItemData.GEM
SHOP_SCENARIO_ID = 0  # reserved scenario ID for the shop

# Victory location IDs for scenarios 1-31 (scenario 32 is the goal, not a gem).
# campaign_val * 100 + chapter = scenario_id; victory = BASE_ID + scenario_id * 100
_BASE_ID = 0x3B0000
VICTORY_LOCATION_IDS: frozenset = frozenset(
    _BASE_ID + (campaign_val * 100 + chapter) * 100
    for campaign_val, chapters in [(1, range(1,11)), (2, range(1,11)), (3, range(1,11)), (4, range(1,2))]
    for chapter in chapters
)


# -----------------------------------------------------------------------
# Context
# -----------------------------------------------------------------------

@dataclass
class AoMGameContext:
    running: bool = True
    user_folder: str = ""
    received_items: list[int] = field(default_factory=list)
    sent_checks: set[int] = field(default_factory=set)
    client_interface: object = None
    # Slot data cached on connect for state file logic
    final_mode: int = -1           # 0=beat_x, 1=always_open, 2=atlantis_key
    x_scenarios_threshold: int = 0  # only used when final_mode == 0
    random_major_gods: bool = False
    update_buildings_for_random_god: bool = True
    god_assignments: dict = None         # scenario_id (int) → major_god int
    minor_god_assignments: dict = None   # scenario_id (int) → [tech_name, ...]\n
    archaic_forbids: dict = None         # scenario_id (int) → [unit_name, ...]
    # Cache identity — set on connect, used to build cache_folder path
    ap_server:   str = ""   # e.g. "archipelago.gg:38281"
    ap_seed:     str = ""   # seed_name from RoomInfo
    ap_slot:     str = ""   # slot name (auth) the player connected with
    # Shop state
    wins_to_open_shop: int = 5
    world_id: int = 0
    gem_shop_enabled: bool = True
    trap_queue: list  = field(default_factory=list)   # list of trap_type ints
    trap_ack_nonce: int = 0                           # written to aom_state.xs
    traps_fired_this_scenario: int = 0                 # reset each scenario load
    purchased_slots: set  = field(default_factory=set)
    shop_obelisk_assignments: dict = field(default_factory=dict)  # obelisk_id → [loc_id,...]
    shop_item_details: dict = field(default_factory=dict)         # loc_id → {player, name, cls}
    shop_hint_config: dict  = field(default_factory=dict)         # slot_id → {type, ...}
    shop_slot_order: list   = field(default_factory=list)
    # Checks the AP server has already confirmed — used for in-memory
    # deduplication only. Never persisted to disk.
    server_known_checks: set[int] = field(default_factory=set)
    # Locked-scenario warnings already shown this connection.
    locked_warning_campaigns: set[str] = field(default_factory=set)
    # Reserved for compatibility with older logic. The runtime log parser now
    # scans from byte 0 on every poll after the connect-time log purge.
    log_start_offset: int = 0

    @property
    def trigger_folder(self) -> Path:
        return Path(self.user_folder) / TRIGGER_FOLDER_NAME

    @property
    def cache_folder(self) -> Path:
        """Per-session cache directory, uniquely scoped by server/seed/slot/world_id.
        Sanitises each component so the path is valid on Windows.
        """
        def _sanitise(s: str) -> str:
            # Replace characters invalid in Windows directory names
            for ch in r'\/:*?"<>|':
                s = s.replace(ch, "_")
            return s.strip("._") or "_"

        server  = _sanitise(self.ap_server  or "unknown_server")
        seed    = _sanitise(self.ap_seed    or "unknown_seed")
        slot    = _sanitise(self.ap_slot    or "unknown_slot")
        world   = str(self.world_id)
        return (Path(self.user_folder) / CACHE_DIR_NAME / server / seed / slot / world)

    @property
    def ai_output_file(self) -> Path:
        # user_folder is e.g. C:/Users/Philip/Games/Age of Mythology Retold/76561198039446386
        # logs are at:         C:/Users/Philip/Games/Age of Mythology Retold/temp/Logs
        return Path(self.user_folder).parent / "temp" / "Logs" / AI_OUTPUT_FILENAME

    @property
    def aom_state_file(self) -> Path:
        return self.trigger_folder / AOM_STATE_FILENAME

    def ap_ai_init_file(self, mods_local_dir: Path) -> Path:
        # ap_ai_init.xs must live in the user-level Game\AI folder.
        return Path(self.user_folder) / "Game" / "AI" / APAI_INIT_FILENAME

    def ap_ai_runtime_file(self, mods_local_dir: Path) -> Path:
        # ap_ai_runtime.xs must live in the user-level Game\AI folder.
        return Path(self.user_folder) / "Game" / "AI" / APAI_RUNTIME_FILENAME


# -----------------------------------------------------------------------
# apai.xs generation
# -----------------------------------------------------------------------

def _load_ap_ai_runtime_template_text() -> str:
    r"""
    Load ap_ai_runtime.xs from the triggers folder inside the apworld zip.

    __file__ for a zip-imported module is a virtual path like:
        C:\...\aom.apworld\aom\client\GameClient.py
    That path doesn't exist on disk, so Path.read_text() fails.
    We walk up __file__'s parents to find the .apworld boundary, then
    use zipfile.ZipFile to read the template directly from the archive.
    """
    import zipfile as _zf
    try:
        # Find the .apworld file in the path hierarchy
        apworld_path = None
        for parent in [Path(__file__)] + list(Path(__file__).parents):
            if str(parent).lower().endswith(".apworld") and parent.is_file():
                apworld_path = parent
                break
        if apworld_path:
            with _zf.ZipFile(apworld_path, "r") as z:
                internal = f"aom/triggers/{APAI_RUNTIME_FILENAME}"
                if internal in z.namelist():
                    return z.read(internal).decode("utf-8")
            logger.error(f"{APAI_RUNTIME_FILENAME} not found inside {apworld_path}")
        else:
            # Not running from a zip — try plain filesystem (dev/test mode)
            template_path = Path(__file__).parent.parent / "triggers" / APAI_RUNTIME_FILENAME
            if template_path.exists():
                return template_path.read_text(encoding="utf-8")
            logger.error(f"Could not locate apworld zip and {template_path} does not exist")
    except Exception as ex:
        logger.error(f"Failed to load {APAI_RUNTIME_FILENAME} template: {ex}")
    # Minimal fallback — trap system won't work but checks still will.
    return (
        'extern int gAPCategory = -1;\n\n'
        'void main()\n'
        '{\n'
        '   gAPCategory = aiAddEchoCategory("Archipelago");\n'
        '   aiEcho("APAI startup.");\n'
        '}\n\n'
        'rule APHeartbeat\n'
        'minInterval 30\n'
        'active\n'
        '{\n'
        '   aiEcho("APAI heartbeat.");\n'
        '}\n'
    )


def _strip_generated_ap_functions(template_text: str) -> str:
    """
    Remove old generated AP bridge functions so the template can safely be
    regenerated without duplicate symbol definitions.
    """
    stripped_lines: list[str] = []
    for line in template_text.splitlines():
        s = line.strip()
        if s.startswith("void APCheck_"):
            continue
        if s.startswith("void APLocked_"):
            continue
        if s.startswith("void APShop_"):
            continue
        if s.startswith("void APShopSignal("):
            continue
        if s.startswith("void APTrapFiredSignal("):
            continue
        stripped_lines.append(line.rstrip())
    return "\n".join(stripped_lines).rstrip() + "\n"


def generate_ap_ai_xs(ctx: AoMGameContext, mods_local_dir: Path) -> None:
    r"""
    Generate Game\AI\ap_ai_runtime.xs from the packaged triggers/ap_ai_runtime.xs
    template, then append generated AP bridge functions for Player 12.
    Called on every client connect so the live runtime AI file is always current.
    """
    # mods_local_dir kept for call-site compatibility.
    _ = mods_local_dir

    template_text = _strip_generated_ap_functions(_load_ap_ai_runtime_template_text())

    lines = [
        template_text.rstrip(),
        "",
        "// -----------------------------------------------------------------------",
        "// AUTO-GENERATED AP BRIDGE FUNCTIONS",
        "// -----------------------------------------------------------------------",
        "",
    ]

    generated_count = 0

    for location in aomLocationData:
        if location.type == aomLocationType.COMPLETION:
            continue
        loc_id = location.id
        lines.append(f'void APCheck_{loc_id}() {{ aiEcho("{AP_CHECK_PREFIX}{loc_id}"); }}')
        generated_count += 1

    lines.append("")

    for campaign in ["Greek", "Egyptian", "Norse", "Final"]:
        lines.append(f'void APLocked_{campaign}() {{ aiEcho("{AP_LOCKED_PREFIX}{campaign}"); }}')
        generated_count += 1

    lines.append("")

    for slot_index in range(1, len(SHOP_SLOT_ORDER) + 1):
        lines.append(f'void APShop_{slot_index}() {{ aiEcho("{AP_SHOP_PREFIX}IDX:{slot_index}"); }}')
        generated_count += 1

    lines.append("")
    lines.append(f'void APTrapFiredSignal() {{ aiEcho("AP_TRAP_FIRED:"); }}')

    lines.append("")
    content = "\n".join(lines)

    runtime_path = ctx.ap_ai_runtime_file(mods_local_dir)
    runtime_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        runtime_path.write_text(content, encoding="utf-8")
        logger.info(f"Generated {runtime_path} with {generated_count} AP bridge functions.")
    except Exception as ex:
        logger.error(f"Failed to write {APAI_RUNTIME_FILENAME}: {ex}")

# -----------------------------------------------------------------------
# aom_state.xs writing
# -----------------------------------------------------------------------

def _get_has_atlantis(ctx: AoMGameContext, received_set: set) -> int:
    """
    Returns 9004 if the player should have Atlantis access, 9000 otherwise.
    In beat_x_scenarios mode, derives access from the local sent_checks count
    so the game state matches the UI without relying on AP event locations.
    In atlantis_key mode, requires the actual item to be received.
    In always_open mode, always returns 9004.
    """
    ATLANTIS_KEY = 3510
    if ATLANTIS_KEY in received_set:
        return 9004
    if ctx.final_mode == 1:  # always_open
        return 9004
    if ctx.final_mode == 0 and ctx.x_scenarios_threshold > 0:  # beat_x_scenarios
        BASE_ID = 0x3B0000
        from ..locations.Locations import aomLocationData, aomLocationType
        beaten = sum(
            1 for loc in aomLocationData
            if loc.type == aomLocationType.VICTORY
            and loc.scenario.global_number <= 30
            and loc.id in ctx.sent_checks
        )
        if beaten >= ctx.x_scenarios_threshold:
            return 9004
    return 9000


# -----------------------------------------------------------------------
# Building transformation data for UpdateBuildingsForRandomGod
# -----------------------------------------------------------------------
_GOD_TO_CIV = {
    1: "Greek", 2: "Greek", 3: "Greek",        # Zeus, Poseidon, Hades
    4: "Egyptian", 5: "Egyptian", 6: "Egyptian", # Ra, Isis, Set
    7: "Norse", 8: "Norse", 9: "Norse",          # Thor, Odin, Loki
    10: "Atlantean", 11: "Atlantean", 12: "Atlantean",  # Kronos, Oranos, Gaia
}
_CLASSICAL_BLDGS = {
    "Greek":     ["MilitaryAcademy", "ArcheryRange", "Stable"],
    "Egyptian":  ["Barracks"],
    "Norse":     ["Longhouse", "GreatHall"],
    "Atlantean": ["MilitaryBarracks", "CounterBarracks"],
}
_HEROIC_BLDGS = {
    "Greek":     ["Fortress"],
    "Egyptian":  ["MigdolStronghold", "SiegeWorks"],
    "Norse":     ["HillFort"],
    "Atlantean": ["Palace"],
}
# Scenarios 7 and 26 use player 3 instead of player 1 for building transforms.
# Scenario 26 also transforms players 4 and 5.
_BLDG_PLAYER_OVERRIDE = {7: [3], 26: [3, 4, 5]}

def write_aom_state(ctx: AoMGameContext) -> None:

    """
    Write aom_state.xs to the trigger folder.
    Contains received item IDs, campaign ID, and civ override.
    XS reads this at scenario load time via include.
    """
    count = len(ctx.received_items)
    # XS arrays require size >= 1
    array_size = max(count, 1)

    # Derive campaign_id from the most recently received check location ID
    # location_id = BASE_ID + scenario_id * 100 + local_id
    # campaign_id = (location_id - BASE_ID) // 10000
    BASE_ID = 0x3B0000
    campaign_id = 0
    for loc_id in ctx.sent_checks:
        derived = (loc_id - BASE_ID) // 10000
        if 1 <= derived <= 4:
            campaign_id = derived
            break

    # Prepend flags at indices 0-5:
    #   [0] = 9001 if Greek Scenarios in items,    else 9000
    #   [1] = 9002 if Egyptian Scenarios in items, else 9000
    #   [2] = 9003 if Norse Scenarios in items,    else 9000
    #   [3] = 9004 if Atlantis Key in items,       else 9000
    #   [4] = 9100 + campaign_id
    #   [5] = 9010 if random_major_gods is on,             else 9000
    #   [6] = 9010 if gem_shop is enabled,          else 9000
    # Real items start at index 7.
    GREEK_SCENARIOS    = 3500
    EGYPTIAN_SCENARIOS = 3501
    NORSE_SCENARIOS    = 3502
    ATLANTIS_KEY       = 3510
    received_set = set(ctx.received_items)
    flags = [
        9001 if GREEK_SCENARIOS    in received_set else 9000,
        9002 if EGYPTIAN_SCENARIOS in received_set else 9000,
        9003 if NORSE_SCENARIOS    in received_set else 9000,
        _get_has_atlantis(ctx, received_set),
        9100 + campaign_id,                      # index 4: campaign ID
        9010 if ctx.random_major_gods else 9000,         # index 5: random_major_gods flag
        9010 if ctx.gem_shop_enabled else 9000,  # index 6: gem_shop flag
    ]
    items_with_flags = flags + list(ctx.received_items)
    total = len(items_with_flags)

    lines = []
    lines.append("void APInitItems()")
    lines.append("{")
    lines.append(f"    gAPItemCount = {total};")
    lines.append(f"    gAPItems = new int({total}, 0);")
    for i, item_id in enumerate(items_with_flags):
        lines.append(f"    gAPItems[{i}] = {item_id};")
    lines.append("}")

    # Random_Major_Gods — APInitGods() sets quest vars for /gods command
    lines.append("")
    lines.append("void APInitGods()")
    lines.append("{")
    # Iterate all scenario IDs that have vanilla god assignments (FotT + NA + GG)
    all_scenario_ids = sorted(ctx.god_assignments.keys()) if (ctx.random_major_gods and ctx.god_assignments) else list(range(1, 33))
    for scenario_id in all_scenario_ids:
        if ctx.random_major_gods and ctx.god_assignments and scenario_id in ctx.god_assignments:
            god_val = ctx.god_assignments[scenario_id]
        else:
            god_val = 0
        lines.append(f"    trQuestVarSet(\"APGod{scenario_id}\", {god_val});")
    lines.append("}")

    # Random_Major_Gods — APInitStartingAgeTechs() grants starting age techs per scenario
    lines.append("")
    lines.append("void APInitStartingAgeTechs()")
    lines.append("{")
    lines.append("    int scenId = trQuestVarGet(\"APScenarioID\");")
    if ctx.random_major_gods and ctx.minor_god_assignments:
        for scenario_id in sorted(ctx.minor_god_assignments.keys()):
            techs = ctx.minor_god_assignments.get(scenario_id) or []
            if not techs:
                continue
            lines.append(f"    if (scenId == {scenario_id})")
            lines.append("    {")
            for tech in techs:
                lines.append(f"        trTechSetStatus(1, {tech}, 2);")
            lines.append("    }")
    lines.append("}")

    # APForbidVanillaArchaicUnits — forbids units from vanilla god/civ
    # that should not be available when the assigned god differs.
    lines.append("")
    lines.append("void APForbidVanillaArchaicUnits()")
    lines.append("{")
    lines.append("    int scenId = trQuestVarGet(\"APScenarioID\");")
    if ctx.archaic_forbids:
        for scenario_id, units in ctx.archaic_forbids.items():
            lines.append(f"    if (scenId == {scenario_id})")
            lines.append("    {")
            for unit in units:
                lines.append(f"        trForbidProtounit(1, \"{unit}\");")
            lines.append("    }")
    lines.append("}")

    # APForbidItemGatedUnits — forbids every unit whose unlock item has not yet
    # been received.  Units whose items HAVE been received are not touched at
    # all, so the game's natural civ / age / minor-god prerequisites still apply.
    lines.append("")
    lines.append("void APForbidItemGatedUnits()")
    lines.append("{")
    for item_id, units in _ITEM_TO_UNITS.items():
        if item_id not in received_set:
            for unit in units:
                lines.append(f"    trForbidProtounit(1, \"{unit}\");")
    lines.append("}")

    # ----------------------------------------------------------------
    # APShopStateInit — sets shop globals and per-obelisk labels.
    # ----------------------------------------------------------------

    PROG_INFO_ID   = 9997
    info_level     = sum(1 for i in ctx.received_items if i == PROG_INFO_ID)
    gems_earned    = sum(1 for i in ctx.received_items if i == GEM_ITEM_ID)
    available_gems = max(0, gems_earned - len(ctx.purchased_slots))
    update_bldgs_on = ctx.update_buildings_for_random_god

    def _xs(s): lines.append(s)
    def _cls_rank(c): return {"trap":-1,"filler":0,"useful":1,"progression":2}.get(c,-1)
    def _cls_disp(c): return {"trap":"Trap","filler":"Filler","useful":"Useful","progression":"Advancement"}.get(c,"?")

    _xs("")
    _xs("void APShopStateInit()")
    _xs("{")
    _xs(f"    gAPShopAvailableGems = {available_gems};")
    _xs(f"    gAPShopTierThreshold = {ctx.wins_to_open_shop};")
    _beaten = len(ctx.sent_checks & VICTORY_LOCATION_IDS)
    _xs('    trQuestVarSet("APBeatenScenarios", ' + str(_beaten) + ");")
    _xs('    trQuestVarSet("APRandom_Major_Gods", ' + ('1' if ctx.random_major_gods else '0') + ");")

    for _sid in ctx.shop_slot_order:
        _pv = "true" if _sid in ctx.purchased_slots else "false"
        _xs(f"    gAPShopPurchased_{_sid} = {_pv};")
        _xs('    trQuestVarSet("APPurchased_' + _sid + '", ' + ('1' if _sid in ctx.purchased_slots else '0') + ");")

    for _oid, _lids in ctx.shop_obelisk_assignments.items():
        _det = [ctx.shop_item_details.get(_l) for _l in _lids if ctx.shop_item_details.get(_l)]
        _n   = len(_det)

        # Main recipient = player with most items in this obelisk
        def _main_recipient(det):
            from collections import Counter
            if not det: return "?"
            counts = Counter(d.get("player_name","?") for d in det)
            return counts.most_common(1)[0][0]

        if not _det or info_level == 0:
            _lbl = "? items\\n? is rarest\\n?: main recipient"
        elif info_level == 1:
            _lbl = str(_n) + " items\\n? is rarest\\n?: main recipient"
        elif info_level == 2:
            _top = _cls_disp(max((_d.get("classification","filler") for _d in _det), key=_cls_rank))
            _lbl = str(_n) + " items\\n" + _top + " is rarest\\n?: main recipient"
        elif info_level == 3:
            _top = _cls_disp(max((_d.get("classification","filler") for _d in _det), key=_cls_rank))
            _pl  = _main_recipient(_det)
            _lbl = str(_n) + " items\\n" + _top + " is rarest\\n" + _pl + ": main recipient"
        else:
            # Level 4: show count of rarest item type
            _top     = max((_d.get("classification","filler") for _d in _det), key=_cls_rank)
            _top_disp = _cls_disp(_top)
            _top_cnt = sum(1 for _d in _det if _d.get("classification","filler") == _top)
            _pl      = _main_recipient(_det)
            _lbl = (str(_n) + " items\\n" + _top_disp + " is rarest\\n\\n"
                    + str(_top_cnt) + " " + _top_disp + " items\\n" + _pl + ": main recipient")
        _lbl = _lbl.replace('"', '\\\\"'  )
        _xs('    gAPShopLabel_' + _oid + ' = "' + _lbl + '";')

    for _sid, _hcfg in ctx.shop_hint_config.items():
        if _hcfg.get("type") == "progressive_info":
            _lbl = "Better Shop Information"
        else:
            _rng = _hcfg.get("missions_range", (1,2))
            _lbl = "Hints for " + str(_rng[0]) + "-" + str(_rng[1]) + " missions"
        _xs('    gAPShopLabel_' + _sid + ' = "' + _lbl + '";')

    _xs("}")

    # Generate APTrapQueueInit — called from APActivateScenario
    _xs("")
    _xs("void APTrapQueueInit()")
    _xs("{")
    _xs(f"    gAPTrapQueueSize = {len(ctx.trap_queue)};")
    if ctx.trap_queue:
        _xs(f"    gAPTrapQueue = new int({len(ctx.trap_queue)}, 0);")
        for _ti, _tt in enumerate(ctx.trap_queue):
            _xs(f"    gAPTrapQueue[{_ti}] = {_tt};")
    _xs('    trQuestVarSet("APTrapAckNonce", ' + str(ctx.trap_ack_nonce) + ");")
    _xs('    trQuestVarSet("APTrapsFiredThisScenario", 0);')
    _xs("}")

    # Generate APTransformBuildings() — data-only, no tr* calls.
    # Writes scenario→building transform pairs as XS int/string arrays.
    # Execution (tr* calls) lives in archipelago.xs APTransformBuildings().
    update_bldgs_on2 = ctx.update_buildings_for_random_god
    _xs("")
    _xs("extern int      gAPBldgTransformCount = 0;")
    _xs("extern int[]    gAPBldgScen           = default;")
    _xs("extern int[]    gAPBldgPlayer         = default;")
    _xs("extern string[] gAPBldgFrom           = default;")
    _xs("extern string[] gAPBldgTo1            = default;")
    _xs("extern string[] gAPBldgTo2            = default;")
    _xs("")
    _xs("void APLoadBuildingTransforms()")
    _xs("{")
    _xs("    gAPBldgTransformCount = 0;")
    if update_bldgs_on2 and ctx.god_assignments:
        _vanilla_gods2 = {
            1: 2, 2: 2, 3: 2, 4: 2,
            5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
            11: 4, 12: 5, 13: 6, 14: 4, 15: 4,
            16: 3,
            17: 5, 18: 5, 19: 4, 20: 4,
            21: 1,
            22: 8, 23: 8,
            24: 9, 25: 9,
            26: 7, 27: 7, 28: 7,
            29: 8, 30: 8,
            31: 1, 32: 1,
        }
        _pairs = []  # list of (scenId, targetPlayer, fromProto, toProto1, toProto2)
        for _sid, _vgod in sorted(_vanilla_gods2.items()):
            _rgod = ctx.god_assignments.get(_sid, _vgod)
            _vc   = _GOD_TO_CIV.get(_vgod, "Greek")
            _rc   = _GOD_TO_CIV.get(_rgod, "Greek")
            if _vc == _rc:
                continue
            _players = _BLDG_PLAYER_OVERRIDE.get(_sid, [1])
            for _tp in _players:
                for _from in _CLASSICAL_BLDGS[_vc]:
                    _to = _CLASSICAL_BLDGS[_rc]
                    _pairs.append((_sid, _tp, _from, _to[0], _to[1] if len(_to)>1 else ""))
                for _from in _HEROIC_BLDGS[_vc]:
                    _to = _HEROIC_BLDGS[_rc]
                    _pairs.append((_sid, _tp, _from, _to[0], _to[1] if len(_to)>1 else ""))
        # Size all arrays before assigning by index (XS requires this)
        _xs(f"    gAPBldgScen   = new int({len(_pairs)}, 0);")
        _xs(f"    gAPBldgPlayer = new int({len(_pairs)}, 1);")
        _xs(f'    gAPBldgFrom   = new string({len(_pairs)}, "");')
        _xs(f'    gAPBldgTo1    = new string({len(_pairs)}, "");')
        _xs(f'    gAPBldgTo2    = new string({len(_pairs)}, "");')
        for _i, (_sid, _tp, _fr, _t1, _t2) in enumerate(_pairs):
            _xs(f'    gAPBldgScen[{_i}]    = {_sid};')
            _xs(f'    gAPBldgPlayer[{_i}]  = {_tp};')
            _xs(f'    gAPBldgFrom[{_i}]    = "{_fr}";')
            _xs(f'    gAPBldgTo1[{_i}]     = "{_t1}";')
            _xs(f'    gAPBldgTo2[{_i}]     = "{_t2}";')
        _xs(f"    gAPBldgTransformCount = {len(_pairs)};")
    _xs("}")

    # Set APUpdateBldgs quest var in APShopStateInit so archipelago.xs knows option state
    # Patch it into the existing APShopStateInit by inserting before closing brace
    # We do this by re-finding and replacing the end of APShopStateInit generation



    content = "\n".join(lines) + "\n"

    try:
        ctx.trigger_folder.mkdir(parents=True, exist_ok=True)
        ctx.aom_state_file.write_text(content, encoding="utf-8")
        logger.debug(f"Wrote aom_state.xs with {len(ctx.received_items)} items.")
    except Exception as ex:
        logger.error(f"Failed to write aom_state.xs: {ex}")


# -----------------------------------------------------------------------
# AI output file reading
# -----------------------------------------------------------------------

def save_trap_state(ctx: AoMGameContext) -> None:
    """Persist trap_queue to the session cache directory."""
    import json
    try:
        ctx.cache_folder.mkdir(parents=True, exist_ok=True)
        path = ctx.cache_folder / "ap_trap_state.json"
        path.write_text(json.dumps({"trap_queue": ctx.trap_queue}), encoding="utf-8")
    except Exception as ex:
        logger.warning(f"Failed to save trap state: {ex}")


def load_trap_state(ctx: AoMGameContext) -> None:
    """Load persisted trap_queue for the current session."""
    import json
    try:
        path = ctx.cache_folder / "ap_trap_state.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            ctx.trap_queue = data.get("trap_queue", [])
            logger.info(f"Loaded trap state: {len(ctx.trap_queue)} trap(s) queued.")
        else:
            ctx.trap_queue = []
    except Exception as ex:
        logger.warning(f"Failed to load trap state: {ex}")
        ctx.trap_queue = []


def save_shop_state(ctx: AoMGameContext) -> None:
    """Persist purchased_slots to the session cache directory."""
    import json
    try:
        ctx.cache_folder.mkdir(parents=True, exist_ok=True)
        path = ctx.cache_folder / "ap_shop_state.json"
        path.write_text(json.dumps({"purchased_slots": list(ctx.purchased_slots)}), encoding="utf-8")
    except Exception as ex:
        logger.warning(f"Failed to save shop state: {ex}")


def load_shop_state(ctx: AoMGameContext) -> None:
    """Load persisted purchased_slots for the current session."""
    import json
    try:
        path = ctx.cache_folder / "ap_shop_state.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            ctx.purchased_slots = set(data.get("purchased_slots", []))
            logger.info(f"Loaded shop state: {len(ctx.purchased_slots)} purchased slot(s).")
        else:
            ctx.purchased_slots = set()
            logger.info("No shop state found for this session — starting fresh.")
    except Exception as ex:
        logger.warning(f"Failed to load shop state: {ex}")
        ctx.purchased_slots = set()


def save_sent_checks(ctx: AoMGameContext) -> None:
    """Persist sent_checks to the session cache directory so dropped checks survive restarts."""
    import json
    try:
        ctx.cache_folder.mkdir(parents=True, exist_ok=True)
        path = ctx.cache_folder / "ap_sent_checks.json"
        path.write_text(json.dumps({"sent_checks": list(ctx.sent_checks)}), encoding="utf-8")
    except Exception as ex:
        logger.warning(f"Failed to save sent checks: {ex}")


def load_sent_checks(ctx: AoMGameContext) -> None:
    """Load persisted sent_checks for the current session."""
    import json
    try:
        path = ctx.cache_folder / "ap_sent_checks.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            ctx.sent_checks = set(data.get("sent_checks", []))
            logger.info(f"Loaded sent checks: {len(ctx.sent_checks)} check(s).")
        else:
            ctx.sent_checks = set()
    except Exception as ex:
        logger.warning(f"Failed to load sent checks: {ex}")
        ctx.sent_checks = set()


def _resolve_shop_signal(ctx: AoMGameContext, slot_id: str) -> list[int]:
    """
    Process a shop purchase signal for the given slot_id.
    For item slots: returns AP location IDs to check.
    For hint slots: fires hint requests and returns empty list.
    Marks the slot as purchased and rewrites aom_state.xs either way.
    """
    if not slot_id:
        logger.warning("Empty shop signal slot_id.")
        return []

    if slot_id in ctx.purchased_slots:
        logger.debug(f"Shop slot {slot_id} already purchased, ignoring duplicate signal.")
        return []

    ctx.purchased_slots.add(slot_id)
    logger.info(f"Shop purchase: {slot_id}")
    save_shop_state(ctx)
    write_aom_state(ctx)
    # Update GUI gems/shops count immediately after purchase
    if ctx.client_interface is not None:
        from .ApClient import _update_atlantis_ui
        _update_atlantis_ui(ctx.client_interface)

    if "ITEM" in slot_id:
        loc_ids = ctx.shop_obelisk_assignments.get(slot_id, [])
        logger.info(f"  → checking {len(loc_ids)} item location(s)")
        return loc_ids

    if "HINT" in slot_id:
        _send_shop_hints(ctx, slot_id)
        return []

    return []


def _send_shop_hints(ctx: AoMGameContext, slot_id: str) -> None:
    """Send mission hints or fire Progressive Shop Info check for a purchased hint slot."""
    hint_cfg = ctx.shop_hint_config.get(slot_id)
    if not hint_cfg or ctx.client_interface is None:
        return

    if hint_cfg.get("type") == "progressive_info":
        # This is a Progressive Shop Info purchase — fire the location check
        loc_id = hint_cfg.get("loc_id")
        if loc_id and loc_id not in ctx.sent_checks:
            ctx.sent_checks.add(loc_id)
            save_sent_checks(ctx)
            asyncio.ensure_future(ctx.client_interface.on_location_received(loc_id))
            logger.info(f"Progressive Shop Info purchased: {slot_id} → location {loc_id}")
            logger.info("Shop Information upgraded! Go back to the shop to see more details.")
        return

    if hint_cfg.get("type") == "mission_hints":
        missions_range = hint_cfg.get("missions_range", (1, 2))
        ctx.client_interface.send_mission_hints(missions_range)


def read_new_checks(ctx: AoMGameContext) -> list[int]:
    """
    Read the entire AI output log from byte 0 on every poll.

    The log is purged on connect, so scanning from the start of the recreated
    file is safe and aggressively picks up newly written AP_CHECK lines even if
    offset tracking would otherwise become misaligned.

    Deduplication is still handled by in-memory and persisted state:
      - AP_CHECK / AP_SHOP -> sent_checks and server_known_checks
      - AP_TRAP_FIRED      -> trap_ack_nonce
      - AP_LOCKED          -> locked_warning_campaigns
    """
    import re
    ai_file = ctx.ai_output_file

    if not ai_file.exists():
        return []

    try:
        file_bytes = ai_file.read_bytes()
    except OSError:
        return []

    if not file_bytes:
        return []

    # Ensure even byte count for UTF-16-LE alignment.
    if len(file_bytes) % 2 != 0:
        file_bytes = file_bytes[:-1]

    content = file_bytes.decode("utf-16-le", errors="ignore")

    # If content doesn't end on a line boundary AoM is mid-write; truncate to
    # the last complete line so we never process a partial signal.
    last_newline = max(content.rfind("\n"), content.rfind("\r"))
    if last_newline >= 0 and last_newline < len(content) - 1:
        content = content[:last_newline + 1]

    new_checks = []
    trap_signals = 0   # AP_TRAP_FIRED lines since the last "APAI startup." in this file
    in_current_session = False

    try:
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            # Each new scenario writes "APAI startup." as the first log line.
            # Reset trap counters when we see it so trap handling is scoped to
            # the current scenario.
            if "APAI startup." in line:
                trap_signals = 0
                ctx.trap_ack_nonce = 0
                in_current_session = True
                continue

            # Ignore anything before the first startup line in the current log.
            if not in_current_session:
                continue

            if AP_LOCKED_PREFIX in line:
                m = re.search(r"AP_LOCKED:(\S+)", line)
                campaign = m.group(1) if m else "unknown"
                if campaign not in ctx.locked_warning_campaigns:
                    logger.warning(
                        f"Archipelago: You need the {campaign} Scenarios item to play this campaign."
                    )
                    ctx.locked_warning_campaigns.add(campaign)
                continue

            if "AP_TRAP_FIRED:" in line:
                trap_signals += 1
                continue

            if AP_SHOP_PREFIX in line:
                m = re.search(r"AP_SHOP:IDX:(\d+)", line)
                if m:
                    try:
                        slot_num = int(m.group(1))
                        from ..locations.Locations import SHOP_SLOT_ORDER
                        slot_id = SHOP_SLOT_ORDER[slot_num - 1] if 1 <= slot_num <= len(SHOP_SLOT_ORDER) else ""
                    except (ValueError, IndexError):
                        slot_id = ""
                else:
                    m2 = re.search(r"AP_SHOP:(\S+)", line)
                    slot_id = m2.group(1) if m2 else ""
                if not slot_id:
                    logger.warning(f"Unrecognised shop signal in line: {line!r}")
                    continue
                shop_checks = _resolve_shop_signal(ctx, slot_id)
                for loc_id in shop_checks:
                    if loc_id not in ctx.sent_checks and loc_id not in ctx.server_known_checks:
                        new_checks.append(loc_id)
                        ctx.sent_checks.add(loc_id)
                if shop_checks:
                    save_sent_checks(ctx)
                continue

            m = re.search(r"AP_CHECK:(\d+)", line)
            if not m:
                continue
            loc_id = int(m.group(1))
            if loc_id not in ctx.sent_checks and loc_id not in ctx.server_known_checks:
                new_checks.append(loc_id)
                ctx.sent_checks.add(loc_id)

    except Exception as ex:
        logger.error(f"Failed to parse AI output file: {ex}")

    # Process trap signals: trap_signals counts only AP_TRAP_FIRED lines since
    # the last "APAI startup." line, so it's already scoped to the current
    # scenario. trap_ack_nonce tracks how many we've popped this scenario.
    new_trap_count = max(0, trap_signals - ctx.trap_ack_nonce)
    if new_trap_count > 0:
        for _ in range(new_trap_count):
            if ctx.trap_queue:
                fired = ctx.trap_queue.pop(0)
                logger.info(f"Trap fired: type {fired}, {len(ctx.trap_queue)} remaining")
            ctx.trap_ack_nonce += 1
        save_trap_state(ctx)
        write_aom_state(ctx)

    if new_checks:
        save_sent_checks(ctx)
    return new_checks

# -----------------------------------------------------------------------
# Items received
# -----------------------------------------------------------------------

def on_items_received(ctx: AoMGameContext, items: list[int]) -> None:
    """
    Called by ApClient when the AP server sends new items.
    Updates received_items and rewrites aom_state.xs.
    """
    ctx.received_items = items
    write_aom_state(ctx)


# -----------------------------------------------------------------------
# Game loop
# -----------------------------------------------------------------------

async def game_loop(ctx: AoMGameContext) -> None:
    """
    Main polling loop. Runs while the client is connected.
    Polls the AI output file every 2 seconds for new checks.
    """
    logger.info("AoMR game loop started. Watching for scenario completions...")
    logger.info(f"Watching file: {ctx.ai_output_file}")
    logger.info("Age of Mythology: Retold client commands:")
    logger.info("  /status                — show connection info and Atlantis Key progress")
    logger.info("  /progress (/scenarios) — list beaten, in-progress, and untouched scenarios")
    logger.info("  /gods                  — show randomized god per scenario (random_major_gods only)")
    logger.info("  /greek /egypt /norse /atlantean — show unit/myth/age unlock items for that civ")
    logger.info("  /generic               — show all other received items (heroes, resources, etc.)")

    # The log is read from byte 0 on every poll; no offset initialization needed.
    ai_file = ctx.ai_output_file
    while ctx.running:
        new_checks = read_new_checks(ctx)

        if new_checks and ctx.client_interface is not None:
            for loc_id in new_checks:
                loc_name = location_id_to_name.get(loc_id, str(loc_id))
                logger.debug(f"Check found: {loc_name}")
                for attempt in range(3):
                    try:
                        await ctx.client_interface.on_location_received(loc_id)
                        break
                    except Exception as ex:
                        if attempt < 2:
                            logger.warning(f"Send attempt {attempt+1} failed for {loc_name}: {ex}. Retrying...")
                            await asyncio.sleep(1.0)
                        else:
                            logger.error(f"Failed to send check {loc_id} ({loc_name}) after 3 attempts: {ex}. Will retry on reconnect.")

        await asyncio.sleep(2.0)