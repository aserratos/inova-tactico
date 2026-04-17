import { useState, useEffect } from 'react';
import { Users, UserPlus, Trash2, KeyRound } from 'lucide-react';

interface UserData {
  id: number;
  email: string;
  nombre_completo: string;
  puesto: string;
  role: string;
  is_active: boolean;
  telefono: string;
}

export default function AdminUsers() {
  const [users, setUsers] = useState<UserData[]>([]);
  const [loading, setLoading] = useState(true);

  // Form states
  const [email, setEmail] = useState('');
  const [nombre, setNombre] = useState('');
  const [puesto, setPuesto] = useState('');
  const [telefono, setTelefono] = useState('');
  const [role, setRole] = useState('tecnico');

  const fetchUsers = async () => {
    try {
      const res = await fetch('http://localhost:8001/auth/api/admin/users', { credentials: 'include' });
      const data = await res.json();
      if (res.ok) setUsers(data.users || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('http://localhost:8001/auth/api/admin/users/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, nombre_completo: nombre, puesto, telefono, role })
      });
      const data = await res.json();
      if (res.ok) {
        alert("Usuario creado exitosamente. Token de invitación generado.");
        setEmail(''); setNombre(''); setPuesto(''); setTelefono('');
        fetchUsers();
      } else {
        alert(data.error || "Error al crear usuario");
      }
    } catch (e) {
      alert("Error de red");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de eliminar este usuario?')) return;
    try {
      const res = await fetch(`http://localhost:8001/auth/api/admin/users/delete/${id}`, {
        method: 'POST',
        credentials: 'include'
      });
      if (res.ok) fetchUsers();
      else alert("Error al eliminar");
    } catch (e) {
      alert("Error de red");
    }
  };

  const handleReset = async (id: number) => {
    const newPass = prompt("Ingresa la nueva contraseña (min 8 caracteres):");
    if (!newPass) return;
    try {
      const res = await fetch(`http://localhost:8001/auth/api/admin/users/reset/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ new_password: newPass })
      });
      const data = await res.json();
      if (res.ok) alert("Contraseña actualizada con éxito");
      else alert(data.error || "Error al actualizar");
    } catch (e) {
      alert("Error de red");
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Cargando usuarios...</div>;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Users className="mr-3 text-corporate-blue" />
            Gestión de Personal
          </h2>
          <p className="text-gray-500 mt-1">Administra los accesos y credenciales de tu equipo</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* CREATE FORM */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center">
            <UserPlus className="mr-2 text-corporate-blue" size={20} />
            Nuevo Usuario
          </h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 uppercase mb-1">Nombre Completo</label>
              <input type="text" required value={nombre} onChange={e => setNombre(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-corporate-blue outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 uppercase mb-1">Correo Electrónico</label>
              <input type="email" required value={email} onChange={e => setEmail(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-corporate-blue outline-none" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-600 uppercase mb-1">Puesto</label>
                <input type="text" value={puesto} onChange={e => setPuesto(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-corporate-blue outline-none" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 uppercase mb-1">Teléfono</label>
                <input type="text" value={telefono} onChange={e => setTelefono(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-corporate-blue outline-none" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 uppercase mb-1">Rol</label>
              <select value={role} onChange={e => setRole(e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-corporate-blue outline-none bg-white">
                <option value="tecnico">Técnico de Campo</option>
                <option value="supervisor">Supervisor</option>
                <option value="admin">Administrador</option>
              </select>
            </div>
            <button type="submit" className="w-full py-2.5 bg-corporate-blue text-white rounded-lg font-bold hover:bg-blue-700 transition-colors mt-2">
              Registrar Personal
            </button>
          </form>
        </div>

        {/* USERS LIST */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold">
                  <th className="px-6 py-4">Usuario</th>
                  <th className="px-6 py-4">Rol</th>
                  <th className="px-6 py-4">Estado</th>
                  <th className="px-6 py-4 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map(u => (
                  <tr key={u.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-gray-900">{u.nombre_completo || u.email}</div>
                      <div className="text-xs text-gray-500">{u.email} • {u.puesto}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        u.role === 'admin' ? 'bg-purple-100 text-purple-700' :
                        u.role === 'supervisor' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {u.role.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`flex items-center text-xs font-medium ${u.is_active ? 'text-green-600' : 'text-red-500'}`}>
                        <span className={`w-2 h-2 rounded-full mr-2 ${u.is_active ? 'bg-green-500' : 'bg-red-500'}`}></span>
                        {u.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button onClick={() => handleReset(u.id)} className="p-2 text-gray-400 hover:text-corporate-blue hover:bg-blue-50 rounded-lg transition-colors" title="Cambiar Contraseña">
                        <KeyRound size={18} />
                      </button>
                      <button onClick={() => handleDelete(u.id)} className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors" title="Eliminar Usuario">
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users.length === 0 && <div className="p-8 text-center text-gray-500">No hay usuarios registrados.</div>}
          </div>
        </div>

      </div>
    </div>
  );
}
