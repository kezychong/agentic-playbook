# Cut boundaries and design checks

## Before building the cut list
Correct clear transcript mishears from context while preserving timestamps and the raw original. Ask about ambiguous words. Captions and visual decisions use only the corrected transcript.

Word timestamps locate a candidate, not a safe cut. Inspect the actual waveform and listen around each proposed seam. Use a silence map with 10 ms RMS windows and at least 120 ms of sustained silence; calibrate the threshold to this recording. A quiet voiced decay is not silence. Start outgoing padding inside the real pause and preserve incoming breath and room tone.

Listen for the completed sentence arc. If the final word still leads into another clause, restore that clause or restructure the edit. After two failed repairs at one seam, restructure instead of trimming again. Use only short anti-click fades, about 8 to 15 ms, outside voiced words. Do not create freeze frames plus artificial silence for breathing room.

## Render and inspect
The bundled renderer sorts keep windows by time. For an approved reordered story, use an order-preserving trim/concat render rather than pretending the existing renderer preserves order. Keep the original render and cut plan.

Inspect and transcribe individual clips around every seam, roughly 2.4 seconds either side. Compare words at seams to the corrected source. Whole-video transcription does not prove the joins are intact. Repeated hallucinated text requires a new transcription with previous-text conditioning disabled when the engine supports it. Confirm available flags first.

Normalize the final audio to the existing loudness target. The member still watches the whole master before exports.

## Optional design and effects
Use every picture or screenshot only once in a video. Visuals must illustrate actual spoken nouns. Correct cut timing before placing captions or overlays. For an optional generated effect, keep the speaker's face and real voice; change only one named element per brief beat. Approve the beat list and credit cost first, then approve a still before video generation. Keep paid effects optional and label their costs; the base clean cut remains local.

For a requested designed long-form cut, preserve source resolution and provide versions with and without optional b-roll. Bank approved b-roll with its origin and rights. Never upload a reference or recording without approval.
