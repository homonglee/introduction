#!/usr/bin/env python3
"""
Pause Challenge Shorts Generator
YouTube Shorts용 5초 Pause Challenge 영상 자동 생성기

사용법:
    python pause_challenge_generator.py --game number --target 42
    python pause_challenge_generator.py --game fortune
    python pause_challenge_generator.py --game penalty
    python pause_challenge_generator.py --game menu
    python pause_challenge_generator.py --game gauge
    python pause_challenge_generator.py --game flag --target "한국"
    python pause_challenge_generator.py --game mbti
    python pause_challenge_generator.py --list
    python pause_challenge_generator.py --all   # 모든 게임 타입 일괄 생성
"""

import os
import sys
import math
import random
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# imageio-ffmpeg 번들 바이너리 사용 (시스템 ffmpeg 의존성 회피)
try:
    import imageio_ffmpeg
    FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_BIN = "ffmpeg"

# ============================================================
# 비디오 설정
# ============================================================
WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION = 5.0
TOTAL_FRAMES = int(FPS * DURATION)

FONT_BOLD   = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FONT_NORMAL = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

# 페이즈 타이밍 (초)
T_INTRO_END  = 0.6   # 0.0 ~ 0.6s  : 인트로 타이틀
T_CYCLE_END  = 4.0   # 0.6 ~ 4.0s  : 빠른 아이템 사이클
T_RESULT_END = 5.0   # 4.0 ~ 5.0s  : 결과 공개

# ============================================================
# 게임 설정
# ============================================================
GAMES = {
    "number": {
        "name": "숫자 멈추기",
        "title_line1": "숫자를",
        "title_line2": "멈춰라!",
        "subtitle": "목표 숫자에서 화면을 멈추세요",
        "items": [str(i) for i in range(1, 101)],
        "item_font_size": 320,
        "bg_dark":  (8,  8,  30),
        "bg_light": (18, 18, 60),
        "item_color":   (255, 220, 40),
        "shadow_color": (180, 140, 0),
        "accent":       (255, 80,  80),
        "glow_color":   (255, 200, 0),
        "has_target": True,
        "target_label": "목표 숫자",
    },
    "fortune": {
        "name": "운세 뽑기",
        "title_line1": "오늘의",
        "title_line2": "운세 뽑기!",
        "subtitle": "화면을 멈춰서 운세를 확인하세요",
        "items": ["대박운", "행  운", "사랑운", "재물운",
                  "꽝!!!",  "대  길", "소  길", "평  범",
                  "건강운", "대  흉"],
        "item_font_size": 180,
        "bg_dark":  (15, 5,  35),
        "bg_light": (28, 10, 58),
        "item_color":   (220, 170, 255),
        "shadow_color": (120, 60,  180),
        "accent":       (255, 200, 50),
        "glow_color":   (180, 100, 255),
        "has_target": False,
        "target_label": None,
    },
    "penalty": {
        "name": "벌칙 뽑기",
        "title_line1": "랜덤",
        "title_line2": "벌칙 뽑기!",
        "subtitle": "멈추면 그게 당신의 벌칙!",
        "items": ["팔굽혀펴기 20개", "노래 한 소절", "애교 부리기",
                  "물 원샷!",       "댄스 한 번!",  "윙크 하기",
                  "치킨 사주기",    "라면 끓여주기", "설거지 하기",
                  "셀카 올리기"],
        "item_font_size": 110,
        "bg_dark":  (30, 8,  8),
        "bg_light": (55, 14, 14),
        "item_color":   (255, 160, 160),
        "shadow_color": (160, 50,  50),
        "accent":       (255, 220, 50),
        "glow_color":   (255, 80,  80),
        "has_target": False,
        "target_label": None,
    },
    "menu": {
        "name": "오늘의 메뉴",
        "title_line1": "오늘의",
        "title_line2": "점심은?",
        "subtitle": "멈추면 오늘 메뉴 결정!",
        "items": ["김  밥", "라  면", "치  킨",
                  "피  자", "삼겹살", "초  밥",
                  "짜장면", "된장찌개", "제육볶음",
                  "돈까스", "파스타",  "햄버거"],
        "item_font_size": 140,
        "bg_dark":  (8,  25, 15),
        "bg_light": (14, 44, 28),
        "item_color":   (130, 255, 170),
        "shadow_color": (40,  150, 80),
        "accent":       (255, 220, 50),
        "glow_color":   (80,  210, 130),
        "has_target": False,
        "target_label": None,
    },
    "gauge": {
        "name": "타이밍 게이지",
        "title_line1": "타이밍",
        "title_line2": "게이지!",
        "subtitle": "PERFECT 구간에서 멈추세요",
        "items": None,
        "item_font_size": 130,
        "bg_dark":  (8,  8,  45),
        "bg_light": (14, 14, 75),
        "item_color":   (50,  200, 255),
        "shadow_color": (0,   100, 180),
        "accent":       (255, 50,  100),
        "glow_color":   (0,   180, 255),
        "has_target": False,
        "target_label": None,
    },
    "flag": {
        "name": "국기 맞추기",
        "title_line1": "국기를",
        "title_line2": "찾아라!",
        "subtitle": "목표 국가의 국기에서 멈추세요",
        "items": ["한  국", "미  국", "일  본",
                  "중  국", "영  국", "프랑스",
                  "독  일", "브라질", "인  도",
                  "호  주", "캐나다", "이탈리아"],
        "item_font_size": 160,
        "bg_dark":  (8,  15, 35),
        "bg_light": (14, 26, 60),
        "item_color":   (255, 255, 255),
        "shadow_color": (80,  100, 160),
        "accent":       (255, 200, 50),
        "glow_color":   (100, 150, 255),
        "has_target": True,
        "target_label": "목표 국가",
    },
    "mbti": {
        "name": "MBTI 뽑기",
        "title_line1": "나의",
        "title_line2": "MBTI는?",
        "subtitle": "화면을 멈춰서 MBTI를 확인하세요",
        "items": ["INTJ", "INTP", "ENTJ", "ENTP",
                  "INFJ", "INFP", "ENFJ", "ENFP",
                  "ISTJ", "ISFJ", "ESTJ", "ESFJ",
                  "ISTP", "ISFP", "ESTP", "ESFP"],
        "item_font_size": 240,
        "bg_dark":  (10, 20, 35),
        "bg_light": (18, 34, 60),
        "item_color":   (150, 220, 255),
        "shadow_color": (50,  100, 160),
        "accent":       (255, 150, 50),
        "glow_color":   (100, 200, 255),
        "has_target": False,
        "target_label": None,
    },
}

# ============================================================
# 폰트 로더
# ============================================================
_font_cache = {}

def get_font(size, bold=True):
    key = (size, bold)
    if key not in _font_cache:
        path = FONT_BOLD if bold else FONT_NORMAL
        try:
            _font_cache[key] = ImageFont.truetype(path, size)
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

# ============================================================
# 배경 생성
# ============================================================
def make_bg(cfg, t):
    dark  = np.array(cfg["bg_dark"],  dtype=np.float32)
    light = np.array(cfg["bg_light"], dtype=np.float32)

    y = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)
    wave = 0.08 * math.sin(t * 2.5)
    y = np.clip(y + wave, 0.0, 1.0)

    cols = dark[None, :] * (1 - y[:, None]) + light[None, :] * y[:, None]
    px = np.broadcast_to(cols[:, None, :], (HEIGHT, WIDTH, 3)).copy().astype(np.uint8)
    return Image.fromarray(px, "RGB")

# ============================================================
# 파티클 효과
# ============================================================
def draw_particles(draw, t, accent, count=18):
    rng = random.Random(int(t * 7))
    for _ in range(count):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        r = rng.randint(2, 7)
        alpha_base = rng.randint(40, 120)
        blink = 0.5 + 0.5 * math.sin(t * 6 + rng.random() * 10)
        alpha = int(alpha_base * blink)
        col = (*accent, alpha)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=col)

# ============================================================
# 텍스트 그리기 (그림자 + 글로우)
# ============================================================
def draw_centered_text(img, text, y_center, font, color, shadow=None, glow=None):
    draw = ImageDraw.Draw(img, "RGBA")
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (WIDTH - tw) // 2
    y = y_center - th // 2

    if glow:
        # 글로우: 블러 처리된 레이어
        glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_layer)
        gd.text((x, y), text, font=font, fill=(*glow, 180))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=18))
        img.paste(glow_layer, (0, 0), glow_layer)

    if shadow:
        draw.text((x + 6, y + 8), text, font=font, fill=(*shadow, 180))

    draw.text((x, y), text, font=font, fill=color)
    return tw, th

def draw_text_box(draw, text, x, y, font, color, bg=(0,0,0,140), pad=20):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.rounded_rectangle(
        [x - pad, y - pad, x + tw + pad, y + th + pad],
        radius=16, fill=bg
    )
    draw.text((x, y), text, font=font, fill=color)
    return tw, th

# ============================================================
# 상단 헤더
# ============================================================
def draw_header(img, cfg, target_text=None):
    draw = ImageDraw.Draw(img, "RGBA")
    # 반투명 상단 배너
    draw.rectangle([0, 0, WIDTH, 220], fill=(*cfg["bg_dark"], 200))
    draw.line([(0, 220), (WIDTH, 220)], fill=(*cfg["accent"], 180), width=3)

    title_font = get_font(72)
    subtitle_font = get_font(42, bold=False)

    title = cfg["title_line1"] + " " + cfg["title_line2"]
    draw_centered_text(img, title, 90, title_font, cfg["item_color"])

    if target_text:
        label = f"{cfg['target_label']}: {target_text}"
        draw_centered_text(img, label, 170, subtitle_font, cfg["accent"])
    else:
        draw_centered_text(img, cfg["subtitle"], 170, subtitle_font, (200, 200, 200))

# ============================================================
# 하단 영역
# ============================================================
def draw_bottom(img, cfg, progress, cta="지금 멈춰!"):
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([0, HEIGHT - 220, WIDTH, HEIGHT], fill=(*cfg["bg_dark"], 210))
    draw.line([(0, HEIGHT - 220), (WIDTH, HEIGHT - 220)], fill=(*cfg["accent"], 180), width=3)

    # 프로그레스 바
    bar_x, bar_y = 80, HEIGHT - 190
    bar_w, bar_h = WIDTH - 160, 22
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                            radius=11, fill=(40, 40, 60))
    fill_w = int(bar_w * min(progress, 1.0))
    if fill_w > 0:
        r = int(255 * progress)
        g = int(200 * (1 - progress))
        draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h],
                                radius=11, fill=(r, g, 50))

    # CTA 텍스트
    cta_font = get_font(90)
    pulse = 0.85 + 0.15 * math.sin(progress * 20)
    alpha = int(255 * pulse)
    draw_centered_text(img, cta, HEIGHT - 100, cta_font,
                       (*cfg["accent"][:3], alpha), glow=cfg["glow_color"])

# ============================================================
# 아이템 변경 플래시 효과
# ============================================================
def apply_flash(img, intensity):
    if intensity <= 0:
        return img
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, int(intensity * 120)))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

# ============================================================
# 인트로 프레임
# ============================================================
def make_intro_frame(cfg, t_ratio):
    img = make_bg(cfg, t_ratio)
    draw = ImageDraw.Draw(img, "RGBA")

    # 등장 애니메이션 (위→중앙)
    eased = 1 - (1 - t_ratio) ** 3
    center_y = HEIGHT // 2

    title_font = get_font(160)
    sub_font   = get_font(70, bold=False)

    y1 = int(center_y - 120 - (1 - eased) * 200)
    y2 = int(center_y + 80  + (1 - eased) * 200)

    alpha = int(255 * eased)
    draw_centered_text(img, cfg["title_line1"], y1, title_font,
                       (*cfg["item_color"], alpha), glow=cfg["glow_color"])
    draw_centered_text(img, cfg["title_line2"], y2, title_font,
                       (*cfg["accent"],     alpha), glow=cfg["glow_color"])

    sub_y = int(center_y + 260 + (1 - eased) * 150)
    draw_centered_text(img, cfg["subtitle"], sub_y, sub_font, (200, 200, 200))
    return img

# ============================================================
# 아이템 사이클 프레임
# ============================================================
def make_cycle_frame(cfg, item, t, flash_intensity=0.0, target=None):
    img = make_bg(cfg, t)
    overlay_draw = ImageDraw.Draw(img, "RGBA")

    draw_particles(overlay_draw, t, cfg["accent"])
    draw_header(img, cfg, target_text=target)

    # 아이템 텍스트
    item_font = get_font(cfg["item_font_size"])
    draw_centered_text(img, item, HEIGHT // 2, item_font,
                       cfg["item_color"], shadow=cfg["shadow_color"],
                       glow=cfg["glow_color"])

    # 프로그레스: 사이클 구간에서 0→1
    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)

    img = apply_flash(img, flash_intensity)
    return img

# ============================================================
# 게이지 게임 프레임
# ============================================================
def make_gauge_frame(cfg, t, target_pos=0.5):
    img = make_bg(cfg, t)
    draw = ImageDraw.Draw(img, "RGBA")

    draw_header(img, cfg)

    # 속도 변화: 사이클 구간에서 점점 빨라졌다가 결과 구간에서 멈춤
    cycle_ratio = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    speed = 1.5 + cycle_ratio * 3.0
    cursor_pos = 0.5 + 0.48 * math.sin(t * speed * math.pi * 2)

    # 게이지 바
    gx, gy = 80, HEIGHT // 2 - 60
    gw, gh = WIDTH - 160, 100

    # 배경
    draw.rounded_rectangle([gx, gy, gx+gw, gy+gh], radius=50, fill=(20, 20, 50))

    # 구간 색상
    zones = [
        (0.0, 0.25,  (180, 50, 50),  "MISS"),
        (0.25, 0.38, (220, 180, 30), "GOOD"),
        (0.38, 0.62, (40, 220, 80),  "PERFECT"),
        (0.62, 0.75, (220, 180, 30), "GOOD"),
        (0.75, 1.0,  (180, 50, 50),  "MISS"),
    ]
    for (s, e, col, _) in zones:
        draw.rectangle([gx + int(gw*s), gy, gx + int(gw*e), gy+gh], fill=col)

    # 구간 레이블
    zone_font = get_font(36, bold=False)
    for (s, e, _, label) in zones:
        mid_x = gx + int(gw * (s+e) / 2)
        bbox = zone_font.getbbox(label)
        draw.text((mid_x - (bbox[2]-bbox[0])//2, gy + 32), label,
                  font=zone_font, fill=(255, 255, 255, 220))

    # 경계선
    for (s, e, _, _) in zones[:-1]:
        draw.line([(gx + int(gw*e), gy), (gx + int(gw*e), gy+gh)],
                  fill=(0,0,0,150), width=3)

    # 커서
    cx = gx + int(gw * cursor_pos)
    draw.ellipse([cx-30, gy-30, cx+30, gy+gh+30], fill=(255,255,255))
    draw.ellipse([cx-22, gy-22, cx+22, gy+gh+22], fill=(50,180,255))

    # 현재 구간 표시
    zone_label = "MISS"
    for (s, e, _, label) in zones:
        if s <= cursor_pos < e:
            zone_label = label
            break
    lbl_font = get_font(130)
    color_map = {"PERFECT": (40,220,80), "GOOD": (220,180,30), "MISS": (220,60,60)}
    draw_centered_text(img, zone_label, HEIGHT // 2 + 200, lbl_font,
                       color_map.get(zone_label, (255,255,255)),
                       glow=color_map.get(zone_label, (255,255,255)))

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return img

# ============================================================
# 결과 프레임
# ============================================================
def make_result_frame(cfg, result, t_ratio):
    img = make_bg(cfg, t_ratio * 0.5 + T_CYCLE_END / DURATION)
    draw = ImageDraw.Draw(img, "RGBA")

    # 배경 글로우 원
    glow_r = int(350 + 30 * math.sin(t_ratio * 6))
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.ellipse([WIDTH//2 - glow_r, HEIGHT//2 - glow_r,
                WIDTH//2 + glow_r, HEIGHT//2 + glow_r],
               fill=(*cfg["glow_color"], 25))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=60))
    img.paste(glow_layer, (0, 0), glow_layer)

    # 파티클 폭발
    draw_particles(ImageDraw.Draw(img, "RGBA"), t_ratio * 5, cfg["accent"], count=35)

    draw_header(img, cfg)

    # "정답!" 레이블
    ans_font = get_font(90)
    eased = 1 - (1 - min(t_ratio * 2.5, 1.0)) ** 3
    draw_centered_text(img, "정  답!", HEIGHT // 2 - 260, ans_font,
                       cfg["accent"], glow=cfg["glow_color"])

    # 결과 텍스트 (스케일 애니메이션)
    scale = 0.7 + 0.3 * eased
    item_size = int(cfg["item_font_size"] * scale)
    item_font = get_font(item_size)
    draw_centered_text(img, result, HEIGHT // 2 + 20, item_font,
                       cfg["item_color"], shadow=cfg["shadow_color"],
                       glow=cfg["glow_color"])

    # 댓글 유도
    cmt_font = get_font(52, bold=False)
    draw_centered_text(img, "댓글로 결과를 공유하세요! 👇", HEIGHT - 320, cmt_font,
                       (200, 200, 200))

    draw_bottom(img, cfg, 1.0, cta="결과 확인!")
    return img

# ============================================================
# 아이템 순서 생성 (점점 빠르게)
# ============================================================
def build_item_sequence(items, total_frames_cycle):
    frames_per_item_start = 12
    frames_per_item_end   = 2
    result = []
    item_pool = items.copy()
    random.shuffle(item_pool)

    for frame_idx in range(total_frames_cycle):
        progress = frame_idx / max(total_frames_cycle - 1, 1)
        fpi = frames_per_item_start + (frames_per_item_end - frames_per_item_start) * progress
        fpi = max(1, fpi)
        item_idx = int(frame_idx / fpi) % len(item_pool)
        result.append(item_pool[item_idx])

    return result

# ============================================================
# 메인 프레임 생성기
# ============================================================
def generate_frames(cfg, result_item=None, target=None):
    is_gauge = (cfg["items"] is None)

    if is_gauge:
        pass
    else:
        items = cfg["items"]
        if result_item is None:
            result_item = random.choice(items)

    frames_intro  = int(T_INTRO_END  * FPS)
    frames_cycle  = int((T_CYCLE_END - T_INTRO_END)  * FPS)
    frames_result = int((T_RESULT_END - T_CYCLE_END) * FPS)

    # ── 인트로 ──
    for i in range(frames_intro):
        t_ratio = i / max(frames_intro - 1, 1)
        yield make_intro_frame(cfg, t_ratio)

    # ── 사이클 ──
    if is_gauge:
        for i in range(frames_cycle):
            t = T_INTRO_END + i / FPS
            yield make_gauge_frame(cfg, t)
    else:
        seq = build_item_sequence(items, frames_cycle)
        prev_item = None
        for i, item in enumerate(seq):
            t = T_INTRO_END + i / FPS
            flash = 0.0
            if item != prev_item and i > 0:
                # 아이템 변경 시 짧은 플래시
                flash = 0.4 * (1 - i / frames_cycle * 0.5)
            yield make_cycle_frame(cfg, item, t, flash_intensity=flash,
                                   target=target)
            prev_item = item

    # ── 결과 ──
    for i in range(frames_result):
        t_ratio = i / max(frames_result - 1, 1)
        if is_gauge:
            # 게이지 게임 결과
            img = make_bg(cfg, T_CYCLE_END / DURATION)
            draw_header(img, cfg)
            res_font = get_font(180)
            draw_centered_text(img, "PERFECT!", HEIGHT // 2, res_font,
                               (40, 220, 80), glow=(40, 220, 80))
            draw_bottom(img, cfg, 1.0, cta="도전 성공!")
            yield img
        else:
            yield make_result_frame(cfg, result_item, t_ratio)

# ============================================================
# ffmpeg로 영상 인코딩
# ============================================================
def encode_video(frame_generator, output_path, fps=FPS):
    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "pipe:0",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "fast",
        "-movflags", "+faststart",
        str(output_path),
    ]

    print(f"  인코딩 시작: {output_path}")
    with subprocess.Popen(cmd, stdin=subprocess.PIPE,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as proc:
        for idx, frame in enumerate(frame_generator):
            proc.stdin.write(np.array(frame.convert("RGB")).tobytes())
            if (idx + 1) % 15 == 0 or idx == TOTAL_FRAMES - 1:
                pct = (idx + 1) / TOTAL_FRAMES * 100
                print(f"\r  프레임 {idx+1}/{TOTAL_FRAMES} ({pct:.0f}%)", end="", flush=True)
        proc.stdin.close()
        proc.wait()
    print()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 오류 (코드 {proc.returncode})")
    print(f"  완료: {output_path}")

# ============================================================
# 단일 게임 생성 진입점
# ============================================================
def generate(game_key, output_path=None, target=None, result=None, seed=None):
    if seed is not None:
        random.seed(seed)

    if game_key not in GAMES:
        raise ValueError(f"알 수 없는 게임: {game_key}. 지원: {list(GAMES.keys())}")

    cfg = GAMES[game_key]
    is_gauge = (cfg["items"] is None)

    # 결과 아이템 결정
    if not is_gauge and result is None:
        result = random.choice(cfg["items"])

    # 타겟 검증
    if cfg["has_target"] and target is None and not is_gauge:
        target = random.choice(cfg["items"])

    if output_path is None:
        output_path = Path(f"pause_challenge_{game_key}.mp4")
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n[ {cfg['name']} ] 생성 중...")
    if target:
        print(f"  목표: {target}")
    print(f"  결과: {result if not is_gauge else 'PERFECT 구간'}")

    frames = generate_frames(cfg, result_item=result, target=target)
    encode_video(frames, output_path)
    return output_path

# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts용 5초 Pause Challenge 영상 자동 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python pause_challenge_generator.py --game number --target 42
  python pause_challenge_generator.py --game fortune --output my_fortune.mp4
  python pause_challenge_generator.py --game gauge
  python pause_challenge_generator.py --game menu --result "치킨"
  python pause_challenge_generator.py --all --output-dir ./output
  python pause_challenge_generator.py --list
        """,
    )
    parser.add_argument("--game",   choices=list(GAMES.keys()), help="게임 타입")
    parser.add_argument("--target", help="목표 항목 (숫자, 국기 등 목표가 있는 게임)")
    parser.add_argument("--result", help="최종 결과 항목 (지정하지 않으면 랜덤)")
    parser.add_argument("--output", help="출력 파일명 (기본: pause_challenge_{game}.mp4)")
    parser.add_argument("--output-dir", default=".", help="출력 디렉토리")
    parser.add_argument("--seed", type=int, help="랜덤 시드 (재현 가능)")
    parser.add_argument("--all", action="store_true", help="모든 게임 타입 일괄 생성")
    parser.add_argument("--list", action="store_true", help="지원하는 게임 타입 목록")

    args = parser.parse_args()

    if args.list:
        print("\n지원하는 Pause Challenge 게임 타입:")
        for key, cfg in GAMES.items():
            target_info = f" (목표 지정 가능: --target)" if cfg["has_target"] else ""
            print(f"  {key:12s} - {cfg['name']}{target_info}")
        print()
        return

    out_dir = Path(args.output_dir)

    if args.all:
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n모든 게임 타입 일괄 생성 → {out_dir}/")
        for key in GAMES:
            out = out_dir / f"pause_challenge_{key}.mp4"
            generate(key, output_path=out, seed=args.seed)
        print(f"\n✓ {len(GAMES)}개 영상 생성 완료!")
        return

    if not args.game:
        parser.print_help()
        print("\n--game 옵션을 지정하거나 --list로 게임 목록을 확인하세요.")
        sys.exit(1)

    out_path = args.output if args.output else out_dir / f"pause_challenge_{args.game}.mp4"
    generate(args.game, output_path=out_path,
             target=args.target, result=args.result, seed=args.seed)


if __name__ == "__main__":
    main()
