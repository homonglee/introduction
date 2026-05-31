#!/usr/bin/env python3
"""
Pause Challenge Shorts Generator
YouTube Shorts용 5초 Pause Challenge 영상 자동 생성기

사용법:
    python pause_challenge_generator.py --game number --target 42
    python pause_challenge_generator.py --game fortune
    python pause_challenge_generator.py --game gauge
    python pause_challenge_generator.py --all --output-dir ./output
    python pause_challenge_generator.py --list
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

try:
    import imageio_ffmpeg
    FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_BIN = "ffmpeg"

# ============================================================
# 비디오 설정
# ============================================================
WIDTH  = 1080
HEIGHT = 1920
FPS    = 30
DURATION    = 5.0
TOTAL_FRAMES = int(FPS * DURATION)

FONT_BOLD   = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
FONT_NORMAL = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

T_INTRO_END  = 0.6
T_CYCLE_END  = 4.0
T_RESULT_END = 5.0

# ============================================================
# 색깔 게임용 컬러 데이터 (항목명 → (메인색, 어두운색))
# ============================================================
COLOR_DATA = {
    "빨간색": ((210, 45,  45),  (80, 10, 10)),
    "파란색": ((45,  90,  220), (10, 20, 90)),
    "노란색": ((240, 210, 20),  (90, 75,  5)),
    "초록색": ((40,  200, 70),  (10, 75, 20)),
    "보라색": ((160, 40,  225), (55, 10, 90)),
    "주황색": ((240, 120, 30),  (90, 40,  5)),
    "분홍색": ((240, 80,  155), (90, 18, 55)),
    "하늘색": ((70,  178, 232), (14, 58, 98)),
    "갈  색": ((140, 85,  40),  (55, 30, 10)),
    "회  색": ((155, 155, 155), (48, 48, 48)),
}

# ============================================================
# 게임 설정 (render_type: standard | gauge | color | ball | archery | memory)
# ============================================================
GAMES = {
    # ── 기존 7개 ──────────────────────────────────────────────
    "number": {
        "name": "숫자 멈추기",
        "title_line1": "숫자를",  "title_line2": "멈춰라!",
        "subtitle": "목표 숫자에서 화면을 멈추세요",
        "items": [str(i) for i in range(1, 101)],
        "item_font_size": 320,
        "bg_dark": (8, 8, 30), "bg_light": (18, 18, 60),
        "item_color": (255, 220, 40), "shadow_color": (180, 140, 0),
        "accent": (255, 80, 80),      "glow_color":   (255, 200, 0),
        "has_target": True, "target_label": "목표 숫자",
        "render_type": "standard",
    },
    "fortune": {
        "name": "운세 뽑기",
        "title_line1": "오늘의", "title_line2": "운세 뽑기!",
        "subtitle": "화면을 멈춰서 운세를 확인하세요",
        "items": ["대박운", "행  운", "사랑운", "재물운",
                  "꽝!!!",  "대  길", "소  길", "평  범",
                  "건강운", "대  흉"],
        "item_font_size": 180,
        "bg_dark": (15, 5, 35), "bg_light": (28, 10, 58),
        "item_color": (220, 170, 255), "shadow_color": (120, 60, 180),
        "accent": (255, 200, 50),       "glow_color":  (180, 100, 255),
        "has_target": False, "target_label": None,
        "render_type": "standard",
    },
    "penalty": {
        "name": "벌칙 뽑기",
        "title_line1": "랜덤", "title_line2": "벌칙 뽑기!",
        "subtitle": "멈추면 그게 당신의 벌칙!",
        "items": ["팔굽혀펴기 20개", "노래 한 소절", "애교 부리기",
                  "물 원샷!",        "댄스 한 번!",  "윙크 하기",
                  "치킨 사주기",     "라면 끓여주기", "설거지 하기",
                  "셀카 올리기"],
        "item_font_size": 110,
        "bg_dark": (30, 8, 8), "bg_light": (55, 14, 14),
        "item_color": (255, 160, 160), "shadow_color": (160, 50, 50),
        "accent": (255, 220, 50),       "glow_color":  (255, 80, 80),
        "has_target": False, "target_label": None,
        "render_type": "standard",
    },
    "menu": {
        "name": "오늘의 메뉴",
        "title_line1": "오늘의", "title_line2": "점심은?",
        "subtitle": "멈추면 오늘 메뉴 결정!",
        "items": ["김  밥", "라  면", "치  킨",
                  "피  자", "삼겹살", "초  밥",
                  "짜장면", "된장찌개", "제육볶음",
                  "돈까스", "파스타",  "햄버거"],
        "item_font_size": 140,
        "bg_dark": (8, 25, 15), "bg_light": (14, 44, 28),
        "item_color": (130, 255, 170), "shadow_color": (40, 150, 80),
        "accent": (255, 220, 50),       "glow_color":  (80, 210, 130),
        "has_target": False, "target_label": None,
        "render_type": "standard",
    },
    "gauge": {
        "name": "타이밍 게이지",
        "title_line1": "타이밍", "title_line2": "게이지!",
        "subtitle": "PERFECT 구간에서 멈추세요",
        "items": None,
        "item_font_size": 130,
        "bg_dark": (8, 8, 45), "bg_light": (14, 14, 75),
        "item_color": (50, 200, 255), "shadow_color": (0, 100, 180),
        "accent": (255, 50, 100),      "glow_color":  (0, 180, 255),
        "has_target": False, "target_label": None,
        "render_type": "gauge",
    },
    "flag": {
        "name": "국기 맞추기",
        "title_line1": "국기를", "title_line2": "찾아라!",
        "subtitle": "목표 국가의 국기에서 멈추세요",
        "items": ["한  국", "미  국", "일  본",
                  "중  국", "영  국", "프랑스",
                  "독  일", "브라질", "인  도",
                  "호  주", "캐나다", "이탈리아"],
        "item_font_size": 160,
        "bg_dark": (8, 15, 35), "bg_light": (14, 26, 60),
        "item_color": (255, 255, 255), "shadow_color": (80, 100, 160),
        "accent": (255, 200, 50),       "glow_color":  (100, 150, 255),
        "has_target": True, "target_label": "목표 국가",
        "render_type": "standard",
    },
    "mbti": {
        "name": "MBTI 뽑기",
        "title_line1": "나의", "title_line2": "MBTI는?",
        "subtitle": "화면을 멈춰서 MBTI를 확인하세요",
        "items": ["INTJ", "INTP", "ENTJ", "ENTP",
                  "INFJ", "INFP", "ENFJ", "ENFP",
                  "ISTJ", "ISFJ", "ESTJ", "ESFJ",
                  "ISTP", "ISFP", "ESTP", "ESFP"],
        "item_font_size": 240,
        "bg_dark": (10, 20, 35), "bg_light": (18, 34, 60),
        "item_color": (150, 220, 255), "shadow_color": (50, 100, 160),
        "accent": (255, 150, 50),       "glow_color":  (100, 200, 255),
        "has_target": False, "target_label": None,
        "render_type": "standard",
    },

    # ── 신규 10개 ─────────────────────────────────────────────
    "color": {
        "name": "색깔 맞추기",
        "title_line1": "색깔을", "title_line2": "맞춰라!",
        "subtitle": "목표 색깔에서 화면을 멈추세요",
        "items": list(COLOR_DATA.keys()),
        "item_font_size": 160,
        "bg_dark": (8, 8, 20), "bg_light": (20, 20, 50),
        "item_color": (255, 255, 255), "shadow_color": (0, 0, 0),
        "accent": (255, 255, 255),      "glow_color":  (220, 220, 220),
        "has_target": True, "target_label": "목표 색깔",
        "render_type": "color",
    },
    "animal": {
        "name": "동물 찾기",
        "title_line1": "동물을", "title_line2": "찾아라!",
        "subtitle": "목표 동물에서 화면을 멈추세요",
        "items": ["강아지", "고양이", "호랑이", "사  자", "코끼리",
                  "기  린", "원숭이", "토  끼", "곰   ", "여  우",
                  "늑  대", "악  어", "독수리", "상  어", "펭  귄"],
        "item_font_size": 160,
        "bg_dark": (10, 22, 8), "bg_light": (18, 40, 14),
        "item_color": (180, 255, 140), "shadow_color": (55, 100, 28),
        "accent": (255, 200, 50),       "glow_color":  (145, 220, 75),
        "has_target": True, "target_label": "목표 동물",
        "render_type": "standard",
    },
    "treasure": {
        "name": "보물 찾기",
        "title_line1": "보물을", "title_line2": "찾아라!",
        "subtitle": "멈추면 그게 당신의 운명!",
        "items": ["보물 상자", "꽝!!! 💀", "황금 열쇠",
                  "폭  탄 💣", "행운권  ✨", "꽝!!! 💀",
                  "다이아  💎", "꽝!!! 💀", "황  금 알"],
        "item_font_size": 120,
        "bg_dark": (20, 15, 5), "bg_light": (40, 28, 8),
        "item_color": (255, 215, 0), "shadow_color": (120, 90, 0),
        "accent": (255, 140, 0),     "glow_color":   (255, 200, 0),
        "has_target": False, "target_label": None,
        "render_type": "standard",
    },
    "ball": {
        "name": "공 위치 맞추기",
        "title_line1": "공을", "title_line2": "멈춰라!",
        "subtitle": "별 표시 위치에서 화면을 멈추세요",
        "items": None,
        "item_font_size": 130,
        "bg_dark": (8, 8, 30), "bg_light": (14, 14, 55),
        "item_color": (255, 220, 50), "shadow_color": (150, 130, 0),
        "accent": (255, 100, 50),      "glow_color":  (255, 200, 0),
        "has_target": False, "target_label": None,
        "render_type": "ball",
    },
    "archery": {
        "name": "양궁 과녁",
        "title_line1": "과녁", "title_line2": "정조준!",
        "subtitle": "중앙(10점)에서 화면을 멈추세요",
        "items": None,
        "item_font_size": 130,
        "bg_dark": (5, 10, 20), "bg_light": (10, 18, 38),
        "item_color": (255, 255, 255), "shadow_color": (80, 80, 80),
        "accent": (255, 60, 60),        "glow_color":  (255, 100, 100),
        "has_target": False, "target_label": None,
        "render_type": "archery",
    },
    "expression": {
        "name": "표정 맞추기",
        "title_line1": "표정을", "title_line2": "맞춰라!",
        "subtitle": "목표 표정에서 화면을 멈추세요",
        "items": ["기  쁨", "슬  픔", "화  남", "놀  람",
                  "공  포", "혐  오", "설  렘", "당  황",
                  "뿌듯함", "민  망"],
        "item_font_size": 160,
        "bg_dark": (20, 10, 30), "bg_light": (35, 18, 52),
        "item_color": (255, 230, 130), "shadow_color": (120, 100, 20),
        "accent": (255, 140, 50),       "glow_color":  (255, 210, 80),
        "has_target": True, "target_label": "목표 표정",
        "render_type": "standard",
    },
    "job": {
        "name": "직업 뽑기",
        "title_line1": "랜덤", "title_line2": "직업 뽑기!",
        "subtitle": "멈추면 그게 당신의 직업!",
        "items": ["유튜버", "의  사", "변호사", "요리사",
                  "가  수", "배  우", "선생님", "운동선수",
                  "CEO",    "개발자", "디자이너", "탐  정"],
        "item_font_size": 150,
        "bg_dark": (10, 18, 30), "bg_light": (18, 32, 55),
        "item_color": (180, 230, 255), "shadow_color": (50, 90, 130),
        "accent": (100, 200, 255),      "glow_color":  (80, 180, 255),
        "has_target": False, "target_label": None,
        "render_type": "standard",
    },
    "country": {
        "name": "여행지 뽑기",
        "title_line1": "랜덤", "title_line2": "여행지!",
        "subtitle": "멈추면 다음 여행지 결정!",
        "items": ["파  리", "도  쿄", "뉴  욕", "방  콕",
                  "발  리", "런  던", "로  마", "두바이",
                  "제  주", "바르셀로나", "시드니", "이스탄불"],
        "item_font_size": 160,
        "bg_dark": (5, 15, 30), "bg_light": (10, 28, 55),
        "item_color": (140, 220, 255), "shadow_color": (30, 80, 130),
        "accent": (80, 180, 255),       "glow_color":  (60, 160, 240),
        "has_target": False, "target_label": None,
        "render_type": "standard",
    },
    "word": {
        "name": "단어 맞추기",
        "title_line1": "단어를", "title_line2": "맞춰라!",
        "subtitle": "목표 단어에서 화면을 멈추세요",
        "items": ["사  랑", "행  복", "꿈   ", "희  망",
                  "열  정", "성  공", "자  유", "평  화",
                  "웃  음", "도  전", "믿  음", "감  사"],
        "item_font_size": 200,
        "bg_dark": (8, 5, 25), "bg_light": (15, 10, 45),
        "item_color": (200, 180, 255), "shadow_color": (80, 60, 150),
        "accent": (180, 140, 255),      "glow_color":  (160, 120, 255),
        "has_target": True, "target_label": "목표 단어",
        "render_type": "standard",
    },
    "memory": {
        "name": "기억력 게임",
        "title_line1": "기억하고", "title_line2": "찾아라!",
        "subtitle": "처음 보여준 기호를 찾아 멈추세요",
        "items": ["★", "♦", "♣", "♠", "♥",
                  "▲", "●", "■", "◆", "✿",
                  "☀", "☽", "⚡", "❄", "☁"],
        "item_font_size": 280,
        "bg_dark": (5, 5, 25), "bg_light": (10, 10, 48),
        "item_color": (255, 240, 100), "shadow_color": (130, 110, 20),
        "accent": (255, 200, 50),       "glow_color":  (255, 220, 80),
        "has_target": True, "target_label": "찾을 기호",
        "render_type": "memory",
    },
}

# ============================================================
# 폰트 로더
# ============================================================
_font_cache: dict = {}

def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _font_cache:
        path = FONT_BOLD if bold else FONT_NORMAL
        try:
            _font_cache[key] = ImageFont.truetype(path, size)
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

# ============================================================
# 배경
# ============================================================
def make_bg(cfg: dict, t: float) -> Image.Image:
    dark  = np.array(cfg["bg_dark"],  dtype=np.float32)
    light = np.array(cfg["bg_light"], dtype=np.float32)
    y = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)
    y = np.clip(y + 0.08 * math.sin(t * 2.5), 0.0, 1.0)
    cols = dark[None, :] * (1 - y[:, None]) + light[None, :] * y[:, None]
    px   = np.broadcast_to(cols[:, None, :], (HEIGHT, WIDTH, 3)).copy().astype(np.uint8)
    return Image.fromarray(px, "RGB")

def make_color_bg(color_rgb: tuple, t: float) -> Image.Image:
    dark  = np.array([max(0, int(c * 0.28)) for c in color_rgb], dtype=np.float32)
    light = np.array([min(255, int(c * 0.62)) for c in color_rgb], dtype=np.float32)
    y = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)
    y = np.clip(y + 0.08 * math.sin(t * 2.5), 0.0, 1.0)
    cols = dark[None, :] * (1 - y[:, None]) + light[None, :] * y[:, None]
    px   = np.broadcast_to(cols[:, None, :], (HEIGHT, WIDTH, 3)).copy().astype(np.uint8)
    return Image.fromarray(px, "RGB")

# ============================================================
# 파티클
# ============================================================
def draw_particles(draw: ImageDraw.ImageDraw, t: float,
                   accent: tuple, count: int = 18) -> None:
    rng = random.Random(int(t * 7))
    for _ in range(count):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        r = rng.randint(2, 7)
        blink = 0.5 + 0.5 * math.sin(t * 6 + rng.random() * 10)
        alpha = int(rng.randint(40, 120) * blink)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*accent, alpha))

# ============================================================
# 텍스트 유틸
# ============================================================
def draw_centered_text(img: Image.Image, text: str, y_center: int,
                       font, color, shadow=None, glow=None):
    draw = ImageDraw.Draw(img, "RGBA")
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (WIDTH - tw) // 2
    y = y_center - th // 2
    if glow:
        gl = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gl)
        gd.text((x, y), text, font=font, fill=(*glow, 180))
        gl = gl.filter(ImageFilter.GaussianBlur(radius=18))
        img.paste(gl, (0, 0), gl)
    if shadow:
        draw.text((x + 6, y + 8), text, font=font, fill=(*shadow, 180))
    draw.text((x, y), text, font=font, fill=color)
    return tw, th

# ============================================================
# 상단 헤더
# ============================================================
def draw_header(img: Image.Image, cfg: dict, target_text=None) -> None:
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([0, 0, WIDTH, 220], fill=(*cfg["bg_dark"], 200))
    draw.line([(0, 220), (WIDTH, 220)], fill=(*cfg["accent"], 180), width=3)
    title_font  = get_font(72)
    sub_font    = get_font(42, bold=False)
    title       = cfg["title_line1"] + " " + cfg["title_line2"]
    draw_centered_text(img, title, 90, title_font, cfg["item_color"])
    if target_text:
        draw_centered_text(img, f"{cfg['target_label']}: {target_text}",
                           170, sub_font, cfg["accent"])
    else:
        draw_centered_text(img, cfg["subtitle"], 170, sub_font, (200, 200, 200))

# ============================================================
# 하단 바
# ============================================================
def draw_bottom(img: Image.Image, cfg: dict, progress: float, cta: str = "지금 멈춰!") -> None:
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([0, HEIGHT - 220, WIDTH, HEIGHT], fill=(*cfg["bg_dark"], 210))
    draw.line([(0, HEIGHT - 220), (WIDTH, HEIGHT - 220)], fill=(*cfg["accent"], 180), width=3)
    bx, by, bw, bh = 80, HEIGHT - 190, WIDTH - 160, 22
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=11, fill=(40, 40, 60))
    fw = int(bw * min(progress, 1.0))
    if fw > 0:
        draw.rounded_rectangle([bx, by, bx + fw, by + bh], radius=11,
                                fill=(int(255 * progress), int(200 * (1 - progress)), 50))
    pulse = 0.85 + 0.15 * math.sin(progress * 20)
    cta_font = get_font(90)
    draw_centered_text(img, cta, HEIGHT - 100, cta_font,
                       (*cfg["accent"][:3], int(255 * pulse)), glow=cfg["glow_color"])

# ============================================================
# 플래시 효과
# ============================================================
def apply_flash(img: Image.Image, intensity: float) -> Image.Image:
    if intensity <= 0:
        return img
    ov = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, int(intensity * 120)))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

# ============================================================
# 인트로 프레임 (일반)
# ============================================================
def make_intro_frame(cfg: dict, t_ratio: float) -> Image.Image:
    img   = make_bg(cfg, t_ratio)
    eased = 1 - (1 - t_ratio) ** 3
    cy    = HEIGHT // 2
    tf    = get_font(160)
    sf    = get_font(70, bold=False)
    alpha = int(255 * eased)
    y1    = int(cy - 120 - (1 - eased) * 200)
    y2    = int(cy +  80 + (1 - eased) * 200)
    draw_centered_text(img, cfg["title_line1"], y1, tf,
                       (*cfg["item_color"], alpha), glow=cfg["glow_color"])
    draw_centered_text(img, cfg["title_line2"], y2, tf,
                       (*cfg["accent"],     alpha), glow=cfg["glow_color"])
    sub_y = int(cy + 260 + (1 - eased) * 150)
    draw_centered_text(img, cfg["subtitle"], sub_y, sf, (200, 200, 200))
    return img

# ============================================================
# 기억력 게임 전용 인트로 (목표 기호를 크게 보여줌)
# ============================================================
def make_memory_intro_frame(cfg: dict, target: str, t_ratio: float) -> Image.Image:
    img   = make_bg(cfg, t_ratio)
    eased = 1 - (1 - t_ratio) ** 3
    alpha = int(255 * eased)
    cy    = HEIGHT // 2
    draw_centered_text(img, "기억하세요!", cy - 340, get_font(120),
                       (*cfg["accent"], alpha), glow=cfg["glow_color"])
    draw_centered_text(img, target, cy, get_font(cfg["item_font_size"]),
                       (*cfg["item_color"], alpha),
                       shadow=cfg["shadow_color"], glow=cfg["glow_color"])
    draw_centered_text(img, "이 기호를 찾아 멈추세요!", cy + 320,
                       get_font(72, bold=False), (200, 200, 200))
    return img

# ============================================================
# 아이템 사이클 프레임 (일반)
# ============================================================
def make_cycle_frame(cfg: dict, item: str, t: float,
                     flash_intensity: float = 0.0, target=None) -> Image.Image:
    img = make_bg(cfg, t)
    draw_particles(ImageDraw.Draw(img, "RGBA"), t, cfg["accent"])
    draw_header(img, cfg, target_text=target)
    draw_centered_text(img, item, HEIGHT // 2, get_font(cfg["item_font_size"]),
                       cfg["item_color"], shadow=cfg["shadow_color"],
                       glow=cfg["glow_color"])
    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return apply_flash(img, flash_intensity)

# ============================================================
# 색깔 게임 사이클 프레임
# ============================================================
def make_color_frame(cfg: dict, item: str, t: float,
                     flash_intensity: float = 0.0, target=None) -> Image.Image:
    col_rgb, _ = COLOR_DATA.get(item, ((128, 128, 128), (40, 40, 40)))
    img        = make_color_bg(col_rgb, t)

    draw = ImageDraw.Draw(img, "RGBA")
    draw_particles(draw, t, col_rgb)

    # 색깔 스와치 직사각형 (화면 중앙 큰 영역)
    sx1, sy1 = 60, 280
    sx2, sy2 = WIDTH - 60, HEIGHT - 380
    draw.rounded_rectangle([sx1, sy1, sx2, sy2], radius=55,
                            fill=(*col_rgb, 230),
                            outline=(255, 255, 255, 100), width=5)

    # 목표 색깔 헤더 (색깔 게임용 – 배경색과 구별되게)
    draw.rectangle([0, 0, WIDTH, 220], fill=(0, 0, 0, 180))
    draw.line([(0, 220), (WIDTH, 220)], fill=(255, 255, 255, 120), width=3)
    draw_centered_text(img, cfg["title_line1"] + " " + cfg["title_line2"],
                       90, get_font(72), (255, 255, 255))
    if target:
        draw_centered_text(img, f"{cfg['target_label']}: {target}",
                           170, get_font(42, bold=False), (255, 215, 0))
    else:
        draw_centered_text(img, cfg["subtitle"], 170,
                           get_font(42, bold=False), (200, 200, 200))

    # 색깔 이름
    swatch_cy = (sy1 + sy2) // 2
    draw_centered_text(img, item, swatch_cy, get_font(cfg["item_font_size"]),
                       (255, 255, 255), shadow=(0, 0, 0))

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    # 하단 바 – 어두운 오버레이
    draw2 = ImageDraw.Draw(img, "RGBA")
    draw2.rectangle([0, HEIGHT - 220, WIDTH, HEIGHT], fill=(0, 0, 0, 180))
    draw2.line([(0, HEIGHT - 220), (WIDTH, HEIGHT - 220)],
               fill=(255, 255, 255, 100), width=3)
    bx, bw, bh = 80, WIDTH - 160, 22
    by = HEIGHT - 190
    draw2.rounded_rectangle([bx, by, bx + bw, by + bh], radius=11, fill=(40, 40, 40))
    fw = int(bw * min(progress, 1.0))
    if fw > 0:
        draw2.rounded_rectangle([bx, by, bx + fw, by + bh], radius=11,
                                 fill=(int(255 * progress), int(200 * (1 - progress)), 50))
    pulse = 0.85 + 0.15 * math.sin(progress * 20)
    draw_centered_text(img, "지금 멈춰!", HEIGHT - 100, get_font(90),
                       (255, 255, 255, int(255 * pulse)))

    return apply_flash(img, flash_intensity)

# ============================================================
# 게이지 게임 프레임
# ============================================================
def make_gauge_frame(cfg: dict, t: float) -> Image.Image:
    img  = make_bg(cfg, t)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_header(img, cfg)

    cycle_ratio = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    speed       = 1.5 + cycle_ratio * 3.0
    cursor_pos  = 0.5 + 0.48 * math.sin(t * speed * math.pi * 2)

    gx, gy, gw, gh = 80, HEIGHT // 2 - 60, WIDTH - 160, 100
    draw.rounded_rectangle([gx, gy, gx+gw, gy+gh], radius=50, fill=(20, 20, 50))

    zones = [
        (0.00, 0.25, (180, 50,  50), "MISS"),
        (0.25, 0.38, (220, 180, 30), "GOOD"),
        (0.38, 0.62, (40,  220, 80), "PERFECT"),
        (0.62, 0.75, (220, 180, 30), "GOOD"),
        (0.75, 1.00, (180, 50,  50), "MISS"),
    ]
    for s, e, col, _ in zones:
        draw.rectangle([gx + int(gw*s), gy, gx + int(gw*e), gy+gh], fill=col)
    zf = get_font(36, bold=False)
    for s, e, _, lbl in zones:
        mx = gx + int(gw * (s+e) / 2)
        bb = zf.getbbox(lbl)
        draw.text((mx - (bb[2]-bb[0])//2, gy + 32), lbl, font=zf,
                  fill=(255, 255, 255, 220))
    for s, e, _, _ in zones[:-1]:
        draw.line([(gx + int(gw*e), gy), (gx + int(gw*e), gy+gh)],
                  fill=(0, 0, 0, 150), width=3)

    cx = gx + int(gw * cursor_pos)
    draw.ellipse([cx-30, gy-30,  cx+30, gy+gh+30], fill=(255, 255, 255))
    draw.ellipse([cx-22, gy-22,  cx+22, gy+gh+22], fill=(50, 180, 255))

    zone_label = next((lbl for s, e, _, lbl in zones if s <= cursor_pos < e), "MISS")
    col_map = {"PERFECT": (40, 220, 80), "GOOD": (220, 180, 30), "MISS": (220, 60, 60)}
    draw_centered_text(img, zone_label, HEIGHT // 2 + 200, get_font(130),
                       col_map[zone_label], glow=col_map[zone_label])

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return img

# ============================================================
# 공 위치 게임 프레임
# ============================================================
def make_ball_frame(cfg: dict, t: float) -> Image.Image:
    img  = make_bg(cfg, t)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_header(img, cfg)

    cycle_ratio = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    speed       = 2.0 + cycle_ratio * 4.0
    ball_pos    = 0.5 + 0.44 * math.sin(t * speed * math.pi * 2)

    lane_y = HEIGHT // 2
    lx1, lx2 = 80, WIDTH - 80
    draw.rounded_rectangle([lx1, lane_y - 12, lx2, lane_y + 12], radius=12,
                            fill=(35, 35, 70))

    # 목표 위치 (중앙 별)
    tx = (lx1 + lx2) // 2
    draw.ellipse([tx - 50, lane_y - 50, tx + 50, lane_y + 50],
                 fill=(255, 215, 0, 80), outline=(255, 215, 0, 200), width=3)
    sf = get_font(60)
    bb = sf.getbbox("★")
    draw.text((tx - (bb[2]-bb[0])//2, lane_y - (bb[3]-bb[1])//2),
              "★", font=sf, fill=(0, 0, 0))

    # 공 글로우
    bx     = lx1 + int((lx2 - lx1) * ball_pos)
    br     = 50
    gl     = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd     = ImageDraw.Draw(gl)
    gd.ellipse([bx - br*2, lane_y - br*2, bx + br*2, lane_y + br*2],
               fill=(*cfg["glow_color"], 60))
    img.paste(gl.filter(ImageFilter.GaussianBlur(20)), (0, 0),
              gl.filter(ImageFilter.GaussianBlur(20)))

    draw2 = ImageDraw.Draw(img, "RGBA")
    draw2.ellipse([bx-br, lane_y-br, bx+br, lane_y+br],
                  fill=(255, 220, 50), outline=(255, 255, 255), width=4)

    dist = abs(ball_pos - 0.5)
    if dist < 0.05:
        msg, mc = "지금이다!", (40, 220, 80)
    elif dist < 0.15:
        msg, mc = "가까워!",   (220, 180, 30)
    else:
        msg, mc = "공이 지나간다!", (220, 80, 80)
    draw_centered_text(img, msg, HEIGHT // 2 + 220, get_font(110), mc, glow=mc)

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return img

# ============================================================
# 양궁 과녁 게임 프레임
# ============================================================
def make_archery_frame(cfg: dict, t: float) -> Image.Image:
    img  = make_bg(cfg, t)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_header(img, cfg)

    cx, cy    = WIDTH // 2, HEIGHT // 2 - 60
    cycle_ratio = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    speed       = 1.5 + cycle_ratio * 3.0
    shrink      = 1 - cycle_ratio * 0.3

    hx = int(220 * math.sin(t * speed * math.pi * 2)       * shrink)
    hy = int(160 * math.sin(t * speed * math.pi * 4 + 0.8) * shrink)
    cross_x = max(cx - 290, min(cx + 290, cx + hx))
    cross_y = max(cy - 290, min(cy + 290, cy + hy))

    # 과녁 링
    ring_defs = [
        (260, (160, 45, 45)),
        (210, (185, 75, 45)),
        (160, (35,  80, 200)),
        (110, (35,  80, 200)),
        (65,  (30, 165, 30)),
        (30,  (255, 210, 0)),
    ]
    for r, col in ring_defs:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=col,
                     outline=(255, 255, 255, 80), width=2)
    lf = get_font(34, bold=False)
    for r, lbl in [(260,"2"),(210,"4"),(160,"6"),(110,"8"),(65,"9"),(30,"10")]:
        bb = lf.getbbox(lbl)
        draw.text((cx - r + 6, cy - (bb[3]-bb[1])//2), lbl, font=lf,
                  fill=(255, 255, 255, 200))

    # 조준선 (십자)
    ll = 55
    draw.line([(cross_x - ll, cross_y), (cross_x + ll, cross_y)],
              fill=(255, 50, 50), width=4)
    draw.line([(cross_x, cross_y - ll), (cross_x, cross_y + ll)],
              fill=(255, 50, 50), width=4)
    draw.ellipse([cross_x - 22, cross_y - 22, cross_x + 22, cross_y + 22],
                 outline=(255, 50, 50), width=3)

    dist = math.hypot(cross_x - cx, cross_y - cy)
    score, sc = next(
        ((s, c) for (r, _), (s, c) in zip(
            ring_defs,
            [("10점!", (255,215,0)), ("9점", (200,165,30)),
             ("8점",  (50,170,50)),  ("6점", (50,170,50)),
             ("4점",  (50,90,200)),  ("2점", (150,50,50))]
        ) if dist <= r),
        ("2점", (150, 50, 50))
    )
    draw_centered_text(img, score, HEIGHT // 2 + 290, get_font(130), sc, glow=sc)

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return img

# ============================================================
# 결과 프레임 ("정답!" 없음)
# ============================================================
def make_result_frame(cfg: dict, result: str, t_ratio: float) -> Image.Image:
    img  = make_bg(cfg, t_ratio * 0.5 + T_CYCLE_END / DURATION)
    eased = 1 - (1 - min(t_ratio * 2.5, 1.0)) ** 3

    # 배경 글로우 원
    gr   = int(350 + 30 * math.sin(t_ratio * 6))
    gl   = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(gl)
    gd.ellipse([WIDTH//2 - gr, HEIGHT//2 - gr, WIDTH//2 + gr, HEIGHT//2 + gr],
               fill=(*cfg["glow_color"], 25))
    img.paste(gl.filter(ImageFilter.GaussianBlur(60)), (0, 0),
              gl.filter(ImageFilter.GaussianBlur(60)))

    draw_particles(ImageDraw.Draw(img, "RGBA"), t_ratio * 5, cfg["accent"], count=35)
    draw_header(img, cfg)

    # 결과 아이템 (정답 레이블 없이 바로 크게 표시)
    item_size = int(cfg["item_font_size"] * (0.7 + 0.3 * eased))
    draw_centered_text(img, result, HEIGHT // 2, get_font(item_size),
                       cfg["item_color"], shadow=cfg["shadow_color"],
                       glow=cfg["glow_color"])

    draw_centered_text(img, "댓글로 결과 알려줘! 👇",
                       HEIGHT - 310, get_font(52, bold=False), (200, 200, 200))
    draw_bottom(img, cfg, 1.0, cta="결과 확인!")
    return img

# 애니메이션 게임 (gauge / ball / archery) 결과 프레임
def make_anim_result_frame(cfg: dict, render_type: str, t_ratio: float) -> Image.Image:
    img   = make_bg(cfg, T_CYCLE_END / DURATION + t_ratio * 0.2)
    eased = 1 - (1 - min(t_ratio * 2.5, 1.0)) ** 3
    draw_particles(ImageDraw.Draw(img, "RGBA"), t_ratio * 5, cfg["accent"], count=30)
    draw_header(img, cfg)
    msgs = {
        "gauge":   ("PERFECT!", (40, 220, 80)),
        "ball":    ("도전 성공!", (255, 215, 0)),
        "archery": ("10점!!",   (255, 215, 0)),
    }
    msg, col = msgs.get(render_type, ("완료!", (255, 255, 255)))
    fs  = int(200 * (0.7 + 0.3 * eased))
    draw_centered_text(img, msg, HEIGHT // 2, get_font(fs), col, glow=col)
    draw_centered_text(img, "댓글로 결과 알려줘! 👇",
                       HEIGHT - 310, get_font(52, bold=False), (200, 200, 200))
    draw_bottom(img, cfg, 1.0, cta="도전 성공!")
    return img

# ============================================================
# 아이템 시퀀스 빌더 (점점 빠르게)
# ============================================================
def build_item_sequence(items: list, total_frames: int) -> list:
    fpi_start, fpi_end = 12, 2
    pool = items.copy()
    random.shuffle(pool)
    seq  = []
    for i in range(total_frames):
        p   = i / max(total_frames - 1, 1)
        fpi = max(1, fpi_start + (fpi_end - fpi_start) * p)
        seq.append(pool[int(i / fpi) % len(pool)])
    return seq

# ============================================================
# 메인 프레임 생성기
# ============================================================
def generate_frames(cfg: dict, result_item=None, target=None):
    rt          = cfg.get("render_type", "standard")
    is_anim     = rt in ("gauge", "ball", "archery")
    items       = cfg.get("items")

    if not is_anim and items and result_item is None:
        result_item = random.choice(items)

    frames_intro  = int(T_INTRO_END                        * FPS)
    frames_cycle  = int((T_CYCLE_END  - T_INTRO_END)       * FPS)
    frames_result = int((T_RESULT_END - T_CYCLE_END)       * FPS)

    # ── 인트로 ──────────────────────────────────────────────
    if rt == "memory":
        tgt = target or (random.choice(items) if items else "★")
        for i in range(frames_intro):
            yield make_memory_intro_frame(cfg, tgt, i / max(frames_intro - 1, 1))
    else:
        for i in range(frames_intro):
            yield make_intro_frame(cfg, i / max(frames_intro - 1, 1))

    # ── 사이클 ──────────────────────────────────────────────
    if rt == "gauge":
        for i in range(frames_cycle):
            yield make_gauge_frame(cfg, T_INTRO_END + i / FPS)
    elif rt == "ball":
        for i in range(frames_cycle):
            yield make_ball_frame(cfg, T_INTRO_END + i / FPS)
    elif rt == "archery":
        for i in range(frames_cycle):
            yield make_archery_frame(cfg, T_INTRO_END + i / FPS)
    elif rt == "color":
        seq  = build_item_sequence(items, frames_cycle)
        prev = None
        for i, item in enumerate(seq):
            t     = T_INTRO_END + i / FPS
            flash = 0.4 * (1 - i / frames_cycle * 0.5) if item != prev and i > 0 else 0.0
            yield make_color_frame(cfg, item, t, flash_intensity=flash, target=target)
            prev  = item
    else:  # standard / memory
        seq  = build_item_sequence(items, frames_cycle)
        prev = None
        for i, item in enumerate(seq):
            t     = T_INTRO_END + i / FPS
            flash = 0.4 * (1 - i / frames_cycle * 0.5) if item != prev and i > 0 else 0.0
            yield make_cycle_frame(cfg, item, t, flash_intensity=flash, target=target)
            prev  = item

    # ── 결과 ────────────────────────────────────────────────
    for i in range(frames_result):
        tr = i / max(frames_result - 1, 1)
        if is_anim:
            yield make_anim_result_frame(cfg, rt, tr)
        else:
            yield make_result_frame(cfg, result_item, tr)

# ============================================================
# ffmpeg 인코딩
# ============================================================
def encode_video(frame_generator, output_path, fps: int = FPS) -> None:
    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24", "-r", str(fps),
        "-i", "pipe:0",
        "-vcodec", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
        str(output_path),
    ]
    print(f"  인코딩: {output_path}")
    with subprocess.Popen(cmd, stdin=subprocess.PIPE,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as proc:
        for idx, frame in enumerate(frame_generator):
            proc.stdin.write(np.array(frame.convert("RGB")).tobytes())
            if (idx + 1) % 15 == 0 or idx == TOTAL_FRAMES - 1:
                print(f"\r  프레임 {idx+1}/{TOTAL_FRAMES} ({(idx+1)/TOTAL_FRAMES*100:.0f}%)",
                      end="", flush=True)
        proc.stdin.close()
        proc.wait()
    print()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 오류 (코드 {proc.returncode})")
    print(f"  완료: {output_path}")

# ============================================================
# 단일 게임 생성
# ============================================================
def generate(game_key: str, output_path=None, target=None, result=None, seed=None):
    if seed is not None:
        random.seed(seed)
    if game_key not in GAMES:
        raise ValueError(f"알 수 없는 게임: {game_key}. 지원: {list(GAMES.keys())}")

    cfg = GAMES[game_key]
    rt  = cfg.get("render_type", "standard")
    is_anim = rt in ("gauge", "ball", "archery")

    if not is_anim and cfg.get("items") and result is None:
        result = random.choice(cfg["items"])

    if cfg["has_target"] and target is None and cfg.get("items"):
        target = random.choice(cfg["items"])

    if rt == "memory" and target is None and cfg.get("items"):
        target = random.choice(cfg["items"])

    if output_path is None:
        output_path = Path(f"pause_challenge_{game_key}.mp4")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"\n[ {cfg['name']} ] 생성 중...")
    if target:  print(f"  목표: {target}")
    if result:  print(f"  결과: {result}")

    encode_video(generate_frames(cfg, result_item=result, target=target), output_path)
    return Path(output_path)

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
  python pause_challenge_generator.py --game color --target 빨간색
  python pause_challenge_generator.py --game memory
  python pause_challenge_generator.py --game archery
  python pause_challenge_generator.py --all --output-dir ./output
  python pause_challenge_generator.py --list
        """,
    )
    parser.add_argument("--game",       choices=list(GAMES.keys()))
    parser.add_argument("--target",     help="목표 항목")
    parser.add_argument("--result",     help="결과 항목 (랜덤 기본)")
    parser.add_argument("--output",     help="출력 파일명")
    parser.add_argument("--output-dir", default=".", help="출력 디렉토리")
    parser.add_argument("--seed",       type=int,    help="랜덤 시드")
    parser.add_argument("--all",        action="store_true", help="모든 게임 일괄 생성")
    parser.add_argument("--list",       action="store_true", help="게임 목록 출력")
    args = parser.parse_args()

    if args.list:
        print("\n지원하는 Pause Challenge 게임 타입:")
        for k, c in GAMES.items():
            ti = " (목표 지정 가능: --target)" if c["has_target"] else ""
            print(f"  {k:14s} - {c['name']}{ti}")
        print()
        return

    out_dir = Path(args.output_dir)

    if args.all:
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n전체 {len(GAMES)}개 게임 일괄 생성 → {out_dir}/")
        for k in GAMES:
            generate(k, output_path=out_dir / f"pause_challenge_{k}.mp4", seed=args.seed)
        print(f"\n✓ {len(GAMES)}개 영상 생성 완료!")
        return

    if not args.game:
        parser.print_help()
        sys.exit(1)

    out = args.output or out_dir / f"pause_challenge_{args.game}.mp4"
    generate(args.game, output_path=out, target=args.target,
             result=args.result, seed=args.seed)


if __name__ == "__main__":
    main()
