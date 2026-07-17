import { useState, useRef, KeyboardEvent } from 'react'

interface Props {
  onSend: (text: string) => void
  teamName: string
}

export default function MessageInput({ onSend, teamName }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const text = value.trim()
    if (!text) return
    onSend(text)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }

  return (
    <div className="px-6 pb-6 pt-3">
      <div className="flex items-end gap-3 bg-ws-surface border border-ws-border rounded-2xl
                      px-4 py-3 transition-all duration-150 focus-within:border-ws-accent-dim">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={`Message ${teamName}...`}
          rows={1}
          className="flex-1 text-sm text-ws-text-primary placeholder-ws-text-muted
                     leading-relaxed min-h-[24px] max-h-40 overflow-y-auto"
        />
        <button
          onClick={handleSend}
          disabled={!value.trim()}
          className={`
            flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center
            transition-all duration-150
            ${value.trim()
              ? 'bg-ws-accent text-ws-bg hover:bg-ws-accent/90'
              : 'bg-ws-elevated text-ws-text-muted cursor-not-allowed'
            }
          `}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
      <p className="text-center text-ws-text-muted text-[10px] mt-2">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
