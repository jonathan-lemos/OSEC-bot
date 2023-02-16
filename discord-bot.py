import discord
from discord.ext import commands
from discord_bot_utils import is_student, StudentResult, logger, handler
import re
import subprocess
import os
import asyncio
#import mailchimp
import datetime
import os.path
import sys
import logging


### grab api information for mailchimp/discord if no config file given give error msg ###

"""
config file contents will be read in assuming the file format below:

NOTE: if information is not presented in this order, bot wont work

[discord api key]
[mailchimp api key]
[mailchimp username]
"""

try: 
	token = os.getenv("TOKEN")
except:
	logger.info(str(datetime.datetime.now()) + " [ERROR] TOKEN environment variable not found. Exiting...")
	exit(1)

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

## Member join ##
# when new member joins server, log it into log file 
@client.event
async def on_member_join(member):
	
	# get Talon role id
	new_member_role = discord.utils.get(message.guild.roles, name="Talon")
	
	# assign "Talon" role
	await member.add_roles(new_member_role)

	logger.info("----------------------------------------------------------------")
	logger.info(str(datetime.datetime.now()) + " New member joined: {}".format(member))
	return


# join-requests
@client.event
async def on_message(message):
	# Only read messages from "join-requests" channel
	if str(message.channel) != "join-requests":
		return

	# If the message is from the bot exit
	if message.author == client.user:
		return

	# set bot logging channel
	# prod channel ID 623862015781502976
	# test channel ID 623860915749781523
	log_channel = await client.fetch_channel("623862015781502976")

	# set Security Intern role id
	member_role = discord.utils.get(message.guild.roles, name="Security Intern")

	# log join request message
	message_log = str(str(message.author) + ": " + message.content)

	# success/failure messages
	success_msg = "Welcome to OSEC " + message.author.mention
	failure_msg = "invalid N number " + message.author.mention
	
	# log join-request message
	logger.info("----------------------------------------------------------------")
	logger.info(str(datetime.datetime.now()) + " @{} user sent a message.".format(message.author))
	logger.info(str(datetime.datetime.now()) + " validating new member... @{}".format(message.author))

	await log_channel.send("-------------------------------------------------")	
	await log_channel.send("**validating new member... @{}**".format(message.author))

	# Grab N# from join-request message
	reg = re.findall(r'(n\d{8})', message.content, re.IGNORECASE)
	if reg:
		student_id = reg[0]
	else:
		logger.error(str(datetime.datetime.now()) + " " + message_log + " [ERROR] invalid input")
		await log_channel.send("```" + message_log + "```" + " [ERROR] invalid input")

		error_msg = await message.channel.send("[ERROR] invalid input")
		await asyncio.sleep(15)
		await message.delete()
		await error_msg.delete()
		return
		
	student_check = is_student(student_id)

	if student_check == StudentResult.STUDENT:
		# verification success
		logger.info(str(datetime.datetime.now()) + " " + message_log + " [SUCCESS] new member is a valid UNF student")
		logger.info(str(datetime.datetime.now()) + " New OSEC member: " + student_id)

		await log_channel.send("```" + message_log + "```" + " [SUCCESS] new member is a valid UNF student")

		# assign "Security Intern" role
		await message.author.add_roles(member_role)

		# Send bot response message
		success_response = await message.channel.send(success_msg)

		# Log student info
		logger.info(str(datetime.datetime.now()) + " New OSEC member: " + student_id)

		# add user to mailchimp subscription list
		#mailchimp_msg = mailchimp.subscribe(student_id, first_name, last_name)
		#await log_channel.send(mailchimp_msg)

		# STEADY LADS
		await asyncio.sleep(15)

		# Delete original join-request message
		await message.delete()
		logger.info(str(datetime.datetime.now()) + " join request message has been deleted")

		# Delete bot response message
		await success_response.delete()
		logger.info(str(datetime.datetime.now()) + " bot response message deleted")

		return
	elif student_check == StudentResult.FACULTY:
		# faculty member
		logger.error(str(datetime.datetime.now()) + " " + message_log + " [ERROR] faculty member detected")

		await log_channel.send("```" + message_log + "```" + " [ERROR] faculty member detected")	

		error_msg = await message.channel.send("[ERROR] this n# is not associated with a UNF student account " + message.author.mention)
		await message.author.send("We are unable to verify your status as a UNF student, if you are a faculty member interested in joining OSEC please contact one of the club officers for further information. We apologize for the inconvenience.")
		await asyncio.sleep(15)
		# Delete original join-request message
		await message.delete()
		await error_msg.delete()
		return

	elif student_check == StudentResult.NOT_FOUND:
		logger.warning(str(datetime.datetime.now()) + " [FAILURE] new member is not a valid UNF student")
		await log_channel.send("[FAILURE] new member is not a valid UNF student")	
		failure_response = await message.channel.send(failure_msg)
		await asyncio.sleep(15)
		# Delete original join-request message
		await message.delete()
		# Delete bot response message
		await failure_response.delete()
		return


logger.info("Discord.py version " + discord.__version__)
client.run(token, log_handler=handler)

