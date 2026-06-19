// frontend/components/ThemeSwitcher.tsx
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/contexts/ThemeContext';

const ThemeSwitcher: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  // ── منع مشاكل SSR ──────────────────────
  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null;

  const isDark = theme === 'dark';

  return (
    <motion.button
      onClick={toggleTheme}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`
        relative flex items-center justify-center
        w-11 h-11 rounded-xl
        transition-colors duration-300
        ${isDark 
          ? 'bg-gray-800 hover:bg-gray-700 text-yellow-400' 
          : 'bg-blue-50 hover:bg-blue-100 text-blue-600'
        }
        shadow-md hover:shadow-lg
        focus:outline-none focus:ring-2 focus:ring-blue-500/50
      `}
      whileTap={{ scale: 0.9 }}
      whileHover={{ scale: 1.05 }}
      aria-label={isDark ? 'تفعيل الوضع النهاري' : 'تفعيل الوضع الليلي'}
      title={isDark ? 'تفعيل الوضع النهاري ☀️' : 'تفعيل الوضع الليلي 🌙'}
    >
      {/* ── تأثير التوهج ───────────────── */}
      {isHovered && (
        <motion.div
          className="absolute inset-0 rounded-xl"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.15 }}
          exit={{ opacity: 0 }}
          style={{
            background: isDark 
              ? 'radial-gradient(circle, rgba(250,204,21,0.4) 0%, transparent 70%)' 
              : 'radial-gradient(circle, rgba(59,130,246,0.4) 0%, transparent 70%)',
          }}
        />
      )}

      {/* ── الأيقونة مع الأنيميشن ───────── */}
      <AnimatePresence mode="wait">
        {isDark ? (
          <motion.div
            key="moon"
            initial={{ rotate: -90, opacity: 0, scale: 0.5 }}
            animate={{ rotate: 0, opacity: 1, scale: 1 }}
            exit={{ rotate: 90, opacity: 0, scale: 0.5 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            {/* أيقونة القمر */}
            <svg 
              className="w-5 h-5" 
              fill="currentColor" 
              viewBox="0 0 24 24"
            >
              <motion.path
                d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5, ease: 'easeInOut' }}
              />
              {/* نجمة صغيرة */}
              <motion.circle
                cx="17"
                cy="8"
                r="1.2"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: [0, 1, 0.7, 1], scale: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              />
            </svg>
          </motion.div>
        ) : (
          <motion.div
            key="sun"
            initial={{ rotate: 90, opacity: 0, scale: 0.5 }}
            animate={{ rotate: 0, opacity: 1, scale: 1 }}
            exit={{ rotate: -90, opacity: 0, scale: 0.5 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            {/* أيقونة الشمس */}
            <svg 
              className="w-5 h-5" 
              fill="currentColor" 
              viewBox="0 0 24 24"
            >
              <motion.path
                d="M12 2v2m0 16v2m-10-8h2m16 0h2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41M12 6a6 6 0 100 12 6 6 0 000-12z"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.5, ease: 'easeInOut' }}
              />
              {/* مركز الشمس */}
              <motion.circle
                cx="12"
                cy="12"
                r="4"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3, delay: 0.2 }}
              />
            </svg>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── مؤشر الوضع الحالي (اختياري) ── */}
      <span className="sr-only">
        {isDark ? 'الوضع الليلي مفعل' : 'الوضع النهاري مفعل'}
      </span>
    </motion.button>
  );
};

export default ThemeSwitcher;