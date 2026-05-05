import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import KanbanBoard from './pages/KanbanBoard';
import ReportCapture from './pages/ReportCapture';
import TemplateSelector from './pages/TemplateSelector';
import TeamManagement from './pages/TeamManagement';
import AdminTemplates from './pages/AdminTemplates';
import AdminLogs from './pages/AdminLogs';
import Login from './pages/Login';
import SecuritySettings from './pages/SecuritySettings';
import ClientPortal from './pages/ClientPortal';
import CustomerManagement from './pages/CustomerManagement';

const HomeRouter = () => {
  const { user } = useAuth();
  if (user?.role === 'cliente') {
    return <ClientPortal />;
  }
  return <KanbanBoard />;
};

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <div className="h-screen flex items-center justify-center">Cargando...</div>;
  if (!user) return <Navigate to="/login" replace />;
  
  return <>{children}</>;
};

const PublicOnlyRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <div className="h-screen flex items-center justify-center">Cargando...</div>;
  if (user) return <Navigate to="/" replace />;
  
  return <>{children}</>;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            <PublicOnlyRoute>
              <Login />
            </PublicOnlyRoute>
          } 
        />

        <Route 
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<HomeRouter />} />
          <Route path="/capture" element={<TemplateSelector />} />
          <Route path="/capture/:id" element={<ReportCapture />} />
          <Route path="/settings" element={<SecuritySettings />} />
          <Route path="/team" element={<TeamManagement />} />
          <Route path="/admin/templates" element={<AdminTemplates />} />
          <Route path="/admin/logs" element={<AdminLogs />} />
          <Route path="/admin/customers" element={<CustomerManagement />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
