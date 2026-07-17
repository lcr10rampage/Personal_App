import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import { Team, Message } from './types'

const TEAMS: Team[] = [
  {
    id: 'life_manager',
    name: 'Life Manager',
    description: 'Your personal chief of staff',
    icon: '◆',
    available: true,
    agents: [
      { id: 'orchestrator', name: 'Orchestrator', status: 'ready' },
      { id: 'calendar',     name: 'Time Manager', status: 'ready' },
      { id: 'email',        name: 'Comms Manager', status: 'ready' },
      { id: 'memory',       name: 'Memory AI', status: 'ready' },
    ],
  },
  {
    id: 'app_builder',
    name: 'App Builder',
    description: 'Design and build applications',
    icon: '⬡',
    available: false,
    agents: [],
  },
  {
    id: 'website_builder',
    name: 'Website Builder',
    description: 'Build and deploy websites',
    icon: '◈',
    available: false,
    agents: [],
  },
]

export default function App() {
  const [activeTeamId, setActiveTeamId] = useState('life_manager')
  const [messagesByTeam, setMessagesByTeam] = useState<Record<string, Message[]>>({})

  const activeTeam = TEAMS.find(t => t.id === activeTeamId)!
  const messages = messagesByTeam[activeTeamId] || []

  const handleSend = (text: string) => {
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessagesByTeam(prev => ({
      ...prev,
      [activeTeamId]: [...(prev[activeTeamId] || []), userMsg],
    }))
    // Backend wiring goes here later
  }

  const handleSelectTeam = (teamId: string) => {
    const team = TEAMS.find(t => t.id === teamId)
    if (team?.available) setActiveTeamId(teamId)
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-ws-bg">
      <Sidebar
        teams={TEAMS}
        activeTeamId={activeTeamId}
        onSelectTeam={handleSelectTeam}
      />
      <ChatWindow
        team={activeTeam}
        messages={messages}
        onSend={handleSend}
      />
    </div>
  )
}
