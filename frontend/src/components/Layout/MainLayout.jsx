import { useState } from 'react'
import Header from './Header'
import Sidebar from '../Sidebar/Sidebar'

export default function MainLayout({ children }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen flex-col bg-[var(--color-canvas)]">
      <Header onToggleSidebar={() => setIsSidebarOpen((v) => !v)} />

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar — always visible, fixed width */}
        <div className="hidden lg:block lg:w-72 shrink-0">
          <Sidebar />
        </div>

        {/* Mobile sidebar — slide-over drawer */}
        {isSidebarOpen && (
          <div className="fixed inset-0 z-40 flex lg:hidden">
            <div
              className="absolute inset-0 bg-black/40 animate-fade-in"
              onClick={() => setIsSidebarOpen(false)}
              role="presentation"
            />
            <div className="relative z-10 w-72 max-w-[85vw] animate-fade-in">
              <Sidebar />
            </div>
          </div>
        )}

        <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
      </div>
    </div>
  )
}
