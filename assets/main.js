import './tailwind.css'
import Alpine from 'alpinejs';

// Make Alpine available globally
window.Alpine = Alpine;

// Start Alpine
Alpine.start();

console.log('Kniffel app loaded - Alpine initialized (HTMX via FastHTML CDN)');
