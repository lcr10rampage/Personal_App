declare global {
  interface Window {
    electron?: {
      minimize: () => void
      maximize: () => void
      close: () => void
    }
  }
}

export default function TitleBar() {
  return (
    <div className="drag-region flex items-center justify-between h-9 px-4 bg-ws-sidebar border-b border-ws-border flex-shrink-0">
      <span className="text-ws-text-muted text-xs select-none">Personal AI Workspace</span>
      <div className="no-drag flex items-center gap-1.5">
        <button
          onClick={() => window.electron?.minimize()}
          className="w-3.5 h-3.5 rounded-full bg-ws-border hover:bg-yellow-500 transition-colors duration-150"
        />
        <button
          onClick={() => window.electron?.maximize()}
          className="w-3.5 h-3.5 rounded-full bg-ws-border hover:bg-green-500 transition-colors duration-150"
        />
        <button
          onClick={() => window.electron?.close()}
          className="w-3.5 h-3.5 rounded-full bg-ws-border hover:bg-red-500 transition-colors duration-150"
        />
      </div>
    </div>
  )
}
