import {defineConfig} from '@playwright/test';
export default defineConfig({
  testDir: '.',
  testMatch: 'standalone-notes.spec.mjs',
  timeout: 30_000,
  workers: 1,
  reporter: 'list',
  use: {browserName: 'chromium', offline: true, trace: 'retain-on-failure'},
  projects: [
    {name: 'standalone-desktop', use: {viewport: {width: 1280, height: 900}}},
    {name: 'standalone-mobile', use: {viewport: {width: 390, height: 844}}},
  ],
});
