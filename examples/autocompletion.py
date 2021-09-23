import discord
from discord.application_commands import ApplicationCommand, ApplicationCommandTree, option

from typing import Any, Generator

tree = ApplicationCommandTree(guild_id=1234)  # Replace with your guild ID, or ``None`` to commands global

CHOICES = [
    'ant',
    'bird',
    'cat',
    'dog',
    'duck',
    'elephant',
    'fish',
    'giraffe',
    'horse',
    'iguana',
    'jellyfish',
    'kangaroo',
]


class Animal(ApplicationCommand, name='animal', tree=tree):
    """Choose an animal"""
    animal: str = option(description='The animal to choose')

    @animal.autocomplete
    async def animal_autocomplete(self, interaction: discord.Interaction) -> Generator[Any, Any, str]:
        query = interaction.value.lower()  # Access the autocomplete query via `interaction.value`

        for animal in CHOICES:
            if query in animal:
                yield animal

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'You chose **{self.animal}**', ephemeral=True)


class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


client = Client(update_application_commands_at_startup=True)
client.add_application_command_tree(tree)
client.run('token')
