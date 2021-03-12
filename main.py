# needed to connect to discord
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient
import os


# needed to connect to the voice channel
import nacl

# needed to create the poem database
import sqlite3

# needed to play the poem as MP3 files on the discord channel
import ffmpy
from mutagen.mp3 import MP3
import time
from gtts import gTTS

# Sets up the bot and gives it the command prefix
client = commands.Bot(command_prefix="&")

# Connects to the database
database = sqlite3.connect("poems.db")
cursor = database.cursor()

# Global variable to be outputted to user just in case there's an error
msg_err = "Error. Please type &help for help with syntax and commands."



# Lays out the structure of the table for reference
table_structure =  """CREATE TABLE Poems(
  PoemID INTEGER PRIMARY KEY AUTOINCREMENT,
  PoemName VARCHAR (50),
  Poem TEXT ,
  Author VARCHAR(20),
  TimeAdded TEXT
)"""
#cursor.execute(table_structure)
#database.commit()
#print(cursor.fetchall())  


# prints out when the bot is ready to the console
@client.event
async def on_ready():
    ascii_art = """
 _  _       _    ___  ___       _          _             ___         _  _            
| \| | ___ | |_ /   \| _ ) ___ | |_       (_) ___       / _ \  _ _  | |(_) _ _   ___ 
| .  |/ _ \|  _|| - || _ \/ _ \|  _|      | |(_-/      | (_) || ' \ | || || ' \ / -_)
|_|\_|\___/ \__||_|_||___/\___/ \__|      |_|/__/       \___/ |_||_||_||_||_||_|\___|

"""
    print (ascii_art)








# the client.command() decorator means that if the function name is mentioned after the command prefix, this function will be called
@client.command(help = "reads out a specified poem")
async def read(ctx, *args):
    """Reads in the name of the poem and searches it up on the database. If there is no result, it informs them. If there is
    more than one result, it lists them and asks the user to specify which one and proceeds to read out the poem in the voice
    channel that the user is in. If there is only one result, the poem is directly read out. The poem is also output on the text
    channel."""
    poem = ""
    for arg in args:
        poem += " " + arg
    poem = poem[1:]
    
    # Check for special characters as to not mess up the SQL
    if (";" in poem) or ("\"" in poem):
        await ctx.send("No semi colons (;) or speech marks please (\")!")
        return
    
    # If the user is not connected to a voice channel then an error is raised
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    
    # Otherwise the user's channel is found
    else:
        channel = ctx.message.author.voice.channel
        
    # Tries connecting to the channel and if it can't then the error is printed out to the console
    try:
        voice = await channel.connect()
    except Exception as e:
        print("""The program crashed due to this error: \n""",e,"""\n""")
      
    # All of the main code is in the catch block in case of errors
    try:
        
        # Makes the name of the poem in upper cases to aid the searching for characters using SQL queries
        poemname1 = poem.upper()
        print(poemname1)
        
        # This writes out the command in SQL to search for the poem and executes and gets it.
        command = f'SELECT * FROM Poems WHERE UPPER(PoemName) LIKE "%{poemname1}%"'
        cursor.execute(command)
        database.commit()
        ret = cursor.fetchall()
        print("poem:",ret)
        
        # All of the code before the next try statement is in case there are more than one search results for a given user query
        poem_num  = 0
        print(len(ret))
        if len(ret) == 0:
            await voice.disconnect()
            await ctx.send("Sorry poem not found. ")
            return
        
        # If there is more than one search result, the indented code is executed
        if len(ret)>1:
            msg = f"There are multiple poems with that keyword. Which one do you want?"
            
            # We go through every single returned item and append its poem id and name 
            for x in range (len(ret)):
                msg = msg + f"\n     {ret[x][0]}) {ret[x][1]}"
            msg = msg + "\n Enter the corresponding number of the poem."
            p = False
            
            # We iterate until a meaningless variable 'p' turns True
            while p != True:
                
                # We send this message initially and then every time they provide an invalid input
                await ctx.send(msg)
                
                # We wait for that specific user to respond and use their reply
                message_response = await client.wait_for('message', check=lambda m: m.author == ctx.author)
                poem_name = (message_response.content)
                
                # We repeat through every single returned tuple and check if the returned poem id is actually one of the results
                for x in range(len(ret)):
                    
                    # If it is one of the results, we save the index of that tuple within our returned list for later use and set p to True
                    if ret[x][0] == int(poem_name):
                        #print(ret[x][0])
                        poem_num = x
                        #print(x)
                        p = True
                
                # If p is still false, we display an error and loop back.
                if p == False:
                    await ctx.send("Sorry that number wasn't displayed. Try again.")
                    
        # This assigns the variable 'poem' to the poem using our poem_num variable we stored earlier
        poem = ret[poem_num][2]
        print(poem)
        
        try:
            # We replace all the "/," with two characters that are very unlikely to be used within the poem itself.
            poem1 = poem.replace("/,", "||")
            
            # Wherever there are commas, we replace with a comma and line break
            poem2 = poem1.replace(",",",\n   ")
            
            # We replace our two special characters with a comma as intended by user
            final_poem = poem2.replace("||",",")


            # This is the sentence to be converted into Text to Speech. It is written in the format {Poem Name} by {Poem author} {Poem}
            x = f"{ret[poem_num][1]} by {ret[poem_num][3]}. {final_poem}"
            
            # We turn the string into speech and save it locally to a file called 'hello.mp3'
            tts = gTTS(x, lang='en', slow = False)
            tts.save('hello.mp3')
        
        # If there is any problem with the code above then that means that there was no comma in the poem. Therefore, the final_poem is just the poem.
        except Exception as e:
            final_poem = poem
            print(e)
            
        # We create a new string which is of the format: {Poem Name} : {Poem}. Created on {Date} by {Poem Author}. 
        mess = f"""{ret[poem_num][1]}: \n
    {final_poem}\n
Created on {ret[poem_num][4]} by {ret[poem_num][3]}""" 
        await ctx.send(mess)
    except IndexError:
        await ctx.send("Poem not found.")
    
    # If there is any error in the function's code above, then an error message is sent to the channel
    except Exception as e:
        await ctx.send(msg_err)
        
        # The error is specified within the console too
        print(e)
    
    # The audio created earlier is played in the channel that the bot has connected to
    voice.play(discord.FFmpegPCMAudio(executable = "file path to ffmpeg.exe", source = "hello.mp3"))
    
    # We find the length of the audio being played so the bot can disconnect after that length of time
    audio = MP3("hello.mp3")
    wait = audio.info.length
    time.sleep(wait)
    await voice.disconnect()
    


# This function is to create a poem and send it to the database
@client.command(help = "takes in a poem that you have created")
async def create(ctx):
    """Prompts the user for their poem's name, the poem itself and their name. It then checks if any of the arguments have a 
    potential special character and if so, returns. Otherwise, it appends the poem and its details to the SQL database.""" 
        
    # When this function is called, the author of the calling of the function is asked for the poem's name. The bot checks to see if the user who called the function is in fact the user who replied.
    await ctx.send("Enter your poem's name: ")
    message_response = await client.wait_for('message', check=lambda m: m.author == ctx.author)
    poem_name = (message_response.content)

    if (";" in poem_name) or ("\"" in poem_name):
        await ctx.send("No semi colons (;) or speech marks please (\")!")
        return
        
    # The author of the calling of the function is asked for the poem. The bot checks to see if the user who called the function is in fact the user who replied.
    await ctx.send("Enter your poem. Remember, the bot will print out your poem in lines separated by commas. If you don't want a comma to make a line, simply use the forward slash, i.e. /, to cancel it. ")
    message_response = await client.wait_for('message', check=lambda m: m.author == ctx.author)
    poem = (message_response.content)
    
    if (";" in poem) or ("\"" in poem):
        await ctx.send("No semi colons (;) or speech marks please (\")!")
        return
    
    # The author of the calling of the function is asked for their name. The bot checks to see if the user who called the function is in fact the user who replied.
    await ctx.send("Enter your name. If you want to use your discord name, enter two bars (i.e., ||): ")
    message_response = await client.wait_for('message', check=lambda m: m.author == ctx.author)
    author = (message_response.content)
    
    if (";" in author) or ("\"" in author):
        await ctx.send("No semi colons (;) or speech marks please (\")!")
        return
    
    # We use the author's name if they wish for their discord name 
    if author == "||":
        author = message_response.author
    

    
    # The SQL command is generated and then executed in order to add the poem name, the poem itself, the author and the current date and time.
    command = f"""INSERT INTO Poems(PoemName, Poem, Author, TimeAdded) VALUES ("{poem_name}", "{poem}", "{author}", datetime('now'))"""
    print(command)
    cursor.execute(command)
    database.commit()
    print(cursor.fetchall()) 
    
    await ctx.send("Poem added! Thank you!")




# This function is used to just show the poem it requests
@client.command(help = "shows a specified poem")
async def show(ctx,*args):
    """Shows the user the poem they requested for. If there is no such poem, they are informed, if there are multiple nmatching poems,
    they are asked to confirm which one. If there is only one, or if they chose they poem, it is formatted and printed out."""
    for arg in args:
        if (";" in arg) or ("\"" in arg):
            await ctx.send("No semi colons (;) or speech marks please (\")!")
            return
        
    # All of this code has just been extracted from the read function above
    poem = ""
    for arg in args:
        poem += " "+arg
    poem = poem[1:]

    try:
        poemname1 = poem.upper()
        print(poemname1)
        command = f'SELECT * FROM Poems WHERE UPPER(PoemName) LIKE "%{poemname1}%"'
        cursor.execute(command)
        database.commit()
        ret = cursor.fetchall()
        poem_num = 0
        
        if len(ret) == 0:
            await ctx.send("Poem not found")
            return
            
        if len(ret)>1:
            msg = f"Sorry, there are multiple poems with that keyword. Which one do you want?"
            for x in range (len(ret)):
                msg = msg + f"\n     {ret[x][0]}) {ret[x][1]}"
            msg = msg + "\n Enter the corresponding number of the poem."
            p = False
            while p != True:
                await ctx.send(msg)
                message_response = await client.wait_for('message', check=lambda m: m.author == ctx.author)
                poem_name = (message_response.content)
                for x in range(len(ret)):
                    if ret[x][0] == int(poem_name):
                        print(ret[x][0])
                        poem_num = x
                        print(x)
                        p = True
                if p == False:
                    await ctx.send("Sorry that number wasn't displayed. Try again.")
        # This assigns the variable 'poem' to the poem
        poem = ret[poem_num][2]
        print(poem)
      
        try:
            
            # We replace all the "/," with two characters that are very unlikely to be used within the poem itself.
            poem1 = poem.replace("/,", "||")
            
            # Wherever there are commas, we replace with a comma and line break
            poem2 = poem1.replace(",",",\n   ")
            
            # We replace our two special characters with a comma as intended by user
            final_poem = poem2.replace("||",",")
        except:
            final_poem = poem
        mess = f"""{ret[poem_num][1]}: \n
    {final_poem}\n
Created on {ret[poem_num][4]} by {ret[poem_num][3]}""" 
        await ctx.send(mess)
        
    except Exception as e:
        await ctx.send(msg_err)
        print(e)

# This just prints out a random poem to the user
@client.command(help = "shows a random poem")
async def random(ctx):
    """Outputs a random poem from the database"""

        
    try:
        
        # Writes out the command for the SQL query to get a random poem
        command = """SELECT * FROM Poems  
ORDER BY random()  
LIMIT 1"""
        cursor.execute(command)
        database.commit()
        ret = cursor.fetchall()
        
        # Prints out poem in same format as before
        poem = ret[0][2]
        try:
            poem1 = poem.replace("/,", "||")
            poem2 = poem1.replace(",",",\n   ")
            final_poem = poem2.replace("||",",")
        except:
            final_poem = poem
        mess = f"""{ret[0][1]}: \n
    {final_poem}\n
Created on {ret[0][4]} by {ret[0][3]}""" 
        await ctx.send(mess)
    except Exception as e:
        await ctx.send("Poem not found.")
        print (e)

# Prints out all the authors in the database
@client.command(help = "shows all the authors in the database")
async def authors(ctx):

        
    try:
        
        # SQL query to group all poems by author and then print out every single author
        command = """SELECT Author FROM Poems GROUP BY Author"""
        cursor.execute(command)
        database.commit()
        ret = cursor.fetchall()
        await ctx.send("These are the authors:")
        
        # Goes through every single author in the 'ret' list which contains them and prints it
        for item in ret:
            await ctx.send(" - "+item[0])
    
    except Exception as e:
        await ctx.send(msg_err)
        print(e)  



@client.command(help = "shows all the poems by an author in the database")
async def poemsby(ctx, author):
    """Outputs the poems by a given author"""
    
    if (";" in author) or ("\"" in author):
        await ctx.send("No semi colons (;) or speech marks please (\")!")
        return
    
    try:
        
        # Looks through the database to see all poems made by the author that has been requested
        command = f"""SELECT PoemName, TimeAdded, Author FROM Poems WHERE UPPER(Author) LIKE "%{author}%\""""
        cursor.execute(command)
        database.commit()
        ret = cursor.fetchall()
        
        # If there are no poems from that author, that author does not exist
        if len(ret) == 0:
            await ctx.send("Sorry, no such author.")
        
        # Goes through every single poem that the author has created and prints it out to the discord channel
        else:
            for item in ret:
                r = (50 - len(item[0])) * " "
                await ctx.send(f" - {item[0]}{r} Created on {item[1]} by {item[2]}")
            await ctx.send("To view one of these poems, type &show PoemName")
        
    except Exception as e:
        await ctx.send(msg_err)
        print(e)


@client.command(help = "returns all poems made on the date provided")
async def date(ctx, dmy):
    """Outputs all poems made on a certain date"""
    
    # If there are any special characters which could mess with the SQL, the function returns.
    if (";" in dmy) or ("\"" in dmy):
        await ctx.send("No semi colons (;) or speech marks please (\")!")
        return
    
    # We query the database for all the poems made on that date. The double wildcard actually means simply putting
    # the year or month or day can return more results.
    command = f"""SELECT * FROM Poems WHERE TimeAdded LIKE "%{dmy}%\""""
    cursor.execute(command)
    database.commit()
    ret = cursor.fetchall()
    
    # If there were no returned results, no poems were made that day and so we return
    if len(ret) == 0:
        await ctx.send("Sorry, no poems were made that day.")
        return
        
    # Otherwise all the poems created that day are outputted to the user
    msg = f"Poems created on {dmy}"
    for x in range(len(ret)):
        msg = msg + f"\n- {ret[x][1]}          by {ret[x][3]}"
    await ctx.send(msg)
    

@client.command(help = "documentation and help for each command")
async def doc(ctx):
    """Prints out all the documentation / syntax in detail for the users"""

    
    msg = """Hey it's NotABot! Here's what I can do:

Note: **DO NOT USE SEMI-COLON(;) OR THE SPEECH MARK(") IN YOUR COMMANDS**

    1) Take in a poem input.

          You can write a poem and I'll add it to my database! Just use this command:

                   **&create**

          Then, just wait for my prompts! Dont't worry, I check who the message is by so it doesn't  \n          matter if someone else sends a message right after my prompt, I'll only \n          use your response.

    2) Show a poem.

          You can request for a poem for me to output to the discord channel. Just use this \n          command:

                   **&show PoemName**
                   
          If there are multiple poems matching yuor query, you'll be asked which one you meant.

    3) Read a poem.

          You can request for a poem to be read out to you. Just use this command:

                   **&read PoemName**

          This requires you to be in a channel.

    4) Show a random poem.

          You can request for a random poem for me to output to the discord channel. Just \n          use this command:

                   **&random**

    5) List all the authors.

          You can ask me to list all the authors. Just use this command:

                   **&authors**

    6) List all poems by an author.
       
          You can ask me to list all the poems by an author. Just use this command:
          
                   **&poemsby AuthorName**
                   
    7) List all poems made on a day.
    
          You can ask me to list all the poems made on a certain date.
          
                   **&date YYYY-MM-DD**
        
          Please be very adhering to the datetime format above.
          
    8) Find out a short summary of commands.
    
                   **&help**

    9) Find out more about commands.
    
                   **&doc**

          But I guess you figured that one out by now.
"""

    await ctx.send(msg)

@client.command()
async def delete(ctx):
    await ctx.send("If you would like to delete a poem please contact my creator ManLikeGrande.")
    # If a user wants to delete a poem, I'll just write an SQL query to remove the poem. Not automating this
    # means that we don't get catastrophic deleting errors or people deleting poems that they haven't made. 

# The bot is told to join the server / come online
client.run("Your bot token.")
