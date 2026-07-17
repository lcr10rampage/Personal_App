import { Team } from '../types'

interface Props {
  teams: Team[]
  activeTeamId: string
  onSelectTeam: (id: string) => void
}

export default function Sidebar({ teams, activeTeamId, onSelectTeam }: Props) {
  return (
    <div className="flex flex-col w-56 min-w-56 h-full bg-ws-sidebar border-r border-ws-border">

      {/* Header — drag region for frameless window */}
      <div className="drag-region flex items-center gap-2.5 px-4 pt-6 pb-5">
        <div className="w-6 h-6 rounded-md bg-ws-accent flex items-center justify-center">
          <span className="text-ws-bg text-xs font-bold">AI</span>
        </div>
        <span className="text-ws-text-primary text-sm font-semibold tracking-wide">
          Workspace
        </span>
      </div>

      {/* Teams label */}
      <div className="px-4 pb-2">
        <span className="text-ws-text-muted text-[10px] font-semibold uppercase tracking-widest">
          Teams
        </span>
      </div>

      {/* Team list */}
      <nav className="flex-1 px-2 space-y-0.5 overflow-y-auto">
        {teams.map(team => {
          const isActive = team.id === activeTeamId
          const isAvailable = team.available

          return (
            <button
              key={team.id}
              onClick={() => onSelectTeam(team.id)}
              disabled={!isAvailable}
              className={`
                no-drag w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                text-left transition-all duration-150
                ${isActive
                  ? 'bg-ws-elevated text-ws-text-primary'
                  : isAvailable
                    ? 'text-ws-text-secondary hover:bg-ws-surface hover:text-ws-text-primary'
                    : 'text-ws-text-muted cursor-not-allowed opacity-50'
                }
              `}
            >
              {/* Icon */}
              <span className={`text-base ${isActive ? 'text-ws-accent' : ''}`}>
                {team.icon}
              </span>

              {/* Name + badge */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium truncate">{team.name}</span>
                  {!isAvailable && (
                    <span className="text-[9px] font-semibold text-ws-text-muted border border-ws-border rounded px-1 py-0.5 uppercase tracking-wide">
                      Soon
                    </span>
                  )}
                </div>
                {isActive && (
                  <p className="text-[11px] text-ws-text-muted truncate mt-0.5">
                    {team.description}
                  </p>
                )}
              </div>

              {/* Active indicator */}
              {isActive && (
                <div className="w-1.5 h-1.5 rounded-full bg-ws-accent flex-shrink-0" />
              )}
            </button>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="px-2 pb-4 pt-2 border-t border-ws-border mt-2">
        <button className="no-drag w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-ws-text-muted hover:text-ws-text-secondary hover:bg-ws-surface transition-all duration-150">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="text-sm">Settings</span>
        </button>
      </div>
    </div>
  )
}
