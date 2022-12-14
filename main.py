import sys

import discord
from discord.ext import commands as botCommands
from dotenv import dotenv_values, load_dotenv
import sqlite3
import pymysql
from commands.developer import developer
from commands.dynamic import dynamic
from commands.fun import fun
from commands.math import math
from commands.moderation import moderation
from commands.other import other
from commands.xp import xp
from PermissionsChecks import devCheck, permissionErrors
import datetime

sys.path.append(".")


load_dotenv()
TOKEN = dotenv_values()["TOKEN"]


async def determine_prefix(bot, message: discord.Message):
    if bot.devmode:
        return [bot.user.mention + " "]
    return ["!","oc!","o!"]
    


bot = botCommands.Bot(command_prefix=determine_prefix,
                      activity=discord.Activity(
                      type=discord.ActivityType.watching, name="/help for commands", url="https://github.com/x8c8r/octorb", start=datetime.datetime.now()),
                      intents=discord.Intents.all(),
                      help_command=None,
                      case_insensitive=True
                      )
db = None
devmode = False
if not "DEVMODE" in dotenv_values():
    db = pymysql.connect(host=dotenv_values()['DBHOST'], user=dotenv_values()[
                         'DBUSERNAME'], password=dotenv_values()['DBPASSWORD'], database=dotenv_values()['DB'])
else:
    devmode = True
    db = sqlite3.connect("database.db")

cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS `gallery` (
  `serverId` tinytext,
  `id` int DEFAULT NULL,
  `picUrl` tinytext
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS `quickCommands` (
  `serverId` tinytext,
  `command` tinytext,
  `output` text
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS `xp` (
  `serverId` text,
  `memberId` text,
  `memberXp` int DEFAULT NULL
)
""")
def dbexec(cursor, command:str, params=[]):
    if isinstance(cursor, sqlite3.Cursor):
        command = command.replace("%s","?")
    if not isinstance(params, list):
        if not isinstance(params, tuple):
            params = (params,)
    cursor.execute(command, params)

setattr(bot, "db", db)
setattr(bot, "dbexec", dbexec)
setattr(bot, "devmode", devmode)

@bot.event
async def on_ready():
    await bot.add_cog(fun(bot))
    await bot.add_cog(xp(bot))
    await bot.add_cog(other(bot))
    await bot.add_cog(moderation(bot))
    await bot.add_cog(math(bot))  # too annoying
    await bot.add_cog(dynamic(bot))
    await bot.add_cog(developer(bot))
    print(f"It's {bot.user}in' time")
    if db is None:
        print(f"WARNING: BOT IS NOT CONNECT TO A DATABASE. SOME COMMANDS MAY NOT WORK.")


@bot.event
async def on_disconnect():  
    print("Disconnected from Discord")


@bot.event
async def on_message(message: discord.Message):
    if not devCheck(message):
        if message.guild == None:
            if message.author.bot:
                return
            await message.channel.send("You are not allowed to use the bot in DMs")
            return
    await bot.process_commands(message)

# Helper Commands


async def getuser(userid, guildid):
    guild = bot.get_guild(guildid)
    user = await guild.fetch_member(userid)
    return user

@bot.event
async def on_command_error(ctx, error):
    match type(error):
        case permissionErrors.NonDeveloperError:
            await ctx.reply("This command is limited to Octorb Developers.")
        case botCommands.errors.MissingRequiredArgument:
            await ctx.reply(f"Missing argument: {error.param.name.capitalize()}")
        case botCommands.errors.MissingRequiredAttachment:
            await ctx.reply(f"Missing attachement.")
        case botCommands.errors.CommandNotFound:
            pass
        case botCommands.errors.CommandInvokeError:
            if isinstance(error.original, discord.errors.HTTPException):
                print(error.original.code)
                if error.original.code == 50035:
                    await ctx.reply("it's too big daddy, it won't fit~")
                    print(error.original.text)
                    return
                raise (error)
        case botCommands.errors.MissingPermissions:
            perms = error.missing_permissions
            await ctx.reply(f"You are missing the following permissions needed to use this command: {' '.join(str(x) for x in perms)}")
        case _: print (error)


@bot.check
async def botperms_check(ctx: botCommands.Context):
    guild = ctx.guild
    me = guild.me if guild is not None else ctx.bot.user
    permissions = ctx.channel.permissions_for(me)

    if getattr(permissions, "send_messages") is False:
        raise botCommands.BotMissingPermissions(["send_messages"])
    return True

if "DEVMODE" in dotenv_values():
    @bot.check
    async def devckeck(ctx: botCommands.Context):
        if devCheck(ctx):
            return True


bot.run(TOKEN)