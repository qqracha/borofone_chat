// =============================================
// Mobile Menu Functions (PWA)
// =============================================
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const roomsSidebar = document.getElementById('roomsSidebar');
    const sidebarOverlay = document.getElementById('roomsSidebarOverlay');
    
    if (!mobileMenuBtn || !roomsSidebar) return;
    
    // Показываем кнопку только на мобильных
    const checkMobile = () => {
        if (window.innerWidth <= 640) {
            mobileMenuBtn.style.display = 'flex';
            // Показываем sidebar
            roomsSidebar.style.display = 'flex';
        } else {
            mobileMenuBtn.style.display = 'none';
            roomsSidebar.classList.remove('active');
            roomsSidebar.style.display = '';
            if (sidebarOverlay) sidebarOverlay.classList.remove('active');
        }
    };
    
    // Проверяем при загрузке и при ресайзе
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    // Открытие меню
    mobileMenuBtn.addEventListener('click', () => {
        // Добавляем inline стили для гарантии
        roomsSidebar.style.position = 'fixed';
        roomsSidebar.style.left = '0';
        roomsSidebar.style.top = '0';
        roomsSidebar.style.bottom = '0';
        roomsSidebar.style.width = '85%';
        roomsSidebar.style.maxWidth = '300px';
        roomsSidebar.style.zIndex = '1000';
        roomsSidebar.style.transform = 'translateX(0)';
        roomsSidebar.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        roomsSidebar.style.borderRadius = '0';
        roomsSidebar.style.margin = '8px 0 8px 8px';
        roomsSidebar.style.display = 'flex';
        
        roomsSidebar.classList.add('active');
        if (sidebarOverlay) {
            sidebarOverlay.style.position = 'fixed';
            sidebarOverlay.style.top = '0';
            sidebarOverlay.style.left = '0';
            sidebarOverlay.style.right = '0';
            sidebarOverlay.style.bottom = '0';
            sidebarOverlay.style.background = 'rgba(0, 0, 0, 0.6)';
            sidebarOverlay.style.zIndex = '999';
            sidebarOverlay.classList.add('active');
        }
        document.body.style.overflow = 'hidden';
    });
    
    // Закрытие по оверлею
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => {
            roomsSidebar.classList.remove('active');
            roomsSidebar.style.transform = 'translateX(-100%)';
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }
    
    // Закрытие меню при выборе комнаты (на мобильных)
    const roomsList = document.getElementById('roomsList');
    if (roomsList) {
        roomsList.addEventListener('click', (e) => {
            if (e.target.closest('.room-item') && window.innerWidth <= 640) {
                roomsSidebar.classList.remove('active');
                roomsSidebar.style.transform = 'translateX(-100%)';
                if (sidebarOverlay) sidebarOverlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }
}
