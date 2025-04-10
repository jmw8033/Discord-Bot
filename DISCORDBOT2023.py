import discord
import random
import asyncio
import datetime
import mytenor 
import myintents
import config
import os
import serial
from discord import AuditLogAction
from pyt2s.services import stream_elements

# -- Constants --
# Startup settings
MESSAGE_LIMIT = config.MESSAGE_LIMIT
GET_INTENTS = config.GET_INTENTS
GET_MESSAGE_HISTORY = config.GET_MESSAGE_HISTORY
GET_MESSAGE_LOOP = config.GET_MESSAGE_LOOP
GET_RAW_MESSAGE_HISTORY = config.GET_RAW_MESSAGE_HISTORY

DISCORD_TOKEN = config.DISCORD_TOKEN
GUILD_ID = config.GUILD_ID
GENERAL_CHANNEL_ID = config.GENERAL_CHANNEL_ID
MY_ID = config.MY_ID
COM_PORT = config.COM_PORT

CHAT_LOG_DIR = config.CHAT_LOG_DIR
RAW_MESSAGE_DIR = config.RAW_MESSAGE_DIR
SOUND_DIR = config.SOUND_DIR
SOUND_FILES = config.SOUND_FILES
MSG_LOOP_MEAN = config.MSG_LOOP_MEAN
MSG_LOOP_STD = config.MSG_LOOP_STD
MSG_LOOP_MIN = config.MSG_LOOP_MIN
MSG_LOOP_MAX = config.MSG_LOOP_MAX
SOUND_LOOP_MEAN = config.SOUND_LOOP_MEAN
SOUND_LOOP_STD = config.SOUND_LOOP_STD
SOUND_LOOP_MIN = config.SOUND_LOOP_MIN
SOUND_LOOP_MAX = config.SOUND_LOOP_MAX

try:
    SERIAL = serial.Serial(COM_PORT, baudrate=9600, timeout=0)
except:
    SERIAL = None


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs): # Initialize variables
        super().__init__(*args, **kwargs)
        self.guild = None
        self.message_list = []
        self.role_list = []
        self.initialized = False
        self.message_loop_start_wait_time = None
        self.message_loop_time_to_wait = None
        self.sound_task = None
        self.message_task = None
        self.myintents = None
        self.reaction_alphabet = [chr(x) for x in range(127462, 127462 + 26)]
        self.quote_of_the_month_message = None


    async def on_ready(self): # Called when the bot is logged in, initializes variables
        print(f"{self.user} has connected to Discord!")
        print(f"Intents: {GET_INTENTS} \nMessage History: {GET_MESSAGE_HISTORY} \nMessage Loop: {GET_MESSAGE_LOOP} \nRaw Messages: {GET_RAW_MESSAGE_HISTORY}\n")

        await client.change_presence(activity=discord.Game("I am coming"))  
        self.guild = self.get_guild(GUILD_ID) # get guild
        self.me = self.guild.get_member(MY_ID) # get my member object (me not the bot)
        self.message_list = [f"<@{member.id}>" for member in self.guild.members] # list of all messages, starts with mentions of all members
        self.role_list = [role.id for role in self.guild.roles][6:-3] # list of roles to assign
        await self.initialize_message_list()
        if GET_INTENTS:
            await self.initialize_intents()
        self.initialized = True
        
        if GET_MESSAGE_LOOP:
            self.message_task = self.loop.create_task(self.message_loop()) # start message loop
        client.loop.create_task(self.check_serial())
        await client.change_presence(activity=discord.Streaming(name="Woodchipper Simulator", url="https://www.twitch.tv/flats"))
        print("Startup Complete\n")


    async def initialize_message_list(self): # Get all messages from the guild, store in message_list
        print("Getting messages...")
        
        # loop through each file in RawMessages and add to message_list
        if GET_RAW_MESSAGE_HISTORY: 
            for filename in os.listdir(RAW_MESSAGE_DIR):
                with open(f"{RAW_MESSAGE_DIR}/{filename}", "r", encoding="utf-8") as file:
                    for line in file:
                        self.message_list.append(line.strip())

            # print according to whether message history is enabled
            if not GET_MESSAGE_HISTORY:
                print(f"{len(self.message_list)} total messages found (raw)")
                return
            else:
                print(f"{len(self.message_list)} raw messages found, getting all messages...")

        # get list of all messages
        for channel in self.guild.text_channels: 
            async for message in channel.history(limit=MESSAGE_LIMIT):
                parsed_message = message.content.replace("<@" + str(self.user.id) + ">", "")
                if len(parsed_message) > 0 and not parsed_message.isspace() and message.author != self.user:
                    self.message_list.append(parsed_message)

        # save messages to text file in ChatLogs
        with open(f"{CHAT_LOG_DIR}/ChatLogs.txt", "w", encoding="utf-8") as file:
            for message in self.message_list:
                file.write(message + "\n")
            print(f"{len(self.message_list)} total messages found, saved to {CHAT_LOG_DIR}/ChatLogs.txt")


    async def initialize_intents(self): # Initialize intents
        print("Initializing intents...")
        self.myintents = myintents.MyIntents(self.message_list)
        await self.get_intents()
        print("Intents initialized")


    async def on_message(self, message): # Called when a message is sent in a channel the bot is in
        print(f"{message.channel}: {message.author}: {message.content}")
        if not self.message_list or message.author == self.user: # ignore messages until message_list is initialized or if the message is from the bot
            return
        
        if message.channel.id == 1118732808752484402: # quotes channel
            return await self.reactions_handler(message)
        
        # if message is a DM from me, the first word is the destination and the rest is the message
        if isinstance(message.channel, discord.channel.DMChannel):
            return await self.dm_handler(message)
        
        dice = random.randint(1, 100) # random number to determine action for send_rmessage
        reply_author = await self.get_reply_author(message)

        # send a message if the bot is mentioned or replied to
        if str(self.user.id) in message.content or reply_author == self.user or "@everyone" in message.content:
            if not self.initialized:
                return await message.channel.send("Hey guys, I won't be on. I feel like dogshit right now")
            
            # handle mentions
            return await self.mention_handler(message)

        elif dice < 5: # chance to send a random message if not mentioned
            tenor_message = mytenor.search_tenor(message.content)
            if tenor_message != None:
                return await message.channel.send(tenor_message, reference=message)


    async def dm_handler(self, message): # Handle DMs from me
        message = message.content.split(" ")
        instruction = message[0].lower()
        message = message[1:]

        # special commands for me
        if message.author.id == MY_ID: 
            if instruction == "send": # send a message to a channel or user
                if len(message) < 2 or (message[0].lower() != "server" and not message[0].isdigit()):
                    return
                return await self.send_message(message[0], " ".join(message[1:]))
            
            elif instruction == "print": # print a variable
                if len(message) == 0:
                    return
                return print(vars(self).get(message[0], "Not found"))
             
        # special commands for everyone
        if instruction == "tts": # send a TTS message to the voice channel
            if len(message) == 0:
                return
            return await self.tts_handler(" ".join(message))
                

    async def tts_handler(self, text, voice="Brian"): # Handle TTS messages
        def delete_tts(error): # Delete the tts file after playing
            if error:
                print(error)
            if os.path.exists("tts.mp3"):
                os.remove("tts.mp3")

        tts = stream_elements.StreamElements().requestTTS(text, voice=voice)
        with open("tts.mp3", "+wb") as file:
            file.write(tts)
        if any([x.is_connected() for x in self.voice_clients]):
            voice = self.voice_clients[0]
            if voice.is_playing():
                voice.stop()
            await self.play_sound(voice, "tts.mp3", after=delete_tts)
 

    async def mention_handler(self, message): # Handle mentions of the bot
        parsed_message = message.content.replace("<@" + str(self.user.id) + ">", "").replace("@everyone", "").strip()
       
        if "yes or no" in parsed_message: # send a yes or no message
            return await message.channel.send(random.choice(["yes", "no"]), reference=message)
        
        elif parsed_message.lower().startswith("pick"):
            options = parsed_message.split(" ")[1:]
            return await message.channel.send(random.choice(options), reference=message)
        
        elif "ban" in message.content.lower():
            await self.ban_handler(message)

        elif message.content.lower().endswith(("join", "doors", "ben", "deliver us")): # join voice channel / play sound
            await self.voice_chat_handler(message)

        elif GET_INTENTS:
            await self.intents_handler(message)


    async def reactions_handler(self, message): # Handle adding reactions in the quotes channel
        if message.author.id != MY_ID: # only I can add reactions
            return
        if "ITS TIME TO VOTE" in message.content: # set the quote of the month message
            self.quote_of_the_month_message = message
        if message.content.startswith("add"): # add reactions to the quote of the month message, ex. add 3 will add A B C
            message = message.content.split(" ")
            if len(message) > 1 and message[1].isdigit() and int(message[1]) < 20 and self.quote_of_the_month_message is not None:
                for i in range(0, int(message[1])):
                    await self.quote_of_the_month_message.add_reaction(self.reaction_alphabet[i])
                await message.delete()
            

    async def ban_handler(self, message): # Remove all roles from members in message and assign a random role to each
        # occasionally gets missing permissions error when adding role, think its being rate limited
        member_ids = message.content.lower().split(" ")[2:]

        for member_id in member_ids:
            member_id = member_id.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            if not member_id.isdigit():
                continue

            member = self.guild.get_member(int(member_id))
            if member:
                new_role = random.choice(self.role_list)
                # remove previous roles
                for role in member.roles:
                    if role.id in self.role_list:
                        await member.remove_roles(role)
                try:
                    await member.add_roles(self.guild.get_role(new_role))
                except discord.errors.Forbidden:
                    # wait a second and try again if rate limited
                    await asyncio.sleep(1)
                    await member.add_roles(self.guild.get_role(new_role))
                
                await message.channel.typing()
                await asyncio.sleep(3)
                await message.channel.send(f"{member.mention}, you're banned", reference=message)
                await asyncio.sleep(1) # sleep to avoid rate limit


    async def voice_chat_handler(self, message): # Handle voice chat commands
        if not any([x.is_connected() for x in self.voice_clients]):
            voice = await self.join_voice(message)
            if not voice:
                return
        else:
            voice = self.voice_clients[0]

        if voice.is_playing():
            voice.stop()

        if message.content.lower().endswith("join"):
            self.sound_task = self.loop.create_task(self.random_sound_loop(voice))
        
        if message.content.lower().endswith("doors"):
            await self.play_sound(voice, f"{SOUND_DIR}/JEFF.mp3")
        
        if message.content.lower().endswith("ben"):
            await self.play_rsound(voice)

        if message.content.lower().endswith("deliver us"):
            await self.play_sound(voice, f"{SOUND_DIR}/deliver_us.mp3")


    async def intents_handler(self, message): # Handle responding with intents
        response = self.myintents.get_response(message)
        await message.channel.typing()
        await asyncio.sleep(3)
        await message.channel.send(response, reference=message)


    async def check_serial(self): # Check for serial input (tog)
        while SERIAL:
            try:
                if SERIAL.in_waiting: # check for serial input
                    line = SERIAL.readline().decode("utf-8").strip()
                    print(line)

                    if line == "tog":  # play random sound in voice channel, also using to reset presence
                        await client.change_presence(activity=discord.Streaming(name="Woodchipper Simulator", url="https://www.twitch.tv/flats"))
                        if any([x.is_connected() for x in self.voice_clients]):
                            voice = self.voice_clients[0]
                            if voice.is_playing():
                                voice.stop()
                            await self.play_rsound(voice)
                await asyncio.sleep(0.25)
            except serial.SerialException:
                return


    async def send_message(self, destination, message): # Send a message to a channel or user
        if destination == "server":
            destination = self.get_channel(GENERAL_CHANNEL_ID)
        else:
            destination = await self.get_user(int(destination)).create_dm() # get DM channel

        if destination is None or message is None:
            return
        await destination.typing()
        await asyncio.sleep(3)
        await destination.send(message)


    async def join_voice(self, message): # Join voice channel
        voice_state = message.author.voice
        if voice_state and self.guild.voice_client not in self.voice_clients:
            return await voice_state.channel.connect()
        return None


    async def get_intents(self): # Get intents from myintents.py
        await self.loop.run_in_executor(None, self.myintents.get_intents) # creates Intents object using myintents.py using loop.run_in_executor to avoid blocking


    async def send_rmessage(self, channel, counter=0, reference=None): # Send a random message
        message = None
        if counter % 3 == 0: # mention a random member
            random_member = random.choice(self.guild.members)
            message = f"<@{random_member.id}> {self.rmessage}"
       
        elif counter % 5 == 0: # send tenor gif of random message
            message = mytenor.search_tenor(self.rmessage)
            if message == None:
                print("Tenor search failed")
                return
        
        else: # send random message
            try:
                message = self.rmessage
                # if in a voice channel, play tts of message
                if any([x.is_connected() for x in self.voice_clients]):
                    voice = self.voice_clients[0]
                    if voice.is_playing():
                        voice.stop()
                    await self.tts_handler(message)
            
            except discord.errors.HTTPException:
                print("Message failed, trying again")
                self.send_rmessage(channel, counter, reference)

        counter += 1
        await channel.typing()
        await asyncio.sleep(3)
        await channel.send(message, reference=reference)
        

    async def wait_random_time(self, mean, std, min_wait, max_wait): # Wait for a random time
        return max(min(abs(random.gauss(mean, std)), min_wait), max_wait)


    async def get_reply_author(self, message): # Get the author of the message being replied to
        if message.reference is not None:
            reply = await message.channel.fetch_message(message.reference.message_id)
            return reply.author
        return None        


    async def play_sound(self, voice, sound, after=None): # Play a sound in the voice channel
        if not voice.is_connected():
            return
        voice.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=sound), after=after)
        print(f"Playing {sound}")


    async def play_rsound(self, voice): # Play a random sound in the voice channel
        values = [x for x, y in SOUND_FILES]
        weights = [y for x, y in SOUND_FILES]
        sound = random.choices(values, weights)[0]
        await self.play_sound(voice, sound)


    async def message_loop(self): # Message loop
        print("Random message loop started")
        counter = random.randint(1, 100)
        channel = self.get_channel(GENERAL_CHANNEL_ID) # general chat
        while not self.is_closed():
            self.message_loop_start_wait_time = datetime.datetime.now()
            self.message_loop_time_to_wait = await self.wait_random_time(MSG_LOOP_MEAN, MSG_LOOP_STD, MSG_LOOP_MIN, MSG_LOOP_MAX)
            print(f"Waiting {round(self.message_loop_time_to_wait / 3600, 2)}h (message loop)")
            await asyncio.sleep(self.message_loop_time_to_wait)
            await self.send_rmessage(channel, counter) 


    async def random_sound_loop(self, voice): # Loop to play random sounds in the voice channel
        while True:
            if not voice.is_connected() and self.sound_task is not None:
                self.sound_task.cancel()
                return
            
            time_to_wait = await self.wait_random_time(SOUND_LOOP_MEAN, SOUND_LOOP_STD, SOUND_LOOP_MIN, SOUND_LOOP_MAX)
            print(f"Waiting {round(time_to_wait / 3600, 2)}h (sound loop)")
            await self.play_rsound(voice)
            await asyncio.sleep(time_to_wait)


    async def on_voice_state_update(self, member, before, after): # Called when a member joins or leaves a voice channel
        print(f"{member} moved from {before.channel} to {after.channel}")
        if member == self.user:
            if before.channel is not None and after.channel is None:
                async for entry in member.guild.audit_logs(action=AuditLogAction.member_disconnect):
                    await entry.user.move_to(None)
                    break
            return
        if before.channel == after.channel:
            return
        
        # if the bot is the only one in the voice channel, disconnect
        voice = [x for x in self.voice_clients if x.channel == before.channel]
        if voice and len(before.channel.members) == 1:
            await voice[0].disconnect()
            if self.sound_task is not None:
                self.sound_task.cancel()
            return
        
        # if I join, join, if I leave, leave
        if member == self.me:
            if after.channel is not None:
                if any([x.is_connected() for x in self.voice_clients]):
                    return
                voice = await after.channel.connect()
                self.sound_task = self.loop.create_task(self.random_sound_loop(voice))
            else:
                if voice:
                    await voice[0].disconnect()
                    if self.sound_task is not None:
                        self.sound_task.cancel()


    @property
    def rmessage(self): # Get a random message from message_list
        while True:
            message = random.choice(self.message_list)
            if message != None and len(message) > 0 and not message.isspace():
                return message
                 

    @property 
    def time_left(self): # Get the time left until the next message
        if self.message_loop_start_wait_time is None or self.message_loop_time_to_wait is None:
            return 0
        else:
            return round((self.message_loop_time_to_wait - (datetime.datetime.now() - self.message_loop_start_wait_time).total_seconds()) / 60)


if __name__ == "__main__":
    intents=discord.Intents.all()
    intents.message_content = True
    client = MyClient(intents=intents)
    client.run(DISCORD_TOKEN)