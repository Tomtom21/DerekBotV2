from discord.ext import commands
from discord import app_commands, Interaction
from shared.constants import GOOGLE_TTS_VOICE_INFO
from shared.TTSManager import TTSManager
from shared.VCAudioManager import VCAudioManager
from shared.data_manager import DataManager

class TTSGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager, tts_manager: TTSManager, audio_manager: VCAudioManager):
        self.bot = bot
        self.data_manager = data_manager
        self.tts_manager = tts_manager
        self.audio_manager = audio_manager

    group = app_commands.Group(name="tts", description="Commands for managing TTS features")

    @group.command(name="tts_language", description="Set the TTS language")
    @app_commands.describe(language="Language choice")
    @app_commands.choices(
        language=[
            app_commands.Choice(name=key, value=key)
            for key in GOOGLE_TTS_VOICE_INFO.keys()
        ]
    )
    async def tts_language(self, interaction: Interaction, language: app_commands.Choice[str]):
        self.tts_manager.set_voice(language)
        await interaction.response.send_message(f"TTS language set to {language.value}.", ephemeral=True)

    @group.command(name="vckick", description="Kick the bot from the current voice channel")
    async def vckick(self, interaction: Interaction):
        successfully_kicked = await self.audio_manager.disconnect_from_vc()
        if successfully_kicked:
            await interaction.response.send_message("Bot kicked from voice channel.", ephemeral=True)
        else:
            await interaction.response.send_message("`Bot is not in a voice channel.`", ephemeral=True)

    @group.command(name="vcskip", description="Skip the current TTS or audio in the voice channel")
    async def vcskip(self, interaction: Interaction):
        successfully_skipped = self.audio_manager.skip_current()
        if successfully_skipped:
            await interaction.response.send_message("Skipped current VC audio.", ephemeral=True)
        else:
            await interaction.response.send_message("`Failed to skip current VC audio`", ephemeral=True)

    @group.command(name="announce_name", description="Announce the name of the user when they use vc-text")
    @app_commands.describe(announce="Do you want your name to be announced when using vc-text?")
    async def announce_name(self, interaction: Interaction, announce: bool):
        self.data_manager.ensure_user_exists(interaction.user)    
        successfully_updated = self.data_manager.update_table_data(
            table_name="users",
            match_json={"user_id": interaction.user.id},
            update_json={'vc_text_announce_name': announce}
        )
        
        if successfully_updated:
            await interaction.response.send_message(
                f"{'Enabled' if announce else 'Disabled'} name announcement for you when using vc-text.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "`Failed to update name announcement setting.`", ephemeral=True
            )
