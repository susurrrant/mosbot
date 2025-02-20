from typing import Optional
import os

import discord
from discord import app_commands
import sqlite3

guild_id = os.environ.get('MOSBOT_GUILD_ID')
MY_GUILD = discord.Object(id=guild_id)  # replace with your guild id


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
client = MyClient(intents=intents)

con = sqlite3.connect("mosbot.db")

cur = con.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS bank(id, balance)")
con.commit()
con.close()


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')



@client.tree.command()
@app_commands.describe(
    member='The user to give $mos to',
    dollars='The numbers of $mos to give',
)
async def mosgive(interaction: discord.Interaction, member: discord.Member, dollars: int, memo: str):
    valid_role = False
    caller = interaction.user
    caller_name = str(caller.display_name)

    member_name = str(member.display_name)
    member_id = member.id

    if dollars < 0:
        dollars = dollars * -1

    for role in caller.roles:
        if role.name == "mos":
            valid_role = True

    if valid_role == True:

        con = sqlite3.connect("mosbot.db")
        cur = con.cursor()
        res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))

        if res.fetchone() is not None:
            res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))
            data = res.fetchone()

            update_dollars = data[1] + dollars

            cur.execute("UPDATE bank SET balance=? WHERE id=?", (update_dollars, member_id,))
            con.commit()
            con.close()

            await interaction.response.send_message(f'{member_name} has gained {dollars} $mos, and now has {update_dollars} $mos. Memo: {memo}')

        else:
            cur.execute("INSERT INTO bank VALUES(?,?)", (member_id, dollars,))
            con.commit()
            con.close()

            await interaction.response.send_message(f'{member_name} now has {dollars} $mos. Memo: {memo}')

    else:
        await interaction.response.send_message(f'{caller_name} does not have $mos ledger write permissions.')



@client.tree.command()
@app_commands.describe(
    dollars='The numbers of $mos to steal',
)
async def mossteal(interaction: discord.Interaction, dollars: int, memo: str):
    valid_role = False
    caller = interaction.user
    caller_name = str(caller.display_name)


    # There is currently one valid criminal interaction
    #   until a table of relationships or something is made, this is hardcoded
    sovoke_id = 134554502140395520;
    thonir_id = 348883795266764800;

    dollars = abs(dollars)

    for role in caller.roles:
        if role.name == "mos":
            valid_role = True

    if valid_role == True:

        con = sqlite3.connect("mosbot.db")
        cur = con.cursor()
        update_source = 0
        update_target = 0

        source_res = cur.execute("SELECT * FROM bank WHERE id=?", (thonir_id,))
        if (source_res is not None):
            source_data = source_res.fetchone()
            update_source = source_data[1] - dollars

        target_res = cur.execute("SELECT * FROM bank WHERE id=?", (sovoke_id,))
        if (target_res is not None):
            target_data = target_res.fetchone()
            update_target = target_data[1] + dollars

            # This should not run if either of the above cursors failed
        if update_source is not 0 and update_target is not 0:
            cur.execute("UPDATE bank SET balance=? WHERE id=?", (update_source, thonir_id,))
            cur.execute("UPDATE bank SET balance=? WHERE id=?", (update_target, sovoke_id,))
            con.commit()
            con.close()

            await interaction.response.send_message(f'Sovoke has stolen {dollars} $mos from Thonir, and now has {update_target} $mos. \n Thonir now has {update_source} $mos. Memo: {memo}')
    else:
        await interaction.response.send_message(f'{caller_name} does not have $mos ledger write permissions.')



@client.tree.command()
@app_commands.describe(
    member='The user to take $mos from',
    dollars='The numbers of $mos to take',
)
async def mostake(interaction: discord.Interaction, member: discord.Member, dollars: int, memo: str):
    valid_role = False
    caller = interaction.user
    caller_name = str(caller.display_name)

    member_name = str(member.display_name)
    member_id = member.id

    if dollars < 0:
        dollars = dollars * -1

    for role in caller.roles:
        if role.name == "mos":
            valid_role = True

    if valid_role == True:

        con = sqlite3.connect("mosbot.db")
        cur = con.cursor()
        res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))

        if res.fetchone() is not None:
            res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))
            data = res.fetchone()

            update_dollars = data[1] - dollars

            cur.execute("UPDATE bank SET balance=? WHERE id=?", (update_dollars, member_id,))
            con.commit()
            con.close()

            await interaction.response.send_message(f'{member_name} has lost {dollars} $mos, and now has {update_dollars} $mos. Memo: {memo}')

        else:
            init_dollars = 0 - dollars
            cur.execute("INSERT INTO bank VALUES(?,?)", (member_id, init_dollars,))
            con.commit()
            con.close()

            await interaction.response.send_message(f'{member_name} has lost {dollars} $mos, and now has {init_dollars} $mos. Memo: {memo}')

    else:
        await interaction.response.send_message(f'{caller_name} does not have $mos ledger write permissions.')

@client.tree.command()
@app_commands.describe(
    member='The user to check $mos balance'
)
async def moscheck(interaction: discord.Interaction, member: discord.Member):
    """Checks a user's current $mos balance"""
    member_name = str(member.display_name)
    member_id = member.id

    con = sqlite3.connect("mosbot.db")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))

    if res.fetchone() is not None:
        res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))
        data = res.fetchone()
        con.close()

        await interaction.response.send_message(f'{member_name} has {data[1]} $mos')

    else:
        con.close()

        await interaction.response.send_message(f'{member_name} has 0 $mos')

@client.tree.command()
@app_commands.describe(
)
async def mosrank(interaction: discord.Interaction):
    """Displays current top 10 $mos rankings"""
    con = sqlite3.connect("mosbot.db")
    cur = con.cursor()

    res = cur.execute("SELECT * FROM bank ORDER BY balance DESC")
    data = res.fetchall()
    con.close()

    data_length = len(data)

    user_name = [0] * 10
    user_rank = [0] * 10

    guild = await client.fetch_guild(guild_id)

    #only care about the top 10
    if data_length >= 10:
        for i in range(0,10):
            #this is because I didn't start storing display_name along with id in the db. eh, will revamp later
            member = await guild.fetch_member(data[i][0])
            user_name[i] = member.display_name
            user_rank[i] = data[i][1]
    else:
        for i in range(0, (data_length - 1)):
            member = await guild.fetch_member(data[i][0])
            user_name[i] = member.display_name
            user_rank[i] = data[i][1]



    #lol, lmao even
    rank_str = f"Top 10 $mos balance \n 1. {user_name[0]}: {user_rank[0]} $mos \n 2. {user_name[1]}: {user_rank[1]} $mos \n 3. {user_name[2]}: {user_rank[2]} $mos \n 4. {user_name[3]}: {user_rank[3]} $mos \n 5.  {user_name[4]}: {user_rank[4]} $mos \n 6. {user_name[5]}: {user_rank[5]} $mos \n 7. {user_name[6]}: {user_rank[6]} $mos \n 8. {user_name[7]}: {user_rank[7]} $mos \n 9. {user_name[8]}: {user_rank[8]} $mos \n 10. {user_name[9]}: {user_rank[9]} $mos"

    await interaction.response.send_message(rank_str)

@client.tree.command()
@app_commands.describe(
)
async def mosrankinv(interaction: discord.Interaction):
    """Displays current bottom 10 $mos rankings"""
    con = sqlite3.connect("mosbot.db")
    cur = con.cursor()

    res = cur.execute("SELECT * FROM bank ORDER BY balance ASC")
    data = res.fetchall()
    con.close()

    data_length = len(data)

    user_name = [0] * 10
    user_rank = [0] * 10

    guild = await client.fetch_guild(guild_id)

    #only care about the top 10
    if data_length >= 10:
        for i in range(0,10):
            #this is because I didn't start storing display_name along with id in the db. eh, will revamp later
            member = await guild.fetch_member(data[i][0])
            user_name[i] = member.display_name
            user_rank[i] = data[i][1]
    else:
        for i in range(0, (data_length - 1)):
            member = await guild.fetch_member(data[i][0])
            user_name[i] = member.display_name
            user_rank[i] = data[i][1]



    #lol, lmao even
    rank_str = f"Bottom 10 $mos balance \n 1. {user_name[0]}: {user_rank[0]} $mos \n 2. {user_name[1]}: {user_rank[1]} $mos \n 3. {user_name[2]}: {user_rank[2]} $mos \n 4. {user_name[3]}: {user_rank[3]} $mos \n 5.  {user_name[4]}: {user_rank[4]} $mos \n 6. {user_name[5]}: {user_rank[5]} $mos \n 7. {user_name[6]}: {user_rank[6]} $mos \n 8. {user_name[7]}: {user_rank[7]} $mos \n 9. {user_name[8]}: {user_rank[8]} $mos \n 10. {user_name[9]}: {user_rank[9]} $mos"

    await interaction.response.send_message(rank_str)

client.run(os.environ.get('MOSBOT_TOKEN'))
