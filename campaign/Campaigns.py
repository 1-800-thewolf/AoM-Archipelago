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