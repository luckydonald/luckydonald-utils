# Todos

## For Agents
If you are an agent tasked to process/fix this file:

- Fix the outstanding issues (unchecked items) below.
- At least 1 commit (/commit-with-lplp-style) per task, possibly more where it makes sense.
- You are allowed to plan for one or more items as it makes sense.


## How to sync from CalDAV

Source: `sync_todo` MCP, calendar `TODO: Today` (`calendar_id` 7). Each item ends with its todo `uid`.
To complete one:
1. tick the box - good to squash into the code commit
2. call `mcp__sync_todo__complete_todo(calendar_id=7, uid=<uid>)`.
3. Finally call `../../../Documents/programming/Python/DockerTgBot/scripts/sync_todos.py --project luckydonaldUtils --purge-missing --purge-complete` to update this file, which may add new tasks.
   - Generally, leaving out the project is fine, too.

## Todos synced from CalDAV

- [ ] migrate to uv and modern pip deployment tech. — `todo:2075ce3d-3f78-452e-bbec-b2ed4c27d9b3`
- [ ] make packages optional to install — `todo:3cde8dfa-dd95-4c9e-95f6-f8222cccdd25`
  > - rename to ˋluckylucy.utilsˋ
  > - Either install ˋluckydonald-utilsˋ as before to get the current set (legacy)
  >   - actually this will not be updated going forward
  > - or new recursive per-module install
  >   - ˋpip install luckylucy.utils.uvicorns.log_configˋ
  >   - ˋpip install luckylucy.utils.uvicornsˋ
  >   - ˋpip install luckylucy.utilsˋ
  > - the outer ones can be just depending on all it's inner ones, keeping the uploads small.
  > - there should be some simple way to mark what should be a module
  >   - aka. how deep it should be
  >   - maybe adding ˋ__is_luckylucyutils_module__ˋ?
  >     - Please recommend better alternatives.
  > - the deployment of all subpackages shall be automated
  >   - and subpackage creation, if needed.
  > - the root ˋluckylucy.utilsˋ and each sub-package share the release versions.
  > - the imports should be analogous to the packages now, and not differ in casing or dash vs underscore.
  >   - e.g. ˋfrom luckylucy.utils.uvicorns.log_config import <something>ˋ.
