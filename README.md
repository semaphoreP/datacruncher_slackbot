# The GPIES Data Cruncher Slack Bot

This is an automated bot to allow the GPIES Data Cruncher chat on Slack.

### Requirements
  * SlackClient python library
  * Slacker python library
  * astropy, numpy
  * pyephem
  * watchdog

### Setup
You need to make a `config.ini` file that populates the same fields as `config.ini.deafult`. The token can be obtained from Slack. The username requires parsing a chat message received with the Slack API that has @data_cruncher in the message. In the message, @data_cruncher will be replaced with @(some characters) and (some characters) is actually the chat it.

### Running it
Currently, the bot is set up to run with both the real-time `ChatResponder` and the `NewImagerPoster` (which runs when a new PSF subtraction is complete) by just executing the following command.
```
$ python bot.py
```


