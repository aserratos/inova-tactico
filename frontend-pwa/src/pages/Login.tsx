import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { apiFetch } from "../lib/api";
import { Mail, Lock, ArrowRight, ShieldCheck } from "lucide-react";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (res.ok && data.token) {
        login(data.token, data.user);
      } else {
        setError(data.error || "Credenciales inválidas");
      }
    } catch (err) {
      setError("Error de red. Revisa tu conexión.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex font-sans">
      {/* Left side: Login Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-6 sm:px-16 xl:px-24 bg-white relative z-10">
        <div className="max-w-md w-full mx-auto">
          {/* Logo / Brand */}
          <div className="mb-12 flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-corporate-blue to-blue-800 rounded-xl flex items-center justify-center text-white font-bold text-2xl shadow-lg shadow-blue-500/30">
              O
            </div>
            <span className="text-3xl font-black text-gray-900 tracking-tight">OmniFlow</span>
          </div>

          <h2 className="text-3xl font-extrabold text-gray-900 mb-2">Bienvenido de nuevo</h2>
          <p className="text-gray-500 mb-8">Ingresa tus credenciales para acceder a tu plataforma operativa.</p>

          {error && (
            <div className="bg-red-50/80 backdrop-blur-sm text-red-600 p-4 rounded-xl mb-6 text-sm font-medium border border-red-100 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Correo Electrónico
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="email"
                  required
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 pl-11 pr-4 py-3 focus:ring-2 focus:ring-corporate-blue focus:bg-white focus:border-transparent outline-none transition-all"
                  placeholder="tu@correo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="password"
                  required
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 pl-11 pr-4 py-3 focus:ring-2 focus:ring-corporate-blue focus:bg-white focus:border-transparent outline-none transition-all"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center justify-between pb-2">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-corporate-blue focus:ring-corporate-blue border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-600">
                  Recordarme
                </label>
              </div>
              <div className="text-sm">
                <a href="#" className="font-medium text-corporate-blue hover:text-blue-500">
                  ¿Olvidaste tu contraseña?
                </a>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-corporate-blue hover:bg-blue-700 text-white font-semibold rounded-xl py-3.5 flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-500/25 disabled:opacity-70 disabled:cursor-not-allowed group"
            >
              {loading ? (
                "Autenticando..."
              ) : (
                <>
                  Ingresar a la Plataforma
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <div className="mt-10 pt-6 border-t border-gray-100 flex items-center justify-center gap-2 text-sm text-gray-500">
            <ShieldCheck className="w-4 h-4 text-green-500" />
            Conexión encriptada y segura de extremo a extremo.
          </div>
        </div>
      </div>

      {/* Right side: Image / Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-gray-900 overflow-hidden items-center justify-center">
        {/* Usando una imagen generada moderna de fondo. Puedes cambiar la URL por tu propia imagen en Cloudflare/R2 */}
        <div className="absolute inset-0 z-0 opacity-60">
          <img 
            src="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop" 
            alt="Abstract Background" 
            className="w-full h-full object-cover"
          />
        </div>
        
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/40 to-transparent z-10"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-gray-900 via-transparent to-transparent z-10"></div>

        <div className="relative z-20 max-w-lg text-white px-8 text-left self-end pb-24 border-l-4 border-corporate-blue ml-12 pl-8">
          <h3 className="text-3xl font-bold mb-4 leading-tight">Optimiza el flujo de tus operaciones en campo.</h3>
          <p className="text-gray-300 text-lg leading-relaxed">
            Generación de reportes, sincronización con tu ERP y gestión documental en una única plataforma unificada.
          </p>
        </div>
      </div>
    </div>
  );
}
