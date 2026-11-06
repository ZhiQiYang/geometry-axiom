'use strict';
// Finite HTML/event shim for shipped adapter code. No layout, pointer, focus
// navigation, browser parsing fidelity or rendering claim is made here.
const decode=value=>String(value).replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
function createDOM() {
  class Element {
    constructor(tag='div') {
      this.tagName=tag.toUpperCase();this.children=[];this.parentNode=null;this.attributes={};this.dataset={};this.listeners=new Map();
      this.value='';this.checked=false;this.disabled=false;this.hidden=false;this.open=false;this.isConnected=true;this._text='';this._html='';
      this.classList={add(){},remove(){},toggle(){},contains(){return false;}};
    }
    setAttribute(name,value='') {
      this.attributes[name]=String(value);
      if(name==='id')this.id=value;if(name==='value')this.value=decode(value);
      if(name.startsWith('data-'))this.dataset[name.slice(5).replace(/-([a-z])/g,(_,letter)=>letter.toUpperCase())]=decode(value);
      if(['hidden','disabled','checked','open'].includes(name))this[name]=true;
    }
    getAttribute(name){return this.attributes[name]??null;}
    set innerHTML(html) {
      this._html=String(html);this._text='';this.children=[];
      const stack=[this],voids=new Set(['INPUT','BR','IMG','HR','META','LINK']);
      for(const token of this._html.matchAll(/<!--[\s\S]*?-->|<[^>]+>|[^<]+/g)) {
        const text=token[0];if(text.startsWith('<!--'))continue;
        if(text.startsWith('</')){if(stack.length>1)stack.pop();continue;}
        if(text.startsWith('<')) {
          const match=/^<([\w-]+)\s*([\s\S]*?)\/?\s*>$/.exec(text);if(!match)continue;
          const element=new Element(match[1]);
          for(const attribute of match[2].matchAll(/([^\s=]+)(?:\s*=\s*"([^"]*)"|\s*=\s*'([^']*)'|\s*=\s*([^\s]+))?/g))
            element.setAttribute(attribute[1],attribute[2]??attribute[3]??attribute[4]??'');
          stack.at(-1).append(element);if(!voids.has(element.tagName)&&!text.endsWith('/>'))stack.push(element);
        } else stack.at(-1)._text+=decode(text);
      }
      for(const element of [this,...this.descendants()])if(element.tagName==='SELECT')element.value=element.children.find(x=>x.tagName==='OPTION')?.value||'';
    }
    get innerHTML(){return this._html;}
    get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
    set textContent(value){this._text=String(value);this._html='';this.children=[];}
    append(...items){for(const item of items){item.parentNode=this;this.children.push(item);}}
    appendChild(item){this.append(item);return item;}
    replaceChildren(...items){this.children=[];this._text='';this._html='';this.append(...items);}
    remove(){if(this.parentNode)this.parentNode.children=this.parentNode.children.filter(x=>x!==this);this.parentNode=null;}
    descendants(){return this.children.flatMap(child=>[child,...child.descendants()]);}
    matches(selector) {
      if(selector.startsWith('#'))return this.id===selector.slice(1);
      const match=/^\[([^=\]]+)(?:="([^"]*)")?\](:checked)?$/.exec(selector);
      if(match)return Object.hasOwn(this.attributes,match[1])&&(match[2]===undefined||this.attributes[match[1]]===match[2])&&(!match[3]||this.checked);
      return this.tagName.toLowerCase()===selector;
    }
    querySelectorAll(selector){return this.descendants().filter(x=>x.matches(selector));}
    querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
    addEventListener(type,fn){const list=this.listeners.get(type)||[];list.push(fn);this.listeners.set(type,list);}
    async dispatch(type,{bubble=true}={}) {
      const event={type,target:this,currentTarget:this,preventDefault(){},stopPropagation(){this.stopped=true;}};
      for(let at=this;at;at=bubble&&!event.stopped?at.parentNode:null){event.currentTarget=at;for(const fn of at.listeners.get(type)||[])await fn(event);}
    }
    showModal(){this.open=true;}
    close(){if(!this.open)return;this.open=false;queueMicrotask(()=>{void this.dispatch('close',{bubble:false});});}
    focus(){document.activeElement=this;}
    scrollIntoView(){}
  }
  const document={body:new Element('body'),activeElement:null,createElement:tag=>new Element(tag),
    getElementById:id=>document.body.querySelector('#'+id),querySelectorAll:s=>document.body.querySelectorAll(s)};
  return{document,Element};
}
module.exports={createDOM};
