from discord.ext import commands
from discord import app_commands, Interaction
from shared.constants import GOOGLE_TTS_VOICE_INFO
from shared.TTSManager import TTSManager
from shared.VCAudioManager import VCAudioManager
from shared.data_manager import DataManager
import logging

class TTSGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager, tts_manager: TTSManager, audio_manager: VCAudioManager):
        self.bot = bot
        self.data_manager = data_manager
        self.tts_manager = tts_manager
        self.audio_manager = audio_manager

    group = app_commands.Group(name="tts", description="Commands for managing TTS features")

    @group.command(name="enable-tts", description="Enable/Disable TTS")
    @app_commands.describe(tts_enabled="Whether TTS should be enabled or not")
    async def enable_tts(self, interaction: Interaction, tts_enabled: bool):
        """
        Enables or disables TTS for the server (admin only).

        :param interaction: The Discord interaction object
        :param tts_enabled: Boolean to enable or disable TTS
        """
        await interaction.response.defer(ephemeral=True)
        db_user = self.data_manager.get_item_by_key(
            table_name="users",
            key="user_id",
            value=interaction.user.id
        )
        if db_user and db_user.get("is_administrator"):
            successfully_updated = self.data_manager.update_table_data(
                table_name="system_config",
                match_json={"config_name": 'tts_enabled'},
                update_json={"config_value_bool": tts_enabled}
            )
            if successfully_updated:
                logging.info(f"User {interaction.user.name} set TTS enabled to {tts_enabled}")
                await interaction.followup.send(f"{'Enabled' if tts_enabled else 'Disabled'} TTS for server.")
            else:
                logging.error(f"Failed to update TTS enabled state for user {interaction.user.name}")
                await interaction.followup.send("`Failed to update TTS state.`")
        else:
            logging.warning(f"User {interaction.user.name} attempted to change TTS enabled state without admin rights")
            await interaction.followup.send("`You must be an administrator to update this value.`")

    @group.command(name="tts-language", description="Set the TTS language")
    @app_commands.describe(language="Language choice")
    @app_commands.choices(
        language=[
            app_commands.Choice(name=key, value=key)
            for key in GOOGLE_TTS_VOICE_INFO.keys()
        ]
    )
    async def tts_language(self, interaction: Interaction, language: app_commands.Choice[str]):
        """
        Sets the TTS language for the bot.

        :param interaction: The Discord interaction object
        :param language: The language choice for TTS
        """
        await interaction.response.defer(ephemeral=True)

        self.data_manager.ensure_user_exists(interaction.user)

        successfully_updated = self.data_manager.update_table_data(
            table_name="users",
            match_json={"user_id": interaction.user.id},
            update_json={"tts_language": language.value}
        )
        if successfully_updated:
            logging.info(f"User {interaction.user.name} set TTS language to {language.value}")
            await interaction.followup.send(f"TTS language set to {language.value}")
        else:
            logging.warning(f"Failed to update TTS language for user {interaction.user.name}")
            await interaction.followup.send("`Failed to update TTS language`")

    @group.command(name="vckick", description="Kick the bot from the current voice channel")
    async def vckick(self, interaction: Interaction):
        """
        Disconnects the bot from the current voice channel.

        :param interaction: The Discord interaction object
        """
        # Deferring so that we can wait for any audios to finish without the command timing out
        await interaction.response.defer()

        successfully_kicked = await self.audio_manager.disconnect_from_vc()
        if successfully_kicked:
            logging.info(f"User {interaction.user.name} kicked bot from voice channel")
            await interaction.followup.send("Bot kicked from voice channel.")
        else:
            logging.warning(f"User {interaction.user.name} tried to kick bot, but bot was not in a voice channel")
            await interaction.followup.send("`Bot is not in a voice channel OR audio is still playing.`")

    @group.command(name="vcskip", description="Skip the current TTS or audio in the voice channel")
    async def vcskip(self, interaction: Interaction):
        """
        Skips the current TTS or audio in the voice channel.

        :param interaction: The Discord interaction object
        """
        successfully_skipped = self.audio_manager.skip_current()
        if successfully_skipped:
            logging.info(f"User {interaction.user.name} skipped current VC audio")
            await interaction.response.send_message("Skipped current VC audio.")
        else:
            logging.error(f"User {interaction.user.name} failed to skip current VC audio")
            await interaction.response.send_message("`Failed to skip current VC audio`", ephemeral=True)

    @group.command(name="announce-name", description="Announce the name of the user when they use vc-text")
    @app_commands.describe(announce="Do you want your name to be announced when using vc-text?")
    async def announce_name(self, interaction: Interaction, announce: bool):
        """
        Sets whether to announce the user's name when using vc-text.

        :param interaction: The Discord interaction object
        :param announce: Boolean to enable or disable name announcement
        """
        await interaction.response.defer(ephemeral=True)
        self.data_manager.ensure_user_exists(interaction.user)    
        successfully_updated = self.data_manager.update_table_data(
            table_name="users",
            match_json={"user_id": interaction.user.id},
            update_json={'vc_text_announce_name': announce}
        )
        
        if successfully_updated:
            logging.info(f"User {interaction.user.name} set announce_name to {announce}")
            await interaction.followup.send(
                f"{'Enabled' if announce else 'Disabled'} name announcement for you when using vc-text."
            )
        else:
            logging.error(f"Failed to update announce_name for user {interaction.user.name}")
            await interaction.followup.send("`Failed to update name announcement setting.`")
