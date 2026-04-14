from BaseClasses import Location, MultiWorld, Region

from ..locations.Campaigns import aomCampaignData
from ..locations.Locations import (
    REGION_TO_LOCATIONS, aomLocationData, aomLocationType,
    WAY_TO_ATLANTIS_LOCATION_ID, WAY_TO_ATLANTIS_LOCATION_NAME,
)
from ..locations.Scenarios import CAMPAIGN_TO_SCENARIOS, aomScenarioData


# Root region the player starts in.
MENU_REGION_NAME = "Menu"


def create_region(
    multiworld: MultiWorld,
    player: int,
    region_name: str,
    locations: list[aomLocationData] | None = None,
) -> Region:
    """
    Create a region and attach any locations passed in.

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
    Create a named one-way connection from source to target, with an optional rule.

    The entrance naming format must match Rules.py exactly.
    """
    entrance = source.connect(target, name=f"{source.name} -> {target.name}")
    if rule is not None:
        entrance.access_rule = rule
    return entrance


def get_campaign_region_name(campaign: aomCampaignData) -> str:
    """
    Region name for a campaign section.

    Example: 'Fall of the Trident: Greek'
    """
    return campaign.campaign_name


def get_scenario_region_name(scenario: aomScenarioData) -> str:
    """
    Region name for an individual scenario.

    Uses enum-style names such as: 'FOTT_1', 'FOTT_22', etc.
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

    # "The Way to Atlantis" lives in the Menu region — always reachable.
    # Rules.py locks the Atlantis Key here (with completion rule) in beat_x mode.
    # In other modes it is a free location filled by the item pool.
    from BaseClasses import Location as _Location
    _way = _Location(player, WAY_TO_ATLANTIS_LOCATION_NAME, WAY_TO_ATLANTIS_LOCATION_ID, menu_region)
    menu_region.locations.append(_way)

    # Campaign section regions — connected to Menu unconditionally here.
    # Rules.py owns all section gate logic.
    campaign_regions: dict[aomCampaignData, Region] = {}
    for campaign in aomCampaignData:
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
    for scenario in aomScenarioData:
        scenario_region = create_region(
            multiworld,
            player,
            get_scenario_region_name(scenario),
            REGION_TO_LOCATIONS.get(scenario, []),
        )
        connect_regions(campaign_regions[scenario.campaign], scenario_region)
    # Shop region — always reachable from Menu. Contains item and progressive info locations.
    # The gem_shop option controls whether these locations are actually filled.
    from ..locations.Locations import (ALL_SHOP_ITEM_IDS as _SHOP_IDS,
        ALL_PROGRESSIVE_INFO_IDS as _INFO_IDS, location_id_to_name as _lid2name)
    from BaseClasses import Location as _ShopLoc
    shop_region = create_region(multiworld, player, "Shop")
    for _loc_id in _SHOP_IDS + _INFO_IDS:
        _name = _lid2name.get(_loc_id)
        if _name:
            _loc = _ShopLoc(player, _name, _loc_id, shop_region)
            shop_region.locations.append(_loc)
    connect_regions(menu_region, shop_region)
