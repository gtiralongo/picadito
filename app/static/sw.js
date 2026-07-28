var CACHE = "picadito-v1";

var PRECACHE_URLS = [
    "/",
    "/static/css/style.css",
    "/static/js/app.js",
    "/static/manifest.json",
    "/static/favicon.svg",
];

self.addEventListener("install", function (event) {
    event.waitUntil(
        caches.open(CACHE).then(function (cache) {
            return cache.addAll(PRECACHE_URLS);
        })
    );
});

self.addEventListener("fetch", function (event) {
    var url = new URL(event.request.url);

    if (url.pathname.startsWith("/static/")) {
        event.respondWith(
            caches.match(event.request).then(function (cached) {
                return cached || fetch(event.request);
            })
        );
        return;
    }

    if (url.pathname === "/") {
        event.respondWith(
            caches.match("/").then(function (cached) {
                return cached || fetch(event.request);
            })
        );
        return;
    }

    event.respondWith(fetch(event.request));
});

self.addEventListener("activate", function (event) {
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(
                keys
                    .filter(function (k) {
                        return k !== CACHE;
                    })
                    .map(function (k) {
                        return caches.delete(k);
                    })
            );
        })
    );
});
