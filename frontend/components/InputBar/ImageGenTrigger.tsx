// frontend/components/ImageGenTrigger.tsx
import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ImageGenTriggerProps {
  onGenerate: (prompt: string, style: string) => Promise<string>; // يرجع رابط الصورة
  onSendToChat?: (imageUrl: string) => void;
}

// ── أنماط الرسم المقترحة ──────────────────
const STYLES = [
  { id: 'realistic', label: 'واقعي 🎯', icon: '📸' },
  { id: 'anime', label: 'أنمي 🌸', icon: '🎨' },
  { id: 'digital', label: 'رقمي 💻', icon: '🖥️' },
  { id: 'oil', label: 'لوحة زيتية 🖌️', icon: '🖼️' },
  { id: '3d', label: 'ثلاثي الأبعاد 🧊', icon: '📦' },
  { id: 'sketch', label: 'رسم بالقلم ✏️', icon: '✏️' },
];

const ImageGenTrigger: React.FC<ImageGenTriggerProps> = ({ onGenerate, onSendToChat }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('realistic');
  const [loading, setLoading] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── توليد الصورة ────────────────────────
  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const imageUrl = await onGenerate(prompt, style);
      setGeneratedImage(imageUrl);
    } catch (err) {
      setError('❌ فشل إنشاء الصورة، حاول مرة أخرى.');
    } finally {
      setLoading(false);
    }
  };

  // ── إرسال الصورة للمحادثة ──────────────
  const handleSendToChat = () => {
    if (generatedImage && onSendToChat) {
      onSendToChat(generatedImage);
      handleClose();
    }
  };

  // ── إعادة التعيين ───────────────────────
  const handleClose = () => {
    setIsOpen(false);
    setPrompt('');
    setGeneratedImage(null);
    setError(null);
    setStyle('realistic');
  };

  // ── فتح النافذة مع تركيز حقل الكتابة ────
  const handleOpen = () => {
    setIsOpen(true);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  return (
    <>
      {/* ── زر التشغيل في شريط الكتابة ────── */}
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={handleOpen}
        className="p-2.5 rounded-xl bg-gradient-to-br from-purple-600 to-pink-500 
                   hover:from-purple-500 hover:to-pink-400 
                   text-white shadow-lg hover:shadow-purple-500/30 transition"
        title="إنشاء صورة بالذكاء الاصطناعي"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </motion.button>

      {/* ── النافذة المنبثقة ──────────────── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-end sm:items-center justify-center 
                       bg-black/60 backdrop-blur-sm p-4"
            onClick={(e) => e.target === e.currentTarget && handleClose()}
          >
            <motion.div
              initial={{ opacity: 0, y: 30, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 30, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              className="w-full max-w-md bg-gray-900 border border-gray-800 rounded-3xl 
                         shadow-2xl overflow-hidden"
            >
              {/* ── شريط العنوان ──────────── */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
                <h2 className="text-white font-semibold text-lg flex items-center gap-2">
                  🎨 إنشاء صورة
                </h2>
                <button
                  onClick={handleClose}
                  className="p-2 rounded-full hover:bg-white/10 text-white/70 hover:text-white transition"
                >
                  ✕
                </button>
              </div>

              <div className="p-5 space-y-4">
                {/* ── حقل الوصف ────────────── */}
                <div>
                  <label className="text-gray-300 text-sm mb-2 block">وصف الصورة</label>
                  <input
                    ref={inputRef}
                    type="text"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                    placeholder="مثال: قطة ترتدي قبعة في الفضاء..."
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl 
                               text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 
                               transition"
                    disabled={loading}
                  />
                </div>

                {/* ── اختيار النمط ─────────── */}
                <div>
                  <label className="text-gray-300 text-sm mb-2 block">نمط الرسم</label>
                  <div className="grid grid-cols-3 gap-2">
                    {STYLES.map((s) => (
                      <motion.button
                        key={s.id}
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setStyle(s.id)}
                        disabled={loading}
                        className={`px-3 py-2.5 rounded-xl text-sm font-medium transition border
                          ${style === s.id
                            ? 'bg-purple-600/20 border-purple-500 text-purple-400 shadow-lg shadow-purple-500/10'
                            : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
                          } disabled:opacity-50`}
                      >
                        <span className="block text-lg">{s.icon}</span>
                        <span className="text-xs">{s.label}</span>
                      </motion.button>
                    ))}
                  </div>
                </div>

                {/* ── رسالة الخطأ ──────────── */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="bg-red-500/20 border border-red-500/40 rounded-xl px-4 py-3"
                    >
                      <p className="text-red-400 text-sm">{error}</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* ── حالة التحميل ─────────── */}
                {loading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex flex-col items-center gap-3 py-4"
                  >
                    <div className="animate-spin rounded-full h-12 w-12 border-4 
                                    border-purple-500/30 border-t-purple-500" />
                    <p className="text-gray-400 text-sm">🎨 جاري الرسم...</p>
                    <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                        initial={{ width: '0%' }}
                        animate={{ width: '100%' }}
                        transition={{ duration: 5, ease: 'linear' }}
                      />
                    </div>
                  </motion.div>
                )}

                {/* ── معاينة الصورة ────────── */}
                <AnimatePresence>
                  {generatedImage && !loading && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="rounded-2xl overflow-hidden border border-gray-700"
                    >
                      <img
                        src={generatedImage}
                        alt="الصورة المُنشأة"
                        className="w-full h-64 object-cover"
                      />
                      <div className="flex gap-2 p-3 bg-gray-800">
                        <motion.button
                          whileHover={{ scale: 1.03 }}
                          whileTap={{ scale: 0.97 }}
                          onClick={handleSendToChat}
                          className="flex-1 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 
                                     text-white font-medium text-sm transition"
                        >
                          📤 إرسال للمحادثة
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.03 }}
                          whileTap={{ scale: 0.97 }}
                          onClick={() => setGeneratedImage(null)}
                          className="px-4 py-2.5 rounded-xl bg-gray-700 hover:bg-gray-600 
                                     text-white text-sm transition"
                        >
                          ↺ إعادة
                        </motion.button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* ── زر التوليد ───────────── */}
                {!generatedImage && !loading && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleGenerate}
                    disabled={!prompt.trim()}
                    className="w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-500 
                               hover:from-purple-500 hover:to-pink-400 text-white font-semibold 
                               transition shadow-lg disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    ✨ توليد الصورة
                  </motion.button>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default ImageGenTrigger;