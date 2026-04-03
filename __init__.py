# world/aom/__init__.py

import logging
import time
from typing import Any, ClassVar, Mapping

import settings
from BaseClasses import Item, ItemClassification
from Options import OptionGroup
from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, Type, components, launch as launch_subprocess
import worlds.LauncherComponents as components_module

from .Options import (
    AomOptions,
    FinalScenarios,
    HeroAbilities,
    StartingScenarios,
    StartingGreekAgeUnlocks,
    StartingEgyptianAgeUnlocks,
    StartingNorseAgeUnlocks,
    XScenarios,
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
        OptionGroup("Starting Setup", [
            StartingScenarios,
            StartingGreekAgeUnlocks,
            StartingEgyptianAgeUnlocks,
            StartingNorseAgeUnlocks,
        ]),
        OptionGroup("Final Section", [
            FinalScenarios,
            XScenarios,
        ]),
        OptionGroup("Item Pool", [
            HeroAbilities,
        ]),
    ]


class aomWorld(World):
    web = aomWebWorld()
    """
    Age of Mythology Retold — Fall of the Trident Archipelago world.

    32 scenarios across Greek, Egyptian, Norse, and Final campaign sections.
    Sections unlock independently. Each scenario has its own age and point
    requirements. Beat scenarios to earn items and advance toward Atlantis.
    """

    game = AOMR
    settings: ClassVar[AoMSettings] = AoMSettings
    options_dataclass = AomOptions
    options: AomOptions
    topology_present = True

    item_names = set(item.item_name for item in Items.aomItemData)
    location_names = (
        set(location.global_name() for location in Locations.aomLocationData)
        | {Locations.WAY_TO_ATLANTIS_LOCATION_NAME}
    )

    item_name_to_id = Items.item_name_to_id
    item_id_to_name = Items.item_id_to_name
    location_name_to_id = Locations.location_name_to_id
    location_id_to_name = Locations.location_id_to_name

    def create_regions(self) -> None:
        Regions.create_regions(self.multiworld, self.player)

    def _starting_campaign(self) -> Campaigns.aomCampaignData:
        value = int(self.options.starting_scenarios.value)
        mapping = {
            StartingScenarios.option_greek:    Campaigns.aomCampaignData.FOTT_GREEK,
            StartingScenarios.option_egyptian: Campaigns.aomCampaignData.FOTT_EGYPTIAN,
            StartingScenarios.option_norse:    Campaigns.aomCampaignData.FOTT_NORSE,
        }
        return mapping.get(value, Campaigns.aomCampaignData.FOTT_GREEK)

    def _final_mode(self) -> int:
        return int(self.options.final_scenarios.value)

    def create_item(self, name: str) -> Item:
        item = Items.NAME_TO_ITEM[name]
        return Item(
            item.item_name,
            Items.item_type_to_classification[item.type_data],
            item.id,
            self.player,
        )

    def get_filler_item_name(self) -> str:
        return self.random.choice([item.item_name for item in Items.filler_items])

    def create_items(self) -> None:
        """
        Build the item pool.

        Pool tiers (in order):
        1. Progression items — section unlocks, age unlocks, unit progression
        2. Atlantis Key — always in pool unless beat_x mode (where it is locked
           to "The Way to Atlantis" by Rules.py and not counted here)
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

        # How many age unlocks to precollect per civ
        starting_age_unlocks = {
            "Greek":    int(self.options.starting_greek_age_unlocks.value),
            "Egyptian": int(self.options.starting_egyptian_age_unlocks.value),
            "Norse":    int(self.options.starting_norse_age_unlocks.value),
        }
        age_unlock_counts: dict[str, int] = {"Greek": 0, "Egyptian": 0, "Norse": 0}

        progression_pool: list[Item] = []
        useful_groups: dict[type, list[str]] = {}
        filler_groups: dict[type, list[str]] = {}

        for item in Items.aomItemData:
            item_type = item.type_data
            classification = Items.item_type_to_classification[item_type]

            # Victory is locked to FOTT_32's Victory location by Rules.py
            if item_type == Items.Victory:
                continue

            # Section unlock items
            if item_type == Items.Campaign:
                if item.type.vanilla_campaign == Campaigns.aomCampaignData.FOTT_FINAL:
                    continue  # Final section has no Campaign item
                ap_item = self.create_item(item.item_name)
                if item.type.vanilla_campaign == start_campaign:
                    self.multiworld.push_precollected(ap_item)
                else:
                    progression_pool.append(ap_item)
                continue

            # Atlantis Key — always in pool EXCEPT in beat_x mode where Rules.py
            # locks it to "The Way to Atlantis" (which is excluded from pool math)
            if item_type == Items.FinalUnlock:
                if final_mode != FinalScenarios.option_beat_x_scenarios:
                    progression_pool.append(self.create_item(item.item_name))
                continue

            # Age unlock items — precollect the first N per civ based on options
            if item_type == Items.AgeUnlock:
                culture = item.type.culture  # "Greek", "Egyptian", or "Norse"
                if age_unlock_counts[culture] < starting_age_unlocks[culture]:
                    self.multiworld.push_precollected(self.create_item(item.item_name))
                    age_unlock_counts[culture] += 1
                    continue
                age_unlock_counts[culture] += 1
                progression_pool.append(self.create_item(item.item_name))
                continue

            # Hero ability items — skip if disabled; filler padding covers the gap
            if isinstance(item.type, hero_ability_types) and not hero_abilities_on:
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

        # Visible location count:
        #   All non-COMPLETION locations, minus the locked Victory location,
        #   plus "The Way to Atlantis" ONLY when the key is in the pool
        #   (in beat_x mode the key is locked there separately and not pooled).
        visible_location_count = sum(
            1 for loc in Locations.aomLocationData
            if loc.type != Locations.aomLocationType.COMPLETION
        ) - 1  # FOTT_32 Victory is locked

        if final_mode != FinalScenarios.option_beat_x_scenarios:
            visible_location_count += 1  # Way to Atlantis is a free fill slot

        if len(progression_pool) > visible_location_count:
            raise ValueError(
                f"Progression pool ({len(progression_pool)} items) exceeds "
                f"visible location count ({visible_location_count})."
            )

        itempool: list[Item] = []
        itempool.extend(progression_pool)
        remaining_slots = visible_location_count - len(itempool)

        def round_robin_pick(groups: dict[type, list[str]], slots: int) -> list[Item]:
            """Pull items evenly across groups until slots are filled or groups run dry."""
            picked: list[Item] = []
            local_groups = {
                key: self.random.sample(names, len(names))
                for key, names in groups.items()
                if names
            }
            while slots > 0 and local_groups:
                progressed = False
                for key in list(local_groups.keys()):
                    names = local_groups[key]
                    if not names:
                        del local_groups[key]
                        continue
                    picked.append(self.create_item(names.pop(0)))
                    slots -= 1
                    progressed = True
                    if not names:
                        del local_groups[key]
                    if slots == 0:
                        break
                if not progressed:
                    break
            return picked

        useful_items = round_robin_pick(useful_groups, remaining_slots)
        itempool.extend(useful_items)
        remaining_slots = visible_location_count - len(itempool)

        filler_items = round_robin_pick(filler_groups, remaining_slots)
        itempool.extend(filler_items)
        remaining_slots = visible_location_count - len(itempool)

        # Dynamic filler padding — covers any shortfall from options removing items
        # (e.g. hero abilities disabled + max age unlock precollection)
        while remaining_slots > 0:
            itempool.append(self.create_item(self.get_filler_item_name()))
            remaining_slots -= 1

        if len(itempool) != visible_location_count:
            raise ValueError(
                f"Item pool size mismatch after padding. "
                f"Visible locations: {visible_location_count}, "
                f"items in pool: {len(itempool)}."
            )

        self.multiworld.itempool += itempool

    def set_rules(self) -> None:
        Rules.set_rules(self)

    def fill_slot_data(self) -> Mapping[str, Any]:
        return {
            "version_public": 0,
            "version_major": 1,
            "version_minor": 0,
            "world_id": ((time.time_ns() >> 17) + self.player) & 0x7FFF_FFFF,
            # Final section mode and threshold for client progress display
            "final_mode":  self._final_mode(),
            "x_scenarios": int(self.options.x_scenarios.value),
        }


def run_client(*args: Any) -> None:
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