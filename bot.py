from slackclient import SlackClient
from slacker import Slacker
import configparser

# Read in configuration from config.ini
# Note that config.ini should never be versioned on git!!!
config = configparser.ConfigParser()
config.read("config.ini")
username = config['DEFAULT']['username']
token = config['DEFAULT']['token']


# client = SlackClient(token)
# print(client.api_call(
#     "chat.postMessage", channel="@jwang", text="Beep. Boop.",
#     username=username, as_user=True))
    

# using Slacker as it's file upload interface is much better
client = Slacker(token)
print(client.chat.post_message('@jwang', 'Beep. Boop', username=username, as_user=True).raw)
print(client.files.upload('tmp.png', channels="@jwang",filename="HD_95086_160229_H_Spec.png", title="HD 95086 2016-02-29 H-Spec" ).raw)

