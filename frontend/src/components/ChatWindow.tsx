import { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Team, Message } from '../types'
import MessageInput from './MessageInput'

interface Props {
  team: Team
  messages: Message[]
  onSend: (text: string) => void
  isThinking?: boolean
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
      inline-block w-1.5 h-1.5 rounded-full transition-colors duration-300
      ${status === 'ready'    ? 'bg-ws-green animate-pulse-dot' :
        status === 'thinking' ? 'bg-ws-accent animate-pulse-dot' :
                                'bg-ws-text-muted'}
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
      <h1 className="text-ws-text-primary text-3xl font-semibold mb-3">
        {getGreeting()}.
      </h1>
      <p className="text-ws-text-secondary text-base mb-10">
        {team.description}. What would you like to work on?
      </p>
      <div className="flex flex-wrap gap-2.5 justify-center max-w-lg">
        {suggestions.map(s => (
          <button
            key={s}
            className="px-4 py-2.5 rounded-lg border border-ws-border text-ws-text-secondary text-sm
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

// Renders assistant markdown (headings, lists, tables, bold, code) themed to the workspace palette.
function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="text-[15px] leading-relaxed text-ws-text-primary space-y-3
                    [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="text-lg font-semibold text-ws-text-primary mt-4 mb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-base font-semibold text-ws-text-primary mt-4 mb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="text-[15px] font-semibold text-ws-text-primary mt-3 mb-1.5">{children}</h3>,
          p:  ({ children }) => <p className="my-2">{children}</p>,
          ul: ({ children }) => <ul className="list-disc pl-5 my-2 space-y-1 marker:text-ws-accent-dim">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 my-2 space-y-1 marker:text-ws-text-muted">{children}</ol>,
          li: ({ children }) => <li className="pl-1">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-ws-text-primary">{children}</strong>,
          em: ({ children }) => <em className="italic text-ws-text-secondary">{children}</em>,
          a:  ({ children, href }) => <a href={href} className="text-ws-accent underline underline-offset-2 hover:text-ws-text-primary">{children}</a>,
          blockquote: ({ children }) => <blockquote className="border-l-2 border-ws-accent pl-3 my-2 text-ws-text-secondary italic">{children}</blockquote>,
          hr: () => <hr className="border-ws-border my-4" />,
          code: ({ className, children }) =>
            className?.includes('language-')
              ? <code className={className}>{children}</code>
              : <code className="bg-ws-elevated text-ws-accent px-1.5 py-0.5 rounded text-[13px]">{children}</code>,
          pre: ({ children }) => <pre className="bg-ws-bg border border-ws-border rounded-lg p-3 my-2 overflow-x-auto text-[13px] leading-relaxed">{children}</pre>,
          table: ({ children }) => (
            <div className="my-3 overflow-x-auto rounded-lg border border-ws-border">
              <table className="w-full border-collapse text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-ws-surface">{children}</thead>,
          th: ({ children }) => <th className="text-left font-semibold text-ws-text-primary px-3 py-2 border-b border-ws-border">{children}</th>,
          td: ({ children }) => <td className="px-3 py-2 border-b border-ws-border/60 align-top text-ws-text-secondary">{children}</td>,
        }}
      >
        {content}
      </ReactMarkdown>
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
      <div className={`${isUser ? 'max-w-[72%] items-end' : 'max-w-[85%] items-start'} flex flex-col min-w-0`}>
        <div className={`
          px-5 py-3.5 rounded-2xl text-base leading-relaxed
          ${isUser
            ? 'bg-ws-user text-ws-text-primary rounded-tr-sm'
            : 'bg-ws-agent text-ws-text-primary rounded-tl-sm w-full'
          }
        `}>
          {isUser ? message.content : <MarkdownContent content={message.content} />}
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

export default function ChatWindow({ team, messages, onSend, isThinking = false }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden">

      {/* Header */}
      <div className="drag-region flex items-center justify-between px-6 pt-5 pb-4 border-b border-ws-border bg-ws-bg">
        <div className="no-drag">
          <h2 className="text-ws-text-primary font-semibold text-lg">{team.name}</h2>
          <p className="text-ws-text-muted text-sm mt-0.5">{team.description}</p>
        </div>

        {/* Agent status pills */}
        {team.available && (
          <div className="no-drag flex items-center gap-3">
            {team.agents.map(agent => (
              <div key={agent.id} className="flex items-center gap-1.5">
                <AgentDot status={agent.status} />
                <span className="text-ws-text-muted text-sm">{agent.name}</span>
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
