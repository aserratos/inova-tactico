import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Camera, Users, FileText, Activity, ShieldCheck, LogOut, Building2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { SyncEngine } from '../components/SyncEngine';

export default function DashboardLayout() {
  const location = useLocation();
  const { user, logout } = useAuth();

  const isAdmin = user?.role === 'admin' || user?.role === 'supervisor';
  const canManageTemplates = isAdmin; // Simplified logic, can be expanded later

  return (
    <div className="min-h-screen bg-corporate-light flex flex-col md:flex-row">
      <SyncEngine />
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
            <span className="font-medium">{user?.role === 'cliente' ? 'Portal' : 'Tablero'}</span>
          </Link>
          
          {user?.role !== 'cliente' && (
            <Link 
              to="/capture" 
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${location.pathname === '/capture' ? 'bg-corporate-blue text-white' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              <Camera size={20} />
              <span className="font-medium">Nueva Captura</span>
            </Link>
          )}

          {user?.role !== 'cliente' && (
            <Link 
              to="/settings" 
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${location.pathname === '/settings' ? 'bg-corporate-blue text-white' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              <ShieldCheck size={20} />
              <span className="font-medium">Ajustes</span>
            </Link>
          )}
          
          {/* Seccion Admin */}
          {isAdmin && (
            <>
              <div className="pt-4 pb-1">
                <p className="px-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Admin</p>
              </div>
              {canManageTemplates && (
                <Link 
                  to="/admin/templates" 
                  className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-colors ${location.pathname.startsWith('/admin/templates') ? 'bg-purple-50 text-purple-700' : 'text-gray-600 hover:bg-gray-50'}`}
                >
                  <FileText size={18} />
                  <span className="font-medium text-sm">Plantillas</span>
                </Link>
              )}
              <Link 
                to="/admin/customers" 
                className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-colors ${location.pathname.startsWith('/admin/customers') ? 'bg-purple-50 text-purple-700' : 'text-gray-600 hover:bg-gray-50'}`}
              >
                <Building2 size={18} />
                <span className="font-medium text-sm">Clientes (Empresas)</span>
              </Link>
              <Link 
                to="/team" 
                className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-colors ${location.pathname.startsWith('/team') ? 'bg-purple-50 text-purple-700' : 'text-gray-600 hover:bg-gray-50'}`}
              >
                <Users size={18} />
                <span className="font-medium text-sm">Mi Equipo</span>
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
        <div className="p-4 border-t border-gray-200 flex flex-col space-y-3">
          <div className="flex items-center justify-between w-full">
            <div className="flex flex-col text-sm w-[150px]">
              <span className="font-medium text-gray-900 truncate">{user?.nombre_completo || 'Usuario'}</span>
              <span className="text-gray-500 text-xs truncate">{user?.email}</span>
            </div>
            <button 
              onClick={logout} 
              className="p-2 text-gray-500 hover:text-red-500 transition-colors"
              title="Cerrar sesión"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>

      {/* Contenido Principal */}
      <main className="flex-1 flex flex-col min-h-screen pb-16 md:pb-0">
        <header className="md:hidden bg-white shadow-sm px-4 py-4 sticky top-0 z-10 flex items-center justify-between">
          <h1 className="text-lg font-bold text-corporate-dark">Inova Admin</h1>
          <button 
            onClick={logout} 
            className="p-2 text-gray-500 hover:text-red-500 transition-colors"
          >
            <LogOut size={20} />
          </button>
        </header>
        <div className="flex-1 p-4 md:p-8">
          <Outlet />
        </div>
        
        {/* Navegación Inferior para Móvil */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around p-3 pb-safe z-10">
          <Link to="/" className={`flex flex-col items-center p-2 ${location.pathname === '/' ? 'text-corporate-blue' : 'text-gray-500'}`}>
            <LayoutDashboard size={24} />
            <span className="text-xs mt-1 font-medium">{user?.role === 'cliente' ? 'Portal' : 'Tablero'}</span>
          </Link>
          {user?.role !== 'cliente' && (
            <Link to="/capture" className={`flex flex-col items-center p-2 ${location.pathname === '/capture' ? 'text-corporate-blue' : 'text-gray-500'}`}>
              <Camera size={24} />
              <span className="text-xs mt-1 font-medium">Captura</span>
            </Link>
          )}
          {user?.role !== 'cliente' && (
            <Link to="/settings" className={`flex flex-col items-center p-2 ${location.pathname === '/settings' ? 'text-corporate-blue' : 'text-gray-500'}`}>
              <ShieldCheck size={24} />
              <span className="text-xs mt-1 font-medium">Ajustes</span>
            </Link>
          )}
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
