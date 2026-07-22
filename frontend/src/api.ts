import { Conversation, Message } from './types'

const API_URL = 'http://localhost:8000'
// Teams like Project & Hobby chain several model calls, so allow a generous window
// before giving up — but never wait forever.
const TIMEOUT_MS = 180_000

export interface ChatResult {
  response: string
  conversationId: string
  title: string
}

export async function sendMessage(
  message: string,
  team: string = 'life_manager',
  conversationId?: string,
): Promise<ChatResult> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const res = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, team, conversation_id: conversationId }),
      signal: controller.signal,
    })

    if (!res.ok) {
      throw new Error(`The backend returned an error (${res.status}). Check the server logs.`)
    }

    const data = await res.json()
    return { response: data.response, conversationId: data.conversation_id, title: data.title }
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error(
        'The team took too long to respond (over 3 minutes) and the request timed out. ' +
        'It may still be finishing in the background — try again, or ask a smaller question.'
      )
    }
    if (err instanceof TypeError) {
      throw new Error(
        'Could not reach the backend. Make sure your SSH tunnel is active and the server is running.'
      )
    }
    throw err
  } finally {
    clearTimeout(timer)
  }
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`)
    return res.ok
  } catch {
    return false
  }
}

export async function listConversations(team: string): Promise<Conversation[]> {
  const res = await fetch(`${API_URL}/conversations?team=${encodeURIComponent(team)}`)
  if (!res.ok) return []
  const data = await res.json()
  return data.conversations ?? []
}

export async function createConversation(team: string): Promise<Conversation> {
  const res = await fetch(`${API_URL}/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ team }),
  })
  if (!res.ok) throw new Error(`Could not create conversation (${res.status}).`)
  return res.json()
}

export async function getConversationMessages(id: string): Promise<Message[]> {
  const res = await fetch(`${API_URL}/conversations/${id}`)
  if (!res.ok) return []
  const data = await res.json()
  return (data.messages ?? []).map((m: any, i: number) => ({
    id: `${id}-${i}`,
    role: m.role,
    content: m.content,
    timestamp: m.ts ? new Date(m.ts * 1000) : new Date(),
  }))
}

export async function deleteConversation(id: string): Promise<void> {
  await fetch(`${API_URL}/conversations/${id}`, { method: 'DELETE' })
}
