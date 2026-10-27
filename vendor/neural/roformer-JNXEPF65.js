import"./chunk-I7AUKTXE.js";async function ee(){let i=await globalThis.navigator?.gpu?.requestAdapter({powerPreference:"high-performance"}).catch(()=>null);return!i||i.info?.isFallbackAdapter||!["subgroups","chromium-experimental-subgroup-matrix"].every($=>i.features.has($))||![...i.info.subgroupMatrixConfigs??[]].some($=>$.componentType==="f32"&&$.M===8&&$.N===8&&$.K===8)?null:i.requestDevice({requiredFeatures:["subgroups","chromium-experimental-subgroup-matrix"],requiredLimits:{maxComputeWorkgroupStorageSize:32768,maxStorageBufferBindingSize:i.limits.maxStorageBufferBindingSize,maxBufferSize:i.limits.maxBufferSize}}).catch(()=>null)}async function ae(i,E,$){if($??=await ee(),!$)return null;let y=await Br($,i,E),{freqs:h,frames:W}=i;return{inputs:[{name:"mix_spec",dims:[1,4,h,W],type:"float32"}],outputs:[{name:"stems_spec",dims:[1,4,h,W],type:"float32"}],backend:"roformer",async run(p){return{stems_spec:{data:await y.run(p.mix_spec.data),dims:[1,4,h,W],type:"float32"}}},free(){$.destroy()}}}async function Br(i,E,$){let{frames:y,freqs:h,channels:W,dim:p,heads:c,depth:Ar,bands:g,groups:Tr}=E,B=64,D=1536,f=1536,t=Math.ceil(y/32)*32,Q=3*c*B,K=Math.ceil((Q+c)/32)*32,A=h*W*2,ir=Math.ceil(y/16)*16,pr=Math.ceil(g/16)*16,Pr=e=>Math.ceil(e/16)*16,G=Tr.map(([e,r,a])=>({b0:e,b1:r,n:r-e,W:a,Wp:Pr(a)})),b=e=>{let r=E.tensors[e],a=r.shape.reduce((u,o)=>u*o,1);return r.type==="float16"?new Float16Array($.buffer,$.byteOffset+r.offset,a):r.type==="int32"?new Int32Array($.buffer,$.byteOffset+r.offset,a):new Float32Array($.buffer,$.byteOffset+r.offset,a)},lr=GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST|GPUBufferUsage.COPY_SRC,v=(e,r="f32")=>i.createBuffer({size:Math.max(16,e*4),usage:lr}),d=e=>{let r=i.createBuffer({size:Math.max(16,e.byteLength),usage:lr,mappedAtCreation:!0});return new e.constructor(r.getMappedRange()).set(e),r.unmap(),r},x=e=>e instanceof Float32Array?e:Float32Array.from(e),gr=(e,r,a,u,o,m,l=(k,_)=>k*m+_)=>{let k=new Float32Array(r*o*m);for(let _=0;_<r;_++)for(let n=0;n<a;n++)for(let s=0;s<u;s++)k[_*o*m+l(n,s)]=e[(_*a+n)*u+s];return k},w={split:[],splitB:[],splitIdx:[],m2:[],m2B:[]};for(let[e,r]of G.entries()){w.split.push(d(gr(b(`split_w.${e}`),r.n,r.W,p,r.Wp,p))),w.splitB.push(d(x(b(`split_b.${e}`))));let a=b(`si${e}`),u=new Int32Array(r.n*r.Wp).fill(A);for(let n=0;n<r.n;n++)for(let s=0;s<r.W;s++)u[n*r.Wp+s]=a[n*r.W+s];w.splitIdx.push(d(u));let o=b(`m2_w.${e}`),m=b(`m2_b.${e}`),l=r.Wp,k=new Float32Array(r.n*f*2*l),_=new Float32Array(r.n*2*l);for(let n=0;n<r.n;n++){for(let s=0;s<f;s++)for(let O=0;O<r.W;O++)k[(n*f+s)*2*l+O]=o[(n*f+s)*2*r.W+O],k[(n*f+s)*2*l+l+O]=o[(n*f+s)*2*r.W+r.W+O];for(let s=0;s<r.W;s++)_[n*2*l+s]=m[n*2*r.W+s],_[n*2*l+l+s]=m[n*2*r.W+r.W+s]}w.m2.push(d(k)),w.m2B.push(d(_))}w.mw=[0,1].map(e=>d(x(b(`mw.${e}`)))),w.mb=[0,1].map(e=>d(x(b(`mb.${e}`)))),w.blocks=[];for(let e=0;e<Ar;e++)for(let r=0;r<2;r++){let a=`blocks.${e}.${r}.`,u=a+"layers.0.0.",o=a+"layers.0.1.";w.blocks.push({out:d(x(b(a+"out"))),qkvg:d(gr(b(u+"qkvg"),1,p,Q+c,p,K)),gb:d(x(b(u+"gb"))),wo:d(x(b(u+"wo"))),w1:d(x(b(o+"w1"))),b1:d(x(b(o+"b1"))),w2:d(x(b(o+"w2"))),b2:d(x(b(o+"b2")))})}let fr=e=>{let r=b(`blocks.0.${e}.layers.0.0.cos`),a=b(`blocks.0.${e}.layers.0.0.sin`);return[d(x(r)),d(x(a))]},[qr,jr]=fr(0),[Sr,Fr]=fr(1),Lr=b("i1"),Or=b("i2"),Gr=b("wt"),V=[],H=[],X=0,Z=0;for(let e of G)V.push(X),H.push(Z),X+=e.n*t*e.Wp,Z+=e.n*e.W;let cr=e=>{if(e>=Z)return[0,0,0];let r=H.findLastIndex(l=>l<=e),a=G[r],u=e-H[r],o=Math.floor(u/a.W),m=u%a.W;return[V[r]+o*t*a.Wp+m,a.Wp,1]},br=new Uint32Array(A*8);for(let e=0;e<A;e++)br.set([...cr(Lr[e]),...cr(Or[e])],e*8);let zr=d(br),J=d(Float32Array.from({length:A},(e,r)=>Gr[r])),rr=v(t*(A+1)),T=v(g*t*p),C=v(g*t*p),mr=v(g*t*K),Y=Math.max(g*c*ir,y*c*pr)*B,er=v(Y),ar=v(Y),tr=v(Y),dr=v(Y),wr=v(g*t*c),$r=v(g*t*c*B),I=v(g*t*D),yr=v(g*t*f),vr=v(X),_r=v(4*h*y),hr=G.map(e=>v(e.n*t*e.Wp)),xr=G.map(e=>v(e.n*t*2*e.Wp)),Er=v(4),Mr=new Map,P=(e,r)=>Mr.get(e)??Mr.set(e,i.createComputePipeline({layout:"auto",compute:{module:i.createShaderModule({code:r}),entryPoint:"main"}})).get(e),q=(...e)=>{let r=i.createBuffer({size:Math.ceil(e.length/4)*16,usage:GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST});return i.queue.writeBuffer(r,0,new Uint32Array(e.map(a=>typeof a=="number"&&!Number.isInteger(a)?new Uint32Array(new Float32Array([a]).buffer)[0]:a))),r},or=[],j=(e,r,a)=>or.push([e,i.createBindGroup({layout:e.getBindGroupLayout(0),entries:r.map((u,o)=>({binding:o,resource:{buffer:u}}))}),a]),S=`enable subgroups;
enable chromium_experimental_subgroup_matrix;
`,Ur=e=>P("mm"+e,S+`
@group(0) @binding(0) var<storage, read> A: array<f32>;
@group(0) @binding(1) var<storage, read> Bm: array<f32>;
@group(0) @binding(2) var<storage, read_write> C: array<f32>;
@group(0) @binding(3) var<storage, read> bias: array<f32>;
struct P { M: u32, N: u32, K: u32, a0: u32, sa: u32, b0: u32, sb: u32, c0: u32, sc: u32, ldc: u32, bias0: u32, sbias: u32 }
@group(0) @binding(4) var<uniform> p: P;
var<workgroup> tile: array<f32, 1024>;
@compute @workgroup_size(32)
fn main(@builtin(workgroup_id) wg: vec3u, @builtin(subgroup_invocation_id) lane: u32) {
  _ = bias[0];   // bound whether read or not: the layout is the module's own
  let r0 = wg.y * 32u; let n0 = wg.x * 32u; let b = wg.z;
  let ab = p.a0 + b * p.sa + r0 * p.K; let bb = p.b0 + b * p.sb + n0;
  ${[0,1,2,3].map(r=>[0,1,2,3].map(a=>`var c${r}${a}: subgroup_matrix_result<f32, 8, 8>;`).join(" ")).join(`
  `)}
  for (var k = 0u; k < p.K; k += 8u) {
    ${[0,1,2,3].map(r=>`let a${r} = subgroupMatrixLoad<subgroup_matrix_left<f32, 8, 8>>(&A, ab + ${r*8}u * p.K + k, false, p.K);`).join(`
    `)}
    ${[0,1,2,3].map(r=>`let b${r} = subgroupMatrixLoad<subgroup_matrix_right<f32, 8, 8>>(&Bm, bb + k * p.N + ${r*8}u, false, p.N);`).join(`
    `)}
    ${[0,1,2,3].map(r=>[0,1,2,3].map(a=>`c${r}${a} = subgroupMatrixMultiplyAccumulate(a${r}, b${a}, c${r}${a});`).join(" ")).join(`
    `)}
  }
  ${[0,1,2,3].map(r=>[0,1,2,3].map(a=>`subgroupMatrixStore(&tile, ${r*8*32+a*8}u, c${r}${a}, false, 32u);`).join(" ")).join(`
  `)}
  workgroupBarrier();
  for (var e = lane; e < 1024u; e += 32u) {
    let r = r0 + e / 32u; let n = n0 + e % 32u;
    if (r < p.M && n < p.N) {
      var v = tile[e];
      ${e.includes("b")?"v += bias[p.bias0 + b * p.sbias + n];":""}
      ${e.includes("g")?"v = 0.5 * v * (1.0 + erf_(v * 0.7071067811865476));":e.includes("t")?"v = tanh(v);":""}
      let o = p.c0 + b * p.sc + r * p.ldc + n;
      ${e.includes("r")?"C[o] += v;":"C[o] = v;"}
    }
  }
}
fn erf_(x: f32) -> f32 {   // Abramowitz & Stegun 7.1.26 is 1.5e-7; GELU's own float32 erf is as close
  let t = 1.0 / (1.0 + 0.3275911 * abs(x));
  let y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * exp(-x * x);
  return select(-y, y, x >= 0.0);
}`),F=(e,r,a,u,o,{M:m,N:l,K:k,batch:_=1,a0:n=0,sa:s=0,b0:O=0,sb:Vr=0,c0:Hr=0,sc:Xr=0,ldc:Zr=l,bias0:Jr=0,sbias:re=0})=>j(Ur(e),[r,a,u,o??J,q(m,l,k,n,s,O,Vr,Hr,Xr,Zr,Jr,re)],[l/32,m/32,_]),Kr=e=>P("norm"+e,S+`
@group(0) @binding(0) var<storage, read_write> x: array<f32>;
@group(0) @binding(1) var<storage, read_write> y: array<f32>;
@group(0) @binding(2) var<storage, read> g: array<f32>;
struct P { rows: u32, n: u32 }
@group(0) @binding(3) var<uniform> p: P;
@compute @workgroup_size(32)
fn main(@builtin(workgroup_id) wg: vec3u, @builtin(subgroup_invocation_id) lane: u32) {
  _ = g[0]; _ = y[0];
  let r = wg.x + wg.y * 65535u;
  if (r >= p.rows) { return; }
  var s = 0.0;
  for (var i = lane; i < p.n; i += 32u) { let v = x[r * p.n + i]; s += v * v; }
  let k = 1.0 / max(sqrt(subgroupAdd(s)), 1e-12);
  for (var i = lane; i < p.n; i += 32u) { ${e?"x[r * p.n + i] = x[r * p.n + i] * k * g[i];":"y[r * p.n + i] = x[r * p.n + i] * k;"} }
}`),Cr=e=>[Math.min(e,65535),Math.ceil(e/65535),1],ur=(e,r,a,u,o)=>j(Kr(!!o),[e,o?Er:r,o??J,q(a,u)],Cr(a)),Yr=P("split",S+`
@group(0) @binding(0) var<storage, read> E: array<f32>;
@group(0) @binding(1) var<storage, read> idx: array<i32>;
@group(0) @binding(2) var<storage, read_write> A: array<f32>;
struct P { Wp: u32, Tp: u32, T: u32, cols: u32 }
@group(0) @binding(3) var<uniform> p: P;
@compute @workgroup_size(32)
fn main(@builtin(workgroup_id) wg: vec3u, @builtin(subgroup_invocation_id) lane: u32) {
  let t = wg.x; let j = wg.y;
  var s = 0.0;
  for (var e = lane; e < p.Wp; e += 32u) { let v = select(0.0, E[t * (p.cols + 1u) + u32(idx[j * p.Wp + e])], t < p.T); s += v * v; }
  let k = 1.0 / max(sqrt(subgroupAdd(s)), 1e-12);
  for (var e = lane; e < p.Wp; e += 32u) {
    let v = select(0.0, E[t * (p.cols + 1u) + u32(idx[j * p.Wp + e])], t < p.T);
    A[(j * p.Tp + t) * p.Wp + e] = v * k;
  }
}`),Ir=P("rope",S+`
@group(0) @binding(0) var<storage, read> Yq: array<f32>;
@group(0) @binding(1) var<storage, read_write> Q: array<f32>;
@group(0) @binding(2) var<storage, read_write> K: array<f32>;
@group(0) @binding(3) var<storage, read_write> V: array<f32>;
@group(0) @binding(4) var<storage, read_write> Gt: array<f32>;
@group(0) @binding(5) var<storage, read> cs: array<f32>;
@group(0) @binding(6) var<storage, read> sn: array<f32>;
@group(0) @binding(7) var<storage, read> gb: array<f32>;
struct P { time: u32, Tp: u32, T: u32, L: u32, ld: u32 }
@group(0) @binding(8) var<uniform> p: P;
@compute @workgroup_size(64)
fn main(@builtin(workgroup_id) wg: vec3u, @builtin(local_invocation_id) li: vec3u) {
  let t = wg.x; let band = wg.y; let h = wg.z; let d = li.x;
  if (t >= p.T) { return; }
  let r = band * p.Tp + t;
  var seq = band; var pos = t;
  if (p.time == 0u) { seq = t; pos = band; }
  let o = ((seq * ${c}u + h) * p.L + pos) * 64u + d;
  let y = r * p.ld + h * 64u;
  let rot = select(Yq[y + d - 32u], -Yq[y + d + 32u], d < 32u);
  let rk = select(Yq[y + ${c*B}u + d - 32u], -Yq[y + ${c*B}u + d + 32u], d < 32u);
  Q[o] = Yq[y + d] * cs[pos * 64u + d] + rot * sn[pos * 64u + d];
  K[o] = Yq[y + ${c*B}u + d] * cs[pos * 64u + d] + rk * sn[pos * 64u + d];
  V[o] = Yq[y + ${2*c*B}u + d];
  if (d == 0u) { Gt[r * ${c}u + h] = 1.0 / (1.0 + exp(-(Yq[r * p.ld + ${Q}u + h] + gb[h]))); }
}`),Nr=P("merge",S+`
@group(0) @binding(0) var<storage, read> O: array<f32>;
@group(0) @binding(1) var<storage, read> Gt: array<f32>;
@group(0) @binding(2) var<storage, read_write> Zb: array<f32>;
struct P { time: u32, Tp: u32, T: u32, L: u32 }
@group(0) @binding(3) var<uniform> p: P;
@compute @workgroup_size(64)
fn main(@builtin(workgroup_id) wg: vec3u, @builtin(local_invocation_id) li: vec3u) {
  let t = wg.x; let band = wg.y; let h = wg.z; let d = li.x;
  let r = band * p.Tp + t;
  if (t >= p.T) { Zb[r * ${c*B}u + h * 64u + d] = 0.0; return; }
  var seq = band; var pos = t;
  if (p.time == 0u) { seq = t; pos = band; }
  Zb[r * ${c*B}u + h * 64u + d] = O[((seq * ${c}u + h) * p.L + pos) * 64u + d] * Gt[r * ${c}u + h];
}`),N=16,M=32,U=4,L=[0,1],z=[0,1,2,3],nr=[...Array(8).keys()],kr=`${L.map(e=>z.map(r=>`var s${e}_${r}: subgroup_matrix_result<f32, 8, 8>;`).join(" ")).join(`
    `)}
    for (var k = 0u; k < 8u; k++) {
      ${L.map(e=>`let q${e} = subgroupMatrixLoad<subgroup_matrix_left<f32, 8, 8>>(&Q, base + (r0 + ${e*8}u) * 64u + k * 8u, false, 64u);`).join(`
      `)}
      ${z.map(e=>`let k${e} = subgroupMatrixLoad<subgroup_matrix_right<f32, 8, 8>>(&K, base + (c0 + ${e*8}u) * 64u + k * 8u, true, 64u);`).join(`
      `)}
      ${L.map(e=>z.map(r=>`s${e}_${r} = subgroupMatrixMultiplyAccumulate(q${e}, k${r}, s${e}_${r});`).join(" ")).join(`
      `)}
    }
    ${L.map(e=>z.map(r=>`subgroupMatrixStore(&S[sg], ${e*8*M+r*8}u, s${e}_${r}, false, ${M}u);`).join(" ")).join(`
    `)}
    workgroupBarrier();`,Rr=P("att",S+`
@group(0) @binding(0) var<storage, read> Q: array<f32>;
@group(0) @binding(1) var<storage, read> K: array<f32>;
@group(0) @binding(2) var<storage, read> V: array<f32>;
@group(0) @binding(3) var<storage, read_write> O: array<f32>;
struct P { n: u32, np: u32 }
@group(0) @binding(4) var<uniform> p: P;
var<workgroup> S: array<array<f32, ${N*M}>, ${U}>;
var<workgroup> Ow: array<array<f32, ${N*64}>, ${U}>;
@compute @workgroup_size(${32*U})
fn main(@builtin(workgroup_id) wg: vec3u, @builtin(subgroup_id) sg: u32, @builtin(subgroup_invocation_id) lane: u32) {
  let b = wg.y;
  let r0 = (wg.x * ${U}u + sg) * ${N}u;
  let base = b * p.np * 64u;
  let row = lane / 2u; let half = (lane % 2u) * ${M/2}u;    // two lanes a row, 16 columns each
  var mx = -1e30;
  for (var c0 = 0u; c0 < p.n; c0 += ${M}u) {
    ${kr}
    for (var j = 0u; j < ${M/2}u; j++) { if (c0 + half + j < p.n) { mx = max(mx, S[sg][row * ${M}u + half + j]); } }
    workgroupBarrier();
  }
  mx = max(mx, subgroupShuffleXor(mx, 1u));
  var l = 0.0;
  ${L.map(e=>nr.map(r=>`var o${e}_${r}: subgroup_matrix_result<f32, 8, 8>;`).join(" ")).join(`
  `)}
  for (var c0 = 0u; c0 < p.n; c0 += ${M}u) {
    ${kr}
    for (var j = 0u; j < ${M/2}u; j++) {
      let at = row * ${M}u + half + j;
      let e = select(0.0, exp(S[sg][at] - mx), c0 + half + j < p.n);
      S[sg][at] = e; l += e;
    }
    workgroupBarrier();
    ${L.map(e=>z.map(r=>`let p${e}_${r} = subgroupMatrixLoad<subgroup_matrix_left<f32, 8, 8>>(&S[sg], ${e*8*M+r*8}u, false, ${M}u);`).join(" ")).join(`
    `)}
    ${nr.map(e=>z.map(r=>`let v${r}_${e} = subgroupMatrixLoad<subgroup_matrix_right<f32, 8, 8>>(&V, base + (c0 + ${r*8}u) * 64u + ${e*8}u, false, 64u);`).join(" ")+`
    `+L.map(r=>z.map(a=>`o${r}_${e} = subgroupMatrixMultiplyAccumulate(p${r}_${a}, v${a}_${e}, o${r}_${e});`).join(" ")).join(" ")).join(`
    `)}
    workgroupBarrier();
  }
  l += subgroupShuffleXor(l, 1u);
  ${L.map(e=>nr.map(r=>`subgroupMatrixStore(&Ow[sg], ${e*8*64+r*8}u, o${e}_${r}, false, 64u);`).join(" ")).join(`
  `)}
  workgroupBarrier();
  // lane pairs hold their row's sum; each lane writes half its row
  for (var d = 0u; d < 32u; d++) {
    let r = r0 + row;
    if (r < p.n) { O[base + r * 64u + half * 2u + d] = Ow[sg][row * 64u + half * 2u + d] / l; }
  }
}`),Dr=P("glu",S+`
@group(0) @binding(0) var<storage, read> Yg: array<f32>;
@group(0) @binding(1) var<storage, read_write> Mo: array<f32>;
struct P { rows: u32, Wp: u32, at: u32 }
@group(0) @binding(2) var<uniform> p: P;
@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gi: vec3u) {
  let i = gi.x + gi.y * 65535u * 64u;
  if (i >= p.rows * p.Wp) { return; }
  let r = i / p.Wp; let e = i % p.Wp;
  Mo[p.at + i] = Yg[r * 2u * p.Wp + e] / (1.0 + exp(-Yg[r * 2u * p.Wp + p.Wp + e]));
}`),Qr=P("mask",S+`
@group(0) @binding(0) var<storage, read> Mo: array<f32>;
@group(0) @binding(1) var<storage, read> map: array<u32>;
@group(0) @binding(2) var<storage, read> wt: array<f32>;
@group(0) @binding(3) var<storage, read> E: array<f32>;
@group(0) @binding(4) var<storage, read_write> Out: array<f32>;
struct P { T: u32, F: u32, cols: u32 }
@group(0) @binding(5) var<uniform> p: P;
fn mask(t: u32, o: u32) -> f32 {
  let a = map[o * 8u]; let sa = map[o * 8u + 1u]; let on1 = map[o * 8u + 2u];
  let b = map[o * 8u + 3u]; let sb = map[o * 8u + 4u]; let on2 = map[o * 8u + 5u];
  var v = 0.0;
  if (on1 == 1u) { v += Mo[a + t * sa]; }
  if (on2 == 1u) { v += Mo[b + t * sb]; }
  return v * wt[o];
}
@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gi: vec3u) {
  let t = gi.x; let fs = gi.y;          // fs = f\xB7S + s
  if (t >= p.T) { return; }
  let f = fs / ${W}u; let s = fs % ${W}u;
  let o = fs * 2u;
  let er = E[t * (p.cols + 1u) + o]; let ei = E[t * (p.cols + 1u) + o + 1u];
  let mr = mask(t, o); let mi = mask(t, o + 1u);
  Out[((s * 2u) * p.F + f) * p.T + t] = er * mr - ei * mi;
  Out[((s * 2u + 1u) * p.F + f) * p.T + t] = er * mi + ei * mr;
}`);for(let[e,r]of G.entries())j(Yr,[rr,w.splitIdx[e],hr[e],q(r.Wp,t,y,A)],[t,r.n,1]),F("b",hr[e],w.split[e],T,w.splitB[e],{M:t,N:p,K:r.Wp,batch:r.n,sa:t*r.Wp,sb:r.Wp*p,c0:r.b0*t*p,sc:t*p,sbias:p});for(let[e,r]of w.blocks.entries()){let a=e%2===0,u=a?ir:pr,o=a?y:g,m=a?g:y;ur(T,C,g*t,p),F("",C,r.qkvg,mr,null,{M:g*t,N:K,K:p}),j(Ir,[mr,er,ar,tr,wr,a?qr:Sr,a?jr:Fr,r.gb,q(a?1:0,t,y,u,K)],[t,g,c]),j(Rr,[er,ar,tr,dr,q(o,u)],[Math.ceil(u/(N*U)),m*c,1]),j(Nr,[dr,wr,$r,q(a?1:0,t,y,u)],[t,g,c]),F("r",$r,r.wo,T,null,{M:g*t,N:p,K:c*B}),ur(T,C,g*t,p),F("bg",C,r.w1,I,r.b1,{M:g*t,N:D,K:p}),F("br",I,r.w2,T,r.b2,{M:g*t,N:p,K:D}),ur(T,T,g*t,p,r.out)}F("bt",T,w.mw[0],I,w.mb[0],{M:t,N:f,K:p,batch:g,sa:t*p,sb:p*f,sc:t*f,sbias:f}),F("bt",I,w.mw[1],yr,w.mb[1],{M:t,N:f,K:f,batch:g,sa:t*f,sb:f*f,sc:t*f,sbias:f});for(let[e,r]of G.entries()){F("b",yr,w.m2[e],xr[e],w.m2B[e],{M:t,N:2*r.Wp,K:f,batch:r.n,a0:r.b0*t*f,sa:t*f,sb:f*2*r.Wp,sc:t*2*r.Wp,sbias:2*r.Wp});let a=r.n*t*r.Wp;j(Dr,[xr[e],vr,q(r.n*t,r.Wp,V[e])],[Math.min(Math.ceil(a/64),65535),Math.ceil(a/64/65535),1])}j(Qr,[vr,zr,J,rr,_r,q(y,h,A)],[Math.ceil(y/64),h*W,1]);let Wr=i.createCommandEncoder();for(let e of[er,ar,tr])Wr.clearBuffer(e);i.queue.submit([Wr.finish()]);let sr=new Float32Array(t*(A+1)),R=i.createBuffer({size:4*h*y*4,usage:GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ});return{steps:or.length,async run(e){sr.fill(0);for(let o=0;o<W;o++)for(let m=0;m<2;m++)for(let l=0;l<h;l++){let k=((o*2+m)*h+l)*y,_=(l*W+o)*2+m;for(let n=0;n<y;n++)sr[n*(A+1)+_]=e[k+n]}i.queue.writeBuffer(rr,0,sr);let r=i.createCommandEncoder(),a=r.beginComputePass();for(let[o,m,l]of or)a.setPipeline(o),a.setBindGroup(0,m),a.dispatchWorkgroups(...l);a.end(),r.copyBufferToBuffer(_r,0,R,0,4*h*y*4),i.queue.submit([r.finish()]),await R.mapAsync(GPUMapMode.READ);let u=new Float32Array(R.getMappedRange().slice(0));return R.unmap(),u}}}export{Br as default,ae as engine,ee as gpu};
