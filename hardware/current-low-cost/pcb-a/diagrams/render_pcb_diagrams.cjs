const fs=require('fs');const path=require('path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'C:/Users/35462/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
for(const name of ['45_pcb_top','46_pcb_bottom']){const page=await browser.newPage({viewport:{width:1800,height:2250},deviceScaleFactor:1});
await page.setContent('<html><body style="margin:0">'+fs.readFileSync(path.join(__dirname,name+'.svg'),'utf8')+'</body></html>');await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:path.join(__dirname,name+'.png')});await page.close();}
await browser.close();})();
