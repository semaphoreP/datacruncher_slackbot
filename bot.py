import sys
if sys.version_info < (3,0):
    #python 2.7 behavior
    import ConfigParser as configparser
else:
    import configparser
import time
import threading
from threading import Thread
import re
import os
import requests

from slackclient import SlackClient
from slacker import Slacker

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import display_image
    

# Read in configuration from config.ini
# Note that config.ini should never be versioned on git!!!
config = configparser.ConfigParser()
config.read("config.ini")
username = config.get('DEFAULT','username')
token = config.get('DEFAULT', 'token')
uid = config.get('DEFAULT', 'id')
dropboxdir = os.path.normpath(config.get('DEFAULT', 'dropboxdir'))

class NewImagePoster(FileSystemEventHandler):
    """
    Thread that posts new PSF subtracted images to the Slack Chat
    """
    def __init__(self, dropboxdir, slacker_bot):
        """
        Runs on creation
        
        Args:
            dropboxdir: full path to dropboxdir to scan
            slacker_bot: a Slacker instance
        """
        self.dropboxdir = dropboxdir
        self.newfiles = []
        self.lock = threading.Lock()
        self.slacker = slacker_bot
    
    def get_joke(self):
        """
        Get a joke
        
        Return:
            joke: LOL
        """
        try:
            req = requests.get("http://tambal.azurewebsites.net/joke/random")
            body = req.json()
            joke = body['joke']
        except requests.exceptions.RequestException:
            # Woops, error getting joke
            joke = None
        return joke
        
    
    def process_file(self):
        with self.lock:
            if len(self.newfiles) == 0:
                return
            
            filepath = self.newfiles.pop(0)
            
        # get title and make image after getting new klip file
        title = display_image.get_title_from_filename(filepath)
        display_image.save_klcube_image(filepath, "tmp.png", title=title)
        #print(self.slacker.chat.post_message('@jwang', 'Beep. Boop. {0}'.format(filepath), username=username, as_user=True).raw)
        print(self.slacker.chat.post_message('@jwang', "Beep. Boop. I just finished a PSF Subtraction for {0}. Here's a quicklook image.".format(title), username=username, as_user=True).raw)
        print(self.slacker.files.upload('tmp.png', channels="@jwang",filename="{0}.png".format(title.replace(" ", "_")), title=title ).raw)
        return
    
    
    def process_new_file_event(self, event):
        """
        Handles what events when a new file / file gets modified:
        
        Args:
            event: file system event
        """
        filepath = event.src_path
        print(filepath)
        
        # we are looking for the first PSF subtraction that happens
        if "_Pol" in filepath:
            matches = re.findall(r".*m1-(ADI-)?KLmodes-all\.fits", filepath)
        else:    
            matches = re.findall(r".*m1-KLmodes-all\.fits", filepath)
        # not a PSF subtraction
        if len(matches) <= 0:
            return
            
        # add item to queue
        with self.lock:
            if filepath not in self.newfiles:
                print("appending {0}".format(filepath))
                self.newfiles.append(filepath)

        # wait 3 seconds before processing
        threading.Timer(3., self.process_file).start() 
        
        
    def on_created(self, event):

        """
        watchdog function to run when a new file appears
        """
        self.process_new_file_event(event)

        
    def on_modified(self, event):
        """
        watchdog function to run when an existing file is modified
        """
        self.process_new_file_event(event)
    

class ChatResponder(Thread):
    def __init__(self, dropboxdir, slack_bot, slacker):
        """
        Init
        
        Args:
            dropboxdir: absolute dropbox path
            slack_bot: a SlackClient instance
            slacker: a Slacker instance
        """
        super(ChatResponder, self).__init__()
        self.dropboxdir = dropboxdir
        self.slack_client = slack_bot
        self.slacker = slacker

    def run(self):
        connected = self.slack_client.rtm_connect()
        if connected:
            while True:
                events = self.slack_client.rtm_read()
                for event in events:
                    self.parse_event(event)
                        
                time.sleep(1)
        else:
            print("Connection Failed, invalid token?")
    
    def get_klipped_img_info(self, request):
        """
        Get the info for a Klipped image that was requested
        
        Args:
            request: a string in the form of "Object Name[, Date[, Band[, Mode]]]"
            
        Returns:
            filename: the full path to the klipped image
            objname: object name (with spaces)
            date: with dashes
            band: the band
            mode: obsmode
        """
        request_args = request.split(',')
        
        objname = request_args[0].strip().replace(" ", "_")
   
        # get object name dropbox path
        auto_dirpath = os.path.join(self.dropboxdir, "GPIDATA", objname, "autoreduced")
        # make sure folder exists
        if not os.path.isdir(auto_dirpath):
            return None
       
        date_folders = [fname for fname in os.listdir(auto_dirpath) if os.path.isdir(os.path.join(auto_dirpath, fname))]
        if len(date_folders) == 0:
            # no subdirs, uh oh
            return None

        # check how many args are passed in
        if len(request_args) == 1:
            datefolder = date_folders[0]
        else:
            date = request_args[1]
            if len(request_args) == 2:
                date = request_args[1].strip()
                date_folders = [fname for fname in date_folders if date in fname]
                if len(date_folders) == 0:
                    # date is invalid
                    return None
                datefolder = date_folders[0]
            else:
                band = request_args[2].strip()
                if len(request_args) ==3:
                    dateband = "{0}_{1}".format(date, band)
                    date_folders = [fname for fname in date_folders if date in fname]
                    if len(date_folders) == 0:
                        # date/band is invalid
                        return None
                    datefolder = date_folders[0]
                else:
                    mode = request_args[3].strip()
                    dateband = "{0}_{1}_{2}".format(date, band, mode)
                    date_folders = [fname for fname in date_folders if date in fname]
                    if len(date_folders) == 0:
                        # date/band is invalid
                        return None
                    datefolder = date_folders[0]


        dateband = datefolder.split("_")
        date = dateband[0]
        band = dateband[1]
        mode = dateband[2]
 
        dirpath = os.path.join(auto_dirpath,  "{0}_{1}_{2}".format(date, band, mode))
        if mode == "Spec":
            pyklip_name = "pyklip-S{date}-{band}-k150a9s4m1-KLmodes-all.fits"
        else:
            pyklip_name = "pyklip-S{date}-{band}-pol-k150a9s1m1-ADI-KLmodes-all.fits"
    
        pyklip_name = pyklip_name.format(date=date, band=band)
        
        filename = os.path.join(dirpath, pyklip_name)
        return filename, objname, date, band, mode


    def craft_response(self, msg, sender, channel):
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
            # strip off the "Show (me)?"
            if "SHOW ME" in msg.upper():
                msg = msg[7:]
            else:
                msg = msg[4:]
            msg = msg.strip()
            
            # get requested pyklip reduction by parsing message
            klip_info = self.get_klipped_img_info(msg)
            if klip_info is None:
                reply = "Beep. Boop. I'm sorry, but I couldn't find the data you requested"
            else:
                # found it. Let's get the details of the request
                pyklip_filename, objname, date, band, mode = klip_info
                
                reply = 'Beep. Boop. Retrieving {obj} taken on {date} in {band}-{mode}...'.format(obj=objname, date=date, band=band, mode=mode)
                
                # generate image to upload
                title = display_image.get_title_from_filename(pyklip_filename)
                display_image.save_klcube_image(pyklip_filename, "tmp.png", title=title)
                
            # generate and send reply
            full_reply = '<@{user}>: '.format(user=sender) + reply
            print(self.slack_client.api_call("chat.postMessage", channel=channel, text=full_reply, username=username, as_user=True))
            # upload image
            print(self.slacker.files.upload('tmp.png', channels="@jwang",filename="{0}.png".format(title.replace(" ", "_")), title=title ).raw)
            
    def parse_txt(self, msg):
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
        
    def parse_event(self, event):
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
            msg_parsed = self.parse_txt(msg)
            self.craft_response(msg_parsed, sender, channel)



# client = SlackClient(token)
# print(client.api_call(
#     "chat.postMessage", channel="@jwang", text="Beep. Boop.",
#     username=username, as_user=True))
    
    
# using Slacker as it's file upload interface is much better
client = Slacker(token)
print(client.chat.post_message('@jwang', 'Beep. Boop.', username=username, as_user=True).raw)
# print(client.files.upload('tmp.png', channels="@jwang",filename="HD_95086_160229_H_Spec.png", title="HD 95086 2016-02-29 H-Spec" ).raw)



    
# Run real time message slack client 
sc = SlackClient(token)

p = ChatResponder(dropboxdir, sc, client)
p.daemon = True


# Run real time PSF subtraction updater
print(dropboxdir)
event_handler = NewImagePoster(dropboxdir, client)
observer = Observer()

observer.schedule(event_handler, dropboxdir, recursive=True)
observer.start()


p.start()
while True:
    time.sleep(100)
