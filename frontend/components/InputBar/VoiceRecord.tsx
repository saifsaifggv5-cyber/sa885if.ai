// frontend/components/VoiceRecord.tsx
import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface VoiceRecordProps {
  onSend: (text: string) => void;           // إرسال النص المحول للدردشة
  onTranscribe: (audioBlob: Blob) => Promise<string>; // تحويل الصوت لنص
}

type RecordingState = 'idle' | 'recording' | 'paused' | 'preview';

const VoiceRecord: React.FC<VoiceRecordProps> = ({ onSend, onTranscribe }) => {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const [state, setState] = useState<RecordingState>('idle');
  const [isOpen, setIsOpen] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [transcribedText, setTranscribedText] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // ── تنظيف الموارد ─────────────────────
  const cleanup = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }, [audioUrl]);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  // ── بدء التسجيل ──────────────────────
  const startRecording = async () => {
    setError(null);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = mediaStream;
      
      const recorder = new MediaRecorder(mediaStream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setState('preview');
      };

      recorder.start();
      setState('recording');
      setElapsed(0);
      
      timerRef.current = setInterval(() => {
        setElapsed(prev => prev + 1);
      }, 1000);
      
    } catch (err: any) {
      if (err.name === 'NotAllowedError') {
        setError('🎤 صلاحية الميكروفون مرفوضة');
      } else {
        setError('❌ تعذر الوصول للميكروفون');
      }
    }
  };

  // ── إيقاف التسجيل ────────────────────
  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    }
  };

  // ── تحويل الصوت لنص ──────────────────
  const transcribe = async () => {
    if (!chunksRef.current.length) return;
    setLoading(true);
    try {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
      const text = await onTranscribe(blob);
      setTranscribedText(text);
    } catch {
      setError('❌ فشل تحويل الصوت لنص');
    } finally {
      setLoading(false);
    }
  };

  // ── إرسال النص ───────────────────────
  const sendText = () => {
    if (transcribedText.trim()) {
      onSend(transcribedText.trim());
      handleClose();
    }
  };

  // ── إعادة التسجيل ────────────────────
  const retake = () => {
    setAudioUrl(null);
    setTranscribedText('');
    setElapsed(0);
    chunksRef.current = [];
    startRecording();
  };

  // ── إغلاق النافذة ────────────────────
  const handleClose = () => {
    stopRecording();
    cleanup();
    setIsOpen(false);
    setState('idle');
    setElapsed(0);
    setAudioUrl(null);
    setTranscribedText('');
    setError(null);
  };

  // ── تنسيق الوقت ──────────────────────
  const formatTime = (seconds: number): string => {
    const min = Math.floor(seconds / 60).toString().padStart(2, '0');
    const sec = (seconds % 60).toString().padStart(2, '0');
    return `${min}:${sec}`;
  };

  // ── عدد الموجات الصوتية ──────────────
  const WAVES = 5;

  return (
    <>
      {/* ── زر التشغيل في شريط الكتابة ──── */}
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={() => setIsOpen(true)}
        className="p-2.5 rounded-xl bg-gradient-to-br from-red-500 to-rose-600 
                   hover:from-red-400 hover:to-rose-500
                   text-white shadow-lg hover:shadow-red-500/30 transition"
        title="تسجيل صوتي"
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 14a3 3 0 003-3V5a3 3 0 00-6 0v6a3 3 0 003 3zm5-3a5 5 0 01-10 0H5a7 7 0 006 6.93V21h2v-3.07A7 7 0 0019 11h-2z" />
        </svg>
      </motion.button>

      {/* ── النافذة المنبثقة ────────────── */}
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
              className="w-full max-w-sm bg-gray-900 border border-gray-800 rounded-3xl 
                         shadow-2xl overflow-hidden"
            >
              {/* ── العنوان ───────────────── */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
                <h2 className="text-white font-semibold text-lg flex items-center gap-2">
                  🎤 تسجيل صوتي
                </h2>
                <button
                  onClick={handleClose}
                  className="p-2 rounded-full hover:bg-white/10 text-white/70 hover:text-white transition"
                >
                  ✕
                </button>
              </div>

              <div className="p-6 flex flex-col items-center gap-6">
                {/* ── حالة الخمول ──────────── */}
                {state === 'idle' && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="flex flex-col items-center gap-4"
                  >
                    <div className="w-20 h-20 rounded-full bg-gray-800 flex items-center justify-center">
                      <span className="text-4xl">🎙️</span>
                    </div>
                    <p className="text-gray-400 text-sm">اضغط على الزر لبدء التسجيل</p>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={startRecording}
                      className="px-8 py-3.5 rounded-full bg-red-500 hover:bg-red-400 
                                 text-white font-semibold shadow-lg shadow-red-500/30 transition"
                    >
                      🎤 بدء التسجيل
                    </motion.button>
                  </motion.div>
                )}

                {/* ── حالة التسجيل ─────────── */}
                {state === 'recording' && (
                  <div className="flex flex-col items-center gap-6 w-full">
                    {/* موجات صوتية متحركة */}
                    <div className="flex items-end gap-1.5 h-20">
                      {[...Array(WAVES)].map((_, i) => (
                        <motion.div
                          key={i}
                          className="w-3 bg-red-500 rounded-full"
                          animate={{ height: [12, 40, 20, 48, 12][i % 5] * 1.5 }}
                          transition={{
                            duration: 0.7,
                            repeat: Infinity,
                            delay: i * 0.1,
                            ease: 'easeInOut',
                          }}
                        />
                      ))}
                    </div>

                    {/* المؤقت */}
                    <motion.div
                      animate={{ opacity: [1, 0.7, 1] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="flex items-center gap-2"
                    >
                      <span className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
                      <span className="text-3xl font-mono text-white tabular-nums">
                        {formatTime(elapsed)}
                      </span>
                    </motion.div>

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={stopRecording}
                      className="px-8 py-3.5 rounded-full bg-gray-700 hover:bg-gray-600 
                                 text-white font-semibold transition"
                    >
                      ⏹️ إيقاف
                    </motion.button>
                  </div>
                )}

                {/* ── حالة المعاينة ────────── */}
                {state === 'preview' && audioUrl && (
                  <div className="flex flex-col items-center gap-4 w-full">
                    <p className="text-green-400 text-sm flex items-center gap-1">
                      ✅ تم التسجيل
                    </p>

                    {/* مشغل الصوت */}
                    <audio controls src={audioUrl} className="w-full h-10" />

                    {!transcribedText && !loading && (
                      <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={transcribe}
                        className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 
                                   text-white font-medium text-sm transition"
                      >
                        📝 تحويل لنص
                      </motion.button>
                    )}

                    {loading && (
                      <div className="flex items-center gap-2 text-blue-400">
                        <div className="animate-spin rounded-full h-5 w-5 border-2 
                                        border-blue-400 border-t-transparent" />
                        <span className="text-sm">جاري التحويل...</span>
                      </div>
                    )}

                    {transcribedText && (
                      <div className="w-full bg-gray-800 rounded-xl p-3">
                        <p className="text-white text-sm">{transcribedText}</p>
                      </div>
                    )}

                    <div className="flex gap-2 w-full">
                      <motion.button
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={retake}
                        className="flex-1 py-2.5 rounded-xl bg-gray-700 hover:bg-gray-600 
                                   text-white text-sm transition"
                      >
                        ↺ إعادة
                      </motion.button>
                      {transcribedText && (
                        <motion.button
                          whileHover={{ scale: 1.03 }}
                          whileTap={{ scale: 0.97 }}
                          onClick={sendText}
                          className="flex-1 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 
                                     text-white text-sm font-medium transition"
                        >
                          📤 إرسال
                        </motion.button>
                      )}
                    </div>
                  </div>
                )}

                {/* ── رسائل الخطأ ──────────── */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="bg-red-500/20 border border-red-500/40 rounded-xl px-4 py-3 w-full"
                    >
                      <p className="text-red-400 text-sm">{error}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default VoiceRecord;