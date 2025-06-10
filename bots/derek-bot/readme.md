# Command/Functionality Implementation list

### Legend
| Icon | Status                  |
|------|-------------------------|
| ✅    | Command implemented     |
| ❌    | Command not implemented |


## Commands
| Type     | Command          | Implemented |
|----------|------------------|-------------|
| AI       | add_memory       | ✅           |
| AI       | memories         | ✅           |
| AI       | remove_memory    | ✅           |
| Birthday | add_birthday     | ✅           |
| Misc     | simon_says       | ✅           |
| Misc     | magic8ball       | ✅           |
| Misc     | random_nicknames | ✅           |
| Misc     | add_nickname     | ✅           |
| Misc     | remove_nickname  | ✅           |
| Misc     | shuffle_nickname | ✅           |
| Movie    | unwatched_movies | ✅           |
| Movie    | watched_movies   | ✅           |
| Movie    | add_movie        | ✅           |
| Movie    | remove_movie     | ✅           |
| Movie    | mark_watched     | ✅           |
| Movie    | search_movie     | ✅           |
| Movie    | random_movie     | ✅           |
| TTS      | toggle_tts       | ❌           |
| TTS      | tts_language     | ❌           |
| TTS      | vckick           | ❌           |
| TTS      | vcskip           | ❌           |
| TTS      | announce_name    | ❌           |


## Operation
| Type     | Operation             | Implemented | Notes                                      | 
|----------|-----------------------|-------------|--------------------------------------------|
| General  | on_member_join        | ❌           |                                            |
| General  | on_member_remove      | ❌           |                                            |
| General  | on_message            | ❌           | Handles reactions, AI messages, or vc-text | 
| Birthday | birthday_check_loop   | ✅           |                                            | 
| General  | cycle_statuses        | ✅           |                                            | 
| TTS      | VC Audio              | ✅           | Implemented in helper class                |
| DB       | update_cached_info    | ⚠️          | Implemented but not running ATM            | 
| General  | on_voice_state_update | ❌           | For vc-activity updates                    | 
| General  | nickname_cycling      | ✅           | For shuffling random nicknames             | 

## AI Tools
| Type         | Implemented |
|--------------|-------------|
| NHC Map      | ❌           |
| SPC Maps     | ❌           |
| Color Swatch | ❌           |


