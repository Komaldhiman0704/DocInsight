import React, { useState } from 'react'
import { Trash2, Edit2, MessageSquare } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function SessionList({
  sessions = [],
  onSessionSelect,
  onSessionCreate,
  onSessionDelete,
  onSessionRename,
  currentSessionId,
  loading = false,
}) {
  const [renaming, setRenaming] = useState(null)
  const [newTitle, setNewTitle] = useState('')

  /**
   * Group sessions by date
   * Returns { "Today": [...], "Yesterday": [...], "Older": [...] }
   */
  function groupByDate(sessions) {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    const groups = { Today: [], Yesterday: [], Older: [] }

    for (const session of sessions) {
      const sessionDate = new Date(session.created_at)
      const sessionDay = new Date(sessionDate.getFullYear(), sessionDate.getMonth(), sessionDate.getDate())

      if (sessionDay.getTime() === today.getTime()) {
        groups.Today.push(session)
      } else if (sessionDay.getTime() === yesterday.getTime()) {
        groups.Yesterday.push(session)
      } else {
        groups.Older.push(session)
      }
    }

    return groups
  }

  function getRelativeTime(dateStr) {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  async function handleRename(sessionId, oldTitle) {
    setRenaming(sessionId)
    setNewTitle(oldTitle)
  }

  async function submitRename(sessionId) {
    if (!newTitle.trim()) {
      setRenaming(null)
      return
    }

    try {
      await onSessionRename(sessionId, newTitle)
      setRenaming(null)
      toast.success('Session renamed')
    } catch (e) {
      toast.error(`Rename failed: ${e.message}`)
    }
  }

  async function handleDelete(sessionId) {
    if (!confirm('Delete this conversation?')) return
    try {
      await onSessionDelete(sessionId)
      toast.success('Conversation deleted')
    } catch (e) {
      toast.error(`Delete failed: ${e.message}`)
    }
  }

  const groups = groupByDate(sessions)
  const hasAny = sessions.length > 0

  return (
    <div className="space-y-3 text-sm">
      {/* New Chat Button */}
      <button
        onClick={onSessionCreate}
        className={clsx(
          'w-full py-2 px-3 rounded-lg border transition-all duration-200',
          'border-[var(--border)] bg-[var(--bg-primary)] text-[var(--text-primary)]',
          'hover:border-[var(--accent)] hover:bg-[var(--bg-secondary)]'
        )}
      >
        <span className="font-medium">+ New Chat</span>
      </button>

      {!hasAny && (
        <div className="text-center py-6 text-[var(--text-muted)]">
          <MessageSquare size={20} className="mx-auto mb-2 opacity-50" />
          <p className="text-xs">No conversations yet</p>
        </div>
      )}

      {/* Sessions grouped by date */}
      {['Today', 'Yesterday', 'Older'].map(groupLabel => {
        const groupSessions = groups[groupLabel]
        if (groupSessions.length === 0) return null

        return (
          <div key={groupLabel} className="space-y-1">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] px-1">
              {groupLabel}
            </p>

            {groupSessions.map(session => (
              <div
                key={session.id}
                className={clsx(
                  'group relative p-2.5 rounded-lg border transition-all duration-200 cursor-pointer',
                  'hover:bg-[var(--bg-tertiary)] border-transparent',
                  currentSessionId === session.id
                    ? 'bg-[var(--bg-tertiary)] border-l-2 border-l-[var(--accent)]'
                    : ''
                )}
                onClick={() => onSessionSelect(session.id)}
              >
                {renaming === session.id ? (
                  // Rename input
                  <input
                    autoFocus
                    type="text"
                    value={newTitle}
                    onChange={e => setNewTitle(e.target.value)}
                    onBlur={() => submitRename(session.id)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') submitRename(session.id)
                      if (e.key === 'Escape') setRenaming(null)
                    }}
                    onClick={e => e.stopPropagation()}
                    className={clsx(
                      'w-full px-2 py-1 rounded text-xs bg-[var(--bg-secondary)] border border-[var(--border)]',
                      'text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]'
                    )}
                  />
                ) : (
                  <>
                    {/* Session info */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-[var(--text-primary)] line-clamp-1 text-xs">
                          {session.title}
                        </p>
                        <p className="text-[10px] text-[var(--text-muted)]">
                          {session.message_count} messages • {getRelativeTime(session.created_at)}
                        </p>
                      </div>

                      {/* Action buttons (show on hover) */}
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 shrink-0">
                        <button
                          onClick={e => {
                            e.stopPropagation()
                            handleRename(session.id, session.title)
                          }}
                          title="Rename"
                          className={clsx(
                            'p-1 rounded transition-colors duration-200',
                            'hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                          )}
                        >
                          <Edit2 size={13} />
                        </button>
                        <button
                          onClick={e => {
                            e.stopPropagation()
                            handleDelete(session.id)
                          }}
                          title="Delete"
                          className={clsx(
                            'p-1 rounded transition-colors duration-200',
                            'hover:bg-red-500/10 text-[var(--text-muted)] hover:text-red-500'
                          )}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )
      })}
    </div>
  )
}
