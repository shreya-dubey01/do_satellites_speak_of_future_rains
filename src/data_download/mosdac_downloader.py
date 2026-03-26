import time
import os
import shutil

'''
Before you use this script, remember to let your "order" complete and fully populate in the MOSDAC interface, so that all your files are listed on the page.
MOSDAC prevents ordering of more than 2000 entries at a time, so you may have to run the script multiple times.
This script will then find all the "..." menu buttons next to each file, click them, and trigger the Download option using JavaScript to ensure it clicks before the menu can disappear.
The script also handles pagination by looking for a "Next" button and clicking it until there are no more pages left.
'''

# In my experience, Edge's WebDriver (msedgedriver) is the most reliable for MOSDAC downloads, 
# but you can switch to Chrome or Firefox by changing the BROWSER variable and adjusting the driver setup accordingly.
BROWSER = "edge"

# Where to save downloaded files
DOWNLOAD_DIR = r"./mosdac_aod_downloads"

# URL of your MOSDAC orders/file listing page
LISTING_URL = "https://www.mosdac.gov.in/download/"

# Seconds to wait between each download click (increase if downloads are slow)
CLICK_DELAY = 2.0

# Seconds to wait for page elements to appear
WAIT_TIMEOUT = 15

# BROWSER SETUP 

def create_driver():
    import glob
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service

    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
    })
    options.add_argument("--window-size=1400,900")

    # Find msedgedriver.exe shipped with Edge (no internet needed)
    driver_path = shutil.which("msedgedriver")
    if not driver_path:
        for pattern in [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\*\msedgedriver.exe",
            r"C:\Program Files\Microsoft\Edge\Application\*\msedgedriver.exe",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "msedgedriver.exe"),
        ]:
            matches = glob.glob(pattern)
            if matches:
                driver_path = sorted(matches)[-1]
                break

    if driver_path:
        print("[*] Using msedgedriver: " + driver_path)
        return webdriver.Edge(service=Service(driver_path), options=options)

    # Let Selenium do it 4 u
    try:
        return webdriver.Edge(options=options)
    except Exception:
        print("[X] Cannot find msedgedriver.exe.")
        print("    Download it from: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        print("    Place msedgedriver.exe in the same folder as this script, then re-run.")
        raise


# HELPERS
'''
These functions are designed to be resilient to MOSDAC's varying page structures and occasional quirks, like disappearing menus or slow-loading elements. 
The js_click_download function is a key part of this, as it tries multiple strategies to find and click the Download option immediately after opening the menu, 
which helps prevent the menu from closing before we can click.
'''
def get_menu_buttons(driver):
    from selenium.webdriver.common.by import By
    for by, sel in [
        (By.CSS_SELECTOR, "td:last-child button"),
        (By.CSS_SELECTOR, "button.icon-button"),
        (By.CSS_SELECTOR, ".item-action button"),
        (By.XPATH,        "//button[normalize-space(text())='...']"),
        (By.XPATH,        "//tr[td][not(.//th)]//button"),
    ]:
        els = [e for e in driver.find_elements(by, sel) if e.is_displayed()]
        if els:
            print("[*] Found " + str(len(els)) + " menu buttons using: " + sel)
            return els

    print("[!] No menu buttons found. Saving page_dump.html for inspection.")
    html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")
    with open("page_dump.html", "w", encoding="utf-8") as f:
        f.write(html)
    return []


def js_click_download(driver):
    """
    Use JavaScript to find and click the visible Download option immediately,
    before the dropdown has a chance to close.
    """
    js = (
        'var tags = ["a","button","li","span","div"];'
        'for (var t=0; t<tags.length; t++) {'
        '  var els = document.querySelectorAll(tags[t]);'
        '  for (var i=0; i<els.length; i++) {'
        '    var el = els[i];'
        '    if (el.textContent.trim() === "Download") {'
        '      var s = window.getComputedStyle(el);'
        '      if (s.display!=="none" && s.visibility!=="hidden" && el.offsetParent!==null) {'
        '        el.click(); return true;'
        '      }'
        '    }'
        '  }'
        '} return false;'
    )
    return driver.execute_script(js)


# MAIN LOOP

def download_all_files(driver):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, StaleElementReferenceException, ElementClickInterceptedException
    )

    buttons = get_menu_buttons(driver)
    total = len(buttons)
    if total == 0:
        return

    success, failed, index = 0, 0, 0

    while index < total:
        try:
            buttons = get_menu_buttons(driver)
            if index >= len(buttons):
                break

            btn = buttons[index]
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.3)

            # Open the ... menu
            try:
                btn.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", btn)

            time.sleep(0.3)

            #
            clicked = js_click_download(driver)

            if not clicked:
                # Fallback: give it a little more time then try Selenium
                time.sleep(0.5)
                clicked = js_click_download(driver)

            if not clicked:
                # Final fallback: Selenium WebDriverWait
                for xpath in [
                    "//a[normalize-space()='Download']",
                    "//button[normalize-space()='Download']",
                    "//li[normalize-space()='Download']",
                    "//span[normalize-space()='Download']",
                ]:
                    try:
                        el = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        driver.execute_script("arguments[0].click();", el)
                        clicked = True
                        break
                    except TimeoutException:
                        continue

            if clicked:
                success += 1
                print("  [" + str(index+1) + "/" + str(total) + "] [OK] Download triggered")
            else:
                print("  [" + str(index+1) + "/" + str(total) + "] [!] Download option not found - skipping")
                # Close any stray open menu
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
                failed += 1

            time.sleep(CLICK_DELAY)

        except StaleElementReferenceException:
            print("  [" + str(index+1) + "/" + str(total) + "] [!] Stale element, retrying...")
            time.sleep(1)
            continue

        except Exception as e:
            print("  [" + str(index+1) + "/" + str(total) + "] [!] Error: " + str(e))
            failed += 1
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
            except Exception:
                pass

        index += 1

    print("\n[*] Done. Triggered: " + str(success) + "  |  Failed: " + str(failed) + "  |  Total: " + str(total))


# PAGINATION 

def try_next_page(driver):
    from selenium.webdriver.common.by import By
    for xpath in [
        "//a[normalize-space()='Next']",
        "//button[normalize-space()='Next']",
        "//*[@aria-label='Next page']",
    ]:
        try:
            btn = driver.find_element(By.XPATH, xpath)
            if btn.is_displayed() and btn.is_enabled():
                btn.click()
                time.sleep(2)
                return True
        except Exception:
            continue
    return False


# ENTRY POINT 

def main():
    driver = create_driver()
    try:
        print("[*] Opening MOSDAC...")
        driver.get(LISTING_URL)
        print("[*] Please log in and navigate to your file listing page.")
        input("Press Enter when files are visible on screen: ")

        page = 1
        while True:
            print("\n--- Page " + str(page) + " ---")
            download_all_files(driver)
            if try_next_page(driver):
                page += 1
            else:
                print("\n[*] No more pages. All done!")
                break
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")
    finally:
        input("\nPress Enter to close the browser...")
        driver.quit()


if __name__ == "__main__":
    main()
