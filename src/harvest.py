"""
Script for automatic baits harvesting and hunger/comfort refill.

Usage: harvest.py
"""

# pylint: disable=no-member
# setting node's attributes will be merged on the fly

import argparse
from time import time, sleep

import pyautogui as pag

import script
from monitor import Monitor
from setting import Setting

# ------------------ flag name, attribute name, description ------------------ #
ARGS = (
    ("power_saving", "power_saving_enabled", "_"),
    ("check_delay_second", "check_delay_second", "_"),
)

# ------------------------ attribute name, description ----------------------- #
RESULTS = (
    ("tea_count", "Tea consumed"),
    ("carrot_count", "Carrot consumed"),
    ("harvest_count", "Number of harvests"),
)


class App:
    """Main application class."""

    def __init__(self):
        """Initialize counters and merge args into setting node."""
        args = self.parse_args()
        self.setting = Setting()
        self.setting.merge_args(args, ARGS)
        self.monitor = Monitor(self.setting)

        self.tea_count = 0
        self.carrot_count = 0
        self.harvest_count = 0

    def parse_args(self) -> argparse.Namespace:
        """Cofigure argparser and parse the command line arguments.

        :return dict-like parsed arguments
        :rtype: argparse.Namespace
        """
        parser = argparse.ArgumentParser(
            description="Harvest baits and refill hunger/comfort automatically.",
        )
        parser.add_argument(
            "-s",
            "--power-saving",
            action="store_true",
            help="Open control panel between checks to reduce power consumption",
        )
        parser.add_argument(
            "-n",
            "--check-delay-second",
            type=int,
            default=32,
            help="The delay time between each checks, default to 32 (seconds)",
        )
        return parser.parse_args()

    def start_harvesting_loop(self) -> None:
        """Main harvesting loop."""
        setting = self.setting
        monitor = self.monitor

        pag.press(setting.shovel_spoon_shortcut)
        sleep(3)
        pre_refill_time = 0
        while True:
            if time() - pre_refill_time > 300 and monitor.is_comfort_low():
                pre_refill_time = time()
                self._consume_food("tea")
                self.tea_count += 1

            if monitor.is_hunger_low():
                self._consume_food("carrot")
                self.carrot_count += 1

            if monitor.is_energy_high():
                self._harvest_baits()
                self.harvest_count += 1

            if setting.power_saving_enabled:
                pag.press("esc")
            sleep(self.check_delay_second)
            if setting.power_saving_enabled:
                pag.press("esc")
            sleep(0.25)

    def _harvest_baits(self) -> None:
        """Harvest baits, the tool should be pulled out in start_harvesting_loop()."""
        # dig and wait (4 + 1)s
        pag.click()
        sleep(5)

        i = 64
        while i > 0 and not self.monitor.is_harvest_success():
            i = script.sleep_and_decrease(i, 2)

        # accept result
        pag.press("space")
        sleep(0.25)

    def _consume_food(self, food: str) -> None:
        """Open food menu, then click on the food icon to consume it.

        :param food: food name
        :type food: str
        """
        with pag.hold("t"):
            sleep(0.25)
            food_position = getattr(self.monitor, "get_food_position")(food)
            pag.moveTo(food_position)
            pag.click()
            sleep(0.25)


if __name__ == "__main__":
    app = App()
    if app.setting.enable_confirmation:
        script.ask_for_confirmation("Are you ready to start harvesting baits")
    app.setting.window_controller.activate_game_window()
    try:
        app.start_harvesting_loop()
    except KeyboardInterrupt:
        pass
    script.display_running_results(app, RESULTS)
