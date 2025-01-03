import requests
import time
import os
import json
import csv
from datetime import datetime
from colorama import init, Fore, Style

init()

CONFIG_FILE = "config.json"

def set_window_title(title):
    os.system(f"title {title}")

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
    else:
        config = {
            "delay": 1,
            "max_retries": 3,
            "input_file": "usernames.txt",
            "output_file": "results.csv",
            "append_csv": False,
            "batch_size": 100
        }
        save_config(config)
    return config

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

def initialize_csv(output_file):
    if not os.path.exists(output_file) or os.stat(output_file).st_size == 0:
        with open(output_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Username", "Status", "Timestamp"])

def load_existing_results(output_file):
    results = {}
    if os.path.exists(output_file):
        with open(output_file, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                results[row["Username"]] = row
    return results

def save_result(username, status, output_file):
    results = load_existing_results(output_file)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    results[username] = {"Username": username, "Status": status, "Timestamp": timestamp}
    
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Username", "Status", "Timestamp"])
        writer.writeheader()
        writer.writerows(results.values())

def log_error(message):
    with open("error_log.txt", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {message}\n")

def check_username(username, max_retries=3):
    url = f"https://guns.lol/{username}"
    retries = 0
    delay = config["delay"]

    while retries < max_retries:
        try:
            response = requests.get(url, timeout=5)
            if "This user is not claimed" in response.text:
                save_result(username, "available", config["output_file"])
                return Fore.GREEN + f"The username '{username}' is available." + Style.RESET_ALL
            else:
                save_result(username, "unavailable", config["output_file"])
                return Fore.RED + f"The username '{username}' is already in use." + Style.RESET_ALL
        except requests.RequestException as e:
            retries += 1
            log_error(f"Failed to check '{username}': {str(e)} (Retry {retries}/{max_retries})")
            time.sleep(delay)
            delay *= 2 

    save_result(username, "error", config["output_file"])
    return Fore.RED + f"Error: Could not check username '{username}' after {max_retries} attempts." + Style.RESET_ALL

def check_usernames_from_file(filename, delay, max_retries, batch_size):
    try:
        with open(filename, "r") as file:
            usernames = file.read().splitlines()
    except FileNotFoundError:
        print(Fore.RED + f"Error: File '{filename}' not found." + Style.RESET_ALL)
        return
    
    print(Fore.WHITE + f"Checking usernames from {filename}..." + Style.RESET_ALL)
    initialize_csv(config["output_file"])

    for i in range(0, len(usernames), batch_size):
        batch = usernames[i:i+batch_size]
        available_count, unavailable_count, error_count = 0, 0, 0

        for username in batch:
            result = check_username(username, max_retries=max_retries)
            print(result)

            if Fore.GREEN in result:
                available_count += 1
            elif Fore.RED in result:
                unavailable_count += 1
            elif Fore.RED in result:
                error_count += 1

            time.sleep(delay)

        print(Fore.WHITE + f"\nBatch {i//batch_size+1} Summary:" + Style.RESET_ALL)
        print(Fore.GREEN + f"Available: {available_count}" + Style.RESET_ALL)
        print(Fore.RED + f"Unavailable: {unavailable_count}" + Style.RESET_ALL)
        print(Fore.RED + f"Errors: {error_count}" + Style.RESET_ALL)


ASCII_LOGO = Fore.RED + r"""
╔╦╗╔═╗╔═╗╔╦╗╦ ╦╦═╗╔╗ ╔═╗╔╦╗╦╔═╗╔╗╔  ╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔
║║║╠═╣╚═╗ ║ ║ ║╠╦╝╠╩╗╠═╣ ║ ║║ ║║║║  ║║║╠═╣ ║ ║║ ║║║║
╩ ╩╩ ╩╚═╝ ╩ ╚═╝╩╚═╚═╝╩ ╩ ╩ ╩╚═╝╝╚╝  ╝╚╝╩ ╩ ╩ ╩╚═╝╝╚╝
""" + Style.RESET_ALL

def main_menu():
    global config
    config = load_config()

    while True:
        clear_screen()
        print(ASCII_LOGO)
        print("1. Check usernames from file (current: {})".format(config["input_file"]))
        print("2. Enter a single username to check")
        print("3. Exit")

        print()
        choice = input(Fore.WHITE + "Select an option (1-3): " + Style.RESET_ALL)

        if choice == '1':
            check_usernames_from_file(config["input_file"], delay=config["delay"], max_retries=config["max_retries"], batch_size=config["batch_size"])
            input(Fore.WHITE + "\nPress Enter to return to the main menu..." + Style.RESET_ALL)

        elif choice == '2':
            username = input(Fore.WHITE + "Enter a username to check: " + Style.RESET_ALL)
            result = check_username(username, max_retries=config["max_retries"])
            print(result)
            input(Fore.WHITE + "\nPress Enter to return to the main menu..." + Style.RESET_ALL)

        elif choice == '3':
            print(Fore.GREEN + "Exiting... Thank you for using 765's Guns.lol Username Checker!" + Style.RESET_ALL)
            break

        else:
            print(Fore.RED + "Invalid option. Please select a valid option (1-3)." + Style.RESET_ALL)
            time.sleep(1)

if __name__ == "__main__":
    set_window_title("765MN - Guns.lol Username Checker")
    main_menu()
