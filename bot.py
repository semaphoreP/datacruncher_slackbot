import configparser
import time

from slackclient import SlackClient
from slacker import Slacker


# Read in configuration from config.ini
# Note that config.ini should never be versioned on git!!!
config = configparser.ConfigParser()
config.read("config.ini")
username = config['DEFAULT']['username']
token = config['DEFAULT']['token']
uid = config['DEFAULT']['id']


# client = SlackClient(token)
# print(client.api_call(
#     "chat.postMessage", channel="@jwang", text="Beep. Boop.",
#     username=username, as_user=True))
    
    
# using Slacker as it's file upload interface is much better
client = Slacker(token)
print(client.chat.post_message('@jwang', 'Beep. Boop', username=username, as_user=True).raw)
# print(client.files.upload('tmp.png', channels="@jwang",filename="HD_95086_160229_H_Spec.png", title="HD 95086 2016-02-29 H-Spec" ).raw)

def get_klipped_img_info(request):
    """
    Get the info for a Klipped image that was requested
    
    Args:
        request: a string in the form of "Object Name[, Date[, Band[, Mode]]]"
        
    Returns:
        filename: the full path to the klipped image
        objname: object name (with spaces)
        date: with dashes
        mode: obsmode
    """
    raise NotImplementedError


def craft_response(msg, sender, channel):
    """
    Given some input text from someone, craft this a response
    
    Args:
        msg: some text someone sent to the data cruncher
        sender: ID of sender
        channel: ID of channel
        
    Return:
        
    """
    if msg is None:
        return
        
    msg = msg.strip()
    if (msg.upper()[:4] == "SHOW") | (msg.upper()[:7] == "SHOW ME"):
        # Someone wants us to show them something!!
        reply = 'I received your text of "{0}"!'.format(msg)
        full_reply = '<@{user}>: '.format(user=sender) + reply
        print(sc.api_call("chat.postMessage", channel=channel, text=full_reply, username=username, as_user=True))
         
         
def parse_txt(msg):
    """
    Parse text someone sent to the Data Cruncher

    Args:
        msg: a string that is the text body
        
    Return:
        parsed: parsed text of some sort
    """
    # clear white space
    msg = msg.strip()
    
    # see if it's addressed to you
    if not "<@{id}>".format(id=uid) == msg[:12]:
        return None
        
    # strip off @data_cruncher:
    body = msg[12:] # strip off @data_cruncher
    if body[0] == ":":
        body = body[1:] # strip off : too
    
    parsed = body
    
    return parsed
    
def parse_event(event):
    """
    Parse an event received from Slack
    
    Args:
        event: a dictionary with key/value pairs. Standardized Slack input
    """
    # how do I do what event it is without a type
    if "type" not in event:
        return
    # look for chat messages
    if (event["type"] == "message") & ("text" in event):
        print(event)
        # grab message info
        try:
            msg = event["text"]
            sender = event["user"]
            channel = event["channel"]
        except KeyError as e:
            print("Got a malformed message packet", e)
            return
           
        print("From {0}@{1}: {2}".format(sender, channel, msg))
        msg_parsed = parse_txt(msg)
        craft_response(msg_parsed, sender, channel)
    
# Run real time message slack client 
sc = SlackClient(token)

connected = sc.rtm_connect()

if connected:
    while True:
        events = sc.rtm_read()
        for event in events:
            parse_event(event)
                
        time.sleep(3)
else:
    print("Connection Failed, invalid token?")
     