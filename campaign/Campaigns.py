# =============================================================================
# DEPRECATED — duplicate of `aom/locations/Campaigns.py`.
# =============================================================================
# This module exists only as a legacy artifact.  No live import path references
# `aom.campaign.Campaigns` — every consumer imports from
# `aom.locations.Campaigns` instead (see grep over `from ..locations.Campaigns`
# / `from .Campaigns` inside the locations package).  Do not add new content
# here.  If you need to extend campaign metadata, edit the canonical file:
#     aom/locations/Campaigns.py
# This file is preserved to avoid breaking any external scripts that may have
# imported it during early prototyping; it can safely be deleted in a future
# cleanup pass once we've verified nothing depends on it.
# =============================================================================
import enum


class aomCampaignData(enum.Enum):
    def __new__(cls, id: int, *args, **kwargs):
        obj = object.__new__(cls)
        obj._value_ = id
        return obj

    def __init__(self, id: int, mnemonic: str, name: str) -> None:
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