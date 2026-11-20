// ==UserScript==
// @name         GitHub Contribution Calendar - Fast Random Blinker
// @namespace    https://github.com/raviraj940
// @version      2.0.0
// @description  Smooth, fast, random glowing/blinking animation on GitHub's native contribution calendar for @raviraj940
// @author       Ravi Raj
// @match        https://github.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // Config: Fast random blinking animation settings
  const CONFIG = {
    minActive: 2,         // Min squares blinking together
    maxActive: 8,         // Max squares blinking together
    minDuration: 150,     // ms (fast blink duration)
    maxDuration: 300,     // ms
    minDelay: 50,         // ms (delay between random cycles)
    maxDelay: 200,        // ms
    glowColors: [
      '#00ff88',
      '#56ff9f',
      '#39d353',
      '#7ee787',
      '#b9ffcb',
      '#ffffff'
    ]
  };

  // Skip if user prefers reduced motion
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  // Inject CSS styles for both SVG <rect> and HTML <td>/<div> calendar cells
  const STYLE_ID = 'gh-calendar-blinker-styles';
  let styleEl = document.getElementById(STYLE_ID);
  if (!styleEl) {
    styleEl = document.createElement('style');
    styleEl.id = STYLE_ID;
    styleEl.textContent = `
      @keyframes ghFastBlinkSvg {
        0% {
          filter: brightness(1) drop-shadow(0 0 0px transparent);
          transform: scale(1);
        }
        50% {
          filter: brightness(2) drop-shadow(0 0 8px #00ff88);
          transform: scale(1.22);
        }
        100% {
          filter: brightness(1) drop-shadow(0 0 0px transparent);
          transform: scale(1);
        }
      }

      @keyframes ghFastBlinkHtml {
        0% {
          filter: brightness(1) drop-shadow(0 0 0px transparent);
          transform: scale(1);
        }
        50% {
          filter: brightness(2.2) drop-shadow(0 0 10px #00ff88);
          transform: scale(1.25);
          outline: 1.5px solid #00ff88;
        }
        100% {
          filter: brightness(1) drop-shadow(0 0 0px transparent);
          transform: scale(1);
          outline: none;
        }
      }

      rect.gh-blinking-cell {
        transform-box: fill-box !important;
        transform-origin: center center !important;
        animation-name: ghFastBlinkSvg !important;
        animation-timing-function: ease-in-out !important;
        animation-iteration-count: 1 !important;
      }

      td.gh-blinking-cell,
      div.gh-blinking-cell {
        position: relative !important;
        z-index: 5 !important;
        animation-name: ghFastBlinkHtml !important;
        animation-timing-function: ease-in-out !important;
        animation-iteration-count: 1 !important;
      }
    `;
    (document.head || document.documentElement).appendChild(styleEl);
  }

  let activeTimer = null;
  let isRunning = true;

  // Locate all active calendar day elements (supports all GitHub web layouts)
  function findCells() {
    // Selectors covering modern table-based and legacy SVG-based GitHub calendars
    const selectors = [
      'table.ContributionCalendar-grid td.ContributionCalendar-day',
      '.js-calendar-graph-table rect.ContributionCalendar-day',
      '.ContributionCalendar-grid [data-date]',
      '.js-yearly-contributions [data-level]',
      '[data-testid="contribution-calendar-cell"]'
    ];

    let found = [];
    for (const sel of selectors) {
      const nodes = Array.from(document.querySelectorAll(sel));
      if (nodes.length > 0) {
        found = nodes;
        break;
      }
    }

    if (found.length === 0) return [];

    // Filter to active contribution days (data-level > 0 or has background color)
    const active = found.filter(el => {
      const level = el.getAttribute('data-level');
      if (level && level !== '0') return true;
      // In table cells, check inline or computed style
      const bg = el.style.backgroundColor || el.getAttribute('fill') || '';
      return bg && !bg.includes('#161b22') && !bg.includes('rgba(255, 255, 255, 0.05)');
    });

    return active.length >= 3 ? active : found;
  }

  function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function blinkCell(cell) {
    if (!cell || !isRunning) return;

    const duration = randomInt(CONFIG.minDuration, CONFIG.maxDuration);
    const glow = CONFIG.glowColors[Math.floor(Math.random() * CONFIG.glowColors.length)];

    cell.style.animationDuration = duration + 'ms';

    const isSvg = cell.tagName.toLowerCase() === 'rect';
    const originalFill = cell.getAttribute('fill');
    const originalBg = cell.style.backgroundColor;

    if (isSvg) {
      cell.setAttribute('fill', glow);
    } else {
      cell.style.backgroundColor = glow;
    }

    cell.classList.add('gh-blinking-cell');

    setTimeout(() => {
      cell.classList.remove('gh-blinking-cell');
      cell.style.animationDuration = '';
      if (isSvg) {
        if (originalFill) cell.setAttribute('fill', originalFill);
        else cell.removeAttribute('fill');
      } else {
        cell.style.backgroundColor = originalBg;
      }
    }, duration);
  }

  function loop() {
    if (!isRunning) return;

    const cells = findCells();
    if (cells.length > 0) {
      const count = randomInt(CONFIG.minActive, Math.min(CONFIG.maxActive, cells.length));
      // Shuffle & pick distinct
      const pool = cells.slice().sort(() => 0.5 - Math.random());
      const selected = pool.slice(0, count);

      selected.forEach(c => blinkCell(c));
    }

    const nextDelay = randomInt(CONFIG.minDelay, CONFIG.maxDelay);
    activeTimer = setTimeout(loop, nextDelay);
  }

  function start() {
    clearTimeout(activeTimer);
    isRunning = true;
    loop();
  }

  function stop() {
    isRunning = false;
    clearTimeout(activeTimer);
  }

  // Handle visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
    else start();
  });

  // Handle GitHub Turbo / SPA page transitions
  document.addEventListener('turbo:load', start);
  document.addEventListener('pjax:end', start);

  // Watch for dynamic DOM rendering of the calendar
  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.addedNodes.length > 0) {
        if (document.querySelector('.js-calendar-graph, .ContributionCalendar-grid, .js-yearly-contributions')) {
          start();
          break;
        }
      }
    }
  });

  observer.observe(document.body || document.documentElement, {
    childList: true,
    subtree: true
  });

  // Initial trigger
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
