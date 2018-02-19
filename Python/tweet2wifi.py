#!/usr/bin/python

import os
import time
import json
import string
import random
import signal
import twitter
import threading
import subprocess

from tweepy import Stream
from datetime import datetime
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

DISALLOWED = []

API_CONSUMER_KEY = ''
API_CONSUMER_SECRET = ''
API_ACCESS_KEY = ''
API_ACCESS_SECRET = ''


class TweetNetwork(object):
    network_user = None
    network_name = None
    network_process = None
    network_creation = None

    def __init__(self, name, user):
        self.network_name = name
        self.network_user = user
        self.network_process = subprocess.Popen(['sudo', '/opt/t2w/bin/t2w-addnet', name,
                                                 TweetNetwork.random_hex_value(26)],
                                                stdout=subprocess.PIPE, preexec_fn=os.setsid)
        self.network_creation = datetime.now()

    def stop(self):
        subprocess.Popen(['sudo', '/opt/t2w/bin/t2w-remnet', '%d' % self.network_process.pid])

    def timeout(self):
        return (datetime.now() - self.network_creation).seconds >= 120

    @staticmethod
    def random_hex_value(len):
        strd = []
        for x in range(0, len):
            strd.append(chr(48 + random.randint(0, 9)))
        return ''.join(strd)


class TweetWatcher(StreamListener):
    watcher_host = None

    def __init__(self, host):
        self.watcher_host = host

    def on_data(self, data):
        tweet_data = json.loads(data)
        try:
            self.handle_tweet(tweet_data['text'], tweet_data['user']['screen_name'], int(tweet_data['user']['id']))
        except:
            self.watcher_host.log('Error handeling tweet! %s' % str(tweet_data))
        return True

    def on_error(self, data):
        return True

    def handle_tweet(self, tweet, user, userid):
        tweet_text = tweet.replace('@tweet2wifi', '').replace('@TWEET2WIFI', '').replace('@tweet2WiFi', '') \
            .replace('\n', '').strip()
        tweet_text = ''.join([i if ord(i) < 128 else ' ' for i in tweet_text])
        self.watcher_host.log('Got tweet.... [%s]' % tweet_text)
        if len(tweet_text) > 32:
            tweet_text = tweet_text[:32]
        tweet_text_lower = tweet_text.lower()
        for ssid in self.watcher_host.t2w_nets_scanned:
            if ssid.lower() == tweet_text_lower:
                self.watcher_host.t2w_api.PostUpdate('@%s SSID already esists, please try again. --%d'
                                                     % (user, random.randint(0, 99999)))
                return False
        for check in DISALLOWED:
            if check[0] == 0 and check[1].lower() == tweet_text_lower:
                self.watcher_host.t2w_api.PostUpdate('@%s Incorrect Text, please try again. --%d'
                                                     % (user, random.randint(0, 99999)))
                return False
            if check[0] == 1 and check[1].lower() in tweet_text_lower:
                self.watcher_host.t2w_api.PostUpdate('@%s Incorrect Text, please try again. --%d'
                                                     % (user, random.randint(0, 99999)))
                return False
        if len(self.watcher_host.t2w_nets_active) < 50:
            if self.does_user_have_message(userid):
                self.watcher_host.t2w_api.PostUpdate('@%s You have a current deployed Message, '
                                                     'please wait until it expires. --%d'
                                                     % (user, random.randint(0, 99999)))
                return False
            self.watcher_host.t2w_nets_active.append(TweetNetwork(tweet_text, userid))
            self.watcher_host.t2w_api.PostUpdate('@%s Created. Active for 2 mins. Thanks for using Tweet2WiFi! --%d' %
                                                 (user, random.randint(0, 99999)))
            return True
        self.watcher_host.t2w_api.PostUpdate('@%s Max Messages Reached, please try again later. --%d' %
                                             (user, random.randint(0, 99999)))
        return False

    def does_user_have_message(self, user):
        for net in self.watcher_host.t2w_nets_active:
            if int(net.network_user) == int(user):
                return True
        return False


class TweetScanner(threading.Thread):
    scanner_host = None

    def __init__(self, host):
        threading.Thread.__init__(self)
        self.scanner_host = host

    def run(self):
        while True:
            scan_proc = subprocess.Popen('sudo iw tw1 scan | grep SSID', shell=True, stdout=subprocess.PIPE)
            while scan_proc.poll() is None:
                pass
            scan_ssids = []
            while True:
                scan_text = scan_proc.stdout.readline()
                if len(scan_text) <= 0:
                    break

                ssid_new = scan_text.decode('UTF-8','ignore').replace('\t', '').replace('\n', '').replace('SSID: ', '')
                if len(ssid_new) >= 1:
                    scan_ssids.append(ssid_new)
            self.scanner_host.log('Found hosts %s' % str(scan_ssids))
            self.scanner_host.t2w_nets_scanned = scan_ssids
            time.sleep(5)


class Tweet2WiFi(threading.Thread):
    LOG_FILE = '/opt/t2w/logs/main.log'

    t2w_api = None
    t2w_logger = None
    t2w_stream = None
    t2w_watcher = None
    t2w_scanner = None
    t2w_nets_active = None
    t2w_nets_scanned = None

    def __init__(self):
        threading.Thread.__init__(self)
        self.t2w_nets_active = []
        self.t2w_nets_scanned = []
        self.t2w_nets_finished = []
        self.t2w_logger = open(Tweet2WiFi.LOG_FILE, 'a')
        self.t2w_api = twitter.Api(consumer_key=API_CONSUMER_KEY, consumer_secret=API_CONSUMER_SECRET,
                                   access_token_key=API_ACCESS_KEY, access_token_secret=API_ACCESS_SECRET)
        self.t2w_watcher = TweetWatcher(self)
        self.t2w_scanner = TweetScanner(self)
        self.t2w_scanner.start()
        self.start()
        t2w_auth = OAuthHandler(API_CONSUMER_KEY, API_CONSUMER_SECRET)
        t2w_auth.set_access_token(API_ACCESS_KEY, API_ACCESS_SECRET)
        self.t2w_stream = Stream(t2w_auth, self.t2w_watcher)
        self.t2w_stream.filter(track=["@tweet2wifi"])

    def run(self):
        self.log('Tweet2WiFi starting....')
        while True:
            for net in self.t2w_nets_active:
                if net.timeout():
                    net.stop()
                    self.t2w_nets_active.remove(net)
                    del (net)
            time.sleep(1)

    def log(self, log_data):
        if self.t2w_logger:
            try:
                self.t2w_logger.write('%s:: %s\n' % (datetime.now().strftime('%m-%d-%y %H:%M:%S'), log_data))
                self.t2w_logger.flush()
            except:
                pass


if __name__ == '__main__':
    Tweet2WiFi()
