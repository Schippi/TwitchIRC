from twitchio.ext import commands;
import sqlite3;
import traceback;
import time;
import asyncio;
from datetime import datetime;
from datetime import timedelta;
import sys;

starttime = {};
polls = {};
myprefix = '#'
lastmsgtime = None;
raidauto = True;

class MyBot(commands.Bot):
	async def event_command_error(self, ctx, error):
		if ( isinstance(error,commands.CommandNotFound)):
			print('command {0} '.format(error), file=sys.stderr)
			pass;
		else:
			traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def main():
	try:
		file = open(sys.argv[1],"r");
		IRCTOKEN = file.read().splitlines()[0];
		file.close();
		file = open(sys.argv[2],"r");
		APITOKEN = file.read().splitlines()[0];
		file.close();
	except Exception:
		traceback.print_exc();
		exit();
	bot = MyBot(
		irc_token=IRCTOKEN,
		api_token=APITOKEN,
		nick='schippirc',
		prefix=myprefix,
		initial_channels=['nilesy','theSchippi','ravs_']
	);

	conn = sqlite3.connect('words.db');
	cur = conn.cursor();

	@bot.event
	async def event_ready():
		print('Ready | {}'.format('schippirc'));
		print(bot.prefixes);
		

	@bot.event
	async def event_message( message):
		if(bot.nick == message.author.name):
			return;
		try:
			st = time.strftime('%Y-%m-%d %H:%M:%S');
			#print(message.content);
			list = [st,message.channel.name,message.author.name,message.content];
			cur.execute("INSERT INTO words(date,channel,usr,msg) VALUES (?,?,?,?)",list);
			conn.commit();
		except Exception:
			print(datetime.now().strftime("%d.%m.%Y, %H:%M:%S"));
			traceback.print_exc();
			
		channel = message.channel;
		global lastmsgtime;
		if(channel.name.lower() in ('nilesy')):
			if not lastmsgtime:
				lastmsgtime = datetime.now();
			else:
				currenttime = datetime.now();
				#if(lastmsgtime + timedelta(hours=4) < currenttime):
				#	await channel.send('.followers 10m');
				lastmsgtime = datetime.now();
		
		
		
		if( channel.name in polls):
			mypoll = polls[channel.name];
			if(time.time() < mypoll['time']):
				if 'VoteYea' in message.content:
					if not message.author.name in mypoll['users']:
						mypoll['users'].append(message.author.name);
						mypoll['yea']= mypoll['yea']+1;
				elif 'VoteNay' in message.content:
					if not message.author.name in mypoll['users']:
						mypoll['users'].append(message.author.name);
						mypoll['nay']= mypoll['nay']+1;
			elif not mypoll['done']:
				mypoll['done'] = True;
				if not message.content.startswith(myprefix+'poll'):
					await channel.send('the poll has closed! For results MODS can do '+myprefix+'poll (without asking a new question)')
		await bot.handle_commands(message);

	@bot.event
	async def event_raw_usernotice( channel, tags: dict):
		global raidauto;
		if tags:
			#print('usernotice tags'+str(tags));
			if tags['msg-id'] == 'raid' and channel.name.lower() in ['nilesy','theschippi'] and raidauto:
				#global starttime;
				
				starttime[channel.name] = time.time() + 900;
				chnl= tags['msg-param-displayName'];
				
				#await channel.send("@nilesy i'd disable followers-only mode, but im not a mod");
				#await asyncio.sleep(2);
				await channel.send('.followersoff');
				await asyncio.sleep(30);
				if chnl:
					await channel.send('Hello Raiders of '+chnl+'! This channel is usually in followers only mode, but i''ve disabled it for now. Be sure to follow to continue to be able to chat when we turn it back on!');
				else:
					await channel.send('Hello Raiders! This channel is usually in followers only mode, but i''ve disabled it for now. Be sure to follow to continue to be able to chat when we turn it back on!');
				await asyncio.sleep(900);
				endtime = time.time();
				if starttime[channel.name] < endtime and raidauto:
					await channel.send('.followers 10m');
					#await asyncio.sleep(2);
					#await channel.send("@nilesy i'd turn on followers-only mode on again but im not a mod");
		pass;

	@bot.event	
	async def event_raw_data(data):
		try:
			st = time.strftime('%Y-%m-%d %H:%M:%S: ');
			fil = open('traffic.log','a')
			fil.write((st+data.strip()+'\n'))
			fil.close();
		except Exception:
			traceback.print_exc();
		msg = data.strip().lower();
		#@msg-id=host_on :tmi.twitch.tv NOTICE #theschippi :Now hosting Nilesy.
		if '@msg-id=host_on' in msg and '#theschippi' in msg and 'hosting nilesy' in msg:
			if bot.get_channel('theschippi'):
				await bot.get_channel('theschippi').send('detecting host');
	
	@bot.command(name='raidauto')
	async def raidauto_command(ctx):
		if ctx.message.author.is_mod:
			channel = ctx.message.channel;
			global raidauto;
			raidauto = not raidauto;
			if raidauto:
				channel.send('i will disable followermode on raids');
			else:
				channel.send('i will do nothing on raids');
	
	# Commands use a different decorator
	@bot.command(name='test')
	async def test_command(ctx):
		#print(ctx.message.author.name + str(ctx.message.tags));
		#print(ctx.message.author.name + str(ctx.message.author.badges));
		if ctx.message.author.is_mod:
		#	await ctx.message.channel.send(ctx.message.content[6:])
		#	await ctx.send(ctx.message.content[6:])
			channel = ctx.message.channel;
			#global starttime;!test 1
			starttime[channel.name] = time.time() + 10;
			await channel.send('Cheer100 i luv u');
			await asyncio.sleep(10);
			endtime = time.time();
			await channel.send('test: times up+'+str(starttime[channel.name])+'  '+str(endtime));
			if starttime[channel.name] < endtime:
				await asyncio.sleep(1);
				await channel.send('right time');
	
	@bot.command(name='poll')
	async def poll_command(ctx):
		if ctx.message.author.is_mod:
			channel = ctx.message.channel;
			if len(ctx.message.content.split(' ')) == 1:
				if( channel.name in polls):
					mypoll = polls[channel.name];
					yea = mypoll['yea'];
					nay = mypoll['nay'];
					sum = yea+nay;
					pyea = 100* yea / (sum * 1.0);
					pnay = 100* nay / (sum * 1.0);
					await channel.send(mypoll['question']+': '+format(pyea, '.2f')+'% voted VoteYea, '+format(pnay, '.2f')+'% voted VoteNay '+str(sum)+' people voted!');
					await asyncio.sleep(0.2);
					if(mypoll['done']):
						await channel.send('polls are closed, so no need to spam');
					else:
						await channel.send('polls are still open, you still can get your vote in!');
				else:
					await channel.send('no poll ever asked');
			elif len(ctx.message.content.split(' ')) < 3:
				await channel.send('you need to ask a question pal... '+myprefix+'poll [time in seconds] [question]');
			else:
				try:
					question= ctx.message.content.split(' ',2)[2];
					offset = int(ctx.message.content.split(' ',2)[1]);
					polls[channel.name] = {'time':(time.time()+offset), 'question':question, 'yea':0, 'nay':0, 'users':[], 'done':False};
					await channel.send('A new poll has been started! - '+question+' - vote with VoteYea or VoteNay! - You have '+str(offset)+ ' seconds!');
				except:
					await channel.send('Something went wrong, please try again. '+myprefix+'poll [time in seconds] [question]');

	bot.run();
	conn.close();
	
if __name__ == '__main__':
	main();