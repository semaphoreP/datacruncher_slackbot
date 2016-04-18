from slackclient import SlackClient
import configparser

# Read in configuration from config.ini
# Note that config.ini should never be versioned on git!!!
config = configparser.ConfigParser()
config.read("config.ini")
username = config['DEFAULT']['username']
token = config['DEFAULT']['token']