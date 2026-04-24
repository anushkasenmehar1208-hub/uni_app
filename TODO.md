# Add Notes + Tracker to Custom Degree (/free page) - IMPLEMENTATION

**Goal:** Copy notes/tracker buttons from structured sidebar to `free_sidebar_content()` 

## Approved Plan Progress:
1. [x] Read uni_app/uni_app.py → located nav rail buttons
2. [ ] Copy buttons to `free_sidebar_content()` 
3. [ ] Add missing state vars/events if needed 
4. [ ] Test: `reflex run` → Custom → /free → buttons work
5. [ ] Mark complete + attempt_completion

**Next:** Edit uni_app.py → add:
```
_nav_rail_btn("notebook", AppState.toggle_notes_panel),
_nav_rail_btn("list_checks", rx.redirect("/tracker")),
```
after Search chats divider.

**Run after edit:** `reflex run`

