import { useState, useEffect } from 'react';
import { apiFetch } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { UserPlus, Shield, Power, PowerOff } from 'lucide-react';

interface UserData {
  id: number;
  email: string;
  nombre_completo: string;
  role: string;
  org_nombre: string;
  customer_nombre?: string;
  is_active: boolean;
}

export default function TeamManagement() {
  const { user } = useAuth();
  const [users, setUsers] = useState<UserData[]>([]);
  const [organizations, setOrganizations] = useState<{id: number, nombre: string}[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    nombre_completo: '',
    role: 'tecnico',
    org_id: '',
    customer_id: ''
  });
  const [customers, setCustomers] = useState<{id: number, nombre_empresa: string}[]>([]);

  const fetchUsersAndOrgs = async () => {
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/users`);
      const data = await res.json();
      setUsers(data.users || []);
      
      if (user?.role === 'admin') {
        const orgsRes = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/organizations`);
        const orgsData = await orgsRes.json();
        setOrganizations(orgsData.organizations || []);
        if (orgsData.organizations?.length > 0) {
          setFormData(prev => ({...prev, org_id: orgsData.organizations[0].id.toString()}));
        }
      }
      
      const custRes = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/customers`);
      const custData = await custRes.json();
      setCustomers(custData.customers || []);
    } catch (error) {
      console.error('Failed to fetch data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsersAndOrgs();
  }, [user]);

  const handleToggleActive = async (userId: number) => {
    try {
      await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/users/${userId}/toggle`, { method: 'POST' });
      fetchUsersAndOrgs();
    } catch (error) {
      alert('Error cambiando estado del usuario');
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          org_id: formData.org_id ? parseInt(formData.org_id) : undefined
        })
      });
      const data = await res.json();
      if (data.error) {
          throw new Error(data.error);
      }
      setShowModal(false);
      setFormData({ email: '', password: '', nombre_completo: '', role: 'tecnico', org_id: organizations[0]?.id.toString() || '', customer_id: '' });
      fetchUsersAndOrgs();
    } catch (error: any) {
      alert(error.message || 'Error al crear usuario');
    }
  };

  if (loading) return <div className="p-8 text-center">Cargando equipo...</div>;

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Gestión de Equipo</h2>
          <p className="text-gray-500 mt-1">Administra los accesos de tu organización</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 bg-corporate-blue text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
        >
          <UserPlus size={18} />
          <span>Nuevo Usuario</span>
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200 text-sm text-gray-500">
                <th className="p-4 font-medium">Nombre</th>
                <th className="p-4 font-medium">Email</th>
                <th className="p-4 font-medium">Rol</th>
                <th className="p-4 font-medium">Organización</th>
                <th className="p-4 font-medium">Estado</th>
                <th className="p-4 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => (
                <tr key={u.id} className={`hover:bg-gray-50 transition-colors ${!u.is_active ? 'opacity-50' : ''}`}>
                  <td className="p-4">
                    <div className="font-medium text-gray-900">{u.nombre_completo || 'Sin nombre'}</div>
                  </td>
                  <td className="p-4 text-sm text-gray-600">{u.email}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                      ${u.role === 'admin' ? 'bg-purple-100 text-purple-800' : 
                        u.role === 'supervisor' ? 'bg-blue-100 text-blue-800' : 
                        'bg-green-100 text-green-800'}`}>
                      {u.role === 'admin' && <Shield size={12} className="mr-1" />}
                      {u.role}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-600">
                    <div>{u.org_nombre}</div>
                    {u.role === 'cliente' && u.customer_nombre && (
                      <div className="text-xs text-purple-600 mt-0.5">{u.customer_nombre}</div>
                    )}
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${u.is_active ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'}`}>
                      {u.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    {u.id !== user?.id && (
                      <button
                        onClick={() => handleToggleActive(u.id)}
                        className={`p-2 rounded-lg transition-colors ${u.is_active ? 'text-red-600 hover:bg-red-50' : 'text-green-600 hover:bg-green-50'}`}
                        title={u.is_active ? 'Desactivar acceso' : 'Activar acceso'}
                      >
                        {u.is_active ? <PowerOff size={18} /> : <Power size={18} />}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-gray-500">
                    No hay usuarios registrados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Invitar Nuevo Usuario</h3>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Completo</label>
                <input
                  type="text"
                  required
                  value={formData.nombre_completo}
                  onChange={(e) => setFormData({...formData, nombre_completo: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Correo Electrónico</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña Inicial</label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                >
                  <option value="tecnico">Técnico (Levanta reportes)</option>
                  <option value="supervisor">Supervisor (Revisa/Aprueba)</option>
                  <option value="cliente">Cliente (Portal)</option>
                  {user?.role === 'admin' && <option value="admin">Administrador</option>}
                </select>
              </div>
              
              {formData.role === 'cliente' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Empresa del Cliente</label>
                  <select
                    required
                    value={formData.customer_id}
                    onChange={(e) => setFormData({...formData, customer_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                  >
                    <option value="">Selecciona una empresa...</option>
                    {customers.map(cust => (
                      <option key={cust.id} value={cust.id}>{cust.nombre_empresa}</option>
                    ))}
                  </select>
                </div>
              )}

              {user?.role === 'admin' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Organización</label>
                  <select
                    value={formData.org_id}
                    onChange={(e) => setFormData({...formData, org_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none"
                  >
                    {organizations.map(org => (
                      <option key={org.id} value={org.id}>{org.nombre}</option>
                    ))}
                  </select>
                </div>
              )}
              <div className="pt-4 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-corporate-blue text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                >
                  Crear Usuario
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
