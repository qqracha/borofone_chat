// =============================================
// Mobile Users Sidebar Functions (PWA)
// =============================================
function initMobileUsersSidebar() {
    const mobileUsersBtn = document.getElementById('mobileUsersBtn');
    const usersSidebar = document.getElementById('usersSidebar');
    const usersSidebarOverlay = document.getElementById('usersSidebarOverlay');
    
    if (!mobileUsersBtn || !usersSidebar) return;
    
    // Показываем кнопку только на мобильных
    const checkMobile = () => {
        if (window.innerWidth <= 640) {
            mobileUsersBtn.style.display = 'flex';
        } else {
            mobileUsersBtn.style.display = 'none';
            usersSidebar.classList.remove('active');
            if (usersSidebarOverlay) usersSidebarOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    };
    
    // Проверяем при загрузке и при ресайзе
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    // Открытие users sidebar
    mobileUsersBtn.addEventListener('click', () => {
        // Просто добавляем класс active - CSS сделает всю работу
        usersSidebar.classList.add('active');
        if (usersSidebarOverlay) {
            usersSidebarOverlay.classList.add('active');
        }
        document.body.style.overflow = 'hidden';
    });
    
    // Закрытие по оверлею
    if (usersSidebarOverlay) {
        usersSidebarOverlay.addEventListener('click', () => {
            usersSidebar.classList.remove('active');
            usersSidebarOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }
    
    // Swipe gestures для мобильных
    let touchStartX = 0;
    let touchEndX = 0;
    const minSwipeDistance = 50;
    
    // Swipe на чате - свайп вправо открывает список пользователей
    const chatContainer = document.querySelector('.chat-container') || document.querySelector('.messages-container');
    if (chatContainer) {
        chatContainer.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        chatContainer.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });
    }
    
    // Swipe на сайдбаре - свайп влево закрывает его
    usersSidebar.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    usersSidebar.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSidebarSwipe();
    }, { passive: true });
    
    function handleSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        // Свайп вправо - открыть сайдбар
        if (swipeDistance > minSwipeDistance && window.innerWidth <= 640) {
            // Проверяем, что сайдбар еще не открыт
            if (!usersSidebar.classList.contains('active')) {
                usersSidebar.classList.add('active');
                if (usersSidebarOverlay) {
                    usersSidebarOverlay.classList.add('active');
                }
                document.body.style.overflow = 'hidden';
            }
        }
    }
    
    function handleSidebarSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        // Свайп влево - закрыть сайдбар
        if (swipeDistance < -minSwipeDistance && window.innerWidth <= 640) {
            if (usersSidebar.classList.contains('active')) {
                usersSidebar.classList.remove('active');
                if (usersSidebarOverlay) {
                    usersSidebarOverlay.classList.remove('active');
                }
                document.body.style.overflow = '';
            }
        }
    }
}

// Инициализируем мобильное меню
initMobileMenu();

// Инициализируем мобильную панель пользователей
initMobileUsersSidebar();

init();
