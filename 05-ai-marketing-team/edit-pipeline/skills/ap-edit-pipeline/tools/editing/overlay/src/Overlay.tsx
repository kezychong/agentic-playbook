// Overlay: the stack of layers this app draws.
//
// SEE-THROUGH by design. This composition draws only the layers, captions,
// proof images and the hook line, on a fully transparent frame. It never
// contains the master video. The app draws layers, ffmpeg does the stacking
// (composite.py lays this file over the master). Anything that is not a layer
// stays clear, so the master shows through underneath.
import React from "react";
import {AbsoluteFill} from "remotion";
import {Captions} from "./Captions";
import {ProofOverlay} from "./ProofOverlay";
import {HookText} from "./HookText";
import type {OverlayProps} from "./types";

export const Overlay: React.FC<OverlayProps> = (props) => {
  return (
    <AbsoluteFill style={{backgroundColor: "transparent"}}>
      {/* proof images sit under the text layers */}
      <ProofOverlay proof={props.proof} />

      {props.captionsEnabled ? (
        <Captions words={props.words} style={props.captionStyle} />
      ) : null}

      <HookText text={props.hookText} durationSeconds={props.hookDurationSeconds} />
    </AbsoluteFill>
  );
};
