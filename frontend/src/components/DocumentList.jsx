import React, { useState } from 'react'
import { FileText, Trash2, CheckSquare, Square, Loader2, Hash } from 'lucide-react'
import { deleteDocument } from '../utils/api'
import clsx from 'clsx'
import toast from 'react-hot-toast'

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso) {
  try {
    const date = new Date(iso)
    // Check if date is valid
    if (isNaN(date.getTime())) return 'Just now'
    return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  } catch {
    return 'Just now'
  }
}

export default function DocumentList({ documents, selectedIds, onToggle, onDeleted }) {
  const [deleting, setDeleting] = useState(null)

  const handleDelete = async (doc) => {
    if (!confirm(`Delete "${doc.filename}"? This cannot be undone.`)) return
    setDeleting(doc.id)
    try {
      await deleteDocument(doc.id)
      onDeleted(doc.id)
      toast.success(`"${doc.filename}" deleted`)
    } catch {
      toast.error('Failed to delete document')
    } finally {
      setDeleting(null)
    }
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-[var(--text-muted)]">
        <FileText size={32} className="mx-auto mb-2 opacity-30" />
        <p className="text-sm">No documents uploaded yet</p>
      </div>
    )
  }

  const allSelected = documents.every(d => selectedIds.includes(d.id))

  return (
    <div className="space-y-1">
      {/* Select all toggle */}
      <button
        onClick={() => {
          if (allSelected) documents.forEach(d => selectedIds.includes(d.id) && onToggle(d.id))
          else documents.forEach(d => !selectedIds.includes(d.id) && onToggle(d.id))
        }}
        className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
      >
        {allSelected ? <CheckSquare size={13} /> : <Square size={13} />}
        {allSelected ? 'Deselect all' : 'Select all'}
      </button>

      {documents.map(doc => {
        const selected = selectedIds.includes(doc.id)
        return (
          <div
            key={doc.id}
            className={clsx(
              'group flex items-start gap-2 p-2.5 rounded-lg border cursor-pointer transition-all duration-150',
              selected
                ? 'border-[var(--accent)] bg-blue-50 dark:bg-blue-950/20'
                : 'border-transparent hover:border-[var(--border)] hover:bg-[var(--bg-secondary)]'
            )}
            onClick={() => onToggle(doc.id)}
          >
            {/* Checkbox */}
            <div className={clsx('mt-0.5 shrink-0 transition-colors', selected ? 'text-[var(--accent)]' : 'text-[var(--text-muted)]')}>
              {selected ? <CheckSquare size={15} /> : <Square size={15} />}
            </div>

            {/* Doc info */}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-[var(--text-primary)] truncate leading-tight">{doc.filename}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] text-[var(--text-muted)]">{formatBytes(doc.file_size)}</span>
                <span className="text-[var(--text-muted)] text-[10px]">·</span>
                <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-0.5">
                  <Hash size={9} />{doc.chunk_count} {doc.chunk_count === 1 ? 'chunk' : 'chunks'}
                </span>
                <span className="text-[var(--text-muted)] text-[10px]">·</span>
                <span className="text-[10px] text-[var(--text-muted)]">{formatDate(doc.uploaded_at)}</span>
              </div>
            </div>

            {/* Delete button */}
            <button
              onClick={(e) => { e.stopPropagation(); handleDelete(doc) }}
              disabled={deleting === doc.id}
              className="shrink-0 p-1 rounded opacity-0 group-hover:opacity-100 text-[var(--text-muted)] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-all"
            >
              {deleting === doc.id
                ? <Loader2 size={13} className="animate-spin" />
                : <Trash2 size={13} />}
            </button>
          </div>
        )
      })}
    </div>
  )
}
