/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable no-var */
import { vi } from 'vitest';

// @ts-ignore
const g: any = globalThis;


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

// @ts-ignore
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
global.Blob = class extends (global as any).Blob {};



import '@testing-library/jest-dom'
