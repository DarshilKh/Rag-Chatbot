import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import { ThemeProvider } from './context/ThemeContext'
import { ToastProvider } from './context/ToastContext'
import { DocumentProvider } from './context/DocumentContext'
import { ChatProvider } from './context/ChatContext'

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <DocumentProvider>
          <ChatProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<Dashboard />} />
              </Routes>
            </BrowserRouter>
          </ChatProvider>
        </DocumentProvider>
      </ToastProvider>
    </ThemeProvider>
  )
}
