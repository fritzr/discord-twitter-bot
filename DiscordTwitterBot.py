## Discord Twitter Bot

import discord
import pickle
import time
import threading

from datetime import datetime
from dateutil import tz
from twython import Twython, TwythonStreamer
from twython.exceptions import TwythonError

## Data Storage
class Storage:
    def __init__(self):
        with open('data.pkl','rb') as self.tinfo:
            self.dct = pickle.load(self.tinfo)
            self.d_email = self.dct['d_email']
            self.d_pass = self.dct['d_pass']
            self.akey = self.dct['akey']
            self.asecret = self.dct['asecret']
            self.otoken = self.dct['otoken']
            self.osecret = self.dct['osecret']
            
            self.twitter = (self.akey, self.asecret, self.otoken, self.osecret)
            self.discord = (self.d_email, self.d_pass)

def _bisect_left(a, x, lo=0, hi=None, key=None, cmp=None):
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(x) will
    insert just before the leftmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.

    If key is given, use key(x) instead of x, and key(e) for each e in a when
    determining ordering.

    If cmp is given, use cmp(x, y) instead of 'x < y' in the comparison check
    done between every pair of elements x, y in a.
    """
    def ident(x): return x
    if key is None: key = ident
    def compare(x, y): return x < y
    if cmp is None: cmp = compare

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)//2
        if cmp(key(a[mid]), key(x)): lo = mid+1
        else: hi = mid
    return lo

class TwitterUserStream(TwythonStreamer):
    """Stream tweets from a user's Twitter feed. Whenever a tweet is
received on the stream, each function in callbacks will be called with the
Twitter response data as the argument.

Note that the Twitter API may deliver messages out of order and may deliver repeat
messages. Use the 'show_dupes' property to control whether duplicate messages are
reported to the callbacks. The 'store' property controls how many of the most
recent messages to store."""
    def __init__(self, user=None, callbacks=[], show_dupes=False, store=10):
        self.data = Storage()
        super(TwitterUserStream, self).__init__(*self.data.twitter)
        self.twitter = Twython(*self.data.twitter)

        self.error = "" # text of last error
        self._errors = 0
        self._max_errors = 5
        self._show_dupes = show_dupes
        self._follow = user
        self._lastn = list()
        self._store = store  # max size of _lastn
        self._callbacks = list()
        self.add_all(callbacks)

    def __getattr__(self, attr):
        if attr == 'show_dupes':
            return self._show_dupes
        elif attr == 'store':
            return self._store
        raise AttributeError

    def __setattr__(self, attr, value):
        # show_dupes (bool): whether to report duplicate messages to the callbacks
        if attr == 'show_dupes':
            self._show_dupes = bool(value)

        # store (int): how many tweets to store
        elif attr == 'store':
            if isinstance(value, int):
                # clamp to 0
                if value < 0:
                    value = 0
                # truncate stored messages if we are reducing the count
                if value < self._store:
                    self._lastn = self._lastn[:value]
                self._store = value
            else:
                raise TypeError("type of argument 'store' must be integral")
        else:
             super(TwitterUserStream, self).__setattr__(attr, value)

    # Format of the 'created_at' timestamp returned from Twitter
    # E.g. 'Wed Jan 20 06:35:02 +0000 2016'
    TIME_FMT = """%a %b %d %H:%M:%S %z %Y"""
    @staticmethod
    def timeof(tweet):
        """Return the 'created_at' time for the given tween as a datetime object."""
        return datetime.strptime(tweet['created_at'], TwitterUserStream.TIME_FMT)

    def _remember(self, tweet):
        """Remember a new tweet, dropping the oldest one if we have reached our
limit on 'store'. Keeps tweets in chronological order. See latest()."""
        if len(self._lastn) >= self.store:
            self._lastn.pop(0)
        # Maintain chronological sorting on insertion (using binary search)
        i = _bisect_left(self._lastn, tweet, key=self.timeof)
        self._lastn.insert(i, tweet)

    def latest(self):
        """Return the last several tweets by the last-followed user, in order of
actual occurrence time. The number of messages stored is limited by the 'store'
property."""
        return iter(self._lastn)

    def last(self):
        """Return the last tweet which was received. Only valid if 'store' is
greater than zero. Otherwise returns an empty dictionary."""
        if len(self._lastn) > 0:
            return self._lastn[-1]
        else:
            return dict()

    def stored(self):
        """Return the number of tweets currently stored in latest()."""
        return len(self._lastn)

    def follow_thread(self, *args, **kwargs):
        """Convenient wrapper for calling follow() in a background thread.
The Thread object is started and then returned. Passes on args and kwargs to
the follow() method."""
        thread = threading.Thread(target=self.follow, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread

    def get_user(self, user):
        """Return the user ID of a Twitter user as a string given his screen name,
or None if the user is invalid."""
        try:
            result = self.twitter.get("users/show", params={'screen_name':user})
            return result['id_str']
        except TwythonError as e:
            self.on_error(e.error_code, e.msg)
        return None
    
    def follow(self, user=None, get_last=True):
        """Start streaming tweents from a user. This method will block basically
forever, so running it in a Thread is a good idea.
If user is None, use the user given on construction.
If get_last is True, fetch the user's last tweets before streaming. The number
of tweets prefetched depends on the 'store' property. Note that any registered
callbacks will NOT be called on these pre-existing tweets. Use latest() to see the
prefetched tweets."""
        user = user or self.follow_user
        if user is None:
            print('No user specified.')
            return False

        # Fetch the ID of the user by screen name
        uid = self.get_user(user)

        # Fill up the last 'store' tweets if get_last is set
        if get_last:
            result = self.twitter.get("statuses/user_timeline",
                params={'user_id':uid, 'count':str(self.store)})
            # Results are returned in reverse-chronological order
            result.reverse()
            self._lastn.extend(result)

        # Follow the given user
        self.statuses.filter(follow=uid)
        return True

    def add(self, callback):
        """Register a function to be called when tweets are received.
Returns the TwitterUserStream object.

Example:
  t = TwitterUserStream(...)
  t.add(myfunc).follow("Bob")
"""
        self._callbacks.append(callback)
        return self

    def add_all(self, callbacks):
        """Register several functions to be called when tweets are received.
Returns the TwitterUserStream object.

Example:
  t = TwitterUserStream(...)
  t.add_all([myfunc1, myfunc2]).follow("Bob")
"""
        self._callbacks.extend(callbacks)

    def remove(self, callback):
        """Unregister the function if it is currently a callback.
Returns the TwitterUserStream object."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def remove_all(self, callbacks):
        """Unregister several functions if they are registered.
Returns the TwitterUserStream object."""
        for callback in callbacks:
            self.remove(callback)

    def _filter_tweet(self, data):
        """Return True if the given tweet should be passed on to the callbacks,
False otherwise."""
        # If we don't have an ID, this isn't valid
        if 'id_str' not in data:
            return False

        # Ignore replies, quotes, and retweets
        if (data.get('in_reply_to_status_id_str')
                or data.get('quoted_statis_id_str')
                or data.get('retweeted_status')):
            return False

        # If show_dupes is off, ignore duplicate tweets
        if not self.show_dupes:
            for tweet in self._lastn:
                if data['id_str'] == tweet['id_str']:
                    return
        
        return True
        
    def on_success(self, data):
        """Called by TwythonStreamer when a message is received on the
underlying stream. Dispatches the message to all registered callbacks (in the
order they were registered) if the message is not a duplicate or show_dupes is
enabled."""
        print("received data:", data)

        # Make sure this is a tweet we are interested in
        if not self._filter_tweet(data):
            return

        # Remember this message - if we reach our store limit, pop the oldest
        self._remember(data)

        # Notify callbacks
        for callback in self._callbacks:
            callback(data)
            
    def on_error(self, code, data):
        """Called when there is an error. Disconnects from the stream after
receiving too many errors. Sets the 'error' attribute to an appropriate error
message."""
        errmsg = ("Twitter Error: [{0}] {1}".format(code, data))
        print(errmsg)
        self.error = errmsg
        self._errors += 1
        if self._errors >= self._max_errors:
            print("Maximum number of errors exceeded, disconnecting...")
            self.disconnect()


class TwitterBot(discord.Client):
    def __init__(self, tuser=None):
        """Connect to the built-in Discord server and stream messages
        from the given Twitter user to the given channel."""
        super(TwitterBot, self).__init__()
        # Register on_message to run as a discord event
        self.tuser = tuser
        self.channels = list() # channels to push updates to
        self.mentions = dict() # users to mention keyed by channel name
        self.ntweets = 0
        self.stream = None
        self.stream_thread = None
        self.pre = 'TwitterBot: ' # message preamble

        # Auto login
        self.data = Storage()
        self.login(*self.data.discord)

    @staticmethod
    def make_mentions(mention_list):
        mstr = " "
        for user in mention_list:
            mstr += user.mention() + " "
        return mstr
    
    def send_all(self, message, mention=False):
        """Send a message to all active channels."""
        mention_str = ""
        for chan in self.channels:
            if mention:
                mention = self.mentions.get(chan.id, [])
                mention_str = self.make_mentions(mention)
            self.send_message(chan, message + mention_str, mention)
            
    def halp(self):
        """Send the clients the usage."""
        return ("""To issue commmands to **TwitterBot**, type a message containing
one of the commands below, and mention the *{0}* user.
Examples: "$help @{0}", "@{0} $info", "hey @{0} show $top 3"
  **$help**   Show this help.
  **$info**   Display some info such as following, number of tweets, etc...
  **$last**   Display the last tweet from the current following.
  **$top <n>**   Display the last N tweets (up to 10).
  **$quit**   Kill the TwitterBot.
  **$follow <user>**   Follow a Twitter user's feed (e.g. "$follow WarframeAlerts")
  **$addchannel**   Register the current channel to receive TwitterBot updates.
  **$rmchannel**   Remove the current channel from the channel list for updates.
  **$mention**   Mention me when a tweet is announced.
  **$nomention**   Do not mention me when a tweet is announced.
""".format(self.user.name))

    def info(self, channel=None):
        """Send the clients some misc info. Only shows channels on the same server
as the given channel. If channel is None, show active channels from all servers."""
        # Get time of last message from following user
        last_time = 'Never'
        if self.stream and self.stream.last():
            last_time = TwitterBot.totime(self.stream.last())

        # Get the active channels on the same server as the request
        ccount = 0
        cstr = ""
        for c in self.channels:
            if channel is None or c.server == channel.server:
                ccount += 1
                cstr += "#" + c.name + ", "
        if cstr:
            cstr = cstr[:-2] # strip extra comma

        # List the user mentions for the current channel
        mstr = ""
        if channel is not None:
            for u in self.mentions.get(channel.id, ()):
                mstr += "@" + u.name + ", "
        if mstr:
            mstr = mstr[:-2] # strip extra comma
        
        return ("**TwitterBot**\n"+
                "Currently following: @" + (self.tuser or "None") + "\n" +
                "Tweets streamed: " + str(self.ntweets) + "\n" +
                "Last tweet from user: " + last_time + "\n" +
                "Active channels on server: (" + str(ccount) + ") " + cstr + "\n" +
                "Mentions in this channel: " + mstr)
        
    def on_message(self, message):
        lcontent = message.content.strip().lower()

        # Only read commands from other users on the current channel
        if message.author.id == self.user.id:
            return
        # Only read commands that we are mentioned in
        elif self.user.id not in [u.id for u in message.mentions]:
            return
        # Only read commands from channels we are active in
        elif message.channel.id not in [c.id for c in self.channels]:
            if '$addchannel' not in lcontent:
                return

        ## Parse commands in current channel

        # $help - print help
        if '$help' in lcontent:
            self.send_message(message.channel, self.halp(), False)

        # $info - dump some misc info
        elif '$info' in lcontent:
            self.send_message(message.channel, self.info(message.channel), False)

        # $last - show last tweet
        elif '$last' in lcontent:
            old_count = self.ntweets
            if self.stream.last():
                self.tweet(self.stream.last(), True, False)
            else:
                self.send_message(message.channel, self.pre+"No tweet to display.")
            self.ntweets = old_count # not actually a new tweet

        # $top <N> - show last N tweets
        elif '$top' in lcontent:
            latest = list(self.stream.latest())

            # Get count argument
            count = self.stream.store
            lsplit = lcontent.split()
            ind = lsplit.index('$top')
            if len(lsplit) > ind and ind >= 0:
                try:
                    count = int(lsplit[ind+1])
                except ValueError:
                    self.send_message(message.channel,
                                      self.pre+"Invalid $top count, defaulting to "
                                      +str(count)+".")
            # Hard limits on count
            if count < 1:
                return
            elif count > self.stream.store:
                count = self.stream.store
                
            old_count = self.ntweets
            for tweet in latest[-count:]:
                self.tweet(tweet, True, False)
            self.ntweets = old_count # don't add to tweet count

        # $follow <user> - switch to following a new Twitter user
        elif '$follow' in lcontent:
            # e.g. "$follow user"
            lsplit = lcontent.split()
            ind = lsplit.index('$follow')
            if len(lsplit) > ind and ind >= 0:
                tuser = message.content.split()[ind+1]
                self.stream.disconnect()
                self.follow(tuser, message.channel)

        # $addchannel - add new channel to receive tweets
        elif '$addchannel' in lcontent:
            self.channels.append(message.channel)
            self.send_message(message.channel, self.pre+"Channel now active.")

        # $rmchannel - remove channel from receiving tweets
        elif '$rmchannel' in lcontent:
            ind = self.channels.index(message.channel)
            if ind >= 0:
                del self.channels[ind]
                self.send_message(message.channel, self.pre+"Channel removed.")

        # $mention - register user to be mentioned on receiving tweets
        elif '$mention' in lcontent:
            if message.channel.id not in self.mentions:
                self.mentions[message.channel.id] = list()
            self.mentions[message.channel.id].append(message.author)
            self.send_message(message.channel,
                self.pre+"You WILL be @mentioned when tweets are received.")

        # $nomention - remove user from mention list per channel
        elif '$nomention' in lcontent:
            if message.channel.id in self.mentions:
                self.mentions[message.channel.id].remove(message.author)
                self.send_message(message.channel,
                    self.pre+"You will NOT be @mentioned when tweets are received.")

        elif '$resend' in lcontent:
            self.tweet(self.stream.last())

        # $quit - kill the bot
        elif '$quit' in lcontent:
            self.end()

    def on_ready(self):
        """Called when connected as a Discord client. Sets up the TwitterUserStream
and starts following a user if one was set upon construction."""
        print("Connected.")
        # Setup twitter stream
        self.stream = TwitterUserStream()
        self.stream.add(self.tweet)
        if self.tuser:
            self.follow(self.tuser)

    def follow(self, tuser, src_channel=None):
        """Start streaming tweets from the Twitter user by the given name.
Returns False if the user does not exist, True otherwise."""
        # Make sure the user is valid
        if self.stream.get_user(tuser) is None:
            if src_channel is not None:
                self.send_message(src_channel, self.pre+self.stream.error)
            return False
            
        # Stop previous thread, if any
        if self.stream_thread:
            self.stream.disconnect()
            self.stream_thread.join()
            
        # Setup new thread to run the twitter stream in background
        self.tuser = tuser
        self.ntweets = 0
        self.stream_thread = self.stream.follow_thread(tuser)
        self.send_all(self.pre+"Now following @"+self.tuser+".")
        return True

    TIME_FMT = """%a %b %d %H:%M:%S %Y"""
    @staticmethod
    def totime(data):
        dt = TwitterUserStream.timeof(data)
        utc = dt.replace(tzinfo=tz.tzutc())
        local = utc.astimezone(tz.tzlocal())
        return local.strftime(TwitterBot.TIME_FMT)
        
    def tweet(self, data, timestamp=False, mention=True):
        """Display a tweet to the current channel. Increments ntweets."""
        text = data and data.get('text')
        if text:
            self.ntweets += 1
            msg = self.pre + "*@"+self.tuser+"* "
            if timestamp:
                msg += TwitterBot.totime(data) + '\n  '
            msg += text
            self.send_all(msg, mention)

    def end(self):
        """Terminate the Twitter and Discord connections and exits the program."""
        self.send_all(self.pre+"Logging out.")
        self.logout()
        if self.stream_thread:
            self.stream.disconnect()
            self.stream_thread.join() # still blocks for a long time
        print("Done.")
        exit()

def dump(data):
    print(data)

def test():
    s = Storage()
    t = TwitterUserStream()
    thread = t.add(dump).follow_thread("WarframeAlerts")
    print("** Following @WarframeAlerts.")

    # Wait for prefetch
    while t.stored() < t.store:
        pass

    # Dump prefetched statuses
    print("** Last", t.store, "tweets:")
    for tweet in t.latest():
        print(tweet['created_at'], tweet['text'])

    # Collect the background thread
    thread.join()
    print("** Done.")

def main():
    t = TwitterBot()
    t.run()

## Initialization
if __name__ == '__main__':
    main()
