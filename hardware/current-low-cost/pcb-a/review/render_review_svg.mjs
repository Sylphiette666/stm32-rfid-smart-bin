import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const r=createRequire('C:/Users/35462/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/anchor.js');
const sharp=r('sharp');
for(const n of ['board-top-copper','board-bottom-solder','board-assembly-top']){
  await sharp(path.join(here,'..','renders',n+'.svg'),{density:500}).flatten({background:'#FFFFFF'}).resize(2200,2200,{fit:'inside'}).png().toFile(path.join(here,n+'.png'));
}
console.log('Three real PCB SVG renders rasterized for review.');
