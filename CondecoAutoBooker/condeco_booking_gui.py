'''
Created on Apr 11, 2025

@author: b55608
'''
import time
import datetime
import threading
import schedule
from tkinter import Tk, Label, Button
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# CONFIGURATIONS
desk_number = "A07-159AA"
days_to_book = ["Tuesday", "Wednesday"]
start_date = datetime.date(2025, 5, 13)
retry_interval_minutes = 30

# Set Chrome options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Path to your chromedriver
CHROMEDRIVER_PATH = "./chromedriver"

running = False

# GUI Functions
def start_automation():
    global running
    if not running:
        running = True
        status_label.config(text="Running...")
        threading.Thread(target=scheduler_loop, daemon=True).start()

def stop_automation():
    global running
    running = False
    status_label.config(text="Stopped")

# Booking Logic
def try_booking():
    if not running:
        return

    today = datetime.date.today()
    delta = datetime.timedelta(days=1)
    target_date = start_date

    while target_date <= today + datetime.timedelta(weeks=4):
        day_name = target_date.strftime('%A')
        if day_name in days_to_book:
            print(f"Attempting to book {desk_number} on {target_date} ({day_name})")
            open_browser_and_book(target_date.strftime('%m/%d/%Y'))
        target_date += delta

# Automation Logic
def open_browser_and_book(date_str):
    driver = webdriver.Chrome(service=ChromeService(CHROMEDRIVER_PATH), options=chrome_options)
    wait = WebDriverWait(driver, 30)
    driver.get("https://cox.condecosoftware.com/master.aspx")

    input("\n>>> Complete SSO login, then press Enter here to continue...\n")

    try:
        wait.until(EC.element_to_be_clickable((By.ID, "DeskBookingHeader"))).click()
        wait.until(EC.element_to_be_clickable((By.ID, "A10"))).click()

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

    finally:
        driver.quit()

# Scheduler Loop
def scheduler_loop():
    schedule.every(retry_interval_minutes).minutes.do(try_booking)
    try_booking()
    while running:
        schedule.run_pending()
        time.sleep(1)

# GUI Setup
app = Tk()
app.title("Condeco Auto Booker")
app.geometry("300x150")

Label(app, text="Desk Auto-Booking Tool", font=("Arial", 14)).pack(pady=10)
status_label = Label(app, text="Stopped", fg="red")
status_label.pack(pady=5)

Button(app, text="Start", command=start_automation, bg="green", fg="white", width=10).pack(pady=5)
Button(app, text="Stop", command=stop_automation, bg="red", fg="white", width=10).pack(pady=5)

app.mainloop()
