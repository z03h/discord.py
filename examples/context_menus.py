import discord
from discord.application_commands import ApplicationCommandTree, MessageCommand, UserCommand

tree = ApplicationCommandTree(guild_id=1234)  # Replace with your guild ID, or ``None`` for global


class Greet(UserCommand, tree=tree):
    """Greets the targeted user"""

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Hello, {interaction.target.mention}!')


class Quote(MessageCommand, tree=tree):
    """Quotes a message"""

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'"{interaction.target.content}" - {interaction.target.author.name}')


class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


client = Client(update_application_commands_at_startup=True)
client.add_application_command_tree(tree)
client.run('token')
