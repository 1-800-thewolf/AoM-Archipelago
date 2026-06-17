# =============================================================================
# Age of Mythology Retold — Region graph builder
# =============================================================================
#
# Archipelago describes a player's world as a graph of `Region`s connected by
# `Entrance`s.  Locations live inside Regions; reachability of a location =
# reachability of its Region from `Menu`.
#
# Topology produced by this module:
#
#     Menu
#      ├── Fall of the Trident: Greek          ── star ── 10 scenario regions
#      ├── Fall of the Trident: Egyptian       ── star ── 10 scenario regions
#      ├── Fall of the Trident: Norse          ── star ── 10 scenario regions
#      ├── Fall of the Trident: Final          ── star ── 2  scenario regions
#      ├── New Atlantis (optional)             ── star ── 12 scenario regions
#      ├── Golden Gift  (optional)             ── star ── 4  scenario regions
#      ├── PILLARS OF THE GODS (optional)      ── star ── 9  scenario regions
#      └── Shop         (optional)             ── all shop / hint locations
#
# Star topology is intentional: once a campaign section is unlocked, every
# scenario in it is independently reachable.  Per-scenario access (age unlocks,
# point requirements) is layered on top by `rules/Rules.py` via `set_rule()`
# on the campaign→scenario entrances created here.
#
# This module is purely structural — it does NOT install access rules.  Rules
# are applied by Rules.py after `create_regions` runs (Archipelago calls
# `create_regions` then `create_items` then `set_rules` in that order).
#
# -----------------------------------------------------------------------------
# EXTENDING
# -----------------------------------------------------------------------------
# * Adding a campaign: add it to `aomCampaignData` (locations/Campaigns.py).
#   This module iterates over that enum, so new campaigns appear automatically
#   provided their scenarios are listed in `aomScenarioData` and their
#   locations populate `REGION_TO_LOCATIONS`.
# * Adding a scenario: add the scenario record to `aomScenarioData` and its
#   locations to `aomLocationData` — `create_regions` walks both.
# * Adding an alternate region (e.g. a tavern hub): build a new region with
#   `create_region`, connect it from `Menu` via `connect_regions`, and supply
#   any locations.  Add a Rules.py rule for the entrance if access should be
#   gated.
# =============================================================================

from BaseClasses import Location, MultiWorld, Region

from ..locations.Campaigns import aomCampaignData
from ..locations.Locations import (
    REGION_TO_LOCATIONS, aomLocationData, aomLocationType,
)
from ..locations.Scenarios import CAMPAIGN_TO_SCENARIOS, aomScenarioData


# Root region the player starts in — every reachability search starts here.
# Rules.py uses this name when looking up the menu region.
MENU_REGION_NAME = "Menu"


def create_region(
    multiworld: MultiWorld,
    player: int,
    region_name: str,
    locations: list[aomLocationData] | None = None,
) -> Region:
    """
    Create a region and attach any locations passed in.

    Args:
        multiworld:  The Archipelago `MultiWorld`. The new region is appended
                     to `multiworld.regions` so the framework can find it.
        player:      Slot id of the local player. Every region/location is
                     scoped per-player.
        region_name: Display name. Must be unique within this player's slot
                     and must match what Rules.py later expects (Rules.py
                     resolves regions by string name).
        locations:   Optional list of `aomLocationData` to attach to the
                     region.  Each becomes an Archipelago `Location`.

    Victory locations get a real address (their globally-offset ID) so they
    appear in the data package and can hold normal items.

    Completion locations are AP events — they must be created with address=None.
    AP's LocationStore (C speedup) requires that every location with a real address
    holds an item with a real integer code. Event items have code=None, so giving
    a Completion location a real address causes:
        TypeError: an integer is required
    when the server tries to load the .archipelago file.

    Rules.py places locked event items (code=None) into the Completion locations.
    FOTT_32's visible Victory location remains a normal addressed location because it
    will hold the real Victory item from the item table, not an event item.

    Caller of note: `create_regions` (this module) for every campaign and
    scenario region; the gem shop block at the bottom of `create_regions`
    when `gem_shop` is enabled.
    """
    region = Region(region_name, player, multiworld)

    if locations:
        for location_data in locations:
            address = (
                None
                if location_data.type == aomLocationType.COMPLETION
                else location_data.id
            )
            location = Location(
                player,
                location_data.global_name(),
                address,
                region,
            )
            region.locations.append(location)

    multiworld.regions.append(region)
    return region


def connect_regions(source: Region, target: Region, rule=None) -> None:
    """
    Create a named one-way connection from `source` to `target`, with an
    optional access rule.

    Args:
        source: Region the entrance leaves.
        target: Region the entrance enters.
        rule:   Optional callable `(state) -> bool`.  If provided, the entrance
                is only traversable when the rule returns True.  Most rules in
                this project are installed later by Rules.py via
                `set_rule(entrance, ...)` so this parameter is usually left
                None at construction time.

    The entrance name follows the convention `"{source} -> {target}"` exactly
    so Rules.py can look the entrance up by formatted string.  Do NOT change
    the format without updating every reference in Rules.py.
    """
    entrance = source.connect(target, name=f"{source.name} -> {target.name}")
    if rule is not None:
        entrance.access_rule = rule
    return entrance


def get_campaign_region_name(campaign: aomCampaignData) -> str:
    """
    Return the display name used as a campaign-section region's `name`.

    Example: `aomCampaignData.FOTT_GREEK` → 'Fall of the Trident: Greek'.

    Source of truth lives on the enum (`aomCampaignData.campaign_name`).
    Rules.py references campaign regions through this helper to stay in sync.
    """
    return campaign.campaign_name


def get_scenario_region_name(scenario: aomScenarioData) -> str:
    """
    Return the display name used as an individual scenario region's `name`.

    Format: 'FOTT_1', 'FOTT_22', 'NEW_ATLANTIS_3', 'GOLDEN_GIFT_2', etc.
    Each scenario's `region_name` comes from its `aomScenarioData` enum
    member.  Rules.py uses this helper when applying per-scenario access
    rules so any rename is centralized here.
    """
    return scenario.region_name


def create_regions(multiworld: MultiWorld, player: int) -> None:
    """
    Build the full region graph for the AoM world.

    Graph layout:
    Menu
      -> Greek section     (rule: has Greek Scenarios item)
      -> Egyptian section  (rule: has Egyptian Scenarios item)
      -> Norse section     (rule: has Norse Scenarios item)
      -> Final section     (rule: set by Rules.py based on option)

    Each section connects DIRECTLY to ALL of its scenarios (star topology).
    There is no chain requirement within a section — once the section unlock
    is received, every scenario in that section is independently accessible
    subject only to its own age-unlock and point requirements.

    Menu -> campaign section connections are created WITHOUT rules here so that
    the regions exist before Rules.py runs. Rules.py calls set_rule() on these
    entrances to apply the actual access conditions.
    """
    # Root region
    menu_region = create_region(multiworld, player, MENU_REGION_NAME)

    # Skip alternate campaigns when their YAML toggle is disabled.
    disabled_campaigns = getattr(multiworld.worlds[player], "disabled_campaigns", set())

    # Campaign section regions — connected to Menu unconditionally here.
    # Rules.py owns all section gate logic.
    campaign_regions: dict[aomCampaignData, Region] = {}
    for campaign in aomCampaignData:
        if campaign in disabled_campaigns:
            continue
        campaign_region = create_region(
            multiworld,
            player,
            get_campaign_region_name(campaign),
        )
        campaign_regions[campaign] = campaign_region
        connect_regions(menu_region, campaign_region)

    # Scenario regions — each connects directly to its campaign section region.
    # All scenarios in a section are accessible as soon as the section is unlocked,
    # gated only by their individual age-unlock and point requirements (set in Rules.py).
    relicsanity_on = bool(getattr(multiworld.worlds[player], "relicsanity_enabled", False))
    optional_objectives_on = bool(getattr(multiworld.worlds[player], "optional_objectives_enabled", False))
    for scenario in aomScenarioData:
        if scenario.campaign in disabled_campaigns:
            continue
        scenario_locations = REGION_TO_LOCATIONS.get(scenario, [])
        if not relicsanity_on:
            scenario_locations = [
                loc for loc in scenario_locations
                if loc.type != aomLocationType.RELIC
            ]
        if not optional_objectives_on:
            scenario_locations = [
                loc for loc in scenario_locations
                if loc.type != aomLocationType.OPTIONAL_OBJECTIVE
            ]
        scenario_region = create_region(
            multiworld,
            player,
            get_scenario_region_name(scenario),
            scenario_locations,
        )
        connect_regions(campaign_regions[scenario.campaign], scenario_region)
    # Shop region — only create it when the Gem Shop option is enabled.
    if bool(multiworld.worlds[player].options.gem_shop.value):
        from ..locations.Locations import (ALL_SHOP_ITEM_IDS as _SHOP_IDS,
            ALL_PROGRESSIVE_INFO_IDS as _INFO_IDS,
            SHOP_E_LOCATION_IDS as _SHOP_E_IDS,
            location_id_to_name as _lid2name)
        from BaseClasses import Location as _ShopLoc
        shop_region = create_region(multiworld, player, "Shop")
        _shop_locs = list(_SHOP_IDS) + list(_INFO_IDS)
        # Shop E locations only registered when the budget gate passed in
        # generate_early.  Only the active subset (per_deck_depth × 4) is
        # added — the rest of the reserved Shop E id block stays unused.
        _world = multiworld.worlds[player]
        if getattr(_world, "shop_e_enabled", False):
            _active_e = getattr(_world, "shop_e_active_ids", set()) or set(_SHOP_E_IDS)
            _shop_locs += [lid for lid in _SHOP_E_IDS if lid in _active_e]
        for _loc_id in _shop_locs:
            _name = _lid2name.get(_loc_id)
            if _name:
                _loc = _ShopLoc(player, _name, _loc_id, shop_region)
                shop_region.locations.append(_loc)
        connect_regions(menu_region, shop_region)

    # Key Delivery region — only when the Key Ring system is active
    # (max_keys_on_keyrings >= 2).  Each scenario in an active campaign gets a
    # "Key for ..." virtual location pre-filled with that scenario's Scenario
    # Key item.  Client auto-checks these locations when the corresponding
    # Key Ring item is received, causing the server to broadcast standard
    # ItemSend events ("test found their <Scenario> Scenario Key") for every
    # bundled scenario — same UX as gem-shop purchases.
    _world = multiworld.worlds[player]
    if int(getattr(_world, "max_keys_on_keyrings", 0)) >= 2:
        from ..locations.Locations import (
            KEY_DELIVERY_SCENARIO_TO_LOC_ID as _KD_S2L,
            location_id_to_name as _lid2name,
        )
        from BaseClasses import Location as _KDLoc
        kd_region = create_region(multiworld, player, "Key Deliveries")
        for _scen in aomScenarioData:
            if _scen.campaign in disabled_campaigns:
                continue
            # FOTT_FINAL (31 & 32) never participates in the scenario-key
            # system — access is governed solely by final_scenarios.
            if _scen.campaign.name == "FOTT_FINAL":
                continue
            _loc_id = _KD_S2L.get(_scen.global_number)
            if _loc_id is None:
                continue
            _name = _lid2name.get(_loc_id)
            if not _name:
                continue
            _loc = _KDLoc(player, _name, _loc_id, kd_region)
            kd_region.locations.append(_loc)
        connect_regions(menu_region, kd_region)
