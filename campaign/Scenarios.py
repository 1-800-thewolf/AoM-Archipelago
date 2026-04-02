import enum

from .Campaigns import aomCampaignData


class aomScenarioData(enum.IntEnum):
    def __new__(cls, scenario_name: str, campaign: aomCampaignData, chapter: int, global_number: int):
        value = campaign.value * 100 + chapter
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    def __init__(self, scenario_name: str, campaign: aomCampaignData, chapter: int, global_number: int) -> None:
        self.id = self.value
        self.scenario_name = scenario_name
        self.campaign = campaign
        self.chapter = chapter
        self.global_number = global_number  # 1-32 across all campaigns

    @property
    def region_name(self) -> str:
        return self.name

    @property
    def display_name(self) -> str:
        # Use global_number (1-32) so location names are unambiguous across all campaigns.
        # Previously chapter reset to 1 for each campaign, producing duplicate prefixes
        # like "1. The Lost Relic" and "1. Old Friends".
        return f"{self.global_number}. {self.scenario_name}"

    # Greek (chapters 1-10, global 1-10)
    FOTT_1  = ("Omens",                    aomCampaignData.FOTT_GREEK,     1,  1)
    FOTT_2  = ("Consequences",             aomCampaignData.FOTT_GREEK,     2,  2)
    FOTT_3  = ("Scratching the Surface",   aomCampaignData.FOTT_GREEK,     3,  3)
    FOTT_4  = ("A Fine Plan",              aomCampaignData.FOTT_GREEK,     4,  4)
    FOTT_5  = ("Just Enough Rope",         aomCampaignData.FOTT_GREEK,     5,  5)
    FOTT_6  = ("I Hope This Works",        aomCampaignData.FOTT_GREEK,     6,  6)
    FOTT_7  = ("More Bandits",             aomCampaignData.FOTT_GREEK,     7,  7)
    FOTT_8  = ("Bad News",                 aomCampaignData.FOTT_GREEK,     8,  8)
    FOTT_9  = ("Revelation",               aomCampaignData.FOTT_GREEK,     9,  9)
    FOTT_10 = ("Strangers",                aomCampaignData.FOTT_GREEK,    10, 10)

    # Egyptian (chapters 1-10, global 11-20)
    FOTT_11 = ("The Lost Relic",           aomCampaignData.FOTT_EGYPTIAN,  1, 11)
    FOTT_12 = ("Light Sleeper",            aomCampaignData.FOTT_EGYPTIAN,  2, 12)
    FOTT_13 = ("Tug of War",               aomCampaignData.FOTT_EGYPTIAN,  3, 13)
    FOTT_14 = ("Isis, Hear My Plea",       aomCampaignData.FOTT_EGYPTIAN,  4, 14)
    FOTT_15 = ("Let's Go",                 aomCampaignData.FOTT_EGYPTIAN,  5, 15)
    FOTT_16 = ("Good Advice",              aomCampaignData.FOTT_EGYPTIAN,  6, 16)
    FOTT_17 = ("The Jackal's Stronghold",  aomCampaignData.FOTT_EGYPTIAN,  7, 17)
    FOTT_18 = ("A Long Way From Home",     aomCampaignData.FOTT_EGYPTIAN,  8, 18)
    FOTT_19 = ("Watch That First Step",    aomCampaignData.FOTT_EGYPTIAN,  9, 19)
    FOTT_20 = ("Where They Belong",        aomCampaignData.FOTT_EGYPTIAN, 10, 20)

    # Norse (chapters 1-10, global 21-30)
    FOTT_21 = ("Old Friends",              aomCampaignData.FOTT_NORSE,     1, 21)
    FOTT_22 = ("North",                    aomCampaignData.FOTT_NORSE,     2, 22)
    FOTT_23 = ("The Dwarven Forge",        aomCampaignData.FOTT_NORSE,     3, 23)
    FOTT_24 = ("Not From Around Here",     aomCampaignData.FOTT_NORSE,     4, 24)
    FOTT_25 = ("Welcoming Committee",      aomCampaignData.FOTT_NORSE,     5, 25)
    FOTT_26 = ("Union",                    aomCampaignData.FOTT_NORSE,     6, 26)
    FOTT_27 = ("The Well of Urd",          aomCampaignData.FOTT_NORSE,     7, 27)
    FOTT_28 = ("Beneath the Surface",      aomCampaignData.FOTT_NORSE,     8, 28)
    FOTT_29 = ("Unlikely Heroes",          aomCampaignData.FOTT_NORSE,     9, 29)
    FOTT_30 = ("All Is Not Lost",          aomCampaignData.FOTT_NORSE,    10, 30)

    # Final (chapters 1-2, global 31-32)
    FOTT_31 = ("Welcome Back",             aomCampaignData.FOTT_FINAL,     1, 31)
    FOTT_32 = ("A Place in My Dreams",     aomCampaignData.FOTT_FINAL,     2, 32)


scenario_from_id: dict[int, aomScenarioData] = {
    scenario.id: scenario for scenario in aomScenarioData
}

scenario_names: list[str] = [
    scenario.scenario_name for scenario in aomScenarioData
]

CAMPAIGN_TO_SCENARIOS: dict[aomCampaignData, list[aomScenarioData]] = {
    campaign: [] for campaign in aomCampaignData
}

for scenario in aomScenarioData:
    CAMPAIGN_TO_SCENARIOS[scenario.campaign].append(scenario)