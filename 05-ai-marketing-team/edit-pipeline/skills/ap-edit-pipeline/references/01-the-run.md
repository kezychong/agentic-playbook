
# The run: your recording becomes a clean master

You filmed straight through and you said your marker word every time you fumbled.
Now I turn that raw recording into one clean master, and then into the three sizes
the platforms want. You watch it once. That is the whole job.

There is no scrubbing a timeline, no dragging clips, no hunting for the moment you
stumbled. I read every word you said, with the exact moment you said it, find your
marker word, and remove the attempt in front of each one.

**Triggers:** "edit my video", "edit my recording", "cut my video", "cut cut this
video", "run the edit", "clean up my take", "make my exports", "export my formats",
"make this tighter".

## Before I start

I need two things, and there is a third if you have it.

1. **The recording.** Point me at it, or drag it into our chat and tell me where it
   saved. Any talking-to-camera video works.
2. **Your marker word.** The word you said out loud every time you fumbled. "Cut
   cut" is the default. If you picked "snip snip", I use that. If you told me once
   before, it is already a standing line in your rules file and I read it from
   there.
3. **Where this piece belongs**, if there is a text file for it. If you run Content
   OS there is a file in `content-os/scripts/` and I append a short record of the
   edit to it. If there is no such file, I still edit, I just have nowhere tidy to
   file the record, and I say so.

If your recording has no marker word in it at all, that is fine. It means you filmed
clean, nothing gets cut, and the whole take becomes the master.

## The road I take, and the road until then

**The default is the automatic road.** I do the whole edit on this machine, for free,
and hand you a master to watch.

**Until the tools are set up, or if this machine cannot run them, there is the
by-hand road.** You open the recording in any editor that shows your words as
searchable text, you search that text for your marker word, and at every hit you
delete backwards: the marker word itself plus the fumbled attempt in front of it,
back to where you started that line. What is left is a clean run of good takes in
order. Nothing else to decide.

Editors that show your words as searchable text make this quick, and several popular
ones do. They are pointers, not requirements. The same search-and-delete-backwards
move works in whatever you already own.

That road is not a lesser option. It is the same cut done by hand, and I will walk
you through it any time the automatic road is not available.

I never give you a menu of technical choices. I tell you which road we are on and
why, in one sentence.

## First time on this machine

Two free tools get set up before the first edit, after I have told you what they are
and you have said yes. The whole procedure, the words to say, and the honest notes
about how long it takes on different machines all live in `02-setup.md`. Read that
file the first time and never again after that.

## The run, step by step

```text
Agent procedure: the edit

1. Decide where the media lives.
   Run tools/editing/media_workspace.py --workspace --create.
   Everything goes in there. Never in a folder that syncs to iCloud, Dropbox,
   OneDrive, Google Drive or Box: the tools refuse, because video files fill up
   a sync plan and slow the machine to a crawl. Never inside a content-os/
   workspace either; that one holds text.
   If their recording is sitting in a synced folder, move it across first and say
   why in one short sentence.

2. Transcribe.
   tools/editing/transcribe.py <recording> -o <run folder>/take.words.json
       --initial-prompt "<their topic, product names, industry words>"
   Priming that prompt matters. Every word may end up on screen as a caption,
   and a mishear is a typo in high definition.

3. Read the transcript before trusting it. Garbled text, repeated words, timings
   that do not advance: STOP and ask. Never build a cut on a bad transcript.

4. Build the cut list.
   tools/editing/cutcut.py <run folder>/take.words.json
       -o <run folder>/take.cuts.json --marker "<their marker>"

   How far back each marker deletes has two settings, and the wrong one throws
   away good footage. The default deletes back to the previous marker, which is
   right when they filmed the same short line over and over. Add --scope line
   when they filmed one continuous run and only redid the line they tripped on:
   then it deletes back to that line and everything good before it survives.
   The tool warns by itself when a removed piece is longer than 15 seconds,
   because one fumbled line is not 15 seconds. On that warning, build it again
   with --scope line, show them both, and recommend one in a single sentence
   with the reason. Never hand them a technical choice.

5. SHOW THEM THE CUT LIST. The tool prints it in plain words already. Read it
   out, do not summarise it away.

6. Render the master.
   tools/editing/render_cuts.py <run folder>/take.cuts.json <recording>
       -o <run folder>/master.mp4

7. Hand them the master and stop. They watch it.

8. Only after they approve:
   tools/editing/export_presets.py <run folder>/master.mp4
       --out-dir <run folder>/exports
```

### The cut list gate

Before a single frame is cut, they see what is going. It reads like this:

> I found your marker 3 times. That means 3 attempts to remove, 41 seconds in
> total.
> 1. cutting 12.4s to 21.0s: "so the thing about margins is, sorry, the thing
> about"
> 2. cutting 48.1s to 62.7s: "which means you end up, hang on, you end up"
> 3. cutting 95.0s to 112.3s: "and that is why I always tell people, no"
> What survives: 1 stretch, 132.6 seconds.

Then I wait. If anything in that list is not what they remember doing, we look before
we cut, not after.

One case matters more than the rest. If they filmed the whole middle in one
continuous run and fumbled once near the end, the plain reading of the marker would
throw away everything before the fumble. I catch that by looking at the list: a
removed piece that runs long, with more than one finished sentence in it, means they
filmed continuously. I rebuild the cut so it removes only the fumbled line, show them
both versions in plain words, and say which one I think is right and why. They still
choose.

**I stop and ask, rather than guessing, when:**

- the number of markers does not match what they remember,
- more than one stretch survives on the default setting, where only the last take
  should ever survive,
- a surviving stretch is suspiciously short,
- the transcript looks garbled.

An honest question costs a minute. A wrong cut costs the take.

### The watch-through gate

I hand over the master and I stop. They watch it once, all the way through.

This is not a formality and it is not me being careful. It is the deal. The machine
takes the hours. They keep the judgment. Nothing gets exported, captioned or passed
on until they have watched it.

If they flag something, I fix it, and then I ask the standing question: should I
remember that as a rule? On a yes it goes into their rules file with the date, and
the next edit already knows.

## Exports

After approval, three files, every time:

- **9:16, 1080x1920.** Reels, Shorts, TikTok.
- **1:1, 1080x1080.** Feed posts.
- **16:9, 1920x1080.** YouTube and anything landscape.

Each one fills the frame and crops from the centre, so nothing is squashed and there
are no black bars.

**No watermark, no logo, no intro bumper.** Ever. A rival app's watermark burned into
a video is one of the cheapest ways to get shown to fewer people.

## If they want it tighter

Sometimes the take is clean but slow. There is an optional pass that removes the long
silences.

I offer it only when they ask for tighter pacing, I run it on the master they already
approved, never on the raw recording, and I say this first:

> Automatic silence cutting is how edits get that choppy, machine-gun feel. Every
> breath disappears. It is off by default for that reason. I can run it, and then you
> watch both and pick.

Only gaps longer than about three quarters of a second are touched, and a cushion is
always left beside every word, so nothing gets clipped. Then they watch the result and
choose which version lives.

```text
Agent procedure: the tighter pass

1. Only on an approved master. Never on the raw recording.
2. tools/editing/silence_trim.py <run folder>/master.mp4
       -o <run folder>/silence.cuts.json
3. tools/editing/render_cuts.py <run folder>/silence.cuts.json
       <run folder>/master.mp4 -o <run folder>/master-tight.mp4
4. Hand them both. They pick. Never delete the one they did not pick.
```

## Captions and on-screen proof

Optional, and only on a master they have already approved. The whole procedure lives
in `03-captions.md`. Open it when they ask for captions and not before.

## Where the files live

Video files are huge, so they live in their own folder outside anything that syncs to
the cloud. `~/ContentStudio` by default, one folder per recording. I create it, I tell
them where it is once, and I never put a video anywhere near a text workspace.

What comes back out as text is one short record of the edit:

```markdown
## Edit record, 2026-03-14

- Marker: cut cut, found 3 times
- Removed: 3 attempts, 41 seconds
- Master: 2 minutes 13 seconds, watched and approved
- Files: ContentStudio/runs/2026-03-14-margin-mistake/
- Note from the watch-through: keep the pause before the number, it lands better
```

If they run Content OS, that section gets appended to the piece's own file in
`content-os/scripts/`. If they do not, it goes in `edit-record.md` inside the run
folder. Either way it is appended, never overwritten.

## Long jobs

Transcribing a long recording and rendering a long video both take real minutes. I say
how long before I start, I start it, and I tell them when it is done. I do not leave
them watching a blank screen wondering, and I do not pretend a ten minute job is
instant.

## The craft, when they want to go further

Two playbooks live in `tools/editing/playbooks/`, one for short-form and one for
long-form. They are rebuilds of proven creator workflows, in our own words, credited
generically, with the tool-specific parts replaced by principles that work with
whatever the member already owns. I read the relevant one when a member wants more
than a clean cut: caption craft, cutaways that are actually motivated, filler-word
hunting, audio levelling, graphics that are earned by the words.

Three things from them are worth saying here, because they apply to every edit:

- **Prime the transcript with their words before transcribing.** Product names,
  industry terms, the client type they say fifty times.
- **Every mishear becomes a standing rule.** When I fix a misheard word, it goes into
  their rules file under the words the transcriber gets wrong, so the same name is
  never wrong twice.
- **Even out the audio.** Clean, level audio is half of what people mean when they say
  a video looks professional. One option on the render does it.

## What this stage never does

- Never cuts before showing you the cut list.
- Never exports before you have watched the master.
- Never runs the silence pass unless you ask for it.
- Never adds captions to a master you have not approved.
- Never puts a video file inside a folder that syncs to the cloud.
- Never adds a watermark, a logo or a bumper.
- **Never posts anything anywhere.**

## Next

You have a clean master, three exports, and a transcript of what you actually said.

If you run Content OS, that is exactly what its next stage needs: say **"multiply
this"** and one recording becomes drafts for every place you publish. If you do not,
the files are in your run folder and they are yours.
