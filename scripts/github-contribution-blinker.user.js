// ==UserScript==
// @name         GitHub Contribution Calendar - Fast Random Blinker
// @namespace    https://github.com/raviraj940
// @version      1.0.0
// @description  Smooth, fast, random blinking animation on GitHub's native contribution calendar for @raviraj940
// @author       Ravi Raj
// @match        https://github.com/raviraj940*
// @match        https://github.com/users/raviraj940/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // Animation configuration matching exact requirements
  const CONFIG = {
    minActive: 2,         // Min squares blinking simultaneously
    maxActive: 8,         // Max squares blinking simultaneously
    minDuration: 150,     // ms (fast blink duration)
    maxDuration: 300,     // ms
    minDelay: 50,         // ms (delay between activation bursts)
    maxDelay: 200,        // ms
    glowColors: [
      '#56ff9f',
      '#00ff88',
      '#7ee787',
      '#39d353',
      '#b9ffcb'
    ]
  };

  // Check prefers-reduced-motion
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  // Inject animation CSS
  const style = document.createElement('style');
  style.id = 'gh-calendar-blinker-styles';
  style.textContent = `
    @keyframes ghBlinkGlow {
      0% {
        filter: brightness(1) drop-shadow(0 0 0px transparent);
        transform: scale(1);
      }
      50% {
        filter: brightness(1.7) drop-shadow(0 0 6px #00ff88);
        transform: scale(1.15);
      }
      100% {
        filter: brightness(1) drop-shadow(0 0 0px transparent);
        transform: scale(1);
      }
    }

    .gh-blinking-cell {
      animation-name: ghBlinkGlow !important;
      animation-timing-function: ease-in-out !important;
      animation-iteration-count: 1 !important;
      transform-origin: center center !important;
      z-index: 10 !important;
    }
  `;
  document.head.appendChild(style);

  let activeTimeouts = new Set();
  let isRunning = true;

  function findContributionCells() {
    // Target GitHub's native contribution calendar squares (SVG rects or HTML td/buttons)
    const selectors = [
      '.js-calendar-graph-table rect.ContributionCalendar-day',
      '.ContributionCalendar-grid td.ContributionCalendar-day',
      'table.ContributionCalendar-grid [data-date]',
      '.js-yearly-contributions [data-level]:not([data-level="0"])',
      'rect.ContributionCalendar-day[data-level]:not([data-level="0"])'
    ];

    for (const sel of selectors) {
      const nodes = Array.from(document.querySelectorAll(sel));
      // Prefer active (green) squares, fallback to all if needed
      const activeNodes = nodes.filter(n => {
        const level = n.getAttribute('data-level');
        return level && level !== '0';
      });
      if (activeNodes.length >= 3) {
        return activeNodes;
      }
      if (nodes.length >= 10) {
        return nodes;
      }
    }
    return [];
  }

  function randomBetween(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function blinkSquare(cell) {
    if (!isRunning || !cell) return;

    const duration = randomBetween(CONFIG.minDuration, CONFIG.maxDuration);
    const color = CONFIG.glowColors[Math.floor(Math.random() * CONFIG.glowColors.length)];

    cell.style.animationDuration = `${duration}ms`;
    cell.classList.add('gh-blinking-cell');

    const tid = setTimeout(() => {
      cell.classList.remove('gh-blinking-cell');
      cell.style.animationDuration = '';
      activeTimeouts.delete(tid);
    }, duration);

    activeTimeouts.add(tid);
  }

  function animationLoop() {
    if (!isRunning) return;

    const cells = findContributionCells();
    if (cells.length > 0) {
      const count = randomBetween(CONFIG.minActive, Math.min(CONFIG.maxActive, cells.length));
      // Pick random distinct cells
      const shuffled = cells.slice().sort(() => 0.5 - Math.random());
      const selected = shuffled.slice(0, count);

      selected.forEach(cell => blinkSquare(cell));
    }

    const nextDelay = randomBetween(CONFIG.minDelay, CONFIG.maxDelay);
    const tid = setTimeout(animationLoop, nextDelay);
    activeTimeouts.add(tid);
  }

  // Handle page visibility
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      isRunning = false;
      activeTimeouts.forEach(clearTimeout);
      activeTimeouts.clear();
    } else {
      isRunning = true;
      animationLoop();
    }
  });

  // Start after GitHub finishes rendering the contribution graph
  function init() {
    const calendar = document.querySelector('.js-yearly-contributions, .js-calendar-graph');
    if (calendar) {
      animationLoop();
    } else {
      // Retry in case GitHub loaded asynchronously
      let retries = 0;
      const checker = setInterval(() => {
        retries++;
        if (document.querySelector('.js-yearly-contributions, .js-calendar-graph') || retries > 10) {
          clearInterval(checker);
          animationLoop();
        }
      }, 500);
    }
  }

  init();
})();
