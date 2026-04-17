import re

with open('templates/dashboard/fill.html', 'r', encoding='utf-8') as f:
    html = f.read()

replacements = {
    'bg-white': 'bg-slate-800/40 backdrop-blur-xl border border-white/5',
    'bg-gray-50': 'bg-slate-900',
    'bg-gray-100': 'bg-slate-800',
    'bg-gray-200': 'bg-slate-700',
    'bg-gray-300': 'bg-slate-600',
    
    'bg-gray-800': 'bg-slate-900/50',
    'bg-gray-900': 'bg-inova-accent text-inova-main hover:bg-white', # Action buttons / labels
    
    'text-gray-900': 'text-white',
    'text-gray-800': 'text-slate-200',
    'text-gray-700': 'text-slate-300',
    'text-gray-600': 'text-slate-400',
    'text-gray-500': 'text-slate-400',
    'text-gray-400': 'text-slate-500',
    
    'border-gray-50': 'border-white/5',
    'border-gray-100': 'border-white/5',
    'border-gray-200': 'border-white/10',
    'border-gray-300': 'border-white/20',
    'border-gray-900': 'border-inova-accent',
    
    'bg-blue-50 text-blue-500': 'bg-blue-500/10 text-blue-400',
    'bg-orange-50 text-orange-500': 'bg-orange-500/10 text-orange-400',
    'bg-green-50 text-green-600': 'bg-green-500/10 text-green-400',
    'bg-red-50 text-red-500': 'bg-red-500/10 text-red-400',
    
    'focus:border-inova-accent': 'focus:border-inova-accent focus:ring-1 focus:ring-inova-accent',
    'hover:border-inova-accent': 'hover:border-inova-accent shadow-[0_0_15px_rgba(0,242,254,0.05)]',
    'text-white text-xs': 'text-slate-300 text-xs',
}

for old, new in replacements.items():
    html = html.replace(old, new)
    
html = html.replace('text-inova-main hover:bg-white text-white', 'text-black hover:bg-white')
html = html.replace('bg-inova-accent text-slate-300', 'bg-inova-accent text-black')
html = html.replace('bg-inova-accent text-white', 'bg-inova-accent text-black')

with open('templates/dashboard/fill.html', 'w', encoding='utf-8') as f:
    f.write(html)
