// frontend/components/ThinkingToggle.tsx
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ThinkingToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  disabled?: boolean;
}

const ThinkingToggle: React.FC<ThinkingToggleProps> = ({ 
  enabled, 
  onToggle, 
  disabled = false 
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative">
      {/* زر التبديل */}
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={() => onToggle(!enabled)}
        onMouseEnter={() => {
          setIsHovered(true);
          setShowTooltip(true);
        }}
        onMouseLeave={() => {
          setIsHovered(false);
          setShowTooltip(false);
        }}
        disabled={disabled}
        className={`
          relative p-2.5 rounded-xl transition-all duration-300 shadow-lg
          ${enabled
            ? 'bg-gradient-to-br from-amber-500 to-orange-600 text-white shadow-amber-500/30'
            : 'bg-gray-800 text-gray-400 hover:text-amber-400 shadow-gray-900/50'
          }
          ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
        `}
        aria-label={enabled ? 'إيقاف وضع التفكير' : 'تفعيل وضع التفكير'}
      >
        {/* أيقونة الدماغ */}
        <AnimatePresence mode="wait">
          {enabled ? (
            <motion.div
              key="brain-active"
              initial={{ rotate: -30, scale: 0 }}
              animate={{ rotate: 0, scale: 1 }}
              exit={{ rotate: 30, scale: 0 }}
              transition={{ duration: 0.4 }}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15h2v2h-2v-2zm0-12h2v8h-2V5z" />
              </svg>
              
              {/* حلقات النبض */}
              <motion.span
                className="absolute inset-0 rounded-full"
                initial={{ opacity: 0.6, scale: 0.8 }}
                animate={{ opacity: 0, scale: 1.8 }}
                transition={{ duration: 1.5, repeat: Infinity }}
                style={{ background: 'radial-gradient(circle, rgba(251,191,36,0.4) 0%, transparent 70%)' }}
              />
              <motion.span
                className="absolute inset-0 rounded-full"
                initial={{ opacity: 0.6, scale: 0.8 }}
                animate={{ opacity: 0, scale: 1.8 }}
                transition={{ duration: 1.5, repeat: Infinity, delay: 0.5 }}
                style={{ background: 'radial-gradient(circle, rgba(251,146,60,0.3) 0%, transparent 70%)' }}
              />
            </motion.div>
          ) : (
            <motion.div
              key="brain-inactive"
              initial={{ rotate: 30, scale: 0 }}
              animate={{ rotate: 0, scale: 1 }}
              exit={{ rotate: -30, scale: 0 }}
              transition={{ duration: 0.4 }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </motion.div>
          )}
        </AnimatePresence>

        {/* مؤشر LED */}
        <motion.span
          animate={{
            backgroundColor: enabled ? '#22c55e' : '#6b7280',
            boxShadow: enabled ? '0 0 8px rgba(34,197,94,0.6)' : '0 0 0px rgba(107,114,128,0)',
          }}
          className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-gray-900"
        />
      </motion.button>

      {/* Tooltip */}
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.9 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 
                       px-4 py-2.5 rounded-xl bg-gray-800 border border-gray-700 
                       shadow-xl text-white text-sm whitespace-nowrap z-10"
          >
            <div className="flex items-center gap-2">
              <span>🧠</span>
              <span>{enabled ? 'وضع التفكير مفعل' : 'تفعيل وضع التفكير'}</span>
            </div>
            <p className="text-gray-400 text-xs mt-1">
              {enabled 
                ? 'سيظهر خطوات استدلال الـ AI قبل الرد' 
                : 'أظهر خطوات تفكير الـ AI قبل الإجابة'}
            </p>
            <div className="absolute top-full left-1/2 -translate-x-1/2 
                            w-0 h-0 border-l-4 border-r-4 border-t-4 
                            border-transparent border-t-gray-800" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ThinkingToggle;