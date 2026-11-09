'use strict';

/* O relatório vem de um LLM: nada aqui usa innerHTML. Tudo é montado com nós de texto. */

const $ = (sel, root = document) => root.querySelector(sel);
const TABS = ['analisar', 'acompanhar', 'material'];
const TITLES = { analisar: 'Analisar', acompanhar: 'Acompanhar', material: 'Material' };
const state = { status: null, apps: [], filter: '' };

function h(tag, props = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === false || value === null || value === undefined) continue;
    if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? '' : value);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) node.append(kid);
  return node;
}

/* replaceChildren escreve `null` como texto; este ajudante descarta o que não for nó. */
function put(el, ...kids) {
  el.replaceChildren(...kids.flat().filter((k) => k !== null && k !== undefined && k !== false));
}

async function api(path, { method = 'GET', json, form } = {}) {
  const opts = { method, headers: {} };
  if (method !== 'GET') opts.headers['X-JobAssist'] = '1'; // sem isto o servidor recusa (proteção contra CSRF)
  if (json !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(json);
  }
  if (form) opts.body = form;
  let res;
  try {
    res = await fetch(path, opts);
  } catch {
    throw new Error('Não consegui falar com o servidor. Ele ainda está rodando no terminal?');
  }
  let data = null;
  try { data = await res.json(); } catch { /* resposta sem corpo */ }
  if (!res.ok) throw new Error((data && data.error) || `Erro ${res.status}`);
  return data;
}

function say(el, text) {
  el.textContent = text || '';
  el.hidden = !text;
}

/* ---------- Markdown mínimo, seguro ---------- */

const TOKEN = /(\*\*[^*\n]+\*\*|\[[^\[\]\n]+?\.(?:pdf|docx|pptx|md|txt)(?:#[^\[\]\n]+)?\])/gi;
const CITE_RE = /\s*\[[^\[\]\n]+?\.(?:pdf|docx|pptx|md|txt)(?:#[^\[\]\n]+)?\]/gi;

function cite(id) {
  const [file, loc = ''] = id.split('#');
  const base = file.length > 26 ? `${file.slice(0, 23)}…` : file;
  return h('span', { class: 'cite', title: id, text: loc ? `${base} ${loc}` : base });
}

function inline(text) {
  const out = [];
  let last = 0;
  for (const m of text.matchAll(TOKEN)) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const tok = m[0];
    out.push(tok.startsWith('**') ? h('strong', { text: tok.slice(2, -2) }) : cite(tok.slice(1, -1)));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

function blocks(text) {
  const frag = document.createDocumentFragment();
  let list = null;
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    const item = line.match(/^[-*]\s+(.*)$/);
    if (item) {
      if (!list) { list = h('ul'); frag.append(list); }
      list.append(h('li', {}, inline(item[1])));
      continue;
    }
    list = null;
    if (line) frag.append(h('p', {}, inline(line)));
  }
  return frag;
}

function splitSections(md) {
  const parts = md.split(/^##\s*(.+)$/m); // [antes, título, corpo, título, corpo...]
  const sections = [];
  for (let i = 1; i < parts.length; i += 2) sections.push({ title: parts[i].trim(), body: (parts[i + 1] || '').trim() });
  return { preface: parts[0], sections };
}

const key = (title) => {
  const t = title.toLowerCase();
  return ['resumo', 'fortes', 'lacunas', 'destacar', 'rascunho'].find((k) => t.includes(k)) || 'outro';
};

function section(title, body, cls = '') {
  return h('div', { class: `sec ${cls}` }, h('h3', { text: title }), blocks(body));
}

function draftCard(title, body) {
  const lines = body.split('\n');
  if (/^rascunho/i.test((lines[0] || '').trim())) lines.shift();
  const text = lines.join('\n').trim();
  const copy = h('button', { class: 'btn btn--outline btn--sm', type: 'button', text: 'Copiar sem as citações' });
  copy.addEventListener('click', async () => {
    const clean = text.replace(CITE_RE, '').replace(/[ \t]+\n/g, '\n').trim();
    try {
      await navigator.clipboard.writeText(clean);
      copy.textContent = 'Copiado';
    } catch {
      copy.textContent = 'Não consegui copiar. Selecione o texto.';
    }
    setTimeout(() => { copy.textContent = 'Copiar sem as citações'; }, 2200);
  });
  return h('div', { class: 'card card--draft' },
    h('div', { class: 'draft__bar' }, h('span', { class: 'pill pill--blush', text: 'Rascunho: revise antes de usar' }), copy),
    section(title, text));
}

/* Monta as seções de um relatório: fortes e lacunas lado a lado, o resto em coluna única. */
function renderSections(md) {
  const { preface, sections } = splitSections(md);
  const by = {};
  for (const s of sections) {
    const k = key(s.title);
    if (k !== 'outro' && !by[k]) by[k] = s; // a primeira seção de cada tipo ocupa o seu lugar
  }
  const out = document.createDocumentFragment();
  if (by.resumo) out.append(section(by.resumo.title, by.resumo.body, 'sec--prose'));
  if (by.fortes || by.lacunas) {
    out.append(h('div', { class: 'pair' },
      by.fortes ? h('div', { class: 'card card--have' }, section(by.fortes.title, by.fortes.body)) : null,
      by.lacunas ? h('div', { class: 'card card--gap' }, section(by.lacunas.title, by.lacunas.body)) : null));
  }
  if (by.destacar) out.append(section(by.destacar.title, by.destacar.body));
  if (by.rascunho) out.append(draftCard(by.rascunho.title, by.rascunho.body));
  for (const s of sections) if (key(s.title) === 'outro') out.append(section(s.title, s.body));
  if (!sections.length && preface.trim()) out.append(h('div', { class: 'sec' }, blocks(preface)));
  return out;
}

/* ---------- Navegação ---------- */

function route(focus = false) {
  const tab = TABS.includes(location.hash.slice(1)) ? location.hash.slice(1) : 'analisar';
  for (const t of TABS) $(`#tab-${t}`).hidden = t !== tab;
  document.querySelectorAll('.tabs a').forEach((a) => {
    if (a.dataset.tab === tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  document.title = `${TITLES[tab]} | Assistente de candidaturas`;
  if (focus) { const hd = $(`#tab-${tab} h1`); hd.tabIndex = -1; hd.focus(); }
}

/* ---------- Diálogos ---------- */

document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-close]');
  if (btn) btn.closest('dialog').close('cancel');
});

function ask(title, text, okLabel) {
  return new Promise((resolve) => {
    const d = $('#dlg-confirm');
    $('#dlg-confirm-title').textContent = title;
    $('#dlg-confirm-text').textContent = text;
    const ok = $('#dlg-confirm-ok');
    ok.textContent = okLabel;
    ok.value = 'ok';
    d.returnValue = '';
    d.addEventListener('close', () => resolve(d.returnValue === 'ok'), { once: true });
    d.showModal();
  });
}

/* ---------- Estado do servidor ---------- */

function fillStatuses(select, selected) {
  select.replaceChildren(...state.status.statuses.map((s) => h('option', { value: s, text: s, selected: s === selected })));
}

function updateHint() {
  const s = state.status;
  const full = $('#full').checked;
  const n = s.files.length;
  let text = 'Só a vaga e os trechos mais relevantes do seu material vão para a OpenAI. Endereço, telefone e e-mail são removidos antes.';
  if (s.is_sample && !full) text = 'Você está usando o material de exemplo (fictício). Só a vaga e os trechos mais relevantes vão para a OpenAI.';
  if (full) text = `Atenção: o conteúdo inteiro de ${s.folder} (${n} arquivo${n === 1 ? '' : 's'}) será enviado à OpenAI.`;
  $('#hint').textContent = text;
}

async function loadStatus() {
  state.status = await api('/api/status');
  const s = state.status;
  const badge = $('#badge');
  badge.hidden = false;
  badge.textContent = s.is_sample ? 'Material de exemplo' : `Seu material (${s.folder})`;
  badge.classList.toggle('badge--sample', s.is_sample);
  const problems = [];
  if (!s.api_key_set) problems.push('Falta a chave da OpenAI (OPENAI_API_KEY).');
  if (!s.model) problems.push('Falta o modelo (OPENAI_MODEL).');
  say($('#banner'), problems.length ? `${problems.join(' ')} Preencha o arquivo .env e reinicie o servidor.` : '');
  fillStatuses($('#n-status'), 'interessada');
  updateHint();
  renderMaterial();
}

/* ---------- Analisar ---------- */

const number = (n) => n.toLocaleString('pt-BR');

function usageLine(u) {
  if (!u || !u.calls) return '';
  const cost = u.cost_usd === null || u.cost_usd === undefined ? '' : `, custo estimado de US$ ${u.cost_usd.toLocaleString('pt-BR', { minimumFractionDigits: 4 })}`;
  return `Consumo da API: ${u.calls} chamada${u.calls === 1 ? '' : 's'}, ${number(u.input)} tokens de entrada e ${number(u.output)} de saída${cost}.`;
}

function registerBox(data) {
  const box = h('div', { class: 'register' });
  const select = h('select', { id: 'reg-status', 'aria-label': 'Status da candidatura' });
  fillStatuses(select, 'interessada');
  const btn = h('button', { class: 'btn btn--outline', type: 'button', text: 'Registrar candidatura' });
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    try {
      await api('/api/applications', { method: 'POST', json: {
        company: data.job.company || 'empresa não informada', title: data.job.title || 'vaga sem título',
        status: select.value, report: data.report_file } });
      box.replaceChildren(h('p', { class: 'ok' }, 'Registrada. Veja em ', h('a', { href: '#acompanhar', text: 'Acompanhar' }), '.'));
      loadApps();
    } catch (e) {
      btn.disabled = false;
      say($('#error'), e.message);
    }
  });
  box.append(select, btn);
  return box;
}

function renderResult(data) {
  const res = $('#result');
  put(res,
    h('div', { class: 'result__head' },
      h('h2', { class: 'result__title', text: data.job.title || 'Vaga' }),
      h('p', { class: 'result__company', text: data.job.company || 'empresa não informada' }),
      h('span', { class: 'pill', text: data.mode === 'RAG' ? 'Com busca nos trechos' : 'Material inteiro' })),
    data.warnings.length
      ? h('div', { class: 'alert' }, h('strong', { text: 'Confira antes de usar.' }), h('ul', {}, data.warnings.map((w) => h('li', { text: w }))))
      : null,
    renderSections(data.report),
    h('div', { class: 'result__foot' }, h('p', { class: 'usage', text: usageLine(data.usage) }), registerBox(data)));
  res.hidden = false;
  res.classList.remove('is-new');
  void res.offsetWidth; // reinicia a animação de entrada
  res.classList.add('is-new');
  res.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
}

$('#full').addEventListener('change', updateHint);

$('#form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const vaga = $('#vaga').value.trim();
  say($('#error'), '');
  if (!vaga) { say($('#error'), 'Cole o texto da vaga.'); $('#vaga').focus(); return; }
  const full = $('#full').checked;
  if (full && !state.status.is_sample) {
    const ok = await ask('Enviar o material inteiro?', `O conteúdo inteiro de ${state.status.folder} será enviado à OpenAI, sem a busca que escolhe só os trechos relevantes.`, 'Enviar e analisar');
    if (!ok) return;
  }
  const go = $('#go');
  go.disabled = true;
  go.setAttribute('aria-busy', 'true');
  go.textContent = 'Analisando…';
  $('#progress').hidden = false;
  $('#result').hidden = true;
  try {
    renderResult(await api('/api/analyze', { method: 'POST', json: { vaga, lang: $('#lang').value, mode: full ? 'full' : 'rag', confirm_send_all: full } }));
  } catch (err) {
    say($('#error'), err.message);
  } finally {
    go.disabled = false;
    go.removeAttribute('aria-busy');
    go.textContent = 'Analisar vaga';
    $('#progress').hidden = true;
  }
});

/* ---------- Acompanhar ---------- */

const fmtDate = (iso) => iso.split('-').reverse().join('/');

function renderApps() {
  const apps = state.apps;
  const counts = {};
  for (const a of apps) counts[a.status] = (counts[a.status] || 0) + 1;
  const pill = (value, label) => h('button', { class: 'chip', type: 'button', 'aria-pressed': String(state.filter === value), text: label, onclick: () => { state.filter = value; renderApps(); } });
  $('#filters').replaceChildren(pill('', `Todas (${apps.length})`), ...state.status.statuses.filter((s) => counts[s]).map((s) => pill(s, `${s} (${counts[s]})`)));
  $('#apps-lede').textContent = apps.length
    ? `${apps.length} candidatura${apps.length === 1 ? '' : 's'} registrada${apps.length === 1 ? '' : 's'}. Mude o status direto na lista.`
    : 'Nenhuma candidatura ainda. Analise uma vaga e registre o resultado, ou adicione uma manualmente abaixo.';
  $('#filters').hidden = !apps.length;
  const shown = apps.filter((a) => !state.filter || a.status === state.filter);
  $('#apps').replaceChildren(...shown.map(appRow));
  $('#apps').hidden = !shown.length;
}

function appRow(a) {
  const select = h('select', { class: `status s-${a.status}`, 'aria-label': `Status de ${a.title} em ${a.company}` });
  fillStatuses(select, a.status);
  select.addEventListener('change', async () => {
    try {
      await api(`/api/applications/${a.id}`, { method: 'PATCH', json: { status: select.value } });
      say($('#apps-error'), '');
    } catch (err) {
      say($('#apps-error'), err.message);
    }
    loadApps();
  });
  return h('li', { class: 'app' },
    h('div', {}, h('h2', { class: 'app__title', text: a.title }), h('p', { class: 'app__meta', text: `${a.company}, ${fmtDate(a.applied_on)}` })),
    select,
    h('div', { class: 'app__actions' },
      a.has_report ? h('button', { class: 'btn btn--outline btn--sm', type: 'button', text: 'Relatório', onclick: () => openReport(a) }) : null,
      h('button', { class: 'btn btn--outline btn--sm', type: 'button', text: 'Editar', onclick: () => openEdit(a) }),
      h('button', { class: 'btn btn--outline btn--sm', type: 'button', text: 'Apagar', onclick: () => removeApp(a) })));
}

async function loadApps() {
  try {
    state.apps = await api('/api/applications');
    say($('#apps-error'), '');
    renderApps();
  } catch (e) {
    say($('#apps-error'), e.message);
  }
}

async function openReport(a) {
  try {
    const { report } = await api(`/api/applications/${a.id}/report`);
    const { sections } = splitSections(report);
    const first = report.split('\n')[0];
    $('#dlg-report-title').textContent = first.startsWith('# ') ? first.slice(2) : `${a.title} | ${a.company}`;
    const note = report.split('\n').filter((l) => l.startsWith('>')).map((l) => l.replace(/^>\s*(-\s*)?/, ''));
    put($('#dlg-report-body'),
      note.length ? h('div', { class: 'alert' }, note.map((l) => h('p', { text: l.replace(/\*\*/g, '') }))) : null,
      sections.length ? renderSections(report) : h('p', { text: report }));
    $('#dlg-report').showModal();
  } catch (e) {
    say($('#apps-error'), e.message);
  }
}

let editing = null;
function openEdit(a) {
  editing = a;
  $('#e-company').value = a.company;
  $('#e-title').value = a.title;
  $('#e-date').value = a.applied_on;
  fillStatuses($('#e-status'), a.status);
  say($('#e-error'), '');
  $('#dlg-edit').showModal();
}

$('#form-edit').addEventListener('submit', async (e) => {
  e.preventDefault(); // fecha só depois de salvar
  try {
    await api(`/api/applications/${editing.id}`, { method: 'PATCH', json: {
      company: $('#e-company').value, title: $('#e-title').value, applied_on: $('#e-date').value, status: $('#e-status').value } });
    $('#dlg-edit').close();
    loadApps();
  } catch (err) {
    say($('#e-error'), err.message);
  }
});

async function removeApp(a) {
  if (!(await ask('Apagar candidatura?', `${a.title} em ${a.company} sai da lista. O relatório continua na pasta reports/.`, 'Apagar'))) return;
  try {
    await api(`/api/applications/${a.id}`, { method: 'DELETE' });
  } catch (err) {
    say($('#apps-error'), err.message);
  }
  loadApps();
}

$('#form-new').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    await api('/api/applications', { method: 'POST', json: {
      company: $('#n-company').value, title: $('#n-title').value, applied_on: $('#n-date').value, status: $('#n-status').value } });
    e.target.reset();
    $('#new').open = false;
    say($('#apps-error'), '');
    loadApps();
  } catch (err) {
    say($('#apps-error'), err.message);
  }
});

/* ---------- Material ---------- */

const fmtSize = (b) => (b >= 1048576 ? `${(b / 1048576).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} MB` : `${Math.max(1, Math.round(b / 1024))} KB`);

function renderMaterial() {
  const s = state.status;
  const n = s.files.length;
  $('#mat-lede').textContent = s.is_sample
    ? 'Você está vendo o material de exemplo (fictício), que fica no Git. Para usar o seu, coloque MATERIAL_DIR=data/private no arquivo .env e reinicie o servidor.'
    : `${n} arquivo${n === 1 ? '' : 's'} em ${s.folder}. É nele que o sistema procura as evidências de cada vaga.`;
  $('#add-files').disabled = s.is_sample;
  $('#reindex').disabled = false;
  $('#files').replaceChildren(...s.files.map((f) => h('li', { class: 'file' },
    h('p', { class: 'file__name', text: f.name }),
    h('p', { class: 'file__meta', text: `${fmtSize(f.size)}, ${f.chunks ? `${f.chunks} trechos indexados` : 'ainda não indexado'}` }),
    s.is_sample ? null : h('button', { class: 'btn btn--outline btn--sm', type: 'button', text: 'Remover', onclick: () => removeFile(f) }))));
  $('#files').hidden = !n;
}

const mat = (text) => { $('#mat-msg').textContent = text; };

async function removeFile(f) {
  if (!(await ask('Remover do material?', `${f.name} sai da pasta e do índice. Essa ação apaga o arquivo.`, 'Remover'))) return;
  mat('Removendo e reindexando…');
  try {
    await api(`/api/material/${encodeURIComponent(f.name)}`, { method: 'DELETE' });
    mat(`${f.name} removido.`);
  } catch (e) {
    mat(e.message);
  }
  await loadStatus();
}

$('#add-files').addEventListener('click', () => $('#upload').click());

$('#upload').addEventListener('change', async (e) => {
  const files = [...e.target.files];
  e.target.value = '';
  if (!files.length) return;
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  mat('Enviando e indexando. Na primeira vez, o modelo de busca pode levar alguns segundos para carregar.');
  $('#add-files').disabled = true;
  try {
    const r = await api('/api/material', { method: 'POST', form });
    const bad = r.errors.map((x) => `${x.name}: ${x.error}`).join(' ');
    mat(`${r.saved.length} arquivo${r.saved.length === 1 ? '' : 's'} adicionado${r.saved.length === 1 ? '' : 's'}.${bad ? ` Não aceitos: ${bad}` : ''}`);
  } catch (err) {
    mat(err.message);
  }
  await loadStatus();
});

$('#reindex').addEventListener('click', async () => {
  mat('Reindexando…');
  try {
    const r = await api('/api/ingest', { method: 'POST' });
    mat(`Pronto: ${r.novos} arquivo(s) indexado(s), ${r.inalterados} inalterado(s), ${r.removidos} removido(s).`);
  } catch (err) {
    mat(err.message);
  }
  await loadStatus();
});

/* ---------- Início ---------- */

window.addEventListener('hashchange', () => route(true));
route();
loadStatus().then(loadApps).catch((e) => say($('#banner'), e.message));
