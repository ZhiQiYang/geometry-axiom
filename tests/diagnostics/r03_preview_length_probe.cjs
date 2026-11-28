'use strict';
/* Read-only browser measurements. A cell containing the right text can still
 * wrap or clip it: keep the value, text line boxes, and containing cell apart. */
function previewLengthProbe() {
  const region=document.querySelector('.ft-results');
  if(!region)return {exists:false,rows:[]};
  const table=region.querySelector('table'),scroll=table.closest('.pf-table-scroll');
  // The pre-fix table has no marker. Locate its existing semantic heading so
  // T-only reaches the actual line-box assertion, never a setup TypeError.
  const headings=[...table.querySelectorAll('thead th')];
  const lengthIndex=headings.findIndex(cell=>cell.textContent.trim()==='長度');
  const box=r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height});
  const rows=[...table.querySelectorAll('[data-ft-member-row]')].map(row=>{
    const cell=row.querySelector('[data-ft-length]')||row.cells.item(lengthIndex),range=document.createRange();
    if(!cell)return {index:Number(row.dataset.ftMemberRow),text:'',cells:[...row.cells].map(item=>item.textContent),cell:null,lines:[],member:null};
    range.selectNodeContents(cell);
    const member=region.querySelector('[data-ft-member="'+row.dataset.ftMemberRow+'"]');
    return {index:Number(row.dataset.ftMemberRow),text:cell.textContent.trim(),
      cells:[...row.cells].map(item=>item.textContent),cell:box(cell.getBoundingClientRect()),
      lines:[...range.getClientRects()].filter(r=>r.width>0&&r.height>0).map(box),
      member:member?{width:Number(member.getAttribute('width')),height:Number(member.getAttribute('height'))}:null,
      whiteSpace:getComputedStyle(cell).whiteSpace};
  });
  return {exists:true,rows,table:box(table.getBoundingClientRect()),
    scroll:{width:scroll.clientWidth,contentWidth:scroll.scrollWidth},viewport:{width:innerWidth,height:innerHeight}};
}
function lengthValuesReady(probe,count,fourDigit) {
  return probe.exists===true&&probe.rows.length===count&&probe.rows.every(row=>
    /^\d+$/.test(row.text)&&row.cells.length===4&&row.member&&
    Number(row.text)===Math.max(row.member.width,row.member.height))&&
    probe.rows.filter(row=>row.text===fourDigit).length>0;
}
function lengthSingleLine(probe) {
  return probe.exists===true&&probe.rows.length>0&&probe.rows.every(row=>row.lines.length===1);
}
function lengthUnclipped(probe) {
  return probe.exists===true&&probe.rows.length>0&&probe.scroll.contentWidth<=probe.scroll.width+1&&
    probe.rows.every(row=>row.lines.length>0&&row.lines.every(line=>
      line.left>=row.cell.left-1&&line.right<=row.cell.right+1&&
      line.top>=row.cell.top-1&&line.bottom<=row.cell.bottom+1));
}
module.exports={previewLengthProbe,lengthValuesReady,lengthSingleLine,lengthUnclipped};
