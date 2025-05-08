from datetime import timedelta, datetime
import xml.etree.ElementTree as ElementTree
import pandas as pd
import re

from rich.console import Console
from rich.theme import Theme
from rich.progress import track

console = Console(theme=Theme({"logging.level.success": "bright_green"}))


def log(message, level="info"):
    console.print(
        f"[log.time][{datetime.now().strftime('%H:%M:%S')}][/log.time] [logging.level.{level}]{level}[/logging.level.{level}] \t{message}"
    )


log("Running Purée CLI…", level="info")

passworded = (
    ElementTree.parse("passworded.xml").getroot().find("REGIONS").text.split(",")
)
log("Loaded passworded regions.", level="success")

tree = ElementTree.parse("regions.xml")
log("Loaded daily dump.", level="success")

root = tree.getroot()

regions = []
practice_regions = []

region_nodes = root.findall("REGION")
log("Loaded all regions.", level="success")

update_start = int(region_nodes[0].find("LASTUPDATE").text)
update_length = int(region_nodes[-1].find("LASTUPDATE").text) - update_start

log(f"Found update length: {update_length} seconds.", level="info")

wfe_criteria = {
    "https://discord.gg/W24yF2aCKs": "the roblox army",
    "[region]Trans Republican Army[/region]": "the roblox army",
    "https://www.nationstates.net/region=trans_republican_army": "the roblox army",
    "Hana Macchia": "Hana Macchia",
    "Megacity": "Hana Macchia",
    "Megacity of Fujishima": "Hana Macchia",
    "Mégapole de Fujishima": "Hana Macchia"
    "[region]Purple Pony Club[/region]": "PPC",
}

roman_numeral_regex = "m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})"
moth_regex = ".*(?i)\bmoth\b.*"
# https://stackoverflow.com/a/267405

offices_criteria = {
    "TRA": "the roblox army",
    "planet duke": "Ducky",
    "tgw": "Ducky",
    "Ice Cream": "Oseao",
    f"{moth_regex}": "moth",
    "detagging moth": "moth",
    "GLASS": "Hana Macchia",
    "CRYSTAL": "Hana Macchia",
    "Love Live!": "Hana Macchia",
}

ro_criteria = [
    "moth_legionary_\d+",
    "mint_chip_\d+",
]

embassies_criteria = {
    "Trans Republican Army": "the roblox army",
    "Hana Macchia": "Hana Macchia",
    "Purple Pony Club": "PPC",
}


def find_issues(region):
    if (
        region.find("NAME").text
        in [
            "Suspicious",
            "The Black Hawks",
            "The Brotherhood of Malice",
            "Lily",
            "Osiris",
        ]
        or "X" not in region.find("DELEGATEAUTH").text
        or region.findall("./EMBASSIES/EMBASSY[.='Antifa']")
        or region.find("DELEGATE").text != "0"
    ):
        return {}

    issues = []
    organizations = set()

    wfe = (region.find("FACTBOOK").text or "").lower()

    flagged_wfe = [substring for substring in wfe_criteria if substring in wfe]

    if flagged_wfe:
        issues.append("WFE")
        organizations.update(
            {wfe_criteria[key] for key in flagged_wfe if wfe_criteria[key] is not None}
        )

    officers = region.find("OFFICERS").findall("OFFICER")

    officer_appointers = [
        (officer.find("BY").text or "").lower() for officer in officers
    ]

    officer_offices = [
        (officer.find("OFFICE").text or "").lower() for officer in officers
    ]

    flagged_offices = [
        office for office in officer_offices if office in offices_criteria
    ]

    if flagged_offices:
        issues.append("RO")
        organizations.update(
            {
                offices_criteria[office]
                for office in flagged_offices
                if offices_criteria[office] is not None
            }
        )

    if "RO" not in issues and any(
        any(re.fullmatch(regex, officer_appointer) for regex in ro_criteria)
        for officer_appointer in officer_appointers
    ):
        issues.append("RO")

    embassies = [
        embassy.text
        for embassy in region.findall(f"./EMBASSIES/EMBASSY")
        if embassy.get("type") not in ["closing", "rejected", "denied"]
    ]

    flagged_embassies = [
        embassy for embassy in embassies if embassy in embassies_criteria
    ]

    if flagged_embassies:
        issues.append("Embassies")
        organizations.update(
            {
                embassies_criteria[key]
                for key in flagged_embassies
                if embassies_criteria[key] is not None
            }
        )

    native_embassies = any(
        embassy.text
        for embassy in region.findall(f"./EMBASSIES/EMBASSY")
        if embassy.get("type") in ["closing", "rejected"]
        and embassy.text not in embassies_criteria
    )

    # if issues found, report them
    if issues:
        return {
            "issues": issues,
            "organizations": sorted(organizations),
            "native_embassies": native_embassies,
        }

    del issues
    del organizations
    del native_embassies

    # otherwise, check for practice detags

    practice_issues = []
    practice_organizations = set()

    practice_wfe_criteria = {
        "Help cleanse this region of the [b][color=C7996C]thiccness[/color][/b], the [b][color=C7996C]gooeyness[/color][/b], and the [b][color=E3CBA1]drip[/color][/b]... [b][color=D6B589]drip[/color][/b]... [b][color=C7996C]drip[/color][/b]... of eggnog by detagging it.".lower(): "Eggnog"
    }

    practice_flagged_wfe = [
        substring for substring in practice_wfe_criteria if substring in wfe
    ]

    if practice_flagged_wfe:
        practice_issues.append("WFE")
        practice_organizations.update(
            {
                practice_wfe_criteria[key]
                for key in practice_flagged_wfe
                if practice_wfe_criteria[key] is not None
            }
        )

    practice_offices_criteria = {"eggnog": "Eggnog"}

    practice_flagged_offices = [
        office for office in officer_offices if office in practice_offices_criteria
    ]

    if practice_flagged_offices:
        practice_issues.append("RO")
        practice_organizations.update(
            {
                practice_offices_criteria[office]
                for office in practice_flagged_offices
                if practice_offices_criteria[office] is not None
            }
        )

    practice_embassies_criteria = {"Eggnog": "Eggnog"}

    practice_flagged_embassies = [
        embassy for embassy in embassies if embassy in practice_embassies_criteria
    ]

    if practice_flagged_embassies:
        practice_issues.append("Embassies")
        practice_organizations.update(
            {
                practice_embassies_criteria[key]
                for key in practice_flagged_embassies
                if practice_embassies_criteria[key] is not None
            }
        )

    return {
        "practice_issues": practice_issues,
        "organizations": sorted(practice_organizations),
        "native_embassies": False,
    }


for region in track(region_nodes, description="Flagging regions…"):
    if region.find("NAME").text in passworded:
        continue

    region_issues = find_issues(region)

    if ("issues" in region_issues and region_issues["issues"]) or (
        "practice_issues" in region_issues and region_issues["practice_issues"]
    ):

        name = region.find("NAME").text
        progress = (int(region.find("LASTUPDATE").text) - update_start) / update_length
        minor_progress = round(progress * 3600)
        major_progress = round(progress * 5400)

        issues = (
            region_issues["issues"]
            if "issues" in region_issues
            else region_issues["practice_issues"]
        )

        region_data = {
            "Region": f"{name}",
            "Issues": f"{', '.join(issues)}",
            "Minor": minor_progress,
            "MinorTimestamp": f"{str(timedelta(seconds=minor_progress))}",
            "Major": major_progress,
            "MajorTimestamp": f"{str(timedelta(seconds=major_progress))}",
            "NativeEmbassies": region_issues["native_embassies"],
            "Link": f"https://www.nationstates.net/region={name.lower().replace(' ', '_')}",
            "Organizations": f"{', '.join(region_issues['organizations'])}"
            if region_issues["organizations"]
            else "Unknown",
        }

        for key, value in region_data.items():
            if type(value) is str and value[0] in ["=", "+", "-", "@"]:
                region_data[key] = f"'{value}"

        if "issues" in region_issues and region_issues["issues"]:
            regions.append(region_data)
        elif "practice_issues" in region_issues and region_issues["practice_issues"]:
            practice_regions.append(region_data)


today = (datetime.utcfromtimestamp(update_start) - timedelta(1)).strftime("%d %B %Y")

detags = pd.DataFrame.from_records(regions, index="Region")
detags.to_csv("_data/detags.csv")
detags.to_csv("data/detags.csv")
detags.to_excel("data/detags.xlsx", sheet_name=today)
detags.reset_index().to_json("data/detags.json", orient="records", indent=2)

log(f"Recorded {len(regions)} detags found.", level="success")

with open("_includes/count.html", "w") as outfile:
    outfile.write(str(len(regions)))

history = pd.read_csv("_data/history.csv", index_col="Date")

if today not in history.index:
    row = pd.DataFrame.from_records(
        [{"Date": today, "Count": len(regions)}], index="Date"
    )
    history = pd.concat([history, row])
    history.to_csv("_data/history.csv")
    history.to_csv("data/history.csv")
    history.to_excel("data/history.xlsx", sheet_name="History")
    history.reset_index().to_json("data/history.json", orient="records", indent=2)
    log("Recorded history.", level="info")
else:
    log("No new history entries found.", level="info")

if practice_regions:
    practice_detags = pd.DataFrame.from_records(practice_regions, index="Region")
    practice_detags.to_csv("_data/practice_detags.csv")
    practice_detags.to_csv("data/practice_detags.csv")
    detags.to_excel("data/practice_detags.xlsx", sheet_name=today)
    practice_detags.reset_index().to_json(
        "data/practice_detags.json", orient="records", indent=2
    )

log(f"Recorded {len(practice_regions)} practice_detags found.", level="success")

with open("_includes/practice_count.html", "w") as outfile:
    outfile.write(str(len(practice_regions)))
