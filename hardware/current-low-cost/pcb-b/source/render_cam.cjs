// Run with the bundled Node runtime and NODE_PATH set to its package directory.
const sharp = require('sharp');
const path = require('path');
const root = path.resolve(__dirname, '..');
Promise.all(['top', 'bottom'].map(side => {
  let pipeline = sharp(path.join(root, `renders/cam-${side}-plain.svg`), {density: 140});
  if (side === 'bottom') pipeline = pipeline.flop();
  return pipeline.flatten({background: '#fff'}).png().toFile(path.join(root, `renders/cam-${side}.png`));
})).then(() => console.log('Actual Gerber renders exported; bottom viewed from underside.'));
