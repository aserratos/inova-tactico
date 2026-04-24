import { SignIn } from "@clerk/clerk-react";

export default function Login() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-extrabold text-corporate-blue tracking-tight">
          Inova Táctico
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          Centro de Operaciones y Reportes
        </p>
      </div>

      <SignIn 
        appearance={{
          elements: {
            card: "bg-white shadow-xl rounded-2xl border border-gray-100",
            headerTitle: "text-2xl font-bold text-gray-900",
            headerSubtitle: "text-gray-500",
            formButtonPrimary: "bg-corporate-blue hover:bg-blue-800 text-white rounded-lg py-2.5 transition-all shadow-md",
            footerActionLink: "text-corporate-blue hover:text-blue-800 font-medium",
            formFieldInput: "rounded-lg border-gray-300 focus:ring-2 focus:ring-corporate-blue focus:border-transparent py-2.5",
          }
        }}
      />
    </div>
  );
}
