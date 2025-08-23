# DerekBotV2

DerekBotV2 represents a series of Discord bots I developed for my own personal use. Each bot has its own specific goal, whether it be providing entertainment or TTS services to a Discord server, or being my own personal assistant. They serve to automate and streamline different processes I want to handle within Discord. 

This project is a re-write of a V1 made several years ago. Enough changes were needed that it warranted a full re-write.

**Please Note:** 
<span style="color: red;">These bots were designed specifically for my own use. They rely on custom database setups and external APIs, so I'm not providing support or assistance in getting them running elsewhere at this time. You're welcome to explore the code, but they aren't intended as ready-to-use public bots.</span>


---

## Bots Overview

### 1. **Derek Bot**
A general Discord bot built for both direct user interaction and back-end support of user activities, such as entertainment or accessibility via TTS.

**Key Features:**
- **GPT-powered Conversation:** Talk with an intelligent chat bot to socialize or answer questions.
    - **AI Memory System:** Save, recall, and remove memories for personalized AI interactions.
    - **Requesting Weather Info:** Enhance conversations about weather by allowing the bot to pull NWS data.
- **Birthday Tracking:** Add and manage user birthdays. The bot wishes happy birthday to the user.
- **Movie Management:** Track watched/unwatched movies, add/remove movies, search, and randomize selections.
- **Nickname Tools:** Allow users to create a set of nicknames, so users who opt-in can have their name randomly set by the bot.
- **Miscellaneous:** Magic 8-ball, Simon Says, and more.
- **Voice Channel (VC) Audio:** TTS and VC activity tracking.
- **User State Tracking:** Discord does not track when a user leaves a Discord server. This bot provides messages to users letting them know when someone does leave.

See [`bots/derek-bot/readme.md`](bots/derek-bot/readme.md) for a full command list and implementation status.

---

### 2. **Derpods Bot**
A complex music playback bot for Discord, supporting playback of music from several sources.

**Key Features:**
- **Music Playback:** Stream music directly in Discord voice channels.
- **Intelligent Search Features:** Utilize Spotify and Youtube APIs to intelligently find audio sources.
- **Playlist Management:** Play entire playlists with ease.
- **Custom GPT Chat:** AI-powered chat interactions for music-related queries. 

---

### 3. **Luna**
A personal assistant bot to provide me with help on everyday activities, such as tracking workouts, storing recipes, and handling any other tasks I need done. This bot is in the works.

---

### 4. **Placeholder Bot**
A short term utility bot that clears out old slash commands from bots that are no longer in use. This prevents there from being several bots with identical, conflicting commands being present in the server. 

While another solution is to simply remove old bots from servers, any bots kept around for nostalgia or data purposes will need to use this bot to purge commands.

---

As I said initially, these bots were primarily created for my own use, so I'm not openly supporting any deployment, however feel free to take a look around.

