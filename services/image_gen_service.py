# services/image_gen_service.py
import os
import aiohttp
import base64
import json
from typing import Optional, List
from config.settings import settings

class ImageGenService:
    """
    خدمة توليد الصور بالذكاء الاصطناعي.
    تدعم مزودين متعددين عبر Strategy Pattern.
    """
    
    def __init__(self):
        self.provider = settings.ACTIVE_IMAGE_PROVIDER or "openai"
        self.openai_api_key = settings.OPENAI_API_KEY
        self.stability_api_key = settings.STABILITY_API_KEY

    async def generate_image(
        self,
        prompt: str,
        style: str = "realistic",
        size: str = "1024x1024",
        negative_prompt: Optional[str] = None
    ) -> dict:
        """
        توليد صورة بناءً على وصف نصي.
        
        Args:
            prompt: وصف الصورة المطلوبة
            style: النمط (realistic, anime, digital, oil, 3d, sketch)
            size: أبعاد الصورة (1024x1024، 1792x1024، إلخ)
            negative_prompt: عناصر يجب تجنبها في الصورة
            
        Returns:
            dict يحتوي على image_url و prompt والمزود المستخدم
        """
        if self.provider == "openai":
            return await self._generate_openai(prompt, style, size)
        elif self.provider == "stability":
            return await self._generate_stability(prompt, style, size, negative_prompt)
        else:
            return await self._generate_openai(prompt, style, size)  # fallback

    async def _generate_openai(self, prompt: str, style: str, size: str) -> dict:
        """
        توليد صورة باستخدام OpenAI DALL·E 3.
        """
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY غير موجود في ملف .env")

        # تحسين الوصف بإضافة النمط
        styled_prompt = self._apply_style(prompt, style)
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": styled_prompt,
            "n": 1,
            "size": size,
            "quality": "hd",
            "response_format": "url"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"OpenAI Image Gen Error: {error}")
                
                data = await response.json()
                image_url = data["data"][0]["url"]
                
                return {
                    "image_url": image_url,
                    "prompt": prompt,
                    "styled_prompt": styled_prompt,
                    "provider": "openai",
                    "model": "dall-e-3",
                    "size": size
                }

    async def _generate_stability(
        self,
        prompt: str,
        style: str,
        size: str,
        negative_prompt: Optional[str] = None
    ) -> dict:
        """
        توليد صورة باستخدام Stability AI (Stable Diffusion).
        """
        if not self.stability_api_key:
            raise ValueError("STABILITY_API_KEY غير موجود في ملف .env")
        
        # تحويل الأبعاد لصيغة Stability
        width, height = self._parse_size(size)
        styled_prompt = self._apply_style(prompt, style)
        
        headers = {
            "Authorization": f"Bearer {self.stability_api_key}",
            "Accept": "application/json"
        }
        
        payload = {
            "text_prompts": [
                {"text": styled_prompt, "weight": 1.0}
            ],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": 30,
        }
        
        if negative_prompt:
            payload["text_prompts"].append({
                "text": negative_prompt,
                "weight": -1.0
            })
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Stability AI Error: {error}")
                
                data = await response.json()
                # الصورة تأتي كـ base64
                base64_image = data["artifacts"][0]["base64"]
                # هنا يمكن رفع الصورة لخدمة تخزين وإرجاع الرابط
                # حالياً نرجع الـ base64 مباشرة (أو نحولها لـ data URL)
                image_url = f"data:image/png;base64,{base64_image}"
                
                return {
                    "image_url": image_url,
                    "prompt": prompt,
                    "styled_prompt": styled_prompt,
                    "provider": "stability",
                    "model": "stable-diffusion-xl-1024-v1-0",
                    "size": size
                }

    def _apply_style(self, prompt: str, style: str) -> str:
        """
        إضافة وصف النمط للـ prompt.
        """
        styles = {
            "realistic": "photorealistic, highly detailed, 8k resolution",
            "anime": "anime style, manga illustration, vibrant colors, studio ghibli inspired",
            "digital": "digital art, concept art, trending on artstation, sharp focus",
            "oil": "oil painting on canvas, textured brushstrokes, classical art style",
            "3d": "3D render, octane render, cinema 4d, hyperrealistic 3D model",
            "sketch": "pencil sketch, hand-drawn, monochrome, detailed line art"
        }
        style_suffix = styles.get(style, styles["realistic"])
        return f"{prompt}, {style_suffix}"

    def _parse_size(self, size: str) -> tuple:
        """
        تحويل نص الأبعاد لـ (width, height).
        """
        try:
            w, h = size.split("x")
            return int(w), int(h)
        except:
            return 1024, 1024

    async def generate_image_variation(
        self,
        image_url: str,
        style: Optional[str] = None
    ) -> dict:
        """
        توليد تنويعة من صورة موجودة (باستخدام OpenAI).
        """
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY غير موجود")
        
        # تحميل الصورة من الرابط
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    raise Exception("فشل تحميل الصورة الأصلية")
                image_data = await resp.read()
        
        # تحويل لـ base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "image": image_b64,
            "n": 1,
            "size": "1024x1024",
            "response_format": "url"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/images/variations",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Image Variation Error: {error}")
                
                data = await response.json()
                return {
                    "image_url": data["data"][0]["url"],
                    "original_image": image_url,
                    "provider": "openai",
                    "model": "dall-e-3-variation"
                }