import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import TitleBar from './components/TitleBar'
import { sendMessage } from './api'
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
  const [isThinking, setIsThinking] = useState(false)

  const activeTeam = TEAMS.find(t => t.id === activeTeamId)!
  const messages = messagesByTeam[activeTeamId] || []

  const addMessage = (teamId: string, message: Message) => {
    setMessagesByTeam(prev => ({
      ...prev,
      [teamId]: [...(prev[teamId] || []), message],
    }))
  }

  const handleSend = async (text: string) => {
    const teamId = activeTeamId

    addMessage(teamId, {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    })

    setIsThinking(true)

    try {
      const response = await sendMessage(text)
      addMessage(teamId, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      })
    } catch (err) {
      addMessage(teamId, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Could not reach the backend. Make sure your SSH tunnel is active and the server is running.',
        timestamp: new Date(),
      })
    } finally {
      setIsThinking(false)
    }
  }

  const handleSelectTeam = (teamId: string) => {
    const team = TEAMS.find(t => t.id === teamId)
    if (team?.available) setActiveTeamId(teamId)
  }

  const activeAgents = isThinking && activeTeamId === 'life_manager'
    ? activeTeam.agents.map((a, i) => ({ ...a, status: i === 0 ? 'thinking' as const : a.status }))
    : activeTeam.agents

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-ws-bg">
      <TitleBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          teams={TEAMS}
          activeTeamId={activeTeamId}
          onSelectTeam={handleSelectTeam}
        />
        <ChatWindow
          team={{ ...activeTeam, agents: activeAgents }}
          messages={messages}
          onSend={handleSend}
          isThinking={isThinking}
        />
      </div>
    </div>
  )
}
