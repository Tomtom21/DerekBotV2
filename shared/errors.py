from discord import Interaction
import logging

class NotInVoiceChannelError(Exception):
    """Raised when a user is not in a voice channel but tries to issue a music command."""

    async def handle_error(self, interaction: Interaction, requires_followup: bool = False):
        """
        Handles the error by sending a message to the user.
        :param interaction: The Discord interaction object
        :param requires_followup: Whether the response requires a follow-up message
        """
        logging.warning(f"User {interaction.user.name} tried to use a music command without being in a voice channel.")
        error_string = "`You must be in a voice channel to use this command.`"
        if requires_followup:
            await interaction.followup.send(error_string)
        else:
            await interaction.response.send_message(error_string)
