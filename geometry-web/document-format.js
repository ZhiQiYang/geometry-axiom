/* Read-only document primitives. Never interpret HTML or fetch document URLs. */
(function(root) {
  'use strict';
  const LIMITS = Object.freeze({text: 2*1024*1024, pdf: 24*1024*1024, pages: 500, search: 2000});
  function fileKind(file) {
    const ext = String(file.name || '').split('.').pop().toLowerCase();
    const kind = new Map([['md','markdown'],['markdown','markdown'],['txt','text'],['pdf','pdf']]).get(ext);
    if (!kind) throw Error('支援 UTF-8 Markdown（.md）、文字（.txt）與 PDF；其他格式請先轉換。');
    if (!Number.isFinite(file.size) || file.size < 1) throw Error('文件是空的或無法讀取。');
    if (file.size > LIMITS[kind === 'pdf' ? 'pdf' : 'text']) throw Error(kind === 'pdf' ? 'PDF 上限為 24 MB。' : '文字文件上限為 2 MB。');
    return kind;
  }
  function decodeText(bytes) {
    let text;
    try { text = new TextDecoder('utf-8',{fatal:true}).decode(bytes); }
    catch (_) { throw Error('無法以 UTF-8 讀取，請另存為 UTF-8 文字後重試。'); }
    if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(text)) throw Error('檔案含有非文字資料，請選擇 UTF-8 文字文件。');
    return text.replace(/^\ufeff/,'').replace(/\r\n?/g,'\n');
  }
  function safeURL(value) {
    if (typeof value !== 'string' || /[\u0000-\u0020\u007f]/.test(value)) return null;
    try { const u = new URL(value); return ['https:','http:'].includes(u.protocol) && !u.username && !u.password ? u.href : null; } catch (_) { return null; }
  }
  function slug(value) { return String(value).trim().toLowerCase().replace(/[^\p{L}\p{N}_ -]/gu,'').replace(/\s+/g,'-'); }
  const inlinePattern=/(`[^`\n]+`|\*\*[^*\n]+\*\*|\*[^*\n]+\*|!?\[[^\]\n]{1,500}\]\([^\)\n]{1,2000}\))/g;
  function validateComplexity(blocks) {
    let nodes=0,headings=0,cells=0;
    const charge=n=>{nodes+=n;if(nodes>20000)throw Error('文件排版過於複雜，請分割後重試（上限 20,000 個閱讀節點）。');};
    const inline=text=>{charge(1);for(const _ of text.matchAll(inlinePattern))charge(3);};
    for(const block of blocks){charge(2);if(block.type==='heading'){if(++headings>1000)throw Error('章節標題超過 1,000 個，請分割文件。');charge(2);}
      if(block.type==='table'){for(const row of block.rows){charge(1);for(const text of row){if(++cells>5000)throw Error('表格儲存格超過 5,000 個，請分割文件。');charge(1);inline(text);}}}
      else if(!['code','hr'].includes(block.type))inline(block.text);
    }
    return blocks;
  }
  // This intentionally supports a bounded Markdown subset, not arbitrary HTML.
  function parse(text) {
    if (typeof text !== 'string' || text.length > LIMITS.text) throw Error('文字文件過大。');
    const lines = text.split('\n'), blocks = []; let code = null, paragraph = [];
    const flush = () => { if (paragraph.length) { blocks.push({type:'p',text:paragraph.join('\n')}); paragraph=[]; } };
    for (let i=0;i<lines.length;i++) {
      if (blocks.length > 10000) throw Error('文件段落過多，請分成較小的文件後重試。');
      const line=lines[i];
      if (/^\s*```/.test(line)) { flush(); if(code!==null) {blocks.push({type:'code',text:code.join('\n')});code=null;} else code=[]; continue; }
      if (code!==null) {code.push(line);continue;}
      const h=/^(#{1,6})\s+(.+?)\s*#*\s*$/.exec(line);
      if(h){flush();blocks.push({type:'heading',level:h[1].length,text:h[2],slug:slug(h[2])});continue;}
      const li=/^(\s*)(?:([-+*])|\d+[.)])\s+(.+)$/.exec(line);
      if(li){flush();blocks.push({type:'li',level:Math.min(8,Math.floor(li[1].replace(/\t/g,'  ').length/2)),ordered:!li[2],text:li[3]});continue;}
      if(/^\s*>/.test(line)){flush();blocks.push({type:'quote',text:line.replace(/^\s*>\s?/,'')});continue;}
      if(/^\s*(?:---+|\*\*\*+)\s*$/.test(line)){flush();blocks.push({type:'hr',text:''});continue;}
      if(line.includes('|') && i+1<lines.length && /^\s*\|?\s*:?-+:?\s*\|/.test(lines[i+1])) {
        flush();const cells=s=>{const values=s.trim().replace(/^\|/,'').replace(/\|$/,'').split('|');if(values.length>256)throw Error('表格欄位超過 256 欄，請分割文件。');return values.map(c=>c.trim());};
        const rows=[cells(line)];i++;while(i+1<lines.length&&lines[i+1].includes('|')&&lines[i+1].trim()){if(rows.length>=1000)throw Error('表格超過 1,000 列，請分割文件。');rows.push(cells(lines[++i]));}
        blocks.push({type:'table',rows,text:rows.map(r=>r.join(' | ')).join('\n')});continue;
      }
      if(!line.trim()){flush();continue;}paragraph.push(line);
    }
    flush();if(code!==null)blocks.push({type:'code',text:code.join('\n')});return validateComplexity(blocks);
  }
  function preferences(value) {
    const v=value&&typeof value==='object'?value:{};
    const clamp=(n,a,b,d)=>typeof n==='number'&&Number.isFinite(n)?Math.min(b,Math.max(a,n)):d;
    return {font:clamp(v.font,14,24,17),line:clamp(v.line,1.4,2.2,1.8),width:clamp(v.width,560,960,720),theme:['light','dark','paper'].includes(v.theme)?v.theme:'light'};
  }
  const api={LIMITS,fileKind,decodeText,safeURL,slug,parse,preferences,validateComplexity};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.DocumentFormat=Object.freeze(api);
})(typeof window==='undefined'?globalThis:window);
