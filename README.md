# comfyui-ffmpeg-mosaic

Rectangular mosaic processing for videos in ComfyUI using ffmpeg.

## Features
- Rectangular mosaic (crop -> pixelate -> overlay)
- Runs ffmpeg directly (no Video Combine required)
- Clear error handling with ffmpeg log output
- Minimal workflow

## Requirements
- ffmpeg in PATH (example: apt install -y ffmpeg)

## Install
Clone into ComfyUI custom_nodes and restart ComfyUI.

## Notes
- This repository provides rectangular mosaic only.
- Mask-based mosaic will be provided in a separate repository: comfyui-ffmpeg-mosaic-mask
