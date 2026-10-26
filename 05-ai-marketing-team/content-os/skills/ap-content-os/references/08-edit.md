
# Edit: your recording becomes a clean master

This stage sits between **M5 Record** and **M6 Multiply**. You filmed straight
through and said your marker word every time you fumbled. Now that raw recording
becomes one clean master, and then the three sizes the platforms want. You watch it
once. That is the whole job.

**The editing itself is a separate skill.** It is called **Edit Pipeline**, it is a
free companion pack, and it does one thing extremely well: turn a talking-to-camera
recording into a clean master and the exports. Content OS does not carry that
machinery any more. It hands the job over and picks the work back up on the other
side.

**Triggers:** "edit my video", "edit my recording", "run the edit", "cut cut this
video", "clean up my take", "make my captions", "export my formats".

## What this stage does now

Three things, and nothing else.

1. **Work out which road they are on.** Do they have the Edit Pipeline skill
   installed, or not?
2. **Hand over cleanly.** If they have it, give it the recording, their marker word,
   and where this piece lives, then get out of the way.
3. **Pick the work back up.** When the master is approved and the exports exist, file
   the edit record next to the piece and point them at M6 Multiply.

## Road A: they have the Edit Pipeline skill

Hand the whole job over. Do not re-explain the edit, do not duplicate its gates, and
do not run any of it from here.

```text
Agent procedure: hand off to the companion skill

1. Gather three things from this workspace, so they never get asked twice:
   - The recording. Wherever they saved it.
   - Their marker word. It is a standing line in content-os/MY-RULES.md if they
     ever told you. "Cut cut" is the default.
   - Which piece this is: the file in content-os/scripts/ this recording came
     from, so the run folder gets the matching name and the edit record has
     somewhere tidy to land. No script file is fine, say so and carry on.
   - Any standing mishear rules in MY-RULES.md: names, product names, industry
     words the transcriber has got wrong before. These prime the transcript.

2. Invoke the Edit Pipeline skill with those. It owns everything from there:
   setting up its two free tools the first time, the transcript, the cut list
   gate, the master, the watch-through gate, the three exports, and captions if
   they are asked for.

3. Do not repeat its gates from this side and do not second-guess its cut list.
   One voice, one procedure. Two systems narrating the same edit is how a member
   loses track of who is asking them what.

4. When it hands back an approved master, do the two things below that belong to
   Content OS and nothing more.
```

**What Content OS still owns, after the master is approved:**

- **The edit record.** Append this to the piece's file in `content-os/scripts/`,
  under its own heading. Appended, never overwritten.

  ```markdown
  ## Edit record, 2026-03-14

  - Marker: cut cut, found 3 times
  - Removed: 3 attempts, 41 seconds
  - Master: 2 minutes 13 seconds, watched and approved
  - Files: ContentStudio/runs/2026-03-14-margin-mistake/
  - Note from the watch-through: keep the pause before the number, it lands better
  ```

- **The corrections loop.** If they flagged something during the watch-through, ask
  the standing question: should I remember that as a rule? On a yes it goes into
  `content-os/MY-RULES.md` with the date, and the next edit already knows. Misheard
  names are the common one.

## Road B: they do not have it yet

Say one sentence, offer one door, and never make it a hurdle. The piece gets finished
either way.

> There is a free companion pack that does the cutting for you: you film in one go,
> say your marker word when you fumble, and it hands you a clean master plus the
> three sizes. It is a separate download at
> the included `ap-edit-pipeline/` companion folder. Want to grab it, or shall I walk
> you through the cut by hand right now? Either way you finish this piece today.

- **If they want it:** they download the zip, and their agent installs it exactly
  like any other pack of ours. One line, once per machine. Then come back to Road A.
- **If they would rather not, or the machine cannot install anything:** take the
  by-hand road below immediately. Do not ask twice and do not raise it again this
  session.

### The by-hand road, in full

This is the same cut, done by hand, and it is not a lesser option. It is what people
did before any of this existed, and it works in whatever editor they already own.

Their recording has the marker word sitting right before every good take, with the
fumbled attempt just in front of it. So:

1. Open the video in an editor that shows the words as searchable text.
2. Search that text for their marker word.
3. At every hit, delete backwards: the marker word itself, plus the fumbled attempt
   in front of it, back to where they started that line.
4. What is left is a clean run of good takes in order. Nothing else to decide.

Editors that show your words as searchable text make this quick, and several popular
ones do. They are pointers, not requirements. The same search-and-delete-backwards
move works anywhere.

The longer walk-through of exactly this, in the member's own words, is **Part 5 of
`05-record.md`**. It stays in this pack for good, because a machine that cannot
install the editing tools is not a machine that cannot finish the piece.

When they have their master, come back here, file the edit record, and go to M6.

## The gates, wherever the edit happened

These do not change with the road. State them once if the member is on Road B, and
let the companion skill state them on Road A.

- **The cut list is shown before anything is cut.** They read what is going.
- **They watch the master once, all the way through.** This is the deal. The machine
  takes the hours, they keep the judgment. Nothing is exported, captioned or
  multiplied until they have watched it.
- **No watermark, no logo, no intro bumper.** Ever. That is law 4. A rival app's
  watermark burned into a video is one of the cheapest ways to get shown to fewer
  people.
- **Video files never live in `content-os/`, and never in a folder that syncs to the
  cloud.** That is law 12. Recordings and renders go in their own folder,
  `~/ContentStudio` by default, one folder per recording. What comes back in here is
  text: the edit record above, and nothing else.

## What this stage never does

- Never runs the edit itself when the companion skill is installed. It hands over.
- Never blocks the piece on a missing companion skill. Road B finishes the work.
- Never puts a video file inside `content-os/` or inside a folder that syncs to the
  cloud.
- Never decides the cut is fine. That is the member's watch-through, on either road.
- **Never posts anything anywhere.** Nothing in this system does.

## Next

You have a clean master and a transcript of what you actually said. That is exactly
what the next stage needs. Say **"multiply this"** and we move to **M6 Multiply**
(`06-multiply.md`), where one recording becomes drafts for every place you publish.
