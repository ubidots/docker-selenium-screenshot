import time

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def _take_screenshot(browser, file_name):
    img = browser.get_screenshot_as_png()
    with open(file_name, "wb") as image:
        image.write(img)


def _init_browser(url, width=1000, height=500):
    try:
        window_width = int(width) if width is not None else 1000
        window_height = int(height) if height is not None else 500
        display = Display(visible=0, size=(1386, 768))
        display.start()

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option(
            "prefs", {"download.prompt_for_download": False}
        )
        browser = webdriver.Chrome(options=chrome_options)
        browser.set_window_size(window_width, window_height)
        browser.get(url)

        return browser
    except Exception as ex:
        return None


def resize_chromium_viewport(browser, height):
    """
        Change the viewport value of  iframe content only when the document has just one

        Keyword arguments:
        browser -- Selenium browser instance
        height -- Browser height
    """
    window_height = int(height) if height is not None else 500
    # Run javasript script to get the iframe's body height
    new_height = browser.execute_script(
        """
        var iframes = document.querySelectorAll('iframe');
        if (iframes.length === 1) {
            var canvas = iframes[0];
            return canvas.contentDocument.body.scrollHeight;
        }
        return arguments[0];
    """,
        window_height,
    )

    if window_height != new_height:
        # An extra margin to prevent hide some content
        HEIGHT_DELTA = 150
        # Append a custom command with current browser session
        browser.command_executor._commands["send_command"] = (
            "POST",
            "/session/{0}/chromium/send_command".format(browser.session_id),
        )
        # Emulation.setDeviceMetricsOverride is a command which allows us to change the viewport size
        params = {
            "cmd": "Emulation.setDeviceMetricsOverride",
            "params": {
                "mobile": False,
                # 1366 is a inherit value from puppeteer script
                "width": 1366,
                "height": max(new_height, window_height) + HEIGHT_DELTA,
                "deviceScaleFactor": 1,
                "screenOrientation": {"angle": 0, "type": "portraitPrimary"},
            },
        }
        # Run custom command
        browser.execute("send_command", params)


def take_selenium_screenshot(url, file_name, width=1000, height=500, **kwargs):
    app_selector_xpath = kwargs.get("app_selector_xpath", "//div[@id='root']")
    not_load_selector_xpath = kwargs.get(
        "not_load_selector_xpath", "//div[contains(@class, 'selenium-data-not-loaded')]"
    )
    # Init chromium
    browser = _init_browser(url, width, height)
    try:
        # Wait until the root element is loaded
        WebDriverWait(browser, 10000).until(
            EC.presence_of_element_located((By.XPATH, app_selector_xpath))
        )
        time.sleep(1)

        # Check if the element is empty
        empty_elements = browser.find_elements_by_xpath(not_load_selector_xpath)
        if len(empty_elements) > 0:
            raise "Data was not loaded, selection `#root .selenium-data-not-loaded` detected."
        time.sleep(1)

        # Resize window for canvas widgets
        resize_chromium_viewport(browser, height)

        # Wait a little bit for DOM changes
        time.sleep(1)

        # Take the screenshot
        _take_screenshot(browser, file_name)
    except Exception as ex:
        print(ex)
    finally:
        if browser is not None:
            browser.quit()


if __name__ == "__main__":
    import sys

    params = {
        "url": sys.argv[1],
        "file_name": sys.argv[2],
        "width": sys.argv[3],
        "height": sys.argv[4]
    }
    if len(sys.argv) == 7:
        params.update(
            {"app_selector_xpath": sys.argv[5], "not_load_selector_xpath": sys.argv[6]}
        )

    take_selenium_screenshot(**params)
