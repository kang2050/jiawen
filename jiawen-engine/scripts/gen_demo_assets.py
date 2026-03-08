"""
生成演示素材脚本
=================
用 Gemini 3 Pro Image Preview 生成：
  1. 4张风格预览图（风格展示板块用）
  2. 8张表情包贴纸（效果展示板块用）

输出到：jiawen/client/public/ai-generated/
"""

import asyncio
import base64
import json
from pathlib import Path

import httpx

API_KEY   = "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"
BASE_URL  = "https://openrouter.ai/api/v1"
MODEL     = "google/gemini-3-pro-image-preview"
OUT_DIR   = Path(__file__).parent.parent.parent / "jiawen" / "client" / "public" / "ai-generated"

# 佳文真实照片（作为参考，提升角色一致性）
REF_PHOTO_PATHS = [
    Path(__file__).parent.parent.parent / "jiawen" / "client" / "public" / "jiawen" / "jiawen_real_front.jpg",
    Path(__file__).parent.parent.parent / "jiawen" / "client" / "public" / "jiawen" / "jiawen_real_side.jpg",
]

# ─── 4种风格预览（展示板块）─────────────────────────────────────
# 每张图：一只狗 + 一只猫，不同品种，干净无涂抹感

STYLE_PREVIEWS = [
    {
        "filename": "style_pixar.png",
        "prompt": (
            "Pixar 3D animated characters rendered by Pixar Animation Studios. "
            "TWO characters side by side: a fluffy Golden Retriever dog and an elegant Persian cat, "
            "both in chibi exaggerated proportions with oversized round heads and big glimmering eyes. "
            "Smooth polished 3D geometry, subsurface scattering fur, soft plush texture. "
            "Warm golden studio key light, gentle rim lighting, vibrant saturated colors. "
            "Clean crisp render — NO painterly smudging, NO brush strokes, NO texture grain. "
            "Both characters happy and expressive, standing together. "
            "Pure white background, square 1:1 format, 4K movie-quality CGI render, ultra-sharp."
        ),
    },
    {
        "filename": "style_japanese.png",
        "prompt": (
            "Japanese kawaii LINE sticker style illustration. "
            "TWO adorable characters side by side: a Shiba Inu dog and a Scottish Fold cat, "
            "both in super-deformed (SD) chibi proportions, 1:1 head-to-body ratio. "
            "Thick clean bold black outlines, perfectly flat cel-shaded pastel colors, zero gradients. "
            "Big glossy sparkle eyes, rosy blush circles on cheeks, tiny happy expressions. "
            "Completely flat and clean — NO watercolor, NO paint texture, NO smudging whatsoever. "
            "Crisp vector illustration quality like LINE Friends or Sanrio. "
            "Pure white background, square 1:1 format, print-ready sticker artwork."
        ),
    },
    {
        "filename": "style_ghibli.png",
        "prompt": (
            "Studio Ghibli hand-drawn animation style, Hayao Miyazaki aesthetic. "
            "TWO characters: a fluffy Samoyed dog and a striped Tabby cat, "
            "illustrated with confident clean ink outlines and precise cel animation coloring. "
            "Expressive Ghibli-style eyes full of soul and warmth. "
            "Clean flat color fills with minimal cel-shading — crisp and sharp, "
            "NO smudging, NO blurry edges, NO painterly blur or texture. "
            "The style is clean animation frame quality, like a frozen moment from My Neighbor Totoro. "
            "Both animals sitting together, cheerful and cozy. "
            "Pure white background, square 1:1 format, high-resolution animation cel quality."
        ),
    },
    {
        "filename": "style_guochao.png",
        "prompt": (
            "Chinese Guochao 国潮 fashion illustration — pet costume design. "
            "TWO characters: a Husky dog and a Siamese cat, "
            "both dressed in elaborate Chinese traditional-meets-streetwear outfits. "
            "The Husky wears a vermillion red embroidered Tang jacket (唐装) with gold cloud (祥云) patterns. "
            "The Siamese cat wears a matching blue-gold qipao-inspired outfit with lotus embroidery. "
            "Bold clean vector outlines, vibrant saturated flat colors, decorative Chinese motif fills. "
            "Completely clean and sharp — NO painterly smudging, NO watercolor bleed, NO texture grain. "
            "Modern Guochao streetwear character design, high fashion pet portrait quality. "
            "Pure white background, square 1:1 format, graphic poster quality."
        ),
    },
]

# ─── 8种表情包贴纸───────────────────────────────────────────────────

CONSISTENCY_PREFIX = (
    "CRITICAL: This is a character sticker set. "
    "Maintain 100% character consistency: same breed (border collie mix), "
    "same black and white coat, same distinctive markings, same fur texture, "
    "same ear shape. Every sticker MUST look like the SAME dog. "
    "Sticker format: single character centered on pure white background, "
    "no shadow, no frame, suitable for messaging app sticker. "
)

STYLE_SUFFIX = (
    "Japanese kawaii sticker style, thick clean black outlines, "
    "flat 2D vector art, pastel colors, chibi proportions, "
    "big sparkly expressive eyes, pure white background. "
)

EMOJI_STICKERS = [
    {
        "filename": "emoji_01_laugh.png",
        "name": "哈哈大笑",
        "prompt": (
            "laughing out loud, eyes squeezed shut into happy crescents, "
            "wide open mouth, body shaking with laughter, "
            "tears of joy at eye corners, speech bubble: 哈哈哈！"
        ),
    },
    {
        "filename": "emoji_02_clingy.png",
        "name": "撒娇卖萌",
        "prompt": (
            "acting cute and clingy, puppy dog eyes glistening with stars, "
            "slight pout, tiny paws pressed together in pleading gesture, "
            "rosy blush marks on cheeks, irresistibly adorable"
        ),
    },
    {
        "filename": "emoji_03_sleep.png",
        "name": "睡着打盹",
        "prompt": (
            "fast asleep, eyes gently closed with long lashes, "
            "soft smile, three ZZZ bubbles floating above, "
            "curled up cozy position, crescent moon and stars nearby"
        ),
    },
    {
        "filename": "emoji_04_hungry.png",
        "name": "超级饿",
        "prompt": (
            "extremely hungry, drooling with watering mouth, "
            "huge pleading round eyes staring up, "
            "stomach rumble lines, holding empty bowl with both paws, "
            "floating food emojis: 🍖🍗 around"
        ),
    },
    {
        "filename": "emoji_05_angry.png",
        "name": "生气了",
        "prompt": (
            "grumpy and angry, furrowed brows V shape, "
            "puffed up cheeks, crossed arms, steam from nostrils, "
            "dark angry aura lines radiating, comically furious"
        ),
    },
    {
        "filename": "emoji_06_shocked.png",
        "name": "哇！惊呆了",
        "prompt": (
            "completely shocked and surprised, eyes wide as saucers, "
            "jaw dropped, both paws raised to cheeks Home Alone style, "
            "bold ！！ marks, exaggerated reaction"
        ),
    },
    {
        "filename": "emoji_07_love.png",
        "name": "爱心满满",
        "prompt": (
            "overflowing with love, heart-shaped pupils, "
            "blowing a kiss, multiple red and pink hearts floating everywhere, "
            "arms stretched wide for a hug, sweet rosy glow"
        ),
    },
    {
        "filename": "emoji_08_tsundere.png",
        "name": "傲娇翻白眼",
        "prompt": (
            "tsundere and haughty, eyes rolled to the side, one eyebrow raised, "
            "arms crossed, head slightly turned away, tiny smirk, "
            "speech bubble: 哼！ too-cool-for-this energy"
        ),
    },
]


async def call_api(messages: list, timeout: float = 120.0) -> str | None:
    """调用 OpenRouter API，返回图片 base64 data URL"""
    payload = {
        "model": MODEL,
        "modalities": ["image", "text"],
        "messages": messages,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://pawsmeme.ai",
                "X-Title": "PawsMeme Demo Asset Generator",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    msg = data["choices"][0]["message"]
    if "images" in msg:
        for img in msg["images"]:
            if img.get("type") == "image_url":
                return img["image_url"]["url"]
    if isinstance(msg.get("content"), list):
        for part in msg["content"]:
            if part.get("type") == "image_url":
                return part["image_url"]["url"]
    # 有时文本 content 中含有 data URL
    if isinstance(msg.get("content"), str) and msg["content"].startswith("data:"):
        return msg["content"]
    return None


def save_image(data_url: str, path: Path) -> None:
    if "," in data_url:
        raw = base64.b64decode(data_url.split(",", 1)[1])
    else:
        raw = base64.b64decode(data_url)
    path.write_bytes(raw)
    print(f"  ✓ 已保存 {path.name} ({len(raw)//1024} KB)")


def load_ref_photos() -> list[bytes]:
    photos = []
    for p in REF_PHOTO_PATHS:
        if p.exists():
            photos.append(p.read_bytes())
            print(f"  📷 加载参考图: {p.name}")
    return photos


def build_messages_text_only(prompt: str) -> list:
    return [{"role": "user", "content": [{"type": "text", "text": prompt}]}]


def build_messages_with_refs(ref_photos: list[bytes], prompt: str) -> list:
    content = []
    for b in ref_photos:
        b64 = base64.b64encode(b).decode()
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    content.append({"type": "text", "text": prompt})
    return [{"role": "user", "content": content}]


async def gen_style_previews():
    print("\n🎨 生成风格预览图（4张）...")
    for item in STYLE_PREVIEWS:
        out_path = OUT_DIR / item["filename"]
        if out_path.exists():
            print(f"  ⏭ 跳过（已存在）: {item['filename']}")
            continue
        print(f"  → 正在生成: {item['filename']}")
        try:
            messages = build_messages_text_only(item["prompt"])
            data_url = await call_api(messages)
            if data_url:
                save_image(data_url, out_path)
            else:
                print(f"  ✗ 未返回图片: {item['filename']}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        await asyncio.sleep(2)  # 限速


async def gen_emoji_stickers(ref_photos: list[bytes]):
    print("\n😄 生成表情包贴纸（8张）...")
    for item in EMOJI_STICKERS:
        out_path = OUT_DIR / item["filename"]
        if out_path.exists():
            print(f"  ⏭ 跳过（已存在）: {item['filename']}")
            continue
        print(f"  → 正在生成: {item['name']} ({item['filename']})")
        full_prompt = CONSISTENCY_PREFIX + STYLE_SUFFIX + f"Expression: {item['name']} — {item['prompt']}."
        try:
            if ref_photos:
                messages = build_messages_with_refs(ref_photos, full_prompt)
            else:
                messages = build_messages_text_only(
                    f"Border collie mix dog sticker. {full_prompt}"
                )
            data_url = await call_api(messages)
            if data_url:
                save_image(data_url, out_path)
            else:
                print(f"  ✗ 未返回图片: {item['filename']}")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
        await asyncio.sleep(2)


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 输出目录: {OUT_DIR}")

    ref_photos = load_ref_photos()

    await gen_style_previews()
    await gen_emoji_stickers(ref_photos)

    # 生成索引 JSON 供前端读取
    index = {
        "style_previews": {s["filename"].replace(".png", "").replace("style_", ""): f"/ai-generated/{s['filename']}"
                           for s in STYLE_PREVIEWS},
        "emoji_stickers": [
            {"filename": s["filename"], "name": s["name"], "url": f"/ai-generated/{s['filename']}"}
            for s in EMOJI_STICKERS
        ],
    }
    index_path = OUT_DIR / "index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    print(f"\n✅ 完成！索引文件: {index_path}")
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
