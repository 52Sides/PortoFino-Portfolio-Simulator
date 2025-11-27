import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './Layout'
import App from './App'
import HistoryPage from './pages/HistoryPage'
import OAuthCallback from './components/OAuthCallback'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<App />} />
          <Route path="/history" element={<HistoryPage />} />
        </Route>
        <Route path="/oauth-callback" element={<OAuthCallback />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
)
