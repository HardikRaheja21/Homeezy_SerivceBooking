'use client';

import { useCallback, useEffect, useState } from 'react';
import { ImagePlus, Loader2, X } from 'lucide-react';
import { toast } from 'sonner';

import { fetchUploadStatus, validateImageFile, getApiErrorMessage } from '@/lib/uploads';

type ImageUploaderProps = {
  label: string;
  hint?: string;
  currentUrl?: string | null;
  onUpload: (file: File, onProgress: (pct: number) => void) => Promise<string | string[]>;
  onSuccess?: (url: string | string[]) => void;
};

export function ImageUploader({
  label,
  hint,
  currentUrl,
  onUpload,
  onSuccess,
}: ImageUploaderProps) {
  const [preview, setPreview] = useState<string | null>(currentUrl ?? null);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    fetchUploadStatus()
      .then((s) => setAvailable(s.uploads_available))
      .catch(() => setAvailable(false));
  }, []);

  useEffect(() => {
    setPreview(currentUrl ?? null);
  }, [currentUrl]);

  const handleFile = useCallback(
    async (file: File) => {
      const validation = validateImageFile(file);
      if (validation) {
        toast.error(validation);
        return;
      }
      setPreview(URL.createObjectURL(file));
      setUploading(true);
      setProgress(0);
      try {
        const result = await onUpload(file, setProgress);
        const url = Array.isArray(result) ? result[result.length - 1] : result;
        setPreview(url);
        onSuccess?.(result);
        toast.success('Upload complete');
      } catch (error) {
        toast.error(getApiErrorMessage(error, 'Upload failed'));
        setPreview(currentUrl ?? null);
      } finally {
        setUploading(false);
        setProgress(0);
      }
    },
    [onUpload, onSuccess, currentUrl]
  );

  if (available === false) {
    return (
      <div className="rounded-xl border border-dashed border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        <p className="font-medium">{label}</p>
        <p className="mt-1 text-amber-700">
          Uploads are temporarily unavailable. You can continue without attaching files.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{label}</p>
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
      <div className="flex flex-wrap items-start gap-4">
        {preview && (
          <div className="relative h-24 w-24 rounded-xl overflow-hidden border border-slate-200 bg-slate-50">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={preview} alt="Preview" className="h-full w-full object-cover" />
            {!uploading && (
              <button
                type="button"
                className="absolute top-1 right-1 rounded-full bg-black/50 p-1 text-white"
                onClick={() => setPreview(null)}
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        )}
        <label className="flex flex-col items-center justify-center h-24 w-24 rounded-xl border-2 border-dashed border-slate-200 hover:border-emerald-400 cursor-pointer transition-colors">
          {uploading ? (
            <Loader2 className="h-6 w-6 animate-spin text-emerald-600" />
          ) : (
            <ImagePlus className="h-6 w-6 text-slate-400" />
          )}
          <span className="text-[10px] text-slate-500 mt-1">Add photo</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            disabled={uploading || available === null}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
              e.target.value = '';
            }}
          />
        </label>
      </div>
      {uploading && (
        <div className="h-1.5 w-full max-w-xs rounded-full bg-slate-100 overflow-hidden">
          <div className="h-full bg-emerald-500 transition-all" style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  );
}
