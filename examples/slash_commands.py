import discord
from discord.application_commands import ApplicationCommand, ApplicationCommandTree, option

tree = ApplicationCommandTree(guild_id=1234)  # Replace with your guild ID, or ``None`` to commands global


class Ping(ApplicationCommand, name='ping', tree=tree):
    """Pong?"""

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message('Pong!')


class Math(ApplicationCommand, name='math', tree=tree):
    """Basic math operations."""

    class Add(ApplicationCommand, name='add'):
        """Sum of x + y."""
        x: int = option(description='Value of "x"', required=True)
        y: int = option(description='Value of "y"', required=True)

        async def callback(self, interaction: discord.Interaction):
            answer = self.x + self.y
            await interaction.response.send_message(
                f'The value of {self.x} + {self.y} is **{answer}**.',
                ephemeral=True
            )

    class Subtract(ApplicationCommand, name='subtract'):
        """Difference of x - y."""
        x: int = option(description='Value of "x"', required=True)
        y: int = option(description='Value of "y"', required=True)

        async def callback(self, interaction: discord.Interaction):
            answer = self.x - self.y
            await interaction.response.send_message(
                f'The value of {self.x} - {self.y} is **{answer}**.',
                ephemeral=True
            )


class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


client = Client(update_application_commands_at_startup=True)
client.add_application_command_tree(tree)
client.run('token')
