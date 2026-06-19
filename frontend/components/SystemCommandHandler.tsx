// frontend/components/SystemCommandHandler.tsx
import { useEffect, useCallback } from 'react';
import { Message } from '@/types';

// ── أنواع الأوامر المدعومة ─────────────────
type CommandAction =
  | { type: 'changeTheme'; payload: string }
  | { type: 'toggleDarkMode'; payload?: boolean }
  | { type: 'clearCache' }
  | { type: 'showStats' }
  | { type: 'deleteOldChats' }
  | { type: 'changeSpeed'; payload: number }
  | { type: 'toggleThinking' }
  | { type: 'regenerate' }
  | { type: 'stopGeneration' };

// ── أنماط التعرف على الأوامر بالعربي ───────
const commandPatterns: { regex: RegExp; action: CommandAction['type'] }[] = [
  { regex: /(?:غير|حول|بدل) (?:الثيم|اللون|المظهر) (?:إلى|لـ)?\s*(\S+)/i, action: 'changeTheme' },
  { regex: /(?:فعل|شغل|افتح) (?:الوضع|المظهر) (?:الليلي|الداكن|الغامق)/i, action: 'toggleDarkMode' },
  { regex: /(?:أوقف|اقفل|عطل) (?:الوضع|المظهر) (?:الليلي|الداكن|الغامق)/i, action: 'toggleDarkMode' },
  { regex: /(?:امسح|نظف|افرغ) (?:الكاش|الذاكرة المؤقتة)/i, action: 'clearCache' },
  { regex: /(?:اعرض|وريني|هات) (?:الإحصائيات|الإحصاءات|تقرير الاستخدام)/i, action: 'showStats' },
  { regex: /(?:احذف|امسح) (?:المحادثات|المحادثات القديمة)/i, action: 'deleteOldChats' },
  { regex: /(?:غير|عدل) (?:سرعة|سرعة الكتابة) (?:إلى|لـ)?\s*(سريعة|بطيئة|متوسطة|عالية|منخفضة)/i, action: 'changeSpeed' },
  { regex: /(?:فعل|شغل|افتح) (?:وضع|خاصية) (?:التفكير|التفكير العميق)/i, action: 'toggleThinking' },
  { regex: /(?:أوقف|اقفل|عطل) (?:وضع|خاصية) (?:التفكير|التفكير العميق)/i, action: 'toggleThinking' },
];

// ── تحويل النص العربي لأرقام سرعة ─────────
const speedMap: Record<string, number> = {
  'سريعة': 20,
  'عالية': 20,
  'متوسطة': 40,
  'بطيئة': 80,
  'منخفضة': 80,
};

interface SystemCommandHandlerProps {
  messages: Message[];
  onThemeChange: (theme: string) => void;
  onDarkModeToggle: (enabled: boolean) => void;
  onClearCache: () => void;
  onShowStats: () => void;
  onDeleteOldChats: () => void;
  onChangeSpeed: (ms: number) => void;
  onToggleThinking: () => void;
}

const SystemCommandHandler: React.FC<SystemCommandHandlerProps> = ({
  messages,
  onThemeChange,
  onDarkModeToggle,
  onClearCache,
  onShowStats,
  onDeleteOldChats,
  onChangeSpeed,
  onToggleThinking,
}) => {
  // ── تنفيذ الأمر بعد استخراجه ────────────
  const executeCommand = useCallback(
    (action: CommandAction) => {
      switch (action.type) {
        case 'changeTheme':
          onThemeChange(action.payload);
          console.log(`🎨 تم تغيير الثيم إلى: ${action.payload}`);
          break;
        case 'toggleDarkMode':
          const enable = action.payload !== undefined ? action.payload : true;
          onDarkModeToggle(enable);
          console.log(`🌙 الوضع الليلي: ${enable ? 'مفعل' : 'معطل'}`);
          break;
        case 'clearCache':
          onClearCache();
          console.log('🧹 تم مسح الكاش');
          break;
        case 'showStats':
          onShowStats();
          console.log('📊 عرض الإحصائيات');
          break;
        case 'deleteOldChats':
          onDeleteOldChats();
          console.log('🗑️ تم حذف المحادثات القديمة');
          break;
        case 'changeSpeed':
          const speed = speedMap[action.payload] || 40;
          onChangeSpeed(speed);
          console.log(`⚡ تم تغيير سرعة الكتابة إلى: ${action.payload}`);
          break;
        case 'toggleThinking':
          onToggleThinking();
          console.log('🧠 تم تبديل وضع التفكير');
          break;
        default:
          console.warn('⚠️ أمر غير معروف:', action);
      }
    },
    [onThemeChange, onDarkModeToggle, onClearCache, onShowStats, onDeleteOldChats, onChangeSpeed, onToggleThinking]
  );

  // ── مراقبة آخر رسالة من المساعد ─────────
  useEffect(() => {
    if (!messages || messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];
    if (lastMessage.role !== 'assistant') return;

    const content = lastMessage.content;

    for (const pattern of commandPatterns) {
      const match = content.match(pattern.regex);
      if (match) {
        // استخراج المعطيات حسب نوع الأمر
        let payload: string | boolean | undefined;

        if (pattern.action === 'changeTheme') {
          payload = match[1];
        } else if (pattern.action === 'toggleDarkMode') {
          payload = content.includes('فعل') || content.includes('شغل') || content.includes('افتح');
        } else if (pattern.action === 'changeSpeed') {
          payload = match[1];
        }

        executeCommand({ type: pattern.action, payload } as CommandAction);
        break; // أمر واحد فقط لكل رسالة
      }
    }
  }, [messages, executeCommand]);

  return null; // المكون لا يعرض أي شيء في الواجهة
};

export default SystemCommandHandler;