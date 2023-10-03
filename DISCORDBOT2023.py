import discord
import random
import asyncio
import datetime
import mytenorpy
import myintents
import config

# Constants
MIN_WAIT = 1000
MAX_WAIT = 100000
GUILD_ID = 850841282485289010
GENERAL_CHANNEL_ID = 850841282485289015
GAUSS_MEAN = 8000
GAUSS_STD = 20000
MESSAGE_LIMIT = None

class MyClient(discord.Client):
    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")
        self.guild = self.get_guild(GUILD_ID) # get guild
        self.msg_list = [f"<@{member.id}>" for member in self.guild.members] # list of all members
        self.initialized = False
        self.start_wait_time = None
        self.time_to_wait = None
        await client.change_presence(activity=discord.Game("Getting Bitches Simulator 2023"))            
        await self.initialize_msg_list()
        print("Initializing intents...")
        self.initialized = True
        self.myintents = myintents.MyIntents(self.msg_list)
        await client.change_presence(activity=discord.Streaming(name="Shark Tank", url="https://www.twitch.tv/gothamchess"))
        self.msg_task = self.loop.create_task(self.msg_loop()) # start message loop

    async def initialize_msg_list(self):
        print("Getting messages...")
        for channel in self.guild.text_channels: # get list of all messages
            async for message in channel.history(limit=MESSAGE_LIMIT):
                if message.content and message.author != self.user:
                    self.msg_list.append(message.content)
        print(f"{len(self.msg_list)} messages found")

    async def on_message(self, message):
        # send a message to the channel the message was sent in
        print(f'{message.author}: {message.content}')
        if not self.msg_list:
            return
        
        if message.author == self.user:
            return
        
        self.msg_list.append(message.content)
        dice = random.randint(1, 100)
        reply_author = await self.get_reply_author(message)

        # send a message if the bot is mentioned
        if str(self.user.id) in message.content or reply_author == self.user or "@everyone" in message.content:
            if not self.initialized:
                await message.channel.send("Hey guys, I won't be on. I feel like dogshit right now")
                return
            
            if message.content.lower().endswith("when"): # send time left until next message
                await message.channel.send(f"{self.time_left} minutes remain", reference=message)
                return
            
            response = self.myintents.get_response(message)
            await message.channel.send(response, reference=message)
        elif dice < 5:
            await message.channel.send(mytenorpy.search_tenor(message.content), reference=message)

    async def msg_loop(self):
        print("rand_message Loop Started")
        counter = random.randint(1, 100)
        channel = self.get_channel(GENERAL_CHANNEL_ID) # general chat
        while not self.is_closed():
            await self.wait_random_time()
            await self.send_rand_message(channel, counter)

    async def send_rand_message(self, channel, counter):
            if counter % 3 == 0: # mention a random member
                random_member = random.choice(self.guild.members)
                await channel.send(f"<@{random_member.id}> {self.rand_message}")
            elif counter % 5 == 0: # send tenor gif of random message
                gif = mytenorpy.search_tenor(self.rand_message)
                if gif != None:
                    await channel.send(gif)
                else:
                    print("Tenor failed")
            else: # send random message
                await channel.send(self.rand_message)
            counter += 1

    async def wait_random_time(self):
            # wait for a random time
            time_to_wait = max(min(abs(random.gauss(GAUSS_MEAN, GAUSS_STD)), MAX_WAIT), MIN_WAIT)
            self.start_wait_time = datetime.datetime.now()
            self.time_to_wait = time_to_wait
            print(f"Waiting {time_to_wait} seconds")
            await asyncio.sleep(time_to_wait)

    async def get_reply_author(self, message):
        return None if message.reference is None or client.get_channel(message.reference.channel_id) is None  \
                    else (await client.get_channel(message.reference.channel_id).fetch_message(message.reference.message_id)).author

    @property
    def rand_message(self):
        while True:
            message = random.choice(self.msg_list)
            if message != None:
                return message
            
    @property
    def time_left(self):
        if self.start_wait_time is None or self.time_to_wait is None:
            return 0
        else:
            return round((self.time_to_wait - (datetime.datetime.now() - self.start_wait_time).total_seconds()) / 60)

if __name__ == "__main__":
    intents=discord.Intents.all()
    intents.message_content = True
    client = MyClient(intents=intents)
    client.run(config.DISCORD_TOKEN)