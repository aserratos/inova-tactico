import re

with open('templates/dashboard/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Structural Regex: Remove old tabs container
tabs_regex = r'<div class="flex flex-col md:flex-row justify-between items-end mb-12 border-b border-gray-100 gap-6">.*?</div>\s+<div class="pb-3 border-b-2 border-transparent">.*?</div>\s+</div>'
html = re.sub(tabs_regex, '', html, flags=re.DOTALL)

# 2. Add Sidebar and flex container
sidebar = '''
    <div class="flex flex-col md:flex-row w-full gap-8 min-h-[calc(100vh-5rem)]">
    <!-- TACTICAL SIDEBAR -->
    <aside class="w-full md:w-64 shrink-0 flex flex-col gap-2">
        <div class="bg-slate-800/50 backdrop-blur-xl border border-white/5 rounded-[2rem] p-4 flex flex-col gap-2 sticky top-24 shadow-2xl">
            <div class="px-4 py-4 mb-2">
                <span class="text-[10px] uppercase font-black text-slate-500 tracking-[0.4em]">{{ current_user.role | replace('_', ' ') }}</span>
                <div class="text-inova-accent font-black text-xs tracking-widest uppercase mt-1">Nivel de Acceso</div>
            </div>
            
            <button @click="tab = 'reports'" :class="tab === 'reports' ? 'bg-inova-accent/10 border-inova-accent text-inova-accent shadow-[inset_0_0_20px_rgba(0,242,254,0.1)]' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5'" class="w-full text-left py-4 px-6 rounded-2xl border transition-all flex items-center gap-4 text-xs font-black uppercase tracking-widest relative overflow-hidden group">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg>
                Operaciones
                {% if draft_reports|length > 0 %} <span class="absolute right-4 w-2 h-2 rounded-full bg-inova-accent animate-pulse shadow-[0_0_10px_#00f2fe]"></span> {% endif %}
            </button>
            <button @click="tab = 'templates'" :class="tab === 'templates' ? 'bg-inova-accent/10 border-inova-accent text-inova-accent shadow-[inset_0_0_20px_rgba(0,242,254,0.1)]' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5'" class="w-full text-left py-4 px-6 rounded-2xl border transition-all flex items-center gap-4 text-xs font-black uppercase tracking-widest">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6v13c1.168.776 2.754 1.253 4.5 1.253s3.332-.477 4.5-1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                Plantillas
            </button>
            {% if current_user.is_admin %}
            <button @click="tab = 'users'" :class="tab === 'users' ? 'bg-inova-accent/10 border-inova-accent text-inova-accent shadow-[inset_0_0_20px_rgba(0,242,254,0.1)]' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5'" class="w-full text-left py-4 px-6 rounded-2xl border transition-all flex items-center gap-4 text-xs font-black uppercase tracking-widest mt-4">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0"></path></svg>
                Agentes
            </button>
            <button @click="tab = 'logs'" :class="tab === 'logs' ? 'bg-inova-accent/10 border-inova-accent text-inova-accent shadow-[inset_0_0_20px_rgba(0,242,254,0.1)]' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5'" class="w-full text-left py-4 px-6 rounded-2xl border transition-all flex items-center gap-4 text-xs font-black uppercase tracking-widest">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path></svg>
                Bitácora
            </button>
            {% endif %}
        </div>
    </aside>
    
    <div class="flex-1 w-full space-y-8">
'''

# Wait, the `x-data` is on line: <div class="w-full max-w-7xl mx-auto py-12 px-4" x-data="{ tab: 'reports',... }">
replace_target = 'x-data="{ tab:'
original_div = html.split('x-data="{ tab:')[0]

html = html.replace('<div class="w-full max-w-7xl mx-auto py-12 px-4"', '<div class="w-full"')
html = html.replace('<!-- TAB: REPORTS (THE EXPERT UX VIEW) -->', sidebar + '\n    <!-- TAB: REPORTS (THE EXPERT UX VIEW) -->')

# Close the new flex wrapper at the very bottom before {% endblock %}
html = html.replace('{% endblock %}', '    </div>\n</div>\n{% endblock %}')

# 3. TAILWIND REPLACEMENTS
replacements = {
    # Light backgrounds to Dark Slate / Glass
    'bg-white/60 backdrop-blur-md': 'bg-slate-900/40 backdrop-blur-xl',
    'bg-white': 'bg-slate-800/40 backdrop-blur-xl border-white/5',
    'bg-gray-50/50': 'bg-slate-900/50',
    'bg-gray-50': 'bg-slate-900',
    'bg-gray-100': 'bg-slate-800',
    'bg-gray-900': 'bg-inova-accent text-inova-main hover:bg-white', # Buttons
    'text-white': 'text-inova-main', # For buttons that were back
    
    # Text colors
    'text-gray-900': 'text-white',
    'text-gray-800': 'text-slate-200',
    'text-gray-700': 'text-slate-300',
    'text-gray-600': 'text-slate-400',
    'text-gray-500': 'text-slate-500',
    'text-gray-400': 'text-slate-500',
    
    # Borders
    'border-gray-50': 'border-white/5',
    'border-gray-100': 'border-white/5',
    'border-gray-200': 'border-white/10',
    'border-gray-300': 'border-white/20',
    'border-gray-900': 'border-inova-accent',
    
    # Accent specific
    'focus:ring-inova-accent': 'focus:ring-inova-accent focus:border-inova-accent',
    'bg-inova-accent': 'bg-inova-accent shadow-[0_0_15px_rgba(0,242,254,0.4)]',
    'hover:bg-inova-accent hover:text-white': 'hover:bg-inova-accent hover:text-black',
}

# Apply them safely
for old, new in replacements.items():
    html = html.replace(old, new)
    
# Fix inverse artifacts
html = html.replace('text-inova-main hover:bg-white border-2 border-transparent', 'bg-inova-accent text-black border-2 border-transparent')
html = html.replace('bg-inova-accent px-12 text-inova-main hover:bg-white text-inova-main hover:bg-white', 'bg-inova-accent px-12 text-black hover:bg-white')

with open('templates/dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML Reestructurado.")
