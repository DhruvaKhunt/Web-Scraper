import time
import re
import tkinter as tk
from tkinter import * 
from tkinter import ttk       
from tkinter.ttk import *
from tkinter import messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import pandas as pd
import os

# Function to generate URLs for subsequent pages
def get_next_page_urls(first_page_url, num_pages=4):
    page_number_pattern = re.compile(r'(\d+)')
    match = page_number_pattern.findall(first_page_url)
    if not match:
        raise ValueError("No page number found in the given URL")
    first_page_number = int(match[-1])
    parts = page_number_pattern.split(first_page_url, maxsplit=1)
    base_url = parts[0] + "{}" + parts[2]
    next_page_urls = [base_url.format(first_page_number + i) for i in range(1, num_pages + 1)]
    return next_page_urls

# Function to scrape data from the website
def scrape_website(url, navigation_type, nav_button_xpath, xpath_expression):
    # Set up the Selenium WebDriver
    service = Service(executable_path="./chromedriver.exe")
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(3)
    scraped_data = []
    try:
        # Handle "Show more button" navigation
        if navigation_type == "Show more button":
            for _ in range(5):
                try:
                    elements = driver.find_elements(By.XPATH, xpath_expression)
                    for element in elements:
                        scraped_data.append(element.text.strip())
                    show_more_button = driver.find_element(By.XPATH, nav_button_xpath)
                    driver.execute_script("arguments[0].click();", show_more_button)
                    time.sleep(3)
                except Exception as e:
                    print(f"Error or no more content to load: {e}")
                    break

        # Handle "Pagination" navigation
        elif navigation_type == "Pagination":
            next_page_urls = get_next_page_urls(url, 5)
            for page_url in next_page_urls:
                try:
                    driver.get(page_url)
                    time.sleep(3)
                    elements = driver.find_elements(By.XPATH, xpath_expression)
                    for element in elements:
                        scraped_data.append(element.text.strip())
                except Exception as e:
                    print(f"Error navigating to {page_url}: {e}")
                    break

        # Handle "Infinite scroll" navigation
        elif navigation_type == "Infinite scroll":
            scroll_pause_time = 2
            last_height = driver.execute_script("return document.body.scrollHeight")
            items = []
            itemTargetCount = 100
            while itemTargetCount > len(items):
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(scroll_pause_time)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        print("Reached end of the page. No more content to load.")
                        break       
                    last_height = new_height
                    elements = driver.find_elements(By.XPATH, xpath_expression)
                    for element in elements:
                        scraped_data.append(element.text.strip())
                    items = scraped_data
                except Exception as e:
                    print(f"Error scrolling or no more content to load: {e}")
                    break

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
    finally:
        driver.quit()
    return scraped_data

# Function to update the visibility of the navigation button XPath entry field
def update_nav_button_visibility(*args):
    navigation_type = navigation_type_var.get()
    if navigation_type == "Show more button":
        nav_button_xpath_label.grid(row=2, column=0, sticky=tk.W)
        nav_button_xpath_entry.grid(row=2, column=1, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
    else:
        nav_button_xpath_label.grid_remove()
        nav_button_xpath_entry.grid_remove()

# Function to start the scraping process
def start_scraping():
    global scraped_data
    url = url_entry.get()
    navigation_type = navigation_type_var.get()
    nav_button_xpath = nav_button_xpath_entry.get()
    xpath_expression = xpath_expression_entry.get()
    field_name = field_name_entry.get()
    if not url or not navigation_type or not xpath_expression or not field_name:
        messagebox.showerror("Error", "Please fill in all required fields")
        return
    scraped_data = scrape_website(url, navigation_type, nav_button_xpath, xpath_expression)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "\n".join(scraped_data))
    messagebox.showinfo("Info", f"Scraping completed. {len(scraped_data)} items scraped.")
    save_button.config(state=tk.NORMAL)
    open_button.config(state=tk.NORMAL)
  
# Function to save the scraped data to a CSV file
def save_to_csv():
    if not scraped_data:
        messagebox.showerror("Error", "No data to save")
        return
    field_name = field_name_entry.get()
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        if os.path.exists(file_path):
            existing_data = pd.read_csv(file_path)
            new_data = pd.DataFrame(scraped_data, columns=[field_name])
            combined_data = pd.concat([existing_data, new_data], axis=1)
            combined_data.to_csv(file_path, index=False)
        else:
            new_data = pd.DataFrame(scraped_data, columns=[field_name])
            new_data.to_csv(file_path, index=False)
        messagebox.showinfo("Info", f"Data saved to {file_path}")

# Function to open and display the content of a CSV file
def open_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path and os.path.isfile(file_path):
        df = pd.read_csv(file_path)
        messagebox.showinfo("CSV Content", df.to_string())


# Set up the Tkinter GUI
root = Tk()
root.title("Web Scraper")
root.geometry("700x700")
root.configure(bg="#f0f0f0")

# Configure Tkinter styles
style = ttk.Style()
style.configure("TLabel", font=("Helvetica", 11), padding=5, background="#f0f0f0")
style.configure("TButton", font=("Helvetica", 11), padding=5)
style.configure("TEntry", font=("Helvetica", 11), padding=5)
style.configure("TCombobox", font=("Helvetica", 11), padding=5)

# Add URL entry field
Label(root, text="URL:").grid(row=0, column=0, sticky=W)
url_entry = Entry(root)
url_entry.grid(row=0, column=1, columnspan=3, sticky=W+E, padx=5, pady=5)

# Add navigation type combobox
Label(root, text="Navigation Type:").grid(row=1, column=0, sticky=W)
navigation_type_var = StringVar()
navigation_type_combobox = ttk.Combobox(root, textvariable=navigation_type_var, state='readonly')
navigation_type_combobox['values'] = ("Show more button", "Pagination", "Infinite scroll")
navigation_type_combobox.grid(row=1, column=1, columnspan=3, sticky=W+E, padx=5, pady=5)

# Add navigation button XPath entry field
nav_button_xpath_label = Label(root, text="Nav Button XPath:")
nav_button_xpath_entry = Entry(root)

# Add data XPath expression entry field
Label(root, text="Data XPath Expression:").grid(row=3, column=0, sticky=W)
xpath_expression_entry = Entry(root)
xpath_expression_entry.grid(row=3, column=1, columnspan=3, sticky=W+E, padx=5, pady=5)

# Add field name entry field
Label(root, text="Field Name:").grid(row=4, column=0, sticky=W)
field_name_entry = Entry(root)
field_name_entry.grid(row=4, column=1, columnspan=3, sticky=W+E, padx=5, pady=5)

# Add start scraping button
start_button = Button(root, text="Start Scraping", command=start_scraping)
start_button.grid(row=5, column=0, columnspan=4, sticky=W+E, padx=5, pady=5)

# Add text widget to display scraped results
result_text = Text(root, height=20)
result_text.grid(row=6, column=0, columnspan=4, padx=5, pady=5)

# Add save button (initially disabled)
save_button = Button(root, text="Save", command=save_to_csv, state=DISABLED, width=37)
save_button.grid(row=7, column=0, columnspan=1, sticky=W+E, padx=5, pady=5)

# Add open button (initially disabled)
open_button = Button(root, text="Open", command=open_csv, state=DISABLED, width=37)
open_button.grid(row=7, column=1, columnspan=1, sticky=W+E, padx=5, pady=5)

# Bind combobox selection event to update visibility of navigation button XPath entry field
navigation_type_combobox.bind("<<ComboboxSelected>>", update_nav_button_visibility)

root.mainloop()