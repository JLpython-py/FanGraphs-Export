#! python3
# FanGraphs/leaders.py

"""

"""

import csv
import datetime
import os
from urllib.request import urlopen

import bs4
from lxml import etree
from playwright.sync_api import sync_playwright
from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

import FanGraphs.exceptions


def compile_options():
    """
    Modifies Selenium WebDriver Options for ideal browser usage.
    Creates directory *out/* for exported files.

    :returns: Selenium WebDriver Options Object
    :rtype: selenium.webdriver.firefox.options.Options
    """
    options = Options()
    options.headless = True
    os.makedirs("out", exist_ok=True)
    preferences = {
        "browser.download.folderList": 2,
        "browser.download.manager.showWhenStarting": False,
        "browser.download.dir": os.path.abspath("out"),
        "browser.helperApps.neverAsk.saveToDisk": "text/csv"
    }
    for pref in preferences:
        options.set_preference(pref, preferences[pref])
    return options


class MajorLeagueLeaderboards:
    """
    Parses the FanGraphs Major League Leaderboards page.
    Note that the Splits Leaderboard is not covered.
    Instead, it is covered by :py:class:`SplitsLeaderboards`
    """

    def __init__(self):
        """
        .. py:attribute:: address
            The base URL address of the Major League Leaderboards page

            :type: str
            :value: https://fangraphs.com/leaders.aspx

        .. py:attribute:: tree
            The ``lxml`` element tree for parsing the webpage HTML.

            :type: lxml.etree._ElementTree

        .. py:attribute:: browser
            The ``selenium`` automated Firefox browser for navigating webpage.

            :type: selenium.webdriver.firefox.webdriver.WebDriver

        """
        self.__selections = {
            "group": "LeaderBoard1_tsGroup",
            "stat": "LeaderBoard1_tsStats",
            "position": "LeaderBoard1_tsPosition",
            "type": "LeaderBoard1_tsType"
        }
        self.__dropdowns = {
            "league": "LeaderBoard1_rcbLeague_Input",
            "team": "LeaderBoard1_rcbTeam_Input",
            "single_season": "LeaderBoard1_rcbSeason_Input",
            "split": "LeaderBoard1_rcbMonth_Input",
            "min_pa": "LeaderBoard1_rcbMin_Input",
            "season1": "LeaderBoard1_rcbSeason1_Input",
            "season2": "LeaderBoard1_rcbSeason2_Input",
            "age1": "LeaderBoard1_rcbAge1_Input",
            "age2": "LeaderBoard1_rcbAge2_Input"
        }
        self.__dropdown_options = {
            "league": "LeaderBoard1_rcbLeague_DropDown",
            "team": "LeaderBoard1_rcbTeam_DropDown",
            "single_season": "LeaderBoard1_rcbSeason_DropDown",
            "split": "LeaderBoard1_rcbMonth_DropDown",
            "min_pa": "LeaderBoard1_rcbMin_DropDown",
            "season1": "LeaderBoard1_rcbSeason1_DropDown",
            "season2": "LeaderBoard1_rcbSeason2_DropDown",
            "age1": "LeaderBoard1_rcbAge1_DropDown",
            "age2": "LeaderBoard1_rcbAge2_DropDown"
        }
        self.__checkboxes = {
            "split_teams": "LeaderBoard1_cbTeams",
            "active_roster": "LeaderBoard1_cbActive",
            "hof": "LeaderBoard1_cbHOF",
            "split_seasons": "LeaderBoard1_cbSeason",
            "rookies": "LeaderBoard1_cbRookie"
        }
        self.__buttons = {
            "season1": "LeaderBoard1_btnMSeason",
            "season2": "LeaderBoard1_btnMSeason",
            "age1": "LeaderBoard1_cmdAge",
            "age2": "LeaderBoard1_cmdAge"
        }
        self.address = "https://fangraphs.com/leaders.aspx"

        response = urlopen(self.address)
        parser = etree.HTMLParser()
        self.tree = etree.parse(response, parser)

        self.browser = webdriver.Firefox(
            options=compile_options()
        )
        self.browser.get(self.address)

    def list_queries(self):
        """
        Lists the possible filter queries which can be used to modify search results.

        :return: Filter queries which can be used to modify search results
        :type: list
        """
        queries = []
        queries.extend(list(self.__selections))
        queries.extend(list(self.__dropdowns))
        queries.extend(list(self.__checkboxes))
        return queries

    def list_options(self, query):
        """
        Lists the possible options which the filter query can be configured to.

        :param query:
        :return: Options which the filter query can be configured to
        :rtype: list
        :raises MajorLeagueLeaderboards.InvalidFilterQuery: Argument ``query`` is invalid
        """
        query = query.lower()
        if query in self.__checkboxes:
            options = ["True", "False"]
        elif query in self.__dropdown_options:
            xpath = "//div[@id='{}']//div//ul//li".format(
                self.__dropdown_options.get(query)
            )
            elems = self.tree.xpath(xpath)
            options = [e.text for e in elems]
        elif query in self.__selections:
            xpath = "//div[@id='{}']//div//ul//li//a//span//span//span".format(
                self.__selections.get(query)
            )
            elems = self.tree.xpath(xpath)
            options = [e.text for e in elems]
        else:
            raise FanGraphs.exceptions.InvalidFilterQueryException(query)
        return options

    def current_option(self, query):
        """
        Retrieves the option which the filter query is currently set to.

        :param query: The filter query being retrieved of its current option
        :return: The option which the filter query is currently set to
        :rtype: str
        :raises MajorLeagueLeaderboards.InvalidFilterQuery: Argument ``query`` is invalid
        """
        query = query.lower()
        if query in self.__checkboxes:
            xpath = "//input[@id='{}']".format(
                self.__checkboxes.get(query)
            )
            elem = self.tree.xpath(xpath)[0]
            option = "True" if elem.get("checked") == "checked" else "False"
        elif query in self.__dropdowns:
            xpath = "//input[@id='{}']".format(
                self.__dropdowns.get(query)
            )
            elem = self.tree.xpath(xpath)[0]
            option = elem.get("value")
        elif query in self.__selections:
            xpath = "//div[@id='{}']//div//ul//li//a[@class='{}']//span//span//span".format(
                self.__selections.get(query),
                "rtsLink rtsSelected"
            )
            elem = self.tree.xpath(xpath)[0]
            option = elem.text
        else:
            raise FanGraphs.exceptions.InvalidFilterQueryException(query)
        return option

    def configure(self, query, option):
        """
        Sets a filter query to a specified option.

        :param query: The filter query to be configured
        :param option: The option to set the filter query to
        """
        query, option = query.lower(), str(option).lower()
        if query not in self.list_queries():
            raise FanGraphs.exceptions.InvalidFilterQueryException(query)
        self.__close_ad()
        while True:
            try:
                if query in self.__checkboxes:
                    self.__config_checkbox(query, option)
                elif query in self.__dropdowns:
                    self.__config_dropdown(query, option)
                elif query in self.__selections:
                    self.__config_selection(query, option)
                if query in self.__buttons:
                    self.__submit_form(query)
            except exceptions.ElementClickInterceptedException:
                self.__close_ad()
                continue
            break
        response = urlopen(self.browser.current_url)
        parser = etree.HTMLParser()
        self.tree = etree.parse(response, parser)

    def __config_checkbox(self, query, option):
        """
        Sets a checkbox-class filter query to an option

        :param query: The checkbox-class filter query to be configured
        :param option: The option to set the filter query to
        """
        current = self.current_option(query).lower()
        if option == current:
            return
        elem = self.browser.find_element_by_xpath(
            self.__checkboxes.get(query)
        )
        elem.click()

    def __config_dropdown(self, query, option):
        """
        Sets a dropdown-class filter query to an option

        :param query: The dropdown-class filter query to be configured
        :param option: The option to set the filter query to
        """
        options = [o.lower() for o in self.list_options(query)]
        index = options.index(option)
        dropdown = self.browser.find_element_by_id(
            self.__dropdowns.get(query)
        )
        dropdown.click()
        elem = self.browser.find_elements_by_css_selector(
            "div[id='{}'] div ul li".format(
                self.__dropdown_options.get(query)
            )
        )[index]
        elem.click()

    def __config_selection(self, query, option):
        """
        Sets a selection-class filter query to an option

        :param query: The selection-class filter query to be configured
        :param option: The option to set the filter query to
        """
        def open_pitch_type_sublevel():
            pitch_type_elem = self.browser.find_element_by_css_selector(
                "div[id='LeaderBoard1_tsType'] div ul li a[href='#']"
            )
            pitch_type_elem.click()
        options = [o.lower() for o in self.list_options(query)]
        index = options.index(option)
        elem = self.browser.find_elements_by_css_selector(
            "div[id='{}'] div ul li".format(
                self.__selections.get(query)
            )
        )[index]
        try:
            elem.click()
        except exceptions.ElementNotInteractableException:
            open_pitch_type_sublevel()
            elem.click()

    def __submit_form(self, query):
        """
        Clicks the button element which submits the search query.

        :param query: The filter query which has an attached form submission button
        """
        elem = self.browser.find_element_by_id(
            self.__buttons.get(query)
        )
        elem.click()

    def __close_popup(self):
        pass

    def __close_ad(self):
        """
        Closes the ad which may interfere with clicking other page elements.
        """
        elem = self.browser.find_element_by_class_name(
            "ezmob-footer-close"
        )
        elem.click()

    def quit(self):
        """
        Calls the ``quit()`` method of :py:attr:`browser`.
        """
        self.browser.quit()

    def reset(self):
        """
        Calls the ``get()`` method of :py:attr:`browser`, passing :py:attr:`address`.
        """
        self.browser.get(self.address)
        response = urlopen(self.browser.current_url)
        parser = etree.HTMLParser()
        self.tree = etree.parse(response, parser)

    def export(self, name=""):
        """
        Exports the current leaderboard as a CSV file.
        The file will be saved to *./out*.
        By default, the name of the file is **FanGraphs Leaderboard.csv**.
        If ``name`` is not specified, the file will be the formatted ``datetime.datetime.now()``.

        :param name: The filename to rename the saved file to
        """
        if not name or os.path.splitext(name)[1] != ".csv":
            name = "{}.csv".format(
                datetime.datetime.now().strftime("%d.%m.%y %H.%M.%S")
            )
        while True:
            try:
                WebDriverWait(self.browser, 20).until(
                    expected_conditions.element_to_be_clickable(
                        (By.ID, "LeaderBoard1_cmdCSV")
                    )
                ).click()
                break
            except exceptions.ElementClickInterceptedException:
                self.__close_ad()
        os.rename(
            os.path.join("out", "FanGraphs Leaderboard.csv"),
            os.path.join("out", name)
        )


class SplitsLeaderboards:
    """
    Parses the FanGraphs Splits Leaderboards page.
    """
    __selections = {
        "group": [
            ".fgBin.row-button > div[class*='button-green fgButton']:nth-child(1)",
            ".fgBin.row-button > div[class*='button-green fgButton']:nth-child(2)",
            ".fgBin.row-button > div[class*='button-green fgButton']:nth-child(3)",
            ".fgBin.row-button > div[class*='button-green fgButton']:nth-child(4)"
        ],
        "stat": [
            ".fgBin.row-button > div[class*='button-green fgButton']:nth-child(6)",
            ".fgBin.row-button > div[class*='button-green fgButton']:nth-child(7)"
        ],
        "type": [
            "#root-buttons-stats > div:nth-child(1)",
            "#root-buttons-stats > div:nth-child(2)",
            "#root-buttons-stats > div:nth-child(3)"
        ]
    }
    __dropdowns = {
        "time_filter": "#root-menu-time-filter > .fg-dropdown.splits.multi-choice",
        "preset_range": "#root-menu-time-filter > .fg-dropdown.splits.single-choice",
        "groupby": ".fg-dropdown.group-by"
    }
    __splits = {
        "handedness": ".fgBin:nth-child(1) > .fg-dropdown.splits.multi-choice:nth-child(1)",
        "home_away": ".fgBin:nth-child(1) > .fg-dropdown.splits.multi-choice:nth-child(2)",
        "batted_ball": ".fgBin:nth-child(1) > .fg-dropdown.splits.multi-choice:nth-child(3)",
        "situation": ".fgBin:nth-child(1) > .fg-dropdown.splits.multi-choice:nth-child(4)",
        "count": ".fgBin:nth-child(1) > .fg-dropdown.splits.multi-choice:nth-child(5)",
        "batting_order": ".fgBin:nth-child(2) > .fg-dropdown.splits.multi-choice:nth-child(1)",
        "position": ".fgBin:nth-child(2) > .fg-dropdown.splits.multi-choice:nth-child(2)",
        "inning": ".fgBin:nth-child(2) > .fg-dropdown.splits.multi-choice:nth-child(3)",
        "leverage": ".fgBin:nth-child(2) > .fg-dropdown.splits.multi-choice:nth-child(4)",
        "shifts": ".fgBin:nth-child(2) > .fg-dropdown.splits.multi-choice:nth-child(5)",
        "team": ".fgBin:nth-child(3) > .fg-dropdown.splits.multi-choice:nth-child(1)",
        "opponent": ".fgBin:nth-child(3) > .fg-dropdown.splits.multi-choice:nth-child(2)",
    }
    __quick_splits = {
        "batting_home": ".quick-splits > div:nth-child(1) > div:nth-child(2) > .fgButton:nth-child(1)",
        "batting_away": ".quick-splits > div:nth-child(1) > div:nth-child(2) > .fgButton:nth-child(2)",
        "vs_lhp": ".quick-splits > div:nth-child(1) > div:nth-child(3) > .fgButton:nth-child(1)",
        "vs_lhp_home": ".quick-splits > div:nth-child(1) > div:nth-child(3) > .fgButton:nth-child(2)",
        "vs_lhp_away": ".quick-splits > div:nth-child(1) > div:nth-child(3) > .fgButton:nth-child(3)",
        "vs_lhp_as_lhh": ".quick-splits > div:nth-child(1) > div:nth-child(3) > .fgButton:nth-child(4)",
        "vs_lhp_as_rhh": ".quick-splits > div:nth-child(1) > div:nth-child(3) > .fgButton:nth-child(5)",
        "vs_rhp": ".quick-splits > div:nth-child(1) > div:nth-child(4) > .fgButton:nth-child(1)",
        "vs_rhp_home": ".quick-splits > div:nth-child(1) > div:nth-child(4) > .fgButton:nth-child(2)",
        "vs_rhp_away": ".quick-splits > div:nth-child(1) > div:nth-child(4) > .fgButton:nth-child(3)",
        "vs_rhp_as_lhh": ".quick-splits > div:nth-child(1) > div:nth-child(4) > .fgButton:nth-child(4)",
        "vs_rhp_as_rhh": ".quick-splits > div:nth-child(1) > div:nth-child(4) > .fgButton:nth-child(5)",
        "pitching_as_sp": ".quick-splits > div:nth-child(2) > div:nth-child(1) .fgButton:nth-child(1)",
        "pitching_as_rp": ".quick-splits > div:nth-child(2) > div:nth-child(1) .fgButton:nth-child(2)",
        "pitching_home": ".quick-splits > div:nth-child(2) > div:nth-child(2) > .fgButton:nth-child(1)",
        "pitching_away": ".quick-splits > div:nth-child(2) > div:nth-child(2) > .fgButton:nth-child(2)",
        "vs_lhh": ".quick-splits > div:nth-child(2) > div:nth-child(3) > .fgButton:nth-child(1)",
        "vs_lhh_home": ".quick-splits > div:nth-child(2) > div:nth-child(3) > .fgButton:nth-child(2)",
        "vs_lhh_away": ".quick-splits > div:nth-child(2) > div:nth-child(3) > .fgButton:nth-child(3)",
        "vs_lhh_as_rhp": ".quick-splits > div:nth-child(2) > div:nth-child(3) > .fgButton:nth-child(4)",
        "vs_lhh_as_lhp": ".quick-splits > div:nth-child(2) > div:nth-child(3) > .fgButton:nth-child(5)",
        "vs_rhh": ".quick-splits > div:nth-child(2) > div:nth-child(4) > .fgButton:nth-child(1)",
        "vs_rhh_home": ".quick-splits > div:nth-child(2) > div:nth-child(4) > .fgButton:nth-child(1)",
        "vs_rhh_away": ".quick-splits > div:nth-child(2) > div:nth-child(4) > .fgButton:nth-child(1)",
        "vs_rhh_as_rhp": ".quick-splits > div:nth-child(2) > div:nth-child(4) > .fgButton:nth-child(1)",
        "vs_rhh_as_lhp": ".quick-splits > div:nth-child(2) > div:nth-child(4) > .fgButton:nth-child(1)"
    }
    __switches = {
        "split_teams": "#stack-buttons > div:nth-child(2)",
        "auto_pt": "#stack-buttons > div:nth-child(3)"
    }

    address = "https://fangraphs.com/leaders/splits-leaderboards"

    def __init__(self, *, browser="chromium"):
        self.__play = sync_playwright().start()
        if browser == "chromium":
            self.__browser = self.__play.chromium.launch()
        self.page = self.__browser.new_page()
        self.page.goto(self.address, timeout=0)

        self.soup = None
        self.__refresh_parser()

        self.configure_group("Show All")
        self.configure("auto_pt", "False", autoupdate=True)

    def __refresh_parser(self):
        self.soup = bs4.BeautifulSoup(
            self.page.content(), features="lxml"
        )

    @classmethod
    def list_queries(cls):
        queries = []
        queries.extend(list(cls.__selections))
        queries.extend(list(cls.__dropdowns))
        queries.extend(list(cls.__splits))
        queries.extend(list(cls.__switches))
        return queries

    def list_filter_groups(self):
        selector = ".fgBin.splits-bin-controller div"
        elems = self.soup.select(selector)
        groups = [e.getText() for e in elems]
        return groups

    def list_options(self, query: str):
        query = query.lower()
        if query in self.__selections:
            elems = [
                self.soup.select(s)[0]
                for s in self.__selections[query]
            ]
            options = [e.getText() for e in elems]
        elif query in self.__dropdowns:
            selector = f"{self.__dropdowns[query]} ul li"
            elems = self.soup.select(selector)
            options = [e.getText() for e in elems]
        elif query in self.__splits:
            selector = f"{self.__splits[query]} ul li"
            elems = self.soup.select(selector)
            options = [e.getText() for e in elems]
        elif query in self.__switches:
            options = ["True", "False"]
        else:
            raise FanGraphs.exceptions.InvalidFilterQueryException(query)
        return options

    def current_option(self, query: str):
        query = query.lower()
        options = []
        if query in self.__selections:
            for sel in self.__selections[query]:
                elem = self.soup.select(sel)[0]
                if "isActive" in elem.get("class"):
                    options = [elem.getText()]
                    break
        elif query in self.__dropdowns:
            elems = self.soup.select(
                f"{self.__dropdowns[query]} ul li"
            )
            for elem in elems:
                if "highlight-selection" in elem.get("class"):
                    options.append(elem.getText())
        elif query in self.__splits:
            elems = self.soup.select(
                f"{self.__splits[query]} ul li"
            )
            for elem in elems:
                if "highlight-selection" in elem.get("class"):
                    options.append(elem.getText())
        elif query in self.__switches:
            elem = self.soup.select(self.__switches[query])
            options = ["True" if "isActive" in elem[0].get("class") else "False"]
        else:
            raise FanGraphs.exceptions.InvalidFilterQueryException(query)
        return options

    def configure_group(self, group="Show All"):
        selector = ".fgBin.splits-bin-controller div"
        elems = self.soup.select(selector)
        options = [e.getText() for e in elems]
        try:
            index = options.index(group)
        except ValueError:
            raise Exception
        self.__close_ad()
        elem = self.page.query_selector_all(selector)[index]
        elem.click()

    def update(self):
        selector = "#button-update"
        elem = self.page.query_selector(selector)
        if elem is None:
            return
        self.__close_ad()
        elem.click()
        self.__refresh_parser()

    def reset_filters(self):
        selector = "#stack-buttons div[class='fgButton small']:nth-last-child(1)"
        elem = self.page.query_selector(selector)
        if elem is None:
            return
        self.__close_ad()
        elem.click()

    def list_quick_splits(self):
        return list(self.__quick_splits)

    def configure_quick_split(self, quick_split: str):
        quick_split = quick_split.lower()
        try:
            selector = self.__quick_splits[quick_split]
        except KeyError:
            raise FanGraphs.exceptions.InvalidQuickSplitException(quick_split)
        self.__close_ad()
        self.page.click(selector)
        self.update()

    def configure(self, query: str, option: str, *, autoupdate=False):
        self.__close_ad()
        query = query.lower()
        if query in self.__selections:
            self.__configure_selection(query, option)
        elif query in self.__dropdowns:
            self.__configure_dropdown(query, option)
        elif query in self.__splits:
            self.__configure_split(query, option)
        elif query in self.__switches:
            self.__configure_switch(query, option)
        else:
            raise FanGraphs.exceptions.InvalidFilterQueryException(query)
        if autoupdate:
            self.update()
        self.__refresh_parser()

    def __configure_selection(self, query: str, option: str):
        options = self.list_options(query)
        try:
            index = options.index(option)
        except ValueError:
            raise FanGraphs.exceptions.InvalidFilterOptionException(query, option)
        self.page.click(self.__selections[query][index])

    def __configure_dropdown(self, query: str, option: str):
        options = self.list_options(query)
        try:
            index = options.index(option)
        except ValueError:
            raise FanGraphs.exceptions.InvalidFilterOptionException(query, option)
        self.page.hover(self.__dropdowns[query])
        elem = self.page.query_selector_all(f"{self.__dropdowns[query]} ul li")[index]
        elem.click()

    def __configure_split(self, query: str, option: str):
        options = self.list_options(query)
        try:
            index = options.index(option)
        except ValueError:
            raise FanGraphs.exceptions.InvalidFilterOptionException(query, option)
        self.page.hover(self.__splits[query])
        elem = self.page.query_selector_all(f"{self.__splits[query]} ul li")[index]
        elem.click()

    def __configure_switch(self, query, option):
        if option == self.current_option(query)[0]:
            return
        self.page.click(self.__switches[query])

    def __close_ad(self):
        elem = self.page.query_selector(".ezmob-footer-close")
        if elem and elem.is_visible():
            elem.click()

    def export(self, path="", *, size="Infinity", sortby="", reverse=False):
        self.page.hover(".data-export")
        self.__close_ad()
        self.__expand_table(size=size)
        if sortby:
            self.__sortby(sortby.title(), reverse=reverse)
        if not path or os.path.splitext(path)[1] != ".csv":
            path = "{}.csv".format(
                datetime.datetime.now().strftime("%d.%m.%y %H.%M.%S")
            )
        with open(os.path.join("out", path), "w", newline="") as file:
            writer = csv.writer(file)
            self.__write_table_headers(writer)
            self.__write_table_rows(writer)

    def __expand_table(self, *, size="Infinity"):
        selector = ".table-page-control:nth-child(3) select"
        dropdown = self.page.query_selector(selector)
        dropdown.click()
        elems = self.soup.select(f"{selector} option")
        options = [e.getText() for e in elems]
        size = "Infinity" if size not in options else size
        index = options.index(size)
        option = self.page.query_selector_all(f"{selector} option")[index]
        option.click()

    def __sortby(self, sortby, *, reverse=False):
        selector = ".table-scroll thead tr th"
        elems = self.soup.select(selector)
        options = [e.getText() for e in elems]
        index = options.index(sortby)
        option = self.page.query_selector_all(selector)[index]
        option.click()
        if reverse:
            option.click()

    def __write_table_headers(self, writer: csv.writer):
        selector = ".table-scroll thead tr th"
        elems = self.soup.select(selector)
        headers = [e.getText() for e in elems]
        writer.writerow(headers)

    def __write_table_rows(self, writer: csv.writer):
        selector = ".table-scroll tbody tr"
        row_elems = self.soup.select(selector)
        for row in row_elems:
            elems = row.select("td")
            items = [e.getText() for e in elems]
            writer.writerow(items)

    def reset(self):
        self.page.goto(self.address)
        self.__refresh_parser()

    def quit(self):
        self.__browser.close()
        self.__play.stop()


class SeasonStatGrid:
    """
    Scrapes the FanGraphs Season Stat Grid webpage

    .. py:attribute:: address
        The base URL address of the Season Stat Grid page

        :type: str
        :value: https://fangraphs.com/season-stat-grid
    """

    __selections = {
        "stat": [
            "div[class*='fgButton button-green']:nth-child(1)",
            "div[class*='fgButton button-green']:nth-child(2)"
        ],
        "type": [
            "div[class*='fgButton button-green']:nth-child(4)",
            "div[class*='fgButton button-green']:nth-child(5)",
            "div[class*='fgButton button-green']:nth-child(6)"
        ]
    }
    __dropdowns = {
        "start_season": ".row-season > div:nth-child(2)",
        "end_season": ".row-season > div:nth-child(4)",
        "popular": ".season-grid-controls-dropdown-row-stats > div:nth-child(1)",
        "standard": ".season-grid-controls-dropdown-row-stats > div:nth-child(2)",
        "advanced": ".season-grid-controls-dropdown-row-stats > div:nth-child(3)",
        "statcast": ".season-grid-controls-dropdown-row-stats > div:nth-child(4)",
        "batted_ball": ".season-grid-controls-dropdown-row-stats > div:nth-child(5)",
        "win_probability": ".season-grid-controls-dropdown-row-stats > div:nth-child(6)",
        "pitch_type": ".season-grid-controls-dropdown-row-stats > div:nth-child(7)",
        "plate_discipline": ".season-grid-controls-dropdown-row-stats > div:nth-child(8)",
        "value": ".season-grid-controls-dropdown-row-stats > div:nth-child(9)"
    }
    address = "https://fangraphs.com/leaders/season-stat-grid"

    def __init__(self):
        """
        .. py:attribute:: page
            The generated synchronous ``Playwright`` page for browser automation.

            :type: playwright.sync_api._generated.Page

        .. py:attribute:: soup
            The ``BeautifulSoup4`` HTML parser for scraping the webpage.

            :type: bs4.BeautifulSoup
        """
        self.__play = sync_playwright().start()
        self.__browser = self.__play.chromium.launch()
        self.page = self.__browser.new_page()
        self.page.goto(self.address)

        self.soup = None
        self.__refresh_parsers()

    def __refresh_parsers(self):
        """
        Re-initializes :py:attr:`soup` if a page reload is expected
        """
        self.soup = bs4.BeautifulSoup(
            self.page.content(), features="lxml"
        )

    @classmethod
    def list_queries(cls):
        """
        Lists the possible filter queries which can be sued to modify search results.

        :return: Filter queries which can be used to modify search results
        :type: list
        """
        queries = []
        queries.extend(list(cls.__selections))
        queries.extend(list(cls.__dropdowns))
        return queries

    def list_options(self, query: str):
        """
        Lists the possible options which the filter query can be configured to.

        :param query: The filter query
        :return: Options which ``query`` can be configured to
        :rtyp: list
        :raises FanGraphs.exceptions.InvalidFilterQuery: Argument ``query`` is invalid
        """
        query = query.lower()
        if query in self.__selections:
            elems = [
                self.soup.select(s)[0]
                for s in self.__selections[query]
            ]
            options = [e.getText() for e in elems]
        elif query in self.__dropdowns:
            elems = self.soup.select(
                f"{self.__dropdowns[query]} li"
            )
            options = [e.getText() for e in elems]
        else:
            raise FanGraphs.exceptions.InvalidFilterQueryException(query)
        return options

    def current_option(self, query: str):
        """
        Retrieves the option which the filter query is currently configured to.

        :param query: The filter query
        :return: The option which the filter query is currently configured to
        :rtype: str
        :raises FanGraphs.exceptions.InvalidFilterQuery: Argument ``query`` is invalid
        """
        query = query.lower()
        if query in self.__selections:
            selector = "div[class='fgButton button-green active isActive']"
            elems = self.soup.select(selector)
            option = {
                "stat": elems[0].getText(), "type": elems[1].getText()
            }[query]
        elif query in self.__dropdowns:
            elems = self.soup.select(
                f"{self.__dropdowns[query]} li[class$='highlight-selection']"
            )
            option = elems[0].getText() if elems else "None"
        else:
            raise FanGraphs.exceptions.InvalidFilterQueryException(query)
        return option

    def configure(self, query: str, option: str):
        """
        Configures the filter query to the specified option.

        :param query: The filter query
        :param option: The option to configure ``query`` to
        :raises FanGraphs.exceptions.InvalidFilterQuery: Argument ``query`` is invalid
        :raises FanGraphs.exceptions.InvalidFilterOption: Filter ``query`` cannot be configured to ``option``
        """
        query = query.lower()
        self.__close_ad()
        if query in self.__selections:
            self.__configure_selection(query, option)
        elif query in self.__dropdowns:
            self.__configure_dropdown(query, option)
        else:
            raise FanGraphs.exceptions.InvalidFilterQueryException(query)
        self.__refresh_parsers()

    def __configure_selection(self, query: str, option: str):
        """
        Configures a selection-class filter query to the option.

        :param query: The filter query
        :param option: The option to configure ``query`` to
        :raises FanGraphs.exceptions.InvalidFilterOption: Filter ``query`` cannot be configured to ``option``
        """
        options = self.list_options(query)
        try:
            index = options.index(option)
        except ValueError:
            raise FanGraphs.exceptions.InvalidFilterOptionException(query, option)
        self.page.click(self.__selections[query][index])

    def __configure_dropdown(self, query: str, option: str):
        """
        Configures a dropdown-class filter query to the option.

        :param query: The filter query
        :param option: The option to configure ``query`` to
        :raises FanGraphs.exceptions.InvalidFilterOption: Filter ``query`` cannot be configured to ``option``
        """
        options = self.list_options(query)
        try:
            index = options.index(option)
        except ValueError:
            raise FanGraphs.exceptions.InvalidFilterOptionException(query, option)
        self.page.hover(self.__dropdowns[query])
        elem = self.page.query_selector_all(f"{self.__dropdowns[query]} ul li")[index]
        elem.click()

    def __close_ad(self):
        """
        Closes the ad which may interfere with interactions with other page elements
        """
        elem = self.page.query_selector(".ezmob-footer-close")
        if elem and elem.is_visible():
            elem.click()

    def export(self, name="", *, size="Infinity", sortby="Name", reverse=False):
        """
        Exports the current leaderboard as a CSV file.
        The file will be saved to *./out*.
        If ``name`` is not specified, the file will take the following format:
        ``datetime.datetime.now().strftime("%d.%m.%y %H.%M.%S")``

        :param name: The filename to rename the exported file to
        :param size: The number of rows, preset to 30, 50, 100, 200, or Infinity
        :param sortby: The table header to sort the data by
        :param reverse: If ``True``, the ordering of the data is reversed
        """
        self.__close_ad()
        self.__expand_table(size=size)
        self.__sortby(sortby.title(), reverse=reverse)
        if not name or os.path.splitext(name)[1] != ".csv":
            name = "{}.csv".format(
                datetime.datetime.now().strftime("%d.%m.%y %H.%M.%S")
            )
        with open(os.path.join("out", name), "w", newline="") as file:
            writer = csv.writer(file)
            self.__write_table_headers(writer)
            self.__write_table_rows(writer)

    def __expand_table(self, *, size="Infinity"):
        """
        Sets the data table size to the specified number of rows.

        :param size: The number of rows, preset to 30, 50, 100, 200 or Infinity
        """
        selector = ".table-page-control:nth-child(3) select"
        dropdown = self.page.query_selector(selector)
        dropdown.click()
        elems = self.soup.select(f"{selector} option")
        options = [e.getText() for e in elems]
        size = "Infinity" if size not in options else size
        index = options.index(size)
        option = self.page.query_selector_all(f"{selector} option")[index]
        option.click()

    def __sortby(self, sortby, *, reverse=False):
        """
        Sorts the data in the table to the specified table header

        :param sortby: The table header to sort the data by
        :param reverse: If ``True``, the ordering of the data will be reversed
        """
        selector = ".table-scroll thead tr th"
        elems = self.soup.select(selector)
        options = [e.getText() for e in elems]
        index = options.index(sortby)
        option = self.page.query_selector_all(selector)[index]
        option.click()
        if reverse:
            option.click()

    def __write_table_headers(self, writer: csv.writer):
        """
        Writes the data table headers

        :param writer: The csv.writer object
        """
        selector = ".table-scroll thead tr th"
        elems = self.soup.select(selector)
        headers = [e.getText() for e in elems]
        writer.writerow(headers)

    def __write_table_rows(self, writer: csv.writer):
        """
        Writes each row of the data table

        :param writer: The csv.writer object
        """
        selector = ".table-scroll tbody tr"
        row_elems = self.soup.select(selector)
        for row in row_elems:
            elems = row.select("td")
            items = [e.getText() for e in elems]
            writer.writerow(items)

    def reset(self):
        """
        Calls the ``get()`` method of :py:attr:`browser`, passing :py:attr:`address`.
        """
        self.page.goto(self.address)
        self.__refresh_parsers()

    def quit(self):
        """
        Calls the ``quit()`` method of :py:attr:`browser`
        """
        self.__browser.close()
        self.__play.stop()


class GameSpanLeaderboards:

    def __init__(self):
        pass


class KBOLeaderboards:

    def __init__(self):
        pass


class WARLeaderboards:

    def __init__(self):
        pass
