const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const R=require('../geometry-web/room-outline.js');
const workerSource=fs.readFileSync(path.join(__dirname,'../geometry-web/room-outline-worker.js'),'utf8');
function run(data) {
  let reply;const scope=vm.createContext({RoomOutline:R,importScripts:()=>{},self:{postMessage:r=>reply=r}});
  vm.runInContext(workerSource,scope);scope.self.onmessage({data});return reply;
}
function payload(){return {kind:'pdf',list:{fnArray:[2,91],argsArray:[[4],[20,[new Float32Array([0,30,30,1,230,30,1,230,150,1,30,150,4])]]]},OPS:{setLineWidth:2,constructPath:91,stroke:20},viewport:{transform:[1,0,0,1,0,0]},options:{},barriers:[],warnings:[],seed:[70,70],crop:[0,0,280,190]};}
test('worker returns the same PDF interior, warnings and manual barriers as local analysis',()=>{
  const p=payload();p.barriers=[[128,32,132,148]];p.warnings=['explicit barrier'];
  const obstacles=R.pdfObstacles(p.list,p.OPS,p.viewport,p.options);obstacles.boxes.push(...p.barriers);obstacles.warnings.push(...p.warnings);
  assert.deepEqual(JSON.parse(JSON.stringify(run(p).result)),R.region(obstacles,p.seed,p.crop));
});
test('worker preserves explicit errors and never fabricates a rectangle',()=>{
  const p=payload();p.seed=[30,30];const got=run(p);assert.equal(got.ok,false);assert.equal(got.error.code,'wall');
});
test('image worker preserves page-coordinate scaling and does not detach caller geometry',()=>{
  const w=280,h=190,data=new Uint8ClampedArray(w*h*4).fill(255);
  for(const [a,b,c,d] of [[28,28,232,32],[228,28,232,152],[28,148,232,152],[28,28,32,152]])
    for(let y=b;y<d;y++)for(let x=a;x<c;x++)data.fill(0,(y*w+x)*4,(y*w+x)*4+3);
  const got=run({kind:'image',image:{width:w,height:h,data},options:{},crop:[100,200,560,380],kx:.5,ky:.5,seed:[240,340],barriers:[],warnings:[]});
  assert.equal(got.ok,true);assert.deepEqual(JSON.parse(JSON.stringify(got.result.points)),[[164,264],[556,264],[556,496],[164,496]]);
});
test('overlapping boxes and repeated strokes retain the exact union at high density',()=>{
  const boxes=[[848,848,952,852],[948,848,952,952],[848,948,952,952],[848,848,852,952]];
  for(let i=0;i<170;i++)boxes.push([20+i*2,20+i*2,21+i*2,21+i*2]);
  for(let i=0;i<11600;i++)boxes.push([10,10,800,800]);
  const result=R.region({boxes,fills:[],warnings:[],method:'pdf-vector'},[900,900],[0,0,1000,1000]);
  assert.deepEqual(result.points,[[852,852],[948,852],[948,948],[852,948]]);
});
function client() {
 const source=fs.readFileSync(path.join(__dirname,'../geometry-web/room-outline-workspace.js'),'utf8'),workers=[];
 class Worker {constructor(){workers.push(this);}terminate(){this.stopped=true;}postMessage(data){this.sent=data;}}
 const context=vm.createContext({Worker,setTimeout,clearTimeout});
 vm.runInContext(source.slice(source.indexOf('  let analysisJob='),source.indexOf('  const pending=')),context);
 return {analyze:context.analyze,stop:context.stopAnalysis,workers};
}
test('cancel/new acquisition terminates the old worker; late old messages cannot settle the new result',async()=>{
 const c=client(),old=c.analyze({kind:'pdf'}),rejected=assert.rejects(old,/取消/);
 const next=c.analyze({kind:'image'});await rejected;assert.equal(c.workers[0].stopped,true);
 c.workers[0].onmessage({data:{ok:true,result:'obsolete'}});
 c.workers[1].onmessage({data:{ok:true,result:'current'}});
 assert.equal(await next,'current');assert.equal(c.workers[1].stopped,true);
});
test('worker startup/message failure rejects cleanly and releases its resource',async()=>{
 const c=client(),result=c.analyze({});c.workers[0].onmessageerror();await assert.rejects(result,/無法讀取/);
 assert.equal(c.workers[0].stopped,true);
});
