# pylint: disable=line-too-long
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

import os
import re
import time
from enum import Enum
from threading import Lock
from typing import Optional

import feedparser
import tvdb_v4_official
from pydantic import BaseModel, ValidationError, field_validator

from formula1 import demonyms
from formula1.grand_prix import GrandPrix


class Processor:
    """Base Processor class"""

    regexes = []
    url = None

    def process(self):
        feed = feedparser.parse(self.url)
        for entry in feed.entries:
            yield self.process_entry(entry)

    def handle_event(self, parsed):
        return parsed

    def process_entry(self, entry):
        if (
            "formula.1" in entry["title"].lower()
            or "formula 1" in entry["title"].lower()
        ):
            for regex in self.regexes:
                m = re.match(regex, entry["title"])
                if m:
                    parsed = m.groupdict()
                    try:
                        r = Release(**parsed)
                        return r, entry
                    except ValidationError as e:
                        print(e, parsed, self.__class__)
                        return None, entry
            return None, entry
        return None, entry


class EgorTechProcessor(Processor):
    """Processor class for specific feed"""

    regexes = [
        r"Formula 1\. (?P<year>\d{4})\. R(?P<round>\d+?)\. (?P<name>[^.]+)[\. ]+(?P<broadcaster>.+?)\. (?P<quality>.+)",
        r"Formula 1\. (?P<year>\d{4})\. (?P<name>[^.]+)\. (?P<broadcaster>.+?)\. (?P<quality>.+)",
    ]
    url = "https://torrentgalaxy.mx/rss?magnet&user=48718"


class SmcgillProcessor(Processor):
    """Processor class for specific feed"""

    regexes = [
        r"Formula\.1\.(?P<year>\d{4})[Xx](?P<round>\d{2})\.(?P<name>.+)\.(?P<event>Teds.Qualifying.Notebook|Qualifying|Race|Sprint|Shootout|Sprint.Shootout|Pre-Season.Test.Day\d).SkyF1(HD|UHD)\.(?P<quality>\d+[kKpP]|SD)"
    ]
    url = "https://torrentgalaxy.to/rss?magnet&user=48067"


class ShowStopperProcessor(Processor):
    """Processor class for specific feed"""

    regexes = [
        r"Formula\.1\.(?P<year>\d{4})[xX](?P<episode>\d+)\.Round\.(?P<round>\d{2})\.(?P<name>.+?)\.(?P<event>Race|Qualifying|Shootout|Sprint.Shootout|Sprint|Pre.Season.Testing.Day.\d|Pre.Season.Testing.Day.\d.Session.\d)\.(.+)\.(?P<quality>\d+[pPkK]).SS",
        r"Formula\.1\.(?P<year>\d{4})[xX](?P<episode>\d+)\.REPACK\.Round\.(?P<round>\d{2})\.(?P<name>.+)\.(?P<event>Race|Qualifying|Shootout|Sprint.Shootout|Sprint|Pre.Season.Testing.Day.\d)\.(F1.Live|International.MULTi)\.(?P<quality>\d+[pPkK]).SS",
        r"Formula\.1\.(?P<year>\d{4})\.Round\.(?P<round>\d{2})\.(?P<name>.+?)\.(?P<event>Race|Qualifying|Sprint|Shootout|Sprint.Shootout|Pre.Season.Testing.Day.\d)\.(.+)\.(?P<quality>\d+[pPkK]).SS",
    ]
    url = "https://torrentgalaxy.to/rss?magnet&user=50801"


class Event(str, Enum):
    """Enum for types of F1 events"""

    RACE = "Race"
    SPRINT = "Sprint"
    SHOOTOUT = "Sprint Shootout"
    TESTING1 = "Pre Season Testing Day 1"
    TESTING2 = "Pre Season Testing Day 2"
    TESTING3 = "Pre Season Testing Day 3"
    TESTING_ALL = "Pre Season Testing"
    FP1 = "Practice One"
    FP2 = "Practice Two"
    FP3 = "Practice Three"
    QUALIFYING = "Qualifying"
    NOTEBOOK = "Teds Qualifying Notebook"
    WEEKEND = "Weekend"


class Release(BaseModel):
    year: int
    round: int = 0
    event: Event = Event.WEEKEND
    name: GrandPrix
    quality: Optional[str] = None
    episode: Optional[int] = None

    @field_validator("name", mode="before")
    @classmethod
    def transform_name(cls, raw: str) -> str:
        common_mappings = {
            "USA": "United States",
            "Sao Paulo": "Brazil",
            "Abu-Dhabi": "Abu Dhabi",
            "Bharain": "Bahrain",
        }

        if common_mappings.get(raw):
            return common_mappings.get(raw)
        fixed = (
            " ".join(
                re.findall("[A-Z][^A-Z]*", raw.replace("GP", "").replace(".", " "))
            )
            .replace("  ", " ")
            .replace("-", " ")
        )
        try:
            without_gp = raw.split("GP")[0]
            if without_gp in demonyms.demonyms:
                return demonyms.demonyms[without_gp]
        except IndexError:
            pass
        try:
            without_gp = raw.split(" Grand Prix")[0]
            if without_gp in demonyms.demonyms:
                return demonyms.demonyms[without_gp]
        except IndexError:
            pass
        if fixed in demonyms.demonyms:
            return demonyms.demonyms[fixed]
        else:
            return fixed

    @field_validator("round", mode="before")
    @classmethod
    def transform_round(cls, raw: str) -> int:
        return int(raw)

    @field_validator("episode", mode="before")
    @classmethod
    def transform_episode(cls, raw: str) -> int:
        return int(raw)

    @field_validator("year", mode="before")
    @classmethod
    def transform_year(cls, raw: str) -> int:
        return int(raw)

    @field_validator("quality", mode="before")
    @classmethod
    def transform_quality(cls, raw: str) -> str:
        if raw.upper() == "4K":
            return "2160P"
        else:
            return raw.upper()

    @field_validator("event", mode="before")
    @classmethod
    def transform_event(cls, raw: str) -> str:
        pt1 = [
            "Pre-Season.Test.Day1",
            "Pre.Season.Testing.Day.1",
            "Pre.Season.Testing.Day.1",
        ]
        pt2 = [
            "Pre-Season.Test.Day2",
            "Pre.Season.Testing.Day.2",
            "Pre.Season.Testing.Day.2",
        ]
        pt3 = [
            "Pre-Season.Test.Day3",
            "Pre.Season.Testing.Day.3",
            "Pre.Season.Testing.Day.3",
        ]
        if raw:
            if raw in pt1:
                return Event.TESTING1
            elif raw in pt2:
                return Event.TESTING2
            elif raw in pt3:
                return Event.TESTING3
            elif raw:
                if raw == "Shootout":
                    return Event.SHOOTOUT
                else:
                    return raw.replace(".", " ")
            elif raw.lower() == "Preseason Testing":
                return Event.TESTING_ALL
        return Event.WEEKEND


def events_by_round(season):
    index = 0
    location = None
    by_round = {}
    for episode in season:
        new_location = episode["name"].split(" (")[0]
        if not location:
            location = new_location
        elif location != new_location:
            index += 1
            location = new_location
        if not by_round.get(index):
            by_round[index] = [episode]
        else:
            by_round[index].append(episode)
    return by_round


def get_episode_for_round(season, release):
    if release.event == Event.WEEKEND:
        return []
    if release.event == Event.TESTING1:
        return season[0]
    if release.event == Event.TESTING2:
        return season[1]
    if release.event == Event.TESTING3:
        return season[2]
    if release.episode:
        options = [
            episode
            for episode in season
            if int(release.episode) == int(episode["number"])
        ]
        if len(options) > 0:
            return options[0]
    if release.round:
        by_round = events_by_round(season)
        if release.year == 2023 and release.round > 5:
            rnd = by_round[release.round - 1]
        else:
            rnd = by_round[release.round]

        for episode in rnd:
            if release.event != Event.SPRINT and release.event in episode["name"]:
                return episode
            elif (
                release.event == Event.SPRINT
                and release.event in episode["name"]
                and Event.SHOOTOUT not in episode["name"]
            ):
                return episode
    return None


class ReleaseFetcher:
    releases = []
    last_check = 0
    lock = Lock()

    def get_releases(self, season, episode, allow_weekend=False):
        with self.lock:
            seconds = time.time() - self.last_check
            if self.last_check and seconds < 600:
                print(f"Last check was {seconds} ago, returning cached releases")
                return [
                    (release, entry, ep)
                    for release, entry, ep in self.releases
                    if (
                        season
                        and episode
                        and int(ep["number"]) == int(episode)
                        and int(ep["seasonNumber"]) == int(season)
                    )
                    or not season
                    and not episode
                ]
            self.releases = []
            print(f"Last check was {seconds} ago, refreshing releases")

            self.last_check = time.time()
            tvdb = tvdb_v4_official.TVDB(
                os.environ["TVDB_KEY"], pin=os.environ["TVDB_PIN"]
            )
            series = tvdb.get_series_extended(387219)
            seasons = {
                season["number"]: sorted(
                    [
                        episode
                        for episode in tvdb.get_season_extended(season["id"])[
                            "episodes"
                        ]
                    ],
                    key=lambda x: x["number"],
                )
                for season in series["seasons"]
                if season["number"] > 2018
            }

            processors = [cl() for cl in Processor.__subclasses__()]
            for processor in processors:
                for release, entry in processor.process():
                    if release:
                        if (
                            release.event
                            in [
                                Event.TESTING1,
                                Event.TESTING2,
                                Event.TESTING3,
                                Event.RACE,
                                Event.SPRINT,
                                Event.SHOOTOUT,
                                Event.QUALIFYING,
                                Event.FP1,
                                Event.FP2,
                                Event.FP3,
                            ]
                            or allow_weekend
                        ):
                            ep = get_episode_for_round(seasons[release.year], release)
                            if ep is not None:
                                if (
                                    (
                                        season
                                        and episode
                                        and int(ep["number"]) == int(episode)
                                        and int(ep["seasonNumber"]) == int(season)
                                    )
                                    or not season
                                    and not episode
                                ):
                                    self.releases.append((release, entry, ep))
            return self.releases
