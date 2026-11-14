import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';
const dir='output/demo/capture';
const browser=await chromium.launch({headless:true,args:['--enable-webgl','--ignore-gpu-blocklist']});
const page=await browser.newPage({viewport:{width:1600,height:900}});
const click=async(name)=>page.getByRole('button',{name,exact:true}).click();
const snap=async(name)=>{await page.waitForTimeout(700);await page.screenshot({path:`${dir}/${name}.png`});console.log(name)};
try{
 await page.goto('http://127.0.0.1:5174/');
 await page.locator('.world-loading').waitFor({state:'hidden',timeout:90000});
 await page.getByRole('button',{name:/Skip arrival/}).click();
 await page.locator('.world-loading').waitFor({state:'hidden',timeout:90000});
 await click('Settings');await page.getByLabel('Guided objectives').uncheck();await click('Close dialog');
 await click('Overview');await page.waitForTimeout(2400);await snap('overview');
 await click('Plan');await snap('plan');
 await page.getByRole('dialog').getByRole('button',{name:/^Use stored oxygen/}).click();await snap('plan-stored');
 await page.getByRole('dialog').getByRole('button',{name:/^Produce oxygen/}).click();
 await page.getByRole('dialog').getByRole('button',{name:/^Power growing lights/}).click();
 await page.getByRole('dialog').getByRole('button',{name:/^Lab research/}).click();await snap('plan-selected');
 await click('Advance turn 1');await snap('result');
 await click('Science library');await snap('science');
 const detail=page.locator('details').filter({has:page.getByText('Explore the evidence & original source',{exact:true})});
 await page.getByText('Explore the evidence & original source',{exact:true}).nth(1).click();await snap('science-detail');
 await fs.writeFile(`${dir}/result-state.json`,await page.evaluate(()=>localStorage.getItem('marsastro.save.v1')));
}catch(e){console.error(e);await fs.writeFile(`${dir}/details-error.txt`,await page.locator('body').innerText());await snap('details-error');process.exitCode=1;}
finally{await browser.close()}
