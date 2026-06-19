// frontend/components/WhatsAppButton.tsx
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-moment';

interface WhatsAppButtonProps {
  phoneNumber: string;          // رقم الواتساب مع الكود الدولي
  message?: string;             // رسالة افتراضية
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  showPulse?: boolean;         // تأثير النبض
  size?: 'sm' | 'md' | 'lg';
}

const WhatsAppButton: React.FC<WhatsAppButtonProps> = ({
  phoneNumber = '+201208672594',
  message = 'مرحباً، لدي استفسار حول منصة SAIF.AI',
  position = 'bottom-right',
  showPulse = true,
  size = 'md',
}) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [isClicked, setIsClicked] = useState(false);

  // ── أحجام الزر ──────────────────────────
  const sizes = {
    sm: 'w-12 h-12',
    md: 'w-14 h-14',
    lg: 'w-16 h-16',
  };

  const iconSizes = {
    sm: 'w-6 h-6',
    md: 'w-7 h-7',
    lg: 'w-8 h-8',
  };

  // ── مواقع الزر ──────────────────────────
  const positions = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6',
  };

  // ── إنشاء رابط واتساب ──────────────────
  const whatsappUrl = `https://wa.me/${phoneNumber.replace(/\+/g, '')}?text=${encodeURIComponent(message)}`;

  // ── فتح الواتساب ────────────────────────
  const handleClick = () => {
    setIsClicked(true);
    window.open(whatsappUrl, '_blank');
    setTimeout(() => setIsClicked(false), 1000);
  };

  return (
    <div className={`fixed ${positions[position]} z-50`}>
      {/* ── تلميح الأدوات (Tooltip) ──────── */}
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            transition={{ duration: 0.2 }}
            className="absolute bottom-full right-0 mb-3 
                       px-4 py-2.5 rounded-xl bg-gray-800 border border-gray-700 
                       shadow-xl text-white text-sm whitespace-nowrap"
          >
            <div className="flex items-center gap-2">
              <span>💬</span>
              <span>تحدث معنا عبر واتساب</span>
            </div>
            <p className="text-gray-400 text-xs mt-1">
              {phoneNumber}
            </p>
            {/* سهم صغير للأسفل */}
            <div className="absolute top-full right-6 
                            w-0 h-0 border-l-4 border-r-4 border-t-4 
                            border-transparent border-t-gray-800" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── الزر الرئيسي ──────────────────── */}
      <motion.button
        onClick={handleClick}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className={`
          ${sizes[size]}
          relative flex items-center justify-center
          rounded-full shadow-2xl
          bg-gradient-to-br from-green-400 to-green-600
          hover:from-green-500 hover:to-green-700
          text-white
          transition-all duration-300
          focus:outline-none focus:ring-4 focus:ring-green-500/40
        `}
        aria-label="تواصل عبر واتساب"
        title="تحدث معنا عبر واتساب"
      >
        {/* أيقونة واتساب */}
        <svg 
          className={iconSizes[size]} 
          viewBox="0 0 24 24" 
          fill="currentColor"
        >
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>

        {/* ── تأثير النبض ────────────────── */}
        {showPulse && (
          <>
            <motion.span
              className="absolute inset-0 rounded-full bg-green-400/30"
              initial={{ opacity: 0.7, scale: 0.9 }}
              animate={{ opacity: 0, scale: 1.8 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeOut' }}
            />
            <motion.span
              className="absolute inset-0 rounded-full bg-green-400/20"
              initial={{ opacity: 0.7, scale: 0.9 }}
              animate={{ opacity: 0, scale: 1.8 }}
              transition={{ duration: 2, repeat: Infinity, delay: 0.5, ease: 'easeOut' }}
            />
            <motion.span
              className="absolute inset-0 rounded-full bg-green-400/10"
              initial={{ opacity: 0.7, scale: 0.9 }}
              animate={{ opacity: 0, scale: 1.8 }}
              transition={{ duration: 2, repeat: Infinity, delay: 1, ease: 'easeOut' }}
            />
          </>
        )}

        {/* ── تأثير الضغط ────────────────── */}
        <AnimatePresence>
          {isClicked && (
            <motion.span
              initial={{ opacity: 0.8, scale: 0.8 }}
              animate={{ opacity: 0, scale: 2.5 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.6 }}
              className="absolute inset-0 rounded-full bg-white/30"
            />
          )}
        </AnimatePresence>

        {/* ── نقطة الإشعار (اختياري) ──────── */}
        <span className="absolute -top-1 -right-1 w-4 h-4 
                         bg-red-500 rounded-full border-2 border-white
                         animate-pulse" />
      </motion.button>
    </div>
  );
};

export default WhatsAppButton;