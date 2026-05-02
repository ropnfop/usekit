/* Path: usekit/tools/editor/sw.js
 * -----------------------------------------------------------------------------------------------
 * Created by: THE Little Prince, in harmony with ROP and FOP
 * Purpose: Service Worker for offline caching and PWA support
 *---------------------------------------------------------------------------------------------*/

const CACHE_VERSION = 'usekit-editor-v0.2.0'; // ← 배포 시 버전 올리기
const CACHE_NAME = CACHE_VERSION;

// 🔧 DEV_MODE: index.html의 DEV_MODE = true 이면 SW가 설치되지 않으므로
//    이 파일은 DEV_MODE = false (배포) 일 때만 동작합니다.

// 캐시할 파일 목록
const ASSETS_TO_CACHE = [
    './',
    './index.html',
    './style.css',
    './manifest.json',
    './icon-192.png',
    './icon-512.png',

    './cm6.bundle.js',

    // Editor & State
    './js2/editor/editor.js',
    './js2/state/state.js',
    './js2/state/state_slot.js',

    // Slot modules
    './js2/slot/slot_storage.js',
    './js2/slot/slot_manager.js',
    './js2/slot/slot_popup.js',
    './js2/slot/save_popup.js',

    // Navigation modules
    './js2/nav/nav_cursor.js',
    './js2/nav/nav_block.js',
    './js2/nav/nav_num.js',
    './js2/nav/nav_find.js',
    './js2/nav/nav_clipboard.js',
    './js2/nav/nav.js',
    './js2/nav/nav_block_v2.js',

    // State modules
    './js2/state/active_state.js',
    './js2/state/block_state.js',
    './js2/state/setup_policy.js',

    // Slot extra
    './js2/slot/slot_usekit.js',
    './js2/slot/tab_usekit.js',

    // UI extra
    './js2/ui/ui_feedback.js',
    './js2/ui/ui_keypad.js',

    // UI modules
    './js2/ui/ui.js',
    './js2/ui/ui_events.js',
    './js2/ui/ui_settings.js',
    './js2/ui/ui_viewport.js',
    './js2/ui/ui_stats.js',
    './js2/ui/ui_debug.js',

    // Float pills (G12 분리)
    './float-pills.css',
    './js2/float/float_common.js',
    './js2/float/float_sql.js',
    './js2/float/float_run.js',
    './js2/float/float_clip.js',
    './js2/float/float_menu.js',

    // Popup
    './js2/popup/popup_manager.js',

    // Themes
    './theme-dark.css',
    './theme-light.css',
    './theme-white.css',

    // Autocomplete
    './js2/editor/py_complete.js',
    './js2/editor/sql_complete.js'
];

// Install 이벤트 - 리소스 캐싱
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker...', CACHE_VERSION);
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching app shell');
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .then(() => {
                console.log('[SW] All resources cached successfully');
                // skipWaiting: 메시지 수신 시 실행 (index.html controllerchange 패턴)
            })
            .catch((error) => {
                console.error('[SW] Cache installation failed:', error);
            })
    );
});

// Activate 이벤트 - 이전 캐시 삭제
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker...', CACHE_VERSION);
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => {
                            // 현재 버전이 아닌 캐시 삭제
                            return name !== CACHE_NAME && name.startsWith('usekit-editor-');
                        })
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[SW] Claiming clients');
                return self.clients.claim(); // 즉시 제어권 획득
            })
    );
});

// Fetch 이벤트 - 캐시 우선 전략 (Cache First, Network Fallback)
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // 같은 origin만 처리 (CDN 등 외부 리소스는 제외)
    if (url.origin !== location.origin) {
        return;
    }
    
    // 🔥 항상 네트워크: API 요청, clear_cache.html
    if (url.pathname.startsWith('/api/') || url.pathname.includes('clear_cache.html')) {
        event.respondWith(fetch(request));
        return;
    }

    // 🔥 index.html: network-first with 1.5s timeout (서버 죽어있어도 빠르게 캐시 폴백)
    if (url.pathname === '/' || url.pathname.endsWith('/index.html') || url.pathname.endsWith('/editor')) {
        event.respondWith(
            fetch(request, { signal: AbortSignal.timeout(1500) })
                .then((response) => {
                    if (response && response.status === 200) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(c => c.put(request, clone));
                    }
                    return response;
                })
                .catch(() => caches.match('./index.html'))
        );
        return;
    }
    
    event.respondWith(
        caches.match(request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    // 캐시에 있으면 캐시 반환
                    return cachedResponse;
                }
                
                // 캐시에 없으면 네트워크 요청
                return fetch(request)
                    .then((response) => {
                        // 유효한 응답인지 확인
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // 응답을 캐시에 저장 (clone 필요)
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(request, responseToCache);
                            });
                        
                        return response;
                    })
                    .catch((error) => {
                        console.error('[SW] Fetch failed:', error);
                        // 오프라인 상태에서 index.html 요청 시 캐시된 index.html 반환
                        if (request.mode === 'navigate') {
                            return caches.match('./index.html');
                        }
                        throw error;
                    });
            })
    );
});

// 메시지 핸들러 - 캐시 업데이트 강제
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        console.log('[SW] Received SKIP_WAITING message');
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        console.log('[SW] Clearing all caches');
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((name) => caches.delete(name))
                );
            })
        );
    }
});

console.log('[SW] Service Worker loaded');