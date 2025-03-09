from discord.ext import commands
from discord import Embed
from config.config import OWNER_IDS, PREFIX

class CustomHelpCommand(commands.HelpCommand):
    """Custom help command implementation"""
    
    def get_command_signature(self, command):
        return f'{PREFIX}{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        embed = Embed(title="📚 Bot Commands", color=0x3498db)
        
        # Check if user is owner
        is_owner = self.context.author.id in OWNER_IDS
        
        for cog, commands in mapping.items():
            filtered_commands = []
            for cmd in commands:
                # Skip owner commands for non-owners
                if cmd.cog_name == "OwnerCog" and not is_owner:
                    continue
                if not cmd.hidden:
                    filtered_commands.append(cmd)
            
            if filtered_commands:
                cog_name = getattr(cog, "qualified_name", "Other")
                # Skip showing OwnerCog section to non-owners
                if cog_name == "OwnerCog" and not is_owner:
                    continue
                    
                command_list = [f"`{PREFIX}{cmd.name}` - {cmd.help}" for cmd in filtered_commands]
                if command_list:
                    embed.add_field(
                        name=f"📌 {cog_name}" if cog else "📌 Misc",
                        value="\n".join(command_list),
                        inline=False
                    )
        
        embed.set_footer(text=f"Type {PREFIX}help <command> for more info on a command.")
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = Embed(title=f"Command: {command.name}", color=0x3498db)
        
        # Don't show owner commands to non-owners
        if command.cog_name == "OwnerCog" and self.context.author.id not in OWNER_IDS:
            embed.description = "❌ This command does not exist."
            await self.get_destination().send(embed=embed)
            return
            
        embed.description = command.help or "No description available."
        embed.add_field(name="Usage", value=f"`{self.get_command_signature(command)}`", inline=False)
        
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{alias}`" for alias in command.aliases), inline=False)
            
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        embed = Embed(title="Error", description=error, color=0xe74c3c)
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = Embed(title=f"{cog.qualified_name} Commands", color=0x3498db)
        
        # Don't show owner cog to non-owners
        if cog.qualified_name == "OwnerCog" and self.context.author.id not in OWNER_IDS:
            embed.description = "❌ This module does not exist."
            await self.get_destination().send(embed=embed)
            return
            
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