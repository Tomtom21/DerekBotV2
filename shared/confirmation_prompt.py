import logging

from discord.ui import Button, View
from discord import ButtonStyle, Interaction

class ConfirmationPrompt:
    """
    A class to handle confirmation prompts in Discord.
    """
    def __init__(
            self,
            prompt_text: str,
            on_confirm_callback,
            on_cancel_callback=None,
            status_default_msg="Please either confirm or cancel.",
            status_confirmed_msg="✅ Confirmed.",
            status_cancelled_msg="❌ Cancelled.",
            timeout=60
    ):
        """
        Initializes a ConfirmationPrompt.

        :param prompt_text: The question to ask the user.
        :param on_confirm_callback: Function to call when confirmed.
        :param on_cancel_callback: Function to call when cancelled.
        :param status_default_msg: Default status message.
        :param status_confirmed_msg: Status message after confirmation.
        :param status_cancelled_msg: Status message after cancellation.
        """
        self.prompt_text = prompt_text

        # Button callbacks
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback

        # Messages to show in status area
        self.status = status_default_msg
        self.status_confirmed_msg = status_confirmed_msg
        self.status_cancelled_msg = status_cancelled_msg

        # Keeping track of button state, incase of double presses
        self.buttons_disabled = False
        self.timeout = timeout

        # So we are aware of the message we sent to time it out
        self.message = None

    def get_message(self):
        """
        Returns the full message to display, including status.
        """
        return f"{self.prompt_text}\n\n---\n{self.status}"

    def create_view(self):
        """
        Creates a Discord UI view with confirm and cancel buttons.
        """
        return ConfirmationView(self, timeout=self.timeout)

class ConfirmationView(View):
    """
    View for the confirmation prompt.
    """
    def __init__(self, prompt: ConfirmationPrompt, timeout):
        super().__init__(timeout=timeout)
        self.prompt: ConfirmationPrompt = prompt

        # Defining buttons
        self.confirm_button = Button(
            label="Confirm",
            style=ButtonStyle.success,
            disabled=self.prompt.buttons_disabled
        )
        self.cancel_button = Button(
            label="Cancel",
            style=ButtonStyle.danger,
            disabled=self.prompt.buttons_disabled
        )

        # Setting callbacks and adding buttons to the view
        self.confirm_button.callback = self.confirm_callback
        self.cancel_button.callback = self.cancel_callback
        self.add_item(self.confirm_button)
        self.add_item(self.cancel_button)

    # Defining our callbacks
    async def confirm_callback(self, interaction: Interaction):
        """
        Handles the confirm button click.
        """
        # Skipping if a second button press happens
        if self.prompt.buttons_disabled:
            return

        self.disable_buttons()
        self.prompt.status = self.prompt.status_confirmed_msg
        await self.refresh(interaction)
        await self.prompt.on_confirm_callback(interaction)

    async def cancel_callback(self, interaction: Interaction):
        """
        Handles the cancel button click.
        """
        # Skipping if a second button press happens
        if self.prompt.buttons_disabled:
            return

        self.disable_buttons()
        self.prompt.status = self.prompt.status_cancelled_msg
        await self.refresh(interaction)

        # Sometimes we may not have anything to do on cancel
        if self.prompt.on_cancel_callback:
            await self.prompt.on_cancel_callback(interaction)

    async def on_timeout(self):
        """
        Handles the timeout by disabling buttons and updating the status.
        """
        # Skipping if the button has already been pressed
        if self.prompt.buttons_disabled:
            return

        # Disabling everything and updating the message
        self.disable_buttons()
        self.prompt.status = "⏰ Timed out. Please try again."
        if self.prompt.message:
            await self.prompt.message.edit(content=self.prompt.get_message(), view=self)

    def disable_buttons(self):
        """
        Disables the confirm and cancel buttons to prevent further interaction.        
        """
        self.prompt.buttons_disabled = True
        self.confirm_button.disabled = True
        self.cancel_button.disabled = True

    async def refresh(self, interaction: Interaction):
        """
        Refreshes the message to show updated status and button states.
        """
        # Refresh the message content and view
        await interaction.response.edit_message(content=self.prompt.get_message(), view=self)
