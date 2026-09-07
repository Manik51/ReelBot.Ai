/* ==========================================================================
   DOCUMENTARY & BUSINESS ANALYSIS STUDIO — CLIENT CONTROLLER
   100% Independent Module: Manages #documentary-studio-workspace
   ========================================================================== */

(function() {
  'use strict';

  const docuState = {
    currentScript: null,
    currentTaskId: null,
    pollInterval: null,
    selectedCategory: 'indian_true_crime',
    selectedDuration: 60,
    presetsData: null,
    lastLogCount: 0
  };

  document.addEventListener('DOMContentLoaded', initDocuStudio);

  async function initDocuStudio() {
    setupThreeWaySwitcher();
    await fetchPresets();
    attachCategoryListeners();
    attachDurationListeners();
    attachStoryboardListeners();
    attachRenderListeners();
    attachYouTubeListeners();
  }

  // ── 1. THREE-WAY MODE SWITCHER ───────────────────────────────────────────
  function setupThreeWaySwitcher() {
    const headerActions = document.querySelector('.header-actions');
    if (!headerActions) return;

    // Replace switcher container with 3 buttons
    let switcher = document.querySelector('.mode-switcher-container');
    if (!switcher) {
      switcher = document.createElement('div');
      switcher.className = 'mode-switcher-container';
      headerActions.insertBefore(switcher, headerActions.firstChild);
    }

    switcher.innerHTML = `
      <button type="button" id="mode-cinema-btn" class="mode-tab-btn mode-cinema" title="Realistic Stock Footage Engine">
        <span>🎥</span> Cinema Studio
      </button>
      <button type="button" id="mode-motion-btn" class="mode-tab-btn mode-motion" title="Viral Looping GIF Engine">
        <span>⚡</span> Motion Studio
      </button>
      <button type="button" id="mode-docu-btn" class="mode-tab-btn mode-docu active" title="Indian True Crime & Documentary Engine">
        <span>🚨</span> True Crime Studio
      </button>
    `;

    document.getElementById('mode-cinema-btn').addEventListener('click', () => switchWorkspace('cinema'));
    document.getElementById('mode-motion-btn').addEventListener('click', () => switchWorkspace('motion'));
    document.getElementById('mode-docu-btn').addEventListener('click', () => switchWorkspace('docu'));

    // Default to documentary if opened or cinema if user clicked
    switchWorkspace('docu');
  }

  window.switchWorkspace = function(mode) {
    const wsCinema = document.getElementById('cinema-studio-workspace');
    const wsMotion = document.getElementById('motion-studio-workspace');
    const wsDocu = document.getElementById('documentary-studio-workspace');

    const btnCinema = document.getElementById('mode-cinema-btn');
    const btnMotion = document.getElementById('mode-motion-btn');
    const btnDocu = document.getElementById('mode-docu-btn');

    if (wsCinema) wsCinema.classList.toggle('hidden', mode !== 'cinema');
    if (wsMotion) wsMotion.classList.toggle('hidden', mode !== 'motion');
    if (wsDocu) wsDocu.classList.toggle('hidden', mode !== 'docu');

    if (btnCinema) btnCinema.classList.toggle('active', mode === 'cinema');
    if (btnMotion) btnMotion.classList.toggle('active', mode === 'motion');
    if (btnDocu) btnDocu.classList.toggle('active', mode === 'docu');

    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // ── 2. FETCH PRESETS & INITIALIZE DROPDOWNS ──────────────────────────────
  async function fetchPresets() {
    try {
      const res = await fetch('/api/documentary/presets');
      if (!res.ok) throw new Error("Could not fetch documentary presets");
      docuState.presetsData = await res.json();
      populateDropdowns();
      renderTopicChips(docuState.selectedCategory);
    } catch (err) {
      console.warn("[DocuStudio] Preset loading warning:", err);
    }
  }

  function populateDropdowns() {
    const data = docuState.presetsData;
    if (!data) return;

    // Categories
    const catSelect = document.getElementById('docu-category-select');
    if (catSelect && data.categories) {
      catSelect.innerHTML = Object.entries(data.categories).map(([k, cat]) =>
        `<option value="${k}" ${k === docuState.selectedCategory ? 'selected' : ''}>${cat.name}</option>`
      ).join('');
    }

    // Themes
    const themeSelect = document.getElementById('docu-theme-select');
    if (themeSelect && data.themes) {
      themeSelect.innerHTML = data.themes.map(t =>
        `<option value="${t.id}" ${t.id === 'crime_noir' ? 'selected' : ''}>${t.name}</option>`
      ).join('');
    }

    // Voices
    const voiceSelect = document.getElementById('docu-voice-select');
    if (voiceSelect && data.voices) {
      voiceSelect.innerHTML = data.voices.map(v => 
        `<option value="${v.id}" ${v.id.includes('am_adam') ? 'selected' : ''}>${v.name}</option>`
      ).join('');
    }

    // Subtitle Colors
    const subColorSelect = document.getElementById('docu-sub-color-select');
    if (subColorSelect && data.subtitle_colors) {
      subColorSelect.innerHTML = data.subtitle_colors.map(c => 
        `<option value="${c.id}">${c.name}</option>`
      ).join('');
    }

    // Fonts
    const fontSelect = document.getElementById('docu-font-select');
    if (fontSelect && data.fonts) {
      fontSelect.innerHTML = data.fonts.map(f => 
        `<option value="${f.id}">${f.name}</option>`
      ).join('');
    }

    // BGM
    const bgmSelect = document.getElementById('docu-bgm-select');
    if (bgmSelect && data.bgm_options) {
      bgmSelect.innerHTML = data.bgm_options.map(b => 
        `<option value="${b.id}">${b.name}</option>`
      ).join('');
    }
  }

  // ── 3. CATEGORY & DURATION SELECTION ─────────────────────────────────────
  function attachCategoryListeners() {
    const catSelect = document.getElementById('docu-category-select');
    if (catSelect) {
      catSelect.addEventListener('change', (e) => {
        docuState.selectedCategory = e.target.value;
        renderTopicChips(docuState.selectedCategory);
      });
    }
  }

  function renderTopicChips(catKey) {
    const grid = document.getElementById('docu-topics-grid');
    if (!grid || !docuState.presetsData) return;

    const catData = docuState.presetsData.categories[catKey];
    if (!catData || !catData.topics) {
      grid.innerHTML = '<p style="color:#94a3b8; font-size:12px;">Select or type any custom topic below.</p>';
      return;
    }

    grid.innerHTML = catData.topics.map((t, idx) => `
      <button type="button" class="docu-topic-chip ${idx === 0 ? 'active' : ''}" data-topic="${t.title}">
        <strong>${t.title}</strong>
        <small>"${t.hook}"</small>
      </button>
    `).join('');

    grid.querySelectorAll('.docu-topic-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        grid.querySelectorAll('.docu-topic-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        const topicInput = document.getElementById('docu-topic-input');
        if (topicInput) topicInput.value = chip.dataset.topic;
      });
    });

    // Set first topic by default
    if (catData.topics[0]) {
      const topicInput = document.getElementById('docu-topic-input');
      if (topicInput && !topicInput.value) topicInput.value = catData.topics[0].title;
    }
  }

  function attachDurationListeners() {
    document.querySelectorAll('.docu-duration-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('.docu-duration-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        docuState.selectedDuration = parseInt(pill.dataset.duration, 10);
      });
    });

    // Volume sliders
    const sfxVol = document.getElementById('docu-sfx-vol');
    const sfxVal = document.getElementById('docu-sfx-val');
    if (sfxVol && sfxVal) {
      sfxVol.addEventListener('input', (e) => {
        sfxVal.textContent = `${e.target.value}%`;
      });
    }

    const bgmVol = document.getElementById('docu-bgm-vol');
    const bgmVal = document.getElementById('docu-bgm-val');
    if (bgmVol && bgmVal) {
      bgmVol.addEventListener('input', (e) => {
        bgmVal.textContent = `${e.target.value}%`;
      });
    }
  }

  // ── 4. STORYBOARD GENERATION & CUSTOMIZER ────────────────────────────────
  function attachStoryboardListeners() {
    const btnGen = document.getElementById('docu-gen-storyboard-btn');
    if (btnGen) {
      btnGen.addEventListener('click', handleGenerateStoryboard);
    }
  }

  async function handleGenerateStoryboard() {
    const topicInput = document.getElementById('docu-topic-input');
    const topic = topicInput ? topicInput.value.trim() : '';
    if (!topic) {
      alert('Please enter a documentary topic or select a preset headline.');
      return;
    }

    const btnGen = document.getElementById('docu-gen-storyboard-btn');
    btnGen.disabled = true;
    btnGen.innerHTML = '<span>⏳</span> Generating Storyboard Beats...';

    const lang = document.getElementById('docu-lang-select')?.value || 'English';
    const theme = document.getElementById('docu-theme-select')?.value || 'dark_slate';
    
    // Checked metaphors
    const metaphors = [];
    document.querySelectorAll('.docu-meta-chk:checked').forEach(cb => metaphors.push(cb.value));

    try {
      const res = await fetch('/api/documentary/generate-storyboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic,
          duration_sec: docuState.selectedDuration,
          language: lang,
          visual_theme: theme,
          allowed_metaphors: metaphors.length ? metaphors : null
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Storyboard generation failed');
      }

      docuState.currentScript = await res.json();
      renderStoryboardBeats(docuState.currentScript);
      
      // Reveal render section
      document.getElementById('docu-storyboard-section')?.classList.remove('hidden');
      document.getElementById('docu-render-action-card')?.classList.remove('hidden');
      document.getElementById('docu-storyboard-section')?.scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      btnGen.disabled = false;
      btnGen.innerHTML = '<span>🎛️</span> Generate & Customize Storyboard Beats';
    }
  }

  function renderStoryboardBeats(scriptData) {
    const container = document.getElementById('docu-beat-list');
    const titleEl = document.getElementById('docu-storyboard-title');
    if (titleEl) titleEl.textContent = scriptData.title || 'Documentary Storyboard';
    if (!container) return;

    const beats = scriptData.beats || [];
    container.innerHTML = beats.map((b, i) => `
      <div class="docu-beat-item" data-beat-idx="${i}">
        <div class="docu-beat-header">
          <span class="docu-beat-num">Beat #${b.beat_index}</span>
          <div class="docu-beat-selects">
            <label style="font-size:11px; color:#94a3b8;">Metaphor:</label>
            <select class="docu-beat-select beat-metaphor-select">
              <option value="archival_photo_pan" ${b.metaphor === 'archival_photo_pan' ? 'selected' : ''}>📸 Archival Photo Ken Burns</option>
              <option value="newspaper_slam" ${b.metaphor === 'newspaper_slam' ? 'selected' : ''}>📰 Newspaper Slam</option>
              <option value="parallax_cutout" ${b.metaphor === 'parallax_cutout' ? 'selected' : ''}>🖼️ 2.5D Grounded Cutout</option>
              <option value="split_comparison" ${b.metaphor === 'split_comparison' ? 'selected' : ''}>⚖️ Rivalry Split (VS)</option>
              <option value="financial_stat" ${b.metaphor === 'financial_stat' ? 'selected' : ''}>💰 Financial Stat</option>
              <option value="action_gif" ${b.metaphor === 'action_gif' ? 'selected' : ''}>⚡ Action GIF / Loop</option>
            </select>

            <label style="font-size:11px; color:#94a3b8; margin-left:6px;">SFX:</label>
            <select class="docu-beat-select beat-sfx-select">
              <option value="camera_shutter" ${b.sfx_cue === 'camera_shutter' ? 'selected' : ''}>📸 Camera Shutter</option>
              <option value="paper_slam" ${b.sfx_cue === 'paper_slam' ? 'selected' : ''}>💥 Paper Slam</option>
              <option value="cash_kaching" ${b.sfx_cue === 'cash_kaching' ? 'selected' : ''}>💰 Cash Kaching</option>
              <option value="whoosh" ${b.sfx_cue === 'whoosh' ? 'selected' : ''}>⚡ Whoosh</option>
              <option value="bass_drop" ${b.sfx_cue === 'bass_drop' ? 'selected' : ''}>🥁 Bass Drop</option>
            </select>
          </div>
        </div>

        <textarea class="docu-beat-narration" rows="2" placeholder="Narration for this beat...">${b.narration || ''}</textarea>
        
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:11px; margin-top:8px;">
          <div>
            <label style="color:#94a3b8; font-size:10px; text-transform:uppercase;">🖼️ Cutout Subject Photo:</label>
            <input type="text" class="docu-input beat-visual-input" style="padding:6px 10px; width:100%; margin-top:3px;" value="${b.visual_subject || b.primary_subject || ''}" placeholder="e.g. Steve Jobs 1997 portrait...">
          </div>
          <div>
            <label style="color:#94a3b8; font-size:10px; text-transform:uppercase;">🎥 Context-Locked B-Roll:</label>
            <input type="text" class="docu-input beat-broll-input" style="padding:6px 10px; width:100%; margin-top:3px;" value="${b.contextual_broll_query || b.broll_keywords || ''}" placeholder="e.g. newspaper printing press / Apple campus...">
          </div>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; font-size:11px; margin-top:8px;">
          <div>
            <label style="color:#94a3b8; font-size:10px; text-transform:uppercase;">📍 Chapter/Location Stamp:</label>
            <input type="text" class="docu-input beat-stamp-input" style="padding:6px 10px; width:100%; margin-top:3px;" value="${b.chapter_stamp || ''}" placeholder="[ 1997 · CUPERTINO, CA ]">
          </div>
          <div>
            <label style="color:#94a3b8; font-size:10px; text-transform:uppercase;">📰 Headline / Stat:</label>
            <input type="text" class="docu-input beat-headline-input" style="padding:6px 10px; width:100%; margin-top:3px;" value="${b.headline_text || ''}" placeholder="Headline text...">
          </div>
          <div>
            <label style="color:#94a3b8; font-size:10px; text-transform:uppercase;">👤 Role Title / Entity:</label>
            <input type="text" class="docu-input beat-role-input" style="padding:6px 10px; width:100%; margin-top:3px;" value="${b.subject_role_title || b.primary_subject || ''}" placeholder="e.g. STEVE JOBS · INTERIM CEO">
          </div>
        </div>
      </div>
    `).join('');
  }

  function collectEditedStoryboard() {
    if (!docuState.currentScript) return null;
    const beatItems = document.querySelectorAll('.docu-beat-item');
    const updatedBeats = [];

    beatItems.forEach((item, idx) => {
      const orig = docuState.currentScript.beats[idx] || {};
      const narration = item.querySelector('.docu-beat-narration')?.value || orig.narration || '';
      const metaphor = item.querySelector('.beat-metaphor-select')?.value || orig.metaphor || 'parallax_cutout';
      const sfx = item.querySelector('.beat-sfx-select')?.value || orig.sfx_cue || 'whoosh';
      const visualSubj = item.querySelector('.beat-visual-input')?.value || orig.visual_subject || orig.primary_subject || '';
      const broll = item.querySelector('.beat-broll-input')?.value || orig.contextual_broll_query || orig.broll_keywords || '';
      const stamp = item.querySelector('.beat-stamp-input')?.value || orig.chapter_stamp || '';
      const headline = item.querySelector('.beat-headline-input')?.value || orig.headline_text || '';
      const role = item.querySelector('.beat-role-input')?.value || orig.subject_role_title || orig.primary_subject || '';

      updatedBeats.push({
        ...orig,
        beat_index: idx + 1,
        narration: narration,
        metaphor: metaphor,
        sfx_cue: sfx,
        visual_subject: visualSubj,
        contextual_broll_query: broll,
        broll_keywords: broll,
        chapter_stamp: stamp,
        headline_text: headline,
        subject_role_title: role,
        primary_subject: role.split('·')[0].trim() || orig.primary_subject || ''
      });
    });

    return {
      ...docuState.currentScript,
      beats: updatedBeats
    };
  }

  // ── 5. RENDER PIPELINE & PROGRESS STREAMING ──────────────────────────────
  function attachRenderListeners() {
    const btnRender = document.getElementById('docu-start-render-btn');
    if (btnRender) {
      btnRender.addEventListener('click', handleStartRender);
    }
  }

  async function handleStartRender() {
    const finalStoryboard = collectEditedStoryboard();
    if (!finalStoryboard || !finalStoryboard.beats || !finalStoryboard.beats.length) {
      alert('No storyboard found. Please generate storyboard beats first.');
      return;
    }

    const payload = {
      storyboard: finalStoryboard,
      voice_id: document.getElementById('docu-voice-select')?.value || 'kokoro:am_adam',
      voice_speed: document.getElementById('docu-speed-select')?.value || '+0%',
      subtitle_color: document.getElementById('docu-sub-color-select')?.value || 'yellow',
      font_name: document.getElementById('docu-font-select')?.value || 'Space Grotesk',
      visual_theme: document.getElementById('docu-theme-select')?.value || 'dark_slate',
      bgm_id: document.getElementById('docu-bgm-select')?.value || 'dark_investigative',
      bgm_volume: (parseInt(document.getElementById('docu-bgm-vol')?.value || 15, 10)) / 100.0,
      sfx_volume: (parseInt(document.getElementById('docu-sfx-vol')?.value || 60, 10)) / 100.0,
      sfx_enabled: document.getElementById('docu-sfx-toggle')?.checked ?? true
    };

    // Switch to progress view
    document.getElementById('docu-progress-card')?.classList.remove('hidden');
    document.getElementById('docu-result-card')?.classList.add('hidden');
    document.getElementById('docu-progress-card')?.scrollIntoView({ behavior: 'smooth' });

    try {
      const res = await fetch('/api/documentary/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to start documentary render.');
      }

      const data = await res.json();
      docuState.currentTaskId = data.task_id;
      docuState.lastLogCount = 0;
      startPollingTask(data.task_id);

    } catch (err) {
      alert(`Render error: ${err.message}`);
    }
  }

  function startPollingTask(taskId) {
    if (docuState.pollInterval) clearInterval(docuState.pollInterval);

    docuState.pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/documentary/task/${taskId}`);
        if (!res.ok) return;

        const task = await res.json();
        updateProgressUI(task);

        if (task.status === 'completed') {
          clearInterval(docuState.pollInterval);
          showCompletionUI(task);
        } else if (task.status === 'failed') {
          clearInterval(docuState.pollInterval);
          alert(`Documentary render failed:\n${task.error || 'Unknown error'}`);
        }
      } catch (err) {
        console.error("[DocuStudio] Poll error:", err);
      }
    }, 1000);
  }

  function updateProgressUI(task) {
    const pFill = document.getElementById('docu-progress-fill');
    const pVal = document.getElementById('docu-progress-percent');
    const pStage = document.getElementById('docu-progress-stage');
    const term = document.getElementById('docu-terminal-logs');

    if (pFill) pFill.style.width = `${task.progress || 0}%`;
    if (pVal) pVal.textContent = `${task.progress || 0}%`;
    if (pStage) pStage.textContent = task.stage || 'Rendering...';

    if (term && task.logs && task.logs.length > docuState.lastLogCount) {
      for (let i = docuState.lastLogCount; i < task.logs.length; i++) {
        const line = document.createElement('div');
        line.textContent = task.logs[i];
        term.appendChild(line);
      }
      docuState.lastLogCount = task.logs.length;
      term.scrollTop = term.scrollHeight;
    }
  }

  function showCompletionUI(task) {
    const resCard = document.getElementById('docu-result-card');
    const videoPlayer = document.getElementById('docu-video-player');
    const downloadBtn = document.getElementById('docu-download-btn');

    if (resCard) resCard.classList.remove('hidden');
    let vUrl = task.video_url;
    if (vUrl && vUrl.startsWith('/api/video/')) {
      vUrl = vUrl.replace('/api/video/', '/output/');
    }
    if (videoPlayer && vUrl) {
      videoPlayer.src = vUrl;
      videoPlayer.load();
    }
    if (downloadBtn && vUrl) {
      downloadBtn.href = vUrl;
      downloadBtn.download = `Documentary_Short_${Date.now()}.mp4`;
    }

    // Pre-fill YouTube fields
    const seoTitle = document.getElementById('docu-yt-title');
    const seoDesc = document.getElementById('docu-yt-desc');
    if (seoTitle) seoTitle.value = task.seo?.title || 'Documentary Short #shorts';
    if (seoDesc) seoDesc.value = task.seo?.description || 'Created with #reelbot.ai';

    resCard?.scrollIntoView({ behavior: 'smooth' });
  }

  // ── 6. DIRECT YOUTUBE UPLOAD ─────────────────────────────────────────────
  function attachYouTubeListeners() {
    const btnUpload = document.getElementById('docu-yt-upload-btn');
    if (btnUpload) {
      btnUpload.addEventListener('click', handleYouTubeUpload);
    }
  }

  async function handleYouTubeUpload() {
    if (!docuState.currentTaskId) {
      alert('No active task to upload.');
      return;
    }

    const btnUpload = document.getElementById('docu-yt-upload-btn');
    const feedback = document.getElementById('docu-yt-feedback');
    btnUpload.disabled = true;
    btnUpload.innerHTML = '<span>⏳</span> Uploading to YouTube...';
    if (feedback) feedback.textContent = '';

    try {
      const res = await fetch('/api/documentary/upload-youtube', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: docuState.currentTaskId,
          title: document.getElementById('docu-yt-title')?.value,
          description: document.getElementById('docu-yt-desc')?.value
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'YouTube upload failed');

      if (feedback) {
        feedback.innerHTML = `<span style="color:#10b981;">✅ Uploaded! <a href="${data.video_url}" target="_blank" style="color:#fbbf24;">Watch on YouTube ↗</a></span>`;
      }
    } catch (err) {
      if (feedback) feedback.innerHTML = `<span style="color:#ef4444;">❌ Error: ${err.message}</span>`;
    } finally {
      btnUpload.disabled = false;
      btnUpload.innerHTML = '<span>▶️</span> Auto-Upload to YouTube Shorts';
    }
  }

})();
