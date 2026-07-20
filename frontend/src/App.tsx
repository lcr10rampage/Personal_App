import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ConversationList from './components/ConversationList'
import ChatWindow from './components/ChatWindow'
import TitleBar from './components/TitleBar'
import {
  sendMessage, listConversations, createConversation,
  getConversationMessages, deleteConversation,
} from './api'
import { Team, Message, Conversation } from './types'

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
    description: 'Design, build, review, and test applications',
    icon: '⬡',
    available: true,
    agents: [
      { id: 'architect', name: 'Architect', status: 'ready' },
      { id: 'engineer',  name: 'Engineer', status: 'ready' },
      { id: 'manager',   name: 'Manager', status: 'ready' },
      { id: 'tester',    name: 'Tester', status: 'ready' },
    ],
  },
  {
    id: 'hobby_project',
    name: 'Project & Hobby Team',
    description: 'Plan hobbies and physical build projects in detail',
    icon: '⬢',
    available: true,
    agents: [
      { id: 'coordinator',   name: 'Coordinator',    status: 'ready' },
      { id: 'measurement',   name: 'Measurement',    status: 'ready' },
      { id: 'designer',      name: 'Designer',       status: 'ready' },
      { id: 'functionality', name: 'Functionality',  status: 'ready' },
      { id: 'cost',          name: 'Cost',           status: 'ready' },
      { id: 'risk',          name: 'Risk',           status: 'ready' },
      { id: 'time',          name: 'Time',           status: 'ready' },
      { id: 'sketch',        name: 'Sketch',         status: 'ready' },
      { id: '3d_model',      name: '3D Model',       status: 'ready' },
      { id: 'materials',     name: 'Materials',      status: 'ready' },
      { id: 'tools_skills',  name: 'Tools & Skills', status: 'ready' },
      { id: 'build_seq',     name: 'Build Sequence', status: 'ready' },
      { id: 'compat',        name: 'Compatibility',  status: 'ready' },
      { id: 'testing',       name: 'Testing',        status: 'ready' },
      { id: 'documentation', name: 'Documentation',  status: 'ready' },
    ],
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
  const [convByTeam, setConvByTeam] = useState<Record<string, Conversation[]>>({})
  const [activeConvByTeam, setActiveConvByTeam] = useState<Record<string, string | null>>({})
  const [messagesByConv, setMessagesByConv] = useState<Record<string, Message[]>>({})
  const [isThinking, setIsThinking] = useState(false)

  const activeTeam = TEAMS.find(t => t.id === activeTeamId)!
  const conversations = convByTeam[activeTeamId] || []
  const activeConvId = activeConvByTeam[activeTeamId] ?? null
  const messages = activeConvId ? (messagesByConv[activeConvId] || []) : []

  // Load a team's conversation list when it becomes active.
  useEffect(() => {
    if (!activeTeam.available) return
    let cancelled = false
    ;(async () => {
      const convs = await listConversations(activeTeamId)
      if (cancelled) return
      setConvByTeam(prev => ({ ...prev, [activeTeamId]: convs }))
      setActiveConvByTeam(prev =>
        prev[activeTeamId] !== undefined ? prev : { ...prev, [activeTeamId]: convs[0]?.id ?? null }
      )
    })()
    return () => { cancelled = true }
  }, [activeTeamId])

  // Load messages for the active conversation the first time it's opened.
  useEffect(() => {
    const cid = activeConvByTeam[activeTeamId]
    if (!cid || messagesByConv[cid]) return
    let cancelled = false
    ;(async () => {
      const msgs = await getConversationMessages(cid)
      if (!cancelled) setMessagesByConv(prev => ({ ...prev, [cid]: msgs }))
    })()
    return () => { cancelled = true }
  }, [activeTeamId, activeConvByTeam])

  const addMessage = (convId: string, message: Message) => {
    setMessagesByConv(prev => ({ ...prev, [convId]: [...(prev[convId] || []), message] }))
  }

  const handleSend = async (text: string) => {
    const teamId = activeTeamId
    let convId = activeConvByTeam[teamId] ?? null

    // Start a conversation on the first message if none is active.
    if (!convId) {
      const c = await createConversation(teamId)
      convId = c.id
      setConvByTeam(prev => ({ ...prev, [teamId]: [c, ...(prev[teamId] || [])] }))
      setActiveConvByTeam(prev => ({ ...prev, [teamId]: c.id }))
      setMessagesByConv(prev => ({ ...prev, [c.id]: [] }))
    }

    addMessage(convId, {
      id: Date.now().toString(), role: 'user', content: text, timestamp: new Date(),
    })
    setIsThinking(true)

    try {
      const result = await sendMessage(text, teamId, convId)
      addMessage(result.conversationId, {
        id: (Date.now() + 1).toString(), role: 'assistant', content: result.response, timestamp: new Date(),
      })
      // Refresh the list so titles/order stay current.
      const convs = await listConversations(teamId)
      setConvByTeam(prev => ({ ...prev, [teamId]: convs }))
    } catch (err) {
      addMessage(convId, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: err instanceof Error
          ? err.message
          : 'Could not reach the backend. Make sure your SSH tunnel is active and the server is running.',
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

  const handleNewConversation = async () => {
    const c = await createConversation(activeTeamId)
    setConvByTeam(prev => ({ ...prev, [activeTeamId]: [c, ...(prev[activeTeamId] || [])] }))
    setActiveConvByTeam(prev => ({ ...prev, [activeTeamId]: c.id }))
    setMessagesByConv(prev => ({ ...prev, [c.id]: [] }))
  }

  const handleSelectConversation = (id: string) => {
    setActiveConvByTeam(prev => ({ ...prev, [activeTeamId]: id }))
  }

  const handleDeleteConversation = async (id: string) => {
    await deleteConversation(id)
    const remaining = (convByTeam[activeTeamId] || []).filter(c => c.id !== id)
    setConvByTeam(prev => ({ ...prev, [activeTeamId]: remaining }))
    setActiveConvByTeam(prev =>
      prev[activeTeamId] === id ? { ...prev, [activeTeamId]: remaining[0]?.id ?? null } : prev
    )
  }

  const activeAgents = isThinking
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
        <ConversationList
          teamName={activeTeam.name}
          conversations={conversations}
          activeId={activeConvId}
          onSelect={handleSelectConversation}
          onNew={handleNewConversation}
          onDelete={handleDeleteConversation}
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
