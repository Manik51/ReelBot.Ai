// ReelBot.Ai (Beta) - Advanced Studio Engine, PWA, Serper Real-Time News & Indic Voices (Sarvam AI / AI4Bharat)

const appState = {
  config: null,
  currentScript: null,
  currentTaskId: null,
  lastVideoFilename: null,
  lastVideoUrl: null,
  pollInterval: null,
  lastLogIndex: 0
};
window.appState = appState;

// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('ReelBot PWA Service Worker Registered', reg))
      .catch(err => console.log('Service Worker registration failed:', err));
  });
}

// DOM Elements
const geminiBadge = document.getElementById('gemini-badge');
const sarvamBadge = document.getElementById('sarvam-badge');
const ai4bharatBadge = document.getElementById('ai4bharat-badge');
const serperBadge = document.getElementById('serper-badge');
const pexelsBadge = document.getElementById('pexels-badge');
const pixabayBadge = document.getElementById('pixabay-badge');
const youtubeBadge = document.getElementById('youtube-badge');

const openSettingsBtn = document.getElementById('open-settings-btn');
const quickOpenSerperBtn = document.getElementById('quick-open-serper-btn');
const closeSettingsBtn = document.getElementById('close-settings-btn');
const cancelSettingsBtn = document.getElementById('cancel-settings-btn');
const saveSettingsBtn = document.getElementById('save-settings-btn');
const settingsModal = document.getElementById('settings-modal');

const settingSarvamKey = document.getElementById('setting-sarvam-key');
const settingAi4bharatKey = document.getElementById('setting-ai4bharat-key');
const settingSerperKey = document.getElementById('setting-serper-key');
const settingGeminiKey = document.getElementById('setting-gemini-key');
const settingPexelsKey = document.getElementById('setting-pexels-key');
const settingPixabayKey = document.getElementById('setting-pixabay-key');
const settingYoutubeJson = document.getElementById('setting-youtube-json');

const findTrendsBtn = document.getElementById('find-trends-btn');
const viralChips = document.getElementById('viral-chips');
const trendEngineBadge = document.getElementById('trend-engine-badge');

const topicInput = document.getElementById('topic-input');
const scriptLangSelect = document.getElementById('script-language');
const scriptToneSelect = document.getElementById('script-tone');
const targetDurationSelect = document.getElementById('target-duration');
const generateScriptBtn = document.getElementById('generate-script-btn');

const stepScriptEditor = document.getElementById('step-script-editor');
const scriptTitleDisplay = document.getElementById('script-title-display');
const estimatedDurationBadge = document.getElementById('estimated-duration-badge');
const scenesContainer = document.getElementById('scenes-container');

const stepCustomization = document.getElementById('step-customization');
const voiceSelect = document.getElementById('voice-select');
const voiceRateSelect = document.getElementById('voice-rate');
const subtitleStyleSelect = document.getElementById('subtitle-style-select');
const subtitlePreviewText = document.getElementById('subtitle-preview-text');
const bgmSelect = document.getElementById('bgm-select');
const bgmVolumeSlider = document.getElementById('bgm-volume');
const bgmVolVal = document.getElementById('bgm-vol-val');
const generateVideoBtn = document.getElementById('generate-video-btn');

const openConfigureBgmBtn = document.getElementById('open-configure-bgm-btn');
const bulkBgmInput = document.getElementById('bulk-bgm-input');
const uploadStatusMsg = document.getElementById('upload-status-msg');

const floatingCreatorBtn = document.getElementById('floating-creator-btn');
const creatorModal = document.getElementById('creator-modal');
const closeCreatorBtn = document.getElementById('close-creator-btn');

const stepProgress = document.getElementById('step-progress');
const progressBar = document.getElementById('progress-bar');
const progressStage = document.getElementById('progress-stage');
const stageSub = document.getElementById('stage-sub');
const stageIcon = document.getElementById('stage-icon');
const progressStatusText = document.getElementById('progress-status-text');
const progressPercent = document.getElementById('progress-percent');
const terminalLogs = document.getElementById('terminal-logs');
const resumeTaskBtn = document.getElementById('resume-task-btn');

const pipeVoice = document.getElementById('pipe-voice');
const pipeSubs = document.getElementById('pipe-subs');
const pipeMedia = document.getElementById('pipe-media');
const pipeRender = document.getElementById('pipe-render');

const stepResult = document.getElementById('step-result');
const finalVideoPlayer = document.getElementById('final-video-player');
const resultTitle = document.getElementById('result-title');
const downloadVideoBtn = document.getElementById('download-video-btn');
const createAnotherBtn = document.getElementById('create-another-btn');

const ytChannelBadge = document.getElementById('yt-channel-badge');
const ytPrivacySelect = document.getElementById('yt-privacy-select');
const directYouTubeUploadBtn = document.getElementById('direct-youtube-upload-btn');
const ytUploadStatus = document.getElementById('yt-upload-status');

const seoTitleInput = document.getElementById('seo-title-input');
const seoDescInput = document.getElementById('seo-desc-input');
const seoTagsInput = document.getElementById('seo-tags-input');
const copyAllSeoBtn = document.getElementById('copy-all-seo-btn');

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
  await fetchConfig();
  setupEventListeners();
  attachViralChipListeners();
});

async function fetchConfig() {
  try {
    const res = await fetch('/api/config');
    if (!res.ok) return;
    const cfg = await res.json();
    appState.config = cfg;
    populateConfigUI(cfg);
  } catch (err) {
    console.error('Failed to fetch config:', err);
  }
}

function populateConfigUI(cfg) {
  updateBadge(geminiBadge, cfg.has_gemini_key, 'Gemini AI');
  updateBadge(sarvamBadge, cfg.has_sarvam_key, 'Sarvam AI');
  updateBadge(ai4bharatBadge, cfg.has_ai4bharat_key, 'AI4Bharat');
  updateBadge(serperBadge, cfg.has_serper_key, 'Serper Live');
  updateBadge(pexelsBadge, cfg.has_pexels_key, 'Pexels');
  updateBadge(pixabayBadge, cfg.has_pixabay_key, 'Pixabay');
  
  if (youtubeBadge) {
    updateBadge(youtubeBadge, cfg.youtube_authenticated, cfg.youtube_channel_title || 'YouTube API');
  }
  if (ytChannelBadge) {
    if (cfg.youtube_authenticated) {
      ytChannelBadge.className = 'badge badge-success';
      ytChannelBadge.textContent = `🟢 ${cfg.youtube_channel_title || 'Channel Connected'}`;
    } else {
      ytChannelBadge.className = 'badge badge-pending';
      ytChannelBadge.textContent = '1-Click Auto Upload';
    }
  }

  updateVoiceDropdownForLang(scriptLangSelect.value);

  // Subtitle Styles
  subtitleStyleSelect.innerHTML = '';
  cfg.subtitle_styles.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = s.name;
    if (s.id === 'hormozi_yellow') opt.selected = true;
    subtitleStyleSelect.appendChild(opt);
  });

  // BGM Tracks
  bgmSelect.innerHTML = '<option value="none">None (Voiceover Only)</option>';
  cfg.bgm_tracks.forEach((b, idx) => {
    const opt = document.createElement('option');
    opt.value = b.id;
    opt.textContent = b.name;
    if (idx === 0) opt.selected = true;
    bgmSelect.appendChild(opt);
  });
}

function updateVoiceDropdownForLang(lang) {
  if (!appState.config || !appState.config.voices) return;

  voiceSelect.innerHTML = '';
  const voices = appState.config.voices;
  const hasSarvam = Boolean(appState.config.has_sarvam_key);

  voices.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.textContent = v.name;

    if (lang === 'Bengali') {
      if (hasSarvam && v.id === 'sarvam:shreya') {
        opt.selected = true;
      } else if (!hasSarvam && v.id === 'bn-IN-TanishaaNeural') {
        opt.selected = true;
      } else if (v.id === 'sarvam:shreya') {
        opt.selected = true;
      }
    } else if (lang === 'Hindi') {
      if (hasSarvam && (v.id === 'sarvam:amit' || v.id === 'sarvam:shreya')) {
        opt.selected = true;
      } else if (!hasSarvam && v.id === 'hi-IN-MadhurNeural') {
        opt.selected = true;
      } else if (v.id === 'sarvam:amit') {
        opt.selected = true;
      }
    } else if (lang === 'English') {
      if (v.id.includes('adam')) opt.selected = true;
    }

    voiceSelect.appendChild(opt);
  });
}

function updateBadge(badgeEl, isConnected, serviceName) {
  if (!badgeEl) return;
  if (isConnected) {
    badgeEl.className = 'badge badge-success';
    badgeEl.textContent = `🟢 ${serviceName} Ready`;
  } else {
    badgeEl.className = 'badge badge-pending';
    badgeEl.textContent = `⚪ ${serviceName} (Optional)`;
  }
}

function setupEventListeners() {
  // Configure Modal
  if (openSettingsBtn) {
    openSettingsBtn.addEventListener('click', () => {
      settingsModal.classList.remove('hidden');
    });
  }

  if (quickOpenSerperBtn) {
    quickOpenSerperBtn.addEventListener('click', () => {
      settingsModal.classList.remove('hidden');
      settingSarvamKey.focus();
    });
  }

  closeSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));
  cancelSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));
  saveSettingsBtn.addEventListener('click', handleSaveSettings);

  // Configure BGM Link
  if (openConfigureBgmBtn) {
    openConfigureBgmBtn.addEventListener('click', () => {
      settingsModal.classList.remove('hidden');
    });
  }

  if (bulkBgmInput) {
    bulkBgmInput.addEventListener('change', handleBulkBgmUpload);
  }

  // Creator Modal
  floatingCreatorBtn.addEventListener('click', () => creatorModal.classList.remove('hidden'));
  closeCreatorBtn.addEventListener('click', () => creatorModal.classList.add('hidden'));

  window.addEventListener('click', (e) => {
    if (e.target === settingsModal) settingsModal.classList.add('hidden');
    if (e.target === creatorModal) creatorModal.classList.add('hidden');
  });

  // Find Trends Button
  findTrendsBtn.addEventListener('click', handleFindTrends);

  // Resume Task Button
  resumeTaskBtn.addEventListener('click', handleResumeTask);

  // Language Change
  scriptLangSelect.addEventListener('change', (e) => {
    updateVoiceDropdownForLang(e.target.value);
  });

  // Subtitle Style Change
  subtitleStyleSelect.addEventListener('change', (e) => {
    const val = e.target.value;
    subtitlePreviewText.className = 'sub-preview';
    if (val === 'hormozi_yellow') subtitlePreviewText.classList.add('hormozi-yellow');
    else if (val === 'hormozi_green') subtitlePreviewText.classList.add('hormozi-green');
    else if (val === 'cyber_cyan') subtitlePreviewText.classList.add('cyber-cyan');
    else if (val === 'crimson_wine') subtitlePreviewText.classList.add('crimson-wine');
    else if (val === 'bold_white') subtitlePreviewText.classList.add('bold-white');
  });

  // BGM Volume Slider
  bgmVolumeSlider.addEventListener('input', (e) => {
    bgmVolVal.textContent = `${e.target.value}%`;
  });

  generateScriptBtn.addEventListener('click', handleGenerateScript);
  generateVideoBtn.addEventListener('click', handleGenerateVideo);

  if (directYouTubeUploadBtn) {
    directYouTubeUploadBtn.addEventListener('click', handleDirectYouTubeUpload);
  }

  if (copyAllSeoBtn) {
    copyAllSeoBtn.addEventListener('click', () => {
      const fullText = `Title:\n${seoTitleInput.value}\n\nDescription:\n${seoDescInput.value}\n\nTags:\n${seoTagsInput.value}`;
      navigator.clipboard.writeText(fullText).then(() => {
        const orig = copyAllSeoBtn.textContent;
        copyAllSeoBtn.textContent = '✅ Copied All!';
        setTimeout(() => { copyAllSeoBtn.textContent = orig; }, 1500);
      });
    });
  }

  createAnotherBtn.addEventListener('click', () => {
    stepResult.classList.add('hidden');
    stepProgress.classList.add('hidden');
    stepScriptEditor.classList.add('hidden');
    stepCustomization.classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

window.copyField = function(inputId, btn) {
  const el = document.getElementById(inputId);
  if (!el) return;
  navigator.clipboard.writeText(el.value).then(() => {
    const orig = btn.textContent;
    btn.textContent = '✅ Copied!';
    setTimeout(() => { btn.textContent = orig; }, 1500);
  });
};

function attachViralChipListeners() {
  const chips = viralChips.querySelectorAll('.topic-chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      viralChips.querySelectorAll('.topic-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      topicInput.value = chip.getAttribute('data-topic');
    });
  });
}

async function handleFindTrends() {
  findTrendsBtn.disabled = true;
  findTrendsBtn.innerHTML = '<span class="btn-icon">⏳</span> Searching Live Google / Serper...';

  try {
    const res = await fetch('/api/find-trends');
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Could not fetch live trends');
    }
    const data = await res.json();
    const trends = data.trends || [];
    const sourceEngine = data.source_engine || 'Real-Time Search';

    if (trendEngineBadge) {
      trendEngineBadge.textContent = sourceEngine;
    }

    if (trends.length > 0) {
      viralChips.innerHTML = '';
      trends.slice(0, 6).forEach((t, idx) => {
        const btn = document.createElement('button');
        btn.className = `topic-chip ${idx === 0 ? 'active' : ''}`;
        btn.setAttribute('data-topic', t.title);
        
        const sourceLabel = t.source || 'Live Source';
        const sourceLink = t.link && t.link !== '#' 
          ? `<a href="${t.link}" target="_blank" class="chip-source-tag" onclick="event.stopPropagation()">${sourceLabel} ↗</a>` 
          : `<span class="chip-source-tag">${sourceLabel}</span>`;

        btn.innerHTML = `
          <span>${t.emoji || '🕵️‍♂️'} ${t.title}</span>
          ${sourceLink}
        `;

        btn.addEventListener('click', () => {
          viralChips.querySelectorAll('.topic-chip').forEach(c => c.classList.remove('active'));
          btn.classList.add('active');
          topicInput.value = t.title;
          if (t.tone) scriptToneSelect.value = t.tone;
        });

        viralChips.appendChild(btn);
      });

      if (trends[0]) {
        topicInput.value = trends[0].title;
      }
    }
  } catch (err) {
    alert('Live Search Note: ' + err.message);
  } finally {
    findTrendsBtn.disabled = false;
    findTrendsBtn.innerHTML = '<span class="btn-icon">⚡</span> Search Live True Crime News';
  }
}

async function handleSaveSettings() {
  const payload = {};
  if (settingSarvamKey.value.trim()) payload.sarvam_api_key = settingSarvamKey.value.trim();
  if (settingAi4bharatKey.value.trim()) payload.ai4bharat_api_key = settingAi4bharatKey.value.trim();
  if (settingSerperKey.value.trim()) payload.serper_api_key = settingSerperKey.value.trim();
  if (settingGeminiKey.value.trim()) payload.gemini_api_key = settingGeminiKey.value.trim();
  if (settingPexelsKey.value.trim()) payload.pexels_api_key = settingPexelsKey.value.trim();
  if (settingPixabayKey.value.trim()) payload.pixabay_api_key = settingPixabayKey.value.trim();

  if (settingYoutubeJson && settingYoutubeJson.value.trim()) {
    try {
      await fetch('/api/youtube/setup-credentials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_secret_json: settingYoutubeJson.value.trim() })
      });
    } catch (e) {
      console.error('Error saving YouTube secret:', e);
    }
  }

  try {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      settingsModal.classList.add('hidden');
      await fetchConfig();
      alert('Settings saved successfully!');
    }
  } catch (err) {
    alert('Failed to save settings: ' + err.message);
  }
}

async function handleBulkBgmUpload(e) {
  const files = e.target.files;
  if (!files || files.length === 0) return;

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  uploadStatusMsg.textContent = `⏳ Uploading ${files.length} audio tracks...`;

  try {
    const res = await fetch('/api/upload-bgm-bulk', {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      uploadStatusMsg.textContent = `✅ ${data.message}!`;
      await fetchConfig();
      setTimeout(() => { uploadStatusMsg.textContent = ''; }, 3000);
    } else {
      uploadStatusMsg.textContent = '❌ Upload failed.';
    }
  } catch (err) {
    uploadStatusMsg.textContent = '❌ Error: ' + err.message;
  }
}

async function handleGenerateScript() {
  const topic = topicInput.value.trim();
  if (!topic) {
    alert('Please enter or select a video topic first.');
    return;
  }

  generateScriptBtn.disabled = true;
  generateScriptBtn.innerHTML = '<span class="btn-icon">⏳</span> Writing Synchronized Visual Scenes (Gemini AI)...';

  try {
    const res = await fetch('/api/generate-script', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic,
        language: scriptLangSelect.value,
        tone: scriptToneSelect.value,
        target_duration_sec: parseInt(targetDurationSelect.value, 10)
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Script generation failed');
    }

    const script = await res.json();
    appState.currentScript = script;
    renderScenesUI(script);

    // Populate YouTube SEO Pack
    if (script.seo) {
      seoTitleInput.value = script.seo.youtube_title || script.title;
      seoDescInput.value = script.seo.youtube_description || (script.title + " - Watch till the end! #shorts");
      seoTagsInput.value = (script.seo.hashtags || ["#shorts", "#mystery", "#viral"]).join(' ');
    } else {
      seoTitleInput.value = `${script.title} 😱 #shorts`;
      seoDescInput.value = `Discover the chilling truth behind ${script.title}. Watch till the end!`;
      seoTagsInput.value = '#shorts #mystery #truecrime #viral';
    }

    updateVoiceDropdownForLang(scriptLangSelect.value);

    stepScriptEditor.classList.remove('hidden');
    stepCustomization.classList.remove('hidden');
    stepScriptEditor.scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    alert('Script Generation Error: ' + err.message);
  } finally {
    generateScriptBtn.disabled = false;
    generateScriptBtn.innerHTML = '<span class="btn-icon">⚡</span> Generate Synchronized Video Script';
  }
}

function renderScenesUI(script) {
  scenesContainer.innerHTML = '';
  let totalWords = 0;
  scriptTitleDisplay.textContent = script.title || 'Scene-by-Scene Script';

  script.scenes.forEach((scene, idx) => {
    const isHook = idx === 0;
    const words = scene.narration.trim().split(/\s+/).length;
    totalWords += words;
    const subText = scene.subtitle_text || scene.narration;

    // Calculate exact timestamp (e.g. 0:00-0:03, 0:03-0:06)
    const startSec = idx * 3;
    const endSec = (idx + 1) * 3;
    const formatTime = (s) => {
      const mins = Math.floor(s / 60);
      const secs = s % 60;
      return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    };
    const timeRange = scene.time_range || `${formatTime(startSec)}-${formatTime(endSec)}`;
    const visualTag = scene.visual_tag || (scene.keywords && scene.keywords[0] ? scene.keywords[0] : 'cinematic atmospheric scene');

    const card = document.createElement('div');
    card.className = `scene-card ${isHook ? 'hook-scene' : ''}`;
    card.innerHTML = `
      <div class="scene-card-header">
        <div class="scene-title">
          <span>${scene.suggested_emoji || '🎬'}</span>
          <span>[SCENE ${scene.scene_id} — ${timeRange}] ${isHook ? '<span class="badge-hook">🔥 HOOK (0-3s)</span>' : ''}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          ${isHook ? '<button class="btn-reroll-hook" onclick="rerollHook(this)">🎲 Re-roll Hook</button>' : ''}
          <span class="kw-label">~${(scene.estimated_seconds || 3.0).toFixed(1)}s</span>
        </div>
      </div>

      <div class="scene-inputs-grid" style="display: flex; flex-direction: column; gap: 10px;">
        <!-- Visual Tag Field (Exact 1-to-1 Match) -->
        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px; color: var(--accent-cyan); text-transform: uppercase; letter-spacing: 0.5px;">🎥 Visual Tag (Exact Physical Stock Match):</label>
          <input type="text" class="scene-visual-tag-input" value="${visualTag}" placeholder="e.g. busy indian marketplace crowds shopping" style="border-color: rgba(0, 229, 255, 0.45); font-weight: 600;">
        </div>

        <!-- Spoken Voiceover Narration -->
        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">🎙️ Voiceover (Narration - 5-7 words with human pauses):</label>
          <textarea class="scene-narration-input" rows="2">${scene.narration}</textarea>
        </div>

        <!-- On-Screen Subtitle -->
        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px; color: var(--wine-bright); text-transform: uppercase; letter-spacing: 0.5px;">🔤 On-Screen Subtitle (Banglish / Hinglish / English):</label>
          <input type="text" class="scene-subtitle-input" value="${subText.toUpperCase()}" placeholder="BANGLISH / HINGLISH / ENGLISH SUBTITLE" style="font-weight: 700; letter-spacing: 0.5px; border-color: rgba(196, 30, 58, 0.45);">
        </div>
      </div>
    `;
    scenesContainer.appendChild(card);
  });

  const estDuration = (totalWords / 2.5).toFixed(0);
  estimatedDurationBadge.textContent = `⏱️ ~${estDuration}s (${script.scenes.length} Scenes, ${totalWords} Words)`;
}

// 1-Click Viral Hook Re-Roller
window.rerollHook = function(btn) {
  const card = btn.closest('.scene-card');
  const narrationInput = card.querySelector('.scene-narration-input');
  const subtitleInput = card.querySelector('.scene-subtitle-input');
  const visualTagInput = card.querySelector('.scene-visual-tag-input');

  const hooks = [
    { n: "STOP SCROLLING! ... This chilling incident was completely covered up.", s: "STOP SCROLLING! THIS WAS COVERED UP!", v: "detective examining classified confidential files night" },
    { n: "In 1971, ... a man vanished into thin air with $200,000.", s: "A MAN VANISHED INTO THIN AIR!", v: "airplane flying in dark stormy night sky" },
    { n: "When detectives entered the room, ... they found something impossible.", s: "THEY FOUND SOMETHING IMPOSSIBLE!", v: "police barrier crime scene tape flashing red blue lights" },
    { n: "ভারতের অর্থনীতি এখন, ... বিশ্বের রেকর্ড গতিতে বাড়ছে।", s: "BHAROTER ORTHONITI RECORD GOTITE BARCHE", v: "stock market graph going up india financial district" }
  ];

  const randomHook = hooks[Math.floor(Math.random() * hooks.length)];
  narrationInput.value = randomHook.n;
  subtitleInput.value = randomHook.s;
  if (visualTagInput) visualTagInput.value = randomHook.v;

  btn.textContent = "✨ Hook Updated!";
  setTimeout(() => { btn.textContent = "🎲 Re-roll Hook"; }, 1500);
};

async function handleGenerateVideo() {
  if (!appState.currentScript) return;

  terminalLogs.innerHTML = '<div class="log-line text-cyan">[00:00.00] ⚡ ReelBot.Ai Engine initialized. Spawning worker thread...</div>';
  appState.lastLogIndex = 0;
  resumeTaskBtn.classList.add('hidden');

  const visualTagInputs = document.querySelectorAll('.scene-visual-tag-input');
  const narrationInputs = document.querySelectorAll('.scene-narration-input');
  const subtitleInputs = document.querySelectorAll('.scene-subtitle-input');
  
  const updatedScenes = appState.currentScript.scenes.map((sc, idx) => {
    const vTag = visualTagInputs[idx] ? visualTagInputs[idx].value.trim() : (sc.visual_tag || '');
    return {
      scene_id: sc.scene_id,
      time_range: sc.time_range || `0:${(idx*3).toString().padStart(2, '0')}-0:${((idx+1)*3).toString().padStart(2, '0')}`,
      visual_tag: vTag,
      narration: narrationInputs[idx].value.trim(),
      subtitle_text: subtitleInputs[idx] ? subtitleInputs[idx].value.trim().toUpperCase() : (sc.subtitle_text || sc.narration),
      keywords: vTag ? [vTag, ...(sc.keywords || [])] : (sc.keywords || []),
      suggested_emoji: sc.suggested_emoji,
      estimated_seconds: sc.estimated_seconds
    };
  });

  const payload = {
    title: appState.currentScript.title || 'Viral Short',
    scenes: updatedScenes,
    voice_id: voiceSelect.value,
    voice_rate: voiceRateSelect.value,
    subtitle_style_id: subtitleStyleSelect.value,
    bgm_track_id: bgmSelect.value,
    bgm_volume: parseFloat(bgmVolumeSlider.value) / 100.0
  };

  generateVideoBtn.disabled = true;
  generateVideoBtn.innerHTML = '<span class="btn-icon">⏳</span> Launching Video Synthesis...';

  try {
    const res = await fetch('/api/generate-video', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to start video task');
    }

    const data = await res.json();
    appState.currentTaskId = data.task_id;

    stepProgress.classList.remove('hidden');
    stepResult.classList.add('hidden');
    stepProgress.scrollIntoView({ behavior: 'smooth' });

    startPolling(data.task_id);
  } catch (err) {
    alert('Video Generation Error: ' + err.message);
    generateVideoBtn.disabled = false;
    generateVideoBtn.innerHTML = '<span class="btn-icon">🚀</span> Render Complete 1080x1920 Viral Video';
  }
}

async function handleResumeTask() {
  if (!appState.currentTaskId) return;

  resumeTaskBtn.disabled = true;
  resumeTaskBtn.textContent = '⏳ Resuming...';

  try {
    const res = await fetch(`/api/resume-task/${appState.currentTaskId}`, {
      method: 'POST'
    });
    if (res.ok) {
      resumeTaskBtn.classList.add('hidden');
      startPolling(appState.currentTaskId);
    } else {
      alert('Could not resume task.');
    }
  } catch (e) {
    alert('Resume error: ' + e.message);
  } finally {
    resumeTaskBtn.disabled = false;
    resumeTaskBtn.textContent = '🔁 Resume Generation';
  }
}

function startPolling(taskId) {
  if (appState.pollInterval) clearInterval(appState.pollInterval);

  appState.pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/task-status/${taskId}`);
      if (!res.ok) return;

      const task = await res.json();
      updateProgressUI(task);

      if (task.status === 'completed') {
        clearInterval(appState.pollInterval);
        handleTaskSuccess(task);
      } else if (task.status === 'failed') {
        clearInterval(appState.pollInterval);
        handleTaskFailure(task);
      }
    } catch (err) {
      console.error('Error polling status:', err);
    }
  }, 1200);
}
window.startPolling = startPolling;

function updateProgressUI(task) {
  const p = task.progress || 0;
  progressBar.style.width = `${p}%`;
  progressPercent.textContent = `${p}%`;
  progressStage.textContent = task.stage || 'Rendering...';
  progressStatusText.textContent = task.stage || 'Processing...';

  const phase = task.current_phase || 'voice';
  if (phase === 'voice') {
    stageIcon.textContent = '🎙️';
    stageSub.textContent = 'Synthesizing voiceover with studio broadcast mastering EQ...';
  } else if (phase === 'subtitles') {
    stageIcon.textContent = '🔤';
    stageSub.textContent = 'Calculating millisecond word-by-word Alex Hormozi animated ASS captions...';
  } else if (phase === 'footage') {
    stageIcon.textContent = '🎥';
    stageSub.textContent = 'Matching exact physical stock clips to spoken narration with 9:16 vertical framing...';
  } else if (phase === 'render') {
    stageIcon.textContent = '⚡';
    stageSub.textContent = 'Compositing clips, mixing ducked BGM, and burning captions via multi-threaded FFmpeg...';
  }

  pipeVoice.className = 'pipe-step' + (p >= 15 ? (p > 35 ? ' done' : ' active') : '');
  pipeSubs.className = 'pipe-step' + (p >= 35 ? (p > 45 ? ' done' : ' active') : '');
  pipeMedia.className = 'pipe-step' + (p >= 45 ? (p > 80 ? ' done' : ' active') : '');
  pipeRender.className = 'pipe-step' + (p >= 80 ? (p === 100 ? ' done' : ' active') : '');

  if (task.logs && task.logs.length > appState.lastLogIndex) {
    for (let i = appState.lastLogIndex; i < task.logs.length; i++) {
      const line = document.createElement('div');
      const text = task.logs[i];
      line.className = 'log-line' + (text.includes('❌') ? ' text-red' : (text.includes('✅') || text.includes('🎉') ? ' text-green' : ' text-cyan'));
      line.textContent = text;
      terminalLogs.appendChild(line);
    }
    appState.lastLogIndex = task.logs.length;
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
  }
}

function handleTaskSuccess(task) {
  generateVideoBtn.disabled = false;
  generateVideoBtn.innerHTML = '<span class="btn-icon">🚀</span> Render Complete 1080x1920 Viral Video';

  appState.lastVideoFilename = task.filename || `short_${task.task_id}.mp4`;
  appState.lastVideoUrl = task.video_url;
  resultTitle.textContent = appState.currentScript.title || 'Viral Video';
  finalVideoPlayer.src = task.video_url;
  downloadVideoBtn.href = task.video_url;
  downloadVideoBtn.download = task.filename || 'viral_short.mp4';

  stepProgress.classList.add('hidden');
  stepResult.classList.remove('hidden');
  stepResult.scrollIntoView({ behavior: 'smooth' });
}

function handleTaskFailure(task) {
  generateVideoBtn.disabled = false;
  generateVideoBtn.innerHTML = '<span class="btn-icon">🚀</span> Render Complete 1080x1920 Viral Video';
  resumeTaskBtn.classList.remove('hidden');
  alert('Video Generation Stopped: ' + (task.error || 'Unknown error occurred') + '\n\nClick "🔁 Resume Generation" in the terminal header to continue from checkpoint!');
}

async function handleDirectYouTubeUpload() {
  if (!appState.lastVideoFilename) {
    alert('কোনো ভিডিও রেডি নেই। আগে ভিডিও Render করুন।');
    return;
  }

  const script = appState.currentScript;

  // ── Auto-fill SEO from generated script ────────────────────────────────
  const autoTitle = (seoTitleInput && seoTitleInput.value.trim())
    || (script && script.seo && script.seo.youtube_title)
    || (script && script.title)
    || 'Viral Mystery Short #Shorts';

  const autoDesc = (seoDescInput && seoDescInput.value.trim())
    || (script && script.seo && script.seo.youtube_description)
    || `${autoTitle}\n\n#shorts #mystery #viral #truecrime`;

  // Merge script hashtags + user-added tags + mandatory #reelbot.ai
  const scriptHashtags = (script && script.seo && script.seo.hashtags) || [];
  const scriptTags     = (script && script.seo && script.seo.tags) || [];
  const userRawTags    = seoTagsInput && seoTagsInput.value.trim()
    ? seoTagsInput.value.trim().split(/[\s,]+/)
    : [];

  const allTags = [
    ...scriptHashtags,
    ...scriptTags,
    ...userRawTags,
    '#reelbot.ai',   // ALWAYS present
    '#shorts',
    '#viral',
    '#mystery',
    '#truecrime',
  ].filter((t, i, arr) => t && arr.indexOf(t) === i); // deduplicate

  const privacy = (ytPrivacySelect && ytPrivacySelect.value) || 'public';

  // ── Confirm before upload ───────────────────────────────────────────────
  const confirmMsg = `🔴 YouTube-এ সরাসরি Upload হবে!\n\n📌 Title: ${autoTitle}\n🔒 Privacy: ${privacy}\n#️⃣ Tags: ${allTags.slice(0,6).join(' ')} ...\n\nConfirm করুন?`;
  if (!confirm(confirmMsg)) return;

  // ── Call API ────────────────────────────────────────────────────────────
  ytUploadStatus.classList.remove('hidden');
  ytUploadStatus.className = 'yt-upload-status-msg';
  ytUploadStatus.innerHTML = '⏳ <strong>YouTube-এ Upload হচ্ছে...</strong> একটু অপেক্ষা করুন।';

  try {
    const res = await fetch('/api/youtube/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_filename: appState.lastVideoFilename,
        title: autoTitle,
        description: autoDesc,
        tags: allTags,
        privacy_status: privacy,
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Upload failed');
    }

    if (data.needs_auth) {
      ytUploadStatus.className = 'yt-upload-status-msg';
      ytUploadStatus.innerHTML = `
        🔑 <strong>YouTube Account Connect করতে হবে:</strong><br>
        একটি Google Sign-in উইন্ডো খুলেছে। সেখানে আপনার চ্যানেল দিয়ে <strong>"Allow / Continue"</strong> দিন।<br>
        অনুমোদন দেওয়ার সাথে সাথেই স্বয়ংক্রিয়ভাবে ভিডিও আপলোড শুরু হয়ে যাবে!
        <br><br>
        <a href="${data.auth_url || '#'}" target="_blank" class="btn btn-sm btn-primary" style="display:inline-block; margin-top:8px;">
          🔗 Google Login Window ওপেন করুন
        </a>
      `;

      if (data.auth_url) {
        window.open(data.auth_url, '_blank');
      }

      // Poll for authentication completion and auto-retry upload
      const authChecker = setInterval(async () => {
        try {
          const stRes = await fetch('/api/youtube/status');
          const stData = await stRes.json();
          if (stData.authenticated) {
            clearInterval(authChecker);
            ytUploadStatus.innerHTML = `🟢 <strong>Channel Connected: ${stData.channel_title}!</strong> এখন ভিডিও আপলোড হচ্ছে...`;
            // Auto re-trigger upload
            handleDirectYouTubeUpload();
          }
        } catch (e) {}
      }, 2000);

      return;
    }

    ytUploadStatus.className = 'yt-upload-status-msg success';
    ytUploadStatus.innerHTML = `
      🎉 <strong>YouTube Upload সফল!</strong><br>
      📺 <a href="${data.watch_url}" target="_blank" style="color:#00E5FF; font-weight:700; text-decoration:underline;">
        ▶ এখনই লাইভ দেখুন: ${data.watch_url}
      </a><br>
      🏷️ <strong>#reelbot.ai</strong> সহ ${data.tags ? data.tags.length : ''} টি ট্যাগ যুক্ত করে শর্টস আপলোড হয়েছে!
    `;
  } catch (err) {
    ytUploadStatus.className = 'yt-upload-status-msg error';
    ytUploadStatus.innerHTML = `❌ <strong>Upload Error:</strong> ${err.message}`;
  }
}

