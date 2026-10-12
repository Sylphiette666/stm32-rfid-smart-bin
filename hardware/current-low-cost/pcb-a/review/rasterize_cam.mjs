import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const r=createRequire('C:/Users/35462/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/anchor.js');
const sharp=r('sharp');
for(const name of ['cam-top','cam-bottom','cam-top-copper','cam-bottom-copper']){
  await sharp(path.join(here,name+'.svg'),{density:500}).flatten({background:'#FFFFFF'}).resize(2200,2200,{fit:'inside'}).png().toFile(path.join(here,name+'.png'));
}
console.log('Four actual Gerber CAM SVGs rasterized.');
