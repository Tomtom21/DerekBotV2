# Command/Functionality Implementation list

### Legend
| Icon | Status                  |
|------|-------------------------|
| ✅    | Command implemented     |
| ❌    | Command not implemented |


## Commands
| Type     | Command          | Implemented |
|----------|------------------|-------------|
| AI       | add-memory       | ✅           |
| AI       | memories         | ✅           |
| AI       | remove-memory    | ✅           |
| Birthday | add-birthday     | ✅           |
| Misc     | simon-says       | ✅           |
| Misc     | magic8ball       | ✅           |
| Misc     | random-nicknames | ✅           |
| Misc     | add-nickname     | ✅           |
| Misc     | remove-nickname  | ✅           |
| Misc     | shuffle-nickname | ✅           |
| Movie    | unwatched-movies | ✅           |
| Movie    | watched-movies   | ✅           |
| Movie    | add-movie        | ✅           |
| Movie    | remove-movie     | ✅           |
| Movie    | mark-watched     | ✅           |
| Movie    | search-movie     | ✅           |
| Movie    | random-movie     | ✅           |
| TTS      | toggle-tts       | ❌           |
| TTS      | tts-language     | ❌           |
| TTS      | vckick           | ❌           |
| TTS      | vcskip           | ❌           |
| TTS      | announce-name    | ❌           |


## Operation
| Type     | Operation             | Implemented | Notes                                          | 
|----------|-----------------------|-------------|------------------------------------------------|
| General  | on_member_join        | ✅           |                                                |
| General  | on_member_remove      | ✅           |                                                |
| General  | on_message            | ⚠️          | Handles reactions ✅, AI messages, or vc-text ✅ | 
| Birthday | birthday_check_loop   | ✅           |                                                | 
| General  | cycle_statuses        | ✅           |                                                | 
| TTS      | VC Audio              | ✅           | Implemented in helper class                    |
| DB       | update_cached_info    | ⚠️          | Implemented but not running ATM                | 
| General  | on_voice_state_update | ✅           | For vc-activity updates                        | 
| General  | nickname_cycling      | ✅           | For shuffling random nicknames                 | 

## AI Tools
| Type          | Implemented |
|---------------|-------------|
| NHC Map       | ❌           |
| SPC Maps      | ✅           |
| Color Swatch  | ✅           |
| Memory Saving | ✅           |


