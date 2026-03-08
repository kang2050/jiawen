"""
佳文 AI Engine — 宠物表情包生成
=================================
流程：主人上传5张照片 + 选择风格 → Gemini 3 Pro Image Preview
      → 返回8张表情包（表情由AI决定，客户不干预）

端口: 8001
"""

import base64
import uuid
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="佳文表情包生成", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = "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"
OPENROUTER_BASE    = "https://openrouter.ai/api/v1"
IMAGE_MODEL        = "google/gemini-3-pro-image-preview"

OUTPUTS_DIR = Path(__file__).parent.parent / "outputs" / "emoji"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR.parent.parent / "outputs")), name="outputs")


# ─── 4 种风格定义 ────────────────────────────────────────────────────

STYLES = {
    "pixar": {
        "name": "皮克斯3D",
        "desc": "圆润可爱的3D动画风，如《寻梦环游记》里的动物",
        "style_prompt": (
            "Pixar 3D animation style, Disney/Pixar quality CGI rendering, "
            "soft subsurface scattering on fur, big expressive eyes, "
            "smooth rounded forms, cinematic 3D lighting, "
            "pure white background, high-gloss finish, "
            "Pixar movie still quality"
        ),
    },
    "japanese": {
        "name": "日系软萌",
        "desc": "厚线条扁平贴纸，LINE贴纸风格，粉嫩可爱",
        "style_prompt": (
            "Japanese kawaii sticker style, LINE sticker quality, "
            "thick clean black outlines, flat 2D vector art, "
            "pastel color palette, chibi super-deformed proportions, "
            "big sparkly eyes, rosy round cheeks, "
            "pure white background, no gradients, bold simple shapes"
        ),
    },
    "watercolor": {
        "name": "水彩手绘",
        "desc": "温柔水彩插画，像手工画的明信片",
        "style_prompt": (
            "soft watercolor illustration style, hand-painted look, "
            "loose fluid brushstrokes, gentle color bleeding at edges, "
            "paper texture, warm pastel tones, "
            "ink outline with watercolor fill, "
            "white background with slight cream tint, "
            "indie artist postcard aesthetic"
        ),
    },
    "guochao": {
        "name": "国潮插画",
        "desc": "国潮国风，撞色大胆，带点传统纹样的现代插画",
        "style_prompt": (
            "Chinese guochao trendy illustration style, "
            "bold saturated colors with retro Chinese aesthetic, "
            "clean vector outlines, subtle traditional cloud or wave pattern accents, "
            "modern flat design meets classical Chinese art, "
            "vivid red gold and cyan color palette, "
            "pure white background, graphic poster quality"
        ),
    },
}

# ─── 8 种表情（AI决定，客户不干预）────────────────────────────────

EXPRESSIONS = [
    {
        "name": "哈哈大笑",
        "prompt": (
            "laughing out loud, eyes squeezed shut into happy crescents, "
            "wide open mouth showing teeth, body shaking with laughter, "
            "tears of joy at eye corners, LOL energy, "
            "speech bubble with 哈哈哈"
        ),
    },
    {
        "name": "撒娇卖萌",
        "prompt": (
            "acting cute and clingy, puppy dog eyes glistening with stars, "
            "slight pout, tiny paws pressed together in pleading gesture, "
            "rosy blush marks on cheeks, "
            "irresistibly adorable begging expression"
        ),
    },
    {
        "name": "睡着打盹",
        "prompt": (
            "fast asleep, eyes gently closed, soft smile, "
            "three ZZZ bubbles floating above, "
            "tiny snore, curled up cozy position, "
            "small crescent moon and stars nearby, dreamy peaceful mood"
        ),
    },
    {
        "name": "超级饿",
        "prompt": (
            "extremely hungry, drooling with watering mouth, "
            "huge pleading round eyes staring at food, "
            "stomach rumble squiggly lines, "
            "holding empty bowl with both paws, "
            "floating food emojis: 🍖🍗🥩 around the head"
        ),
    },
    {
        "name": "生气了",
        "prompt": (
            "grumpy and angry, furrowed brows forming a V shape, "
            "puffed up cheeks, crossed arms, steam from nostrils, "
            "dark angry aura lines radiating outward, "
            "small lightning bolt symbols, comically furious"
        ),
    },
    {
        "name": "哇！惊呆了",
        "prompt": (
            "completely shocked and surprised, eyes wide as saucers, "
            "jaw dropped open, both paws raised to cheeks Home Alone style, "
            "motion lines radiating shock, "
            "bold ！！ exclamation marks, exaggerated reaction"
        ),
    },
    {
        "name": "爱心满满",
        "prompt": (
            "overflowing with love, heart-shaped pupils in eyes, "
            "blowing a kiss, multiple red and pink hearts floating everywhere, "
            "arms stretched out wide for a hug, "
            "rosy warm glow around the body, sweet romantic mood"
        ),
    },
    {
        "name": "傲娇翻白眼",
        "prompt": (
            "tsundere and haughty, eyes rolled to the side with one eyebrow raised, "
            "arms crossed, head slightly turned away, "
            "tiny smirk that says 'whatever', "
            "sparkle effect on attitude, too-cool-for-this energy, "
            "speech bubble: 哼！"
        ),
    },
]

# ─── 角色一致性前缀（每次生成都带上）────────────────────────────────

CONSISTENCY_PREFIX = (
    "CRITICAL: This is a character sheet sticker. "
    "You MUST replicate the exact same pet character from the reference photos: "
    "same breed, identical coat color and markings, same fur texture, "
    "same ear shape, same body proportions, same distinctive features. "
    "Every sticker must look like the SAME character. "
    "Sticker format: single character centered, isolated on pure white background, "
    "no shadow, no frame, suitable for messaging app sticker pack. "
)


# ─── 生成函数 ────────────────────────────────────────────────────────

def photos_to_content(photo_bytes_list: list[bytes], prompt: str) -> list[dict]:
    content = []
    for b in photo_bytes_list:
        b64 = base64.b64encode(b).decode()
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })
    content.append({"type": "text", "text": prompt})
    return content


async def generate_one(photo_bytes_list: list[bytes], prompt: str) -> str | None:
    payload = {
        "model": IMAGE_MODEL,
        "modalities": ["image", "text"],
        "messages": [
            {"role": "user", "content": photos_to_content(photo_bytes_list, prompt)}
        ],
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://jiawen.pet",
                "X-Title": "佳文宠物表情包",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    msg = data["choices"][0]["message"]

    # 提取图片 data URL
    if "images" in msg:
        for img in msg["images"]:
            if img.get("type") == "image_url":
                return img["image_url"]["url"]
    if isinstance(msg.get("content"), list):
        for part in msg["content"]:
            if part.get("type") == "image_url":
                return part["image_url"]["url"]
    return None


def save_b64_image(data_url: str, filename: str) -> str:
    raw = base64.b64decode(data_url.split(",", 1)[1] if "," in data_url else data_url)
    path = OUTPUTS_DIR / filename
    path.write_bytes(raw)
    return f"/outputs/emoji/{filename}"


# ─── API 路由 ────────────────────────────────────────────────────────

@app.get("/api/styles")
def get_styles():
    """返回可用风格列表，供前端渲染选择卡片"""
    return {
        "styles": [
            {"id": k, "name": v["name"], "desc": v["desc"]}
            for k, v in STYLES.items()
        ]
    }


@app.post("/api/generate")
async def generate(
    pet_name:  str = Form("宠物"),
    pet_breed: str = Form(""),
    style_id:  str = Form("pixar"),
    photos: list[UploadFile] = File(...),
):
    """
    生成8张宠物表情包

    - pet_name:  宠物名字
    - pet_breed: 品种（可选，填了效果更准确）
    - style_id:  风格 ID（pixar / japanese / watercolor / guochao）
    - photos:    5张宠物照片（正面/侧面/45°/特写/背面）
    """
    if style_id not in STYLES:
        return JSONResponse(status_code=400, content={"error": f"未知风格: {style_id}"})
    if not photos:
        return JSONResponse(status_code=400, content={"error": "请上传照片"})

    photo_bytes_list = [await p.read() for p in photos[:5]]
    style = STYLES[style_id]
    breed_hint = f"The pet is a {pet_breed}. " if pet_breed else ""
    job_id = str(uuid.uuid4())[:8]

    results = []
    errors  = []

    for i, expr in enumerate(EXPRESSIONS):
        full_prompt = (
            CONSISTENCY_PREFIX
            + breed_hint
            + f"Expression/emotion: {expr['name']} — {expr['prompt']}. "
            + f"Art style: {style['style_prompt']}."
        )
        try:
            data_url = await generate_one(photo_bytes_list, full_prompt)
            if data_url:
                filename = f"{job_id}_{style_id}_{i+1:02d}_{expr['name']}.png"
                url = save_b64_image(data_url, filename)
                results.append({
                    "index": i + 1,
                    "expression": expr["name"],
                    "url": url,
                })
            else:
                errors.append(f"{expr['name']}: 未返回图片")
        except Exception as e:
            errors.append(f"{expr['name']}: {str(e)[:100]}")

    return {
        "job_id": job_id,
        "pet_name": pet_name,
        "style": {"id": style_id, "name": style["name"]},
        "stickers": results,       # 成功生成的贴纸
        "errors": errors,          # 失败项（方便调试）
        "total": len(results),
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": IMAGE_MODEL,
        "styles": list(STYLES.keys()),
        "expressions": [e["name"] for e in EXPRESSIONS],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
