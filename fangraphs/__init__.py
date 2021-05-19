#! python3
# FanGraphs/__init__.py

"""
Subpackage for scraping the FanGraphs **Leaders** pages.
"""

import os

import pandas as pd
from playwright.sync_api import sync_playwright

import fangraphs.exceptions


class __DecoratorAdapter:
    """
    Adapts a decorator for both function and method usage.
    """

    def __init__(self, decorator, func):
        self.decorator = decorator
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.decorator(self.func)(*args, **kwargs)

    def __get__(self, instance, owner):
        return self.decorator(self.func.__get__(instance, owner))


def __adapt(decorator):
    """
    Decorator for adapting decorators for function or method usage.
    """
    def wrapper(func):
        return __DecoratorAdapter(decorator, func)
    return wrapper


@__adapt
def fangraphs_scraper(func):

    def wrapper(scraper, /, path="out/", *, headless=True):
        path = os.path.abspath(path)
        assert os.path.exists(path)
        with sync_playwright() as play:
            browser = play.chromium.launch(
                headless=headless,
                downloads_path=path
            )
            results = func(scraper(browser))
            browser.close()
            return results

    return wrapper


class ScrapingUtilities:
    """
    Manages the various objects used for scraping the FanGraphs webpages.
    Intializes and manages ``Playwright`` browsers and pages.
    Intializes and manages ``bs4.BeautifulSoup`` objects.
    """
    def __init__(self, browser, address: str, queries):
        """

        :param address:
        :param queries:
        """
        self.browser = browser
        self.page = self.browser.new_page(accept_downloads=True)
        self.address = address
        self.queries = queries

        self.reset()

    def _close_ad(self):
        """
        Closes the ad which may interfere with clicking other page elements.
        """
        elem = self.page.query_selector(".ezmob-footer-close")
        if self.page.query_selector_all(
                "#ezmob-wrapper > div[style='display: none;']"
        ):
            return
        if elem:
            elem.click()

    def list_queries(self):
        """
        Lists the possible filter queries which can be used to modify search results.

        :return: Filter queries which can be used to modify search results
        :rtype: list
        """
        return list(self.queries.__dict__)

    def list_options(self, query: str):
        """
        Lists the possible options which a filter query can be configured to.

        :param query: The filter query
        :return: Options which the filter query can be configured to
        :rtype: list
        :raises FanGraphs.exceptions.InvalidFilterQuery: Invalid argument ``query``
        """
        sel_obj = self.queries.__dict__.get(query.lower())
        if sel_obj is None:
            raise fangraphs.exceptions.InvalidFilterQuery(query)
        return sel_obj.list_options()

    def current_option(self, query: str):
        """
        Retrieves the option which a filter query is currently set to.

        :param query: The filter query being retrieved of its current option
        :return: The option which the filter query is currently set to
        :rtype: str
        :raises FanGraphs.exceptions.InvalidFilterQuery: Invalid argument ``query``
        """
        sel_obj = self.queries.__dict__.get(query.lower())
        if sel_obj is None:
            raise fangraphs.exceptions.InvalidFilterQuery(query)
        return sel_obj.current_option()

    def configure(self, query: str, option: str):
        """
        Configures a filter query to a specified option.

        :param query: The filter query to be configured
        :param option: The option to set the filter query to
        :raises FanGraphs.exceptions.InvalidFilterQuery: Invalid argument ``query``
        """
        self._close_ad()
        sel_obj = self.queries.__dict__.get(query.lower())
        if sel_obj is None:
            raise fangraphs.exceptions.InvalidFilterQuery(query)
        sel_obj.configure(option)

    def export(self, *, cleanup=True):
        """
        Uses the **Export Data** button on the webpage to export the current leaderboard.
        The CSV file is read and the data is stored in a DataFrame.

        :param cleanup: Whether to delete the downloaded file
        :return: The DataFrame containing the CSV data.
        If ``cleanup`` is ``False``, the path to the CSV file will be returned.
        """
        self._close_ad()
        with self.page.expect_download() as down_info:
            self.page.click(self.queries.export_data)
        download = down_info.value
        download_path = download.path()
        dataframe = pd.read_csv(download_path)
        if cleanup:
            os.remove(download_path)
            return dataframe
        else:
            return dataframe, download_path

    def reset(self):
        """
        Navigates :py:attr:`page` to :py:attr:`address`.
        """
        self.page.goto(self.address, timeout=0)
        if self.queries.waitfor:
            self.page.wait_for_selector(".fg-data-grid")
