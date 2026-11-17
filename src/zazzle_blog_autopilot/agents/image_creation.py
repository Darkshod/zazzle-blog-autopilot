"""Image & Design Agent — generates optimized blog thumbnails (1200x630) and 2:3 Pinterest graphics."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from ..models import TaskResult
from . import BaseAgent


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/georgia.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def create_editorial_card_image(
    title: str,
    subtitle: str,
    out_path: Path,
    size: tuple[int, int],
    bg_rgb: tuple[int, int, int] = (250, 247, 242),
    accent_rgb: tuple[int, int, int] = (34, 56, 44),
) -> Path:
    """Create a clean editorial graphic without faking product photography."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    w, h = size
    img = Image.new("RGB", (w, h), bg_rgb)
    draw = ImageDraw.Draw(img)

    pad = max(24, w // 24)
    draw.rectangle([pad, pad, w - pad, h - pad], outline=accent_rgb, width=3)
    draw.rectangle([pad + 12, pad + 12, w - pad - 12, h - pad - 12], outline=(180, 145, 90), width=1)

    f_kicker = _load_font(max(18, w // 38))
    f_title = _load_font(max(28, w // 18))
    f_sub = _load_font(max(16, w // 42))

    draw.text((pad * 2, pad * 2), subtitle.upper()[:48], fill=(169, 134, 76), font=f_kicker)
    wrapped = textwrap.fill(title, width=26 if w >= 1000 else 20)
    draw.multiline_text((pad * 2, int(h * 0.28)), wrapped, fill=accent_rgb, font=f_title, spacing=12)
    draw.text((pad * 2, h - pad * 3), "EDITORIAL GIFT GUIDE  •  CURATED PICKS", fill=accent_rgb, font=f_kicker)

    img.save(out_path, format="JPEG", quality=88, optimize=True)
    return out_path


class ImageCreationAgent(BaseAgent):
    name = "image_creation"

    def execute(self, output_dir: Path | None = None, **kwargs: Any) -> TaskResult:
        asset_root = output_dir or (Path.cwd() / "site" / "assets" / "generated")
        articles = self.db.list_articles()
        generated: list[str] = []
        manifest: list[dict[str, str]] = []

        for article in articles:
            blog_img = asset_root / f"{article.slug}-guide-cover.jpg"
            pin_img = asset_root / f"{article.slug}-pinterest-pin.jpg"
            if not blog_img.exists():
                create_editorial_card_image(
                    title=article.title,
                    subtitle=article.category,
                    out_path=blog_img,
                    size=(1200, 630),
                )
            if not pin_img.exists():
                create_editorial_card_image(
                    title=article.title,
                    subtitle=f"{article.category} Guide",
                    out_path=pin_img,
                    size=(1000, 1500),
                )
            article.image_path = f"/assets/generated/{blog_img.name}"
            self.db.upsert_article(article)
            generated.append(blog_img.name)
            manifest.append(
                {
                    "slug": article.slug,
                    "blog_image": str(blog_img),
                    "pin_image": str(pin_img),
                    "alt_text": article.image_alt,
                    "license": "Original generated editorial graphic (MIT / repo-owned)",
                }
            )

        asset_root.mkdir(parents=True, exist_ok=True)
        (asset_root / "image_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return TaskResult(
            agent_name=self.name,
            task="generate_blog_and_pin_images",
            status="success",
            input_summary={"articles": len(articles)},
            output_summary={"images_ready": len(generated), "manifest": str(asset_root / "image_manifest.json")},
            recommendations=[
                "Replace editorial covers with authorized Zazzle product photography where available; never fabricate fake product photos."
            ],
        )
