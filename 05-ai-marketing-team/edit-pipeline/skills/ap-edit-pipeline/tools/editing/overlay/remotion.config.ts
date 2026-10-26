// Defaults for the overlay app.
//
// These only affect a preview session or a bare render with no flags. The edit
// chain (render_overlays.py) passes the codec, pixel format and profile flags
// explicitly every time, so the automated path never depends on this file. They
// are set here so that opening the app to look at a preview still gives a
// see-through result.
import {Config} from "@remotion/cli/config";

Config.setVideoImageFormat("png");
Config.setPixelFormat("yuva444p10le");
Config.setCodec("prores");
Config.setProResProfile("4444");
