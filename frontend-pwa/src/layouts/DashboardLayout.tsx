import { Outlet, Link, useLocation, Navigate } from 'react-router-dom';
import { LayoutDashboard, Camera, LogOut, Users, FileText, Activity } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function DashboardLayout() {
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8001/auth/api/session', { credentials: 'include' })
      .then(res => {
        if (res.ok) {
          setIsAuthenticated(true);
          return res.json();
        } else {
          setIsAuthenticated(false);
          return null;
        }
      })
      .then(data => {
        if (data && data.user && data.user.is_admin) setIsAdmin(true);
      })
      .catch(() => setIsAuthenticated(false));
  }, []);

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8001/auth/api/logout', { method: 'POST', credentials: 'include' });
      window.location.href = '/login';
    } catch (e) {
      window.location.href = '/login';
    }
  };

  if (isAuthenticated === null) {
    return <div className="min-h-screen bg-corporate-light flex items-center justify-center">Verificando seguridad...</div>;
  }

  if (isAuthenticated === false) {
    return <Navigate to="/login" replace />;
  }


  return (
    <div className="min-h-screen bg-corporate-light flex flex-col md:flex-row">
      {/* Sidebar para Escritorio */}
      <aside className="hidden md:flex flex-col w-64 bg-white border-r border-gray-200 h-screen sticky top-0 shadow-sm">
        <div className="p-6">
          <h1 className="text-xl font-bold text-corporate-dark">Inova Admin</h1>
        </div>
        <nav className="flex-1 px-4 space-y-2">
          <Link 
            to="/" 
            className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${location.pathname === '/' ? 'bg-corporate-blue text-white' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <LayoutDashboard size={20} />
            <span className="font-medium">Tablero</span>
          </Link>
          <Link 
            to="/capture" 
            className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${location.pathname === '/capture' ? 'bg-corporate-blue text-white' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <Camera size={20} />
            <span className="font-medium">Nueva Captura</span>
          </Link>
          
          {isAdmin && (
            <>
              <div className="pt-4 pb-1">
                <p className="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Admin</p>
              </div>
              <Link 
                to="/admin/users" 
                className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-colors ${location.pathname.startsWith('/admin/users') ? 'bg-purple-50 text-purple-700' : 'text-gray-600 hover:bg-gray-50'}`}
              >
                <Users size={18} />
                <span className="font-medium text-sm">Usuarios</span>
              </Link>
              <Link 
                to="/admin/templates" 
                className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-colors ${location.pathname.startsWith('/admin/templates') ? 'bg-purple-50 text-purple-700' : 'text-gray-600 hover:bg-gray-50'}`}
              >
                <FileText size={18} />
                <span className="font-medium text-sm">Plantillas</span>
              </Link>
              <Link 
                to="/admin/logs" 
                className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-colors ${location.pathname.startsWith('/admin/logs') ? 'bg-purple-50 text-purple-700' : 'text-gray-600 hover:bg-gray-50'}`}
              >
                <Activity size={18} />
                <span className="font-medium text-sm">Bitácora</span>
              </Link>
            </>
          )}
        </nav>
        <div className="p-4 border-t border-gray-200">
          <button onClick={handleLogout} className="flex items-center space-x-3 px-4 py-3 w-full rounded-lg transition-colors text-red-600 hover:bg-red-50">
            <LogOut size={20} />
            <span className="font-medium">Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      {/* Contenido Principal */}
      <main className="flex-1 flex flex-col min-h-screen">
        <header className="md:hidden bg-white shadow-sm px-4 py-4 sticky top-0 z-10 flex items-center justify-between">
          <h1 className="text-lg font-bold text-corporate-dark">Inova Admin</h1>
        </header>
        <div className="flex-1 p-4 md:p-8">
          <Outlet />
        </div>
        
        {/* Navegación Inferior para Móvil */}
        <nav className="md:hidden fixed bottom-0 w-full bg-white border-t border-gray-200 flex justify-around p-3 pb-safe z-10">
          <Link to="/" className={`flex flex-col items-center p-2 ${location.pathname === '/' ? 'text-corporate-blue' : 'text-gray-500'}`}>
            <LayoutDashboard size={24} />
            <span className="text-xs mt-1 font-medium">Tablero</span>
          </Link>
          <Link to="/capture" className={`flex flex-col items-center p-2 ${location.pathname === '/capture' ? 'text-corporate-blue' : 'text-gray-500'}`}>
            <Camera size={24} />
            <span className="text-xs mt-1 font-medium">Captura</span>
          </Link>
          {isAdmin && (
            <Link to="/admin/logs" className={`flex flex-col items-center p-2 ${location.pathname.startsWith('/admin') ? 'text-purple-600' : 'text-gray-500'}`}>
              <Activity size={24} />
              <span className="text-xs mt-1 font-medium">Admin</span>
            </Link>
          )}
        </nav>
      </main>
    </div>
  );
}
