import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import KanbanBoard from './pages/KanbanBoard';
import ReportCapture from './pages/ReportCapture';
import TemplateSelector from './pages/TemplateSelector';
import AdminUsers from './pages/AdminUsers';
import AdminTemplates from './pages/AdminTemplates';
import AdminLogs from './pages/AdminLogs';
import Login from './pages/Login';
import SecuritySettings from './pages/SecuritySettings';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<KanbanBoard />} />
          <Route path="/capture" element={<TemplateSelector />} />
          <Route path="/capture/:id" element={<ReportCapture />} />
          <Route path="/settings" element={<SecuritySettings />} />
          <Route path="/admin/users" element={<AdminUsers />} />
          <Route path="/admin/templates" element={<AdminTemplates />} />
          <Route path="/admin/logs" element={<AdminLogs />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
