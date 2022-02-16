import discord
from discord.ui import Modal, text_input


class MyModal(Modal):
    name = text_input(label='Name', placeholder='Enter your name here...', min_length=2, max_length=32, required=True)
    about = text_input(label='About', style=discord.TextInputStyle.long, placeholder='Enter things about you...', max_length=2048)

    def __init__(self):
        super().__init__(title='My Modal', timeout=240)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Hello, {self.name.value}! {self.about.value}')


class Hello(discord.application_commands.ApplicationCommand):
    """Sends a hello modal"""

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MyModal())


if __name__ == '__main__':
    client = discord.Client(update_application_commands_at_startup=True)
    client.add_application_command(Hello)
    client.run('token')
