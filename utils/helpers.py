"""
utils/helpers.py
ملف الدوال المساعدة العامة لمنصة SAIF.AI
يحتوي على دوال للنصوص، الوقت، القوائم، التنسيق، التحقق، التنفيذ، وغيرها
"""

import re
import json
import asyncio
import uuid
import random
import string
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
from functools import wraps
import time
import hashlib


# ═══════════════════════════════════════════════════════════════════
# 1. دوال النصوص (Strings)
# ═══════════════════════════════════════════════════════════════════

def clean_text(text: str, max_length: int = 8000) -> str:
    """
    تنظيف النص من الأحرف غير المرغوب فيها.
    
    Args:
        text: النص المراد تنظيفه
        max_length: الحد الأقصى لطول النص
        
    Returns:
        النص النظيف
    """
    if not text:
        return ""
    
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # مسافات متعددة -> مسافة واحدة
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)  # أحرف تحكم
    text = re.sub(r'[<>]', '', text)  # إزالة علامات HTML
    text = re.sub(r'https?://\S+', '[رابط]', text)  # إخفاء الروابط (للخصوصية)
    
    return text[:max_length]


def extract_json_from_text(text: str) -> Optional[Dict]:
    """
    استخراج JSON من نص (حتى لو كان محاطاً بـ ```json).
    
    Args:
        text: النص المراد استخراج JSON منه
        
    Returns:
        قاموس JSON أو None
    """
    if not text:
        return None
    
    # محاولة استخراج JSON من markdown
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        text = json_match.group(1)
    
    # محاولة تحليل JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # محاولة إصلاح JSON مقطوع
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except:
            pass
        return None


def truncate_with_context(text: str, max_length: int = 500, context_ratio: float = 0.3) -> str:
    """
    قص النص مع الحفاظ على السياق (البداية والنهاية).
    
    Args:
        text: النص المراد قصه
        max_length: الحد الأقصى للطول
        context_ratio: نسبة النهاية المحتفظ بها (0.0 - 1.0)
        
    Returns:
        النص المختصر
    """
    if len(text) <= max_length:
        return text
    
    keep_start = int(max_length * (1 - context_ratio))
    keep_end = max_length - keep_start - 3  # 3 للـ "..."
    
    return f"{text[:keep_start]}...{text[-keep_end:]}"


def extract_hashtags(text: str) -> List[str]:
    """
    استخراج الهاشتاجات من النص.
    
    Args:
        text: النص المراد استخراج الهاشتاجات منه
        
    Returns:
        قائمة الهاشتاجات
    """
    return re.findall(r'#[\w\u0600-\u06FF]+', text)


def replace_emojis(text: str) -> str:
    """
    استبدال الإيموجي بنصوص بديلة (للتخزين في قاعدة البيانات).
    
    Args:
        text: النص المراد استبدال الإيموجي فيه
        
    Returns:
        النص بعد الاستبدال
    """
    emoji_map = {
        '😊': ':smile:',
        '😂': ':joy:',
        '❤️': ':heart:',
        '👍': ':thumbsup:',
        '🔥': ':fire:',
        '✨': ':sparkles:',
        '💡': ':bulb:',
        '📌': ':pushpin:',
        '🎨': ':art:',
        '🧠': ':brain:',
        '📷': ':camera:',
        '🎤': ':microphone:',
        '📎': ':paperclip:',
        '📄': ':document:',
    }
    
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)
    
    return text


def slugify(text: str) -> str:
    """
    تحويل النص إلى slug صالح للـ URL.
    
    Args:
        text: النص المراد تحويله
        
    Returns:
        slug صالح
    """
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)  # إزالة الرموز غير المسموحة
    text = re.sub(r'[\s_-]+', '-', text)  # مسافات -> شرطة
    text = re.sub(r'^-+|-+$', '', text)  # إزالة الشرط من البداية والنهاية
    return text or 'untitled'


def normalize_arabic(text: str) -> str:
    """
    تطبيع النص العربي (توحيد الحروف المتشابهة).
    
    Args:
        text: النص العربي
        
    Returns:
        النص المطبع
    """
    arabic_map = {
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا',  # توحيد الألف
        'ة': 'ه',  # توحيد التاء المربوطة
        'ى': 'ا',  # توحيد الألف المقصورة
        'ؤ': 'ء', 'ئ': 'ء',  # توحيد الهمزة
    }
    
    for char, replacement in arabic_map.items():
        text = text.replace(char, replacement)
    
    return text


# ═══════════════════════════════════════════════════════════════════
# 2. دوال الوقت والتاريخ (Time & Date)
# ═══════════════════════════════════════════════════════════════════

def now_iso() -> str:
    """الوقت الحالي بصيغة ISO."""
    return datetime.utcnow().isoformat() + "Z"


def format_arabic_date(dt: datetime = None) -> str:
    """
    تنسيق التاريخ بالعربية.
    
    Args:
        dt: التاريخ المطلوب تنسيقه (افتراضي: الوقت الحالي)
        
    Returns:
        التاريخ بصيغة عربية
    """
    if dt is None:
        dt = datetime.utcnow()
    
    days = {
        0: 'الأحد', 1: 'الإثنين', 2: 'الثلاثاء',
        3: 'الأربعاء', 4: 'الخميس', 5: 'الجمعة', 6: 'السبت'
    }
    
    months = {
        1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
        5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
        9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
    }
    
    return f"{days[dt.weekday()]}، {dt.day} {months[dt.month]} {dt.year}"


def time_ago(dt: datetime) -> str:
    """
    تحويل الوقت لصيغة 'منذ X دقيقة' بالعربية.
    
    Args:
        dt: الوقت المطلوب تحويله
        
    Returns:
        نص زمني بالعربية
    """
    diff = datetime.utcnow() - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "منذ لحظات"
    if seconds < 3600:
        mins = int(seconds // 60)
        return f"منذ {mins} {'دقيقة' if mins == 1 else 'دقائق'}"
    if seconds < 86400:
        hours = int(seconds // 3600)
        return f"منذ {hours} {'ساعة' if hours == 1 else 'ساعات'}"
    if seconds < 604800:
        days = int(seconds // 86400)
        return f"منذ {days} {'يوم' if days == 1 else 'أيام'}"
    if seconds < 2592000:
        weeks = int(seconds // 604800)
        return f"منذ {weeks} {'أسبوع' if weeks == 1 else 'أسابيع'}"
    
    months = int(seconds // 2592000)
    if months < 12:
        return f"منذ {months} {'شهر' if months == 1 else 'أشهر'}"
    
    years = int(seconds // 31536000)
    return f"منذ {years} {'عام' if years == 1 else 'أعوام'}"


def parse_date(date_str: str, formats: List[str] = None) -> Optional[datetime]:
    """
    محاولة تحويل نص إلى تاريخ باستخدام صيغ متعددة.
    
    Args:
        date_str: النص المراد تحويله
        formats: قائمة الصيغ الممكنة
        
    Returns:
        كائن datetime أو None
    """
    if not date_str:
        return None
    
    if formats is None:
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def get_day_range(date: datetime = None) -> Tuple[datetime, datetime]:
    """
    الحصول على بداية ونهاية اليوم.
    
    Args:
        date: التاريخ المطلوب (افتراضي: اليوم)
        
    Returns:
        (بداية اليوم, نهاية اليوم)
    """
    if date is None:
        date = datetime.utcnow()
    
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1) - timedelta(microseconds=1)
    
    return start, end


# ═══════════════════════════════════════════════════════════════════
# 3. دوال القوائم والمجموعات (Lists & Sets)
# ═══════════════════════════════════════════════════════════════════

def chunk_list(lst: List[Any], size: int) -> List[List[Any]]:
    """
    تقسيم قائمة إلى أجزاء متساوية.
    
    Args:
        lst: القائمة المراد تقسيمها
        size: حجم كل جزء
        
    Returns:
        قائمة من الأجزاء
    """
    if size <= 0:
        return []
    
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def unique_preserve_order(lst: List[Any]) -> List[Any]:
    """
    إزالة المكررات مع الحفاظ على الترتيب.
    
    Args:
        lst: القائمة المراد تنظيفها
        
    Returns:
        قائمة بدون مكررات
    """
    seen = set()
    return [x for x in lst if not (x in seen or seen.add(x))]


def group_by_key(items: List[Dict], key: str) -> Dict[str, List[Dict]]:
    """
    تجميع قائمة من القواميس حسب مفتاح معين.
    
    Args:
        items: قائمة القواميس
        key: المفتاح المستخدم للتجميع
        
    Returns:
        قاموس المجموعات
    """
    result = {}
    for item in items:
        k = item.get(key)
        if k is None:
            continue
        if k not in result:
            result[k] = []
        result[k].append(item)
    
    return result


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    تسطيح قاموس متداخل.
    
    Args:
        d: القاموس المتداخل
        parent_key: المفتاح الأب
        sep: الفاصل بين المفاتيح
        
    Returns:
        قاموس مسطح
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}{sep}{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}{sep}{i}", item))
        else:
            items.append((new_key, v))
    
    return dict(items)


def find_in_list(lst: List[Any], key: str, value: Any) -> Optional[Any]:
    """
    البحث عن عنصر في قائمة حسب مفتاح وقيمة.
    
    Args:
        lst: القائمة المراد البحث فيها
        key: المفتاح
        value: القيمة المطلوبة
        
    Returns:
        العنصر الموجود أو None
    """
    for item in lst:
        if isinstance(item, dict) and item.get(key) == value:
            return item
        if hasattr(item, key) and getattr(item, key) == value:
            return item
    
    return None


def sort_by_key(items: List[Dict], key: str, reverse: bool = False) -> List[Dict]:
    """
    ترتيب قائمة قواميس حسب مفتاح.
    
    Args:
        items: قائمة القواميس
        key: مفتاح الترتيب
        reverse: ترتيب تنازلي
        
    Returns:
        قائمة مرتبة
    """
    return sorted(items, key=lambda x: x.get(key, 0), reverse=reverse)


# ═══════════════════════════════════════════════════════════════════
# 4. دوال التنسيق (Formatting)
# ═══════════════════════════════════════════════════════════════════

def format_size(bytes_count: int) -> str:
    """
    تحويل حجم الملف لصيغة مقروءة.
    
    Args:
        bytes_count: عدد البايتات
        
    Returns:
        حجم مقروء (مثال: 2.5 MB)
    """
    if bytes_count < 1024:
        return f"{bytes_count} B"
    if bytes_count < 1024 ** 2:
        return f"{bytes_count / 1024:.1f} KB"
    if bytes_count < 1024 ** 3:
        return f"{bytes_count / 1024 ** 2:.1f} MB"
    if bytes_count < 1024 ** 4:
        return f"{bytes_count / 1024 ** 3:.2f} GB"
    return f"{bytes_count / 1024 ** 4:.2f} TB"


def format_number(num: Union[int, float]) -> str:
    """
    تنسيق الأرقام بفواصل (مثال: 1,234,567).
    
    Args:
        num: الرقم المراد تنسيقه
        
    Returns:
        رقم بتنسيق عربي
    """
    if isinstance(num, int):
        return f"{num:,}".replace(',', '،')
    
    if isinstance(num, float):
        formatted = f"{num:,.2f}".replace(',', '،')
        return formatted


def format_duration(seconds: float) -> str:
    """
    تحويل الثواني لصيغة HH:MM:SS.
    
    Args:
        seconds: عدد الثواني
        
    Returns:
        صيغة الوقت
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_percentage(value: float, total: float, decimals: int = 1) -> str:
    """
    حساب وتنسيق النسبة المئوية.
    
    Args:
        value: القيمة
        total: الإجمالي
        decimals: عدد الخانات العشرية
        
    Returns:
        النسبة المئوية (مثال: 75.5%)
    """
    if total == 0:
        return "0%"
    
    percentage = (value / total) * 100
    return f"{percentage:.{decimals}f}%"


def mask_text(text: str, visible_start: int = 4, visible_end: int = 4) -> str:
    """
    إخفاء وسط النص (مثال: saif...abc).
    
    Args:
        text: النص المراد إخفاؤه
        visible_start: عدد الأحرف الظاهرة في البداية
        visible_end: عدد الأحرف الظاهرة في النهاية
        
    Returns:
        النص المخفي
    """
    if len(text) <= visible_start + visible_end:
        return "*" * len(text)
    return text[:visible_start] + "*" * (len(text) - visible_start - visible_end) + text[-visible_end:]


# ═══════════════════════════════════════════════════════════════════
# 5. دوال التحقق (Validation)
# ═══════════════════════════════════════════════════════════════════

def is_valid_uuid(uuid_string: str) -> bool:
    """
    التحقق من صحة UUID.
    
    Args:
        uuid_string: النص المراد التحقق منه
        
    Returns:
        True إذا كان UUID صالحاً
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def is_valid_email(email: str) -> bool:
    """
    التحقق من صحة البريد الإلكتروني.
    
    Args:
        email: البريد الإلكتروني
        
    Returns:
        True إذا كان صالحاً
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """
    التحقق من صحة رقم الهاتف المصري.
    
    Args:
        phone: رقم الهاتف
        
    Returns:
        True إذا كان صالحاً
    """
    if not phone:
        return False
    
    # إزالة المسافات والرموز غير الرقمية
    phone = re.sub(r'[^\d+]', '', phone)
    pattern = r'^(\+?2?0?1[0125]\d{8})$'
    return bool(re.match(pattern, phone))


def is_valid_url(url: str) -> bool:
    """
    التحقق من صحة URL.
    
    Args:
        url: الرابط المراد التحقق منه
        
    Returns:
        True إذا كان صالحاً
    """
    if not url:
        return False
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def is_arabic_text(text: str, threshold: float = 0.5) -> bool:
    """
    التحقق مما إذا كان النص عربياً بنسبة معينة.
    
    Args:
        text: النص المراد التحقق منه
        threshold: النسبة المئوية للحروف العربية (0.0 - 1.0)
        
    Returns:
        True إذا كان النص عربياً
    """
    if not text:
        return False
    
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    ratio = arabic_chars / len(text)
    
    return ratio >= threshold


# ═══════════════════════════════════════════════════════════════════
# 6. دوال المعرفات الفريدة (IDs & Tokens)
# ═══════════════════════════════════════════════════════════════════

def generate_short_id(length: int = 8) -> str:
    """
    توليد ID قصير عشوائي.
    
    Args:
        length: طول المعرف
        
    Returns:
        معرف قصير
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_secure_token(length: int = 32) -> str:
    """
    توليد رمز آمن.
    
    Args:
        length: طول الرمز
        
    Returns:
        رمز آمن
    """
    import secrets
    return secrets.token_urlsafe(length)


def generate_session_id() -> str:
    """
    توليد معرف جلسة فريد.
    
    Returns:
        معرف جلسة
    """
    return f"session_{int(time.time() * 1000)}_{generate_short_id(6)}"


def generate_message_id() -> str:
    """
    توليد معرف رسالة فريد.
    
    Returns:
        معرف رسالة
    """
    return f"msg_{uuid.uuid4().hex[:12]}"


# ═══════════════════════════════════════════════════════════════════
# 7. دوال التنفيذ (Execution Helpers)
# ═══════════════════════════════════════════════════════════════════

async def retry_async(
    func: Callable,
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    إعادة محاولة تنفيذ دالة غير متزامنة عند الفشل.
    
    Args:
        func: الدالة غير المتزامنة
        retries: عدد المحاولات
        delay: التأخير الأولي بالثواني
        backoff: مضاعفة التأخير
        exceptions: الاستثناءات التي يتم إعادة المحاولة لها
        
    Returns:
        نتيجة الدالة
        
    Raises:
        آخر استثناء حدث
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(retries):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < retries - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff
    
    raise last_exception


def retry_sync(
    func: Callable,
    retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    نسخة متزامنة من retry_async.
    
    Args:
        func: الدالة المتزامنة
        retries: عدد المحاولات
        delay: التأخير بالثواني
        exceptions: الاستثناءات التي يتم إعادة المحاولة لها
        
    Returns:
        نتيجة الدالة
    """
    last_exception = None
    
    for attempt in range(retries):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < retries - 1:
                time.sleep(delay)
    
    raise last_exception


async def timeout_async(func: Callable, timeout_seconds: float = 30) -> Any:
    """
    تنفيذ دالة غير متزامنة مع حد زمني.
    
    Args:
        func: الدالة غير المتزامنة
        timeout_seconds: الحد الزمني بالثواني
        
    Returns:
        نتيجة الدالة
        
    Raises:
        TimeoutError: إذا انتهى الوقت
    """
    try:
        return await asyncio.wait_for(func(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"انتهى الوقت المحدد ({timeout_seconds} ثانية)")


def measure_time(func: Callable) -> Callable:
    """
    ديكوراتور لقياس وقت تنفيذ الدالة المتزامنة.
    
    Args:
        func: الدالة المراد قياس وقتها
        
    Returns:
        الدالة مع قياس الوقت
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        wrapper.last_duration = elapsed
        print(f"⏱️ {func.__name__} took {elapsed:.3f}s")
        return result
    
    wrapper.last_duration = 0
    return wrapper


# ═══════════════════════════════════════════════════════════════════
# 8. ديكوراتورز (Decorators)
# ═══════════════════════════════════════════════════════════════════

def timed(logger=None):
    """
    ديكوراتور لقياس وقت تنفيذ الدالة (يدعم المتزامن وغير المتزامن).
    
    Usage:
        @timed()
        async def my_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                if logger:
                    logger.info(f"{func.__name__} took {elapsed:.3f}s")
                print(f"⏱️ {func.__name__} took {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                if logger:
                    logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                if logger:
                    logger.info(f"{func.__name__} took {elapsed:.3f}s")
                print(f"⏱️ {func.__name__} took {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                if logger:
                    logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def safe_execute(default_return=None, log_error: bool = True):
    """
    ديكوراتور لتنفيذ آمن - يعيد قيمة افتراضية عند الفشل.
    
    Usage:
        @safe_execute(default_return=[])
        def risky_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    print(f"⚠️ {func.__name__} failed: {e}")
                return default_return
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    print(f"⚠️ {func.__name__} failed: {e}")
                return default_return
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def cache_result(ttl: int = 3600):
    """
    ديكوراتور لتخزين نتيجة الدالة في الذاكرة المؤقتة.
    
    Usage:
        @cache_result(ttl=60)
        def expensive_function():
            ...
    """
    cache = {}
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # توليد مفتاح الكاش
            key = f"{func.__name__}:{args}:{kwargs}"
            key_hash = hashlib.md5(key.encode()).hexdigest()
            
            # التحقق من الكاش
            if key_hash in cache:
                cached_data, timestamp = cache[key_hash]
                if time.time() - timestamp < ttl:
                    return cached_data
            
            # تنفيذ الدالة
            result = func(*args, **kwargs)
            cache[key_hash] = (result, time.time())
            return result
        
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════
# 9. دوال خاصة بـ SAIF.AI
# ═══════════════════════════════════════════════════════════════════

def generate_session_title(first_message: str, response: str = None) -> str:
    """
    توليد عنوان تلقائي للمحادثة من أول رسالة.
    
    Args:
        first_message: أول رسالة من المستخدم
        response: أول رد من المساعد (اختياري)
        
    Returns:
        عنوان المحادثة
    """
    if not first_message:
        return "محادثة جديدة"
    
    # استخدام أول 50 حرف كعنوان
    title = first_message[:50].strip()
    if len(first_message) > 50:
        title += "..."
    
    return title


def extract_user_intent(text: str) -> Dict[str, Union[str, float]]:
    """
    تحليل نية المستخدم من النص.
    
    Args:
        text: النص المراد تحليله
        
    Returns:
        قاموس يحتوي على النية ودرجة الثقة
    """
    intents = {
        'question': ['?', 'ما', 'ماذا', 'كيف', 'لماذا', 'متى', 'أين', 'هل', 'من'],
        'command': ['افعل', 'قم', 'انشئ', 'ارسل', 'احذف', 'غير', 'عدل'],
        'greeting': ['مرحباً', 'السلام', 'اهلا', 'مرحبا', 'صباح', 'مساء'],
        'farewell': ['مع السلامة', 'وداعاً', 'سلام', 'باي', 'الى اللقاء'],
        'complaint': ['شكوى', 'مشكلة', 'خطأ', 'لا يعمل', 'بطيء'],
        'feedback': ['اقتراح', 'فكرة', 'تحسين', 'تطوير'],
    }
    
    text_lower = text.lower()
    scores = {}
    
    for intent, keywords in intents.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[intent] = score / len(keywords) if keywords else 0
    
    best_intent = max(scores, key=scores.get)
    
    return {
        'intent': best_intent,
        'confidence': scores[best_intent],
        'all_scores': scores
    }


def is_system_command(text: str) -> bool:
    """
    التحقق مما إذا كان النص أمر نظام.
    
    Args:
        text: النص المراد التحقق منه
        
    Returns:
        True إذا كان أمر نظام
    """
    system_patterns = [
        r'(?:غير|حول|بدل).*(?:الثيم|اللون|المظهر)',
        r'(?:فعل|شغل|افتح|أوقف|اقفل|عطل).*(?:الوضع الليلي|الداكن)',
        r'(?:امسح|نظف).*(?:الكاش|الذاكرة)',
        r'(?:اعرض|وريني).*(?:الإحصائيات)',
        r'(?:احذف|امسح).*(?:المحادثات|الدردشات)',
        r'(?:غير|عدل).*(?:السرعة|سرعة الكتابة)',
        r'(?:فعل|شغل|أوقف).*(?:التفكير|وضع التفكير)',
        r'(?:سجل|سجلني|سجل صوت)',
        r'(?:صور|التقط|كاميرا)',
    ]
    
    return any(re.search(p, text, re.IGNORECASE) for p in system_patterns)


def get_persona_from_text(text: str) -> Optional[str]:
    """
    استخراج الشخصية من النص (إذا طلب المستخدم تغييرها).
    
    Args:
        text: النص المراد تحليله
        
    Returns:
        اسم الشخصية أو None
    """
    patterns = [
        r'(?:غير|بدل|تغيير|تبديل)\s*(?:الشخصية|شخصيتي|البيرسونا)\s*(?:إلى|لـ)?\s*([^\s]+(?:\s[^\s]+){0,3})',
        r'شخصية\s*(?:جديدة)?\s*["\']?([^"\']+)["\']?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 10. دوال السجل والتنظيف (Logging & Cleanup)
# ═══════════════════════════════════════════════════════════════════

def log_safe(data: Any, max_length: int = 1000) -> str:
    """
    تنسيق بيانات للسجل مع إخفاء المعلومات الحساسة.
    
    Args:
        data: البيانات المراد تنسيقها
        max_length: الحد الأقصى للطول
        
    Returns:
        نص آمن للسجل
    """
    if isinstance(data, dict):
        sensitive_keys = {'password', 'token', 'api_key', 'secret', 'key', 'auth', 'credential'}
        safe_data = {}
        
        for k, v in data.items():
            if any(s in k.lower() for s in sensitive_keys):
                safe_data[k] = '***'
            elif isinstance(v, str) and len(v) > max_length:
                safe_data[k] = truncate_with_context(v, max_length)
            else:
                safe_data[k] = v
        
        return json.dumps(safe_data, ensure_ascii=False, default=str)
    
    if isinstance(data, str) and len(data) > max_length:
        return truncate_with_context(data, max_length)
    
    return str(data)[:max_length]


async def cleanup_temp_files(directory: str, older_than_hours: int = 24) -> int:
    """
    حذف الملفات المؤقتة الأقدم من عدد ساعات معين.
    
    Args:
        directory: المجلد المراد تنظيفه
        older_than_hours: العمر بالساعات
        
    Returns:
        عدد الملفات المحذوفة
    """
    import os
    from pathlib import Path
    
    cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
    deleted = 0
    
    for file_path in Path(directory).rglob('*'):
        if file_path.is_file():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff:
                try:
                    os.remove(file_path)
                    deleted += 1
                except:
                    pass
    
    return deleted


def get_client_ip(request) -> str:
    """
    استخراج IP المستخدم من الـ request.
    
    Args:
        request: كائن الطلب (FastAPI)
        
    Returns:
        عنوان IP
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    return request.client.host if request.client else "unknown"


def is_mobile_agent(user_agent: str) -> bool:
    """
    التحقق مما إذا كان الطلب من موبايل.
    
    Args:
        user_agent: User-Agent من الطلب
        
    Returns:
        True إذا كان موبايل
    """
    if not user_agent:
        return False
    
    mobile_patterns = ['android', 'iphone', 'ipad', 'mobile', 'phone', 'blackberry', 'windows phone']
    user_agent_lower = user_agent.lower()
    
    return any(p in user_agent_lower for p in mobile_patterns)


# ═══════════════════════════════════════════════════════════════════
# 11. دوال القواميس (Dictionary Helpers)
# ═══════════════════════════════════════════════════════════════════

def merge_dicts(dict1: dict, dict2: dict, deep: bool = True) -> dict:
    """
    دمج قاموسين (مع دعم التداخل).
    
    Args:
        dict1: القاموس الأول
        dict2: القاموس الثاني
        deep: دمج عميق أو سطحي
        
    Returns:
        القاموس المدمج
    """
    if not deep:
        return {**dict1, **dict2}
    
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value, deep=True)
        else:
            result[key] = value
    
    return result


def filter_dict_keys(data: Dict, keys_to_keep: List[str]) -> Dict:
    """
    تصفية قاموس للاحتفاظ بمفاتيح محددة فقط.
    
    Args:
        data: القاموس الأصلي
        keys_to_keep: المفاتيح المطلوب الاحتفاظ بها
        
    Returns:
        قاموس جديد بالمفاتيح المحددة
    """
    return {k: v for k, v in data.items() if k in keys_to_keep}


def exclude_dict_keys(data: Dict, keys_to_exclude: List[str]) -> Dict:
    """
    تصفية قاموس لإزالة مفاتيح محددة.
    
    Args:
        data: القاموس الأصلي
        keys_to_exclude: المفاتيح المطلوب إزالتها
        
    Returns:
        قاموس جديد بدون المفاتيح المستبعدة
    """
    return {k: v for k, v in data.items() if k not in keys_to_exclude}


def safe_get(data: Dict, keys: List[str], default: Any = None) -> Any:
    """
    استرجاع قيمة من قاموس متداخل بأمان.
    
    Args:
        data: القاموس
        keys: قائمة المفاتيح (متدرجة)
        default: القيمة الافتراضية عند عدم وجود المفتاح
        
    Returns:
        القيمة أو default
    """
    result = data
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    return result


# ═══════════════════════════════════════════════════════════════════
# 12. دوال الملفات (File Helpers)
# ═══════════════════════════════════════════════════════════════════

def get_file_extension(filename: str) -> str:
    """
    استخراج امتداد الملف.
    
    Args:
        filename: اسم الملف
        
    Returns:
        الامتداد (بدون النقطة)
    """
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


def get_mime_type(filename: str) -> str:
    """
    تخمين نوع MIME للملف.
    
    Args:
        filename: اسم الملف
        
    Returns:
        نوع MIME
    """
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def is_image_file(filename: str) -> bool:
    """
    التحقق مما إذا كان الملف صورة.
    
    Args:
        filename: اسم الملف
        
    Returns:
        True إذا كان صورة
    """
    image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico', 'tiff'}
    ext = get_file_extension(filename)
    return ext in image_extensions


def is_document_file(filename: str) -> bool:
    """
    التحقق مما إذا كان الملف مستنداً.
    
    Args:
        filename: اسم الملف
        
    Returns:
        True إذا كان مستنداً
    """
    doc_extensions = {'pdf', 'doc', 'docx', 'txt', 'md', 'csv', 'json', 'xml', 'xls', 'xlsx', 'ppt', 'pptx'}
    ext = get_file_extension(filename)
    return ext in doc_extensions


# ═══════════════════════════════════════════════════════════════════
# تصدير الدوال الأكثر استخداماً لتسهيل الاستيراد
# ═══════════════════════════════════════════════════════════════════

__all__ = [
    # نصوص
    'clean_text', 'extract_json_from_text', 'truncate_with_context',
    'extract_hashtags', 'replace_emojis', 'slugify', 'normalize_arabic',
    
    # وقت
    'now_iso', 'format_arabic_date', 'time_ago', 'parse_date', 'get_day_range',
    
    # قوائم
    'chunk_list', 'unique_preserve_order', 'group_by_key', 'flatten_dict',
    'find_in_list', 'sort_by_key',
    
    # تنسيق
    'format_size', 'format_number', 'format_duration', 'format_percentage', 'mask_text',
    
    # تحقق
    'is_valid_uuid', 'is_valid_email', 'is_valid_phone', 'is_valid_url', 'is_arabic_text',
    
    # معرفات
    'generate_short_id', 'generate_secure_token', 'generate_session_id', 'generate_message_id',
    
    # تنفيذ
    'retry_async', 'retry_sync', 'timeout_async', 'measure_time',
    
    # ديكوراتورز
    'timed', 'safe_execute', 'cache_result',
    
    # خاصة بـ SAIF.AI
    'generate_session_title', 'extract_user_intent', 'is_system_command', 'get_persona_from_text',
    
    # سجل وتنظيف
    'log_safe', 'cleanup_temp_files', 'get_client_ip', 'is_mobile_agent',
    
    # قواميس
    'merge_dicts', 'filter_dict_keys', 'exclude_dict_keys', 'safe_get',
    
    # ملفات
    'get_file_extension', 'get_mime_type', 'is_image_file', 'is_document_file',
]