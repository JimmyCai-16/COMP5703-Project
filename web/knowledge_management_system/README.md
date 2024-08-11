## Links
- Notion: https://www.notion.so/orefox/KMS-rebuild-Phase-One-15207f99bc114b28b487b76ab8c53578
- Scope: https://www.notion.so/orefox/Scope-dddf2ebbda2c4443b9ac8b07545708da
- Wireframe: https://lucid.app/lucidchart/426a980c-18f4-4771-8b65-0bc66132557e/edit?invitationId=inv_6439485a-e174-47d0-9837-f2ba03f719d9&page=0_0#

## App Folder (knowledge_management_system)
- `/consumers.py` \
	Web socket consumer file. Handles websocket related logic

- `/routing.py` \
	Handles websocket routes (similar to urls.py)

- `/static/js/tinymce` \
	JS library to make fancy text entry fields

- `/static/js/KMS.js` \
	handles the instantiation of the KMS websocket across the other pages. 	

- `/static/js/project.js` and `/static/js/prospect.js` \
	Specific to their dashboards. Try to keep common logic in the KMS.js (unless new pages are required that won't use them)

- `/static/templates/forms/` \
	Templates for the modalforms. They're pretty complex so separating them from the main template code was convenient

- `/static/templates/forms/widgets/` \
    Custom widgets for form inputs primarily the inline checkbox/radio button

## Next Up
These components are what need to be completed first (in no particular order) 

- Create views/routing to handle the creation/deletion/modification of entries
	- modification would likely entail a post request to the server with an ID and model type which would then populate the form as it opens
- Handle template creation/deletion/modification
	- We need a place where users can manage templates as well
	- The creation is just handled by the "Save as template?" checkbox on their respective form
- Interactive map widget displaying project area and prospect markers 
- All interactions that affect frontend need to be handled by the django channel and sent to all group members
	- e.g., user creates item, server sends item to each client to add data to the table (and wherever else data the information is required e.g., select dropdowns)
    - Test by having the page open in two separate browsers logged in with a different user each (ideally with different project permission e.g., admin and read)
- On prospect page, auto-select correct "Prospect Tags" in related forms (and gray them out to make them un-deselectable)


## Questions for Warwick (non-urgent)
These components aren't overly important right now and can be ignored until primary components are working as intended.

- How does this interact with the "Spirit" KMS that already exists?
- Importance of certain models
- Permissions for specific actions
- More websocket use-cases/optimisation
  - Are we interested in what other users on the page
  - Should there be a 'chat room'
- "Previous Exploration Reports" table contents doesn't reflect the associated upload form, need more info
	- Also what are "Downloaded PERs"
- Require more information about "Latest Report" section on lucid chart for prospect dashboard
- What is the "Personnel at site" form field meant to be.


## Thoughts/Ideas
- Predictive text for the "Report Author" or "Project Manager" fields etc. (uses an intersection of project member set as well as existing authors/managers used in other documents)

