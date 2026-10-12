// Repo-authored valid original PDF; no external or private material.
module.exports=function fixture(changed=false){
  const objects=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R 5 0 R 7 0 R 9 0 R] /Count 4 >>'];
  for(const [i,rotation]of [0,90,180,270].entries()){
    const stream=`0 0 0 RG 1 w 20 30 90 70 re S BT /F1 12 Tf 20 160 Td (Authored evidence ${changed?'458':'457.5'} mm) Tj ET`;
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 340 260] /CropBox [20 30 320 230] /Rotate ${rotation} /Resources << /Font << /F1 11 0 R >> >> /Contents ${4+i*2} 0 R >>`,`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
  }objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  let text='%PDF-1.4\n',offsets=[0];objects.forEach((object,i)=>{offsets.push(text.length);text+=`${i+1} 0 obj\n${object}\nendobj\n`;});const xref=text.length;
  text+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n`+offsets.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('');
  return Buffer.from(text+`trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
};
