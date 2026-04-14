import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X } from 'lucide-react';
import Button from '../shared/Button';
import { uploadDocument } from '../../api/documents';
import { CHUNKING_STRATEGIES, type ChunkingStrategy } from '../../utils/constants';
import { formatFileSize } from '../../utils/formatters';
import toast from 'react-hot-toast';

interface FileUploaderProps {
  onUploadComplete: () => void;
}

const ACCEPTED_TYPES: Record<string, string[]> = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/html': ['.html', '.htm'],
  'text/markdown': ['.md'],
};

export default function FileUploader({ onUploadComplete }: FileUploaderProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [category, setCategory] = useState('');
  const [strategy, setStrategy] = useState<ChunkingStrategy>('fixed');
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    setFiles((prev) => [...prev, ...accepted]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    multiple: true,
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      for (const file of files) {
        await uploadDocument({ file, category: category || undefined, chunking_strategy: strategy });
      }
      toast.success(`${files.length} document(s) uploaded successfully`);
      setFiles([]);
      setCategory('');
      onUploadComplete();
    } catch {
      toast.error('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
          ${isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-border dark:border-dark-border hover:border-primary/50'
          }`}
      >
        <input {...getInputProps()} />
        <Upload className="h-10 w-10 text-text-muted dark:text-dark-text-muted mx-auto mb-3" />
        <p className="text-sm font-medium text-text dark:text-dark-text">
          {isDragActive ? 'Drop files here' : 'Drag & drop files here, or click to browse'}
        </p>
        <p className="text-xs text-text-muted dark:text-dark-text-muted mt-1">
          PDF, DOCX, HTML, Markdown
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, i) => (
            <div
              key={`${file.name}-${i}`}
              className="flex items-center justify-between p-3 rounded-lg bg-white dark:bg-dark-surface border border-border dark:border-dark-border"
            >
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm font-medium text-text dark:text-dark-text">{file.name}</p>
                  <p className="text-xs text-text-muted dark:text-dark-text-muted">
                    {formatFileSize(file.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={() => removeFile(i)}
                className="p-1 text-text-muted hover:text-danger transition-colors cursor-pointer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Options */}
      {files.length > 0 && (
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs font-medium text-text-muted dark:text-dark-text-muted mb-1">
              Category (optional)
            </label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g. Engineering, Legal"
              className="w-full px-3 py-2 text-sm rounded-lg border border-border dark:border-dark-border
                bg-white dark:bg-dark-surface text-text dark:text-dark-text
                focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <div className="min-w-[160px]">
            <label className="block text-xs font-medium text-text-muted dark:text-dark-text-muted mb-1">
              Chunking Strategy
            </label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as ChunkingStrategy)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-border dark:border-dark-border
                bg-white dark:bg-dark-surface text-text dark:text-dark-text
                focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              {CHUNKING_STRATEGIES.map((s) => (
                <option key={s} value={s}>
                  {s.charAt(0).toUpperCase() + s.slice(1).replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>
          <Button onClick={handleUpload} loading={uploading}>
            Upload {files.length} file{files.length > 1 ? 's' : ''}
          </Button>
        </div>
      )}
    </div>
  );
}
