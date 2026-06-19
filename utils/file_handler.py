# utils/file_handler.py
import os
import uuid
import aiofiles
import mimetypes
from typing import List, Optional, Tuple
from datetime import datetime
from config.settings import settings


class FileHandler:
    """
    معالج الملفات - رفع، تخزين، فحص، واستخراج المحتوى.
    يدعم: صور، PDF، Word، نصوص، صوت، فيديو.
    """
    
    # ── الإعدادات ─────────────────────────
    UPLOAD_DIR = "storage/uploads"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 ميجابايت
    ALLOWED_EXTENSIONS = {
        # صور
        'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp',
        # مستندات
        'pdf', 'doc', 'docx', 'txt', 'md', 'csv', 'json', 'xml',
        # صوت
        'mp3', 'wav', 'ogg', 'webm', 'm4a', 'flac',
        # فيديو
        'mp4', 'avi', 'mov', 'mkv',
        # أرشيف
        'zip', 'rar'
    }
    
    ALLOWED_MIMETYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain', 'text/markdown', 'text/csv',
        'application/json',
        'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/webm', 'audio/mp4',
        'video/mp4', 'video/avi', 'video/quicktime',
        'application/zip', 'application/x-rar-compressed'
    }
    
    def __init__(self):
        self._ensure_upload_dir()
    
    def _ensure_upload_dir(self):
        """إنشاء مجلد التحميلات إذا لم يكن موجوداً."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        # إنشاء مجلدات فرعية حسب النوع
        for subdir in ['images', 'documents', 'audio', 'video', 'archives']:
            os.makedirs(os.path.join(self.UPLOAD_DIR, subdir), exist_ok=True)
    
    # ═══════════════════════════════════════════
    # التحقق من الملفات
    # ═══════════════════════════════════════════
    
    def validate_file(self, filename: str, file_size: int, mime_type: str = None) -> Tuple[bool, str]:
        """
        التحقق من صحة الملف قبل التخزين.
        
        Args:
            filename: اسم الملف
            file_size: حجم الملف بالبايت
            mime_type: نوع MIME للملف
            
        Returns:
            (نجاح, رسالة خطأ إن وجدت)
        """
        # التحقق من الامتداد
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"نوع الملف .{ext} غير مسموح به"
        
        # التحقق من الحجم
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE // (1024 * 1024)
            return False, f"حجم الملف كبير جداً (الحد الأقصى {max_mb}MB)"
        
        # التحقق من MIME type
        if mime_type and mime_type not in self.ALLOWED_MIMETYPES:
            return False, f"نوع الملف {mime_type} غير مسموح به"
        
        return True, ""
    
    def get_file_type(self, filename: str, mime_type: str = None) -> str:
        """
        تحديد نوع الملف: image, document, audio, video, archive.
        """
        if mime_type:
            if mime_type.startswith('image/'):
                return 'images'
            elif mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type in ['application/pdf', 'application/msword',
                               'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                               'text/plain', 'text/markdown', 'text/csv',
                               'application/json']:
                return 'documents'
            elif mime_type in ['application/zip', 'application/x-rar-compressed']:
                return 'archives'
        
        # التخمين من الامتداد
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext in {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'}:
            return 'images'
        elif ext in {'mp3', 'wav', 'ogg', 'webm', 'm4a', 'flac'}:
            return 'audio'
        elif ext in {'mp4', 'avi', 'mov', 'mkv'}:
            return 'video'
        elif ext in {'zip', 'rar'}:
            return 'archives'
        else:
            return 'documents'
    
    # ═══════════════════════════════════════════
    # تخزين الملفات
    # ═══════════════════════════════════════════
    
    async def save_file(
        self,
        file_data: bytes,
        filename: str,
        user_id: str = "default",
        mime_type: str = None
    ) -> dict:
        """
        حفظ ملف على القرص.
        
        Args:
            file_data: بيانات الملف الخام
            filename: اسم الملف الأصلي
            user_id: معرف المستخدم
            mime_type: نوع MIME
            
        Returns:
            dict يحتوي على معلومات الملف المحفوظ
        """
        # توليد اسم فريد
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        unique_name = f"{uuid.uuid4()}.{ext}"
        
        # تحديد المجلد الفرعي
        file_type = self.get_file_type(filename, mime_type)
        user_dir = os.path.join(self.UPLOAD_DIR, file_type, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # حفظ الملف
        file_path = os.path.join(user_dir, unique_name)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)
        
        # معلومات الملف
        file_size = len(file_data)
        relative_path = os.path.join(file_type, user_id, unique_name)
        
        return {
            "id": unique_name.split('.')[0],
            "filename": filename,
            "stored_name": unique_name,
            "path": relative_path,
            "full_path": file_path,
            "size": file_size,
            "type": file_type,
            "extension": ext,
            "mime_type": mime_type,
            "user_id": user_id,
            "uploaded_at": datetime.utcnow().isoformat(),
            "url": f"/uploads/{relative_path}"  # رابط الوصول العام
        }
    
    async def save_multiple(
        self,
        files: List[Tuple[bytes, str, str]],  # (data, filename, mime_type)
        user_id: str = "default"
    ) -> List[dict]:
        """
        حفظ عدة ملفات دفعة واحدة.
        """
        results = []
        for data, filename, mime_type in files:
            result = await self.save_file(data, filename, user_id, mime_type)
            results.append(result)
        return results
    
    # ═══════════════════════════════════════════
    # استخراج المحتوى
    # ═══════════════════════════════════════════
    
    async def extract_text(self, file_path: str, mime_type: str = None) -> str:
        """
        استخراج النص من ملف (PDF, Word, TXT).
        
        Args:
            file_path: مسار الملف الكامل
            mime_type: نوع MIME
            
        Returns:
            النص المستخرج
        """
        ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ''
        
        if ext == 'txt' or ext == 'md':
            return await self._extract_text_file(file_path)
        elif ext == 'pdf':
            return await self._extract_pdf(file_path)
        elif ext in ('doc', 'docx'):
            return await self._extract_docx(file_path)
        elif ext == 'csv':
            return await self._extract_csv(file_path)
        elif ext == 'json':
            return await self._extract_json(file_path)
        else:
            return f"[ملف: {file_path} - لا يمكن استخراج النص]"
    
    async def _extract_text_file(self, file_path: str) -> str:
        """استخراج النص من ملف نصي."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except UnicodeDecodeError:
            async with aiofiles.open(file_path, 'r', encoding='latin-1') as f:
                return await f.read()
    
    async def _extract_pdf(self, file_path: str) -> str:
        """استخراج النص من PDF باستخدام PyPDF2."""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return '\n\n'.join(text_parts) or "[ملف PDF لا يحتوي على نص قابل للاستخراج]"
        except ImportError:
            return "[PDF: تحتاج تثبيت PyPDF2 - pip install PyPDF2]"
    
    async def _extract_docx(self, file_path: str) -> str:
        """استخراج النص من Word."""
        try:
            from docx import Document
            doc = Document(file_path)
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            return '\n'.join(text_parts) or "[مستند فارغ]"
        except ImportError:
            return "[Word: تحتاج تثبيت python-docx - pip install python-docx]"
    
    async def _extract_csv(self, file_path: str) -> str:
        """استخراج النص من CSV."""
        content = await self._extract_text_file(file_path)
        lines = content.strip().split('\n')
        if len(lines) > 50:
            return '\n'.join(lines[:50]) + f"\n... (و {len(lines) - 50} صف إضافي)"
        return content
    
    async def _extract_json(self, file_path: str) -> str:
        """استخراج النص من JSON بشكل منظم."""
        content = await self._extract_text_file(file_path)
        try:
            import json
            data = json.loads(content)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except:
            return content
    
    # ═══════════════════════════════════════════
    # قراءة الملفات
    # ═══════════════════════════════════════════
    
    async def read_file(self, file_path: str) -> Optional[bytes]:
        """
        قراءة ملف من القرص.
        """
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        except FileNotFoundError:
            return None
    
    async def get_file_info(self, file_path: str) -> dict:
        """
        معلومات عن ملف موجود.
        """
        try:
            stat = os.stat(file_path)
            filename = os.path.basename(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                "filename": filename,
                "size": stat.st_size,
                "mime_type": mime_type,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "exists": True
            }
        except FileNotFoundError:
            return {"exists": False, "filename": os.path.basename(file_path)}
    
    # ═══════════════════════════════════════════
    # تنظيف
    # ═══════════════════════════════════════════
    
    async def delete_file(self, file_path: str) -> bool:
        """حذف ملف."""
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return False
    
    def get_absolute_path(self, relative_path: str) -> str:
        """تحويل مسار نسبي لمطلق."""
        return os.path.join(self.UPLOAD_DIR, relative_path)
    
    def get_public_url(self, relative_path: str) -> str:
        """الحصول على رابط الوصول العام للملف."""
        return f"/uploads/{relative_path}"


# نسخة واحدة من المعالج
file_handler = FileHandler()