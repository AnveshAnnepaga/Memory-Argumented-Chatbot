'use client';

import React from 'react';
import type { FileAttachment } from '@/store/useChatStore';

interface AttachmentRendererProps {
  attachments: FileAttachment[];
}

function getFileIcon(type: string): string {
  switch (type) {
    case 'pdf': return '📄';
    case 'docx': return '📝';
    case 'image': return '🖼️';
    default: return '📎';
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

export default function AttachmentRenderer({ attachments }: AttachmentRendererProps) {
  if (!attachments || attachments.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
      {attachments.map((att) => (
        <div
          key={att.fileId}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '3px 8px',
            borderRadius: '6px',
            background: '#1f2937',
            border: '1px solid #374151',
            fontSize: '12px',
            color: '#d1d5db',
          }}
        >
          <span>{getFileIcon(att.type)}</span>
          <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {att.filename}
          </span>
          {att.sizeBytes > 0 && (
            <span style={{ color: '#6b7280', fontSize: '11px' }}>{formatSize(att.sizeBytes)}</span>
          )}
        </div>
      ))}
    </div>
  );
}
