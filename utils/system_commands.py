# utils/system_commands.py
import json
import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class CommandResult:
    """نتيجة تنفيذ أمر نظام."""
    success: bool
    message: str
    action: str = ""
    data: dict = field(default_factory=dict)


class SystemCommands:
    """
    معالج أوامر النظام.
    يستخرج الأوامر من ردود الـ AI وينفذها على المنصة.
    
    الأوامر المدعومة:
    - تغيير الثيم والوضع الليلي
    - إدارة المحادثات
    - مسح الكاش
    - عرض الإحصائيات
    - تغيير سرعة الكتابة
    - تفعيل/تعطيل وضع التفكير
    - تغيير الشخصية
    - إيقاف التوليد
    - إعادة التوليد
    """
    
    def __init__(self):
        self._register_commands()
    
    def _register_commands(self):
        """تسجيل كل الأوامر وأنماط التعرف عليها."""
        self.commands = [
            {
                "name": "change_theme",
                "patterns": [
                    r"(?:غير|حول|بدل|تغيير)\s*(?:الثيم|اللون|المظهر|الوان|ألوان|الخلفية)\s*(?:إلى|لـ|الي|الى)?\s*(\S+)",
                    r"(?:اجعل|خلي|خلّي)\s*(?:الثيم|اللون|المظهر)\s*(\S+)",
                    r"theme\s+(\w+)",
                ],
                "params": ["color"],
                "description": "تغيير ثيم المنصة"
            },
            {
                "name": "toggle_dark_mode",
                "patterns": [
                    r"(?:فعل|شغل|افتح|شغّل|فعّل)\s*(?:الوضع|المظهر|الوضع الليلي|الداكن|الغامق|الليلي)",
                    r"dark\s*mode\s*on",
                ],
                "params": [],
                "action": "enable"
            },
            {
                "name": "toggle_dark_mode",
                "patterns": [
                    r"(?:أوقف|اقفل|عطل|أغلق|عطّل)\s*(?:الوضع|المظهر|الوضع الليلي|الداكن|الغامق|الليلي)",
                    r"dark\s*mode\s*off",
                ],
                "params": [],
                "action": "disable"
            },
            {
                "name": "clear_cache",
                "patterns": [
                    r"(?:امسح|نظف|افرغ|مسح|تنظيف|افراغ|حذف)\s*(?:الكاش|الذاكرة المؤقتة|cache|الكاش)",
                    r"clear\s*cache",
                ],
                "params": [],
                "description": "مسح الذاكرة المؤقتة"
            },
            {
                "name": "show_stats",
                "patterns": [
                    r"(?:اعرض|وريني|هات|أظهر|عرض|إظهار)\s*(?:الإحصائيات|الإحصاءات|إحصائيات|تقرير|الاحصائيات|احصائيات|تقرير الاستخدام)",
                    r"show\s*stats",
                ],
                "params": [],
                "description": "عرض إحصائيات المنصة"
            },
            {
                "name": "delete_old_chats",
                "patterns": [
                    r"(?:احذف|امسح|حذف|مسح)\s*(?:المحادثات|المحادثات القديمة|المحادثات المؤرشفة|كل المحادثات)",
                    r"delete\s*(?:old\s*)?chats",
                ],
                "params": [],
                "description": "حذف المحادثات القديمة"
            },
            {
                "name": "change_speed",
                "patterns": [
                    r"(?:غير|عدل|تغيير|تعديل)\s*(?:سرعة|سرعة الكتابة|سرعة الرد)\s*(?:إلى|لـ)?\s*(سريعة|بطيئة|متوسطة|عالية|منخفضة|سريع|بطيء|متوسط|عالي|منخفض)",
                    r"speed\s+(fast|slow|medium)",
                ],
                "params": ["speed"],
                "description": "تغيير سرعة عرض الرد"
            },
            {
                "name": "toggle_thinking",
                "patterns": [
                    r"(?:فعل|شغل|افتح|شغّل|فعّل)\s*(?:وضع|خاصية|نمط)\s*(?:التفكير|التفكير العميق|التفكير)",
                    r"thinking\s*on",
                ],
                "params": [],
                "action": "enable"
            },
            {
                "name": "toggle_thinking",
                "patterns": [
                    r"(?:أوقف|اقفل|عطل|أغلق|عطّل)\s*(?:وضع|خاصية|نمط)\s*(?:التفكير|التفكير العميق|التفكير)",
                    r"thinking\s*off",
                ],
                "params": [],
                "action": "disable"
            },
            {
                "name": "change_persona",
                "patterns": [
                    r"(?:غير|بدل|تغيير|تبديل)\s*(?:الشخصية|شخصيتي|البيرسونا)\s*(?:إلى|لـ)?\s*(.+)",
                ],
                "params": ["persona"],
                "description": "تغيير شخصية المساعد"
            },
            {
                "name": "stop_generation",
                "patterns": [
                    r"(?:أوقف|اقفل|أبطل|إيقاف|وقف)\s*(?:التوليد|الكتابة|الرد|البث)",
                    r"stop\s*(?:generation|writing)",
                ],
                "params": [],
                "description": "إيقاف توليد الرد الحالي"
            },
            {
                "name": "regenerate",
                "patterns": [
                    r"(?:أعد|إعادة)\s*(?:التوليد|الرد|الإجابة|توليد)",
                    r"regenerate",
                ],
                "params": [],
                "description": "إعادة توليد آخر رد"
            },
            {
                "name": "new_chat",
                "patterns": [
                    r"(?:أنشئ|ابدأ|جديد|إنشاء|بدء)\s*(?:محادثة|دردشة|جلسة)\s*(?:جديدة)?",
                    r"new\s*(?:chat|session)",
                ],
                "params": [],
                "description": "إنشاء محادثة جديدة"
            },
            {
                "name": "search_chats",
                "patterns": [
                    r"(?:ابحث|بحث|فتش)\s*(?:عن|في)\s*(?:المحادثات|الدردشات)\s*(?:عن)?\s*(.+)",
                ],
                "params": ["query"],
                "description": "البحث في المحادثات"
            },
            {
                "name": "pin_chat",
                "patterns": [
                    r"(?:ثبت|تثبيت)\s*(?:المحادثة|الدردشة|الجلسة)",
                    r"pin\s*chat",
                ],
                "params": [],
                "description": "تثبيت المحادثة الحالية"
            },
            {
                "name": "archive_chat",
                "patterns": [
                    r"(?:أرشفة|ارشفة|أرشف)\s*(?:المحادثة|الدردشة|الجلسة)",
                    r"archive\s*chat",
                ],
                "params": [],
                "description": "أرشفة المحادثة الحالية"
            },
        ]
    
    # ═══════════════════════════════════════════
    # استخراج الأوامر
    # ═══════════════════════════════════════════
    
    def extract_command(self, text: str) -> Optional[dict]:
        """
        استخراج الأمر من نص عادي.
        
        Args:
            text: النص المستخدم للبحث عن أمر
            
        Returns:
            dict يحتوي على اسم الأمر والمعطيات، أو None
        """
        text_lower = text.lower().strip()
        
        for cmd in self.commands:
            for pattern in cmd["patterns"]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result = {
                        "name": cmd["name"],
                        "description": cmd.get("description", ""),
                        "params": {},
                        "raw_text": text
                    }
                    
                    # استخراج المعطيات
                    for i, param in enumerate(cmd.get("params", [])):
                        try:
                            result["params"][param] = match.group(i + 1)
                        except IndexError:
                            pass
                    
                    # إضافة الإجراء (enable/disable) إن وجد
                    if "action" in cmd:
                        result["params"]["action"] = cmd["action"]
                    
                    return result
        
        return None
    
    def extract_from_response(self, response: str) -> list:
        """
        استخراج كل الأوامر من رد المساعد.
        قد يحتوي الرد على عدة أوامر.
        
        Returns:
            قائمة بالأوامر المستخرجة
        """
        commands = []
        
        # البحث عن أوامر صريحة بين علامات خاصة
        # مثال: [COMMAND:change_theme:أزرق]
        explicit = re.findall(r'\[COMMAND:(\w+):?(.*?)?\]', response)
        for cmd_name, args in explicit:
            commands.append({
                "name": cmd_name,
                "params": {"value": args.strip()} if args.strip() else {},
                "explicit": True
            })
        
        # البحث عن أوامر نصية عادية
        # نقسم الرد لجمل
        sentences = response.split('\n')
        for sentence in sentences:
            cmd = self.extract_command(sentence)
            if cmd and not cmd.get("explicit"):
                commands.append(cmd)
        
        return commands
    
    # ═══════════════════════════════════════════
    # تنفيذ الأوامر
    # ═══════════════════════════════════════════
    
    def execute_command(self, command: dict) -> CommandResult:
        """
        تنفيذ أمر مستخرج.
        
        Args:
            command: قاموس الأمر المستخرج
            
        Returns:
            CommandResult بنتيجة التنفيذ
        """
        name = command["name"]
        params = command.get("params", {})
        
        handlers = {
            "change_theme": self._handle_change_theme,
            "toggle_dark_mode": self._handle_toggle_dark_mode,
            "clear_cache": self._handle_clear_cache,
            "show_stats": self._handle_show_stats,
            "delete_old_chats": self._handle_delete_old_chats,
            "change_speed": self._handle_change_speed,
            "toggle_thinking": self._handle_toggle_thinking,
            "change_persona": self._handle_change_persona,
            "stop_generation": self._handle_stop_generation,
            "regenerate": self._handle_regenerate,
            "new_chat": self._handle_new_chat,
            "search_chats": self._handle_search_chats,
            "pin_chat": self._handle_pin_chat,
            "archive_chat": self._handle_archive_chat,
        }
        
        handler = handlers.get(name)
        if handler:
            return handler(params)
        
        return CommandResult(
            success=False,
            message=f"الأمر '{name}' غير معروف",
            action=name
        )
    
    # ═══════════════════════════════════════════
    # معالجات الأوامر
    # ═══════════════════════════════════════════
    
    def _handle_change_theme(self, params: dict) -> CommandResult:
        color = params.get("color", "افتراضي")
        colors_map = {
            "أزرق": "blue", "ازرق": "blue", "blue": "blue",
            "أخضر": "green", "اخضر": "green", "green": "green",
            "أحمر": "red", "احمر": "red", "red": "red",
            "بنفسجي": "purple", "purple": "purple", "violet": "purple",
            "برتقالي": "orange", "orange": "orange",
            "وردي": "pink", "pink": "pink",
            "أسود": "dark", "اسود": "dark", "black": "dark", "dark": "dark",
            "أبيض": "light", "ابيض": "light", "white": "light", "light": "light",
            "ذهبي": "gold", "gold": "gold",
            "رمادي": "gray", "gray": "gray", "grey": "gray",
            "افتراضي": "default", "default": "default",
        }
        
        mapped = colors_map.get(color, color)
        
        return CommandResult(
            success=True,
            message=f"تم تغيير الثيم إلى {color}",
            action="change_theme",
            data={"theme": mapped, "color": color}
        )
    
    def _handle_toggle_dark_mode(self, params: dict) -> CommandResult:
        action = params.get("action", "enable")
        enabled = action == "enable"
        
        return CommandResult(
            success=True,
            message=f"تم {'تفعيل' if enabled else 'تعطيل'} الوضع الليلي",
            action="toggle_dark_mode",
            data={"enabled": enabled}
        )
    
    def _handle_clear_cache(self, params: dict) -> CommandResult:
        return CommandResult(
            success=True,
            message="تم مسح الذاكرة المؤقتة بنجاح",
            action="clear_cache",
            data={"cleared": True}
        )
    
    def _handle_show_stats(self, params: dict) -> CommandResult:
        return CommandResult(
            success=True,
            message="جاري عرض الإحصائيات...",
            action="show_stats",
            data={}
        )
    
    def _handle_delete_old_chats(self, params: dict) -> CommandResult:
        return CommandResult(
            success=True,
            message="تم حذف المحادثات القديمة بنجاح",
            action="delete_old_chats",
            data={"deleted": True}
        )
    
    def _handle_change_speed(self, params: dict) -> CommandResult:
        speed_map = {
            "سريعة": 15, "سريع": 15, "fast": 15, "عالية": 15, "عالي": 15,
            "متوسطة": 40, "متوسط": 40, "medium": 40,
            "بطيئة": 80, "بطيء": 80, "slow": 80, "منخفضة": 80, "منخفض": 80,
        }
        
        speed_text = params.get("speed", "متوسطة")
        speed_ms = speed_map.get(speed_text, 40)
        
        return CommandResult(
            success=True,
            message=f"تم تغيير سرعة الكتابة إلى {speed_text}",
            action="change_speed",
            data={"speed_ms": speed_ms, "speed_text": speed_text}
        )
    
    def _handle_toggle_thinking(self, params: dict) -> CommandResult:
        action = params.get("action", "enable")
        enabled = action == "enable"
        
        return CommandResult(
            success=True,
            message=f"تم {'تفعيل' if enabled else 'تعطيل'} وضع التفكير",
            action="toggle_thinking",
            data={"enabled": enabled}
        )
    
    def _handle_change_persona(self, params: dict) -> CommandResult:
        persona = params.get("persona", "افتراضي")
        
        return CommandResult(
            success=True,
            message=f"تم تغيير الشخصية إلى: {persona}",
            action="change_persona",
            data={"persona": persona}
        )
    
    def _handle_stop_generation(self, params: dict) -> CommandResult:
        return CommandResult(
            success=True,
            message="تم إيقاف توليد الرد",
            action="stop_generation",
            data={"stopped": True}
        )
    
    def _handle_regenerate(self, params: dict) -> CommandResult:
        return CommandResult(
            success=True,
            message="جاري إعادة توليد الرد...",
            action="regenerate",
            data={}
        )
    
    def _handle_new_chat(self, params: dict) -> CommandResult:
        return CommandResult(
            success=True,
            message="تم إنشاء محادثة جديدة",
            action="new_chat",
            data={"created": True}
        )
    
    def _handle_search_chats(self, params: dict) -> CommandResult:
        query = params.get("query", "")
        
        return CommandResult(
            success=True,
            message=f"جاري البحث عن: {query}",
            action="search_chats",
            data={"query": query}
        )
    
    def _handle_pin_chat(self, params: dict) -> CommandResult:
        return CommandResult(
            success=True,
            message="تم تثبيت المحادثة",
            action="pin_chat",
            data={"pinned": True}
        )
    
    def _handle_archive_chat(self, params: dict) -> CommandResult:
        return CommandResult(
            success=True,
            message="تم أرشفة المحادثة",
            action="archive_chat",
            data={"archived": True}
        )


# نسخة واحدة من معالج الأوامر
system_commands = SystemCommands()