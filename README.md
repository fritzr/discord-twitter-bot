# discord-twitter-bot
A simple Python-based chat-configurable Discord bot which will live echo a Twitter user's tweets.

## Prerequisites

The following dependencies are required:

python 3.3+  
discord.py (v0.9.2)  
twython (v3.3.0)  
python-dateutil (v2.4.2)  

The last three can be installed with pip or easy_install. Note that the Python Discord API changes frequently and makes little effort to hold backwards-compatibility, so you must use the release listed here (not a later version). An easy way to make sure you get the right version is to explicitly provide it to pip on install: `pip install discord.py==0.9.2`

## Setup

The bot must login to both a Twitter account and a Discord account to function. See the Twitter API for more info on obtaining the appropriate authentication keys. I recommend using a dummy Discord account (for example one named 'Twitter Bot') rather than your personal user account, because this application makes no effort to secure the login credentials you enter. The Twitter account requires 4 application keys which you must set up from your Twitter account according to this webpage: https://dev.twitter.com/oauth/overview/application-owner-access-tokens.

To setup the bot, run DiscordTwitterBotSetup.py. This will ask you to enter Discord and Twitter authentication information for a one-time setup. The entered information is stored directly into a file named 'data.pkl'. *DO NOT ENTER IMPORTANT PERSONAL ACCOUNT INFORMATION HERE*. This information is not secured or protected in any way.

## Usage

After __Setup__, run DiscordTwitterBot.py. It will use the login information entered in the Setup stage to login as the provided Discord user and Twitter user. Once the bot is running, it can be configured via text commands within Discord by any user. All text commands must contain a *@mention* to the Discord user running the bot (shown below as *@Bot* in command samples).

First you must enable the bot in each specific Discord channel in which it should echo tweets. The bot user must be connected to the channel. Then as any Discord user type __$addchannel *@Bot*__ in that channel.

To start following a Twitter user, type __$follow *TwitterUser* *@Bot*__, replacing *TwitterUser* with the name of the Twitter user you want to follow.

To see more commands, enter __$help *@Bot*__.

## Notes

This bot was written very quickly and could use a lot more features and some cleanup. Feel free to contribute changes or report bugs.

## Authors

Fritz Reese  
Rhett Zimmer  

## License

See the LICENSE file.
