import { OrganizationProfile } from "@clerk/clerk-react";

export default function TeamManagement() {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Mi Equipo</h2>
        <p className="text-gray-500 mt-1">
          Administra los miembros de tu organización, asigna roles e invita a nuevos técnicos.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex justify-center p-4">
        {/* Componente nativo de Clerk que renderiza toda la UI de administración */}
        <OrganizationProfile 
          routing="hash" 
          appearance={{
            elements: {
              rootBox: "w-full flex justify-center",
              card: "shadow-none w-full max-w-4xl"
            }
          }}
        />
      </div>
    </div>
  );
}
