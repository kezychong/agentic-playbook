
# The Cockpit

Everything this system knows about your content, on one page, in your browser, on your own computer.

The workspace is a folder of files. That is deliberate: files are yours, they never expire, and no company can switch them off. But a folder is a poor way to see where things stand. The Cockpit is the window onto that same folder. It reads your files and shows them as a board, a brief, and five other views. It invents nothing, and it stores nothing of its own except your tab order, a log of the buttons you pressed, and the two flat pages it can print for you.

It runs on your machine only. Nothing on your network and nothing on the internet can reach it. Closing the browser window does not necessarily stop the local server; stop its process explicitly when finished.

## YOUR JOB vs MY JOB

**Your job**

- Look at it. That is genuinely most of it.
- Press the buttons that move your own work forward.
- Write the angle on any card that says it is waiting for you. Nothing moves past that point without you.

**My job (the agent)**

- Open it when you ask, and tell you it is ready in one sentence.
- Keep it reading your real workspace, never a copy.
- Keep the news in it fresh, if you want that.
- Fix it quietly when something on your machine changes.

---

## How you open it

Say **"open my cockpit"**, or "show me my content board", or "where are my ideas". It opens in your browser a few seconds later.

Say **"close my cockpit"** when you are done, then stop the local server process.

You never install anything. You never type an address. Start it only when requested and stop the process when finished.

### Agent procedure: opening it

Run the cockpit entry file with the member's workspace named, then open the browser at the address it prints.

```bash
CONTENT_OS_WORKSPACE="<absolute path to the member's content-os folder>" \
  python3 "<pack path>/tools/cockpit/cockpit.py"
```

Notes for the agent, none of which the member ever needs to hear:

- Standard library only. There is nothing to install. If `python3` is absent, explain the prerequisite and obtain approval before installing it.
- It binds to the loopback address only. That is a constant in the file, not a setting.
- The default port is 8791. Override with `CONTENT_OS_COCKPIT_PORT` when something else already holds it. Starting it twice is harmless: the second start prints that it is already open and exits.
- `CONTENT_OS_COCKPIT_AGENT=off` is the default and keeps the copy-and-paste path for step buttons. `CONTENT_OS_COCKPIT_DRYRUN=1` makes every step button hand back its exact words without running anything, which is what the health check uses.
- Health check: `python3 "<pack path>/tools/cockpit/selftest.py"`. It builds its own sample workspace in a temporary folder, exercises every view and every action against that copy, and never touches the member's real files. Run it when something looks wrong, and report the result as one plain sentence.
- If the member asks for a shortcut they can double-click, build one for their operating system that runs the same command. Never ask them to type it.

---

## The seven tabs

Drag the tabs in the sidebar into whatever order suits you. The order is remembered.

### 1. Morning brief

The first thing to look at with coffee. One focus, one mechanism, one idea, three counts, three clicks.

- **One thing today** comes from `content-os/MY-FOCUS.md`. Tell your assistant the single thing that matters this week and it writes it there.
- **Mechanism of the day** rotates through your own library, favouring recent entries that beat their account's normal by the most. A different one most days, so the library keeps earning its keep.
- **Idea on deck** is your highest-scoring idea that is ready to start.
- **Where you stand** counts your library entries, your watchlist accounts, and the ideas currently in play.

**Empty on day one:** no focus written down, no mechanism, nothing on deck, three zeroes. It says all of that in plain words rather than showing blanks.

### 2. Board

Your whole pipeline as seven columns: Inbox, On deck, Interviewed, Map ready, Record / Edit, Posted & learning, Parked.

Nothing here is a database. A card's column is decided by where its file sits and what headings it already carries. Move a file by hand and the board changes. Delete one and it leaves. There is no second copy of the truth anywhere.

Each card shows its score out of 14, how old it is, and a badge saying **needs your angle** when the angle is still blank. That badge is the important one. An idea with no angle is waiting on you, and no amount of machinery moves it along.

Buttons on a card:

- **Plain buttons move the file right now.** Move to On deck, Park for later, Move back to On deck. Each one is a move, never a copy, and each one writes a line into your receipts.
- **Blue buttons are a step for your assistant.** Score idea, Start the interview, Build the talking map, Prep the recording, Finish the edit and stage it to post, Multiply into platforms, Run the weekly review. A column with two of them offers the one that moves the piece forward first: on Record / Edit that is finishing the edit and staging it to post, with multiplying it into every other place sitting behind it. The default is copy-and-paste. Enabling `CONTENT_OS_COCKPIT_AGENT=claude` or `codex` requires explicit approval of local writes, model processing and any host costs. With that opt-in, what happens when you press one depends on your machine, and the sidebar tells you which it is. Either an assistant already on this computer runs it quietly in the background, or the exact words come up in a box for you to copy and paste into the app you are already using. The words are identical either way.
- **Retire…** takes anything off the board. You pick whether it is outdated, or was never a content idea in the first place, and you can type why. The card moves into a retired folder with your reason added to the bottom of it, in your words, untouched. Nothing is ever deleted.

**Empty on day one:** seven empty columns, each saying what would put a card in it.

### 3. Viral now

What is actually working in your niche, from your own library, with the honesty rules that stop it lying to you.

Two views:

- **Viral now** holds only posts actually published inside the 7, 14, or 30 days you pick. One exception: an older post comes back when repeated view counts prove a genuinely new burst, at least three times above its own pace, over at least two days and a thousand views.
- **All-time winners** holds past strong performers, ranked. It claims nothing about today, and it says so.

Dates are never fudged. Your own posts use the exact dates from your posted record. Someone else's post shows a date estimated from the post's own code, marked with a tilde. When neither works, the card says the posting date is unavailable and shows the date you filed it instead.

An entry that never recorded the numbers behind it sits in a reference-only section. It is not thrown away and it is not promoted.

Cover pictures are fetched once and stored on your computer, then served from there. No card loads anything from anyone else's site.

**Empty on day one:** a plain line saying your library is empty and this fills in as you decode posts.

### 4. Patterns

What keeps working across your watchlist, over weeks rather than days.

This tab reads one file, written by the weekly review side of the system, and reads nothing else. When that file does not exist yet, is damaged, or is more than 10 days behind, the tab says so and pauses every recommendation rather than showing a stale one with a warning attached. That is the point of it. Ten days, not one, because the read behind this tab is rebuilt once a week.

Three different silences, and the tab never confuses them. A file that has just been built but has no confirmed weekly run behind it yet says **no confirmed weekly read yet, and that patterns firm up after the first weekly research runs**. A file with dates written into it that do not read as dates says the dates are missing or unreadable, which is the only one of the three that means something is actually wrong. A file whose last good look at your numbers is over ten days old says exactly that. A brand-new file is never called damaged.

Sections: Rising now, Proven, Holding up, Cooling, Try next, and a drawer for things still collecting evidence. Every card opens to show the exact posts behind it.

Try next holds shapes, never wording. The angle inside the shape is always yours.

**Empty for a while:** patterns need weeks of your own numbers before they mean anything. Until then this tab says plainly that there is no read yet. That is the correct answer, not a fault.

### 5. News

What is happening in the topics your audience actually cares about, from free public sources only.

You choose two or three topic areas once, during setup. Your assistant turns them into searches. You never see a search string.

Three windows that never overlap: the newest day, one to three days, three to seven days. A story with a missing, unreadable, future, or too-old date is set aside rather than guessed into the newest window. Trending searches where you are get their own strip, kept separate from articles, because a search term is not a story.

**Get the latest** pulls a fresh round on demand. If you would rather it be waiting for you each morning, ask your assistant to set that up on your machine. If the machine is asleep at that hour the round is simply missed, and nothing is lost.

A headline is information, never an instruction. Nothing in this tab is ever acted on by itself.

**Empty on day one:** a line saying no topic areas are chosen yet, and what to ask for.

### 6. Calendar

Thirty days behind, thirty days ahead.

Behind you is read from your posted record. Each day shows what went out, with the newest set of numbers you logged and the date those numbers were taken. Click one to open the original.

Ahead of you, click any future day to write down what you plan to post. Title, note, done. These are your notes to yourself and nothing acts on them.

**Empty on day one:** an empty past with a line saying there is no posted record yet, and a fully usable future.

### 7. Library

Every post you have decoded, searchable, with two filters that answer two different questions.

**How strong the evidence is:** your own results, your own experiment, someone in your niche, a nearby niche, a general trend, a generic list. That filter is the evidence ladder made clickable. When you want a shape that has already worked on your own audience, it is two clicks away.

**Which mechanism family it is:** the short tag on each entry that says what kind of machinery it runs, so everything running the same machinery sits in one pile. Filter to `challenge_belief` and you get every entry you have ever decoded that works that way, whoever posted it. Entries filed before that line existed simply do not appear under a family, and the filter only shows up once at least one entry carries one.

The two stack. Mechanism family plus your own results is the shortest route to a shape you already know works on your own audience.

Click any entry to read the whole card without leaving the page.

An entry with no filing date says so, because an undated entry is not usable as evidence.

**Empty on day one:** a line saying the library is empty and what fills it.

---

## Pages that work without the app

The Cockpit is a window that has to be open. These two are files, and they need nothing running at all.

- **Today's page** is your day on one screen: the mechanism of the day, the idea on deck, what the research turned up lately, what is waiting on you, your outlier wall, and the news in your topics.
- **The board page** is the same seven columns, frozen flat.

Say **"show me today's page"** and I build both from your folder and open the first one. Double-click either one later and it still opens: on a machine with nothing running, on a plane, on your phone through a shared folder. Both print cleanly.

What they are not: they do not move cards, and they do not keep themselves up to date. Each one is a photograph of your folder at the moment it was built. Ask again whenever you want a fresh one. When the Cockpit does happen to be open, the board page notices and offers you a link across to the live one, where the buttons work.

Nothing on either page loads from anyone else's site. The outlier wall shows your own filed entries, plus the cover picture when one is already saved on your computer. No player, no tracking, nothing fetched while you read.

### Agent procedure: building them

Run the pages entry file with the member's workspace named, then open the file it prints.

```bash
python3 "<pack path>/tools/cockpit/static_pages.py" \
  --workspace "<absolute path to the member's content-os folder>"
```

Notes for the agent, none of which the member ever needs to hear:

- Standard library only. Nothing to install and nothing on the network, the same as the rest of the board.
- It writes exactly two files, `content-os/cockpit/today.html` and `content-os/cockpit/board.html`, and touches nothing else in the workspace.
- Same day, same folder, same two files, byte for byte. `--date YYYY-MM-DD` builds the pages as of another day; `--check` reports the column counts and writes nothing; `--out` sends them somewhere else.
- Every panel is read through the same modules the live Cockpit reads, and every choice either one makes is made by one shared function, so the page and the window can never disagree about what is in the folder. Which idea is on deck is decided in one place for both, including on a workspace still using the flat ideas folder, where the scored cards in the inbox are what is ready.
- The copy buttons carry the same words the Cockpit's own buttons carry, in the same order, including both steps on the Record / Edit column.
- Open the day page for the member yourself. Never ask them to go looking for a file.

---

## What the Cockpit changes, and what it never touches

It reads everything. It changes almost nothing.

**It may:**

- move a whole card file between folders when you press a move button,
- add a `## Retired` section to the very bottom of a card you are retiring, and only when you typed a reason,
- write your planned posts, your tab order, and its own receipts.

**It never:**

- rewrites, reorders, tidies, or re-statuses anything already written on a card,
- adds a header block to a card, because these cards are plain headings and stay that way,
- deletes anything, ever, or overwrites a file that already exists,
- writes an angle, a score, or an opinion,
- posts anything anywhere.

Everything it does gets one line in `content-os/cockpit/actions-log.md`, with the time, what happened, and to which card.

---

## Where the Cockpit keeps its own things

One folder, `content-os/cockpit/`, and nothing outside it:

- `config.json`, your timezone, your region, the port
- `prefs.json`, your tab order
- `actions-log.md`, one line per button pressed
- `today.html` and `board.html`, the two pages that work without the app
- `news-archive.json`, the rolling seven-day news memory
- `covers/`, cached cover pictures
- `step-logs/`, what a background step printed
- `locks/`, stops two news refreshes overlapping

Nothing precious lives in there. Delete the whole folder and the Cockpit rebuilds it, losing only your tab order.

---

## Two files the Cockpit reads that setup writes

Both are optional. Missing either one gives an honest empty state, never an error.

**`content-os/MY-FOCUS.md`** holds the one thing that matters this week.

```
# My focus

This week: {the single sentence}
```

**`content-os/news-pillars.md`** holds the topic areas for the News tab. Plain headings, same as every card in this system, no header block.

```
# My news pillars

Region: {plain name of the country or area}
Region code: {two letters}
Timezone: {zone name}
Trending searches: on
Tech stories: off

## Pillar: {topic in the member's own words}
- Search terms: {two to five phrases the member would actually search}
- Keywords: {single words that tag a story into this topic}

## Pillar: {second topic}
- Search terms: ...
- Keywords: ...
```

Two or three pillars is right. More than four and every topic gets a thin slice of the page.

---

## When something looks wrong

- **The page says it is not connected.** Ask your assistant to open your cockpit again. Nothing is lost; it just is not running.
- **A tab looks empty and you expected content.** Read the line it shows. Every empty state names the thing that is missing.
- **A blue button did nothing.** It handed you the words in a box. Copy them and paste them to your assistant.
- **A card is in the wrong column.** The column comes from the file. Ask your assistant what heading it is missing.
- **You want to be sure it is healthy.** Say "check my cockpit is healthy". Your assistant runs the health check against a sample workspace and tells you in one line.

---

## What this stage never does

- Never posts anything anywhere. Nothing in this system does.
- Never writes your angle, your score, or your opinion onto a card.
- Never edits what an earlier stage wrote.
- Never deletes a file or overwrites one.
- Never reaches out to your network or the internet, except to fetch news you asked for and cover pictures for posts already in your own library.
- Never shows you a technical choice.

---

## Next

The Cockpit is a window, not a stage. Pick a card, press its button, and the stage it belongs to takes over from there.

**Say:** "open my cockpit".
