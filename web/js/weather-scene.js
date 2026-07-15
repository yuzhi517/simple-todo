const DPR_LIMIT = 2;
const TAU = Math.PI * 2;

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function random(min, max) {
    return min + Math.random() * (max - min);
}

function seededRandom(seed) {
    let value = seed >>> 0;
    return () => {
        value += 0x6D2B79F5;
        let t = value;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

function chooseWeather() {
    const forced = new URLSearchParams(window.location.search).get('weather');
    if (forced === 'sunny' || forced === 'rain') return forced;

    if (window.crypto?.getRandomValues) {
        const value = new Uint32Array(1);
        window.crypto.getRandomValues(value);
        return value[0] % 2 === 0 ? 'sunny' : 'rain';
    }
    return Math.random() < 0.5 ? 'sunny' : 'rain';
}

function fitCanvas(canvas, width, height, dpr) {
    canvas.width = Math.max(1, Math.round(width * dpr));
    canvas.height = Math.max(1, Math.round(height * dpr));
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    const ctx = canvas.getContext('2d', { alpha: true });
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return ctx;
}

function fillEllipseGradient(ctx, x, y, rx, ry, inner, outer) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(rx, ry);
    const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, 1);
    gradient.addColorStop(0, inner);
    gradient.addColorStop(1, outer);
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(0, 0, 1, 0, TAU);
    ctx.fill();
    ctx.restore();
}

function drawCloud(ctx, x, y, width, alpha, color, blur = 0) {
    ctx.save();
    if (blur) ctx.filter = `blur(${blur}px)`;
    ctx.fillStyle = color.replace('ALPHA', String(alpha));
    ctx.beginPath();
    ctx.ellipse(x, y, width * 0.34, width * 0.085, 0, 0, TAU);
    ctx.ellipse(x - width * 0.19, y + width * 0.012, width * 0.23, width * 0.06, 0, 0, TAU);
    ctx.ellipse(x + width * 0.22, y + width * 0.016, width * 0.27, width * 0.07, 0, 0, TAU);
    ctx.fill();
    ctx.restore();
}

function drawCity(ctx, width, height, rainy) {
    const rng = seededRandom((width * 17 + height * 31 + (rainy ? 701 : 211)) | 0);
    const horizon = height * 0.61;
    const base = height * 0.77;

    ctx.save();
    ctx.globalAlpha = rainy ? 0.24 : 0.34;
    ctx.fillStyle = rainy ? '#49616b' : '#5e7f87';
    let x = -20;
    while (x < width + 30) {
        const buildingWidth = 24 + rng() * 66;
        const buildingHeight = 38 + rng() * (height * 0.19);
        const top = base - buildingHeight;
        ctx.fillRect(x, top, buildingWidth, buildingHeight);

        if (rng() > 0.65) {
            ctx.fillRect(x + buildingWidth * 0.45, top - 8 - rng() * 18, 2, 12 + rng() * 18);
        }

        ctx.fillStyle = rainy ? 'rgba(224,220,179,.13)' : 'rgba(255,238,174,.16)';
        const columns = Math.max(1, Math.floor(buildingWidth / 16));
        for (let column = 0; column < columns; column += 1) {
            for (let row = 0; row < 3; row += 1) {
                if (rng() > 0.48) {
                    ctx.fillRect(x + 7 + column * 14, top + 11 + row * 17, 3, 5);
                }
            }
        }
        ctx.fillStyle = rainy ? '#49616b' : '#5e7f87';
        x += buildingWidth + 5 + rng() * 14;
    }

    const haze = ctx.createLinearGradient(0, horizon, 0, base + 20);
    haze.addColorStop(0, rainy ? 'rgba(200,214,216,.62)' : 'rgba(219,231,220,.45)');
    haze.addColorStop(1, 'rgba(197,214,216,0)');
    ctx.globalAlpha = 1;
    ctx.fillStyle = haze;
    ctx.fillRect(0, horizon - 20, width, base - horizon + 45);
    ctx.restore();
}

function drawTree(ctx, x, baseY, scale, rainy, rng) {
    ctx.save();
    ctx.globalAlpha = rainy ? 0.68 : 0.86;
    ctx.strokeStyle = rainy ? '#344d47' : '#4e6040';
    ctx.lineWidth = Math.max(2, 4 * scale);
    ctx.beginPath();
    ctx.moveTo(x, baseY);
    ctx.quadraticCurveTo(x + 3 * scale, baseY - 28 * scale, x - 1 * scale, baseY - 54 * scale);
    ctx.stroke();

    const colors = rainy
        ? ['#395e50', '#45695a', '#557568']
        : ['#49754d', '#5c8557', '#739266'];
    for (let i = 0; i < 10; i += 1) {
        const cx = x + (rng() - 0.5) * 48 * scale;
        const cy = baseY - (40 + rng() * 47) * scale;
        ctx.fillStyle = colors[Math.floor(rng() * colors.length)];
        ctx.beginPath();
        ctx.ellipse(cx, cy, (12 + rng() * 16) * scale, (8 + rng() * 13) * scale, rng() - 0.5, 0, TAU);
        ctx.fill();
    }
    ctx.restore();
}

function drawTrees(ctx, width, height, rainy) {
    const rng = seededRandom((width * 43 + height * 13 + (rainy ? 991 : 307)) | 0);
    const baseY = height * 0.79;
    const count = clamp(Math.floor(width / 110), 7, 22);
    for (let i = 0; i < count; i += 1) {
        drawTree(ctx, (i + rng() * 0.65) * (width / count), baseY, 0.72 + rng() * 0.8, rainy, rng);
    }
}

function drawGround(ctx, width, height, rainy) {
    const groundTop = height * 0.73;
    const gradient = ctx.createLinearGradient(0, groundTop, 0, height);
    if (rainy) {
        gradient.addColorStop(0, '#647779');
        gradient.addColorStop(0.42, '#43575c');
        gradient.addColorStop(1, '#263b42');
    } else {
        gradient.addColorStop(0, '#78957b');
        gradient.addColorStop(0.36, '#70877b');
        gradient.addColorStop(1, '#52676a');
    }
    ctx.fillStyle = gradient;
    ctx.fillRect(0, groundTop, width, height - groundTop);

    ctx.save();
    const rng = seededRandom((width + height + (rainy ? 149 : 37)) | 0);
    if (rainy) {
        ctx.globalAlpha = 0.32;
        for (let i = 0; i < 20; i += 1) {
            const x = rng() * width;
            const y = groundTop + rng() * (height - groundTop);
            const reflectionLength = 18 + rng() * 68;
            const reflectionWidth = 1.5 + rng() * 4;
            const reflection = ctx.createLinearGradient(x, y, x, Math.min(height, y + reflectionLength));
            reflection.addColorStop(0, 'rgba(208,225,226,.55)');
            reflection.addColorStop(1, 'rgba(208,225,226,0)');
            ctx.fillStyle = reflection;
            ctx.fillRect(x - reflectionWidth * 0.5, y, reflectionWidth, reflectionLength);

            ctx.strokeStyle = 'rgba(226,237,235,.22)';
            ctx.lineWidth = 0.65;
            ctx.beginPath();
            ctx.moveTo(x - reflectionWidth * 2.4, y + reflectionLength * 0.72);
            ctx.lineTo(x + reflectionWidth * 2.4, y + reflectionLength * 0.72);
            ctx.stroke();
        }
    } else {
        ctx.globalAlpha = 0.18;
        for (let i = 0; i < 24; i += 1) {
            const x = rng() * width;
            const y = groundTop + rng() * (height - groundTop);
            const reflection = ctx.createLinearGradient(x, y, x, Math.min(height, y + 90));
            reflection.addColorStop(0, 'rgba(247,227,174,.24)');
            reflection.addColorStop(1, 'rgba(208,225,226,0)');
            ctx.fillStyle = reflection;
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x + random(3, 15), y);
            ctx.lineTo(x + random(10, 34), Math.min(height, y + random(30, 96)));
            ctx.lineTo(x - random(7, 24), Math.min(height, y + random(30, 96)));
            ctx.closePath();
            ctx.fill();
        }
    }
    ctx.restore();

    ctx.strokeStyle = rainy ? 'rgba(220,232,232,.25)' : 'rgba(231,239,224,.2)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 7; i += 1) {
        const y = groundTop + (i + 1) * (height - groundTop) / 8;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y + i * 0.6);
        ctx.stroke();
    }
}

function drawSunnyBackground(ctx, width, height) {
    const sky = ctx.createLinearGradient(0, 0, 0, height);
    sky.addColorStop(0, '#66a9d0');
    sky.addColorStop(0.42, '#a9cfda');
    sky.addColorStop(0.7, '#d9dfc5');
    sky.addColorStop(1, '#637574');
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, width, height);

    fillEllipseGradient(ctx, width * 0.88, height * 0.06, width * 0.25, height * 0.34,
        'rgba(255,243,190,.88)', 'rgba(255,230,168,0)');
    drawCloud(ctx, width * 0.25, height * 0.18, Math.min(width * 0.4, 440), 0.18, 'rgba(240,248,246,ALPHA)');
    drawCloud(ctx, width * 0.68, height * 0.31, Math.min(width * 0.32, 360), 0.12, 'rgba(237,246,241,ALPHA)');
    drawCity(ctx, width, height, false);
    drawTrees(ctx, width, height, false);
    drawGround(ctx, width, height, false);

    const exposure = ctx.createLinearGradient(width, 0, 0, height);
    exposure.addColorStop(0, 'rgba(255,237,179,.25)');
    exposure.addColorStop(0.48, 'rgba(255,245,210,.05)');
    exposure.addColorStop(1, 'rgba(15,43,55,.13)');
    ctx.fillStyle = exposure;
    ctx.fillRect(0, 0, width, height);
}

function drawRainBackground(ctx, width, height) {
    const sky = ctx.createLinearGradient(0, 0, 0, height);
    sky.addColorStop(0, '#728890');
    sky.addColorStop(0.42, '#9aa9aa');
    sky.addColorStop(0.67, '#aeb9b5');
    sky.addColorStop(1, '#34494f');
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, width, height);

    drawCloud(ctx, width * 0.2, height * 0.1, Math.min(width * 0.68, 740), 0.3, 'rgba(68,84,91,ALPHA)');
    drawCloud(ctx, width * 0.72, height * 0.2, Math.min(width * 0.62, 680), 0.23, 'rgba(76,90,95,ALPHA)');
    drawCloud(ctx, width * 0.48, height * 0.31, Math.min(width * 0.52, 570), 0.16, 'rgba(212,220,217,ALPHA)');
    drawCity(ctx, width, height, true);
    drawTrees(ctx, width, height, true);
    drawGround(ctx, width, height, true);

    const fog = ctx.createLinearGradient(0, height * 0.25, 0, height * 0.83);
    fog.addColorStop(0, 'rgba(209,219,218,.04)');
    fog.addColorStop(0.55, 'rgba(209,219,218,.2)');
    fog.addColorStop(1, 'rgba(195,207,206,.04)');
    ctx.fillStyle = fog;
    ctx.fillRect(0, 0, width, height);
}

function dropletPath(ctx, drop) {
    const { x, y, width, height } = drop;
    ctx.beginPath();
    ctx.moveTo(x - width * 0.08, y - height * 0.5);
    ctx.bezierCurveTo(
        x + width * 0.16, y - height * 0.36,
        x + width * 0.5, y - height * 0.06,
        x + width * 0.44, y + height * 0.2,
    );
    ctx.bezierCurveTo(
        x + width * 0.38, y + height * 0.48,
        x - width * 0.26, y + height * 0.56,
        x - width * 0.43, y + height * 0.22,
    );
    ctx.bezierCurveTo(
        x - width * 0.57, y - height * 0.04,
        x - width * 0.28, y - height * 0.36,
        x - width * 0.08, y - height * 0.5,
    );
    ctx.closePath();
}

function lensDropletPath(ctx, drop) {
    const { x, y, width, height } = drop;
    ctx.beginPath();
    ctx.moveTo(x - width * 0.16, y - height * 0.46);
    ctx.bezierCurveTo(
        x + width * 0.12, y - height * 0.51,
        x + width * 0.43, y - height * 0.25,
        x + width * 0.45, y + height * 0.04,
    );
    ctx.bezierCurveTo(
        x + width * 0.48, y + height * 0.34,
        x + width * 0.17, y + height * 0.51,
        x - width * 0.1, y + height * 0.48,
    );
    ctx.bezierCurveTo(
        x - width * 0.4, y + height * 0.44,
        x - width * 0.52, y + height * 0.16,
        x - width * 0.45, y - height * 0.1,
    );
    ctx.bezierCurveTo(
        x - width * 0.39, y - height * 0.34,
        x - width * 0.29, y - height * 0.44,
        x - width * 0.16, y - height * 0.46,
    );
    ctx.closePath();
}

class WeatherScene {
    constructor(root, weather) {
        this.root = root;
        this.weather = weather;
        this.backgroundCanvas = root.querySelector('#weather-background');
        this.atmosphereCanvas = root.querySelector('#weather-atmosphere');
        this.glassCanvas = root.querySelector('#weather-glass');
        this.motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        this.reducedMotion = this.motionQuery.matches;
        this.width = 0;
        this.height = 0;
        this.dpr = 1;
        this.raf = 0;
        this.lastTime = 0;
        this.frame = 0;
        this.rain = [];
        this.drops = [];
        this.trails = [];
        this.resizeTimer = 0;

        this.handleVisibility = this.handleVisibility.bind(this);
        this.handleResize = this.handleResize.bind(this);
        this.handleMotionChange = this.handleMotionChange.bind(this);
        this.tick = this.tick.bind(this);
    }

    init() {
        document.documentElement.dataset.weather = this.weather;
        document.body.dataset.weather = this.weather;
        this.root.dataset.weather = this.weather;
        this.resize();

        window.addEventListener('resize', this.handleResize, { passive: true });
        document.addEventListener('visibilitychange', this.handleVisibility);
        this.motionQuery.addEventListener?.('change', this.handleMotionChange);

        if (!this.reducedMotion && !document.hidden) this.start();
        const diagnostics = {
            type: this.weather,
            reducedMotion: this.reducedMotion,
            dpr: this.dpr,
        };
        Object.defineProperty(diagnostics, 'running', {
            enumerable: true,
            get: () => Boolean(this.raf),
        });
        window.__simpleTodoWeather = diagnostics;
    }

    handleResize() {
        window.clearTimeout(this.resizeTimer);
        this.resizeTimer = window.setTimeout(() => this.resize(), 100);
    }

    handleVisibility() {
        if (document.hidden) this.stop();
        else if (!this.reducedMotion) this.start();
    }

    handleMotionChange(event) {
        this.reducedMotion = event.matches;
        if (this.reducedMotion) {
            this.stop();
            this.drawFrame(performance.now(), 0);
        } else if (!document.hidden) {
            this.start();
        }
        if (window.__simpleTodoWeather) {
            window.__simpleTodoWeather.reducedMotion = this.reducedMotion;
        }
    }

    resize() {
        this.width = Math.max(1, window.innerWidth);
        this.height = Math.max(1, window.innerHeight);
        this.dpr = Math.min(window.devicePixelRatio || 1, DPR_LIMIT);
        this.backgroundCtx = fitCanvas(this.backgroundCanvas, this.width, this.height, this.dpr);
        this.atmosphereCtx = fitCanvas(this.atmosphereCanvas, this.width, this.height, this.dpr);
        this.glassCtx = fitCanvas(this.glassCanvas, this.width, this.height, this.dpr);

        if (this.weather === 'sunny') {
            drawSunnyBackground(this.backgroundCtx, this.width, this.height);
        } else {
            drawRainBackground(this.backgroundCtx, this.width, this.height);
            this.createRain();
            this.createDrops();
        }
        this.drawFrame(performance.now(), 0);
        if (window.__simpleTodoWeather) window.__simpleTodoWeather.dpr = this.dpr;
    }

    createRain() {
        const count = clamp(Math.round((this.width * this.height) / 10500), 70, 180);
        this.rain = Array.from({ length: count }, () => this.makeRainStreak(true));
    }

    makeRainStreak(initial = false) {
        const depth = Math.random();
        return {
            x: random(-this.width * 0.08, this.width * 1.08),
            y: initial ? random(-40, this.height + 40) : random(-120, -20),
            depth,
            length: 10 + depth * 38,
            speed: 250 + depth * 720,
            drift: 24 + depth * 42,
            alpha: 0.07 + depth * 0.25,
        };
    }

    createDrops() {
        const count = this.width < 620 ? 34 : clamp(Math.round(this.width / 23), 46, 78);
        this.drops = Array.from({ length: count }, (_, index) => this.makeDrop(true, index % 11 === 0));
        this.trails = [];
    }

    makeDrop(initial = false, forceLarge = false) {
        const large = forceLarge || Math.random() > 0.9;
        const width = large ? random(7, 12) : random(2.2, 7);
        const height = width * (large ? random(1.15, 1.55) : random(1.15, 1.65));
        return {
            x: random(width, this.width - width),
            y: initial ? random(-height, this.height + height) : random(-90, -height),
            width,
            height,
            speed: large ? random(5, 17) : random(0.08, 2.2),
            wobble: random(0, TAU),
            life: random(13, 38),
            alpha: random(0.58, 0.92),
            trailClock: 0,
        };
    }

    resetDrop(drop, forceLarge = false) {
        Object.assign(drop, this.makeDrop(false, forceLarge));
    }

    start() {
        if (this.raf) return;
        this.lastTime = performance.now();
        this.raf = requestAnimationFrame(this.tick);
    }

    stop() {
        if (this.raf) cancelAnimationFrame(this.raf);
        this.raf = 0;
        this.lastTime = 0;
    }

    tick(time) {
        if (document.hidden || this.reducedMotion) {
            this.raf = 0;
            return;
        }
        const dt = clamp((time - this.lastTime) / 1000, 0, 0.05);
        this.lastTime = time;
        this.drawFrame(time, dt);
        this.raf = requestAnimationFrame(this.tick);
    }

    drawFrame(time, dt) {
        this.frame += 1;
        if (this.weather === 'sunny') this.drawSunlight(time);
        else this.drawRain(time, dt);
    }

    drawSunlight(time) {
        const ctx = this.atmosphereCtx;
        const width = this.width;
        const height = this.height;
        const phase = time * 0.000075;
        ctx.clearRect(0, 0, width, height);
        ctx.save();
        ctx.globalCompositeOperation = 'screen';

        const sourceX = width * 0.92;
        const sourceY = -height * 0.04;
        for (let i = 0; i < 5; i += 1) {
            const slowShift = Math.sin(phase * (0.42 + i * 0.035) + i) * width * 0.012;
            const endX = width * (0.08 + i * 0.13) + slowShift;
            const beamWidth = width * (0.085 + i * 0.008);
            const opacity = 0.025 + (Math.sin(phase * 0.68 + i * 1.7) + 1) * 0.014;
            const gradient = ctx.createLinearGradient(sourceX, sourceY, endX, height);
            gradient.addColorStop(0, `rgba(255,247,205,${opacity * 1.8})`);
            gradient.addColorStop(0.48, `rgba(255,238,178,${opacity})`);
            gradient.addColorStop(1, 'rgba(255,229,162,0)');
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.moveTo(sourceX - beamWidth * 0.12, sourceY);
            ctx.lineTo(sourceX + beamWidth * 0.12, sourceY);
            ctx.lineTo(endX + beamWidth, height);
            ctx.lineTo(endX - beamWidth, height);
            ctx.closePath();
            ctx.fill();
        }

        const exposure = ctx.createLinearGradient(width, 0, 0, height);
        exposure.addColorStop(0, `rgba(255,244,196,${0.08 + Math.sin(phase * 0.42) * 0.012})`);
        exposure.addColorStop(0.52, 'rgba(255,239,190,.018)');
        exposure.addColorStop(1, 'rgba(208,241,238,0)');
        ctx.fillStyle = exposure;
        ctx.fillRect(0, 0, width, height);

        ctx.globalAlpha = 0.11;
        ctx.lineWidth = 1.2;
        for (let i = 0; i < 4; i += 1) {
            const y = height * (0.64 + i * 0.075);
            const shift = Math.sin(phase * 0.8 + i) * 12;
            ctx.strokeStyle = i % 2 ? 'rgba(255,214,141,.72)' : 'rgba(160,231,235,.62)';
            ctx.beginPath();
            ctx.moveTo(width * 0.03, y + shift);
            ctx.bezierCurveTo(width * 0.31, y - 14, width * 0.58, y + 18, width * 0.89, y - 4 + shift);
            ctx.stroke();
        }
        ctx.restore();

        const glass = this.glassCtx;
        glass.clearRect(0, 0, width, height);
        glass.save();
        glass.globalCompositeOperation = 'screen';
        glass.lineCap = 'round';
        for (let i = 0; i < 3; i += 1) {
            const y = height * (0.18 + i * 0.31);
            const drift = Math.sin(phase * 0.5 + i * 1.9) * width * 0.009;
            glass.lineWidth = 0.8 + i * 0.28;
            glass.strokeStyle = `rgba(225,250,247,${0.035 + i * 0.008})`;
            glass.beginPath();
            glass.moveTo(width * 0.06 + drift, y);
            glass.bezierCurveTo(
                width * 0.3, y - height * 0.035,
                width * 0.58, y + height * 0.04,
                width * 0.92 + drift, y - height * 0.018,
            );
            glass.stroke();

            glass.lineWidth = 0.55;
            glass.strokeStyle = `rgba(255,197,183,${0.018 + i * 0.005})`;
            glass.translate(1.1, -0.7);
            glass.stroke();
            glass.translate(-1.1, 0.7);
        }
        glass.restore();
    }

    updateRain(dt) {
        for (let i = 0; i < this.rain.length; i += 1) {
            const streak = this.rain[i];
            streak.y += streak.speed * dt;
            streak.x -= streak.drift * dt;
            if (streak.y - streak.length > this.height || streak.x < -80) {
                this.rain[i] = this.makeRainStreak(false);
                this.rain[i].x = random(0, this.width * 1.1);
            }
        }

        for (const trail of this.trails) trail.alpha -= dt * 0.055;
        this.trails = this.trails.filter(trail => trail.alpha > 0.015);

        for (const drop of this.drops) {
            const movement = drop.speed * dt;
            drop.wobble += dt * 0.24;
            drop.x += Math.sin(drop.wobble) * movement * 0.12;
            drop.y += movement;
            drop.life -= dt;
            drop.trailClock += movement;

            if (drop.width > 7 && drop.trailClock > 2.5) {
                this.trails.push({
                    x: drop.x + random(-0.8, 0.8),
                    y: drop.y - drop.height * 0.45,
                    length: random(8, 34),
                    width: clamp(drop.width * random(0.08, 0.18), 0.7, 2.2),
                    alpha: random(0.14, 0.28),
                });
                drop.trailClock = 0;
                if (this.trails.length > 130) this.trails.splice(0, this.trails.length - 130);
            }

            if (drop.life < 3) drop.alpha *= 0.992;
            if (drop.y - drop.height > this.height || drop.life <= 0 || drop.alpha < 0.13) {
                this.resetDrop(drop);
            }
        }

        if (this.frame % 12 === 0) this.mergeDrops();
    }

    mergeDrops() {
        for (let i = 0; i < this.drops.length; i += 1) {
            const first = this.drops[i];
            if (first.width < 6) continue;
            for (let j = i + 1; j < this.drops.length; j += 1) {
                const second = this.drops[j];
                const dx = first.x - second.x;
                const dy = first.y - second.y;
                const reach = (first.width + second.width) * 0.48;
                if (dx * dx + dy * dy < reach * reach) {
                    const area = first.width * first.width + second.width * second.width;
                    first.width = Math.min(14, Math.sqrt(area));
                    first.height = first.width * random(1.2, 1.5);
                    first.speed = Math.min(22, Math.max(first.speed, second.speed) * 1.08);
                    first.alpha = Math.min(0.95, Math.max(first.alpha, second.alpha) + 0.05);
                    this.resetDrop(second);
                    break;
                }
            }
        }
    }

    drawRain(time, dt) {
        if (dt > 0) this.updateRain(dt);
        const atmosphere = this.atmosphereCtx;
        const glass = this.glassCtx;
        const width = this.width;
        const height = this.height;
        atmosphere.clearRect(0, 0, width, height);

        const fogShift = Math.sin(time * 0.000055) * width * 0.035;
        const fog = atmosphere.createLinearGradient(0, height * 0.22, width, height * 0.7);
        fog.addColorStop(0, 'rgba(221,230,228,0)');
        fog.addColorStop(0.42, 'rgba(221,230,228,.075)');
        fog.addColorStop(0.7, 'rgba(193,207,207,.03)');
        fog.addColorStop(1, 'rgba(193,207,207,0)');
        atmosphere.fillStyle = fog;
        atmosphere.fillRect(fogShift - width * 0.08, 0, width * 1.16, height);

        atmosphere.save();
        atmosphere.lineCap = 'round';
        for (const streak of this.rain) {
            atmosphere.strokeStyle = `rgba(218,233,235,${streak.alpha})`;
            atmosphere.lineWidth = 0.45 + streak.depth * 1.1;
            atmosphere.beginPath();
            atmosphere.moveTo(streak.x, streak.y);
            atmosphere.lineTo(streak.x - streak.length * 0.18, streak.y + streak.length);
            atmosphere.stroke();
        }
        atmosphere.restore();

        glass.clearRect(0, 0, width, height);
        this.drawTrails(glass);
        for (const drop of this.drops) this.drawDrop(glass, drop);
    }

    drawTrails(ctx) {
        ctx.save();
        ctx.lineCap = 'round';
        for (const trail of this.trails) {
            const gradient = ctx.createLinearGradient(trail.x, trail.y - trail.length, trail.x, trail.y);
            gradient.addColorStop(0, 'rgba(230,241,241,0)');
            gradient.addColorStop(1, `rgba(226,239,240,${trail.alpha})`);
            ctx.strokeStyle = gradient;
            ctx.lineWidth = trail.width;
            ctx.beginPath();
            ctx.moveTo(trail.x, trail.y - trail.length);
            ctx.quadraticCurveTo(trail.x - 1.5, trail.y - trail.length * 0.45, trail.x, trail.y);
            ctx.stroke();
        }
        ctx.restore();
    }

    drawDrop(ctx, drop) {
        if (drop.width >= 7) {
            this.drawLensDrop(ctx, drop);
            return;
        }

        const alpha = drop.alpha;
        ctx.save();
        const shade = ctx.createLinearGradient(
            drop.x - drop.width * 0.55,
            drop.y - drop.height * 0.45,
            drop.x + drop.width * 0.48,
            drop.y + drop.height * 0.5,
        );
        shade.addColorStop(0, `rgba(248,254,255,${alpha * 0.46})`);
        shade.addColorStop(0.35, `rgba(214,232,233,${alpha * 0.05})`);
        shade.addColorStop(0.7, `rgba(39,69,78,${alpha * 0.08})`);
        shade.addColorStop(1, `rgba(20,43,52,${alpha * 0.34})`);
        dropletPath(ctx, drop);
        ctx.fillStyle = shade;
        ctx.fill();
        ctx.lineWidth = clamp(drop.width * 0.075, 0.55, 1.5);
        ctx.strokeStyle = `rgba(236,249,250,${alpha * 0.68})`;
        ctx.stroke();

        ctx.strokeStyle = `rgba(255,255,255,${alpha * 0.58})`;
        ctx.lineWidth = clamp(drop.width * 0.1, 0.65, 1.8);
        ctx.beginPath();
        ctx.moveTo(drop.x - drop.width * 0.25, drop.y - drop.height * 0.22);
        ctx.quadraticCurveTo(
            drop.x - drop.width * 0.42,
            drop.y + drop.height * 0.02,
            drop.x - drop.width * 0.22,
            drop.y + drop.height * 0.18,
        );
        ctx.stroke();

        ctx.strokeStyle = `rgba(19,42,50,${alpha * 0.36})`;
        ctx.lineWidth = clamp(drop.width * 0.08, 0.55, 1.45);
        ctx.beginPath();
        ctx.moveTo(drop.x + drop.width * 0.38, drop.y + drop.height * 0.02);
        ctx.quadraticCurveTo(
            drop.x + drop.width * 0.28,
            drop.y + drop.height * 0.43,
            drop.x - drop.width * 0.06,
            drop.y + drop.height * 0.48,
        );
        ctx.stroke();
        ctx.restore();
    }

    drawLensDrop(ctx, drop) {
        const alpha = drop.alpha;
        const sourceWidth = drop.width * 0.78;
        const sourceHeight = drop.height * 0.7;
        const sx = clamp(drop.x - sourceWidth * 0.5 + 2.2, 0, this.width - sourceWidth);
        const sy = clamp(drop.y - sourceHeight * 0.5 + 1.5, 0, this.height - sourceHeight);

        ctx.save();
        lensDropletPath(ctx, drop);
        ctx.clip();
        ctx.translate(drop.x, drop.y);
        ctx.scale(1, -1);
        ctx.globalAlpha = alpha * 0.72;
        ctx.drawImage(
            this.backgroundCanvas,
            sx * this.dpr,
            sy * this.dpr,
            sourceWidth * this.dpr,
            sourceHeight * this.dpr,
            -drop.width * 0.54,
            -drop.height * 0.53,
            drop.width * 1.08,
            drop.height * 1.06,
        );
        ctx.restore();

        ctx.save();
        const lensShade = ctx.createLinearGradient(
            drop.x - drop.width * 0.48,
            drop.y - drop.height * 0.42,
            drop.x + drop.width * 0.42,
            drop.y + drop.height * 0.46,
        );
        lensShade.addColorStop(0, `rgba(250,255,255,${alpha * 0.16})`);
        lensShade.addColorStop(0.36, 'rgba(225,239,240,0)');
        lensShade.addColorStop(0.72, `rgba(36,62,69,${alpha * 0.045})`);
        lensShade.addColorStop(1, `rgba(20,45,53,${alpha * 0.18})`);
        lensDropletPath(ctx, drop);
        ctx.fillStyle = lensShade;
        ctx.fill();
        ctx.lineWidth = clamp(drop.width * 0.045, 0.4, 0.72);
        ctx.strokeStyle = `rgba(20,46,54,${alpha * 0.22})`;
        ctx.stroke();

        ctx.lineCap = 'round';
        ctx.strokeStyle = `rgba(255,255,255,${alpha * 0.62})`;
        ctx.lineWidth = clamp(drop.width * 0.09, 0.62, 1.05);
        ctx.beginPath();
        ctx.moveTo(drop.x - drop.width * 0.27, drop.y - drop.height * 0.24);
        ctx.quadraticCurveTo(
            drop.x - drop.width * 0.38,
            drop.y - drop.height * 0.06,
            drop.x - drop.width * 0.29,
            drop.y + drop.height * 0.06,
        );
        ctx.stroke();

        ctx.fillStyle = `rgba(255,255,255,${alpha * 0.52})`;
        ctx.beginPath();
        ctx.ellipse(
            drop.x - drop.width * 0.17,
            drop.y - drop.height * 0.28,
            clamp(drop.width * 0.055, 0.45, 0.8),
            clamp(drop.height * 0.045, 0.55, 0.95),
            -0.4,
            0,
            TAU,
        );
        ctx.fill();

        ctx.strokeStyle = `rgba(12,35,43,${alpha * 0.32})`;
        ctx.lineWidth = clamp(drop.width * 0.06, 0.48, 0.82);
        ctx.beginPath();
        ctx.moveTo(drop.x + drop.width * 0.34, drop.y + drop.height * 0.08);
        ctx.quadraticCurveTo(
            drop.x + drop.width * 0.22,
            drop.y + drop.height * 0.4,
            drop.x - drop.width * 0.08,
            drop.y + drop.height * 0.43,
        );
        ctx.stroke();

        ctx.strokeStyle = `rgba(229,244,244,${alpha * 0.24})`;
        ctx.lineWidth = 0.55;
        ctx.beginPath();
        ctx.moveTo(drop.x - drop.width * 0.13, drop.y + drop.height * 0.31);
        ctx.quadraticCurveTo(
            drop.x + drop.width * 0.05,
            drop.y + drop.height * 0.39,
            drop.x + drop.width * 0.19,
            drop.y + drop.height * 0.29,
        );
        ctx.stroke();
        ctx.restore();
    }
}

export function initWeatherScene() {
    const root = document.getElementById('weather-scene');
    if (!root) return null;
    const scene = new WeatherScene(root, chooseWeather());
    scene.init();
    return scene;
}
