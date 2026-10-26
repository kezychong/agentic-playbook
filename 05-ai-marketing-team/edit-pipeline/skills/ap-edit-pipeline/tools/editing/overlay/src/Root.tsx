import React from "react";
import {Composition, CalculateMetadataFunction} from "remotion";
import {Overlay} from "./Overlay";
import type {OverlayProps} from "./types";

// Vertical 9:16 at 30fps by default. render_overlays.py overrides the size,
// frame rate and length through the props file, and the function below picks
// those up.
const DEFAULT_FPS = 30;
const DEFAULT_WIDTH = 1080;
const DEFAULT_HEIGHT = 1920;

// These caption defaults are deliberately neutral: white for the word being
// spoken, dimmed grey for the rest. Set active_color in the manifest to the
// member's own accent colour. They must match DEFAULT_CAPTION_STYLE in
// ../props_builder.py exactly.
const defaultProps: OverlayProps = {
  fps: DEFAULT_FPS,
  width: DEFAULT_WIDTH,
  height: DEFAULT_HEIGHT,
  durationInSeconds: 3,
  hookText: "",
  hookDurationSeconds: 2,
  captionsEnabled: true,
  captionStyle: {
    fontSizePx: 72,
    activeColor: "#FFFFFF",
    inactiveColor: "#B8B8B8",
    bottomMarginPx: 320,
    maxWordsPerGroup: 4,
  },
  words: [],
  proof: [],
};

// Length and size come from the props, and the see-through export settings are
// set here too, so even a bare render gives a transparent file. The chain also
// passes those flags explicitly, so the automated path never depends on this.
const calculateMetadata: CalculateMetadataFunction<OverlayProps> = async ({
  props,
}) => {
  const fps = props.fps || DEFAULT_FPS;
  const seconds = props.durationInSeconds || 3;
  return {
    durationInFrames: Math.max(1, Math.ceil(seconds * fps)),
    fps,
    width: props.width || DEFAULT_WIDTH,
    height: props.height || DEFAULT_HEIGHT,
    defaultCodec: "prores",
    defaultVideoImageFormat: "png",
    defaultPixelFormat: "yuva444p10le",
    defaultProResProfile: "4444",
  };
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Overlay"
      component={Overlay}
      durationInFrames={90}
      fps={DEFAULT_FPS}
      width={DEFAULT_WIDTH}
      height={DEFAULT_HEIGHT}
      defaultProps={defaultProps}
      calculateMetadata={calculateMetadata}
    />
  );
};
