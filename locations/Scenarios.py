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
        if self.campaign.value <= 4:
            return f"{self.global_number}. {self.scenario_name}"
        return f"{self.campaign.mnemonic} {self.chapter}. {self.scenario_name}"

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
    # New Atlantis (campaign value 5, APScenarioIDs 501-512)
    NA_1  = ("A Lost People",         aomCampaignData.NEW_ATLANTIS,  1, 501)
    NA_2  = ("Atlantis Reborn",       aomCampaignData.NEW_ATLANTIS,  2, 502)
    NA_3  = ("Greetings From Greece", aomCampaignData.NEW_ATLANTIS,  3, 503)
    NA_4  = ("Odin's Tower",          aomCampaignData.NEW_ATLANTIS,  4, 504)
    NA_5  = ("The Ancient Relics",    aomCampaignData.NEW_ATLANTIS,  5, 505)
    NA_6  = ("Mount Olympus",         aomCampaignData.NEW_ATLANTIS,  6, 506)
    NA_7  = ("Betrayal at Sikyos",    aomCampaignData.NEW_ATLANTIS,  7, 507)
    NA_8  = ("Cerberus",              aomCampaignData.NEW_ATLANTIS,  8, 508)
    NA_9  = ("Rampage",               aomCampaignData.NEW_ATLANTIS,  9, 509)
    NA_10 = ("Making Amends",         aomCampaignData.NEW_ATLANTIS, 10, 510)
    NA_11 = ("Atlantis Betrayed",     aomCampaignData.NEW_ATLANTIS, 11, 511)
    NA_12 = ("War of the Titans",     aomCampaignData.NEW_ATLANTIS, 12, 512)

    # The Golden Gift (campaign value 6, APScenarioIDs 601-604)
    GG_1  = ("Brokk's Journey",       aomCampaignData.GOLDEN_GIFT,  1, 601)
    GG_2  = ("Eitri's Journey",       aomCampaignData.GOLDEN_GIFT,  2, 602)
    GG_3  = ("Fight at the Forge",    aomCampaignData.GOLDEN_GIFT,  3, 603)
    GG_4  = ("Loki's Temples",        aomCampaignData.GOLDEN_GIFT,  4, 604)


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