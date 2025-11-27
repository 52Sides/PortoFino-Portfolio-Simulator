/* eslint-disable @typescript-eslint/no-explicit-any */
import { vi } from 'vitest';

// @ts-expect-error TS does not know that 'g' exists on globalThis
(globalThis as any).g = globalThis;

// --- Fix Plotly.js canvas + Blob issues in JSDOM ---
Object.defineProperty(global.HTMLCanvasElement.prototype, 'getContext', {
  value: () => ({
    fillRect: () => {},
    clearRect: () => {},
    getImageData: () => ({ data: [] }),
    putImageData: () => {},
    createImageData: () => [],
    setTransform: () => {},
    drawImage: () => {},
    save: () => {},
    fillText: () => {},
    restore: () => {},
    beginPath: () => {},
    moveTo: () => {},
    lineTo: () => {},
    closePath: () => {},
    stroke: () => {},
    translate: () => {},
    scale: () => {},
    rotate: () => {},
    arc: () => {},
    fill: () => {},
    measureText: () => ({ width: 0 }),
    transform: () => {},
    rect: () => {},
    clip: () => {},
  }),
});

global.URL.createObjectURL = vi.fn();

// @ts-expect-error Overriding Blob for JSDOM compatibility
global.Blob = class extends (global as any).Blob {};

import '@testing-library/jest-dom';
