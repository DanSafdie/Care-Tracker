/**
 * Care-Tracker Confetti - MEGA DOPAMINE EDITION
 * Designed for maximum impact while staying smooth on Fire HD 10 (MediaTek MT8183).
 *
 * Features:
 * - 3 sequential bursts (Left, Right, Center)
 * - Subtle screen flash on each burst
 * - Mix of colored rectangles and emojis (🐾, 🦴, ✨)
 * - Enhanced physics (more drag, bouncier wobble)
 * 
 * Performance notes:
 * - Total particles capped at ~160 across all bursts
 * - No object creation inside the draw loop
 * - Cleans up completely after 5 seconds
 */

var _confettiRunning = false;

function launchConfetti() {
    if (_confettiRunning) return;
    _confettiRunning = true;

    var DURATION_MS = 5000;
    var COLORS = [
        '#3fb950', '#58a6ff', '#f85149', '#d29922',
        '#a371f7', '#f778ba', '#ff9f43', '#00d2d3'
    ];
    var EMOJIS = ['🐾', '🦴', '✨', '❤️'];

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
    var W, H;

    function resize() {
        W = window.innerWidth;
        H = window.innerHeight;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        ctx.scale(dpr, dpr);
    }
    resize();

    var particles = [];
    var flashes = []; // Track screen flashes

    // Helper to spawn a burst of particles
    function spawnBurst(xRatio, yRatio, count, isBig) {
        // Add a screen flash
        flashes.push({ alpha: isBig ? 0.6 : 0.3, decay: 0.05 });
        
        for (var i = 0; i < count; i++) {
            var isEmoji = Math.random() > 0.75; // ~25% emojis
            var angle = (Math.random() * Math.PI) - (Math.PI / 2); // -90 to +90 (upward fan)
            var speed = (isBig ? 8 : 5) + Math.random() * (isBig ? 12 : 8);
            
            particles.push({
                type: isEmoji ? 'emoji' : 'rect',
                text: isEmoji ? EMOJIS[Math.floor(Math.random() * EMOJIS.length)] : '',
                x: W * xRatio,
                y: H * yRatio,
                vx: Math.cos(angle) * speed * 1.5,
                vy: Math.sin(angle) * speed - (isBig ? 6 : 3),
                w: 8 + Math.random() * 8,
                h: 5 + Math.random() * 5,
                color: COLORS[Math.floor(Math.random() * COLORS.length)],
                rotation: Math.random() * 360,
                rotSpeed: (Math.random() - 0.5) * 15,
                gravity: 0.15 + Math.random() * 0.1,
                drag: 0.95 + Math.random() * 0.04, // slightly more drag for explosive feel
                opacity: 1,
                wobble: Math.random() * Math.PI * 2,
                wobbleSpeed: 0.002 + Math.random() * 0.002
            });
        }
    }

    // Schedule the bursts
    spawnBurst(0.2, 0.6, 40, false); // Left burst immediately
    
    setTimeout(function() {
        if (!_confettiRunning) return;
        spawnBurst(0.8, 0.6, 40, false); // Right burst
    }, 300);
    
    setTimeout(function() {
        if (!_confettiRunning) return;
        spawnBurst(0.5, 0.8, 80, true);  // Center BIG burst
    }, 700);

    var startTime = Date.now();
    var animFrame;

    function draw() {
        var elapsed = Date.now() - startTime;
        if (elapsed > DURATION_MS) {
            cleanup();
            return;
        }

        ctx.clearRect(0, 0, W, H);

        // Draw flashes
        for (var f = flashes.length - 1; f >= 0; f--) {
            if (flashes[f].alpha > 0) {
                ctx.fillStyle = 'rgba(255, 255, 255, ' + flashes[f].alpha + ')';
                ctx.fillRect(0, 0, W, H);
                flashes[f].alpha -= flashes[f].decay;
            } else {
                flashes.splice(f, 1);
            }
        }

        // Fade out in the last 1000ms
        var globalAlpha = elapsed > (DURATION_MS - 1000) 
            ? (DURATION_MS - elapsed) / 1000 
            : 1;

        for (var i = 0; i < particles.length; i++) {
            var p = particles[i];

            // Physics
            p.vy += p.gravity;
            p.vx *= p.drag;
            p.vy *= p.drag;
            p.x += p.vx + Math.sin(elapsed * p.wobbleSpeed + p.wobble) * 1.5; // pronounced lateral drift
            p.y += p.vy;
            p.rotation += p.rotSpeed;

            // Draw
            ctx.save();
            ctx.globalAlpha = globalAlpha * p.opacity;
            ctx.translate(p.x, p.y);
            ctx.rotate((p.rotation * Math.PI) / 180);
            
            if (p.type === 'rect') {
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
            } else {
                ctx.font = '24px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(p.text, 0, 0);
            }
            
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
