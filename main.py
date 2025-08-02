#!/usr/bin/env python3

import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, InvalidSelectorException

# --- Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("miwifi-selenium")

# --- Environment Variables ---
SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL")
ROUTER_ADMIN_URL = os.environ.get("ROUTER_ADMIN_URL")
ROUTER_PASSWORD = os.environ.get("ROUTER_PASSWORD")
DEBUG_PAUSE_SECONDS = int(os.environ.get("DEBUG_PAUSE_SECONDS", 0))
ERROR_ARTIFACTS_DIR = os.environ.get("ERROR_ARTIFACTS_DIR", "/app/errors")

# --- Validation ---
if not all([SELENIUM_REMOTE_URL, ROUTER_ADMIN_URL, ROUTER_PASSWORD]):
    logger.critical("One or more required environment variables are not set: SELENIUM_REMOTE_URL, ROUTER_ADMIN_URL, ROUTER_PASSWORD")
    exit(1)

# --- Selenium Setup ---
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.accept_insecure_certs = True

# --- Helper Functions ---
def wait_for_overlay_to_disappear(driver, timeout=8):
    try:
        WebDriverWait(driver, timeout).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, "div.panel-mask")))
    except TimeoutException:
        logger.warning("Overlay may still be visible after %ds, proceeding...", timeout)

def wait_and_click(driver, by, value, desc, timeout=10):
    logger.info("Waiting for %s...", desc)
    try:
        element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        element.click()
        logger.info("Successfully clicked %s.", desc)
        return True
    except (TimeoutException, InvalidSelectorException) as e:
        logger.error("Error finding or clicking %s: %s", desc, str(e))
        return False

def create_driver_with_retry(url, options, retries=10, delay=2):
    for attempt in range(retries):
        try:
            return webdriver.Remote(command_executor=url, options=options)
        except WebDriverException as e:
            logger.warning("Selenium not ready, attempt %d/%d: %s", attempt + 1, retries, str(e).split('\n')[0])
            time.sleep(delay)
    logger.critical("Could not connect to Selenium after %d retries. Exiting.", retries)
    exit(2)

def save_debug_artifacts(driver):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    logger.info(f"Saving debug artifacts to {ERROR_ARTIFACTS_DIR}")
    try:
        os.makedirs(ERROR_ARTIFACTS_DIR, exist_ok=True)
        screenshot_path = os.path.join(ERROR_ARTIFACTS_DIR, f"error_{timestamp}.png")
        source_path = os.path.join(ERROR_ARTIFACTS_DIR, f"error_src_{timestamp}.html")
        driver.save_screenshot(screenshot_path)
        logger.info(f"Saved screenshot to {screenshot_path}")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info(f"Saved page source to {source_path}")
    except Exception as e:
        logger.error(f"Failed to save debug artifacts: {e}")

# --- Main Execution ---
def main():
    driver = None
    try:
        driver = create_driver_with_retry(SELENIUM_REMOTE_URL, chrome_options)
        logger.info("Opening router admin page: %s", ROUTER_ADMIN_URL)
        driver.get(ROUTER_ADMIN_URL)
        
        # LOGIN
        password_input = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, "loginDialogPassword")))
        password_input.clear()
        password_input.send_keys(ROUTER_PASSWORD)
        driver.find_element(By.ID, "loginDialogBtn").click()
        WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.ID, "loginDialogPassword")))
        logger.info("Login successful.")
        wait_for_overlay_to_disappear(driver)
        
        # NAVIGATION & REBOOT
        steps = [
            (By.XPATH, "//div[@id='nav']//a[contains(text(), 'Advanced')]", "Advanced navbar item"),
            (By.XPATH, "//div[contains(@class, 'cpe-set-nav')]//li[.//span[text()='System settings']]", "System settings menu"),
            (By.ID, "btnReboot", "Reboot button"),
            (By.XPATH, "//button[contains(@class, 'btn-primary') and contains(., 'Reboot')]", "Reboot confirmation 1"),
            (By.XPATH, "//a[@data-id='ok' and contains(@class, 'btn-primary')]", "Reboot confirmation 2 (OK)")
        ]

        for i, (by, value, desc) in enumerate(steps):
            if i > 0: time.sleep(1) # Add a small pause between steps
            if not wait_and_click(driver, by, value, desc):
                raise RuntimeError(f"Failed at step: {desc}")
            if i == 0: wait_for_overlay_to_disappear(driver) # Wait for overlay after first main navigation

        logger.info("Reboot command sent successfully!")
        
    except Exception as exc:
        logger.error(f"Automation failed: {exc}")
        if driver:
            save_debug_artifacts(driver)
            if DEBUG_PAUSE_SECONDS > 0:
                logger.info(f"Pausing {DEBUG_PAUSE_SECONDS} seconds for manual inspection...")
                time.sleep(DEBUG_PAUSE_SECONDS)
        exit(1)
        
    finally:
        if driver:
            driver.quit()
        logger.info("Automation finished.")

if __name__ == '__main__':
    main()
