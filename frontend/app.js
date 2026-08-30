// ReelBot.Ai (Beta) - Advanced Studio Engine, PWA & YouTube SEO Pack

const appState = {
  config: null,
  currentScript: null,
  currentTaskId: null,
  pollInterval: null,
  lastLogIndex: 0
};

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
const pexelsBadge = document.getElementById('pexels-badge');
const pixabayBadge = document.getElementById('pixabay-badge');

const openSettingsBtn = document.getElementById('open-settings-btn');
const closeSettingsBtn = document.getElementById('close-settings-btn');
const cancelSettingsBtn = document.getElementById('cancel-settings-btn');
const saveSettingsBtn = document.getElementById('save-settings-btn');
const settingsModal = document.getElementById('settings-modal');

const settingGeminiKey = document.getElementById('setting-gemini-key');
const settingPexelsKey = document.getElementById('setting-pexels-key');
const settingPixabayKey = document.getElementById('setting-pixabay-key');

const findTrendsBtn = document.getElementById('find-trends-btn');
const trendingGridContainer = document.getElementById('trending-grid-container');

const videoTopicInput = document.getElementById('video-topic');
const scriptLangSelect = document.getElementById('script-lang');
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
const openCreatorModalNavBtn = document.getElementById('open-creator-modal-nav-btn');
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

const seoTitleInput = document.getElementById('seo-title-input');
const seoDescInput = document.getElementById('seo-desc-input');
const seoTagsInput = document.getElementById('seo-tags-input');
const copyAllSeoBtn = document.getElementById('copy-all-seo-btn');

// Initialize App
document.addEventListener('DOMContentLoaded', async () => {
  await fetchConfig();
  setupEventListeners();
  attachTrendingChipListeners();
});

async function fetchConfig() {
  try {
    const res = await fetch('/api/config');
    const cfg = await res.json();
    appState.config = cfg;
    populateConfigUI(cfg);
  } catch (err) {
    console.error('Failed to fetch config:', err);
  }
}

function populateConfigUI(cfg) {
  // Update status badges (inside configure modal)
  updateBadge(geminiBadge, cfg.has_gemini_key, 'Gemini AI');
  updateBadge(pexelsBadge, cfg.has_pexels_key, 'Pexels');
  updateBadge(pixabayBadge, cfg.has_pixabay_key, 'Pixabay');

  // Update voices based on current language
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

  voices.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.textContent = v.name;
    
    // Smart language matching for 100% natural pronunciation
    if (lang === 'Hindi' && v.id === 'hi-IN-MadhurNeural') {
      opt.selected = true;
    } else if (lang === 'Bengali' && v.id === 'bn-IN-TanishaaNeural') {
      opt.selected = true;
    } else if (lang === 'English' && v.id === 'kokoro:am_adam') {
      opt.selected = true;
    }
    voiceSelect.appendChild(opt);
  });
}

function updateBadge(el, isConnected, name) {
  if (!el) return;
  if (isConnected) {
    el.className = 'badge badge-connected';
    el.textContent = `${name} Connected`;
  } else {
    el.className = 'badge badge-pending';
    el.textContent = `${name} (Key Needed)`;
  }
}

function attachTrendingChipListeners() {
  document.querySelectorAll('.trending-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.trending-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const topic = chip.getAttribute('data-topic');
      const tone = chip.getAttribute('data-tone');

      if (topic) {
        videoTopicInput.value = topic;
        videoTopicInput.focus();
      }
      if (tone) {
        scriptToneSelect.value = tone;
      }
    });
  });
}

function setupEventListeners() {
  // Configure Modal
  const openConfigModal = () => {
    if (appState.config) {
      settingGeminiKey.value = '';
      settingPexelsKey.value = '';
      settingPixabayKey.value = '';
    }
    settingsModal.classList.remove('hidden');
  };

  openSettingsBtn.addEventListener('click', openConfigModal);
  if (openConfigureBgmBtn) openConfigureBgmBtn.addEventListener('click', openConfigModal);

  closeSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));
  cancelSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));

  saveSettingsBtn.addEventListener('click', async () => {
    const body = {};
    if (settingGeminiKey.value.trim()) body.gemini_api_key = settingGeminiKey.value.trim();
    if (settingPexelsKey.value.trim()) body.pexels_api_key = settingPexelsKey.value.trim();
    if (settingPixabayKey.value.trim()) body.pixabay_api_key = settingPixabayKey.value.trim();

    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (res.ok) {
        settingsModal.classList.add('hidden');
        await fetchConfig();
      }
    } catch (err) {
      alert('Error saving settings: ' + err);
    }
  });

  // Creator Modal / Drawer
  const openCreatorModal = () => creatorModal.classList.remove('hidden');
  const closeCreatorModal = () => creatorModal.classList.add('hidden');

  floatingCreatorBtn.addEventListener('click', openCreatorModal);
  if (openCreatorModalNavBtn) openCreatorModalNavBtn.addEventListener('click', openCreatorModal);
  closeCreatorBtn.addEventListener('click', closeCreatorModal);

  // Bulk BGM Upload input handler
  bulkBgmInput.addEventListener('change', async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    uploadStatusMsg.textContent = `Uploading ${files.length} audio tracks...`;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const res = await fetch('/api/upload-bgm-bulk', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      uploadStatusMsg.textContent = `✅ ${data.message}`;
      await fetchConfig();
    } catch (err) {
      uploadStatusMsg.textContent = `❌ Upload failed: ${err.message}`;
    }
  });

  // Resume / Retry Pipeline Button
  resumeTaskBtn.addEventListener('click', async () => {
    if (!appState.currentTaskId) return;

    resumeTaskBtn.classList.add('hidden');
    generateVideoBtn.disabled = true;
    generateVideoBtn.innerHTML = '<span class="btn-icon">⏳</span> Resuming Video Pipeline...';

    try {
      const res = await fetch(`/api/resume-task/${appState.currentTaskId}`, { method: 'POST' });
      if (res.ok) {
        startPolling(appState.currentTaskId);
      }
    } catch (err) {
      alert('Failed to resume: ' + err.message);
    }
  });

  // Copy All SEO Metadata Button
  copyAllSeoBtn.addEventListener('click', () => {
    const title = seoTitleInput.value;
    const desc = seoDescInput.value;
    const tags = seoTagsInput.value;

    const fullText = `${title}\n\n${desc}\n\n${tags}`;
    navigator.clipboard.writeText(fullText).then(() => {
      copyAllSeoBtn.textContent = '✅ Copied All!';
      setTimeout(() => { copyAllSeoBtn.textContent = '📋 Copy All'; }, 2000);
    });
  });

  // Find Trends AI Button
  findTrendsBtn.addEventListener('click', handleFindTrends);

  // Language Change Listener -> Updates Smart Voice Default
  scriptLangSelect.addEventListener('change', (e) => {
    updateVoiceDropdownForLang(e.target.value);
  });

  // Subtitle Preview Switcher
  subtitleStyleSelect.addEventListener('change', (e) => {
    const val = e.target.value;
    subtitlePreviewText.className = 'sub-preview';
    if (val === 'hormozi_yellow') subtitlePreviewText.classList.add('hormozi-yellow');
    else if (val === 'hormozi_green') subtitlePreviewText.classList.add('hormozi-green');
    else if (val === 'cyber_cyan') subtitlePreviewText.classList.add('cyber-cyan');
    else if (val === 'crimson_wine') subtitlePreviewText.classList.add('crimson-wine');
    else if (val === 'bold_white') subtitlePreviewText.classList.add('bold-white');
  });

  // Volume Slider
  bgmVolumeSlider.addEventListener('input', (e) => {
    bgmVolVal.textContent = `${e.target.value}%`;
  });

  // Generate Script Button
  generateScriptBtn.addEventListener('click', handleGenerateScript);

  // Generate Video Button
  generateVideoBtn.addEventListener('click', handleGenerateVideo);

  // Create Another Button
  createAnotherBtn.addEventListener('click', () => {
    stepResult.classList.add('hidden');
    stepProgress.classList.add('hidden');
    stepScriptEditor.classList.add('hidden');
    stepCustomization.classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// Copy inline field helper
window.copyField = function(inputId, btn) {
  const el = document.getElementById(inputId);
  if (!el) return;
  navigator.clipboard.writeText(el.value).then(() => {
    const orig = btn.textContent;
    btn.textContent = '✅ Copied!';
    setTimeout(() => { btn.textContent = orig; }, 1500);
  });
};

async function handleFindTrends() {
  findTrendsBtn.disabled = true;
  findTrendsBtn.innerHTML = '<span class="btn-icon">⏳</span> Searching Trends...';

  try {
    const res = await fetch('/api/find-trends');
    if (!res.ok) throw new Error('Could not fetch trends');
    const data = await res.json();
    const trends = data.trends || [];

    if (trends.length > 0) {
      trendingGridContainer.innerHTML = '';
      trends.forEach(t => {
        const btn = document.createElement('button');
        btn.className = 'chip trending-chip';
        btn.setAttribute('data-topic', t.title);
        btn.setAttribute('data-tone', t.tone || 'High Energy / Viral');
        btn.innerHTML = `
          <span><span class="chip-emoji">${t.emoji || '🔥'}</span> ${t.title.length > 32 ? t.title.substring(0, 32) + '...' : t.title}</span>
          <span class="chip-views">${t.views_potential || 'Viral'}</span>
        `;
        trendingGridContainer.appendChild(btn);
      });
      attachTrendingChipListeners();
    }
  } catch (err) {
    console.error('Find trends error:', err);
  } finally {
    findTrendsBtn.disabled = false;
    findTrendsBtn.innerHTML = '<span class="btn-icon">⚡</span> Find Trends (AI Search)';
  }
}

async function handleGenerateScript() {
  const topic = videoTopicInput.value.trim();
  if (!topic) {
    alert('Please enter or select a video topic first.');
    return;
  }

  generateScriptBtn.disabled = true;
  generateScriptBtn.innerHTML = '<span class="btn-icon">⏳</span> Writing 18-20 Rapid Scenes (Gemini AI)...';

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
      seoTagsInput.value = (script.seo.hashtags || ["#shorts", "#viral", "#reels"]).join(' ');
    } else {
      seoTitleInput.value = `${script.title} 😱 #shorts`;
      seoDescInput.value = `Discover ${script.title}. Watch till the end! Subscribe for more viral shorts.`;
      seoTagsInput.value = '#shorts #viral #reels #facts #trending';
    }

    // Auto-update voice recommendation for this language
    updateVoiceDropdownForLang(scriptLangSelect.value);

    stepScriptEditor.classList.remove('hidden');
    stepCustomization.classList.remove('hidden');
    stepScriptEditor.scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    alert('Script Generation Error: ' + err.message);
  } finally {
    generateScriptBtn.disabled = false;
    generateScriptBtn.innerHTML = '<span class="btn-icon">⚡</span> Generate Viral 18-Scene Script';
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

    const card = document.createElement('div');
    card.className = `scene-card ${isHook ? 'hook-scene' : ''}`;
    card.innerHTML = `
      <div class="scene-card-header">
        <div class="scene-title">
          <span>${scene.suggested_emoji || '🎬'}</span>
          <span>Scene ${scene.scene_id} ${isHook ? '<span class="badge-hook">🔥 HOOK (0-3s)</span>' : ''}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          ${isHook ? '<button class="btn-reroll-hook" onclick="rerollHook(this)">🎲 Re-roll Hook</button>' : ''}
          <span class="kw-label">~${(scene.estimated_seconds || 3.0).toFixed(1)}s</span>
        </div>
      </div>

      <div class="scene-inputs-grid" style="display: flex; flex-direction: column; gap: 10px;">
        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">🎙️ Spoken Voiceover (Narration)</label>
          <textarea class="scene-narration-input" rows="2">${scene.narration}</textarea>
        </div>

        <div class="form-group" style="margin-bottom: 0;">
          <label style="font-size: 11px; color: var(--wine-bright); text-transform: uppercase; letter-spacing: 0.5px;">🔤 On-Screen Subtitle (Hinglish / Banglish / English)</label>
          <input type="text" class="scene-subtitle-input" value="${subText.toUpperCase()}" placeholder="BANGLISH / HINGLISH / ENGLISH SUBTITLE" style="font-weight: 700; letter-spacing: 0.5px; border-color: rgba(196, 30, 58, 0.45);">
        </div>
      </div>

      <div class="scene-keywords-row">
        <span class="kw-label">Visual Keywords:</span>
        ${scene.keywords.map(kw => `<span class="kw-tag">${kw}</span>`).join('')}
      </div>
    `;
    scenesContainer.appendChild(card);
  });

  const estDuration = (totalWords / 2.6).toFixed(0);
  estimatedDurationBadge.textContent = `⏱️ ~${estDuration}s (${script.scenes.length} Scenes, ${totalWords} Words)`;
}

// 1-Click Viral Hook Re-Roller
window.rerollHook = function(btn) {
  const card = btn.closest('.scene-card');
  const narrationInput = card.querySelector('.scene-narration-input');
  const subtitleInput = card.querySelector('.scene-subtitle-input');

  const hooks = [
    { n: "STOP SCROLLING! This secret will completely change your perspective forever.", s: "STOP SCROLLING! THIS SECRET WILL CHANGE EVERYTHING!" },
    { n: "99% of people have no idea about this shocking truth.", s: "99% OF PEOPLE HAVE NO IDEA ABOUT THIS!" },
    { n: "If you watch only one video today, make sure it is this one.", s: "WATCH THIS BEFORE YOU REGRET IT!" },
    { n: "Here is the dark psychological secret nobody warned you about.", s: "THE DARK SECRET NOBODY WARNED YOU ABOUT!" }
  ];

  const randomHook = hooks[Math.floor(Math.random() * hooks.length)];
  narrationInput.value = randomHook.n;
  subtitleInput.value = randomHook.s;

  btn.textContent = "✨ Hook Updated!";
  setTimeout(() => { btn.textContent = "🎲 Re-roll Hook"; }, 1500);
};

async function handleGenerateVideo() {
  if (!appState.currentScript) return;

  // Reset terminal
  terminalLogs.innerHTML = '<div class="log-line text-cyan">[00:00.00] ⚡ ReelBot.Ai Engine initialized. Spawning worker thread...</div>';
  appState.lastLogIndex = 0;
  resumeTaskBtn.classList.add('hidden');

  // Extract edited scenes
  const narrationInputs = document.querySelectorAll('.scene-narration-input');
  const subtitleInputs = document.querySelectorAll('.scene-subtitle-input');
  const updatedScenes = appState.currentScript.scenes.map((sc, idx) => {
    return {
      scene_id: sc.scene_id,
      narration: narrationInputs[idx].value.trim(),
      subtitle_text: subtitleInputs[idx] ? subtitleInputs[idx].value.trim().toUpperCase() : (sc.subtitle_text || sc.narration),
      keywords: sc.keywords,
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

    // Show Progress section
    stepProgress.classList.remove('hidden');
    stepResult.classList.add('hidden');
    stepProgress.scrollIntoView({ behavior: 'smooth' });

    startPolling(data.task_id);
  } catch (err) {
    alert('Video Generation Error: ' + err.message);
    generateVideoBtn.disabled = false;
    generateVideoBtn.innerHTML = '<span class="btn-icon">🚀</span> Render Complete 1080x1920 Viral Short Video';
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

function updateProgressUI(task) {
  const p = task.progress || 0;
  progressBar.style.width = `${p}%`;
  progressPercent.textContent = `${p}%`;
  progressStage.textContent = task.stage || 'Rendering...';
  progressStatusText.textContent = task.stage || 'Processing...';

  // Update animated stage icon & headline based on phase
  const phase = task.current_phase || 'voice';
  if (phase === 'voice') {
    stageIcon.textContent = '🎙️';
    stageSub.textContent = 'Synthesizing crystal-clear vocal track with broadcast mastering EQ...';
  } else if (phase === 'subtitles') {
    stageIcon.textContent = '🔤';
    stageSub.textContent = 'Calculating millisecond word-by-word Alex Hormozi animated ASS captions...';
  } else if (phase === 'footage') {
    stageIcon.textContent = '🎥';
    stageSub.textContent = 'Searching & downloading exact matching 9:16 vertical HD stock clips...';
  } else if (phase === 'render') {
    stageIcon.textContent = '⚡';
    stageSub.textContent = 'Compositing clips, mixing ducked BGM, and burning captions via multi-threaded FFmpeg...';
  }

  // Highlight step indicators
  pipeVoice.className = 'pipe-step' + (p >= 15 ? (p > 35 ? ' done' : ' active') : '');
  pipeSubs.className = 'pipe-step' + (p >= 35 ? (p > 45 ? ' done' : ' active') : '');
  pipeMedia.className = 'pipe-step' + (p >= 45 ? (p > 80 ? ' done' : ' active') : '');
  pipeRender.className = 'pipe-step' + (p >= 80 ? (p === 100 ? ' done' : ' active') : '');

  // Stream terminal logs
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
  generateVideoBtn.innerHTML = '<span class="btn-icon">🚀</span> Render Complete 1080x1920 Viral Short Video';

  resultTitle.textContent = appState.currentScript.title || 'Viral Short';
  finalVideoPlayer.src = task.video_url;
  downloadVideoBtn.href = task.video_url;
  downloadVideoBtn.download = task.filename || 'viral_short.mp4';

  stepProgress.classList.add('hidden');
  stepResult.classList.remove('hidden');
  stepResult.scrollIntoView({ behavior: 'smooth' });
}

function handleTaskFailure(task) {
  generateVideoBtn.disabled = false;
  generateVideoBtn.innerHTML = '<span class="btn-icon">🚀</span> Render Complete 1080x1920 Viral Short Video';
  resumeTaskBtn.classList.remove('hidden');
  alert('Video Generation Stopped: ' + (task.error || 'Unknown error occurred') + '\n\nClick "🔁 Resume Generation" in the terminal header to continue from checkpoint!');
}
