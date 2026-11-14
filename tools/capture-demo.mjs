import console from 'node:console';
import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';

const out=path.resolve('output/demo');
await fs.mkdir(path.join(out,'capture'),{recursive:true});
const browser=await chromium.launch({headless:true,args:['--enable-webgl','--ignore-gpu-blocklist']});
const context=await browser.newContext({viewport:{width:1600,height:900},recordVideo:{dir:path.join(out,'capture'),size:{width:1600,height:900}},deviceScaleFactor:1});
const page=await context.newPage();
const started=Date.now(); const marks={};
const mark=async(name)=>{marks[name]=(Date.now()-started)/1000;await page.screenshot({path:path.join(out,'capture',name+'.png')});console.log(name,marks[name]);};
const click=async(name)=>page.getByRole('button',{name,exact:true}).click();
const wait=async(ms=1000)=>page.waitForTimeout(ms);
try {
 await page.goto('http://127.0.0.1:5174/');
 await page.locator('.world-loading').waitFor({state:'hidden',timeout:90000});
 await wait(1800);await mark('arrival');await wait(2500);
 if(await page.getByRole('button',{name:/Skip arrival/}).count())await page.getByRole('button',{name:/Skip arrival/}).click();
 await page.locator('.world-loading').waitFor({state:'hidden',timeout:90000});await wait(1800);
 await mark('walk');await page.keyboard.down('w');await wait(1600);await page.keyboard.up('w');await page.keyboard.press('e');await wait(1200);
 if(await page.getByRole('button',{name:'Continue',exact:true}).count()===0){await click('Find Dr. Maya');await click('Talk to Dr. Maya');}
 await mark('crew');await click('Continue');await page.getByRole('button',{name:/Find Alex/}).click();await click('Talk to Alex');await click('Continue');
 await page.getByRole('button',{name:/Find power station/}).click();await wait(1700);await mark('power');
 await page.getByRole('button',{name:/GO: Power station/}).click();await wait(1000);await mark('allocate');
 await page.getByRole('button',{name:/^Use stored oxygen/}).click();await wait(1800);await mark('allocation-stored');
 await page.getByRole('button',{name:/^Produce oxygen/}).click();await wait(1300);await click('Keep this plan');
 const guide=page.getByRole('region',{name:'Mission guide',exact:true});
 await guide.locator('button.primary').click();await click('Water tank checked');
 await guide.locator('button.primary').click();await click('Keep this plan');
 await guide.locator('button.primary').click();await click('Keep this plan');
 await click('Plan');await wait(900);await mark('plan');await wait(1600);
 await click('Advance turn 1');await wait(1600);await mark('result');await wait(2500);
 await click('Science library');await wait(1000);await mark('science');await wait(2000);
 await page.screenshot({path:path.join(out,'capture','science-final.png')});
}catch(e){console.error(e);await page.screenshot({path:path.join(out,'capture','error.png')});await fs.writeFile(path.join(out,'capture','page.txt'),await page.locator('body').innerText());}
await fs.writeFile(path.join(out,'capture','marks.json'),JSON.stringify(marks,null,2));
const video=page.video();await context.close();await video.saveAs(path.join(out,'capture','gameplay.webm'));await browser.close();console.log('Saved gameplay recording');
