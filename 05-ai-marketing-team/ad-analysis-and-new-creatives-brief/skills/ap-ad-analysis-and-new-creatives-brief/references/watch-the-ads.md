# Watch the ads

This file is for the agent. The owner never runs any of it.

The point of this step is simple. You are going to see every ad in the account before you say a word about what to make next. Reading the ad copy is not seeing the ad. The copy is the caption. The thing that stops the scroll is the picture and the first three seconds of the video.

## Before you start

Tell the owner what is about to happen and how big it is. Something like: "I found 34 ads. I am going to download each one and watch it. I will tell you when the profiles are done."

If a tool you need is missing, install it yourself and narrate it in plain words: "setting up my video tools, about two minutes." The owner never installs anything.

Make a working folder inside their own project folder, for example `ad-review/assets/`, and keep everything there. Tell them the folder exists once, in plain words.

## Coverage rule

Coverage rule. Watch every ad that is running now, plus every ad that is off but spent enough to matter: take the top spenders until they cover about three quarters of the window's spend, or anything above the owner's threshold if they name one. Count the rest and say in one line how many were not watched and why. Never spend the run on ads that spent nothing.

## Step A. Download the assets

For every ad in the account, get the creative asset behind it:

- Image ad: the full size image file.
- Video ad: the video source file. If only a streaming link is available, download that.
- Carousel or multi card ad: every card counts as its own asset. Keep them grouped under one ad.

Name each file with the ad id so nothing gets mixed up, for example `120xxxxxx.mp4`.

If an asset will not download, note it and move on. At the end, list the ads you could not open. Never guess what an ad looked like.

## Step B. Image ads

Open the image file and look at it. Then write down what is actually there:

- Subject: who or what is in the frame.
- On-image headline: the exact words printed on the image.
- Layout: where the text sits, how much of the frame it covers.
- Style: photo, graphic, screenshot, meme, chat screenshot, before and after, product shot.
- Colour and contrast: does it read on a phone at arm's length.
- Proof elements: numbers, logos, faces, screenshots of results.
- Aspect ratio: square, portrait, story.

## Step C. Video ads

Two passes, then read them together.

**One contact sheet per ad.** Use a fresh folder for this ad and this pass, so old frames cannot enter the sheet. Set the source and output paths:

```bash
source_video="assets/120xxxxxx.mp4"
sheet_dir="frames/120xxxxxx-pass-1"
mkdir -p "$sheet_dir"
ffmpeg -hide_banner -loglevel error -y -i "$source_video" -t 4 -vf "select='isnan(prev_selected_t)+gte(t-prev_selected_t,1)',scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(ow-iw)/2:(oh-ih)/2" -frames:v 4 -fps_mode vfr "$sheet_dir/0-open-%02d.jpg"
ffmpeg -hide_banner -loglevel error -y -ss 4 -i "$source_video" -vf "select='isnan(prev_selected_t)+gte(t-prev_selected_t,5)',scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(ow-iw)/2:(oh-ih)/2" -frames:v 8 -fps_mode vfr "$sheet_dir/1-body-%02d.jpg"
ffmpeg -hide_banner -loglevel error -y -pattern_type glob -i "$sheet_dir/[01]-*.jpg" -vf "tile=4x3:nb_frames=12:color=black" -frames:v 1 "$sheet_dir/contact-sheet.png"
```

The opening has one frame per second for the first four seconds. The body starts at second four, with one frame every five seconds, capped at eight. The sorted names put the opening first. The sheet has four columns and twelve slots, 1440 by 1920 pixels. Short videos leave unused slots black. Open and read the one contact sheet, with the opening first.

**Pass 2, the audio.** Pull the audio and transcribe it with whatever transcription tool is available in the session. If none is available, install one and say so in plain words.

```bash
ffmpeg -i assets/120xxxxxx.mp4 -ar 16000 -ac 1 audio/120xxxxxx.wav
```

Keep the transcript with timestamps if the tool gives them. Timestamps let you match a spoken line to the frame it landed on.

**Read them together.** Frames plus transcript is how you understand the ad. Written words alone tell you nothing about whether the hook worked.

## What to capture from a video

- **Hook, first three seconds.** Both halves: what is on screen, and the first line spoken or printed. Write the opening line word for word.
- **Script shape.** How it moves: problem, then agitation, then method, then proof, then call to action. Or story, then turn. Or demonstration. Name the shape.
- **Visual style.** Talking head, screen recording, user generated selfie, cinematic, animated, stock, whiteboard.
- **On-screen text.** Captions burned in or not, big word callouts, subtitles.
- **Pacing.** Roughly how many cuts, and whether the pace is fast or slow.
- **Sound.** Voice only, voice over music, music only, silent with captions. Note it, because it matters later when you write prompts.
- **Length.** In seconds.
- **Call to action.** What it asks for and when it asks.

## Step D. Write one profile per ad

One profile per ad, not per concept. Variations are separate ads.

- `id`: the ad id from the account
- `name`: the ad name as it appears in the account
- `campaign` and `ad_set`: where it sits
- `format`: image or video or carousel
- `length`: seconds, for video
- `awareness`: which awareness level it speaks to (see `creative-brief-template.md` for the five)
- `concept`: a short label for the angle, for example "hidden cost of doing it yourself"
- `hook`: the opening visual and the opening line
- `script_or_copy`: the spoken script for video, the primary text for image
- `headline`: the on-image headline or the ad headline
- `primary_text`: the ad's primary text
- `visual`: your written description of what is on screen
- `sound`: voice, music, both, or none
- `cta`: the call to action
- `status`: running, off
- `performance`: spend, results, cost per result, click through rate, frequency
- `flags`: winner, fatigued, untested, or nothing yet

Winner and fatigued are judgements, so show your reason next to them. A winner is an ad producing results at a cost the owner is happy with. Fatigued is an ad whose cost per result has climbed while frequency has climbed with it.

## Rules for this step

- **Never describe an ad you did not open.** If you skipped it, list it as skipped.
- **Quote the opening line exactly.** Paraphrasing the hook loses the thing you are trying to learn.
- **One sheet per ad.** The opening is sampled every second; the rest every five. That is enough to know what the ad does.
- **Keep the files.** The downloaded assets are useful later. One clean video with no music becomes the voice reference in `generator-handoff.md`.
- **Say when you are done.** Report how many profiles you wrote and how many ads you could not open.
