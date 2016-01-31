# discord-twitter-bot
A simple Python-based chat-configurable Discord bot which will live echo a Twitter user's tweets.

The following dependencies are required:

python 3+
discord.py
twython.py

The bot must login to both a Twitter account and a Discord account to function. See the Twitter API for more info on obtaining the appropriate authentication keys.

To setup the bot, run DiscordTwitterBotSetup.py. This will ask you to enter Discord and Twitter authentication information for a one-time setup. The entered information is stored directly into a file named 'data.pkl'. DO NOT ENTER IMPORTANT PERSONAL ACCOUNT INFORMATION HERE. I recommend creating a dummy user to host the bot, and entering its login information.

Once the bot is setup, run DiscordTwitterBot.py. It will use the login information entered in the Setup stage to login as the provided Discord user and Twitter user. To enable the bot in a Discord channel, the bot user must be connected to the channel. Then type "$addchannel @<Bot>" in that channel, replacing "@<Bot>" with a mention to the user. To start following a Twitter user, type "$follow <TwitterUser> @<Bot>", replacing "<TwitterUser>" with the name of the Twitter user you want to follow. Type "$help @<Bot>" to see more commands.

This bot was written very quickly and could use a lot more features and some cleanup. Feel free to contribute changes or report bugs.
