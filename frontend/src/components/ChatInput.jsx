import React, { useState, useRef } from 'react'
import { Send, Mic, MicOff, Loader2 } from 'lucide-react'
import { useVoiceInput } from '../hooks/useVoiceInput'
import clsx from 'clsx'

export default function ChatInput({ onSubmit, disabled, hasDocuments }) {
  const [input, setInput] = useState('')
  const textareaRef = useRef(null)

  const { listening, supported: voiceSupported, startListening, stopListening } = useVoiceInput((transcript) => {
    setInput(prev => prev ? prev + ' ' + transcript : transcript)
    textareaRef.current?.focus()
  })

  const handleSubmit = () => {
    const q = input.trim()
    if (!q || disabled) return
    onSubmit(q)
    setInput('')
    // Reset textarea height
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleInput = (e) => {
    setInput(e.target.value)
    // Auto-resize
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 160) + 'px'
    }
  }

  return (
    <div className={clsx(
      'flex items-end gap-2 p-3 rounded-xl border transition-all duration-200',
      'bg-[var(--bg-primary)] border-[var(--border)]',
      'focus-within:border-[var(--accent)] focus-within:shadow-sm focus-within:shadow-blue-100 dark:focus-within:shadow-blue-950/20'
    )}>
      {/* Text area */}
      <textarea
        ref={textareaRef}
        value={input}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder={hasDocuments ? 'Ask anything about your PDFs… (Enter to send, Shift+Enter for newline)' : 'Upload a PDF first to start chatting…'}
        disabled={disabled || !hasDocuments}
        rows={1}
        className={clsx(
          'flex-1 resize-none bg-transparent text-sm text-[var(--text-primary)]',
          'placeholder:text-[var(--text-muted)] outline-none min-h-[36px] max-h-40',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      />

      {/* Voice input button */}
      {voiceSupported && (
        <button
          type="button"
          onClick={listening ? stopListening : startListening}
          disabled={disabled || !hasDocuments}
          title={listening ? 'Stop voice input' : 'Voice input'}
          className={clsx(
            'p-2 rounded-lg transition-all duration-200 shrink-0',
            listening
              ? 'bg-red-500 text-white animate-pulse'
              : 'text-[var(--text-muted)] hover:text-[var(--accent)] hover:bg-[var(--bg-secondary)]',
            'disabled:opacity-40 disabled:cursor-not-allowed'
          )}
        >
          {listening ? <MicOff size={18} /> : <Mic size={18} />}
        </button>
      )}

      {/* Send button */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={disabled || !input.trim() || !hasDocuments}
        className={clsx(
          'p-2 rounded-lg transition-all duration-200 shrink-0',
          input.trim() && !disabled && hasDocuments
            ? 'bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] shadow-sm'
            : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] cursor-not-allowed'
        )}
      >
        {disabled
          ? <Loader2 size={18} className="animate-spin" />
          : <Send size={18} />}
      </button>
    </div>
  )
}
