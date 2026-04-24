import { UserProfile } from "@clerk/clerk-react";

export default function SecuritySettings() {
  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Seguridad y Perfil</h1>
        <p className="mt-2 text-gray-600">
          Administra tu contraseña, FaceID, huella dactilar y autenticación de dos pasos.
        </p>
      </div>
      
      {/* Clerk's pre-built UserProfile component handles everything! */}
      <UserProfile 
        appearance={{
          elements: {
            rootBox: "w-full",
            card: "w-full shadow-sm border border-gray-200 rounded-xl",
            navbar: "hidden sm:flex", // Hide the left navbar on very small screens if desired, or let Clerk handle it
          }
        }}
      />
    </div>
  );
}
