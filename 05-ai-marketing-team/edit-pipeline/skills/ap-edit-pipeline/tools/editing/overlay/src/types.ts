// Shared types for the overlay layers.
//
// The build_input_props function in ../props_builder.py produces exactly this
// shape and hands it to the app as a props file. Keep this file and that one in
// lockstep: change a field here, change it there, and re-pin the test.

// One caption word with its absolute timing in SECONDS. Whether a word is the
// active one is worked out at render time from the current frame, not stored.
export type CaptionWord = {
  text: string;
  start: number; // seconds
  end: number; // seconds
};

export type CaptionStyle = {
  fontSizePx: number; // caption size at 1080x1920
  activeColor: string; // the word being spoken right now
  inactiveColor: string; // the other words on screen
  bottomMarginPx: number; // how far the caption band sits above the bottom edge
  maxWordsPerGroup: number; // how many words are on screen at once
};

export type ProofWindow = {
  assetPath: string; // full path to the image in the media workspace
  start: number; // seconds, when it appears
  end: number; // seconds, when it goes
  position: "top" | "center" | "bottom";
  label: string; // optional line under the image ("" means none)
};

// Exactly what the Overlay composition receives.
export type OverlayProps = {
  fps: number;
  width: number;
  height: number;
  durationInSeconds: number;

  hookText: string; // "" turns the hook layer off
  hookDurationSeconds: number; // how long the opening line stays up

  captionsEnabled: boolean;
  captionStyle: CaptionStyle;
  words: CaptionWord[];

  proof: ProofWindow[];
};
