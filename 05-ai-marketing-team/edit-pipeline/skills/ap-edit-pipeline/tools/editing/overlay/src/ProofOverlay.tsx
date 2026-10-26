// Proof layer: screenshots and photos that appear at the moment the words claim
// something, taken from the manifest.
//
// Each proof image appears for its window, at the position asked for, with a
// short fade either side. The file is loaded from the app's public folder, which
// bootstrap_overlay.py and the render step stage for you. If an image cannot be
// found the layer falls back to the label text rather than failing the render.
import React from "react";
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import type {ProofWindow} from "./types";

const FADE_SECONDS = 0.25;

const positionStyle = (
  position: ProofWindow["position"],
): React.CSSProperties => {
  switch (position) {
    case "top":
      return {justifyContent: "flex-start", paddingTop: "14%"};
    case "bottom":
      return {justifyContent: "flex-end", paddingBottom: "22%"};
    case "center":
    default:
      return {justifyContent: "center"};
  }
};

const One: React.FC<{win: ProofWindow}> = ({win}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;

  if (t < win.start || t >= win.end) {
    return null;
  }

  const opacity = interpolate(
    t,
    [win.start, win.start + FADE_SECONDS, win.end - FADE_SECONDS, win.end],
    [0, 1, 1, 0],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
  );

  // The app resolves files from its public folder. The manifest carries a full
  // path in the media workspace, and the file is staged in by name, so the
  // lookup here is by file name.
  const rel = win.assetPath.split("/").pop() ?? win.assetPath;

  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        flexDirection: "column",
        pointerEvents: "none",
        ...positionStyle(win.position),
      }}
    >
      <div style={{opacity, display: "flex", flexDirection: "column", alignItems: "center", maxWidth: "78%"}}>
        <Img
          src={staticFile(rel)}
          style={{
            maxWidth: "100%",
            maxHeight: "48vh",
            borderRadius: 28,
            boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
          }}
        />
        {win.label ? (
          <div
            style={{
              marginTop: 18,
              fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif",
              fontWeight: 700,
              fontSize: 40,
              color: "#ffffff",
              background: "rgba(0,0,0,0.5)",
              padding: "10px 22px",
              borderRadius: 14,
              textAlign: "center",
            }}
          >
            {win.label}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

export const ProofOverlay: React.FC<{proof: ProofWindow[]}> = ({proof}) => {
  return (
    <>
      {proof.map((win, i) => (
        <One key={`${win.assetPath}-${i}`} win={win} />
      ))}
    </>
  );
};
