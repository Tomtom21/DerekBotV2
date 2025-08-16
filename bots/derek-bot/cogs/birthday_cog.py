from discord.ext import commands
from discord import app_commands, Interaction

from shared.data_manager import DataManager
import pytz
import logging

COMMON_TIMEZONES = {
    "UTC": "Etc/UTC",
    "HST (Hawaii)": "Pacific/Honolulu",
    "AKST (Alaska)": "America/Anchorage",
    "PST (US Pacific)": "America/Los_Angeles",
    "MST (US Mountain)": "America/Denver",
    "CST (US Central)": "America/Chicago",
    "EST (US Eastern)": "America/New_York",
    "BRT (Brazil)": "America/Sao_Paulo",
    "GMT (UK)": "Europe/London",
    "WAT (West Africa)": "Africa/Lagos",
    "CET (Central Europe)": "Europe/Berlin",
    "EET (Eastern Europe)": "Europe/Bucharest",
    "MSK (Moscow)": "Europe/Moscow",
    "IST (India)": "Asia/Kolkata",
    "BST (Bangladesh)": "Asia/Dhaka",
    "ICT (Indochina)": "Asia/Bangkok",
    "CST (China)": "Asia/Shanghai",
    "JST (Japan)": "Asia/Tokyo",
    "KST (Korea)": "Asia/Seoul",
    "AWST (Australia West)": "Australia/Perth",
    "ACST (Australia Central)": "Australia/Adelaide",
    "AEST (Australia East)": "Australia/Sydney",
    "NZST (New Zealand)": "Pacific/Auckland"
}

TIMEZONE_CHOICES = [
    app_commands.Choice(name=label, value=tz)
    for label, tz in COMMON_TIMEZONES.items()
]

DEFAULT_TIMEZONE = app_commands.Choice(name="EST (US Eastern)", value="America/New_York")


class BirthdayGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data_manager = data_manager

    group = app_commands.Group(name="birthday", description="Commands for managing birthday information")

    @group.command(name="addbirthday", description="Save a birthday for Derek to remember later")
    @app_commands.describe(
        month="The month of your birthday (1-12)",
        day="The day of your birthday (1-31)",
        year="The year of your birthday (optional, 1985-2010)",
        timezone="Your timezone (optional, defaults to EST)"
    )
    @app_commands.choices(timezone=TIMEZONE_CHOICES)
    async def add_birthday(self, interaction: Interaction,
                           month: app_commands.Range[int, 1, 12],
                           day: app_commands.Range[int, 1, 31],
                           year: app_commands.Range[int, 1985, 2010] = None,
                           timezone: app_commands.Choice[str] = None):
        """
        Adds or updates a user's birthday in the database.

        :param interaction: The Discord interaction object
        :param month: The month of the birthday (1-12)
        :param day: The day of the birthday (1-31)
        :param year: The year of the birthday (optional, 1985-2010)
        :param timezone: The user's timezone (optional, defaults to EST)
        """
        await interaction.response.defer(ephemeral=True)

        self.data_manager.ensure_user_exists(interaction.user)

        # Setting a default timezone
        if not timezone:
            timezone = DEFAULT_TIMEZONE

        # Checking if the user already has a set birthday
        if any(birthday["user_id"] == interaction.user.id for birthday in self.data_manager.data.get("birthdays")):
            # If the user already has a birthday
            successfully_updated = self.data_manager.update_table_data(
                table_name="birthdays",
                match_json={"user_id": interaction.user.id},
                update_json={
                    "month": month,
                    "day": day,
                    "year": year,
                    "nickname": interaction.user.name,
                    "timezone": timezone.value
                }
            )
            if successfully_updated:
                logging.info(f"Updated birthday for user {interaction.user.name}")
                await interaction.followup.send("Your birthday has been updated!")
            else:
                logging.warning(f"Failed to update birthday for user {interaction.user.name}")
                await interaction.followup.send("`Failed to update birthday`")
        else:
            # If the user doesn't have a birthday
            successfully_added = self.data_manager.add_table_data(
                table_name="birthdays",
                json_data={
                    "month": month,
                    "day": day,
                    "year": year,
                    "user_id": interaction.user.id,
                    "nickname": interaction.user.name,
                    "timezone": timezone.value
                }
            )
            if successfully_added:
                logging.info(f"Added birthday for user {interaction.user.name}")
                await interaction.followup.send("Your birthday is saved!")
            else:
                logging.error(f"Failed to save birthday for user {interaction.user.name}")
                await interaction.followup.send("`Failed to save birthday`")
