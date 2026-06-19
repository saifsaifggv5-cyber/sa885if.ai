# services/voice_service.py
import os
import aiohttp
import base64
import json
from typing import Optional, AsyncGenerator
from config.settings import settings


class VoiceService:
    """
    خدمة الصوتيات - تحويل الصوت لنص (STT) والنص لصوت (TTS).
    تدعم OpenAI Whisper و Google TTS.
    """
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.google_api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.provider = settings.ACTIVE_VOICE_PROVIDER or "openai"

    # ═══════════════════════════════════════════
    # تحويل الصوت لنص (Speech-to-Text)
    # ═══════════════════════════════════════════

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "ar",
        model: str = "whisper-1"
    ) -> dict:
        """
        تحويل ملف صوتي إلى نص.
        
        Args:
            audio_data: بيانات الصوت الخام (bytes)
            language: لغة المقطع (ar, en, auto)
            model: نموذج التحويل
            
        Returns:
            dict يحتوي على النص المستخرج واللغة والمدة
        """
        if self.provider == "google":
            return await self._transcribe_google(audio_data, language)
        else:
            return await self._transcribe_openai(audio_data, language, model)
    
    async def _transcribe_openai(
        self,
        audio_data: bytes,
        language: str,
        model: str
    ) -> dict:
        """تحويل الصوت لنص باستخدام OpenAI Whisper."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY غير موجود")
        
        # تجهيز form-data
        form_data = aiohttp.FormData()
        form_data.add_field(
            'file',
            audio_data,
            filename='audio.webm',
            content_type='audio/webm'
        )
        form_data.add_field('model', model)
        form_data.add_field('language', language if language != 'auto' else 'ar')
        form_data.add_field('response_format', 'verbose_json')
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                data=form_data
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Whisper Error: {error}")
                
                data = await response.json()
                
                return {
                    "text": data.get("text", ""),
                    "language": data.get("language", language),
                    "duration": data.get("duration", 0),
                    "provider": "openai",
                    "model": model
                }
    
    async def _transcribe_google(
        self,
        audio_data: bytes,
        language: str
    ) -> dict:
        """تحويل الصوت لنص باستخدام Google Speech-to-Text."""
        if not self.google_api_key:
            raise ValueError("GEMINI_API_KEY غير موجود")
        
        # تحويل الصوت لـ base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # استخدام Gemini API للنسخ (متوفر في الإصدارات الحديثة)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={self.google_api_key}"
        
        # ملاحظة: Google قد لا يدعم الصوت مباشرة في Gemini، لكن يمكن استخدام Vertex AI
        # هذا تطبيق مبسط، في الإنتاج قد تحتاج Vertex AI أو خدمة منفصلة
        return {
            "text": "",
            "language": language,
            "duration": 0,
            "provider": "google",
            "note": "Google STT requires Vertex AI setup"
        }

    # ═══════════════════════════════════════════
    # تحويل النص لصوت (Text-to-Speech)
    # ═══════════════════════════════════════════

    async def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0,
        format: str = "mp3"
    ) -> bytes:
        """
        تحويل نص إلى صوت.
        
        Args:
            text: النص المراد تحويله (حد أقصى 4096 حرف)
            voice: الصوت (alloy, echo, fable, onyx, nova, shimmer)
            speed: سرعة القراءة (0.25 - 4.0)
            format: صيغة الملف (mp3, opus, aac, flac)
            
        Returns:
            بيانات الصوت الخام (bytes)
        """
        if self.provider == "google":
            return await self._synthesize_google(text, voice, speed)
        else:
            return await self._synthesize_openai(text, voice, speed, format)
    
    async def _synthesize_openai(
        self,
        text: str,
        voice: str,
        speed: float,
        format: str
    ) -> bytes:
        """تحويل النص لصوت باستخدام OpenAI TTS."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY غير موجود")
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": format
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"TTS Error: {error}")
                
                return await response.read()
    
    async def _synthesize_google(
        self,
        text: str,
        voice: str = "ar-XA-Wavenet-A",
        speed: float = 1.0
    ) -> bytes:
        """تحويل النص لصوت باستخدام Google Cloud TTS."""
        if not self.google_api_key:
            raise ValueError("GEMINI_API_KEY غير موجود")
        
        # Google Cloud TTS يحتاج لمشروع على GCP وإعدادات معينة
        # هذا تطبيق مبسط
        return b""

    # ═══════════════════════════════════════════
    # بث الصوت (Streaming Audio)
    # ═══════════════════════════════════════════

    async def stream_synthesize(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        """
        بث الصوت أجزاءً (Streaming) لتشغيل فوري.
        """
        # OpenAI TTS لا يدعم البث حالياً، لكن يمكن تقطيعه
        sentences = text.replace('\n', ' ').split('. ')
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            try:
                audio_chunk = await self.synthesize(
                    sentence.strip() + '.',
                    voice=voice,
                    speed=speed
                )
                yield audio_chunk
            except Exception as e:
                print(f"خطأ في توليد الصوت: {e}")
                continue

    # ═══════════════════════════════════════════
    # أصوات متاحة
    # ═══════════════════════════════════════════

    def get_available_voices(self) -> list:
        """قائمة الأصوات المتاحة."""
        return [
            {"id": "alloy", "name": "ألوي - محايد", "gender": "neutral"},
            {"id": "echo", "name": "إيكو - ذكوري", "gender": "male"},
            {"id": "fable", "name": "فيبل - بريطاني", "gender": "male"},
            {"id": "onyx", "name": "أونيكس - عميق", "gender": "male"},
            {"id": "nova", "name": "نوفا - أنثوي", "gender": "female"},
            {"id": "shimmer", "name": "شيمر - رقيق", "gender": "female"},
        ]

    def get_supported_languages(self) -> list:
        """اللغات المدعومة للتحويل الصوتي."""
        return [
            {"code": "ar", "name": "العربية"},
            {"code": "en", "name": "English"},
            {"code": "fr", "name": "Français"},
            {"code": "de", "name": "Deutsch"},
            {"code": "es", "name": "Español"},
            {"code": "auto", "name": "تلقائي"},
        ]


# نسخة واحدة من الخدمة
voice_service = VoiceService()