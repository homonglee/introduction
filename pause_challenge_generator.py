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
# 신규 게임용 상수 데이터
# ============================================================

# 행성 데이터
PLANET_DATA = {
    "수  성": {"col": (175, 165, 155), "r": 80,  "rings": False, "glow": (210, 200, 190)},
    "금  성": {"col": (240, 220, 130), "r": 130, "rings": False, "glow": (255, 240, 150)},
    "지  구": {"col": (45,  120, 200), "r": 140, "rings": False, "glow": (70,  150, 235)},
    "화  성": {"col": (200, 80,  50),  "r": 110, "rings": False, "glow": (235, 110, 75)},
    "목  성": {"col": (210, 170, 100), "r": 230, "rings": False, "glow": (240, 200, 130)},
    "토  성": {"col": (230, 200, 140), "r": 195, "rings": True,  "glow": (255, 225, 165)},
    "천왕성": {"col": (130, 210, 220), "r": 175, "rings": False, "glow": (160, 240, 250)},
    "해왕성": {"col": (60,  80,  210), "r": 170, "rings": False, "glow": (90,  110, 245)},
}

# 도형 데이터
SHAPE_ORDER  = ["원", "삼각형", "사각형", "별", "하트", "마름모", "오각형", "육각형"]
SHAPE_COLORS = [
    (255, 80,  80),  (80,  180, 255), (80,  255, 120), (255, 220, 50),
    (255, 100, 180), (200, 80,  255), (50,  220, 220), (255, 160, 50),
]

# 주사위 점 위치 (비율)
DICE_DOTS = {
    "1": [(0.50, 0.50)],
    "2": [(0.28, 0.28), (0.72, 0.72)],
    "3": [(0.28, 0.28), (0.50, 0.50), (0.72, 0.72)],
    "4": [(0.28, 0.28), (0.72, 0.28), (0.28, 0.72), (0.72, 0.72)],
    "5": [(0.28, 0.28), (0.72, 0.28), (0.50, 0.50), (0.28, 0.72), (0.72, 0.72)],
    "6": [(0.28, 0.25), (0.72, 0.25), (0.28, 0.50), (0.72, 0.50), (0.28, 0.75), (0.72, 0.75)],
}

# 원소 데이터 (기호 → (원자번호, 한국어명, 배경색))
ELEMENT_DATA = {
    "H":  (1,  "수  소", (50,  120, 200)),
    "He": (2,  "헬  륨", (100, 60,  180)),
    "Li": (3,  "리  튬", (200, 80,  60)),
    "C":  (6,  "탄  소", (60,  60,  60)),
    "N":  (7,  "질  소", (60,  100, 200)),
    "O":  (8,  "산  소", (200, 60,  60)),
    "Na": (11, "나트륨", (200, 140, 50)),
    "Fe": (26, "철   ", (150, 80,  50)),
    "Cu": (29, "구  리", (200, 130, 50)),
    "Ag": (47, "은   ", (160, 160, 170)),
    "Au": (79, "금   ", (220, 180, 30)),
    "Al": (13, "알루미늄", (160, 170, 180)),
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

    # ── 신규 10개 (타겟 지정 스타일) ──────────────────────────
    "zodiac": {
        "name": "별자리 맞추기",
        "title_line1": "별자리를", "title_line2": "맞춰라!",
        "subtitle": "목표 별자리에서 화면을 멈추세요",
        "items": ["양자리 ♈", "황소자리 ♉", "쌍둥이자리 ♊", "게자리 ♋",
                  "사자자리 ♌", "처녀자리 ♍", "천칭자리 ♎", "전갈자리 ♏",
                  "사수자리 ♐", "염소자리 ♑", "물병자리 ♒", "물고기자리 ♓"],
        "item_font_size": 110,
        "bg_dark": (5, 5, 28), "bg_light": (10, 10, 55),
        "item_color": (200, 210, 255), "shadow_color": (60, 70, 160),
        "accent": (180, 160, 255),      "glow_color":  (160, 140, 255),
        "has_target": True, "target_label": "목표 별자리",
        "render_type": "standard",
    },
    "planet": {
        "name": "행성 맞추기",
        "title_line1": "행성을", "title_line2": "맞춰라!",
        "subtitle": "목표 행성에서 화면을 멈추세요",
        "items": list(PLANET_DATA.keys()),
        "item_font_size": 130,
        "bg_dark": (3, 3, 18), "bg_light": (8, 8, 35),
        "item_color": (220, 230, 255), "shadow_color": (30, 30, 80),
        "accent": (150, 180, 255),      "glow_color":  (120, 160, 255),
        "has_target": True, "target_label": "목표 행성",
        "render_type": "planet",
    },
    "kpop": {
        "name": "K-POP 맞추기",
        "title_line1": "K-POP", "title_line2": "그룹 맞추기!",
        "subtitle": "목표 그룹에서 화면을 멈추세요",
        "items": ["BTS", "aespa", "IVE", "NewJeans",
                  "BLACKPINK", "TWICE", "EXO", "SEVENTEEN",
                  "Stray Kids", "LE SSERAFIM", "NCT 127", "ITZY"],
        "item_font_size": 110,
        "bg_dark": (25, 5, 35), "bg_light": (45, 10, 65),
        "item_color": (255, 180, 255), "shadow_color": (130, 30, 150),
        "accent": (255, 100, 255),      "glow_color":  (230, 80, 255),
        "has_target": True, "target_label": "목표 그룹",
        "render_type": "standard",
    },
    "sport": {
        "name": "스포츠 맞추기",
        "title_line1": "스포츠를", "title_line2": "맞춰라!",
        "subtitle": "목표 스포츠에서 화면을 멈추세요",
        "items": ["축  구", "야  구", "농  구", "배  구",
                  "수  영", "테니스", "골  프", "탁  구",
                  "배드민턴", "스  키", "복  싱", "사이클"],
        "item_font_size": 140,
        "bg_dark": (5, 20, 10), "bg_light": (10, 38, 20),
        "item_color": (130, 255, 160), "shadow_color": (30, 100, 55),
        "accent": (80, 220, 130),       "glow_color":  (60, 200, 110),
        "has_target": True, "target_label": "목표 스포츠",
        "render_type": "standard",
    },
    "element": {
        "name": "원소 기호 맞추기",
        "title_line1": "원소를", "title_line2": "찾아라!",
        "subtitle": "목표 원소 기호에서 화면을 멈추세요",
        "items": list(ELEMENT_DATA.keys()),
        "item_font_size": 220,
        "bg_dark": (5, 15, 25), "bg_light": (10, 28, 48),
        "item_color": (255, 255, 255), "shadow_color": (40, 80, 130),
        "accent": (100, 200, 255),      "glow_color":  (80, 180, 255),
        "has_target": True, "target_label": "찾을 원소",
        "render_type": "element",
    },
    "shape": {
        "name": "도형 맞추기",
        "title_line1": "도형을", "title_line2": "맞춰라!",
        "subtitle": "목표 도형에서 화면을 멈추세요",
        "items": SHAPE_ORDER,
        "item_font_size": 100,
        "bg_dark": (10, 8, 25), "bg_light": (20, 16, 50),
        "item_color": (255, 255, 255), "shadow_color": (0, 0, 0),
        "accent": (255, 255, 255),      "glow_color":  (200, 200, 255),
        "has_target": True, "target_label": "목표 도형",
        "render_type": "shape",
    },
    "clock": {
        "name": "시계 맞추기",
        "title_line1": "시계를", "title_line2": "멈춰라!",
        "subtitle": "목표 시각에서 화면을 멈추세요",
        "items": ["1시", "2시", "3시", "4시", "5시", "6시",
                  "7시", "8시", "9시", "10시", "11시", "12시"],
        "item_font_size": 130,
        "bg_dark": (8, 8, 22), "bg_light": (16, 16, 45),
        "item_color": (255, 240, 180), "shadow_color": (100, 90, 30),
        "accent": (255, 210, 80),       "glow_color":  (255, 200, 60),
        "has_target": True, "target_label": "목표 시각",
        "render_type": "clock",
    },
    "dice": {
        "name": "주사위 맞추기",
        "title_line1": "주사위를", "title_line2": "멈춰라!",
        "subtitle": "목표 숫자에서 화면을 멈추세요",
        "items": ["1", "2", "3", "4", "5", "6"],
        "item_font_size": 130,
        "bg_dark": (8, 5, 20), "bg_light": (18, 12, 42),
        "item_color": (255, 255, 255), "shadow_color": (60, 40, 100),
        "accent": (200, 150, 255),      "glow_color":  (180, 130, 255),
        "has_target": True, "target_label": "목표 숫자",
        "render_type": "dice",
    },
    "flower": {
        "name": "꽃 맞추기",
        "title_line1": "꽃을", "title_line2": "맞춰라!",
        "subtitle": "목표 꽃에서 화면을 멈추세요",
        "items": ["장  미", "튤  립", "벚  꽃", "해바라기",
                  "국  화", "라일락", "수선화", "민들레",
                  "진달래", "개나리", "백  합", "코스모스"],
        "item_font_size": 150,
        "bg_dark": (25, 8, 18), "bg_light": (48, 14, 35),
        "item_color": (255, 200, 220), "shadow_color": (130, 40, 80),
        "accent": (255, 140, 180),      "glow_color":  (255, 120, 160),
        "has_target": True, "target_label": "목표 꽃",
        "render_type": "standard",
    },
    "language": {
        "name": "언어 맞추기",
        "title_line1": "언어를", "title_line2": "맞춰라!",
        "subtitle": "목표 언어에서 화면을 멈추세요",
        "items": ["한국어", "영  어", "일본어", "중국어",
                  "스페인어", "프랑스어", "독일어", "아랍어",
                  "러시아어", "포르투갈어", "이탈리아어", "힌디어"],
        "item_font_size": 130,
        "bg_dark": (8, 15, 28), "bg_light": (15, 28, 52),
        "item_color": (180, 240, 255), "shadow_color": (35, 80, 130),
        "accent": (100, 210, 255),      "glow_color":  (80, 195, 255),
        "has_target": True, "target_label": "목표 언어",
        "render_type": "standard",
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
# 도형 그리기 헬퍼
# ============================================================
def _star_pts(cx, cy, r_out, r_in, n=5):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = math.pi * i / n - math.pi / 2
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    return pts

def _heart_pts(cx, cy, s, steps=48):
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps - math.pi / 2
        x = s * 16 * math.sin(t) ** 3 / 16
        y = -s * (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) / 16
        pts.append((int(cx + x), int(cy + y)))
    return pts

def _hex_pts(cx, cy, r):
    return [(int(cx + r * math.cos(math.pi * i / 3)),
             int(cy + r * math.sin(math.pi * i / 3))) for i in range(6)]

def _draw_shape(draw, name, cx, cy, size, fill_col, outline_col=(255, 255, 255)):
    s = int(size)
    if name == "원":
        draw.ellipse([cx-s, cy-s, cx+s, cy+s], fill=fill_col,
                     outline=outline_col, width=8)
    elif name == "삼각형":
        pts = [(cx, cy-s),
               (cx - int(s*0.866), cy + s//2),
               (cx + int(s*0.866), cy + s//2)]
        draw.polygon(pts, fill=fill_col, outline=outline_col)
    elif name == "사각형":
        draw.rectangle([cx-s, cy-s, cx+s, cy+s], fill=fill_col,
                       outline=outline_col, width=8)
    elif name == "별":
        draw.polygon(_star_pts(cx, cy, s, int(s*0.4)), fill=fill_col,
                     outline=outline_col)
    elif name == "하트":
        draw.polygon(_heart_pts(cx, cy + s//5, int(s*0.92)), fill=fill_col,
                     outline=outline_col)
    elif name == "마름모":
        draw.polygon([(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)],
                     fill=fill_col, outline=outline_col)
    elif name == "오각형":
        pts = [(cx + int(s*math.cos(2*math.pi*i/5 - math.pi/2)),
                cy + int(s*math.sin(2*math.pi*i/5 - math.pi/2)))
               for i in range(5)]
        draw.polygon(pts, fill=fill_col, outline=outline_col)
    elif name == "육각형":
        draw.polygon(_hex_pts(cx, cy, s), fill=fill_col, outline=outline_col)

def _draw_planet(img, planet_name, cx, cy, r):
    pd   = PLANET_DATA.get(planet_name, PLANET_DATA["지  구"])
    col  = pd["col"]
    draw = ImageDraw.Draw(img, "RGBA")
    # 글로우
    gl   = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(gl)
    gd.ellipse([cx - r*2, cy - r*2, cx + r*2, cy + r*2],
               fill=(*pd["glow"], 35))
    blurred = gl.filter(ImageFilter.GaussianBlur(32))
    img.paste(blurred, (0, 0), blurred)
    draw2 = ImageDraw.Draw(img, "RGBA")
    # 토성 고리
    if pd.get("rings"):
        for width_mul, alpha in [(1.85, 55), (1.65, 90), (1.45, 70)]:
            ra, rb = int(r * width_mul), int(r * 0.38)
            draw2.ellipse([cx-ra, cy-rb, cx+ra, cy+rb],
                          outline=(*col, alpha), width=10)
    # 행성 본체
    draw2.ellipse([cx-r, cy-r, cx+r, cy+r],
                  fill=col, outline=(255, 255, 255, 50), width=3)

def _draw_dice(draw, value, x1, y1, side):
    dr   = int(side * 0.065)
    draw.rounded_rectangle([x1, y1, x1+side, y1+side], radius=int(side*0.12),
                            fill=(240, 240, 240), outline=(30, 30, 30), width=6)
    for (fx, fy) in DICE_DOTS.get(str(value), []):
        dx = x1 + int(side * fx)
        dy = y1 + int(side * fy)
        draw.ellipse([dx-dr, dy-dr, dx+dr, dy+dr], fill=(20, 20, 20))

def _draw_element_card(img, symbol, cx, cy, card_h=560):
    num, name, col = ELEMENT_DATA.get(symbol, (0, "?", (100, 100, 100)))
    draw = ImageDraw.Draw(img, "RGBA")
    cw   = 480
    x1, y1 = cx - cw//2, cy - card_h//2
    x2, y2 = cx + cw//2, cy + card_h//2
    # 카드 배경
    draw.rounded_rectangle([x1, y1, x2, y2], radius=32,
                            fill=(*col, 220), outline=(255, 255, 255, 100), width=4)
    # 원자번호
    num_f = get_font(55, bold=False)
    bb    = num_f.getbbox(str(num))
    draw.text((x1 + 20, y1 + 14), str(num), font=num_f, fill=(255, 255, 255, 180))
    # 기호 (크게)
    sym_f = get_font(230)
    bb2   = sym_f.getbbox(symbol)
    draw.text((cx - (bb2[2]-bb2[0])//2, cy - (bb2[3]-bb2[1])//2 - 20),
              symbol, font=sym_f, fill=(255, 255, 255))
    # 원소명
    nm_f  = get_font(68, bold=False)
    bb3   = nm_f.getbbox(name)
    draw.text((cx - (bb3[2]-bb3[0])//2, y2 - 90), name, font=nm_f,
              fill=(255, 255, 255, 210))

def _draw_clock_face(img, cfg, t, speed_factor, frozen_hour=None):
    """시계 얼굴을 그립니다. frozen_hour가 있으면 해당 시각에 고정."""
    draw = ImageDraw.Draw(img, "RGBA")
    cx, cy, r = WIDTH // 2, HEIGHT // 2 - 60, 340

    # 페이스
    draw.ellipse([cx-r-4, cy-r-4, cx+r+4, cy+r+4],
                 fill=(255, 255, 255, 30), outline=(255,255,255,80), width=6)
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*cfg["bg_dark"], 240))
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(200, 200, 200), width=6)

    # 눈금 & 숫자
    mf = get_font(50, bold=False)
    for h in range(1, 13):
        angle = 2 * math.pi * h / 12 - math.pi / 2
        mx = cx + (r - 68) * math.cos(angle)
        my = cy + (r - 68) * math.sin(angle)
        bb = mf.getbbox(str(h))
        draw.text((mx - (bb[2]-bb[0])//2, my - (bb[3]-bb[1])//2),
                  str(h), font=mf, fill=(200, 200, 200))
    for m in range(60):
        a   = 2 * math.pi * m / 60 - math.pi / 2
        l1  = r - 12 if m % 5 else r - 14
        l2  = r - 30 if m % 5 else r - 48
        lw  = 2 if m % 5 else 5
        draw.line([(cx + l1*math.cos(a), cy + l1*math.sin(a)),
                   (cx + l2*math.cos(a), cy + l2*math.sin(a))],
                  fill=(150, 150, 150), width=lw)

    if frozen_hour is not None:
        ha = 2 * math.pi * frozen_hour / 12 - math.pi / 2
        ma = ha * 12
        sa = ha * 720
    else:
        full = t * speed_factor * 2 * math.pi / 12
        ha   = full % (2 * math.pi) - math.pi / 2
        ma   = (full * 12) % (2 * math.pi) - math.pi / 2
        sa   = (full * 720) % (2 * math.pi) - math.pi / 2

    # 시침
    draw.line([(cx, cy), (cx + r*0.58*math.cos(ha), cy + r*0.58*math.sin(ha))],
              fill=(255, 255, 255), width=14)
    # 분침
    draw.line([(cx, cy), (cx + r*0.82*math.cos(ma), cy + r*0.82*math.sin(ma))],
              fill=(200, 200, 220), width=8)
    # 초침 (빨강)
    draw.line([(cx, cy), (cx + r*0.88*math.cos(sa), cy + r*0.88*math.sin(sa))],
              fill=(255, 50, 50), width=4)
    # 중심 점
    draw.ellipse([cx-14, cy-14, cx+14, cy+14], fill=(255, 255, 255))
    draw.ellipse([cx-7, cy-7, cx+7, cy+7], fill=(255, 50, 50))

    # 현재 시각 레이블 (고정모드 제외)
    if frozen_hour is None:
        cur_h = int((ha + math.pi / 2) / (2 * math.pi) * 12) % 12
        if cur_h == 0:
            cur_h = 12
        draw_centered_text(img, f"{cur_h}시", HEIGHT // 2 + 340, get_font(110),
                           cfg["item_color"], glow=cfg["glow_color"])

# ============================================================
# 도형 게임 사이클 프레임
# ============================================================
def make_shape_frame(cfg, shape_name, t, flash_intensity=0.0, target=None):
    img  = make_bg(cfg, t)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_particles(draw, t, cfg["accent"])
    draw_header(img, cfg, target_text=target)

    cx, cy = WIDTH // 2, HEIGHT // 2 - 60
    idx    = SHAPE_ORDER.index(shape_name) if shape_name in SHAPE_ORDER else 0
    col    = SHAPE_COLORS[idx % len(SHAPE_COLORS)]
    _draw_shape(draw, shape_name, cx, cy, 270, col)

    name_font = get_font(110)
    draw_centered_text(img, shape_name, cy + 340, name_font, col,
                       shadow=(0, 0, 0), glow=col)

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return apply_flash(img, flash_intensity)

# ============================================================
# 행성 게임 사이클 프레임
# ============================================================
def make_planet_frame(cfg, planet_name, t, flash_intensity=0.0, target=None):
    img  = make_bg(cfg, t)
    draw_particles(ImageDraw.Draw(img, "RGBA"), t, cfg["accent"], count=25)
    draw_header(img, cfg, target_text=target)

    pd  = PLANET_DATA.get(planet_name, list(PLANET_DATA.values())[0])
    cx  = WIDTH // 2
    # 토성은 고리 공간 확보를 위해 약간 위로
    cy  = HEIGHT // 2 - (80 if pd.get("rings") else 30)
    r   = pd["r"]
    _draw_planet(img, planet_name, cx, cy, r)

    name_font = get_font(120)
    draw_centered_text(img, planet_name, cy + r + 130, name_font,
                       pd["col"], shadow=(0, 0, 0), glow=pd["glow"])

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return apply_flash(img, flash_intensity)

# ============================================================
# 원소 게임 사이클 프레임
# ============================================================
def make_element_frame(cfg, symbol, t, flash_intensity=0.0, target=None):
    img  = make_bg(cfg, t)
    draw_particles(ImageDraw.Draw(img, "RGBA"), t, cfg["accent"])
    draw_header(img, cfg, target_text=target)

    _draw_element_card(img, symbol, WIDTH // 2, HEIGHT // 2 - 20)

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return apply_flash(img, flash_intensity)

# ============================================================
# 시계 애니메이션 프레임
# ============================================================
def make_clock_anim_frame(cfg, t, target=None):
    img  = make_bg(cfg, t)
    draw_particles(ImageDraw.Draw(img, "RGBA"), t, cfg["accent"], count=14)
    draw_header(img, cfg, target_text=target)

    cycle_ratio  = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    speed_factor = 1.2 + cycle_ratio * 4.5
    _draw_clock_face(img, cfg, t, speed_factor)

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return img

# ============================================================
# 주사위 게임 사이클 프레임
# ============================================================
def make_dice_frame(cfg, value, t, flash_intensity=0.0, target=None):
    img  = make_bg(cfg, t)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_particles(draw, t, cfg["accent"])
    draw_header(img, cfg, target_text=target)

    side = 520
    x1   = (WIDTH  - side) // 2
    y1   = (HEIGHT - side) // 2 - 40
    _draw_dice(draw, value, x1, y1, side)

    progress = (t - T_INTRO_END) / (T_CYCLE_END - T_INTRO_END)
    draw_bottom(img, cfg, progress)
    return apply_flash(img, flash_intensity)

# ============================================================
# 비주얼 결과 프레임 (shape / planet / element / dice / clock)
# ============================================================
def make_visual_result_frame(cfg, rt, result, t_ratio):
    img   = make_bg(cfg, T_CYCLE_END / DURATION + t_ratio * 0.2)
    eased = 1 - (1 - min(t_ratio * 2.5, 1.0)) ** 3
    draw_particles(ImageDraw.Draw(img, "RGBA"), t_ratio * 5, cfg["accent"], count=35)
    draw_header(img, cfg)

    cx, cy = WIDTH // 2, HEIGHT // 2

    if rt == "shape":
        idx  = SHAPE_ORDER.index(result) if result in SHAPE_ORDER else 0
        col  = SHAPE_COLORS[idx % len(SHAPE_COLORS)]
        size = int(260 * (0.65 + 0.35 * eased))
        _draw_shape(ImageDraw.Draw(img, "RGBA"), result, cx, cy - 60, size, col)
        draw_centered_text(img, result, cy + size + 50, get_font(110), col,
                           shadow=(0, 0, 0), glow=col)

    elif rt == "planet":
        pd  = PLANET_DATA.get(result, list(PLANET_DATA.values())[0])
        r   = int(pd["r"] * (0.65 + 0.35 * eased))
        pcy = cy - (60 if pd.get("rings") else 20)
        _draw_planet(img, result, cx, pcy, r)
        draw_centered_text(img, result, pcy + r + 120, get_font(115),
                           pd["col"], shadow=(0, 0, 0), glow=pd["glow"])

    elif rt == "element":
        card_h = int(520 * (0.65 + 0.35 * eased))
        _draw_element_card(img, result, cx, cy - 20, card_h)

    elif rt == "dice":
        side = int(500 * (0.65 + 0.35 * eased))
        x1   = cx - side // 2
        y1   = cy - side // 2 - 30
        _draw_dice(ImageDraw.Draw(img, "RGBA"), result, x1, y1, side)

    elif rt == "clock":
        # 시계를 목표 시각에 고정 (결과로 표시)
        try:
            frozen_h = int(result.replace("시", ""))
        except Exception:
            frozen_h = 12
        _draw_clock_face(img, cfg, 0, 1.0, frozen_hour=frozen_h)
        draw_centered_text(img, result, HEIGHT // 2 + 350, get_font(110),
                           cfg["item_color"], glow=cfg["glow_color"])

    draw_centered_text(img, "댓글로 결과 알려줘! 👇",
                       HEIGHT - 310, get_font(52, bold=False), (200, 200, 200))
    draw_bottom(img, cfg, 1.0, cta="결과 확인!")
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
    rt      = cfg.get("render_type", "standard")
    is_anim = rt in ("gauge", "ball", "archery")          # 순수 애니메이션 (items 없음)
    is_vis  = rt in ("shape", "planet", "element", "dice", "clock")  # 비주얼 결과
    items   = cfg.get("items")

    if not is_anim and items and result_item is None:
        result_item = random.choice(items)

    frames_intro  = int(T_INTRO_END                  * FPS)
    frames_cycle  = int((T_CYCLE_END - T_INTRO_END)  * FPS)
    frames_result = int((T_RESULT_END - T_CYCLE_END) * FPS)

    # ── 인트로 ──────────────────────────────────────────────
    if rt == "memory":
        tgt = target or (random.choice(items) if items else "★")
        for i in range(frames_intro):
            yield make_memory_intro_frame(cfg, tgt, i / max(frames_intro - 1, 1))
    else:
        for i in range(frames_intro):
            yield make_intro_frame(cfg, i / max(frames_intro - 1, 1))

    # ── 사이클 ──────────────────────────────────────────────
    def _seq_cycle(frame_fn):
        seq  = build_item_sequence(items, frames_cycle)
        prev = None
        for i, item in enumerate(seq):
            t     = T_INTRO_END + i / FPS
            flash = 0.4 * (1 - i / frames_cycle * 0.5) if item != prev and i > 0 else 0.0
            yield frame_fn(cfg, item, t, flash_intensity=flash, target=target)
            prev  = item

    if rt == "gauge":
        for i in range(frames_cycle):
            yield make_gauge_frame(cfg, T_INTRO_END + i / FPS)
    elif rt == "ball":
        for i in range(frames_cycle):
            yield make_ball_frame(cfg, T_INTRO_END + i / FPS)
    elif rt == "archery":
        for i in range(frames_cycle):
            yield make_archery_frame(cfg, T_INTRO_END + i / FPS)
    elif rt == "clock":
        for i in range(frames_cycle):
            yield make_clock_anim_frame(cfg, T_INTRO_END + i / FPS, target=target)
    elif rt == "color":
        yield from _seq_cycle(make_color_frame)
    elif rt == "shape":
        yield from _seq_cycle(make_shape_frame)
    elif rt == "planet":
        yield from _seq_cycle(make_planet_frame)
    elif rt == "element":
        yield from _seq_cycle(make_element_frame)
    elif rt == "dice":
        yield from _seq_cycle(make_dice_frame)
    else:  # standard / memory
        yield from _seq_cycle(make_cycle_frame)

    # ── 결과 ────────────────────────────────────────────────
    for i in range(frames_result):
        tr = i / max(frames_result - 1, 1)
        if is_anim:
            yield make_anim_result_frame(cfg, rt, tr)
        elif is_vis:
            yield make_visual_result_frame(cfg, rt, result_item, tr)
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
    is_anim = rt in ("gauge", "ball", "archery", "clock")

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
