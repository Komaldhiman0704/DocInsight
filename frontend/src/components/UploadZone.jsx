import React, { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { uploadPDF } from '../utils/api'
import clsx from 'clsx'

export default function UploadZone({ onUploadSuccess }) {
  const [uploads, setUploads] = useState([]) // { file, status, progress, error }

  const onDrop = async (accepted) => {
    for (const file of accepted) {
      const id = Date.now() + Math.random()
      setUploads(prev => [...prev, { id, file, status: 'uploading', progress: 0 }])

      try {
        const result = await uploadPDF(file, (pct) => {
          setUploads(prev => prev.map(u => u.id === id ? { ...u, progress: pct } : u))
        })
        setUploads(prev => prev.map(u => u.id === id ? { ...u, status: 'done', progress: 100 } : u))
        onUploadSuccess(result.document)

        // Remove from list after 3s
        setTimeout(() => setUploads(prev => prev.filter(u => u.id !== id)), 3000)
      } catch (err) {
        setUploads(prev => prev.map(u => u.id === id ? { ...u, status: 'error', error: err.message } : u))
      }
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    multiple: true,
    maxSize: 100 * 1024 * 1024,
  })

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200',
          isDragActive
            ? 'border-[var(--accent)] bg-blue-50 dark:bg-blue-950/20 scale-[1.01]'
            : 'border-[var(--border)] hover:border-[var(--accent)] hover:bg-[var(--bg-secondary)]'
        )}
      >
        <input {...getInputProps()} />
        <Upload
          size={28}
          className={clsx('mx-auto mb-3 transition-colors', isDragActive ? 'text-[var(--accent)]' : 'text-[var(--text-muted)]')}
        />
        <p className="text-sm font-medium text-[var(--text-primary)]">
          {isDragActive ? 'Drop files here…' : 'Drag & drop files here'}
        </p>
        <p className="text-xs text-[var(--text-muted)] mt-1">PDFs, DOCX, or TXT · max 100MB each</p>
      </div>

      {/* Upload progress list */}
      {uploads.length > 0 && (
        <div className="space-y-2">
          {uploads.map(u => (
            <div
              key={u.id}
              className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm animate-fade-in"
            >
              <FileText size={16} className="shrink-0 text-[var(--text-muted)]" />
              <span className="flex-1 truncate text-[var(--text-primary)]">{u.file.name}</span>

              {u.status === 'uploading' && (
                <div className="flex items-center gap-2 shrink-0">
                  <div className="w-20 h-1.5 bg-[var(--border)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[var(--accent)] rounded-full transition-all duration-300"
                      style={{ width: `${u.progress}%` }}
                    />
                  </div>
                  <Loader2 size={14} className="animate-spin text-[var(--accent)]" />
                </div>
              )}
              {u.status === 'done' && <CheckCircle2 size={16} className="text-green-500 shrink-0" />}
              {u.status === 'error' && (
                <div className="flex items-center gap-1 text-red-500 shrink-0">
                  <XCircle size={14} />
                  <span className="text-xs">{u.error}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
