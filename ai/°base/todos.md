# Todos

Source: `sync_todo` MCP, calendar `TODO: Today` (`calendar_id` 7). Each item ends with its todo `uid`.
To complete one: tick the box and call `mcp__sync_todo__complete_todo(calendar_id=7, uid=<uid>)`.

- [x] fix the codestyle not loading for /plan. — `todo:268ba6c5-56d0-4879-9a52-50c3c9ede70c`
  > Use the official anthropic skill creator skill to help you.
- [x] #base the Make sure a file mention like (@ai/somefile.txt) gets detected to not include the ).I guess the try combinations algortithm (….txt) does not exist, ….txt does exist) would work here, too. — `todo:66f35747-cd41-4646-aee5-989858265baf`
- [x] #base Allow referenced file auto-commit in more git states: — `todo:b7a5299c-3989-4bc1-bef3-b12418b8249b`
  > • for the linked file in query (@ai/whatever) detection & committing hook
  > • staged and previously commited files
  > • still must adhere to .gitignore
- [x] also link `/skill` calls to their `ai/skills/…/SKILL.md` — `todo:be604b2a-0d90-4b41-973b-d57bc48e0772`
  > • obviously the skill must exist
