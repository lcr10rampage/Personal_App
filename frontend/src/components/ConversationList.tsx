import { Conversation } from '../types'

interface Props {
  teamName: string
  conversations: Conversation[]
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  onDelete: (id: string) => void
}

function relTime(sec: number): string {
  if (!sec) return ''
  const diff = Date.now() / 1000 - sec
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function ConversationList({
  teamName, conversations, activeId, onSelect, onNew, onDelete,
}: Props) {
  return (
    <div className="flex flex-col w-60 min-w-60 h-full bg-ws-sidebar border-r border-ws-border">
      <div className="px-4 pt-5 pb-3">
        <div className="text-ws-text-muted text-xs font-semibold uppercase tracking-widest mb-2">
          {teamName}
        </div>
        <button
          onClick={onNew}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg
                     border border-ws-border text-ws-text-secondary text-sm
                     hover:border-ws-accent-dim hover:text-ws-text-primary hover:bg-ws-surface
                     transition-all duration-150"
        >
          <span className="text-base leading-none">+</span> New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-0.5">
        {conversations.length === 0 && (
          <p className="text-ws-text-muted text-xs px-3 py-2">No conversations yet.</p>
        )}
        {conversations.map(c => {
          const isActive = c.id === activeId
          return (
            <div
              key={c.id}
              onClick={() => onSelect(c.id)}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
                transition-all duration-150
                ${isActive
                  ? 'bg-ws-elevated text-ws-text-primary'
                  : 'text-ws-text-secondary hover:bg-ws-surface hover:text-ws-text-primary'}`}
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm truncate">{c.title}</div>
                <div className="text-[10px] text-ws-text-muted">{relTime(c.updated)}</div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(c.id) }}
                title="Delete conversation"
                className="opacity-0 group-hover:opacity-100 text-ws-text-muted hover:text-ws-accent
                           text-xs px-1 transition-opacity"
              >
                ✕
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
