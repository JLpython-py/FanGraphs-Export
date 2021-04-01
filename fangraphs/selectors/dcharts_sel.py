#! python3
# fangraphs/selectors/dcharts_sel.py

"""
CSS selectors for the classes in :py:mod:`fangraphs.depth_charts`.
"""


class DepthCharts:
    selections = {
        "type": "#tsPosition"
    }
    dropdowns = {
        "al_east": ".menu-team > .menu-team-header:nth-child(1)",
        "al_central": ".menu-team > .menu-team-header:nth-child(2)",
        "al_west": ".menu-team > .menu-team-header:nth-child(3)",
        "nl_east": ".menu-team > .menu-team-header:nth-child(4)",
        "nl_central": ".menu-team > .menu-team-header:nth-child(5)",
        "nl_west": ".menu-team > .menu-team-header:nth-child(6)",
        "free_agents": ".menu-team > .menu-team-header:nth-child(7)",
    }
    waitfor = ""
    export_data = ""
