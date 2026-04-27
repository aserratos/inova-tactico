import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { SignedIn, SignedOut, RedirectToSignIn } from '@clerk/clerk-react';
import DashboardLayout from './layouts/DashboardLayout';
import KanbanBoard from './pages/KanbanBoard';
import ReportCapture from './pages/ReportCapture';
import TemplateSelector from './pages/TemplateSelector';
import TeamManagement from './pages/TeamManagement';
import AdminTemplates from './pages/AdminTemplates';
import AdminLogs from './pages/AdminLogs';
import Login from './pages/Login';
import SecuritySettings from './pages/SecuritySettings';

function App() {
  return (
    <Router>
      <Routes>
        {/* Ruta de Login (solo si estás deslogueado) */}
        <Route 
          path="/login" 
          element={
            <>
              <SignedIn>
                <Navigate to="/" replace />
              </SignedIn>
              <SignedOut>
                <Login />
              </SignedOut>
            </>
          } 
        />

        {/* Rutas Protegidas (Requieren estar logueado, sino te manda al login) */}
        <Route 
          element={
            <>
              <SignedIn>
                <DashboardLayout />
              </SignedIn>
              <SignedOut>
                <RedirectToSignIn />
              </SignedOut>
            </>
          }
        >
          <Route path="/" element={<KanbanBoard />} />
          <Route path="/capture" element={<TemplateSelector />} />
          <Route path="/capture/:id" element={<ReportCapture />} />
          <Route path="/settings" element={<SecuritySettings />} />
          <Route path="/team" element={<TeamManagement />} />
          <Route path="/admin/templates" element={<AdminTemplates />} />
          <Route path="/admin/logs" element={<AdminLogs />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
