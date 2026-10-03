/* Self-authored public drawings. Coordinates here are independent test oracles. */
'use strict';
const zlib=require('node:zlib');
const shapes=[
  {name:'rectangle',points:[[30,30],[230,30],[230,150],[30,150]],inside:[[32,32],[228,32],[228,148],[32,148]]},
  {name:'l',points:[[30,30],[230,30],[230,80],[130,80],[130,150],[30,150]],inside:[[32,32],[228,32],[228,78],[128,78],[128,148],[32,148]]},
  {name:'notch',points:[[30,30],[230,30],[230,150],[170,150],[170,110],[130,110],[130,150],[30,150]],inside:[[32,32],[228,32],[228,148],[172,148],[172,108],[128,108],[128,148],[32,148]]}
];
function pdf() {
  const objects=['<< /Type /Catalog /Pages 2 0 R >>',''],kids=[];
  const add=o=>{objects.push(o);return objects.length;};
  const font=add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  for(let page=0;page<4;page++) {
    const shape=shapes[page%3],points=shape.points.map(p=>[p[0]+3,191-p[1]]); // reversed by explicit CTM below
    const stream=`q 1 0 0 1 7 9 cm 0 0 0 RG 4 w ${points.map((p,i)=>p.join(' ')+(i?' l':' m')).join(' ')} h S Q\n`+
      '0 0 0 RG .5 w 15 185 m 280 185 l S 15 15 m 15 185 l S\n'+
      '[2 2] 0 d .4 w 45 25 m 45 165 l S [] 0 d\n'+
      '2 w 180 80 m 180 90 190 100 200 100 c S\n'+
      `BT /F1 10 Tf 80 125 Td (${shape.name} - self authored) Tj ET\n`;
    const content=add(`<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}endstream`);
    kids.push(add(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 210] /CropBox [10 10 290 200] /Rotate ${page===3?90:0} /Resources << /Font << /F1 ${font} 0 R >> >> /Contents ${content} 0 R >>`));
  }
  // A scan-only PDF, using the same rectangle. No hidden vector room path.
  const w=280,h=190,rgb=Buffer.alloc(w*h*3,255);
  const paint=b=>{for(let y=b[1];y<b[3];y++)for(let x=b[0];x<b[2];x++)rgb.fill(0,(y*w+x)*3,(y*w+x)*3+3);};
  for(let i=0;i<shapes[0].points.length;i++){const a=shapes[0].points[i],b=shapes[0].points[(i+1)%4];paint([Math.min(a[0],b[0])-2,Math.min(a[1],b[1])-2,Math.max(a[0],b[0])+2,Math.max(a[1],b[1])+2]);}
  paint([15,10,265,11]);paint([80,65,88,66]);
  const compressed=zlib.deflateSync(rgb),image=add(Buffer.concat([Buffer.from(`<< /Type /XObject /Subtype /Image /Width ${w} /Height ${h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length ${compressed.length} >>\nstream\n`),compressed,Buffer.from('\nendstream')]));
  const stream='q 280 0 0 190 10 10 cm /Scan Do Q\n',content=add(`<< /Length ${stream.length} >>\nstream\n${stream}endstream`);
  kids.push(add(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 210] /CropBox [10 10 290 200] /Resources << /XObject << /Scan ${image} 0 R >> >> /Contents ${content} 0 R >>`));
  objects[1]=`<< /Type /Pages /Kids [${kids.map(k=>k+' 0 R').join(' ')}] /Count ${kids.length} >>`;
  const chunks=[Buffer.from('%PDF-1.4\n')],offsets=[0];let length=chunks[0].length;
  objects.forEach((o,i)=>{offsets.push(length);const b=Buffer.concat([Buffer.from(`${i+1} 0 obj\n`),Buffer.isBuffer(o)?o:Buffer.from(o),Buffer.from('\nendobj\n')]);chunks.push(b);length+=b.length;});
  chunks.push(Buffer.from(`xref\n0 ${objects.length+1}\n0000000000 65535 f \n${offsets.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('')}trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${length}\n%%EOF\n`));
  return Buffer.concat(chunks);
}
// A calibrated room lies well outside the unchanged 4000 x 3000 mm outer ring.
// At 3235 mm / 100 page units, that ring covers the upper-left legend only.
function calibrationRegressionPDF() {
  const stream='4 w 220 250 m 420 250 l 420 100 l 320 100 l 320 150 l 220 150 l h S 20 330 100 50 re S';
  const objects=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 400] /Resources << >> /Contents 4 0 R >>',
    `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`];
  let text='%PDF-1.4\n',offsets=[0];
  objects.forEach((o,i)=>{offsets.push(text.length);text+=`${i+1} 0 obj\n${o}\nendobj\n`;});
  const xref=text.length;
  return Buffer.from(text+`xref\n0 5\n0000000000 65535 f \n`+offsets.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('')+
    `trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
}
module.exports={shapes,pdf,calibrationRegressionPDF};
if(require.main===module) {
  const fs=require('node:fs'),path=require('node:path');
  const destination=process.argv[2];if(!destination)throw Error('Specify the public PDF output path');
  fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,pdf());
}
