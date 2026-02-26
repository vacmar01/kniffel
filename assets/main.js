import './tailwind.css'
import htmx from 'htmx.org';
import Alpine from 'alpinejs';

// Make htmx available globally for HTMX attributes
window.htmx = htmx;

// Make Alpine available globally
window.Alpine = Alpine;

// Start Alpine
Alpine.start();

console.log('Kniffel app loaded - HTMX and Alpine initialized');
