from logging import getLogger
from pathlib import Path
from subprocess import Popen
from tempfile import TemporaryDirectory
from time import sleep

import undetected_chromedriver as uc
from selenium import webdriver
from .humanlike import randsleep


class BrowserError(Exception):
    pass


class Browser:
    URL = "https://driverpracticaltest.dvsa.gov.uk/login"
    instances = []

    def __init__(
        self,
        port: int = None,
        buster: Path = None,
        chrome: str = "google-chrome-stable",
        chromedriver_path: str = "chromedriver",
        url: str = None,
    ):
        self._installed = False
        self._port = port or 8745
        if buster and not buster.is_dir():
            raise BrowserError("Please unzip buster and pass the dir.")
        self._buster = buster
        self._profile_dir = None
        self._chrome = chrome
        i = max(self.instances) + 1 if self.instances else 1
        self.instances.append(i)
        self.name = f"Browser-{i}"
        self._logger = getLogger(self.name)
        self._proc = None
        self._chromedriver_path = chromedriver_path
        self._url = url or self.URL

    @property
    def buster_arg(self) -> str:
        if self._buster:
            return f"--load-extension={self._buster}"
        else:
            return ""

    @property
    def profile_arg(self) -> str:
        if not self._profile_dir:
            self._profile_dir = TemporaryDirectory()
        return f"--user-data-dir={self._profile_dir}"

    @property
    def port_arg(self) -> str:
        return f"--remote-debugging-port={self._port}"

    def kill(self, proc):
        self._logger.info("Killing Chrome")
        if not proc:
            return
        proc.terminate()
        proc.wait(2)
        if proc.poll():
            self.logger.info("Failed to die: killing with SIGKILL")
            proc.kill()
            proc.wait(2)
            if proc.poll():
                raise BrowserError("Process failed to die")

    def launch_chrome(self, extra_args=None):
        self._logger.info("Starting chrome")
        cmd = [
            self._chrome,
            self.port_arg,
            self.profile_arg,
            self.buster_arg,
            "--no-first-run",
            "--blink-settings=imagesEnabled=false",
            self._url,
        ]
        if extra_args:
            cmd.append(extra_args)
        # needed at present to prevent failure
        # chrome_options.experimental_options.pop("excludeSwitches")
        self._proc = Popen(cmd)

    def __enter__(self) -> webdriver.Chrome:
        self.launch_chrome()

        self._logger.info("Waiting 10s for page to load and js to run.")
        randsleep(10)
        chrome_options = webdriver.ChromeOptions()

        chrome_options.add_experimental_option(
            "debuggerAddress", f"localhost:{self._port}"
        )

        driver = webdriver.Chrome(
            executable_path=self._chromedriver_path,
            options=chrome_options,
        )

        driver.execute_cdp_cmd(
            "Network.setBlockedURLs",
            {
                "urls": [
                    "https://driverpracticaltest.dvsa.gov.uk/nions-to-vnse-the-Bewarfish-so-like-here-hoa-Mon"
                ]
            },
        )
        driver.execute_cdp_cmd("Network.enable", {})
        driver.refresh()
        return driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill(self._proc)
        self._profile_dir.cleanup()


class TorBrowser(Browser):
    """A browser tunneled by TOR."""

    def start_tor(self):
        cmd = ["tor", "--SocksPort", "8897"]
        proc = Popen(cmd)
        self._tor_proc = proc

    def launch_chrome(self):
        tor_args = [
            '--proxy-server="socks5://localhost:8997"',
            '--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE myproxy"',
        ]
        super().launch_chrome(extra_args=tor_args)

    def __exit__(self, *args):
        super().__exit__(*args)
        self.kill(self._tor_proc)
