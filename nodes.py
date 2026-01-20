import os
import shutil
import subprocess
from typing import Tuple

# =========================
# Helpers
# =========================

def _find_ffmpeg(local_dir: str) -> str:
    bundled = os.path.join(local_dir, "ffmpeg", "ffmpeg")
    if os.path.isfile(bundled) and os.access(bundled, os.X_OK):
        return bundled

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    return ""

def _norm_path(p: str) -> str:
    if p is None:
        return ""
    p = str(p).strip()
    if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
        p = p[1:-1].strip()
    return p

def _is_video_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in [
        ".mp4", ".mov", ".mkv", ".webm", ".avi"
    ]


# =========================
# Node
# =========================

class FFmpegMosaicRectVideo:
    """
    入力動画に矩形モザイクを適用し、
    同一ディレクトリに *_mosaic.mp4 を出力する。
    """

    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # ★ ここが最大の修正点
                "filename": ("STRING", {
                    "default": "",
                    "multiline": False,
                }),

                # モザイク矩形（左上基準）
                "x": ("INT", {"default": 0, "min": 0}),
                "y": ("INT", {"default": 0, "min": 0}),
                "w": ("INT", {"default": 256, "min": 1}),
                "h": ("INT", {"default": 256, "min": 1}),

                "block_size": ("INT", {"default": 24, "min": 2, "max": 256}),

                "crf": ("INT", {"default": 18, "min": 0, "max": 51}),
                "preset": ([
                    "ultrafast", "superfast", "veryfast",
                    "faster", "fast", "medium",
                    "slow", "slower", "veryslow"
                ], {"default": "veryfast"}),

                "copy_audio": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("output_video_path", "ffmpeg_log")
    FUNCTION = "run"
    CATEGORY = "Video/FFmpeg"

    def run(
        self,
        filename: str,
        x: int, y: int, w: int, h: int,
        block_size: int,
        crf: int,
        preset: str,
        copy_audio: bool
    ) -> Tuple[str, str]:

        local_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg = _find_ffmpeg(local_dir)
        if not ffmpeg:
            raise RuntimeError(
                "ffmpeg が見つかりません。\n"
                "同梱(ffmpeg/ffmpeg) または PATH に ffmpeg を配置してください。"
            )

        filename = _norm_path(filename)

        # -------- 入力検証 --------
        if not filename:
            raise ValueError("filename が空です。動画ファイルのフルパスを指定してください。")

        if not os.path.isfile(filename):
            raise FileNotFoundError(f"入力動画が存在しません:\n{filename}")

        if not _is_video_file(filename):
            raise ValueError(f"動画ファイルではありません:\n{filename}")

        if w <= 0 or h <= 0:
            raise ValueError("w / h は 1 以上である必要があります。")

        # -------- 出力パス自動生成 --------
        in_dir = os.path.dirname(filename)
        base, ext = os.path.splitext(os.path.basename(filename))
        out_path = os.path.join(in_dir, f"{base}_mosaic.mp4")

        # -------- フィルタ構築 --------
        vf = (
            f"[0:v]split=2[base][tmp];"
            f"[tmp]crop={w}:{h}:{x}:{y},"
            f"scale=iw/{block_size}:ih/{block_size}:flags=neighbor,"
            f"scale=iw*{block_size}:ih*{block_size}:flags=neighbor[m];"
            f"[base][m]overlay={x}:{y}"
        )

        cmd = [
            ffmpeg, "-y",
            "-i", filename,
            "-filter_complex", vf,
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-pix_fmt", "yuv420p",
        ]

        if copy_audio:
            cmd += ["-c:a", "copy"]
        else:
            cmd += ["-an"]

        cmd.append(out_path)

        # -------- 実行 --------
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        log = proc.stdout or ""

        if proc.returncode != 0:
            raise RuntimeError(
                "ffmpeg 実行に失敗しました。\n\n"
                "===== ffmpeg log =====\n"
                + log
            )

        if not os.path.isfile(out_path):
            raise RuntimeError(
                "ffmpeg は正常終了しましたが、出力ファイルが見つかりません:\n"
                + out_path
            )

        return (out_path, log)


# =========================
# Registry
# =========================

NODE_CLASS_MAPPINGS = {
    "FFmpeg Mosaic (Rect) [Video]": FFmpegMosaicRectVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FFmpeg Mosaic (Rect) [Video]": "FFmpeg Mosaic (Rect) [Video]",
}
