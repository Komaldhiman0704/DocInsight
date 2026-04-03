import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Moon, Sun, Trash2, MessageSquare, ChevronLeft, ChevronRight, Bot } from 'lucide-react'
import { Toaster } from 'react-hot-toast'
import toast from 'react-hot-toast'

import { useDarkMode } from './hooks/useDarkMode'
import { listDocuments, streamChat } from './utils/api'

import UploadZone from './components/UploadZone'
import DocumentList from './components/DocumentList'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'

const SUGGESTIONS = [
  'Summarize this document',
  'What are the key points?',
  'List the main conclusions',
  'What is this document about?',
]

export default function App() {
  const [dark, setDark] = useDarkMode()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const [documents, setDocuments] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [docsLoading, setDocsLoading] = useState(true)

  const [messages, setMessages] = useState([])
  const [chatting, setChatting] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => { loadDocuments() }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function loadDocuments() {
    setDocsLoading(true)
    try {
      const data = await listDocuments()
      setDocuments(data.documents || [])
      setSelectedIds((data.documents || []).map(d => d.id))
    } catch {
      toast.error('Could not reach backend. Is it running?')
    } finally {
      setDocsLoading(false)
    }
  }

  function handleDocumentUploaded(doc) {
    setDocuments(prev => [doc, ...prev])
    setSelectedIds(prev => [doc.id, ...prev])
    toast.success(`"${doc.filename}" ready!`, { icon: '📄' })
  }

  function handleDocumentDeleted(docId) {
    setDocuments(prev => prev.filter(d => d.id !== docId))
    setSelectedIds(prev => prev.filter(id => id !== docId))
  }

  function toggleDocument(docId) {
    setSelectedIds(prev =>
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    )
  }

  function clearChat() {
    if (messages.length === 0) return
    if (!confirm('Clear chat history?')) return
    setMessages([])
  }

  function buildHistory() {
    return messages
      .filter(m => m.status === 'done' || m.role === 'user')
      .slice(-10)
      .map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content }))
  }

  const handleSend = useCallback(async (question) => {
    if (chatting) return

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: question,
      status: 'done',
      timestamp: new Date().toISOString(),
    }

    const aiMsgId = Date.now() + 1
    const aiMsg = {
      id: aiMsgId,
      role: 'assistant',
      content: '',
      sources: [],
      status: 'thinking',
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMsg, aiMsg])
    setChatting(true)

    try {
      const history = buildHistory()
      let fullContent = ''

      for await (const chunk of streamChat({
        question,
        chatHistory: history,
        docIds: selectedIds,
      })) {
        if (chunk.type === 'sources') {
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId
              ? { ...m, sources: chunk.sources, status: 'streaming' }
              : m
          ))
        } else if (chunk.type === 'token') {
          fullContent += chunk.token
          const captured = fullContent
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId
              ? { ...m, content: captured, status: 'streaming' }
              : m
          ))
        }
      }

      setMessages(prev => prev.map(m =>
        m.id === aiMsgId ? { ...m, status: 'done' } : m
      ))
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === aiMsgId
          ? { ...m, content: `⚠️ Error: ${err.message}`, status: 'done' }
          : m
      ))
      toast.error(err.message)
    } finally {
      setChatting(false)
    }
  }, [chatting, selectedIds, messages])

  const hasDocuments = documents.length > 0
  const hasSelected = selectedIds.length > 0

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)]">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border)',
            fontSize: '13px',
          }
        }}
      />

      {/* ── Sidebar ── */}
      <aside
        className="flex flex-col shrink-0 border-r border-[var(--border)] bg-[var(--bg-secondary)] transition-all duration-300 overflow-hidden"
        style={{ width: sidebarOpen ? '288px' : '0px', minWidth: sidebarOpen ? '288px' : '0px' }}
      >
        <div className="flex flex-col h-full" style={{ minWidth: '288px' }}>
          {/* Header */}
          <div className="flex items-center gap-2.5 px-4 py-4 border-b border-[var(--border)]">
            <div className="w-7 h-7 rounded-lg bg-[var(--accent)] flex items-center justify-center shrink-0">
              <Bot size={14} className="text-white" />
            </div>
            <span className="font-semibold text-sm text-[var(--text-primary)]">PDF Chatbot AI</span>
          </div>

          {/* Upload */}
          <div className="p-3 border-b border-[var(--border)]">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2 px-1">
              Upload PDFs
            </p>
            <UploadZone onUploadSuccess={handleDocumentUploaded} />
          </div>

          {/* Documents */}
          <div className="flex-1 overflow-y-auto p-3">
            <div className="flex items-center gap-2 mb-2 px-1">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                Your Documents
              </p>
              {documents.length > 0 && (
                <span className="px-1.5 py-0.5 rounded-md bg-[var(--bg-tertiary)] text-[var(--text-muted)] font-mono text-[10px]">
                  {selectedIds.length}/{documents.length}
                </span>
              )}
            </div>

            {docsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-14 rounded-lg shimmer" />
                ))}
              </div>
            ) : (
              <DocumentList
                documents={documents}
                selectedIds={selectedIds}
                onToggle={toggleDocument}
                onDeleted={handleDocumentDeleted}
              />
            )}
          </div>

          {/* Warning */}
          {!hasSelected && hasDocuments && (
            <div className="px-3 py-2 border-t border-[var(--border)]">
              <p className="text-xs text-amber-600 dark:text-amber-400 text-center">
                ⚠ Select at least one document to chat
              </p>
            </div>
          )}
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex flex-col flex-1 min-w-0">
        {/* Topbar */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-primary)] shrink-0">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
          >
            {sidebarOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
          </button>

          <div className="flex-1 text-sm text-[var(--text-secondary)]">
            {!hasDocuments
              ? <span className="text-[var(--text-muted)]">Upload a PDF to get started</span>
              : !hasSelected
                ? <span className="text-amber-600 dark:text-amber-400">Select at least one document</span>
                : <span>Querying <strong className="text-[var(--text-primary)]">{selectedIds.length}</strong> document{selectedIds.length > 1 ? 's' : ''}</span>
            }
          </div>

          <div className="flex items-center gap-1">
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-red-500 transition-colors"
                title="Clear chat"
              >
                <Trash2 size={16} />
              </button>
            )}
            <button
              onClick={() => setDark(!dark)}
              className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              title="Toggle dark mode"
            >
              {dark ? <Sun size={17} /> : <Moon size={17} />}
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center select-none">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center mb-4 shadow-lg shadow-blue-200 dark:shadow-blue-900/30">
                <MessageSquare size={26} className="text-white" />
              </div>
              <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
                Ask your PDFs anything
              </h2>
              <p className="text-sm text-[var(--text-muted)] max-w-sm mb-6 leading-relaxed">
                Upload PDF documents and chat with them using AI.
                Get answers with exact page citations.
              </p>
              {hasSelected && (
                <div className="flex flex-wrap gap-2 justify-center max-w-md">
                  {SUGGESTIONS.map(s => (
                    <button
                      key={s}
                      onClick={() => handleSend(s)}
                      className="px-3 py-1.5 text-xs rounded-full border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)] hover:text-[var(--accent)] hover:bg-blue-50 dark:hover:bg-blue-950/20 transition-all"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            messages.map(msg => <ChatMessage key={msg.id} message={msg} />)
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-4 pb-4 shrink-0">
          <ChatInput
            onSubmit={handleSend}
            disabled={chatting}
            hasDocuments={hasSelected}
          />
          <p className="text-center text-[10px] text-[var(--text-muted)] mt-2">
            AI may make mistakes · Always verify answers with source documents
          </p>
        </div>
      </main>
    </div>
  )
}
