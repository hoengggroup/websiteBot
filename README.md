# websiteBot

## Introduction
This is a bot written in Python3 which monitors a given website for changes using an efficient 𝒪(𝑛²) from-scratch implementation of a ```diff```-like difference tracker.
Upon detecting changes, it sends a message via the Telegram bot ```@websiteBot_bot``` to any people who subscribed to the pertinent websites.

## Caveats
This bot can only track websites that do not need a login and it cannot interact with the websites in any way.

Your mileage may also vary with non-English (especially non-Latin-script) websites, as the difference tracker was only designed for this character set.

Due to the nature of what this bot does, only the admins have the capability to add new websites to the tracking list.

Furthermore, this bot is currently invitation-only after application (start the bot and let it guide you - see below under "use").

## Use / Installation
#### If you want to use this one:
- Start a chat with ```@websiteBot_bot``` on Telegram.
- The bot will guide you on how to proceed (you will have to apply to use it).
- Receive notifications about the available websites which you subscribe to.

#### If you want to start your own instance of this bot:
- Download this repository and install its dependencies (see below).
- Make sure you have PostgreSQL and Azure Data Studio (technically optional but recommended) installed on your system.
- The bot can monitor whether a VPN connection is active (only to NordVPN) if you want to hide your IP address while running this bot. For this you will need the NordVPN app or Openvpn client.
- Make a bot using the official Telegram bot ```@BotFather```. The name of your bot obviously needs to be different from this one.
- Insert the token you received from ```@BotFather``` and your own Telegram user id number into the relevant code cells of the ```db_setup.ipynb``` file (preferably using Azure Data Studio).
- Follow the instructions in the ```db_setup.ipynb``` file to to create the bot's database (preferably using Azure Data Studio).
- Either execute ```main_driver.py``` directly using Python3 or add the ```websiteBot.sh``` script as a service (only on Linux; familiarize yourself with its contents first!) and start a chat with your bot on Telegram.
- The bot will guide you on how to proceed (you should see a lot more options as you are now the admin of the bot).
- Receive notifications about the websites which you subscribe to and maintain the bot.

## Dependencies & Attributions
| Library                   | Use in project                                      | Links                                                        | License    | Attribution                                                  |
| ------------------------- | --------------------------------------------------- | ------------------------------------------------------------ | ---------- | ------------------------------------------------------------ |
| ```python-telegram-bot``` | interaction with the Telegram API                   | [Homepage](https://python-telegram-bot.org/), [pypi](https://pypi.org/project/python-telegram-bot/), [GitHub](https://github.com/python-telegram-bot/python-telegram-bot) | LGPLv3     | [AUTHORS.rst](https://github.com/python-telegram-bot/python-telegram-bot/blob/master/AUTHORS.rst) |
| ```psycopg```             | interaction with the bot's PostgreSQL database      | [Homepage](https://www.psycopg.org/), [pypi](https://pypi.org/project/psycopg/), [GitHub](https://github.com/psycopg/psycopg) | LGPLv3     | Daniele Varrazzo, The Psycopg Team                           |
| ```requests```            | networking / downloading websites                   | [Homepage](https://requests.readthedocs.io/en/latest/), [pypi](https://pypi.org/project/requests/), [GitHub](https://github.com/psf/requests) | Apache 2.0 | [AUTHORS.rst](https://github.com/psf/requests/blob/main/AUTHORS.rst) |
| ```html2text```           | converting HTML to markdown for improved processing | [Homepage](https://alir3z4.github.io/html2text/), [pypi](https://pypi.org/project/html2text/), [GitHub](https://github.com/Alir3z4/html2text/) | GPLv3      | [AUTHORS.rst](https://github.com/Alir3z4/html2text/blob/master/AUTHORS.rst) |
| ```unidecode```           | stripping non-ASCII characters during processing    | [pypi](https://pypi.org/project/Unidecode/), [GitHub](https://github.com/avian2/unidecode) | GPLv2+     | [Copyright](https://github.com/avian2/unidecode#copyright)   |
| ```sdnotify```            | interacting with ```systemctl``` (only on Linux)    | [pypi](https://pypi.org/project/sdnotify/), [GitHub](https://github.com/bb4242/sdnotify) | MIT        | [Brett Bethke](https://github.com/bb4242), [Daniel M. Weeks](https://github.com/doctaweeks), [David Lechner](https://github.com/dlech) |

*We do not claim any affiliation with the projects listed above and also do not have any influence on the content of the linked websites. The entries listed in the columns "Links", "License", and "Attribution" were last checked for validity on 2022-05-26. This list is provided in good faith.*

## Copyright

**This project is currently licensed under GPLv3 (see [LICENSE](./LICENSE) file). In accordance with the additional section 7b, we require attribution to the authors (us) mentioned in the [AUTHORS.rst](./AUTHORS.rst) file.**

Licensing under GPLv3 is in accordance with the licensing requirements of some of our direct dependencies (which are also licensed under GPLv3; see above). This is to our current knowledge compatible with the more permissive licenses of the other dependencies.

## Contributors

[Tassilo Schwarz](https://github.com/blackTay) - responsible for the "backend" (dp_edit_distance.py)

[Niklas Bogensperger](https://github.com/niklasbogensperger) - responsible for the "frontend" (module_telegram.py)

All other parts of the project are developed by the two of us together, and the repo is owned by our shared GitHub account [hoengggroup](https://github.com/hoengggroup).

