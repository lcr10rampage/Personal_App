import { useEffect, useRef } from 'react'
import { Team, Message } from '../types'
import MessageInput from './MessageInput'

interface Props {
  team: Team
  messages: Message[]
  onSend: (text: string) => void
}

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

function AgentDot({ status }: { status: string }) {
  return (
    <span className={`
      inline-block w-1.5 h-1.5 rounded-full
      ${status === 'ready' ? 'bg-ws-green animate-pulse-dot' : 'bg-ws-text-muted'}
    `} />
  )
}

function WelcomeScreen({ team }: { team: Team }) {
  const suggestions = [
    'What\'s on my schedule today?',
    'Check my emails',
    'Any RSVPs pending?',
    'Help me plan my week',
  ]

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-8 animate-fade-in">
      <div className="text-ws-accent text-4xl mb-6">{team.icon}</div>
      <h1 className="text-ws-text-primary text-2xl font-semibold mb-2">
        {getGreeting()}.
      </h1>
      <p className="text-ws-text-secondary text-sm mb-10">
        {team.description}. What would you like to work on?
      </p>
      <div className="flex flex-wrap gap-2 justify-center max-w-lg">
        {suggestions.map(s => (
          <button
            key={s}
            className="px-3.5 py-2 rounded-lg border border-ws-border text-ws-text-secondary text-sm
                       hover:border-ws-accent-dim hover:text-ws-text-primary hover:bg-ws-surface
                       transition-all duration-150"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex w-full mb-6 animate-slide-up ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-ws-elevated flex items-center justify-center
                        text-ws-accent text-xs font-bold mr-3 mt-0.5 flex-shrink-0">
          AI
        </div>
      )}
      <div className={`max-w-[72%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div className={`
          px-4 py-3 rounded-2xl text-sm leading-relaxed
          ${isUser
            ? 'bg-ws-user text-ws-text-primary rounded-tr-sm'
            : 'bg-ws-agent text-ws-text-primary rounded-tl-sm'
          }
        `}>
          {message.content}
        </div>
        <span className="text-ws-text-muted text-[10px] mt-1.5 px-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-ws-accent flex items-center justify-center
                        text-ws-bg text-xs font-bold ml-3 mt-0.5 flex-shrink-0">
          Y
        </div>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex items-start mb-6 animate-fade-in">
      <div className="w-7 h-7 rounded-full bg-ws-elevated flex items-center justify-center
                      text-ws-accent text-xs font-bold mr-3 flex-shrink-0">
        AI
      </div>
      <div className="bg-ws-agent px-4 py-3.5 rounded-2xl rounded-tl-sm flex gap-1.5 items-center">
        {[0, 1, 2].map(i => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-ws-text-muted animate-typing"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  )
}

export default function ChatWindow({ team, messages, onSend }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const isThinking = false // will be wired up later

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden">

      {/* Header */}
      <div className="drag-region flex items-center justify-between px-6 pt-5 pb-4 border-b border-ws-border bg-ws-bg">
        <div className="no-drag">
          <h2 className="text-ws-text-primary font-semibold text-base">{team.name}</h2>
          <p className="text-ws-text-muted text-xs mt-0.5">{team.description}</p>
        </div>

        {/* Agent status pills */}
        {team.available && (
          <div className="no-drag flex items-center gap-3">
            {team.agents.map(agent => (
              <div key={agent.id} className="flex items-center gap-1.5">
                <AgentDot status={agent.status} />
                <span className="text-ws-text-muted text-xs">{agent.name}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {messages.length === 0
          ? <WelcomeScreen team={team} />
          : (
            <>
              {messages.map(m => (
                <MessageBubble key={m.id} message={m} />
              ))}
              {isThinking && <TypingIndicator />}
              <div ref={bottomRef} />
            </>
          )
        }
      </div>

      {/* Input */}
      <MessageInput onSend={onSend} teamName={team.name} />
    </div>
  )
}
