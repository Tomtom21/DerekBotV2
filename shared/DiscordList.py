from discord.ui import Button, View
from discord import ButtonStyle
import math

class DiscordList:
    def __init__(self,
                 get_items,
                 title="List",
                 have_pages=True,
                 items_per_page=10,
                 max_size_buffer=224):
        self.get_items = get_items  # the function to get items
        self.title = title
        self.have_pages = have_pages
        self.items_per_page = items_per_page
        self.max_size_buffer = max_size_buffer  # For item_fits_discord_limit, the buffer to apply before checking size

        # State
        self.current_page = 0

        # Keeping track of buttons we're adding
        self.custom_buttons = []

        # Keeping track of updating table metadata (at top)
        self.metadata: list = []

        # Keeping track of hints
        self.hints = []

        # Other housekeeping things (30 characters)
        self.separator = "**------------------------------**\n"

    # Uses the current_page value to generate the next page
    def get_page(self):
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

    # Checking to make sure we have enough characters to put something
    def item_fits_discord_limit(self, string):
        if (len(string) + self.max_size_buffer) < 2000:
            return True
        else:
            return False

    # Adding metadata with an actively updating header
    def add_metadata(self, metadata_text, metadata_callback):
        self.metadata.append({"text": metadata_text,
                              "callback": metadata_callback})

    # Adding a hint to the bottom of the list
    def add_hint(self, text):
        self.hints.append(text)

    # Add a custom button with a callback to the list
    def add_custom_button(self, label, callback, style=ButtonStyle.secondary):
        button = Button(label=label, style=style)
        button.callback = callback
        self.custom_buttons.append(button)

    # Gets the max page based on the number of items in the list
    def get_max_page(self):
        item = self.get_items()
        max_page = math.ceil(len(item) / self.items_per_page)
        return max_page - 1

    def create_view(self):
        view = View(timeout=None)

        # Adding the first and back buttons if needed
        if self.have_pages:
            first_button = Button(label="<<", style=ButtonStyle.primary)
            back_button = Button(label="<", style=ButtonStyle.primary)

            # Defining the first and back callbacks
            async def first_callback(interaction):
                self.current_page = 0
                text = self.get_page()
                await interaction.response.edit_message(content=text)

            async def back_callback(interaction):
                self.current_page = max(0, self.current_page - 1)
                text = self.get_page()
                await interaction.response.edit_message(content=text)

            first_button.callback = first_callback
            back_button.callback = back_callback

            view.add_item(first_button)
            view.add_item(back_button)

        # Adding the custom buttons
        for button in self.custom_buttons:
            view.add_item(button)

        # Adding the next and last buttons if needed
        if self.have_pages:
            next_button = Button(label=">", style=ButtonStyle.primary)
            last_button = Button(label=">>", style=ButtonStyle.primary)

            # Defining the next and last callbacks
            async def next_callback(interaction):
                max_page = self.get_max_page()
                self.current_page = min(max_page, self.current_page + 1)
                text = self.get_page()
                await interaction.response.edit_message(content=text)

            async def last_callback(interaction):
                max_page = self.get_max_page()
                self.current_page = max_page
                text = self.get_page()
                await interaction.response.edit_message(content=text)

            next_button.callback = next_callback
            last_button.callback = last_callback

            view.add_item(next_button)
            view.add_item(last_button)

        return view
