# websiteBot

## Introduction
This is a bot written in Python3 which monitors a given website for changes using a home-made from-scratch implementation of a ```diff```-like difference tracker.
Upon detecting changes, it sends a message via the Telegram bot ```@websiteBot_bot``` to any people who subscribed to the pertinent websites.

## Caveats
This bot can only track websites that do not need a login and it cannot interact with the websites in any way.
Due to the nature of what this bot does, only the admins have the capability to add new websites to the tracking list.
Furthermore, this bot is currently invitation-only after application (start the bot and let it guide you - see below under "use").

## Use / Installation
#### If you want to use this one:
- Start a chat with ```@websiteBot_bot``` on Telegram.
- The bot will guide you on how to proceed (you will have to apply to use it).
- Receive notifications about the available websites which you subscribe to.

#### If you want to start your own instance of this bot:
- Download this repository and install its dependencies.
- Make sure you have PostgreSQL and Azure Data Studio (technically optional but recommended) installed on your system.
- The bot can monitor whether a VPN connection is active (only to NordVPN) if you want to hide your IP address while running this bot. For this you will need the NordVPN app or Openvpn client.
- Make a bot using the official Telegram bot ```@BotFather```. The name of your bot obviously needs to be different from this one.
- Insert the token you received from this bot and your own Telegram user id number into the relevant code cells of the ```db_setup.ipynb``` file (preferably using Azure Data Studio).
- Follow the instructions in the ```db_setup.ipynb``` file to to create the bot's database (preferably using Azure Data Studio).
- Either execute ```main_driver.py``` directly using Python3 or add the ```websiteBot.sh``` script as a service (only on Linux) and start a chat with your bot on Telegram.
- The bot will guide you on how to proceed (you should see a lot more options as you are now the admin of the bot).
- Receive notifications about the websites which you subscribe to and maintain the bot.

## Dependencies
- ```python-telegram-bot``` - for interaction with the bot using Telegram
- ```psycopg2``` - for interaction with the bot's PostgreSQL database
- ```requests``` - for requesting and downloading the websites
- ```html2text``` - for converting HTML to text during processing
- ```unidecode``` - for stripping special characters during processing
- ```sdnotify``` - for interacting with systemctl (only on Linux)
