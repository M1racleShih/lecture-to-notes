import {test, expect} from '@playwright/test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

let directory, fileURL;
test.beforeAll(() => {
  directory=fs.mkdtempSync(path.join(os.tmpdir(), 'standalone-lecture-'));
  let html=fs.readFileSync(new URL('../skills/lecture-to-notes/assets/notes-template.html',import.meta.url),'utf8');
  const content='<h2 id="mechanism">如何独立复核</h2><p>先独立计算，再比较差异，最后由人核对业务前提。</p>'+
    '<div data-stepper aria-label="复核过程"><ol>'+
    '<li data-step>两个 AI 独立计算。</li><li data-step>第三个 AI 比较差异。</li><li data-step>人核对业务前提。</li></ol>'+
    '<div data-controls hidden><button type="button" data-action="previous">上一步</button>'+
    '<button type="button" data-action="play">播放</button><button type="button" data-action="pause">暂停</button>'+
    '<button type="button" data-action="next">下一步</button><button type="button" data-action="reset">重置</button>'+
    '<output aria-live="polite"></output></div></div>'+
    '<h2 id="summary">总结</h2><p>独立复核提供证据，交付决定仍需明确责任。</p>';
  const values={TITLE:'交互讲义合成测试', ORGANIZED_DATE:'2026-10-23', READER_OUTCOME:'解释复核与决策的分工',
    UPLOADER:'合成测试来源', PUBLISHED_DATE:'2026-10-21', DURATION:'18 分钟',
    VIDEO_URL:'https://example.com/video', COVER_ALT:'合成测试封面', CONTENT:content};
  for(const [key,value] of Object.entries(values))html=html.replaceAll('{{'+key+'}}',value);
  const svg='<svg xmlns="http://www.w3.org/2000/svg" width="640" height="180"><rect width="640" height="180" fill="#dfecdf"/></svg>';
  html=html.replace('src="cover.jpg"','src="data:image/svg+xml,'+encodeURIComponent(svg)+'"');
  const destination=path.join(directory,'notes.html');
  fs.writeFileSync(destination,html);fileURL=pathToFileURL(destination).href;
});
test.afterAll(()=>fs.rmSync(directory,{recursive:true,force:true}));

test('file URL works offline, navigation and print retain meaning',async({page})=>{
  const errors=[],network=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url());});
  await page.goto(fileURL);
  await expect(page.getByRole('heading',{level:1})).toHaveText('交互讲义合成测试');
  await page.getByRole('navigation').getByRole('link',{name:'如何独立复核'}).click();
  await expect(page).toHaveURL(/#mechanism$/);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  await page.emulateMedia({media:'print'});
  await expect(page.locator('[data-controls]')).not.toBeVisible();
  for(const step of await page.locator('[data-step]').all())await expect(step).toBeVisible();
  expect(errors).toEqual([]);expect(network).toEqual([]);
});

test('manual controls, playback, pause, reset and endpoints',async({page})=>{
  await page.goto(fileURL);
  const player=page.locator('[data-stepper]');
  const previous=page.getByRole('button',{name:'上一步'}),next=page.getByRole('button',{name:'下一步'});
  await expect(player).toHaveAttribute('data-index','0');
  await expect(previous).toBeDisabled();
  await next.focus();await page.keyboard.press('Enter');
  await expect(player).toHaveAttribute('data-index','1');
  await page.getByRole('button',{name:'重置'}).click();
  await page.getByRole('button',{name:'播放'}).click();
  await expect(player).toHaveAttribute('data-playing','true');
  await expect(player).toHaveAttribute('data-index','1',{timeout:4000});
  await page.getByRole('button',{name:'暂停'}).click();
  await expect(player).toHaveAttribute('data-playing','false');
  const stopped=await player.getAttribute('data-index');
  await page.waitForTimeout(2000);
  await expect(player).toHaveAttribute('data-index',stopped);
  await next.click();
  await expect(player).toHaveAttribute('data-index','2');
  await expect(next).toBeDisabled();
  await expect(page.getByRole('button',{name:'播放'})).toBeDisabled();
  await previous.click();
  await expect(player).toHaveAttribute('data-index','1');
  await page.getByRole('button',{name:'重置'}).click();
  await expect(player).toHaveAttribute('data-index','0');
});

test('reduced motion preserves manual use without playback',async({page})=>{
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto(fileURL);
  await expect(page.getByRole('button',{name:'播放'})).toBeDisabled();
  await expect(page.locator('output')).toContainText('已减少动态效果');
  await page.getByRole('button',{name:'下一步'}).click();
  await expect(page.locator('[data-stepper]')).toHaveAttribute('data-index','1');
  await expect(page.locator('[data-stepper]')).toHaveAttribute('data-playing','false');
});

test('JavaScript-disabled reading retains all explanations',async({browser},testInfo)=>{
  const context=await browser.newContext({javaScriptEnabled:false,offline:true,viewport:testInfo.project.use.viewport});
  try{
    const page=await context.newPage();await page.goto(fileURL);
    await expect(page.getByRole('heading',{name:'如何独立复核'})).toBeVisible();
    for(const step of await page.locator('[data-step]').all())await expect(step).toBeVisible();
    await expect(page.locator('[data-controls]')).not.toBeVisible();
    await expect(page.locator('main')).toContainText('独立复核提供证据');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  }finally{await context.close();}
});
