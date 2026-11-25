'use strict';

const fs=require('fs');
const path=require('path');
const root=path.resolve(__dirname,'../..');
const css=fs.readFileSync(path.join(root,'geometry-web/workspace-height.css'),'utf8');
const moduleSource=fs.readFileSync(path.join(root,'geometry-web/canvas_sections/P1231.js'),'utf8');
const begin='/* R123H_NARROW_WORKSPACE_STRIP_BEGIN';
const end='/* R123H_NARROW_WORKSPACE_STRIP_END */';
const start=css.indexOf(begin),finish=css.indexOf(end,start);
const withdrawn=process.argv.includes('--withdraw');
const block=start>=0&&finish>=0?css.slice(start,finish+end.length):'';
const candidate=withdrawn?'':block;
const clauses=[
  /@media \(min-width: 561px\) and \(max-width: 680px\)/,
  /overflow-x: auto/,
  /overflow-y: hidden/,
  /min-width: max-content/,
  /overflow: visible/,
  /height: 56px/
];
const okay=start>=0&&finish>start&&clauses.every(pattern=>pattern.test(candidate))&&
  moduleSource.includes('R123H_FACE_HELP_REACH')&&moduleSource.includes('#feSelectionSummaryHelp');
if(!okay){
  console.error('AssertionError: R123H_FACE_HELP_REACH narrow workspace strip is absent or incomplete');
  process.exit(1);
}
console.log('R123H_FACE_HELP_REACH narrow workspace strip contract OK');
