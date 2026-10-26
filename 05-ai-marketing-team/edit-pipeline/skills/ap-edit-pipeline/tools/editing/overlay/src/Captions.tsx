// Captions layer: word-by-word captions driven by the words JSON.
//
// A small sliding window of words sits near the bottom safe area of a vertical
// frame. The word whose time window contains the current moment is highlighted;
// the rest of the group is dimmed. This is a see-through layer, so there is no
// background on the frame itself, only a soft dark pill behind the text so it
// stays readable over any footage.
import React from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import type {CaptionStyle, CaptionWord} from "./types";

export const Captions: React.FC<{
  words: CaptionWord[];
  style: CaptionStyle;
}> = ({words, style}) => {
  const frame = useCurrentFrame();
  const {fps, height} = useVideoConfig();
  const t = frame / fps;

  if (words.length === 0) {
    return null;
  }

  // The active word is the first one whose window contains this moment.
  let activeIdx = -1;
  for (let i = 0; i < words.length; i++) {
    if (t >= words[i].start && t < words[i].end) {
      activeIdx = i;
      break;
    }
  }
  // Between words, hold the group on the most recently started word so the
  // captions do not blink out during a pause.
  if (activeIdx === -1) {
    for (let i = 0; i < words.length; i++) {
      if (words[i].start <= t) {
        activeIdx = i;
      } else {
        break;
      }
    }
  }
  if (activeIdx === -1) {
    // Before the first word: nothing to show yet.
    return null;
  }

  const groupSize = Math.max(1, style.maxWordsPerGroup);
  const groupStart = Math.floor(activeIdx / groupSize) * groupSize;
  const group = words.slice(groupStart, groupStart + groupSize);

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: style.bottomMarginPx,
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-end",
        padding: "0 8%", // side safe margin
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: `${Math.round(style.fontSizePx * 0.25)}px`,
          background: "rgba(0,0,0,0.35)",
          borderRadius: Math.round(style.fontSizePx * 0.4),
          padding: `${Math.round(style.fontSizePx * 0.3)}px ${Math.round(
            style.fontSizePx * 0.6,
          )}px`,
          maxWidth: "100%",
        }}
      >
        {group.map((w, i) => {
          const globalIdx = groupStart + i;
          const isActive = globalIdx === activeIdx;
          return (
            <span
              key={globalIdx}
              style={{
                fontFamily:
                  "'Helvetica Neue', Helvetica, Arial, sans-serif",
                fontWeight: 800,
                fontSize: style.fontSizePx,
                lineHeight: 1.1,
                color: isActive ? style.activeColor : style.inactiveColor,
                textShadow: "0 3px 12px rgba(0,0,0,0.65)",
                transform: isActive ? "scale(1.06)" : "scale(1.0)",
                transition: "transform 60ms linear",
                textTransform: "uppercase",
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
      {/* keeps the band inside the frame on very tall crops */}
      <div style={{position: "absolute", height, width: 0}} aria-hidden />
    </div>
  );
};
