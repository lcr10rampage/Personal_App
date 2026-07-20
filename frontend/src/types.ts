export interface Team {
  id: string
  name: string
  description: string
  icon: string
  available: boolean
  agents: Agent[]
}

export interface Agent {
  id: string
  name: string
  status: 'ready' | 'thinking' | 'offline'
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface Conversation {
  id: string
  title: string
  updated: number
  message_count?: number
}
