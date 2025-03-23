# Custom libraries, their functions, and other planning info

## Planning
- ChatLLMManager.py
  - Things to consider
    - Ignore messages that have already been cached
    - If a chain does/does not exist already
      - If it does, check if parent is in middle of cache or at end
        - If at end, just append to the end of the chain
        - If in middle, create new chain taking the previous messages into the new chain
      - If it doesn't, create a new chain and add the message to the chain
