discord.py
==========

.. image:: https://discord.com/api/guilds/336642139381301249/embed.png
   :target: https://discord.gg/r3sSKJJ
   :alt: Discord server invite
.. image:: https://img.shields.io/pypi/v/discord.py.svg
   :target: https://pypi.python.org/pypi/discord.py
   :alt: PyPI version info
.. image:: https://img.shields.io/pypi/pyversions/discord.py.svg
   :target: https://pypi.python.org/pypi/discord.py
   :alt: PyPI supported Python versions

A modern, easy to use, feature-rich, and async ready API wrapper for Discord written in Python.

Welcome to my spoon of discord.py
---------------------------------

It was originally made to implement Danny's
`slash command DSL <https://gist.github.com/Rapptz/2a7a299aa075427357e9b8a970747c2c>`_ (The class based version),
and it does it pretty well, although I still need to decide what happens with naming conflicts.

There have been many changes since this DSL was created however, for example slash commands turning
into a category of "application commands". These "application commands" also contain "context menus",
specifically referred to as "message commands" and "user commands". This spoon™ does, in fact, support them.

As a result of this, naming schemes that go along "slash command" have been renamed to their counterparts
that go along with "application_command". This unfortunately does make things a bit verbose, however
shortening the names would leave name conflicts and confusion.

Everything that this spoon™ adds/supports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Application commands

  - Slash commands
  - Context menus (Message commands & user commands)
  - ``channel_types`` option field
  - Autocomplete options

- Role icons
- Welcome screens (in which is *not* NC's PR)

Key Features
-------------

- Modern Pythonic API using ``async`` and ``await``.
- Proper rate limit handling.
- Optimised in both speed and memory.

Installing
----------

**Python 3.8 or higher is required**

To install the library without full voice support, you can just run the following command:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U discord.py

    # Windows
    py -3 -m pip install -U discord.py

Otherwise to get voice support you should run the following command:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U "discord.py[voice]"

    # Windows
    py -3 -m pip install -U discord.py[voice]


To install the development version, do the following:

.. code:: sh

    $ git clone https://github.com/jay3332/discord.py
    $ cd discord.py
    $ python3 -m pip install -U .[voice]


Optional Packages
~~~~~~~~~~~~~~~~~~

* `PyNaCl <https://pypi.org/project/PyNaCl/>`__ (for voice support)

Please note that on Linux installing voice you must install the following packages via your favourite package manager (e.g. ``apt``, ``dnf``, etc) before running the above commands:

* libffi-dev (or ``libffi-devel`` on some systems)
* python-dev (e.g. ``python3.6-dev`` for Python 3.6)

Quick Example
--------------

.. code:: py

    import discord

    class MyClient(discord.Client):
        async def on_ready(self):
            print('Logged on as', self.user)

        async def on_message(self, message):
            # don't respond to ourselves
            if message.author == self.user:
                return

            if message.content == 'ping':
                await message.channel.send('pong')

    client = MyClient()
    client.run('token')

Application Command Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

    import discord
    from discord.application_commands import ApplicationCommand, ApplicationCommandTree, option

    tree = ApplicationCommandTree(guild_id=123456)

    class HelloWorld(ApplicationCommand, name='hello-world', tree=tree):
        """Hello"""
        async def callback(self, interaction):
            await interaction.response.send_message('Hello, world!')

    client = discord.Client(update_application_commands_at_startup=True)
    client.add_application_command_tree(tree)
    client.run('token')

Bot Example
~~~~~~~~~~~~~

.. code:: py

    import discord
    from discord.ext import commands

    bot = commands.Bot(command_prefix='>')

    @bot.command()
    async def ping(ctx):
        await ctx.send('pong')

    bot.run('token')

You can find more examples in the examples directory.

Links
------

- `Documentation <https://discordpy.readthedocs.io/en/latest/index.html>`_
- `Official Discord Server <https://discord.gg/r3sSKJJ>`_
- `Discord API <https://discord.gg/discord-api>`_
