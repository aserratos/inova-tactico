"""
Script de diagnóstico para conexión Odoo XML-RPC
Ejecutar con: python test_odoo.py
"""
import xmlrpc.client
import sys

# Fix encoding para Windows
sys.stdout.reconfigure(encoding='utf-8')

URL = "https://inovasecurite.odoo.com"
DB = "inovasecurite"
USERNAME = "aserratos84@gmail.com"
API_KEY = "fca03bfd82d9c5a4a620f7d99d20edf1a1926a59"

print("=" * 60)
print("DIAGNOSTICO DE CONEXION ODOO")
print("=" * 60)
print(f"URL:      {URL}")
print(f"DB:       {DB}")
print(f"Usuario:  {USERNAME}")
print(f"API Key:  {API_KEY[:8]}...")
print("=" * 60)

# -- Paso 1: Verificar que el endpoint responde
print("\n[1/4] Verificando endpoint /xmlrpc/2/common ...")
try:
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    version = common.version()
    print(f"  OK - Servidor responde. Version Odoo: {version.get('server_version', '?')}")
except Exception as e:
    print(f"  ERROR: {e}")
    print("\n  POSIBLES CAUSAS:")
    print("  - La instancia Odoo.com tiene XML-RPC deshabilitado")
    print("  - La URL no es correcta")
    print("  - Problema de red o SSL")
    sys.exit(1)

# -- Paso 2: Autenticar con API Key
print(f"\n[2/4] Autenticando como '{USERNAME}' con API Key...")
try:
    uid = common.authenticate(DB, USERNAME, API_KEY, {})
    if uid:
        print(f"  OK - Autenticacion exitosa. UID: {uid}")
    else:
        print("  FALLO - Autenticacion fallida (uid=False/0)")
        print("\n  POSIBLES CAUSAS:")
        print("  - El usuario o email no coincide")
        print("  - La API Key no es valida o expiro")
        print("  - La API Key no esta habilitada en la cuenta Odoo")
        print("\n  TIP: En Odoo ve a tu perfil > Seguridad de la Cuenta > Claves API")
        sys.exit(1)
except Exception as e:
    print(f"  ERROR en autenticacion: {e}")
    sys.exit(1)

# -- Paso 3: Probar lectura de datos
print(f"\n[3/4] Probando acceso a res.partner (empresas)...")
try:
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
    count = models.execute_kw(DB, uid, API_KEY,
        'res.partner', 'search_count',
        [[('is_company', '=', True)]]
    )
    print(f"  OK - Total de empresas en Odoo: {count}")
except Exception as e:
    print(f"  ERROR al leer datos: {e}")
    sys.exit(1)

# -- Paso 4: Mostrar primeras 3 empresas
print(f"\n[4/4] Primeras 3 empresas que se sincronizarian:")
try:
    partners = models.execute_kw(DB, uid, API_KEY,
        'res.partner', 'search_read',
        [[('is_company', '=', True)]],
        {'fields': ['name', 'vat', 'email'], 'limit': 3}
    )
    for p in partners:
        print(f"  - {p['name']} | RFC: {p.get('vat') or 'N/A'} | Email: {p.get('email') or 'N/A'}")
    if not partners:
        print("  (No hay empresas aun en Odoo, pero la conexion funciona)")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTICO COMPLETADO - La conexion funciona correctamente.")
print("=" * 60)
