document.addEventListener('DOMContentLoaded', () => {
    // Sidebar logic
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const toggleBtn = document.getElementById('mobileMenuBtn');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
            if(sidebarOverlay) sidebarOverlay.classList.toggle('hidden');
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => {
            sidebar.classList.add('-translate-x-full');
            sidebarOverlay.classList.add('hidden');
        });
    }

    // Modal Utility
    window.showModal = (modalId) => {
        document.getElementById(modalId).classList.remove('hidden');
    };

    window.hideModal = (modalId) => {
        document.getElementById(modalId).classList.add('hidden');
    };

    // Auto-active nav link based on current path
    const navLinks = document.querySelectorAll('#sidebar a');
    const currentPath = window.location.pathname;
    const currentFilename = currentPath.split('/').pop() || 'index.html';
    
    navLinks.forEach(link => {
        const linkFilename = link.getAttribute('href').split('/').pop() || 'index.html';
        if (currentFilename === linkFilename) {
            link.classList.add('bg-blue-800', 'text-white');
            link.classList.remove('text-blue-100', 'hover:bg-blue-800');
        }
    });

    // Alert Utility
    window.showAlert = (message, type='success') => {
        const alertBox = document.createElement('div');
        const bgColor = type === 'error' ? 'bg-red-500' : 'bg-green-500';
        alertBox.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 fade-in`;
        alertBox.textContent = message;
        document.body.appendChild(alertBox);
        setTimeout(() => {
            alertBox.remove();
        }, 3000);
    };
});
