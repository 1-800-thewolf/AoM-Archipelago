# =============================================================================
# Campaign enum — one member per campaign section that may appear in a multiworld.
# =============================================================================
#
# Used as:
#   * region grouping in regions/Regions.py (one Region per campaign)
#   * filtering key in __init__.py's `disabled_campaigns`
#   * back-reference on `aomScenarioData` so each scenario knows its parent
#   * payload of `Items.Campaign.vanilla_campaign` for section-unlock items
#
# Adding a new campaign:
#   1. Append a member here with a unique numeric id and short mnemonic.
#   2. Add scenarios for it in locations/Scenarios.py.
#   3. Add locations for those scenarios in locations/Locations.py.
#   4. Add an Items.Campaign(...) entry in items/Items.py if section-gated.
#   5. Add a YAML opt-out option in Options.py if the campaign is optional.
#   6. The regions module iterates this enum so the new campaign automatically
#      gets a Region created (provided it has scenarios).
#
# IMPORTANT: FOTT_FINAL is special — it is never gated by a Campaign item.
# Access is controlled by the FinalScenarios YAML option (always_open /
# atlantis_key / beat_x_scenarios).  See Items.py FinalUnlock.
# =============================================================================

import enum


class aomCampaignData(enum.Enum):
    """Enum of all campaign sections.  Members carry three attributes:

      * `id`            — numeric value used for slot_data wire format and
                          section-unlock indexing
      * `mnemonic`      — short prefix used in scenario / location naming
                          (e.g. 'FOTT-GR-3 Caretaker' for scenario 3 in FotT
                          Greek campaign)
      * `campaign_name` — human-friendly display name (also used as the
                          campaign region name in regions/Regions.py)
    """
    def __new__(cls, id: int, *args, **kwargs):
        """Enum constructor — stores the numeric id as the enum value."""
        obj = object.__new__(cls)
        obj._value_ = id
        return obj

    def __init__(self, id: int, mnemonic: str, name: str) -> None:
        """Attach the metadata trio to each enum member."""
        self.id = id
        self.mnemonic = mnemonic
        self.campaign_name = name

    FOTT_GREEK = 1, "FOTT-GR", "Fall of the Trident: Greek"
    FOTT_EGYPTIAN = 2, "FOTT-EG", "Fall of the Trident: Egyptian"
    FOTT_NORSE = 3, "FOTT-NO", "Fall of the Trident: Norse"
    FOTT_FINAL = 4, "FOTT-FI", "Fall of the Trident: Final"
    NEW_ATLANTIS = 5, "NA", "The New Atlantis"
    GOLDEN_GIFT  = 6, "GG", "The Golden Gift"
    PILLARS_OF_THE_GODS = 7, "POTG", "Pillars of the Gods"