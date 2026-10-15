(() => {
  'use strict';

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // ------------------------------------------------------------------ textes
  const I18N = {
    fr: {
      tagline: "Laboratoire d'IA pour l'image", beta: 'Plateforme de test', api: 'API',
      dropTitle: 'Déposez une image ici',
      dropHint: 'ou cliquez pour choisir un fichier — vous pouvez aussi coller (Ctrl+V)',
      viewCompare: 'Avant / après', viewAfter: 'Résultat', viewBefore: 'Original',
      checker: 'Damier', bgDark: 'Fond sombre', bgLight: 'Fond clair',
      newImage: 'Nouvelle image', before: 'Avant', after: 'Après', splitAria: 'Position du comparateur',
      processing: 'Traitement en cours', cancel: 'Annuler',
      resultTitle: 'Résultat', reuse: 'Retravailler ce résultat', download: 'Télécharger',
      analysisTitle: "Analyse automatique de l'image",
      presets: 'Que voulez-vous faire ?',
      pCut: 'Retirer le fond', pCutSub: 'PNG transparent',
      pFix: 'Corriger la photo', pFixSub: 'Couleurs, lumière, bruit',
      pUp: 'Agrandir ×4', pUpSub: 'Super-résolution IA',
      pAll: 'Tout-en-un', pAllSub: 'Corriger + détourer',
      secEnhance: "Correction de l'image", secEnhanceSub: 'Balance des blancs, exposition, contraste, bruit, netteté',
      auto: 'Automatique', manual: 'Manuelle',
      autoHint: "L'image est analysée (dominante de couleur, exposition, bruit, flou) et chaque correction est dosée en conséquence.",
      secBg: 'Arrière-plan', secBgSub: 'Détourage du sujet par segmentation neuronale',
      model: 'Modèle', edges: 'Bords',
      edgesRefined: 'Affinés (recommandé)', edgesStandard: 'Bruts du modèle', edgesMatting: 'Matting cheveux (lent)',
      newBg: 'Nouveau fond', bgTransparent: 'Transparent', bgColor: 'Couleur', bgBlur: 'Flou', bgImage: 'Image',
      blurAmount: 'Intensité du flou', chooseBg: 'Choisir une image de fond…',
      secUp: 'Agrandissement IA', secUpSub: 'Real-ESRGAN : reconstruit les détails, pas un simple étirement',
      factor: 'Facteur', x2: '×2', x4: '×4', srDenoise: 'Débruitage',
      dLow: 'Garder le grain', dMed: 'Moyen', dHigh: 'Fort',
      format: 'Format de sortie', run: 'Lancer le traitement', runHint: "Ajoutez d'abord une image.",
      runReady: 'Prêt.',
      privacy: 'Vos images sont traitées en mémoire et ne sont jamais conservées sur le serveur. Métadonnées (EXIF, GPS) retirées du résultat.',
      engine: 'Calcul sur processeur, sans GPU : les traitements prennent de 1 à 40 secondes.',
      limits: 'Limites : {mb} Mo par fichier, images réduites à {side} px de côté.',
      p_wb: 'Balance des blancs', p_levels: 'Niveaux (plage tonale)', p_exposure: 'Exposition',
      p_local_contrast: 'Contraste local', p_denoise: 'Débruitage', p_sharpen: 'Netteté', p_vibrance: 'Vibrance',
      st_decode: 'Lecture', st_enhance: 'Correction', st_segment: 'Détourage', st_edges: 'Bords',
      st_background: 'Nouveau fond', st_upscale: 'Agrandissement', st_encode: 'Encodage', st_total: 'Total',
      fmtJpgAlpha: 'Le JPEG ne gère pas la transparence : le fond sera blanc. Choisissez PNG ou WebP.',
      fmtPng: 'PNG : sans perte, garde la transparence.',
      fmtWebp: 'WebP : léger, garde la transparence.',
      fmtJpg: 'JPEG : le plus léger, sans transparence.',
      upFits: 'Résultat attendu : {w} × {h} px.',
      upReduce: 'Votre image ({sw} × {sh}) sera d\'abord ramenée à {side} px de côté : résultat {w} × {h} px. L\'agrandissement IA sert surtout aux petites images.',
      upNoImage: 'Entrée limitée à {s2} px (×2) et {s4} px (×4) de côté sur ce serveur sans GPU.',
      mattingHint: 'Le matting travaille au plus à {side} px de côté.',
      busyUp: "L'agrandissement IA est la partie la plus longue (jusqu'à ~40 s).",
      busyMatting: 'Le matting des cheveux prend quelques secondes de plus.',
      busyFirst: 'Premier usage de ce modèle : chargement en mémoire.',
      resultMeta: '{w} × {h} px · {fmt} · {size}',
      noteReduced: 'Image réduite à {w} × {h} px avant traitement (limite {side} px de côté).',
      noteEmptyMask: "Aucun sujet net n'a été détecté : essayez un autre modèle.",
      noteJpg: 'JPEG sans transparence : le fond a été rempli en blanc.',
      noPreview: 'Aperçu indisponible dans ce navigateur (HEIC) — le serveur sait le lire.',
      needBgImage: "Choisissez l'image qui servira de nouveau fond.",
      nothingToDo: 'Activez au moins un traitement.',
      tooBig: 'Fichier trop lourd : {mb} Mo au maximum.',
      notImage: "Ce fichier n'est pas une image.",
      err_busy: 'La plateforme est occupée, réessayez dans quelques instants.',
      err_rate: 'Trop de demandes rapprochées : patientez une minute.',
      err_too_large: 'Fichier trop lourd.',
      err_bad_image: 'Fichier illisible : ce n\'est pas une image valide.',
      err_unsupported_format: "Format d'image non pris en charge.",
      err_too_many_pixels: 'Image trop grande (nombre de pixels).',
      err_missing_background: "Image d'arrière-plan manquante.",
      err_upscale_unavailable: 'Agrandissement IA indisponible pour le moment.',
      err_internal: 'Le traitement a échoué. Réessayez, ou avec une autre image.',
      err_gateway: 'Le serveur a mis trop de temps à répondre. Essayez une image plus petite.',
      err_network: 'Connexion au serveur impossible.',
      chipNoise: 'Bruit σ', chipSharp: 'Netteté', chipLum: 'Luminosité', chipCast: 'Dominante', chipSat: 'Saturation',
      castNone: 'neutre',
    },
    en: {
      tagline: 'AI imaging lab', beta: 'Test platform', api: 'API',
      dropTitle: 'Drop an image here',
      dropHint: 'or click to pick a file — you can also paste (Ctrl+V)',
      viewCompare: 'Before / after', viewAfter: 'Result', viewBefore: 'Original',
      checker: 'Checker', bgDark: 'Dark backdrop', bgLight: 'Light backdrop',
      newImage: 'New image', before: 'Before', after: 'After', splitAria: 'Comparison slider position',
      processing: 'Processing', cancel: 'Cancel',
      resultTitle: 'Result', reuse: 'Keep working on this result', download: 'Download',
      analysisTitle: 'Automatic image analysis',
      presets: 'What do you want to do?',
      pCut: 'Remove background', pCutSub: 'Transparent PNG',
      pFix: 'Fix the photo', pFixSub: 'Colour, light, noise',
      pUp: 'Upscale ×4', pUpSub: 'AI super-resolution',
      pAll: 'All-in-one', pAllSub: 'Fix + cut out',
      secEnhance: 'Image correction', secEnhanceSub: 'White balance, exposure, contrast, noise, sharpness',
      auto: 'Automatic', manual: 'Manual',
      autoHint: 'The image is analysed (colour cast, exposure, noise, blur) and each correction is dosed accordingly.',
      secBg: 'Background', secBgSub: 'Subject cut-out by neural segmentation',
      model: 'Model', edges: 'Edges',
      edgesRefined: 'Refined (recommended)', edgesStandard: 'Raw model output', edgesMatting: 'Hair matting (slow)',
      newBg: 'New background', bgTransparent: 'Transparent', bgColor: 'Colour', bgBlur: 'Blur', bgImage: 'Image',
      blurAmount: 'Blur strength', chooseBg: 'Choose a background image…',
      secUp: 'AI upscaling', secUpSub: 'Real-ESRGAN: rebuilds detail instead of stretching pixels',
      factor: 'Factor', x2: '×2', x4: '×4', srDenoise: 'Denoising',
      dLow: 'Keep grain', dMed: 'Medium', dHigh: 'Strong',
      format: 'Output format', run: 'Run', runHint: 'Add an image first.',
      runReady: 'Ready.',
      privacy: 'Your images are processed in memory and never stored on the server. Metadata (EXIF, GPS) is stripped from the result.',
      engine: 'CPU-only processing, no GPU: jobs take 1 to 40 seconds.',
      limits: 'Limits: {mb} MB per file, images downsized to {side} px on the long side.',
      p_wb: 'White balance', p_levels: 'Levels (tonal range)', p_exposure: 'Exposure',
      p_local_contrast: 'Local contrast', p_denoise: 'Denoise', p_sharpen: 'Sharpen', p_vibrance: 'Vibrance',
      st_decode: 'Decode', st_enhance: 'Correction', st_segment: 'Cut-out', st_edges: 'Edges',
      st_background: 'New background', st_upscale: 'Upscaling', st_encode: 'Encode', st_total: 'Total',
      fmtJpgAlpha: 'JPEG has no transparency: the background will be white. Pick PNG or WebP.',
      fmtPng: 'PNG: lossless, keeps transparency.',
      fmtWebp: 'WebP: small, keeps transparency.',
      fmtJpg: 'JPEG: smallest, no transparency.',
      upFits: 'Expected result: {w} × {h} px.',
      upReduce: 'Your image ({sw} × {sh}) will first be reduced to {side} px on the long side: result {w} × {h} px. AI upscaling is mainly meant for small images.',
      upNoImage: 'Input limited to {s2} px (×2) and {s4} px (×4) on the long side on this GPU-less server.',
      mattingHint: 'Matting works at {side} px on the long side at most.',
      busyUp: 'AI upscaling is the slowest part (up to ~40 s).',
      busyMatting: 'Hair matting takes a few extra seconds.',
      busyFirst: 'First use of this model: loading it into memory.',
      resultMeta: '{w} × {h} px · {fmt} · {size}',
      noteReduced: 'Image reduced to {w} × {h} px before processing ({side} px limit).',
      noteEmptyMask: 'No clear subject was detected: try another model.',
      noteJpg: 'JPEG has no transparency: the background was filled with white.',
      noPreview: 'No preview in this browser (HEIC) — the server can read it.',
      needBgImage: 'Choose the image to use as the new background.',
      nothingToDo: 'Turn on at least one operation.',
      tooBig: 'File too large: {mb} MB maximum.',
      notImage: 'This file is not an image.',
      err_busy: 'The platform is busy, please retry in a moment.',
      err_rate: 'Too many requests in a row: wait a minute.',
      err_too_large: 'File too large.',
      err_bad_image: 'Unreadable file: not a valid image.',
      err_unsupported_format: 'Unsupported image format.',
      err_too_many_pixels: 'Image too large (pixel count).',
      err_missing_background: 'Background image missing.',
      err_upscale_unavailable: 'AI upscaling is unavailable right now.',
      err_internal: 'Processing failed. Retry, or try another image.',
      err_gateway: 'The server took too long to answer. Try a smaller image.',
      err_network: 'Cannot reach the server.',
      chipNoise: 'Noise σ', chipSharp: 'Sharpness', chipLum: 'Brightness', chipCast: 'Colour cast', chipSat: 'Saturation',
      castNone: 'neutral',
    },
  };

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch { /* stockage indisponible */ } },
  };

  let lang = store.get('legenipng.lang') || ((navigator.language || 'fr').toLowerCase().startsWith('en') ? 'en' : 'fr');

  function t(key, vars) {
    let s = (I18N[lang] && I18N[lang][key]) ?? I18N.fr[key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));
    return s;
  }

  function applyI18n() {
    document.documentElement.lang = lang;
    $$('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
    $$('[data-i18n-aria]').forEach((el) => el.setAttribute('aria-label', t(el.dataset.i18nAria)));
    $('#langBtn').textContent = lang === 'fr' ? 'EN' : 'FR';
    fillModels();
    updateHints();
    updateBgToggle();
    if (state.config) $('#limits').textContent = t('limits', { mb: state.config.max_upload_mb, side: state.config.max_side });
    if (state.report) renderReport(state.report);
    $('#runHint').textContent = t(state.file ? 'runReady' : 'runHint');
    const bgf = $('#bgFile').files[0];
    $('#bgFileName').textContent = bgf ? bgf.name : t('chooseBg');
  }

  // ------------------------------------------------------------------ état
  const PARAMS = ['wb', 'levels', 'exposure', 'local_contrast', 'denoise', 'sharpen', 'vibrance'];
  const state = {
    config: null,
    file: null, fileName: 'image', srcURL: null, srcW: 0, srcH: 0, noPreview: false,
    resultURL: null, resultBlob: null, report: null, resultExt: 'png',
    enhanceMode: 'auto', bgMode: 'transparent', upFactor: 4, srDenoise: 'medium', fmt: 'png',
    manual: { wb: 30, levels: 50, exposure: 0, local_contrast: 25, denoise: 0, sharpen: 30, vibrance: 15 },
    controller: null, timer: null, startedAt: 0, view: 'compare', backdrop: 0, usedModels: new Set(),
  };

  // ------------------------------------------------------------------ configuration serveur
  async function loadConfig() {
    try {
      const r = await fetch('/api/config');
      state.config = await r.json();
    } catch {
      state.config = {
        max_upload_mb: 15, max_side: 3000, matting_max_side: 2048,
        upscale_max_side: { 2: 1200, 4: 720 }, upscale_levels: ['low', 'medium', 'high'],
        models: [], default_model: 'isnet-general-use', heif: true,
      };
    }
    applyI18n();
  }

  function fillModels() {
    const sel = $('#model');
    const models = state.config ? state.config.models : [];
    const current = sel.value || (state.config && state.config.default_model);
    sel.textContent = '';
    for (const m of models) {
      const o = document.createElement('option');
      o.value = m.id;
      o.textContent = lang === 'en' ? m.en : m.fr;
      sel.appendChild(o);
    }
    if (current) sel.value = current;
    updateModelHint();
  }

  function updateModelHint() {
    const m = state.config && state.config.models.find((x) => x.id === $('#model').value);
    $('#modelHint').textContent = m ? (lang === 'en' ? m.hint_en : m.hint_fr) : '';
  }

  // ------------------------------------------------------------------ contrôles
  function seg(id, attr, onPick) {
    const root = $(id);
    root.addEventListener('click', (e) => {
      const b = e.target.closest('button');
      if (!b || !root.contains(b)) return;
      $$('button', root).forEach((x) => x.classList.toggle('on', x === b));
      onPick(b.dataset[attr]);
    });
  }

  function setSeg(id, attr, value) {
    $$(`${id} button`).forEach((b) => b.classList.toggle('on', b.dataset[attr] === String(value)));
  }

  function syncBlocks() {
    $('#blkEnhance').classList.toggle('off', !$('#enhanceOn').checked);
    $('#blkBg').classList.toggle('off', !$('#bgOn').checked);
    $('#blkUp').classList.toggle('off', !$('#upOn').checked);
    $('#sliders').hidden = state.enhanceMode !== 'manual';
    $('#autoHint').hidden = state.enhanceMode !== 'auto';
    $('#bgColorRow').hidden = state.bgMode !== 'color';
    $('#bgBlurRow').hidden = state.bgMode !== 'blur';
    $('#bgImageRow').hidden = state.bgMode !== 'image';
    updateHints();
  }

  function clearPreset() { $$('.preset').forEach((p) => p.classList.remove('on')); }

  const PRESETS = {
    cutout: { enhance: false, bg: true, up: false, bgMode: 'transparent', fmt: 'png' },
    fix: { enhance: true, bg: false, up: false, fmt: 'jpg' },
    upscale: { enhance: false, bg: false, up: true, factor: 4, fmt: 'jpg' },
    all: { enhance: true, bg: true, up: false, bgMode: 'transparent', fmt: 'png' },
  };

  function applyPreset(name) {
    const p = PRESETS[name];
    $$('.preset').forEach((x) => x.classList.toggle('on', x.dataset.preset === name));
    $('#enhanceOn').checked = p.enhance;
    $('#bgOn').checked = p.bg;
    $('#upOn').checked = p.up;
    if (p.enhance) { state.enhanceMode = 'auto'; setSeg('#enhanceMode', 'mode', 'auto'); }
    if (p.bgMode) { state.bgMode = p.bgMode; setSeg('#bgMode', 'bg', p.bgMode); }
    if (p.factor) { state.upFactor = p.factor; setSeg('#upFactor', 'f', p.factor); }
    state.fmt = p.fmt; setSeg('#fmt', 'fmt', p.fmt);
    syncBlocks();
  }

  function buildSliders() {
    const box = $('#sliders');
    box.textContent = '';
    for (const p of PARAMS) {
      const label = document.createElement('label');
      label.className = 'slider';
      const span = document.createElement('span');
      span.dataset.i18n = `p_${p}`;
      span.textContent = t(`p_${p}`);
      const input = document.createElement('input');
      input.type = 'range'; input.min = '0'; input.max = '100'; input.value = state.manual[p]; input.id = `p_${p}`;
      const out = document.createElement('output');
      out.textContent = state.manual[p];
      input.addEventListener('input', () => { state.manual[p] = +input.value; out.textContent = input.value; clearPreset(); });
      label.append(span, input, out);
      box.appendChild(label);
    }
  }

  function updateHints() {
    const cfg = state.config;
    if (!cfg) return;
    // format
    const bgTransparent = $('#bgOn').checked && state.bgMode === 'transparent';
    const fmtHint = $('#fmtHint');
    if (state.fmt === 'jpg' && bgTransparent) fmtHint.textContent = t('fmtJpgAlpha');
    else fmtHint.textContent = t({ png: 'fmtPng', webp: 'fmtWebp', jpg: 'fmtJpg' }[state.fmt]);
    fmtHint.classList.toggle('warn', state.fmt === 'jpg' && bgTransparent);
    // agrandissement
    const lim = cfg.upscale_max_side;
    const up = $('#upHint');
    if (!state.srcW) {
      up.textContent = t('upNoImage', { s2: lim['2'], s4: lim['4'] });
    } else {
      const f = state.upFactor;
      let side = Math.min(cfg.max_side, lim[String(f)]);
      if ($('#bgOn').checked && $('#edges').value === 'matting') side = Math.min(side, cfg.matting_max_side);
      const big = Math.max(state.srcW, state.srcH);
      const k = big > side ? side / big : 1;
      const w = Math.round(state.srcW * k) * f;
      const h = Math.round(state.srcH * k) * f;
      up.textContent = k < 1
        ? t('upReduce', { sw: state.srcW, sh: state.srcH, side, w, h })
        : t('upFits', { w, h });
    }
  }

  // ------------------------------------------------------------------ fichier source
  function isImageFile(f) {
    return f && ((f.type && f.type.startsWith('image/')) || /\.(heic|heif|avif)$/i.test(f.name || ''));
  }

  function setFile(f, name) {
    hideAlert();
    if (!isImageFile(f)) { showAlert(t('notImage')); return; }
    const mb = state.config ? state.config.max_upload_mb : 15;
    if (f.size > mb * 1024 * 1024) { showAlert(t('tooBig', { mb })); return; }
    state.file = f;
    state.fileName = name || f.name || 'image';
    if (state.srcURL) URL.revokeObjectURL(state.srcURL);
    state.srcURL = URL.createObjectURL(f);
    state.srcW = 0; state.srcH = 0; state.noPreview = false;
    clearResult();
    const img = $('#imgBefore');
    img.hidden = false;
    img.onload = () => {
      state.srcW = img.naturalWidth; state.srcH = img.naturalHeight;
      setRatio(state.srcW, state.srcH);
      $('#fileLine').textContent = `${state.fileName} · ${state.srcW} × ${state.srcH} px · ${fmtSize(f.size)}`;
      updateHints();
    };
    img.onerror = () => {
      if (!img.getAttribute('src')) return;
      state.noPreview = true;
      img.hidden = true;
      $('#fileLine').textContent = `${state.fileName} · ${fmtSize(f.size)} — ${t('noPreview')}`;
      setRatio(4, 3);
    };
    img.src = state.srcURL;
    $('#drop').hidden = true;
    $('#viewer').hidden = false;
    setCompareMode('single');
    $('#runBtn').disabled = false;
    $('#runHint').textContent = t('runReady');
  }

  function clearResult() {
    if (state.resultURL) URL.revokeObjectURL(state.resultURL);
    state.resultURL = null; state.resultBlob = null; state.report = null;
    $('#imgAfter').removeAttribute('src');
    $('#result').hidden = true;
  }

  function resetAll() {
    clearResult();
    if (state.srcURL) URL.revokeObjectURL(state.srcURL);
    state.file = null; state.srcURL = null; state.srcW = 0; state.srcH = 0;
    $('#imgBefore').removeAttribute('src');
    $('#viewer').hidden = true;
    $('#drop').hidden = false;
    $('#runBtn').disabled = true;
    $('#runHint').textContent = t('runHint');
    $('#fileInput').value = '';
    hideAlert();
    updateHints();
  }

  function setRatio(w, h) {
    if (w > 0 && h > 0) $('#compare').style.setProperty('--ratio', String(w / h));
  }

  // ------------------------------------------------------------------ comparateur
  function setSplit(v) {
    $('#afterWrap').style.clipPath = `inset(0 0 0 ${v}%)`;
    $('#handle').style.left = `${v}%`;
  }

  function setCompareMode(mode) {
    const c = $('#compare');
    c.classList.remove('single', 'mode-after', 'mode-before');
    if (mode === 'single') {
      c.classList.add('single');
      $('#viewSeg').hidden = true;
      $('#bgToggle').hidden = true;
      return;
    }
    $('#viewSeg').hidden = state.noPreview;
    $('#bgToggle').hidden = false;
    if (mode === 'after') c.classList.add('mode-after');
    if (mode === 'before') c.classList.add('mode-before');
    state.view = mode;
    setSeg('#viewSeg', 'view', mode);
  }

  const BACKDROPS = [['checker', 'checker'], ['dark-bg', 'bgDark'], ['light-bg', 'bgLight']];
  function updateBgToggle() {
    const wrap = $('#afterWrap');
    BACKDROPS.forEach(([cls]) => wrap.classList.remove(cls));
    const [cls] = BACKDROPS[state.backdrop];
    wrap.classList.add(cls);
    $('#bgToggle').textContent = t(BACKDROPS[state.backdrop][1]);
  }

  // ------------------------------------------------------------------ traitement
  function buildForm() {
    const fd = new FormData();
    fd.append('image', state.file, state.fileName);
    const enhanceOn = $('#enhanceOn').checked;
    fd.append('enhance_mode', enhanceOn ? state.enhanceMode : 'off');
    if (enhanceOn && state.enhanceMode === 'manual') PARAMS.forEach((p) => fd.append(p, state.manual[p]));
    const bgOn = $('#bgOn').checked;
    fd.append('remove_bg', bgOn ? 'true' : 'false');
    if (bgOn) {
      fd.append('model', $('#model').value);
      fd.append('edges', $('#edges').value);
      fd.append('bg_mode', state.bgMode);
      fd.append('bg_color', $('#bgColor').value);
      fd.append('bg_blur', $('#bgBlur').value);
      if (state.bgMode === 'image') fd.append('background_image', $('#bgFile').files[0]);
    }
    const upOn = $('#upOn').checked;
    fd.append('upscale', upOn ? String(state.upFactor) : '1');
    fd.append('sr_denoise', state.srDenoise);
    fd.append('output_format', state.fmt);
    return fd;
  }

  async function run(e) {
    e.preventDefault();
    if (!state.file || state.controller) return;
    hideAlert();
    const enhanceOn = $('#enhanceOn').checked, bgOn = $('#bgOn').checked, upOn = $('#upOn').checked;
    if (!enhanceOn && !bgOn && !upOn) { showAlert(t('nothingToDo')); return; }
    if (bgOn && state.bgMode === 'image' && !$('#bgFile').files[0]) { showAlert(t('needBgImage')); return; }

    const hints = [];
    if (bgOn && !state.usedModels.has($('#model').value)) hints.push(t('busyFirst'));
    if (bgOn && $('#edges').value === 'matting') hints.push(t('busyMatting'));
    if (upOn) hints.push(t('busyUp'));
    $('#busyHint').textContent = hints.join(' ');

    state.controller = new AbortController();
    $('#busy').hidden = false;
    $('#runBtn').disabled = true;
    state.startedAt = performance.now();
    $('#elapsed').textContent = '0';
    state.timer = setInterval(() => {
      $('#elapsed').textContent = String(Math.floor((performance.now() - state.startedAt) / 1000));
    }, 250);

    try {
      const res = await fetch('/api/process', { method: 'POST', body: buildForm(), signal: state.controller.signal });
      if (!res.ok) {
        let code = null;
        try { code = (await res.json()).code; } catch { /* réponse non JSON (nginx) */ }
        if (!code) code = res.status === 413 ? 'too_large' : res.status === 429 ? 'rate' : (res.status === 502 || res.status === 504) ? 'gateway' : 'internal';
        showAlert(t(`err_${code}`));
        return;
      }
      const blob = await res.blob();
      let report = null;
      try { report = JSON.parse(res.headers.get('X-Legenipng-Report') || 'null'); } catch { /* en-tête absent */ }
      if (bgOn) state.usedModels.add($('#model').value);
      showResult(blob, report);
    } catch (err) {
      if (err.name !== 'AbortError') showAlert(t('err_network'));
    } finally {
      clearInterval(state.timer);
      state.controller = null;
      $('#busy').hidden = true;
      $('#runBtn').disabled = !state.file;
    }
  }

  function showResult(blob, report) {
    if (state.resultURL) URL.revokeObjectURL(state.resultURL);
    state.resultURL = URL.createObjectURL(blob);
    state.resultBlob = blob;
    state.report = report;
    state.resultExt = report ? report.output.format : 'png';
    const img = $('#imgAfter');
    img.src = state.resultURL;
    if (report && state.noPreview) setRatio(report.output.width, report.output.height);
    setSplit($('#split').value);
    setCompareMode(state.noPreview ? 'after' : 'compare');
    const base = state.fileName.replace(/\.[^.]+$/, '').replace(/-legenipng$/, '') || 'image';
    const dl = $('#downloadBtn');
    dl.href = state.resultURL;
    dl.download = `${base}-legenipng.${state.resultExt}`;
    $('#result').hidden = false;
    renderReport(report);
  }

  function fmtSize(n) {
    const [b, kb, mb] = lang === 'fr' ? ['o', 'Ko', 'Mo'] : ['B', 'KB', 'MB'];
    if (n < 1024) return `${n} ${b}`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} ${kb}`;
    return `${(n / 1024 / 1024).toFixed(1).replace('.', lang === 'fr' ? ',' : '.')} ${mb}`;
  }

  function fmtMs(ms) {
    const s = ms / 1000;
    const txt = s < 10 ? s.toFixed(1) : s.toFixed(0);
    return `${lang === 'fr' ? txt.replace('.', ',') : txt} s`;
  }

  function renderReport(r) {
    const steps = $('#steps'), notes = $('#notes'), chips = $('#analysis');
    steps.textContent = ''; notes.textContent = ''; chips.textContent = '';
    if (!r) { $('#resultMeta').textContent = ''; $('#analysisBox').hidden = true; return; }
    $('#resultMeta').textContent = t('resultMeta', {
      w: r.output.width, h: r.output.height, fmt: r.output.format.toUpperCase(), size: fmtSize(r.output.bytes),
    });
    for (const s of r.steps) {
      const li = document.createElement('li');
      let label = t(`st_${s.step}`);
      if (s.step === 'upscale') label += ` ×${s.factor}`;
      if (s.step === 'segment') {
        const m = state.config && state.config.models.find((x) => x.id === s.model);
        if (m) label += ` · ${(lang === 'en' ? m.en : m.fr).replace(/\s*\(.*\)$/, '')}`;
      }
      li.append(`${label} `);
      const b = document.createElement('b');
      b.textContent = fmtMs(s.ms);
      li.appendChild(b);
      steps.appendChild(li);
    }
    const total = document.createElement('li');
    total.append(`${t('st_total')} `);
    const tb = document.createElement('b');
    tb.textContent = fmtMs(r.total_ms);
    total.appendChild(tb);
    steps.appendChild(total);

    for (const n of r.notes || []) {
      const div = document.createElement('div');
      div.className = 'note';
      div.textContent = n.code === 'reduced' ? t('noteReduced', { w: n.width, h: n.height, side: n.side })
        : n.code === 'empty_mask' ? t('noteEmptyMask')
        : n.code === 'jpg_flattened' ? t('noteJpg') : n.code;
      notes.appendChild(div);
    }

    const enh = r.steps.find((s) => s.step === 'enhance');
    $('#analysisBox').hidden = !enh;
    if (enh) {
      const chip = (label, value) => {
        const c = document.createElement('span');
        c.className = 'chip';
        c.append(`${label} `);
        const b = document.createElement('b');
        b.textContent = value;
        c.appendChild(b);
        chips.appendChild(c);
      };
      for (const p of PARAMS) chip(t(`p_${p}`), enh.params[p] ?? 0);
      const a = enh.analysis;
      const cast = Math.hypot(a.cast_a, a.cast_b);
      chip(t('chipCast'), cast < 2 ? t('castNone') : castName(a.cast_a, a.cast_b));
      chip(t('chipLum'), `${Math.round(a.mean_l)} / 100`);
      chip(t('chipNoise'), a.noise.toFixed(1));
      chip(t('chipSharp'), Math.round(a.sharpness));
      chip(t('chipSat'), `${Math.round(a.saturation * 100)} %`);
    }
  }

  function castName(a, b) {
    // teinte dans le plan a*b* : a+ magenta, b+ jaune, a- vert, b- bleu
    const deg = ((Math.atan2(b, a) * 180) / Math.PI + 360) % 360;
    const ranges = [
      [25, 'magenta', 'magenta'], [55, 'red', 'rouge'], [75, 'orange', 'orangée'], [110, 'yellow', 'jaune'],
      [190, 'green', 'verte'], [235, 'cyan', 'cyan'], [290, 'blue', 'bleue'], [345, 'violet', 'violette'],
      [360, 'magenta', 'magenta'],
    ];
    const hit = ranges.find(([upper]) => deg < upper) || ranges[0];
    return lang === 'en' ? hit[1] : hit[2];
  }

  // ------------------------------------------------------------------ alertes
  function showAlert(msg) { const a = $('#alert'); a.textContent = msg; a.hidden = false; }
  function hideAlert() { $('#alert').hidden = true; }

  // ------------------------------------------------------------------ branchements
  function wire() {
    const drop = $('#drop'), input = $('#fileInput');
    drop.addEventListener('click', () => input.click());
    drop.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); } });
    input.addEventListener('change', () => { if (input.files[0]) setFile(input.files[0]); });
    ['dragenter', 'dragover'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('over'); }));
    ['dragleave', 'drop'].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove('over')));
    window.addEventListener('dragover', (e) => e.preventDefault());
    window.addEventListener('drop', (e) => {
      e.preventDefault();
      const f = e.dataTransfer && e.dataTransfer.files[0];
      if (f && !state.controller) setFile(f);
    });
    document.addEventListener('paste', (e) => {
      const item = [...(e.clipboardData ? e.clipboardData.items : [])].find((i) => i.type.startsWith('image/'));
      if (item && !state.controller) {
        const f = item.getAsFile();
        const ext = (item.type.split('/')[1] || 'png').replace('jpeg', 'jpg');
        setFile(f, `presse-papiers.${ext}`);
      }
    });

    $('#newBtn').addEventListener('click', resetAll);
    $('#cancelBtn').addEventListener('click', () => state.controller && state.controller.abort());
    $('#reuseBtn').addEventListener('click', () => {
      const blob = state.resultBlob;
      if (!blob) return;
      const base = state.fileName.replace(/\.[^.]+$/, '').replace(/-legenipng$/, '');
      setFile(new File([blob], `${base}-legenipng.${state.resultExt}`, { type: blob.type }));
    });
    $('#bgToggle').addEventListener('click', () => { state.backdrop = (state.backdrop + 1) % BACKDROPS.length; updateBgToggle(); });
    $('#split').addEventListener('input', (e) => setSplit(e.target.value));
    seg('#viewSeg', 'view', (v) => setCompareMode(v));

    $$('.preset').forEach((p) => p.addEventListener('click', () => applyPreset(p.dataset.preset)));
    ['#enhanceOn', '#bgOn', '#upOn'].forEach((id) => $(id).addEventListener('change', () => { clearPreset(); syncBlocks(); }));
    seg('#enhanceMode', 'mode', (v) => { state.enhanceMode = v; clearPreset(); syncBlocks(); });
    seg('#bgMode', 'bg', (v) => { state.bgMode = v; clearPreset(); syncBlocks(); });
    seg('#upFactor', 'f', (v) => { state.upFactor = +v; clearPreset(); updateHints(); });
    seg('#srDenoise', 'd', (v) => { state.srDenoise = v; clearPreset(); });
    seg('#fmt', 'fmt', (v) => { state.fmt = v; clearPreset(); updateHints(); });
    $('#model').addEventListener('change', () => { updateModelHint(); clearPreset(); });
    $('#edges').addEventListener('change', () => {
      const m = $('#edges').value === 'matting';
      $('#modelHint').textContent = m && state.config ? t('mattingHint', { side: state.config.matting_max_side }) : '';
      if (!m) updateModelHint();
      updateHints();
    });
    $('#bgBlur').addEventListener('input', (e) => { $('#bgBlurOut').textContent = e.target.value; });
    $('#bgFile').addEventListener('change', (e) => {
      const f = e.target.files[0];
      $('#bgFileName').textContent = f ? f.name : t('chooseBg');
    });
    const swatches = ['#ffffff', '#000000', '#f1f2f4', '#dfe9ff', '#ffe8d2', '#1f3a8a', '#0f766e', '#b42318'];
    for (const c of swatches) {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'swatch'; b.title = c; b.setAttribute('aria-label', c);
      b.style.background = c;
      b.addEventListener('click', () => { $('#bgColor').value = c; });
      $('#swatches').appendChild(b);
    }
    $('#langBtn').addEventListener('click', () => {
      lang = lang === 'fr' ? 'en' : 'fr';
      store.set('legenipng.lang', lang);
      applyI18n();
    });
    $('#form').addEventListener('submit', run);
  }

  buildSliders();
  wire();
  setSplit(50);
  applyPreset('cutout');
  applyI18n();
  loadConfig();
})();
