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
INTENTS = True

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
        self.initialized = True
        if INTENTS:
            print("Initializing intents...")
            self.myintents = myintents.MyIntents(self.msg_list)
            print("Intents initialized")
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
            
            if message.content.lower().endswith("join"):
                voice_state = message.author.voice
                if voice_state and self.guild.voice_client not in self.voice_clients:
                    voice = await voice_state.channel.connect()
                    self.sound_task = self.loop.create_task(self.play_random_sound(voice))
                return
            
            if INTENTS:
                response = self.myintents.get_response(message)
                await message.channel.send(response, reference=message)
        elif dice < 5:
            await message.channel.send(mytenorpy.search_tenor(message.content), reference=message)

    async def msg_loop(self):
        print("rand_message Loop Started")
        counter = random.randint(1, 100)
        channel = self.get_channel(GENERAL_CHANNEL_ID) # general chat
        while not self.is_closed():
            self.start_wait_time = datetime.datetime.now()
            await asyncio.sleep(self.wait_random_time())
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

    async def wait_random_time(self, gauss_mean=GAUSS_MEAN, gauss_std=GAUSS_STD, min_wait=MIN_WAIT, max_wait=MAX_WAIT):
            # wait for a random time
            self.time_to_wait = max(min(abs(random.gauss(gauss_mean, gauss_std)), max_wait), min_wait)
            print(f"Waiting {self.time_to_wait} seconds")
            return self.time_to_wait

    async def get_reply_author(self, message):
        return None if message.reference is None or client.get_channel(message.reference.channel_id) is None  \
                    else (await client.get_channel(message.reference.channel_id).fetch_message(message.reference.message_id)).author
    
    async def play_random_sound(self, voice):
        await asyncio.sleep(random.randint(1, 30))
        while True:
            if not voice.is_connected() and self.sound_task is not None:
                self.sound_task.cancel()
                return
            if voice.is_connected() and len(voice.channel.members) == 1:
                await voice.disconnect()
                self.sound_task.cancel()
                return
            
            sound_files = [(f"{config.SOUND_DIR}/{x}.mp3", y) for x, y in [
                ("A60", 5), ("AMBUSH", 5), ("AMBUSH2", 5), ("FIGURE", 10), ("FIGURE2", 10), ("HALT", 5),
                ("HIDE", 10), ("JACK", 2), ("JEFF", 20), ("PSST", 40), ("SCREECH", 30), ("SEEK", 10), ("SEEK2", 10),
                ("TIMOTHY", 5), ("RUSH", 10), ("ELEVATOR", 1), ("FNAF", 2)]]
            values = [x for x, y in sound_files]
            weights = [y for x, y in sound_files]
            sound = random.choices(values, weights)[0]

            voice.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=sound))
            print(f"Playing {sound}")
            await asyncio.sleep(await self.wait_random_time(100, 500, 10, 20000))

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