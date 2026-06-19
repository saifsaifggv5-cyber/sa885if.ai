// frontend/components/FileUpload.tsx
import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// ── أنواع الملفات المسموحة ───────────────
interface UploadedFile {
  id: string;
  file: File;
  preview?: string;
  name: string;
  size: number;
  type: string;
}

interface FileUploadProps {
  onUpload: (files: File[]) => void;
  onClose?: () => void;
  accept?: string;           // مثال: "image/*,.pdf,.doc,.docx,.txt"
  maxFiles?: number;         // أقصى عدد للملفات
  maxSize?: number;          // أقصى حجم بالميجابايت
  isOpen?: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onUpload,
  onClose,
  accept = 'image/*,.pdf,.doc,.docx,.txt,.mp3,.mp4',
  maxFiles = 5,
  maxSize = 10, // ميجابايت
  isOpen = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── توليد معاينة للصور ──────────────────
  const generatePreview = (file: File): string | undefined => {
    if (file.type.startsWith('image/')) {
      return URL.createObjectURL(file);
    }
    return undefined;
  };

  // ── التحقق من الملف ─────────────────────
  const validateFile = useCallback(
    (file: File): string | null => {
      // التحقق من الحجم
      const maxSizeBytes = maxSize * 1024 * 1024;
      if (file.size > maxSizeBytes) {
        return `الملف ${file.name} أكبر من ${maxSize}MB`;
      }

      // التحقق من النوع (إذا تم تحديد accept)
      if (accept && accept !== '*') {
        const acceptedTypes = accept.split(',').map(t => t.trim());
        const isAccepted = acceptedTypes.some(type => {
          if (type.endsWith('/*')) {
            return file.type.startsWith(type.replace('/*', '/'));
          }
          if (type.startsWith('.')) {
            return file.name.toLowerCase().endsWith(type.toLowerCase());
          }
          return file.type === type;
        });

        if (!isAccepted) {
          return `نوع الملف ${file.name} غير مسموح`;
        }
      }

      return null;
    },
    [maxSize, accept]
  );

  // ── معالجة الملفات المختارة ─────────────
  const handleFiles = useCallback(
    (selectedFiles: FileList | File[]) => {
      setError(null);
      const newFiles: UploadedFile[] = [];
      const fileArray = Array.from(selectedFiles);

      for (const file of fileArray) {
        // التحقق من العدد
        if (files.length + newFiles.length >= maxFiles) {
          setError(`الحد الأقصى ${maxFiles} ملفات`);
          break;
        }

        // التحقق من الملف
        const validationError = validateFile(file);
        if (validationError) {
          setError(validationError);
          continue;
        }

        // التحقق من عدم التكرار
        const exists = files.some(f => f.name === file.name && f.size === file.size);
        if (exists) {
          setError(`الملف ${file.name} مضاف مسبقاً`);
          continue;
        }

        newFiles.push({
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          file,
          preview: generatePreview(file),
          name: file.name,
          size: file.size,
          type: file.type,
        });
      }

      setFiles(prev => [...prev, ...newFiles]);
    },
    [files, maxFiles, validateFile]
  );

  // ── حذف ملف ─────────────────────────────
  const removeFile = (id: string) => {
    setFiles(prev => {
      const file = prev.find(f => f.id === id);
      if (file?.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter(f => f.id !== id);
    });
    setError(null);
  };

  // ── إرسال الملفات ──────────────────────
  const handleUpload = () => {
    if (files.length === 0) return;
    const rawFiles = files.map(f => f.file);
    onUpload(rawFiles);
    // تنظيف الذاكرة
    files.forEach(f => {
      if (f.preview) URL.revokeObjectURL(f.preview);
    });
    setFiles([]);
  };

  // ── أحداث السحب والإفلات ───────────────
  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  // ── تنسيق الحجم ─────────────────────────
  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // ── أيقونة الملف ────────────────────────
  const getFileIcon = (type: string): string => {
    if (type.startsWith('image/')) return '🖼️';
    if (type.includes('pdf')) return '📄';
    if (type.includes('word')) return '📝';
    if (type.includes('text')) return '📃';
    if (type.startsWith('audio/')) return '🎵';
    if (type.startsWith('video/')) return '🎬';
    return '📎';
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        >
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="w-full max-w-lg bg-gray-900 rounded-3xl shadow-2xl overflow-hidden border border-gray-800"
          >
            {/* ── شريط العنوان ────────────── */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
              <h2 className="text-white font-semibold text-lg">📎 رفع الملفات</h2>
              {onClose && (
                <button
                  onClick={onClose}
                  className="p-2 rounded-full hover:bg-white/10 text-white/70 hover:text-white transition"
                >
                  ✕
                </button>
              )}
            </div>

            <div className="p-5 space-y-4">
              {/* ── منطقة السحب والإفلات ──── */}
              <motion.div
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                animate={{
                  borderColor: dragOver ? '#3b82f6' : '#374151',
                  backgroundColor: dragOver ? 'rgba(59,130,246,0.1)' : 'rgba(17,24,39,0.5)',
                }}
                className="border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer
                           transition-colors duration-200"
                onClick={() => fileInputRef.current?.click()}
              >
                <motion.div
                  animate={{ y: dragOver ? -5 : 0 }}
                  className="flex flex-col items-center gap-3"
                >
                  <span className="text-4xl">📤</span>
                  <div>
                    <p className="text-white font-medium">
                      اسحب وأفلت الملفات هنا
                    </p>
                    <p className="text-gray-400 text-sm mt-1">
                      أو اضغط للاختيار
                    </p>
                  </div>
                  <p className="text-gray-500 text-xs">
                    الملفات المدعومة: صور، PDF، Word، نصوص، صوت، فيديو
                  </p>
                  <p className="text-gray-500 text-xs">
                    الحد الأقصى: {maxFiles} ملفات | الحجم: {maxSize}MB
                  </p>
                </motion.div>
              </motion.div>

              {/* إدخال الملف المخفي */}
              <input
                ref={fileInputRef}
                type="file"
                accept={accept}
                multiple
                onChange={e => e.target.files && handleFiles(e.target.files)}
                className="hidden"
              />

              {/* ── رسالة الخطأ ────────────── */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="bg-red-500/20 border border-red-500/40 rounded-xl px-4 py-3"
                  >
                    <p className="text-red-400 text-sm">⚠️ {error}</p>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* ── قائمة الملفات ──────────── */}
              <AnimatePresence>
                {files.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="space-y-2 max-h-48 overflow-y-auto"
                  >
                    {files.map((file, index) => (
                      <motion.div
                        key={file.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ delay: index * 0.05 }}
                        className="flex items-center gap-3 bg-gray-800 rounded-xl px-4 py-3"
                      >
                        {/* معاينة مصغرة للصورة أو أيقونة */}
                        {file.preview ? (
                          <img
                            src={file.preview}
                            alt={file.name}
                            className="w-10 h-10 rounded-lg object-cover"
                          />
                        ) : (
                          <span className="text-2xl">{getFileIcon(file.type)}</span>
                        )}

                        {/* معلومات الملف */}
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm font-medium truncate">
                            {file.name}
                          </p>
                          <p className="text-gray-400 text-xs">
                            {formatSize(file.size)}
                          </p>
                        </div>

                        {/* زر الحذف */}
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => removeFile(file.id)}
                          className="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 
                                     hover:text-red-400 transition"
                        >
                          ✕
                        </motion.button>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* ── زر الإرسال ─────────────── */}
              {files.length > 0 && (
                <motion.button
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleUpload}
                  className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 
                             text-white font-semibold transition shadow-lg"
                >
                  📤 إرسال {files.length} {files.length === 1 ? 'ملف' : 'ملفات'}
                </motion.button>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default FileUpload;