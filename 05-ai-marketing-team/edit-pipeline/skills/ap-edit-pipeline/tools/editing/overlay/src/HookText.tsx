// Hook layer: the opening line, on screen for the first couple of seconds.
//
// Big, centred, high contrast. It springs in on the first frame and fades out at
// the end of its window. An empty hook line turns the layer off completely.
import React from "react";
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";

export const HookText: React.FC<{
  text: string;
  durationSeconds: number;
}> = ({text, durationSeconds}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  if (!text || t >= durationSeconds) {
    return null;
  }

  const enter = spring({frame, fps, config: {damping: 200}, durationInFrames: Math.round(fps * 0.4)});
  const fadeStart = Math.max(0, durationSeconds - 0.35);
  const opacity = interpolate(t, [fadeStart, durationSeconds], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "0 8%",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          opacity,
          transform: `scale(${0.9 + enter * 0.1})`,
          fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif",
          fontWeight: 900,
          fontSize: 96,
          lineHeight: 1.05,
          color: "#ffffff",
          textAlign: "center",
          textShadow: "0 6px 24px rgba(0,0,0,0.7)",
          textTransform: "uppercase",
          letterSpacing: "-0.01em",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
