/* ==========================================================================
   ReelBot Motion Studio — Dedicated Modern Workspace Controller
   100% Independent: Manages #motion-studio-workspace without touching Cinema
   ========================================================================== */

(function() {
  'use strict';

  const motionState = {
    currentMode: 'cinema', // 'cinema' or 'motion'
    currentScript: null,
    currentTaskId: null,
    pollInterval: null,
    lastLogIndex: 0
  };

  document.addEventListener('DOMContentLoaded', initMotionStudio);

  function initMotionStudio() {
    renderModeSwitcher();
    attachTopicFinderListeners();
    attachScriptGenerateListener();
    attachRenderListeners();
    attachYouTubeUploadListener();
    loadVoicesForMotion();

    const langSelect = document.getElementById('motion-language-select');
    if (langSelect) {
      langSelect.addEventListener('change', () => loadVoicesForMotion());
    }
  }

  // 1. Mode Switcher
  function renderModeSwitcher() {
    // If static 3-way switcher already exists with documentary studio, do not overwrite
    if (document.getElementById('mode-docu-btn')) {
      const btnCinema = document.getElementById('mode-cinema-btn');
      const btnMotion = document.getElementById('mode-motion-btn');
      if (btnCinema) btnCinema.addEventListener('click', () => switchStudioWorkspace('cinema'));
      if (btnMotion) btnMotion.addEventListener('click', () => switchStudioWorkspace('motion'));
      return;
    }

    const headerActions = document.querySelector('.header-actions');
    if (!headerActions) return;

    // Remove any existing switcher
    const existing = document.querySelector('.mode-switcher-container');
    if (existing) existing.remove();

    const switcherContainer = document.createElement('div');
    switcherContainer.className = 'mode-switcher-container';
    switcherContainer.innerHTML = `
      <button type="button" id="mode-cinema-btn" class="mode-tab-btn mode-cinema active" title="Switch to Realistic Stock Footage Engine">
        <span>🎥</span> Cinema Studio
      </button>
      <button type="button" id="mode-motion-btn" class="mode-tab-btn mode-motion" title="Switch to Animated GIF & Meme Short Maker">
        <span>⚡</span> Motion Studio
      </button>
    `;

    headerActions.insertBefore(switcherContainer, headerActions.firstChild);

    const btnCinema = document.getElementById('mode-cinema-btn');
    const btnMotion = document.getElementById('mode-motion-btn');

    btnCinema.addEventListener('click', () => switchStudioWorkspace('cinema'));
    btnMotion.addEventListener('click', () => switchStudioWorkspace('motion'));
  }

  function switchStudioWorkspace(mode) {
    if (typeof window.switchWorkspace === 'function') {
      return window.switchWorkspace(mode);
    }
    motionState.currentMode = mode;
    const cinemaWorkspace = document.getElementById('cinema-studio-workspace');
    const motionWorkspace = document.getElementById('motion-studio-workspace');
    const btnCinema = document.getElementById('mode-cinema-btn');
    const btnMotion = document.getElementById('mode-motion-btn');

    if (mode === 'motion') {
      if (btnCinema) btnCinema.classList.remove('active');
      if (btnMotion) btnMotion.classList.add('active');

      if (cinemaWorkspace) cinemaWorkspace.classList.add('hidden');
      if (motionWorkspace) motionWorkspace.classList.remove('hidden');

      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      if (btnMotion) btnMotion.classList.remove('active');
      if (btnCinema) btnCinema.classList.add('active');

      if (motionWorkspace) motionWorkspace.classList.add('hidden');
      if (cinemaWorkspace) cinemaWorkspace.classList.remove('hidden');

      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  // 2. Load and Populate Voices from existing ReelBot config (Kokoro + Piper only)
  async function loadVoicesForMotion() {
    const voiceSelect = document.getElementById('motion-voice-select');
    const langSelect = document.getElementById('motion-language-select');
    if (!voiceSelect) return;

    try {
      const res = await fetch('/api/config');
      if (!res.ok) return;
      const cfg = await res.json();
      const voices = cfg.voices || [];

      if (voices.length > 0) {
        voiceSelect.innerHTML = '';
        const currentLang = langSelect ? langSelect.value : 'Bengali';

        voices.forEach(v => {
          const opt = document.createElement('option');
          opt.value = v.id;
          opt.textContent = v.name;

          if (currentLang === 'Bengali' && v.id === 'piper:bn_BD-google-medium') {
            opt.selected = true;
          } else if (currentLang === 'Hindi' && v.id === 'piper:hi_IN-pratham-medium') {
            opt.selected = true;
          } else if (currentLang === 'English' && v.id === 'kokoro:am_adam') {
            opt.selected = true;
          }

          voiceSelect.appendChild(opt);
        });
      }
    } catch (e) {
      console.error('Error loading voices for Motion Studio:', e);
    }
  }

  // 3. Category Selection & Dynamic 6-Topic Finder
  function attachTopicFinderListeners() {
    const findBtn = document.getElementById('motion-find-topics-btn');
    const catSelect = document.getElementById('motion-category-select');
    const resultsGrid = document.getElementById('motion-topic-results-grid');
    const topicInput = document.getElementById('motion-topic-input');

    if (!findBtn || !catSelect || !resultsGrid) return;

    findBtn.addEventListener('click', async () => {
      const cat = catSelect.value || 'all';
      findBtn.disabled = true;
      findBtn.innerHTML = '<span>⏳</span> Finding 6 Viral Topics...';

      try {
        const res = await fetch(`/api/motion/find-trends?category=${cat}`);
        if (!res.ok) throw new Error('Failed to find topics');
        const data = await res.json();
        const trends = data.trends || [];

        if (trends.length > 0) {
          resultsGrid.innerHTML = '';
          trends.slice(0, 6).forEach((item, idx) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `motion-idea-chip ${idx === 0 ? 'active' : ''}`;
            btn.dataset.topic = item.title;

            btn.innerHTML = `
              <span class="chip-emoji">${item.emoji || '🔥'}</span>
              <div class="chip-text">
                <strong>${item.title}</strong>
                <small>${item.hook_desc || item.hook || 'High retention viral hook'}</small>
              </div>
              <span class="chip-views">${item.views_potential || '24.5M Views'}</span>
            `;

            btn.addEventListener('click', () => {
              resultsGrid.querySelectorAll('.motion-idea-chip').forEach(c => c.classList.remove('active'));
              btn.classList.add('active');
              if (topicInput) topicInput.value = item.title;
            });

            resultsGrid.appendChild(btn);
          });

          // Set the first topic as active
          if (topicInput && trends[0]) {
            topicInput.value = trends[0].title;
          }
        }
      } catch (e) {
        console.error('Find topics error:', e);
        alert('Could not find topics: ' + e.message);
      } finally {
        findBtn.disabled = false;
        findBtn.innerHTML = '<span>🔍</span> Find 6 Viral Topics';
      }
    });

    // Default static chips click handlers
    resultsGrid.querySelectorAll('.motion-idea-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        resultsGrid.querySelectorAll('.motion-idea-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        if (topicInput) topicInput.value = chip.dataset.topic;
      });
    });
  }

  // 4. Generate Script & Storyboard
  function attachScriptGenerateListener() {
    const genBtn = document.getElementById('motion-generate-script-btn');
    const topicInput = document.getElementById('motion-topic-input');
    const durationSelect = document.getElementById('motion-duration-select');
    const langSelect = document.getElementById('motion-language-select');

    if (!genBtn || !topicInput) return;

    genBtn.addEventListener('click', async () => {
      const topic = topicInput.value.trim();
      if (!topic) {
        alert('Please enter or select a topic first.');
        return;
      }

      genBtn.disabled = true;
      genBtn.innerHTML = '<span>⏳</span> Writing Comedy Storyboard (Gemini AI)...';

      try {
        const res = await fetch('/api/motion/generate-script', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: topic,
            language: langSelect.value,
            tone: 'Funny / Entertainment',
            target_duration_sec: parseInt(durationSelect.value, 10)
          })
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Script generation failed');
        }

        const script = await res.json();
        motionState.currentScript = script;
        renderMotionStoryboard(script);

      } catch (e) {
        alert('Script Generation Error: ' + e.message);
      } finally {
        genBtn.disabled = false;
        genBtn.innerHTML = '<span>✨</span> Generate Motion Storyboard & Preview';
      }
    });
  }

  function renderMotionStoryboard(script) {
    const storyboardSection = document.getElementById('motion-storyboard-section');
    const scenesGrid = document.getElementById('motion-scenes-grid');
    const titleEl = document.getElementById('motion-script-title');
    const metaEl = document.getElementById('motion-script-meta');

    if (!storyboardSection || !scenesGrid) return;

    if (titleEl) titleEl.textContent = script.title || 'Motion Short Storyboard';
    if (metaEl) {
      metaEl.textContent = `${script.scenes.length} Scenes · ~${script.estimated_total_duration || 30}s · Romanized Hormozi Captions · Animated Loops`;
    }

    scenesGrid.innerHTML = '';

    script.scenes.forEach(sc => {
      const tile = document.createElement('div');
      tile.className = 'motion-scene-tile';

      const romanSub = (sc.subtitle_text || sc.narration || '').toUpperCase();
      const vTag = sc.visual_tag || (sc.keywords && sc.keywords[0]) || 'funny cartoon animation';

      tile.innerHTML = `
        <div class="scene-tile-top">
          <span class="scene-tile-badge">${sc.suggested_emoji || '🎬'} Scene ${sc.scene_id}</span>
          <span class="scene-tile-dur">⏱️ ${sc.time_range || '0:00 - 0:03'}</span>
        </div>

        <div class="scene-tile-field">
          <label>🎙️ Spoken Narration (Conversational):</label>
          <textarea class="scene-tile-input motion-tile-narration" rows="2">${sc.narration}</textarea>
        </div>

        <div class="scene-tile-field">
          <label>🔤 Subtitle (Romanized Banglish / English):</label>
          <input type="text" class="scene-tile-input sub motion-tile-subtitle" value="${romanSub}">
        </div>

        <div class="scene-tile-field">
          <label>👾 Story Action Visual Tag (Search Prompt):</label>
          <input type="text" class="scene-tile-input vtag motion-tile-vtag" value="${vTag}">
        </div>
      `;

      scenesGrid.appendChild(tile);
    });

    storyboardSection.classList.remove('hidden');
    storyboardSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // 5. Render Motion Video
  function attachRenderListeners() {
    const btnTop = document.getElementById('motion-render-btn');
    const btnBottom = document.getElementById('motion-render-btn-bottom');

    const handleRender = () => launchMotionVideoRender();

    if (btnTop) btnTop.addEventListener('click', handleRender);
    if (btnBottom) btnBottom.addEventListener('click', handleRender);
  }

  async function launchMotionVideoRender() {
    if (!motionState.currentScript) return;

    const narrationInputs = document.querySelectorAll('.motion-tile-narration');
    const subInputs = document.querySelectorAll('.motion-tile-subtitle');
    const vtagInputs = document.querySelectorAll('.motion-tile-vtag');

    const updatedScenes = motionState.currentScript.scenes.map((sc, idx) => {
      const narr = narrationInputs[idx] ? narrationInputs[idx].value.trim() : sc.narration;
      const sub = subInputs[idx] ? subInputs[idx].value.trim().toUpperCase() : sc.subtitle_text;
      const vtag = vtagInputs[idx] ? vtagInputs[idx].value.trim() : sc.visual_tag;

      return {
        scene_id: sc.scene_id,
        time_range: sc.time_range || `0:${(idx*3).toString().padStart(2, '0')}-0:${((idx+1)*3).toString().padStart(2, '0')}`,
        visual_tag: vtag,
        narration: narr,
        subtitle_text: sub,
        keywords: vtag ? [vtag, ...(sc.keywords || [])] : (sc.keywords || []),
        suggested_emoji: sc.suggested_emoji || '👾',
        estimated_seconds: sc.estimated_seconds || 3.0
      };
    });

    const voiceSelect = document.getElementById('motion-voice-select');
    const subtitleStyleSelect = document.getElementById('motion-subtitle-style-select');
    const vibeSelect = document.getElementById('motion-vibe-select');
    const sfxSelect = document.getElementById('motion-sfx-select');

    const payload = {
      title: motionState.currentScript.title || 'Viral Motion Short',
      scenes: updatedScenes,
      voice_id: voiceSelect ? voiceSelect.value : 'piper:bn_BD-google-medium',
      voice_rate: '+10%',
      subtitle_style_id: subtitleStyleSelect ? subtitleStyleSelect.value : 'hormozi_yellow',
      style_preset: vibeSelect ? vibeSelect.value : 'meme',
      sfx_intensity: sfxSelect ? sfxSelect.value : 'cinematic',
      bgm_track_id: 'default',
      bgm_volume: 0.15
    };

    const progressSection = document.getElementById('motion-progress-section');
    const storyboardSection = document.getElementById('motion-storyboard-section');
    const resultSection = document.getElementById('motion-result-section');

    try {
      const res = await fetch('/api/motion/generate-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to launch motion video task');
      }

      const data = await res.json();
      motionState.currentTaskId = data.task_id;

      if (storyboardSection) storyboardSection.classList.add('hidden');
      if (resultSection) resultSection.classList.add('hidden');
      if (progressSection) {
        progressSection.classList.remove('hidden');
        progressSection.scrollIntoView({ behavior: 'smooth' });
      }

      startMotionPolling(data.task_id);

    } catch (e) {
      alert('Motion Render Error: ' + e.message);
    }
  }

  // 6. Polling Progress
  function startMotionPolling(taskId) {
    if (motionState.pollInterval) clearInterval(motionState.pollInterval);
    motionState.lastLogIndex = 0;

    const barEl = document.getElementById('motion-progress-bar');
    const pctEl = document.getElementById('motion-progress-pct');
    const stageEl = document.getElementById('motion-progress-stage');
    const logBox = document.getElementById('motion-log-box');

    motionState.pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/task-status/${taskId}`);
        if (!res.ok) return;
        const task = await res.json();

        const p = task.progress || 0;
        if (barEl) barEl.style.width = `${p}%`;
        if (pctEl) pctEl.textContent = `${p}%`;
        if (stageEl) stageEl.textContent = task.stage || 'Processing...';

        if (task.logs && task.logs.length > motionState.lastLogIndex && logBox) {
          for (let i = motionState.lastLogIndex; i < task.logs.length; i++) {
            const line = document.createElement('div');
            line.textContent = task.logs[i];
            logBox.appendChild(line);
          }
          motionState.lastLogIndex = task.logs.length;
          logBox.scrollTop = logBox.scrollHeight;
        }

        if (task.status === 'completed') {
          clearInterval(motionState.pollInterval);
          handleMotionSuccess(task);
        } else if (task.status === 'failed') {
          clearInterval(motionState.pollInterval);
          alert('Motion synthesis failed: ' + (task.error || 'Unknown error'));
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    }, 1200);
  }

  function handleMotionSuccess(task) {
    const progressSection = document.getElementById('motion-progress-section');
    const resultSection = document.getElementById('motion-result-section');
    const videoPlayer = document.getElementById('motion-video-player');
    const downloadBtn = document.getElementById('motion-download-btn');
    const createAnotherBtn = document.getElementById('motion-create-another-btn');
    const seoTitle = document.getElementById('motion-seo-title');
    const seoDesc = document.getElementById('motion-seo-desc');

    if (progressSection) progressSection.classList.add('hidden');
    if (resultSection) {
      resultSection.classList.remove('hidden');
      resultSection.scrollIntoView({ behavior: 'smooth' });
    }

    if (videoPlayer && task.video_url) {
      videoPlayer.src = task.video_url;
      videoPlayer.load();
      videoPlayer.play().catch(() => {});
    }

    if (downloadBtn && task.video_url) {
      downloadBtn.href = task.video_url;
      downloadBtn.download = task.filename || 'motion_short.mp4';
    }

    if (seoTitle && motionState.currentScript) {
      const t = (motionState.currentScript.seo && motionState.currentScript.seo.youtube_title) || `${motionState.currentScript.title} 😂 #shorts`;
      seoTitle.value = t;
    }

    if (seoDesc && motionState.currentScript) {
      const d = (motionState.currentScript.seo && motionState.currentScript.seo.youtube_description) || `${motionState.currentScript.title} #shorts #funny #reelbot.ai`;
      seoDesc.value = d;
    }

    if (createAnotherBtn) {
      createAnotherBtn.onclick = () => {
        if (resultSection) resultSection.classList.add('hidden');
        const cockpit = document.querySelector('.motion-cockpit');
        if (cockpit) cockpit.scrollIntoView({ behavior: 'smooth' });
      };
    }
  }

  // 7. 1-Click YouTube Upload
  function attachYouTubeUploadListener() {
    const uploadBtn = document.getElementById('motion-yt-upload-btn');
    const feedbackEl = document.getElementById('motion-yt-feedback');

    if (!uploadBtn) return;

    uploadBtn.addEventListener('click', async () => {
      if (!motionState.currentTaskId) {
        alert('No finished video to upload!');
        return;
      }

      uploadBtn.disabled = true;
      uploadBtn.innerHTML = '<span>⏳</span> Uploading to YouTube...';
      if (feedbackEl) feedbackEl.textContent = 'Contacting YouTube API...';

      try {
        const res = await fetch('/api/youtube/upload-video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task_id: motionState.currentTaskId,
            privacy_status: 'public'
          })
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'YouTube upload failed');
        }

        const data = await res.json();
        if (feedbackEl) {
          feedbackEl.innerHTML = `
            <span style="color: #10b981;">✅ Uploaded Successfully!</span>
            <a href="${data.youtube_url}" target="_blank" style="color: #60a5fa; text-decoration: underline; margin-left: 8px;">View on YouTube ↗</a>
          `;
        }
      } catch (e) {
        if (feedbackEl) feedbackEl.innerHTML = `<span style="color: #ef4444;">❌ Error: ${e.message}</span>`;
      } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<span>▶️</span> Auto-Upload to YouTube Shorts';
      }
    });
  }

})();
