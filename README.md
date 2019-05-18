# websiteBot

## Introduction
This is a bot written in Python which monitors a given webpage for changes using the Selenium library and a home-made from-scratch implementation of a ```diff```-like difference tracker.
Upon detecting changes, it sends a message via the Telegram bot ```@websiteBot_bot``` to any people who subscribed to the pertinent webpages.

## Use / Installation
#### If you want to use this one:
- Start a chat with ```@websiteBot_bot``` on Telegram.
- The bot will guide you on how to proceed.
- Receive notifications about the available webpages which you subscribe to.

#### If you want to start your own instance of this bot:
- Download this repository and its dependencies.
- Make a bot using the official Telegram bot ```@BotFather``` and change any "token" variable in the code to the token you received from this bot. The name of your bot obviously needs to be different from this one.
- Add the webpages you want to track to the code.
- Execute ```main_driver.py``` and start a chat with your bot on Telegram.
- The bot will guide you on how to proceed.
- Receive notifications about the available webpages which you subscribe to.

## Dependencies
- ```selenium``` (for website interaction)
- A browser driver executable of your choice: (for use by selenium)
    - ```geckodriver``` for Firefox
    - ```chromedriver``` for Chrome
- ```pickle``` (for saving and loading webpage and chat-ID lists)
- ```python-telegram-bot``` (for interaction with the bot using Telegram)
