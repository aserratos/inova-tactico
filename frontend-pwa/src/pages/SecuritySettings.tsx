import { useState } from 'react';
import { apiFetch } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { User, Lock, Save, CheckCircle2, AlertCircle, Eye, EyeOff, ShieldCheck } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8001';

type MsgState = { type: 'success' | 'error'; text: string } | null;

export default function SecuritySettings() {
  const { user, setUser } = useAuth();

  // --- Perfil ---
  const [profile, setProfile] = useState({
    nombre_completo: user?.nombre_completo || '',
    puesto: user?.puesto || '',
    telefono: user?.telefono || '',
  });
  const [profileMsg, setProfileMsg] = useState<MsgState>(null);
  const [savingProfile, setSavingProfile] = useState(false);

  // --- Contraseña ---
  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPwd, setShowPwd] = useState(false);
  const [pwdMsg, setPwdMsg] = useState<MsgState>(null);
  const [savingPwd, setSavingPwd] = useState(false);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileMsg(null);
    try {
      const res = await apiFetch(`${API}/api/auth/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setProfileMsg({ type: 'success', text: 'Perfil actualizado correctamente.' });
        if (data.user) setUser(data.user);
      } else {
        setProfileMsg({ type: 'error', text: `[HTTP ${res.status}] ${data.error || 'Error al guardar el perfil.'}` });
      }
    } catch (e: any) {
      setProfileMsg({ type: 'error', text: `Error de red: ${e.message}` });
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdMsg(null);
    if (passwords.new_password !== passwords.confirm_password) {
      setPwdMsg({ type: 'error', text: 'Las contraseñas nuevas no coinciden.' });
      return;
    }
    if (passwords.new_password.length < 8) {
      setPwdMsg({ type: 'error', text: 'La nueva contraseña debe tener al menos 8 caracteres.' });
      return;
    }
    setSavingPwd(true);
    try {
      const res = await apiFetch(`${API}/api/auth/change-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: passwords.current_password,
          new_password: passwords.new_password,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setPwdMsg({ type: 'success', text: 'Contraseña actualizada correctamente.' });
        setPasswords({ current_password: '', new_password: '', confirm_password: '' });
      } else {
        setPwdMsg({ type: 'error', text: `[HTTP ${res.status}] ${data.error || 'Error al cambiar contraseña.'}` });
      }
    } catch (e: any) {
      setPwdMsg({ type: 'error', text: `Error de red: ${e.message}` });
    } finally {
      setSavingPwd(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">

      {/* Header */}
      <div className="flex items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div className="w-12 h-12 rounded-xl bg-corporate-blue/10 flex items-center justify-center text-corporate-blue">
          <ShieldCheck size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ajustes de cuenta</h1>
          <p className="text-sm text-gray-500 mt-0.5">{user?.email}</p>
        </div>
      </div>

      {/* ── Perfil ── */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
          <User size={18} className="text-corporate-blue" />
          <h2 className="font-semibold text-gray-800">Información personal</h2>
        </div>

        {profileMsg && (
          <div className={`mx-6 mt-4 flex items-start gap-2 p-3 rounded-xl text-sm border ${
            profileMsg.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}>
            {profileMsg.type === 'success'
              ? <CheckCircle2 size={16} className="flex-shrink-0 mt-0.5" />
              : <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />}
            <span>{profileMsg.text}</span>
          </div>
        )}

        <form onSubmit={handleSaveProfile} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo</label>
            <input
              type="text"
              value={profile.nombre_completo}
              onChange={e => setProfile({ ...profile, nombre_completo: e.target.value })}
              className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none text-sm"
              placeholder="Ej. Juan Pérez García"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Puesto</label>
              <input
                type="text"
                value={profile.puesto}
                onChange={e => setProfile({ ...profile, puesto: e.target.value })}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none text-sm"
                placeholder="Ej. Técnico de Campo"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
              <input
                type="tel"
                value={profile.telefono}
                onChange={e => setProfile({ ...profile, telefono: e.target.value })}
                className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none text-sm"
                placeholder="+52 33 1234 5678"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={savingProfile}
              className="flex items-center gap-2 bg-corporate-blue text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 shadow-sm"
            >
              {savingProfile
                ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                : <Save size={16} />}
              {savingProfile ? 'Guardando...' : 'Guardar perfil'}
            </button>
          </div>
        </form>
      </div>

      {/* ── Contraseña ── */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
          <Lock size={18} className="text-corporate-blue" />
          <h2 className="font-semibold text-gray-800">Cambiar contraseña</h2>
        </div>

        {pwdMsg && (
          <div className={`mx-6 mt-4 flex items-start gap-2 p-3 rounded-xl text-sm border ${
            pwdMsg.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}>
            {pwdMsg.type === 'success'
              ? <CheckCircle2 size={16} className="flex-shrink-0 mt-0.5" />
              : <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />}
            <span>{pwdMsg.text}</span>
          </div>
        )}

        <form onSubmit={handleChangePassword} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña actual</label>
            <div className="relative">
              <input
                type={showPwd ? 'text' : 'password'}
                required
                value={passwords.current_password}
                onChange={e => setPasswords({ ...passwords, current_password: e.target.value })}
                className="w-full p-2.5 pr-10 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none text-sm"
                placeholder="Tu contraseña actual"
              />
              <button
                type="button"
                onClick={() => setShowPwd(p => !p)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nueva contraseña</label>
            <input
              type={showPwd ? 'text' : 'password'}
              required
              minLength={8}
              value={passwords.new_password}
              onChange={e => setPasswords({ ...passwords, new_password: e.target.value })}
              className="w-full p-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-corporate-blue outline-none text-sm"
              placeholder="Mínimo 8 caracteres"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirmar nueva contraseña</label>
            <input
              type={showPwd ? 'text' : 'password'}
              required
              value={passwords.confirm_password}
              onChange={e => setPasswords({ ...passwords, confirm_password: e.target.value })}
              className={`w-full p-2.5 rounded-xl border outline-none text-sm focus:ring-2 focus:ring-corporate-blue ${
                passwords.confirm_password && passwords.confirm_password !== passwords.new_password
                  ? 'border-red-300 focus:border-red-400'
                  : 'border-gray-300 focus:border-corporate-blue'
              }`}
              placeholder="Repite la nueva contraseña"
            />
            {passwords.confirm_password && passwords.confirm_password !== passwords.new_password && (
              <p className="text-xs text-red-500 mt-1">Las contraseñas no coinciden</p>
            )}
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={savingPwd}
              className="flex items-center gap-2 bg-corporate-blue text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 shadow-sm"
            >
              {savingPwd
                ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                : <Lock size={16} />}
              {savingPwd ? 'Cambiando...' : 'Cambiar contraseña'}
            </button>
          </div>
        </form>
      </div>

      {/* Info de rol */}
      <div className="bg-gray-50 border border-gray-100 rounded-2xl p-5 flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-gray-200 flex items-center justify-center text-gray-500 flex-shrink-0">
          <User size={20} />
        </div>
        <div className="text-sm">
          <p className="font-semibold text-gray-700">Rol asignado: <span className="capitalize">{user?.role || 'N/A'}</span></p>
          <p className="text-gray-500">Para cambiar tu rol contacta al administrador de tu organización.</p>
        </div>
      </div>
    </div>
  );
}
