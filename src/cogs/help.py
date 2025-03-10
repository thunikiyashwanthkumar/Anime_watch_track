from discord.ext import commands
from discord import Embed
from config.config import OWNER_IDS, PREFIX

class CustomHelpCommand(commands.HelpCommand):
    """Custom help command implementation"""
    
    def get_command_signature(self, command):
        return f'{PREFIX}{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        embed = Embed(title="📚 Available Commands", color=0x3498db)
        
        # Check if user is owner
        is_owner = self.context.author.id in OWNER_IDS
        
        anime_commands = []
        owner_commands = []
        
        for cog, commands in mapping.items():
            for cmd in commands:
                if not cmd.hidden:
                    if cmd.cog_name == "OwnerCog":
                        if is_owner:
                            owner_commands.append(cmd)
                    elif cmd.cog_name != "HelpCog":
                        anime_commands.append(cmd)
        
        # Add anime commands
        if anime_commands:
            command_list = [f"`{PREFIX}{cmd.name}` - {cmd.help}" for cmd in anime_commands]
            embed.add_field(
                name="🎌 Anime Commands",
                value="\n".join(command_list),
                inline=False
            )
        
        # Add owner commands only for owners
        if owner_commands and is_owner:
            command_list = [f"`{PREFIX}{cmd.name}` - {cmd.help}" for cmd in owner_commands]
            embed.add_field(
                name="⚙️ Owner Commands",
                value="\n".join(command_list),
                inline=False
            )
        
        embed.set_footer(text=f"Type {PREFIX}help <command> for more info on a command.")
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        # Don't show owner commands to non-owners
        if command.cog_name == "OwnerCog" and self.context.author.id not in OWNER_IDS:
            embed = Embed(title="Command Not Found", color=0xe74c3c)
            embed.description = "This command does not exist."
            await self.get_destination().send(embed=embed)
            return
            
        embed = Embed(title=f"Command: {command.name}", color=0x3498db)
        embed.description = command.help or "No description available."
        
        # Add usage
        embed.add_field(
            name="Usage",
            value=f"`{self.get_command_signature(command)}`",
            inline=False
        )
        
        # Add aliases if any
        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False
            )
            
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        embed = Embed(title="Error", description=error, color=0xe74c3c)
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        # Don't show owner cog to non-owners
        if cog.qualified_name == "OwnerCog" and self.context.author.id not in OWNER_IDS:
            embed = Embed(title="Module Not Found", color=0xe74c3c)
            embed.description = "This module does not exist."
            await self.get_destination().send(embed=embed)
            return
            
        embed = Embed(
            title="Commands Help",
            color=0x3498db
        )
        
        if cog.description:
            embed.description = cog.description
            
        filtered_commands = []
        for command in cog.get_commands():
            if not command.hidden:
                filtered_commands.append(command)
                
        if filtered_commands:
            for command in filtered_commands:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command.help or "No description available.",
                    inline=False
                )
                
        await self.get_destination().send(embed=embed)

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self
        
    def cog_unload(self):
        self.bot.help_command = self._original_help_command

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
    return True 