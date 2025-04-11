import time
import datetime
import threading
import schedule
import os
from tkinter import Tk, Label, Button
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# CONFIGURATIONS
desk_number = "A07-159AA"
days_to_book = ["Thursday", "Friday"]
start_date = datetime.date(2025, 5, 15)
retry_interval_minutes = 15

# Set Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Path to your chromedriver
CHROMEDRIVER_PATH = r"C:\\Webdrivers\\chromedriver.exe"
print(f"Using ChromeDriver path: {CHROMEDRIVER_PATH}")
print("Exists?", os.path.exists(CHROMEDRIVER_PATH))

running = False

# GUI Functions
def start_automation():
    global running
    if not running:
        running = True
        print(">>> Start clicked")
        status_label.config(text="Running...")
        threading.Thread(target=scheduler_loop, daemon=True).start()

def stop_automation():
    global running
    running = False
    print(">>> Stopped by user")
    status_label.config(text="Stopped")

# Booking Logic
def try_booking():
    if not running:
        print(">>> Skipping booking — automation is stopped.")
        return

    print(">>> Trying to book...")

    today = datetime.date.today()
    start_check_date = today + datetime.timedelta(weeks=5)
    end_check_date = start_check_date + datetime.timedelta(weeks=4)

    target_date = start_check_date
    while target_date <= end_check_date:
        day_name = target_date.strftime('%A')
        print(f"Checking {target_date} ({day_name})...")

        if day_name in days_to_book:
            print(f"✔️ Match found! Attempting to book {desk_number} on {target_date} ({day_name})")
            open_browser_and_book(target_date.strftime('%m/%d/%Y'))
            return  # Exit after first successful attempt
        else:
            print(f"⏩ Skipping {target_date} ({day_name}) — not a booking day.")

        target_date += datetime.timedelta(days=1)


# Automation Logic
def open_browser_and_book(date_str):
    print(f">>> Opening Chrome for {date_str}")
    try:
        driver = webdriver.Chrome(service=ChromeService(CHROMEDRIVER_PATH), options=chrome_options)
        wait = WebDriverWait(driver, 30)
        driver.get("https://cox.condecosoftware.com/master.aspx")

        input("\n>>> Please complete SSO login in Chrome, then press Enter here to continue...\n")

        print(">>> SSO complete. Waiting 10 seconds for page to load...")
        time.sleep(10)
        print(">>> Current page title:", driver.title)
        print(">>> Current URL:", driver.current_url)
        driver.save_screenshot("debug_landing_page.png")

        # Switch to iframe that holds the main menu if necessary
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                driver.find_element(By.ID, "DeskBookingHeader")
                print(">>> Found DeskBookingHeader inside iframe.")
                break
            except:
                driver.switch_to.default_content()

        wait.until(EC.element_to_be_clickable((By.ID, "DeskBookingHeader"))).click()
        wait.until(EC.element_to_be_clickable((By.ID, "A10"))).click()
        print(">>> Clicked 'Book a personal space'")

        # Switch into the booking page iframe
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "mainDisplayFrame")))
        print(">>> Switched to iframe 'mainDisplayFrame'")

        # Wait for loading screen to disappear
        try:
            WebDriverWait(driver, 20).until(EC.invisibility_of_element_located((By.CLASS_NAME, "preLoaderBg")))
            print(">>> Preloader overlay is gone. Safe to click Search.")
        except:
            print("⚠️ Timeout waiting for preLoaderBg to disappear. Proceeding anyway.")
        
        # Now safely click Search
        wait.until(EC.element_to_be_clickable((By.ID, "btnSearch"))).click()

        time.sleep(2)

        wait.until(EC.element_to_be_clickable((By.ID, "tabFloorPlan"))).click()
        time.sleep(2)

        desk_xpath = f"//a[contains(@aria-label, '{desk_number}') and contains(@onclick, '{date_str}') and contains(@onclick, 'fn_makeBooking')]"
        desk_element = wait.until(EC.element_to_be_clickable((By.XPATH, desk_xpath)))
        desk_element.click()
        time.sleep(2)

        book_button = wait.until(EC.element_to_be_clickable((By.ID, "btnbook")))
        book_button.click()

        print(f"[SUCCESS] Booked {desk_number} on {date_str}")
        time.sleep(2)

    except Exception as e:
        print(f"[ERROR] Booking failed for {date_str}: {e}")
        driver.save_screenshot(f"booking_error_{date_str.replace('/', '-')}.png")

    finally:
        driver.quit()


# Scheduler Loop
def scheduler_loop():
    try:
        print(">>> Scheduler started")
        schedule.every(retry_interval_minutes).minutes.do(try_booking)
        try_booking()
        while running:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        print(f"[ERROR in scheduler]: {e}")

# GUI Setup
app = Tk()
app.title("Condeco Auto Booker")
app.geometry("300x180")

Label(app, text="Desk Auto-Booking Tool", font=("Arial", 14)).pack(pady=10)
status_label = Label(app, text="Stopped", fg="red")
status_label.pack(pady=5)

Button(app, text="Start", command=start_automation, bg="green", fg="white", width=10).pack(pady=5)
Button(app, text="Stop", command=stop_automation, bg="red", fg="white", width=10).pack(pady=5)

app.mainloop()

# Uncomment this to test booking directly:
# if __name__ == "__main__":
#     open_browser_and_book("05/14/2025")