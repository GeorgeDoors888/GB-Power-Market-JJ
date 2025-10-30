#!/usr/bin/env python
"""
Manual DNO DUoS File Download Helper

This script opens a web browser to help manually download the required DNO files
from the comprehensive guide. It cannot download the files automatically due to
website security measures, but it will help navigate to the correct pages.

Usage:
    source .venv/bin/activate && python manual_dno_download_helper.py
"""

import os
import sys
import time
import webbrowser


def clear_screen():
    """Clear the terminal screen"""
    os.system("cls" if os.name == "nt" else "clear")


def show_banner():
    """Display script banner"""
    print("\033[1;34m" + "=" * 80 + "\033[0m")
    print(
        "\033[1;34m UK DNO DUoS Charging Methodology - Manual Download Helper \033[0m"
    )
    print("\033[1;34m" + "=" * 80 + "\033[0m")
    print()


def show_menu():
    """Display the main menu"""
    clear_screen()
    show_banner()

    print("Select a DNO to download files from:")
    print()
    print("  1. SP Manweb (MPAN 13) - Scottish Power")
    print(
        "  2. National Grid Electricity Distribution (MPAN 11, 14, 21, 22) - formerly WPD"
    )
    print("  3. SSEN (MPAN 17, 20) - Scottish and Southern")
    print("  4. UKPN (MPAN 10, 12, 19) - UK Power Networks")
    print("  5. NPG (MPAN 15, 23) - Northern Powergrid")
    print("  6. ENWL (MPAN 16) - Electricity North West")
    print()
    print("  0. Exit")
    print()

    choice = input("Enter your choice (0-6): ")
    return choice


def handle_sp_manweb():
    """Help download SP Manweb files"""
    clear_screen()
    show_banner()

    print("SP Manweb (MPAN 13) - Scotland Power Files")
    print("-" * 50)
    print()
    print("Opening the Scottish Power website in your browser...")
    print("Please manually download the required files from the SP Manweb section.")
    print()
    print("Instructions:")
    print("1. Navigate to the 'SP Manweb' section")
    print("2. Select the appropriate year (2025, 2026)")
    print("3. Download the following files:")
    print("   - LC14 Charging Statement")
    print("   - Schedule of Charges and Other Tables")
    print("   - CDCM Model")
    print("   - CDCM Annual Review Pack (if needed)")
    print()

    input("Press Enter to open the website in your browser...")

    webbrowser.open(
        "http://www.scottishpower.com/pages/connections_use_of_system_and_metering_services.asp"
    )

    print()
    input("Press Enter to return to the main menu...")


def handle_nged():
    """Help download National Grid files"""
    clear_screen()
    show_banner()

    print("National Grid Electricity Distribution - formerly WPD")
    print("-" * 50)
    print()
    print("Opening the National Grid website in your browser...")
    print("Please manually navigate to find and download the required files.")
    print()
    print("Instructions:")
    print("1. Navigate to the document library")
    print("2. Search for 'Schedule of Charges' or 'CDCM Model'")
    print("3. Filter by region (East Midlands, West Midlands, South Wales, South West)")
    print("4. Download files for each region:")
    print("   - Schedule of Charges and Other Tables")
    print("   - CDCM Model")
    print()

    input("Press Enter to open the website in your browser...")

    webbrowser.open("https://www.nationalgrid.co.uk/electricity-distribution/")

    print()
    input("Press Enter to return to the main menu...")


def handle_ssen():
    """Help download SSEN files"""
    clear_screen()
    show_banner()

    print("SSEN - Scottish and Southern Electricity Networks")
    print("-" * 50)
    print()
    print("Opening the SSEN website in your browser...")
    print("Please manually navigate to find and download the required files.")
    print()
    print("Instructions:")
    print("1. Navigate to the 'Use of System Charging' section")
    print("2. Filter by region (SHEPD or SEPD)")
    print("3. Download the appropriate files:")
    print("   - Statement of Charges")
    print("   - CDCM Models")
    print()

    input("Press Enter to open the website in your browser...")

    webbrowser.open(
        "https://www.ssen.co.uk/our-services/use-of-system-and-connection-charging/"
    )

    print()
    input("Press Enter to return to the main menu...")


def handle_ukpn():
    """Help download UKPN files"""
    clear_screen()
    show_banner()

    print("UKPN - UK Power Networks")
    print("-" * 50)
    print()
    print("Opening the UKPN website in your browser...")
    print("Please manually navigate to find and download the required files.")
    print()

    input("Press Enter to open the website in your browser...")

    webbrowser.open("https://www.ukpowernetworks.co.uk/internet/en/about-us/duos/")

    print()
    input("Press Enter to return to the main menu...")


def handle_npg():
    """Help download NPG files"""
    clear_screen()
    show_banner()

    print("NPG - Northern Powergrid")
    print("-" * 50)
    print()
    print("Opening the NPG website in your browser...")
    print("Please manually navigate to find and download the required files.")
    print()

    input("Press Enter to open the website in your browser...")

    webbrowser.open("https://www.northernpowergrid.com/use-of-system-charges")

    print()
    input("Press Enter to return to the main menu...")


def handle_enwl():
    """Help download ENWL files"""
    clear_screen()
    show_banner()

    print("ENWL - Electricity North West")
    print("-" * 50)
    print()
    print("Opening the ENWL website in your browser...")
    print("Please manually navigate to find and download the required files.")
    print()

    input("Press Enter to open the website in your browser...")

    webbrowser.open(
        "https://www.enwl.co.uk/get-connected/connection-charges/duos-charges/"
    )

    print()
    input("Press Enter to return to the main menu...")


def main():
    """Main function"""
    while True:
        choice = show_menu()

        if choice == "0":
            clear_screen()
            print("Thank you for using the Manual DNO Download Helper!")
            print("Exiting...")
            sys.exit(0)
        elif choice == "1":
            handle_sp_manweb()
        elif choice == "2":
            handle_nged()
        elif choice == "3":
            handle_ssen()
        elif choice == "4":
            handle_ukpn()
        elif choice == "5":
            handle_npg()
        elif choice == "6":
            handle_enwl()
        else:
            print("\nInvalid choice. Please try again.")
            time.sleep(1)


if __name__ == "__main__":
    main()
