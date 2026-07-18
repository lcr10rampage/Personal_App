const API_URL = 'http://localhost:8000'
// Teams like Project & Hobby chain several model calls, so allow a generous window
// before giving up — but never wait forever.
const TIMEOUT_MS = 180_000

export async function sendMessage(message: string, team: string = 'life_manager'): Promise<string> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const res = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, team }),
      signal: controller.signal,
    })

    if (!res.ok) {
      throw new Error(`The backend returned an error (${res.status}). Check the server logs.`)
    }

    const data = await res.json()
    return data.response
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
