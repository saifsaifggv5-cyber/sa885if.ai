// frontend/components/CameraCapture.tsx
import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface CameraCaptureProps {
  onCapture: (imageDataUrl: string) => void;
  onClose: () => void;
  isOpen: boolean;
}

const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture, onClose, isOpen }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [stream, setStream] = useState<MediaStream | null>(null);
  const [photo, setPhoto] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cameraFacing, setCameraFacing] = useState<'user' | 'environment'>('user');

  // ── بدء الكاميرا ───────────────────────
  const startCamera = useCallback(async (facing: 'user' | 'environment' = 'user') => {
    setLoading(true);
    setError(null);
    try {
      // إيقاف أي بث سابق
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facing,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      });

      streamRef.current = mediaStream;
      setStream(mediaStream);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err: any) {
      if (err.name === 'NotAllowedError') {
        setError('⚠️ صلاحية الكاميرا مرفوضة. يرجى السماح بالوصول للكاميرا من إعدادات المتصفح.');
      } else if (err.name === 'NotFoundError') {
        setError('📷 لم يتم العثور على كاميرا. تأكد من توصيل كاميرا.');
      } else if (err.name === 'NotReadableError') {
        setError('🔒 الكاميرا قيد الاستخدام من تطبيق آخر.');
      } else {
        setError('❌ حدث خطأ غير متوقع: ' + err.message);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // ── التقاط الصورة ──────────────────────
  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    if (!context) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageDataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setPhoto(imageDataUrl);

    // إيقاف الكاميرا بعد الالتقاط
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  }, []);

  // ── قلب الكاميرا (أمامية/خلفية) ────────
  const switchCamera = useCallback(() => {
    const newFacing = cameraFacing === 'user' ? 'environment' : 'user';
    setCameraFacing(newFacing);
    setPhoto(null);
    startCamera(newFacing);
  }, [cameraFacing, startCamera]);

  // ── قبول الصورة وإرسالها ──────────────
  const acceptPhoto = () => {
    if (photo) {
      onCapture(photo);
      resetCamera();
    }
  };

  // ── إعادة الالتقاط ─────────────────────
  const retakePhoto = () => {
    setPhoto(null);
    startCamera(cameraFacing);
  };

  // ── إعادة تعيين الكاميرا ───────────────
  const resetCamera = () => {
    setPhoto(null);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    onClose();
  };

  // ── تشغيل الكاميرا عند الفتح ───────────
  useEffect(() => {
    if (isOpen) {
      startCamera(cameraFacing);
    } else {
      resetCamera();
    }
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="relative w-full max-w-lg mx-4 rounded-3xl overflow-hidden bg-gray-900 shadow-2xl"
          >
            {/* ── شريط العنوان ────────────── */}
            <div className="flex items-center justify-between px-5 py-4 bg-black/40">
              <h2 className="text-white font-semibold text-lg">📷 التقاط صورة</h2>
              <button
                onClick={resetCamera}
                className="p-2 rounded-full hover:bg-white/10 text-white/70 hover:text-white transition"
              >
                ✕
              </button>
            </div>

            {/* ── جسم الكاميرا ────────────── */}
            <div className="relative aspect-[4/3] bg-black">
              {/* رسالة الخطأ */}
              {error && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/70 p-4 text-center">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}

              {/* تحميل */}
              {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent" />
                </div>
              )}

              {/* فيديو الكاميرا */}
              {!photo && !error && (
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="absolute inset-0 w-full h-full object-cover"
                  style={{ transform: cameraFacing === 'user' ? 'scaleX(-1)' : 'none' }}
                />
              )}

              {/* معاينة الصورة */}
              {photo && (
                <img
                  src={photo}
                  alt="معاينة"
                  className="absolute inset-0 w-full h-full object-cover"
                />
              )}

              {/* Canvas مخفي للالتقاط */}
              <canvas ref={canvasRef} className="hidden" />
            </div>

            {/* ── أزرار التحكم ────────────── */}
            <div className="flex items-center justify-center gap-4 p-5 bg-black/40">
              {!photo ? (
                <>
                  {/* التقاط */}
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={capturePhoto}
                    disabled={!!error || loading}
                    className="w-16 h-16 rounded-full bg-white shadow-lg hover:shadow-xl 
                               disabled:opacity-50 disabled:cursor-not-allowed
                               flex items-center justify-center transition"
                  >
                    <div className="w-12 h-12 rounded-full border-4 border-gray-800" />
                  </motion.button>

                  {/* قلب الكاميرا */}
                  {!error && !loading && (
                    <motion.button
                      whileTap={{ scale: 0.9 }}
                      onClick={switchCamera}
                      className="absolute right-6 w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 
                                 flex items-center justify-center text-white"
                      title="قلب الكاميرا"
                    >
                      🔄
                    </motion.button>
                  )}
                </>
              ) : (
                <>
                  {/* إعادة الالتقاط */}
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={retakePhoto}
                    className="px-6 py-2.5 rounded-xl bg-gray-600 hover:bg-gray-500 
                               text-white font-medium text-sm transition shadow-lg"
                  >
                    ↺ إعادة
                  </motion.button>

                  {/* قبول وإرسال */}
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={acceptPhoto}
                    className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 
                               text-white font-medium text-sm transition shadow-lg"
                  >
                    ✓ إرسال
                  </motion.button>
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default CameraCapture;