"""
Environment for Behave Testing
"""

import time
from os import getenv
import requests
from requests.exceptions import ConnectionError, Timeout
from selenium import webdriver

WAIT_SECONDS = int(getenv("WAIT_SECONDS", "60"))
BASE_URL = getenv("BASE_URL", "http://localhost:8080")
DRIVER = getenv("DRIVER", "chrome").lower()


def before_all(context):
    """Executed once before all tests"""
    context.base_url = BASE_URL
    context.wait_seconds = WAIT_SECONDS

    # Wait for the service to be available before starting tests
    wait_for_service(BASE_URL, context.wait_seconds)

    # Select either Chrome or Firefox
    if "firefox" in DRIVER:
        context.driver = get_firefox()
    else:
        context.driver = get_chrome()

    context.driver.implicitly_wait(context.wait_seconds)
    context.driver.set_page_load_timeout(context.wait_seconds)
    context.driver.set_window_size(1280, 1300)
    context.config.setup_logging()


def after_all(context):
    """Executed after all tests"""
    if hasattr(context, "driver"):
        context.driver.quit()


def wait_for_service(base_url, wait_seconds):
    """
    Wait for the service to be available

    Args:
        base_url: The base URL of the service
        wait_seconds: Maximum time to wait for the service
    """
    print(f"Waiting for service at {base_url} to be ready...")

    # Calculate number of retries based on wait_seconds
    # Try every 2 seconds
    retry_interval = 2
    max_retries = wait_seconds // retry_interval

    for attempt in range(max_retries):
        try:
            # Try to hit the health endpoint first (if available)
            health_url = f"{base_url}/api/health"
            response = requests.get(health_url, timeout=5)

            if response.status_code == 200:
                print(
                    f"✓ Service is ready! Health check passed on attempt {attempt + 1}"
                )
                return
            else:
                print(
                    f"Health check returned status {response.status_code}, retrying..."
                )

        except (ConnectionError, Timeout) as error:
            # If health endpoint doesn't exist, try the root URL
            try:
                response = requests.get(base_url, timeout=5)
                if response.status_code in [
                    200,
                    404,
                ]:  # 404 is OK, means service is responding
                    print(
                        f"✓ Service is ready! Root URL check passed on attempt {attempt + 1}"
                    )
                    return
            except (ConnectionError, Timeout):
                pass

            # Service not ready yet
            if attempt < max_retries - 1:
                print(
                    f"Attempt {attempt + 1}/{max_retries}: Service not ready yet, retrying in {retry_interval}s... ({error})"
                )
                time.sleep(retry_interval)
            else:
                print(
                    f"Warning: Health check failed after {max_retries} attempts: {error}"
                )
                print("Proceeding with tests anyway, but they may fail...")


######################################################################
# Utility functions to create web drivers
######################################################################


def get_chrome():
    """Creates a headless Chrome driver"""
    print("Running Behave using the Chrome driver...\n")
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    return webdriver.Chrome(options=options)

def get_firefox():
    """Creates a headless Firefox driver"""
    print("Running Behave using the Firefox driver...\n")
    options = webdriver.FirefoxOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    options.add_argument("--width=1280")
    options.add_argument("--height=1300")
    return webdriver.Firefox(options=options)
