/**
 * Care-Tracker Confetti Animation
 * Lightweight canvas-based celebration effect for when all tasks are completed.
 *
 * Designed for Fire HD 10 (1280x800 CSS viewport, MediaTek MT8183).
 * Keeps particle count modest (~120) and cleans up after ~4 seconds.
 * Written in ES5 for Fully Kiosk Browser (WebView ~Chrome 90) compatibility.
 *
 * Usage: launchConfetti()  — safe to call multiple times; concurrent calls are ignored.
 */

var _confettiRunning = false;

function launchConfetti() {
    if (_confettiRunning) return;
    _confettiRunning = true;

    var PARTICLE_COUNT = 120;
    var DURATION_MS = 4000;
    var COLORS = [
        '#3fb950', '#58a6ff', '#f85149', '#d29922',
        '#a371f7', '#f778ba', '#ff9f43', '#00d2d3'
    ];

    var canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '9999';
    document.body.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    var dpr = window.devicePixelRatio || 1;

    function resize() {
        canvas.width = window.innerWidth * dpr;
        canvas.height = window.innerHeight * dpr;
        ctx.scale(dpr, dpr);
    }
    resize();

    var W = window.innerWidth;
    var H = window.innerHeight;

    // Build particles — burst from top center with spread
    var particles = [];
    for (var i = 0; i < PARTICLE_COUNT; i++) {
        var angle = (Math.random() * Math.PI) - (Math.PI / 2); // -90° to +90° (upward fan)
        var speed = 4 + Math.random() * 8;
        particles.push({
            x: W * (0.3 + Math.random() * 0.4),   // spawn across top 40% center
            y: -10 - Math.random() * 40,            // just above viewport
            vx: Math.cos(angle) * speed * 1.5,
            vy: Math.sin(angle) * speed - 2,        // initial upward bias
            w: 6 + Math.random() * 6,               // rectangle width
            h: 4 + Math.random() * 4,               // rectangle height
            color: COLORS[Math.floor(Math.random() * COLORS.length)],
            rotation: Math.random() * 360,
            rotSpeed: (Math.random() - 0.5) * 12,
            gravity: 0.12 + Math.random() * 0.08,
            drag: 0.98 + Math.random() * 0.015,
            opacity: 1,
            wobble: Math.random() * Math.PI * 2      // phase offset for lateral wobble
        });
    }

    var startTime = Date.now();
    var animFrame;

    function draw() {
        var elapsed = Date.now() - startTime;
        if (elapsed > DURATION_MS) {
            cleanup();
            return;
        }

        // Fade out in the last 800ms
        var globalAlpha = elapsed > (DURATION_MS - 800)
            ? (DURATION_MS - elapsed) / 800
            : 1;

        ctx.clearRect(0, 0, W, H);

        for (var i = 0; i < particles.length; i++) {
            var p = particles[i];

            // Physics
            p.vy += p.gravity;
            p.vx *= p.drag;
            p.vy *= p.drag;
            p.x += p.vx + Math.sin(elapsed * 0.002 + p.wobble) * 0.5;
            p.y += p.vy;
            p.rotation += p.rotSpeed;

            // Draw
            ctx.save();
            ctx.globalAlpha = globalAlpha * p.opacity;
            ctx.translate(p.x, p.y);
            ctx.rotate((p.rotation * Math.PI) / 180);
            ctx.fillStyle = p.color;
            ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
            ctx.restore();
        }

        animFrame = requestAnimationFrame(draw);
    }

    function cleanup() {
        if (animFrame) cancelAnimationFrame(animFrame);
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
        _confettiRunning = false;
    }

    animFrame = requestAnimationFrame(draw);
}
