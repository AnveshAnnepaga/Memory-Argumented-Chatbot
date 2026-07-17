'use client';

import React, { useCallback, useState } from 'react';
import { uploadFile } from '@/lib/api';

interface UploadedFileInfo {
  fileId: string;
  filename: string;
  type: 'pdf' | 'docx' | 'image' | 'other';
  uploading: boolean;
  error?: string;
}

interface FileUploaderProps {
  onFilesUploaded: (files: UploadedFileInfo[]) => void;
  maxFiles?: number;
  accept?: string;
}

const ACCEPTED_TYPES = '.pdf,.docx,.doc,.png,.jpg,.jpeg,.gif,.webp';

function getFileType(filename: string, mimeType?: string): UploadedFileInfo['type'] {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return 'pdf';
  if (ext === 'docx' || ext === 'doc') return 'docx';
  if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext || '')) return 'image';
  return 'other';
}

export default function FileUploader({ onFilesUploaded, maxFiles = 5 }: FileUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadedFileInfo[]>([]);

  const processFiles = useCallback(async (files: FileList | File[]) => {
    const fileArray = Array.from(files).slice(0, maxFiles);
    const newInfos: UploadedFileInfo[] = fileArray.map((f) => ({
      fileId: '',
      filename: f.name,
      type: getFileType(f.name),
      uploading: true,
    }));
    setUploadingFiles((prev) => [...prev, ...newInfos]);

    const results: UploadedFileInfo[] = [];
    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i];
      try {
        const result = await uploadFile(file);
        results.push({
          fileId: result.file_id,
          filename: file.name,
          type: getFileType(file.name),
          uploading: false,
        });
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Upload failed';
        results.push({
          fileId: '',
          filename: file.name,
          type: getFileType(file.name),
          uploading: false,
          error: msg,
        });
      }
    }

    setUploadingFiles((prev) =>
      prev.map((p) => {
        const match = results.find((r) => r.filename === p.filename);
        return match || p;
      })
    );

    onFilesUploaded(results.filter((r) => !r.error && r.fileId));
  }, [maxFiles, onFilesUploaded]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      if (e.dataTransfer.files.length > 0) {
        processFiles(e.dataTransfer.files);
      }
    },
    [processFiles]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => setIsDragOver(false), []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        processFiles(e.target.files);
        e.target.value = '';
      }
    },
    [processFiles]
  );

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      style={{
        border: `2px dashed ${isDragOver ? '#3b82f6' : '#374151'}`,
        borderRadius: '8px',
        padding: '12px',
        textAlign: 'center',
        cursor: 'pointer',
        background: isDragOver ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
        transition: 'all 0.2s',
        fontSize: '13px',
        color: '#9ca3af',
      }}
    >
      <input
        type="file"
        onChange={handleFileSelect}
        accept={ACCEPTED_TYPES}
        multiple
        style={{ display: 'none' }}
        id="file-upload-input"
      />
      <label htmlFor="file-upload-input" style={{ cursor: 'pointer', display: 'block' }}>
        {isDragOver ? 'Drop files here' : 'Click or drag PDF, DOCX, or images'}
      </label>

      {uploadingFiles.length > 0 && (
        <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Uploaded Files
          </div>
          {uploadingFiles.map((f, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                padding: '6px 10px',
                borderRadius: '6px',
                background: f.error ? 'rgba(239,68,68,0.1)' : f.uploading ? 'rgba(245,158,11,0.1)' : 'rgba(16,185,129,0.1)',
                border: `1px solid ${f.error ? 'rgba(239,68,68,0.3)' : f.uploading ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.3)'}`,
              }}
            >
              <span style={{ fontSize: '14px' }}>
                {f.uploading ? '⏳' : f.error ? '❌' : '✅'}
              </span>
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#e5e7eb' }}>
                {f.filename}
              </span>
              <span style={{ color: f.error ? '#ef4444' : '#10b981', fontWeight: 600, fontSize: '11px' }}>
                {f.uploading ? 'Uploading...' : f.error ? f.error : 'Uploaded'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
