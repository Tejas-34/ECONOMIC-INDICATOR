import '@testing-library/jest-dom';

// In JSDOM test environments, ensure window.AbortController matches Node's fetch implementation
if (typeof window !== 'undefined' && (globalThis as any).AbortController) {
  window.AbortController = (globalThis as any).AbortController;
  window.AbortSignal = (globalThis as any).AbortSignal;
}

