from discord.ui import Button, View
from discord import ButtonStyle
import math


class DiscordList:
    def __init__(self,
                 get_items,
                 title="List",
                 have_pages=True,
                 items_per_page=10,
                 max_size_buffer=224,
                 add_refresh_button=False):
        """
        Initializes a DiscordList for paginated or non-paginated list.

        :param get_items: Function to retrieve the list items
        :param title: The title of the list
        :param have_pages: Whether to paginate the list
        :param items_per_page: Number of items per page
        :param max_size_buffer: Buffer for Discord message size limit
        :param add_refresh_button: Whether to add a refresh button to the view
        """
        self.get_items = get_items  # the function to get items
        self.title = title
        self.have_pages = have_pages
        self.items_per_page = items_per_page
        self.max_size_buffer = max_size_buffer  # For item_fits_discord_limit, the buffer to apply before checking size
        self.add_refresh_button = add_refresh_button

        # Pagination state
        self.current_page = 0

        # UI info
        self.custom_buttons = []
        self.metadata: list = []
        self.hints = []
        self.separator = "**------------------------------**\n"

    def get_page(self):
        """
        Generates the next page using the value of current_page.

        :return: Returns the text string for the page
        """
        # Getting updated content for the next page
        items = self.get_items()
        item_count = len(items)

        # Building out the page
        final_page = f"## **{self.title} ⸺ ({item_count})**\n"
        final_page += self.separator

        # Adding the metadata
        if self.metadata:
            for item in self.metadata:
                metadata_content = item["callback"]()
                final_page += f"{item['text']}: *{metadata_content}*\n"
            final_page += self.separator

        # Adding the individual list items. Ignore items per page if no pages
        # Add nothing found if there are no items in list
        if self.have_pages and items:
            start = self.current_page * self.items_per_page
            end = start + self.items_per_page
            for idx, item in enumerate(items[start:end], start=start):
                temp_page = final_page
                temp_page += f"`{idx+1}.` {item}\n"
                if self.item_fits_discord_limit(temp_page):
                    final_page = temp_page
                else:
                    final_page += "--*More Items Below*--\n"
                    break
        elif not self.have_pages and items:
            for idx, item in enumerate(items):
                temp_page = final_page
                temp_page += f"`{idx + 1}.` {item}\n"
                if self.item_fits_discord_limit(temp_page):
                    final_page = temp_page
                else:
                    final_page += "--*More Items Below*--\n"
                    break
        elif not items:
            final_page += "*Nothing found*\n"

        final_page += self.separator

        # Adding the hints
        if self.hints:
            for hint in self.hints:
                final_page += f"{hint}\n"

            if self.have_pages:
                final_page += self.separator

        # Adding the page
        if self.have_pages:
            final_page += f":page_facing_up: *Page {self.current_page + 1} of {max(1, self.get_max_page() + 1)}*"

        return final_page

    def item_fits_discord_limit(self, string):
        """
        Checks if a string is within the Discord character limit. Includes a buffer for extra info.

        :param string: The string to check
        :return: True if the string is within the Discord message size limits, false otherwise
        """
        if (len(string) + self.max_size_buffer) < 2000:
            return True
        else:
            return False

    def add_metadata(self, metadata_name, metadata_callback):
        """
        Adds metadata with an actively updating header to the list of metadata items to show.

        :param metadata_name: The name of the metadata item
        :param metadata_callback: The callback to update the metadata shown in the generated page
        """
        self.metadata.append({"text": metadata_name,
                              "callback": metadata_callback})

    def add_hint(self, text):
        """
        Adds a hint to the bottom of the list.

        :param text: The hint text to add
        """
        self.hints.append(text)

    def add_custom_button(self, label, callback, style=ButtonStyle.secondary):
        """
        Adds a custom button with a callback to the list of items to show in the list.

        :param label: The text for the button
        :param callback: The function to call when the button is pressed
        :param style: The style of the button
        """
        button = Button(label=label, style=style)
        button.callback = callback
        self.custom_buttons.append(button)

    def get_max_page(self):
        """
        Returns the maximum number of pages based on the number of items in the list, using max item count per page.

        :return: Max number of pages possible for the list
        """
        item = self.get_items()
        max_page = math.ceil(len(item) / self.items_per_page)
        return max_page - 1

    async def refresh_message(self, interaction):
        """
        Universal function to refresh the message with the current page and view.
        """
        text = self.get_page()
        await interaction.response.edit_message(content=text, view=self.create_view())

    def create_view(self):
        """
        Generates the view that contains any buttons the message needs.

        :return: A discord.ui view with buttons and their callbacks ready
        """
        view = View(timeout=None)

        # Adding the first and back buttons if needed
        if self.have_pages:
            first_button = Button(label="<<", style=ButtonStyle.primary)
            back_button = Button(label="<", style=ButtonStyle.primary)

            # Defining the first and back callbacks
            async def first_callback(interaction):
                self.current_page = 0
                await self.refresh_message(interaction)

            async def back_callback(interaction):
                self.current_page = max(0, self.current_page - 1)
                await self.refresh_message(interaction)

            first_button.callback = first_callback
            back_button.callback = back_callback

            view.add_item(first_button)
            view.add_item(back_button)

        # Adding the custom buttons
        for button in self.custom_buttons:
            view.add_item(button)

        # Add refresh button if requested
        if self.add_refresh_button:
            refresh_button = Button(label="Refresh", style=ButtonStyle.gray)

            async def refresh_callback(interaction):
                await self.refresh_message(interaction)

            refresh_button.callback = refresh_callback
            view.add_item(refresh_button)

        # Adding the next and last buttons if needed
        if self.have_pages:
            next_button = Button(label=">", style=ButtonStyle.primary)
            last_button = Button(label=">>", style=ButtonStyle.primary)

            # Defining the next and last callbacks
            async def next_callback(interaction):
                max_page = self.get_max_page()
                self.current_page = min(max_page, self.current_page + 1)
                await self.refresh_message(interaction)

            async def last_callback(interaction):
                max_page = self.get_max_page()
                self.current_page = max_page
                await self.refresh_message(interaction)

            next_button.callback = next_callback
            last_button.callback = last_callback

            view.add_item(next_button)
            view.add_item(last_button)

        return view
