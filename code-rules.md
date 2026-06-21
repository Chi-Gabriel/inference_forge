# Stack

Backend(in embedding-backend).

* Python + FastAPI
* Docker
* Redis
* PyTorch
* Qwen3-VL-Embedding
* Qwen3-VL-Reranker
* FFmpeg
* No database for now

rules

* avoid crowding my code with comments

* in a file which has things that can be tuned(constants). u place them directly below imports

* The codebase should have a proper(proffessional and easy to maintain or navigate) file structure.

* all test code files goes to test/codes in root

* no database or migrations for now. If database is added later, add the migration rule then.

* use Redis for short lived jobs, queues, locks, progress, media ids, and cache metadata. Do not store large videos or huge vectors directly in Redis.

* as u work, anything tricky that was a nightmare to solve or u feel was tricky and would save someone out of this codebase(other project with almost same stack) time, mention it in `knowledge.md`. Write it in global/project-agnostic terms: extract the reusable idea/pattern, avoid local file names, app names, endpoints, or feature labels unless they are generic examples. If the note needs project-specific details, put those in the relevant `Logic/*.md`, `deployment.md`, or feature docs instead. Keep it brief without losing the useful lesson.

* Also, document your coding approach in code-vibe.md which is the coding mentality. security wise, scalling wise, gpu usage wise, batching wise, memory wise, etc. it should be brief. this will help another developer pick up from where u stopped later

* Keep deployment.md updated whenever a change needs server-side env changes, model download steps, cache setup, one-off repair commands, worker restarts, or any action needed to keep the server/app in sync with local development. Deployment notes must be grouped by date in chronological order, with the latest date at the bottom: if today's date section exists, write under it; otherwise append a new date section at the bottom.

* As u move. u document when necessary in the readme.md

* my backend app should be well organized. make use of typing and pydantic with other things to make it more maintainable and scalable.

* NB: instead of comments in code, i prefer u analize the canonical Logic folder at `Logic` and see if any feature is there related to the one u are implementing. If none, u create a new md file there to document the feature behavior and algorithm rather than adding inline comments in code. Features are broad like (OpenAI compatible embedding feature, media id feature, video embedding feature, reranking feature, etc). Logic/*.md is for product behavior, domain rules, data flow, algorithms, invariants, and important edge-case reasoning only. Do not put deployment steps, env commands, script usage, changelog notes, or implementation file inventories there. Put operational steps in deployment.md. Only mention specific files in Logic when needed to explain ownership or an algorithm boundary.

* Try to make every endpoint call as efficient as it can be and find the sweet spot between performance and maintainability.

* After reading this, analyze relevant files in `Logic` first, `knowledge.md`, `code-vibe.md`. It can guide u navigate.

* also read `remember.md`. If any note is relevant to the current work, check whether it is already done. If it is still pending, briefly bring it to my attention and propose whether to handle it now or leave it pending, with a short reason.

before implementing.

```
- When I say something should be remembered, preserved for now, revisited later, or removed after another task, record it in `remember.md`.

- In `remember.md`, group notes by date. If today’s date section does not exist, create it. Add new notes as short checklist items under today’s date.

- Do not treat `remember.md` as automatic permission to implement everything inside it. It is a reminder and decision checkpoint.

- When a remembered item is completed or no longer needed, remove it from `remember.md`.
```

* B4 building a component, service, helper, scheduler, media utility, or endpoint, check if there is a best fit available to use b4 thinking of creating one.
* Listing endpoints with no finite limit to what it can return should always be paginated.
* Anything which is a component/helper/service must have a parameter debug or equivalent debug config which on True b4 it prints anything to console. This is to avoid cluttering the console with logs.
* Design with mentality of easy scalability as a service in a bigger system.
* An example env is very important and should be updated as u add new env variables.
* test endpoints with curl
* avoid massive files.
* split files before they become difficult to navigate (extremely above 250L).

# service rules
* the embedding-service and other future services should be designed in a way they can have seperate parts or they can be ran from different gpus if multiple gpus and if possible a vram cap.
* all services must be able to cleanly batch items if possible efficiently following a pattern which should be standard to services in this project. the system should have one cache kind of system where all services can look or work with if they need
* manage jobs and status properly so client always stays updated.
* standard error response pattern should be adopted and standardized for services in this project.
* standard building ideology(high level architechtural mindset) should be standardized for all services in this project. 
* always find the best way to optimize/ ensure we use the gpu power to is full without crashes
* The HTTP API should talk to a worker/batching layer before touching GPU work.
* services are in the system which this system can decide to turn of a service -> it shouldn't be active on the api. the system has to have some kind of api layer on the services so it manages communication with the client over the internet while keeping services focused on what they are to be on.
* where we can have open ai compatible endpoints, we should see into it. you can always research so we are close to openai compatible endpoints and can extend when need be

# media rules

* Videos and other medias should get stable media ids.
* Do not make clients upload the same video repeatedly if a media id already exists.
* Do not make the server download the same video repeatedly if it is already cached.
* Hash media bytes for deduplication.
* URL downloads must have size limits, timeout limits, content-type checks, and redirect limits.
* Do not support YouTube or complex third-party extractors unless a feature document is added for it.
* Keep uploaded media, downloaded media, temp files, decoded frames, and embedding cache separate.
* Cleanup must handle expired media, failed jobs, temp files, old decoded frames, and orphaned files.
* Do not expose internal paths, stack traces, signed urls, gpu details, or secrets.



