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

What this fork adds
-------------------
This fork simply implements Danny's `slash command DSL <https://gist.github.com/Rapptz/2a7a299aa075427357e9b8a970747c2c>`_ (The class based version).

Differences between the DSL and this fork
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There were some modifications to the slash commands API since the DSL was created.
Therefore, there are some key differences between the DSL and what is in this fork:

- Slash commands are now a type of "application command" in Discord's API. (This was because of context menus.)
  Therefore, some names have been changed to be consistent with the API.

  - ``SlashCommand`` has been renamed to ``ApplicationCommand``
  - The namespace ``discord.slash`` has been renamed to ``discord.application_commands``.
  - ``argument`` is now ``option``. (``slash.argument`` -> ``application_commands.option``)

- The name for the command callback function is now ``callback`` instead of ``run``.
  This was to keep it consistent with the UI module.

Full list of additions
~~~~~~~~~~~~~~~~~~~~~~

.. |x| replace:: *(Not implemented yet)*

``application_commands`` namespace
**********************************

- ``application_commands.ApplicationCommand``
- ``application_commands.ApplicationCommandMeta``
- ``application_commands.ApplicationCommandOption``
- ``application_commands.ApplicationCommandOptionChoice``
- ``application_commands.ApplicationCommandPool``
- ``application_commands.option``

``interactions`` namespace
**************************

- ``discord.ApplicationCommand``
- ``discord.ApplicationCommandOption``
- ``discord.ApplicationCommandOptionChoice``

ConnectionState
***************

- ``ConnectionState.add_application_command``
- ``ConnectionState.get_application_command`` |x|
- ``ConnectionState.update_application_commands``

Client
******

- ``Client.application_commands`` |x|
- ``Client.add_application_command``
- ``Client.add_application_commands``
- ``Client.get_application_command`` |x|
- ``Client.fetch_application_command`` |x|
- ``Client.fetch_application_commands`` |x|
- ``Client.update_application_commands``
- ``Client.create_application_command`` |x|
- ``Client.bulk_create_application_commands`` |x|

Guild
*****

- ``Guild.application_commands`` |x|
- ``Guild.add_application_command`` |x|
- ``Guild.add_application_commands`` |x|
- ``Guild.get_application_command`` |x|
- ``Guild.fetch_application_command`` |x|
- ``Guild.fetch_application_commands`` |x|
- ``Guild.update_application_commands`` |x|
- ``Guild.create_application_command`` |x|
- ``Guild.bulk_create_application_commands`` |x|

Events
******

- ``on_application_command(interaction)``
- ``on_application_command_completion(interaction)``
- ``on_application_command_error(interaction, error)``

Exceptions
**********

- ``IncompatibleCommandSignature``

Notes
~~~~~

- ``discord.ApplicationCommand`` is not to be confused with ``discord.application_commands.ApplicationCommand``.
  ``discord.application_commands.ApplicationCommand`` is the one you construct yourself, and
  ``discord.ApplicationCommand`` is the one that is retrieved from Discord's API (E.g. fetching commands from a guild)

- Although ``discord.application_commands`` is extremely verbose in my opinion, no other names seemed better to me.
  Moving it to the module level would have conflicts.

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

    $ git clone https://github.com/Rapptz/discord.py
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
    from discord.application_commands import ApplicationCommand, option

    class HelloWorld(ApplicationCommand, name='hello-world'):
        """Hello"""
        async def callback(self, interaction):
            await interaction.response.send_message('Hello, world!')

    client = discord.Client()
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
