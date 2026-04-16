/**
 * Alex Live Voice — OpenAI Whisper STT + OpenRouter LLM + OpenAI TTS (WAV base64)
 * STT: OpenAI Whisper  (MediaRecorder → /api/alex-voice-stt, needs OPENAI_API_KEY)
 * LLM: OpenRouter      (/api/alex-voice, needs OPENROUTER_API_KEY)
 * TTS: server returns WAV base64 — Fish Audio (Sol) if FISH_AUDIO_API_KEY is set, else OpenAI or browser fallback
 * Works on ALL browsers (Chrome, Firefox, Safari, Edge)
 */
(function () {
  var sessionId = Math.random().toString(36).slice(2); // fallback only
  var voiceStartedAt = 0;
  var limitTimer = null;
  var active = false;
  var processing = false;
  var mediaRecorder = null;
  var micStream = null;
  var audioChunks = [];
  var currentAudio = null;
  /** When using Blob URLs for TTS playback (Safari often fails on long data:audio/wav;base64,...). */
  var currentAudioObjectUrl = null;
  var maxRecordTimeout = null;

  function disposeCurrentPlayback() {
    try {
      if (currentAudio) {
        currentAudio.onended = null;
        currentAudio.onerror = null;
        currentAudio.pause();
      }
    } catch (e0) {}
    currentAudio = null;
    if (currentAudioObjectUrl) {
      try {
        URL.revokeObjectURL(currentAudioObjectUrl);
      } catch (e1) {}
      currentAudioObjectUrl = null;
    }
  }
  var introPlayed = false;

  /** Best-scoring system voice for SpeechSynthesis (neural / local voices rank higher). */
  var cachedBrowserVoice = null;

  // Voice Activity Detection (VAD) state
  var audioContext = null;
  var analyser = null;
  var vadInterval = null;
  var speechDetected = false;
  var silenceStart = 0;
  /** Smoothed mic level (0–~90); updated each VAD tick */
  var vadSmoothedRms = 0;
  /** When current “above start threshold” streak began; 0 = none */
  var vadSustainStart = 0;
  // Raw time-domain RMS is noisy; smooth + require sustained energy before “speech”
  var VAD_EMA_ALPHA = 0.28;
  // Must exceed this (after smoothing) to count toward speech onset — filters keyboard/fan hum
  var VAD_SPEECH_START_RMS = 18;
  // Lower threshold after speech began — keeps natural pauses inside a sentence
  var VAD_SPEECH_END_RMS = 10;
  // Require this many ms of continuous “loud” before we treat it as real speech
  var VAD_SPEECH_SUSTAIN_MS = 200;
  // Still run STT if blob is at least this big, even when VAD never armed (fixes “ok” / whispers)
  var MIN_BLOB_FOR_STT = 80;
  var SILENCE_DURATION = 1500;   // ms of silence before auto-stop
  var MAX_RECORD_MS = 15000;     // absolute max recording time
  /** If user never starts speaking, Alex checks in after this many ms */
  var NO_SPEECH_NUDGE_MS = 5000;
  var noSpeechNudgeTimer = null;
  var silenceNudgePending = false;

  function apiBase() {
    var base = (window.ALEX_API_BASE || '').replace(/\/$/, '');
    if (base) return base;
    if (location.port === '3000' || location.port === '3001') {
      return location.protocol + '//' + location.hostname + ':8000';
    }
    return '';
  }

  function voiceKey() {
    return window.ALEX_VOICE_KEY || sessionId;
  }

  function authToken() {
    try {
      var k = window.ALEX_AUTH_STORAGE_KEY || '';
      return k ? (localStorage.getItem(k) || '') : '';
    } catch (e) {
      return '';
    }
  }

  function authHeadersJson() {
    var h = { 'Content-Type': 'application/json' };
    var t = authToken();
    if (t) h['X-Auth-Token'] = t;
    return h;
  }

  function authHeadersForStt(audioMime) {
    var h = { 'Content-Type': audioMime || 'audio/webm' };
    var t = authToken();
    if (t) h['X-Auth-Token'] = t;
    return h;
  }

  function authHeadersForGet() {
    var h = {};
    var t = authToken();
    if (t) h['X-Auth-Token'] = t;
    return h;
  }

  /** @returns {boolean} true if caller should abort normal flow */
  function handleVoiceHttpError(status) {
    if (status === 401 || status === 403) {
      setStatus('Sign-in required');
      setTranscript('Your session expired — sign in again and reload this page.');
      stopAlex(true);
      return true;
    }
    if (status === 410) {
      setStatus('Session expired');
      setTranscript('Reload this page to start a new voice session.');
      stopAlex(true);
      return true;
    }
    return false;
  }

  console.log('[AlexVoice] loaded (orb UI + voice APIs + VAD)');

  function voiceQualityScore(v) {
    var n = (v.name || '').toLowerCase();
    var lang = (v.lang || '').toLowerCase();
    var s = 0;
    if (lang.indexOf('en') === 0) s += 18;
    try {
      if (v.localService) s += 50;
    } catch (e1) {}
    if (/premium|enhanced|neural|natural|wavenet|neural2|siri/.test(n)) s += 38;
    if (/google us english|google uk english|microsoft|samantha|^daniel\b|\baaron\b|\bava\b|matthew|melina|zoe|flo|tom/.test(n)) s += 22;
    if (/zarvox|bad news|whisper|pipe|bubbles|\.loc|compact/.test(n)) s -= 90;
    return s;
  }

  function refreshBrowserVoice() {
    cachedBrowserVoice = null;
    try {
      if (typeof speechSynthesis === 'undefined') return;
      var voices = speechSynthesis.getVoices();
      if (!voices || !voices.length) return;
      var best = null;
      var bestS = -1e9;
      var i;
      var sc;
      for (i = 0; i < voices.length; i++) {
        sc = voiceQualityScore(voices[i]);
        if (sc > bestS) {
          bestS = sc;
          best = voices[i];
        }
      }
      cachedBrowserVoice = best;
    } catch (e2) {}
  }

  if (typeof speechSynthesis !== 'undefined') {
    speechSynthesis.onvoiceschanged = refreshBrowserVoice;
    refreshBrowserVoice();
  }

  function preferBrowserVoiceOutput() {
    var v = window.ALEX_VOICE_BROWSER_ONLY;
    if (v === true || v === 1) return true;
    if (typeof v === 'string' && v.toLowerCase() === 'true') return true;
    return false;
  }

  /**
   * Decode server WAV base64 into a blob: URL — more reliable than huge data: URLs (esp. Safari).
   * @returns {string|null}
   */
  function wavBase64ToObjectUrl(b64) {
    try {
      var bin = atob(b64);
      var n = bin.length;
      var bytes = new Uint8Array(n);
      for (var i = 0; i < n; i++) bytes[i] = bin.charCodeAt(i);
      var blob = new Blob([bytes], { type: 'audio/wav' });
      return URL.createObjectURL(blob);
    } catch (e) {
      console.warn('[AlexVoice] invalid audio base64:', e);
      return null;
    }
  }

  // Attach click handler to button (React doesn't support string onclick)
  function attachBtn() {
    var btn = document.getElementById('alex-btn');
    if (btn && !btn._alexBound) {
      btn._alexBound = true;
      btn.addEventListener('click', function () { toggleAlexVoice(); });
      console.log('[AlexVoice] button bound');
    }
  }

  function setTypeUiEnabled(on) {
    var row = document.getElementById('alex-type-row');
    var inp = document.getElementById('alex-type-input');
    var snd = document.getElementById('alex-type-send');
    if (inp) inp.disabled = !on;
    if (snd) snd.disabled = !on;
    if (row) row.style.opacity = on ? '1' : '0.45';
  }

  function attachTypeUi() {
    var inp = document.getElementById('alex-type-input');
    var snd = document.getElementById('alex-type-send');
    if (inp && !inp._alexBound) {
      inp._alexBound = true;
      inp.addEventListener('focus', function () {
        if (active) abortCurrentListenSegment();
      });
      inp.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' && !ev.shiftKey) {
          ev.preventDefault();
          sendTypedAlexMessage();
        }
      });
    }
    if (snd && !snd._alexBound) {
      snd._alexBound = true;
      snd.addEventListener('click', function () { sendTypedAlexMessage(); });
    }
  }

  // Try immediately + poll for React render
  attachBtn();
  attachTypeUi();
  var _bindAttempts = 0;
  var _bindPoll = setInterval(function () {
    attachBtn();
    attachTypeUi();
    _bindAttempts++;
    var b = document.getElementById('alex-btn');
    var i = document.getElementById('alex-type-input');
    if ((b && b._alexBound && i && i._alexBound) || _bindAttempts > 100) {
      clearInterval(_bindPoll);
    }
  }, 300);

  // ── UI helpers ──────────────────────────────────────────────
  function setStatus(msg) {
    var el = document.getElementById('alex-status');
    if (el) el.textContent = msg;
  }

  function setTranscript(msg) {
    var el = document.getElementById('alex-transcript');
    if (!el) return;
    el.innerHTML = '';
    el.textContent = msg || '';
  }

  /** Rich markdown pane (server-rendered HTML) + optional plain user line above — like main chat. */
  /** Plain string for TTS fallbacks — never use raw markdown `text` as first choice. */
  function plainTextForVoiceTts(data) {
    var st = (data.speech_text || '').trim();
    if (st) return st;
    var html = data.display_html || '';
    if (html) {
      try {
        var d = document.createElement('div');
        d.innerHTML = html;
        var t = (d.textContent || d.innerText || '').trim();
        if (t) return t;
      } catch (e0) {}
    }
    var md = (data.text || '').trim();
    if (!md) return '';
    return md
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/^#{1,6}\s+/gm, '')
      .replace(/^\s*[-*•]\s+/gm, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function renderVoiceTranscriptBlock(userLinePlain, alexData) {
    var el = document.getElementById('alex-transcript');
    if (!el) return;
    el.innerHTML = '';
    if (userLinePlain) {
      var uw = document.createElement('div');
      uw.className = 'alex-voice-user-line';
      uw.textContent = userLinePlain;
      el.appendChild(uw);
    }
    if (alexData && (alexData.display_html || alexData.text)) {
      var box = document.createElement('div');
      box.className = 'claude-md alex-voice-md-pane';
      if (alexData.display_html) {
        box.innerHTML = alexData.display_html;
      } else {
        var p = document.createElement('p');
        p.textContent = alexData.text || '';
        box.appendChild(p);
      }
      el.appendChild(box);
    }
  }

  function upsellEnabled() {
    return window.ALEX_VOICE_SHOW_UPSELL !== false;
  }

  function showUpgradeButton() {
    if (!upsellEnabled()) return;
    var existing = document.getElementById('alex-upgrade-btn');
    if (existing) return;
    var btn = document.createElement('a');
    btn.id = 'alex-upgrade-btn';
    btn.textContent = '⭐ Upgrade to Premium';
    btn.href = '/pricing';
    btn.style.cssText = (
      'display:inline-block;margin-top:12px;padding:11px 28px;'
      + 'background:linear-gradient(135deg,#7c3aed,#4f46e5);'
      + 'color:white;border-radius:50px;font-size:.88rem;font-weight:600;'
      + 'text-decoration:none;letter-spacing:.03em;'
      + 'box-shadow:0 4px 15px rgba(124,58,237,.35);'
      + 'transition:opacity .2s;'
    );
    btn.onmouseover = function() { btn.style.opacity = '.85'; };
    btn.onmouseout  = function() { btn.style.opacity = '1'; };
    var transcript = document.getElementById('alex-transcript');
    if (transcript) transcript.after(btn);
  }

  function hideUpgradeButton() {
    var btn = document.getElementById('alex-upgrade-btn');
    if (btn) btn.remove();
  }

  function setOrbState(state) {
    // state: 'idle' | 'ai-speaking' | 'user-speaking' | 'thinking'
    var orb = document.getElementById('alex-orb');
    if (!orb) return;
    orb.className = state;
  }

  // ── Toggle ──────────────────────────────────────────────────
  window.toggleAlexVoice = async function () {
    if (active) { stopAlex(); return; }

    // Check access before requesting mic
    var allowed = (window.ALEX_VOICE_ALLOWED !== false);
    var btnEarly = document.getElementById('alex-btn');
    if (!allowed && btnEarly && btnEarly.textContent === 'Close' && window.__alex_overlay_mode) {
      var br0 = document.getElementById('alex-voice-overlay-close-bridge');
      if (br0) br0.click();
      return;
    }
    if (!allowed) {
      var reason = window.ALEX_VOICE_BLOCK_REASON || '';
      if (reason === 'home_blocked') {
        setStatus('Premium feature');
        setTranscript('Voice chat on the home page is available for premium users only.');
      } else if (reason === 'limit_reached') {
        setStatus("Daily limit reached");
        setTranscript("You've used your 10 min free voice chat for today. Come back tomorrow or upgrade for unlimited access.");
      } else {
        setStatus('Voice chat not available.');
      }
      if (upsellEnabled()) showUpgradeButton();
      var b0 = document.getElementById('alex-btn');
      if (b0) { b0.textContent = 'Close'; b0.disabled = false; b0.classList.remove('live'); }
      return;
    }

    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      alert('Microphone access is required for voice chat.');
      var bMic = document.getElementById('alex-btn');
      if (bMic) { bMic.textContent = 'Try again'; bMic.disabled = false; bMic.classList.remove('live'); }
      setStatus('Microphone blocked');
      return;
    }

    // Setup audio analysis for VAD
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    var source = audioContext.createMediaStreamSource(micStream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);

    active = true;
    voiceStartedAt = Date.now();
    hideUpgradeButton();
    setTypeUiEnabled(true);
    var btn = document.getElementById('alex-btn');
    if (btn) { btn.disabled = false; btn.textContent = 'END CALL'; btn.classList.add('live'); }

    // Set auto-cutoff timer for non-premium users (only when commercial gates + upsell are on)
    var remainingSec = window.ALEX_VOICE_REMAINING_SEC;
    if (upsellEnabled() && typeof remainingSec === 'number' && remainingSec > 0) {
      var minsLeft = Math.ceil(remainingSec / 60);
      setTranscript('Free usage: ' + minsLeft + ' min remaining today.');
      limitTimer = setTimeout(function () {
        setOrbState('idle');
        setStatus("Daily limit reached");
        setTranscript("You've used your 10 min free voice chat for today. Upgrade for unlimited access.");
        showUpgradeButton();
        stopAlex();
      }, remainingSec * 1000);
    }

    if (!introPlayed) {
      introPlayed = true;
      playIntro();
    } else {
      startListening();
    }
  };

  // ── Auto-introduction ────────────────────────────────────────
  async function playIntro() {
    setOrbState('thinking');
    setStatus('Alex is waking up...');
    setTranscript('');
    try {
      var resp = await fetch(
        apiBase() + '/api/alex-voice-intro?voice_key=' + encodeURIComponent(voiceKey()),
        { headers: authHeadersForGet() }
      );
      if (!resp.ok) {
        if (handleVoiceHttpError(resp.status)) return;
        setStatus('Could not load intro');
        setTranscript('Tap END CALL and try again, or reload the page.');
        if (active) startListening();
        return;
      }
      var data = await resp.json();
      playAlexVoiceResponse(data);
    } catch (e) {
      console.error('[AlexVoice] intro error:', e);
      if (active) startListening();
    }
  }

  // ── Listening with silence detection ────────────────────────
  function startListening() {
    if (!active || !micStream) return;
    processing = false;
    audioChunks = [];
    speechDetected = false;
    silenceStart = 0;
    vadSmoothedRms = 0;
    vadSustainStart = 0;
    silenceNudgePending = false;
    clearNoSpeechNudgeTimer();
    setOrbState('idle');
    setStatus('Listening to you, bro...');
    setTranscript('');

    // Choose supported mime
    var mimeType = 'audio/webm;codecs=opus';
    if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'audio/webm';
    if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'audio/mp4';
    if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = '';

    try {
      mediaRecorder = new MediaRecorder(micStream, mimeType ? { mimeType: mimeType } : {});
    } catch (e) {
      console.error('[AlexVoice] MediaRecorder error:', e);
      setStatus('Mic recorder error — resetting');
      stopAlex(true);
      return;
    }

    mediaRecorder.ondataavailable = function (e) {
      if (e.data && e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = function () {
      stopVAD();
      if (!active) return;
      if (silenceNudgePending) {
        silenceNudgePending = false;
        fetchSilenceNudgeAndPlay();
        return;
      }
      if (audioChunks.length === 0) { startListening(); return; }

      var blob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      console.log('[AlexVoice] recorded', blob.size, 'B, vadSpeech=' + speechDetected);
      if (blob.size < MIN_BLOB_FOR_STT) { startListening(); return; }

      if (!speechDetected) {
        console.log('[AlexVoice] VAD did not flag speech — running STT anyway (short/quiet clips)');
      }

      processing = true;
      setOrbState('thinking');
      setStatus('Processing...');
      setTranscript('');
      transcribeAndRespond(blob);
    };

    mediaRecorder.start(200);

    // Start VAD — monitors audio level and auto-stops on silence
    startVAD();

    // Absolute max recording safety net
    maxRecordTimeout = setTimeout(function () {
      finishRecording();
    }, MAX_RECORD_MS);

    scheduleNoSpeechNudge();

    console.log('[AlexVoice] recording...');
  }

  // ── Voice Activity Detection ────────────────────────────────
  function startVAD() {
    if (!analyser) return;
    var dataArray = new Uint8Array(analyser.fftSize);

    vadInterval = setInterval(function () {
      analyser.getByteTimeDomainData(dataArray);

      var sum = 0;
      for (var i = 0; i < dataArray.length; i++) {
        var v = dataArray[i] - 128;
        sum += v * v;
      }
      var rawRms = Math.sqrt(sum / dataArray.length);
      vadSmoothedRms = vadSmoothedRms * (1 - VAD_EMA_ALPHA) + rawRms * VAD_EMA_ALPHA;

      var now = Date.now();

      if (!speechDetected) {
        // Ignore brief spikes: only arm after sustained energy
        if (vadSmoothedRms >= VAD_SPEECH_START_RMS) {
          if (!vadSustainStart) vadSustainStart = now;
          if (now - vadSustainStart >= VAD_SPEECH_SUSTAIN_MS) {
            speechDetected = true;
            vadSustainStart = 0;
            clearTimeout(noSpeechNudgeTimer);
            noSpeechNudgeTimer = null;
            setOrbState('user-speaking');
            setStatus('Hearing you...');
            silenceStart = 0;
            console.log('[AlexVoice] speech started (sustained)');
          }
        } else {
          vadSustainStart = 0;
        }
      } else {
        // Hysteresis: end only when level drops below lower threshold
        if (vadSmoothedRms >= VAD_SPEECH_END_RMS) {
          silenceStart = 0;
        } else {
          if (!silenceStart) silenceStart = now;
          else if (now - silenceStart > SILENCE_DURATION) {
            console.log('[AlexVoice] silence detected, auto-stopping');
            finishRecording();
          }
        }
      }
    }, 100);
  }

  function stopVAD() {
    if (vadInterval) { clearInterval(vadInterval); vadInterval = null; }
    if (maxRecordTimeout) { clearTimeout(maxRecordTimeout); maxRecordTimeout = null; }
  }

  function clearNoSpeechNudgeTimer() {
    if (noSpeechNudgeTimer) {
      clearTimeout(noSpeechNudgeTimer);
      noSpeechNudgeTimer = null;
    }
  }

  function scheduleNoSpeechNudge() {
    clearNoSpeechNudgeTimer();
    noSpeechNudgeTimer = setTimeout(function () {
      noSpeechNudgeTimer = null;
      if (!active || speechDetected || processing) return;
      if (!mediaRecorder || mediaRecorder.state !== 'recording') return;
      silenceNudgePending = true;
      finishRecording();
    }, NO_SPEECH_NUDGE_MS);
  }

  function finishRecording() {
    stopVAD();
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
  }

  /** Drop the current mic segment without running STT (used when user types instead). */
  function abortCurrentListenSegment() {
    stopVAD();
    clearNoSpeechNudgeTimer();
    silenceNudgePending = false;
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.onstop = null;
      mediaRecorder.stop();
    }
    audioChunks = [];
  }

  async function fetchVoiceReplyAndPlay(transcript) {
    setOrbState('thinking');
    setStatus('Alex is thinking...');
    try {
      var resp = await fetch(apiBase() + '/api/alex-voice', {
        method: 'POST',
        headers: authHeadersJson(),
        body: JSON.stringify({ transcript: transcript, voice_key: voiceKey() })
      });
      if (!resp.ok) {
        if (handleVoiceHttpError(resp.status)) return;
        var vErr = 'Voice reply failed.';
        try {
          var vBody = await resp.json();
          if (vBody.error) vErr = String(vBody.error);
        } catch (e2) {}
        setStatus('Alex could not reply');
        try {
          window.__voiceLastUserLine = '';
        } catch (eClr) {}
        setTranscript(vErr);
        setOrbState('idle');
        processing = false;
        setTimeout(function () { if (active) startListening(); }, 2200);
        return;
      }
      var data = await resp.json();
      processing = false;
      playAlexVoiceResponse(data);
    } catch (err) {
      console.error('[AlexVoice] API error:', err);
      try {
        window.__voiceLastUserLine = '';
      } catch (eClr2) {}
      setStatus('Network error — retrying...');
      setOrbState('idle');
      processing = false;
      setTimeout(function () { if (active) startListening(); }, 1500);
    }
  }

  async function sendTypedAlexMessage() {
    var input = document.getElementById('alex-type-input');
    if (!input || !active) {
      if (!active) setStatus('Start the call first — then type or speak.');
      return;
    }
    var text = (input.value || '').trim();
    if (!text) return;
    if (processing) {
      setStatus('Hang on… still processing.');
      return;
    }
    input.value = '';

    disposeCurrentPlayback();
    speechSynthesis.cancel();

    abortCurrentListenSegment();

    processing = true;
    setOrbState('thinking');
    setStatus('Alex is thinking...');
    window.__voiceLastUserLine = 'You: ' + text;
    setTranscript('');

    await fetchVoiceReplyAndPlay(text);
  }

  function playAlexVoiceResponse(data) {
    var uLine = window.__voiceLastUserLine || '';
    window.__voiceLastUserLine = '';
    console.log('[AlexVoice] response:', (data.text || '').substring(0, 80), '| audio:', (data.audio_b64 || '').length);
    disposeCurrentPlayback();
    try {
      if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
    } catch (eC) {}
    setOrbState('ai-speaking');
    setStatus('Alex is speaking...');
    if (data.display_html || data.text) {
      renderVoiceTranscriptBlock(uLine, data);
    } else if (uLine) {
      setTranscript(uLine);
    }
    var speechText = plainTextForVoiceTts(data);

    var done = function () {
      setTranscript('');
      setOrbState('idle');
      if (active) startListening();
    };

    if (data.audio_b64 && !preferBrowserVoiceOutput()) {
      var objectUrl = wavBase64ToObjectUrl(data.audio_b64);
      if (!objectUrl) {
        console.warn('[AlexVoice] no playable server audio — browser TTS fallback');
        if (speechText) speakBrowserTTS(speechText, done);
        else done();
        return;
      }
      currentAudioObjectUrl = objectUrl;
      currentAudio = new Audio(objectUrl);
      currentAudio.onended = function () {
        disposeCurrentPlayback();
        done();
      };
      currentAudio.onerror = function () {
        console.warn('[AlexVoice] <audio> error — browser TTS fallback');
        disposeCurrentPlayback();
        if (speechText) {
          speakBrowserTTS(speechText, done);
        } else {
          done();
        }
      };
      currentAudio.play().catch(function (err) {
        console.warn('[AlexVoice] play() blocked or failed — browser TTS fallback', err);
        disposeCurrentPlayback();
        if (speechText) {
          speakBrowserTTS(speechText, done);
        } else {
          done();
        }
      });
    } else if (speechText) {
      if (!data.audio_b64 && !preferBrowserVoiceOutput()) {
        console.warn('[AlexVoice] empty server audio (check OPENAI_API_KEY + redeploy / Railway logs) — browser TTS fallback');
      }
      speakBrowserTTS(speechText, done);
    } else {
      setOrbState('idle');
      if (active) startListening();
    }
  }

  async function fetchSilenceNudgeAndPlay() {
    if (!active) return;
    processing = true;
    setOrbState('thinking');
    setStatus('Alex is checking in...');
    setTranscript('');
    try {
      var resp = await fetch(apiBase() + '/api/alex-voice', {
        method: 'POST',
        headers: authHeadersJson(),
        body: JSON.stringify({ silence_nudge: true, voice_key: voiceKey() })
      });
      if (!resp.ok) {
        if (handleVoiceHttpError(resp.status)) return;
        processing = false;
        setOrbState('idle');
        if (active) startListening();
        return;
      }
      var data = await resp.json();
      processing = false;
      playAlexVoiceResponse(data);
    } catch (e) {
      console.error('[AlexVoice] silence nudge error:', e);
      processing = false;
      setOrbState('idle');
      setTimeout(function () { if (active) startListening(); }, 1200);
    }
  }

  // ── Transcribe → LLM → TTS → Play ──────────────────────────
  async function transcribeAndRespond(audioBlob) {
    clearNoSpeechNudgeTimer();
    // Step 1: STT
    setStatus('Transcribing...');
    var transcript = '';
    try {
      var sttResp = await fetch(apiBase() + '/api/alex-voice-stt', {
        method: 'POST',
        headers: authHeadersForStt(audioBlob.type),
        body: audioBlob
      });
      if (!sttResp.ok) {
        if (handleVoiceHttpError(sttResp.status)) return;
        var sttErr = 'Transcription failed. Try again.';
        try {
          var sttErrBody = await sttResp.json();
          if (sttErrBody.error) sttErr = String(sttErrBody.error);
        } catch (e1) {}
        setOrbState('idle');
        setStatus('Could not transcribe');
        setTranscript(sttErr);
        processing = false;
        setTimeout(function () { if (active) startListening(); }, 2200);
        return;
      }
      var sttData = await sttResp.json();
      transcript = (sttData.text || '').trim();
      console.log('[AlexVoice] transcript:', transcript);
      if (transcript) window.__voiceLastUserLine = 'You: ' + transcript;
      setTranscript('');
    } catch (e) {
      console.error('[AlexVoice] STT error:', e);
      setOrbState('idle');
      setStatus('Transcription error');
      processing = false;
      setTimeout(function () { if (active) startListening(); }, 1500);
      return;
    }

    if (!transcript.length) {
      setOrbState('idle');
      processing = false;
      startListening();
      return;
    }

    await fetchVoiceReplyAndPlay(transcript);
  }

  function speakBrowserTTS(text, onDone) {
    var utter = new SpeechSynthesisUtterance(text);
    if (typeof speechSynthesis !== 'undefined') {
      if (!cachedBrowserVoice) refreshBrowserVoice();
      if (cachedBrowserVoice) utter.voice = cachedBrowserVoice;
    }
    utter.onend = function () { if (onDone) onDone(); };
    utter.onerror = function () { if (onDone) onDone(); };
    if (typeof speechSynthesis !== 'undefined') speechSynthesis.speak(utter);
    else if (onDone) onDone();
  }

  // ── Stop ────────────────────────────────────────────────────
  function stopAlex(skipSync) {
    // Fire-and-forget: sync voice session back to text chat DB
    var durationSec = voiceStartedAt ? Math.round((Date.now() - voiceStartedAt) / 1000) : 0;
    if (!skipSync) {
      fetch(apiBase() + '/api/alex-voice-sync', {
        method: 'POST',
        headers: authHeadersJson(),
        body: JSON.stringify({ voice_key: voiceKey(), duration_seconds: durationSec })
      })
        .then(function (r) {
          return r.json().then(function (d) {
            if (!r.ok) {
              console.warn('[AlexVoice] sync HTTP', r.status, d);
            } else {
              console.log('[AlexVoice] synced voice session to text chat:', d);
            }
          });
        })
        .catch(function (e) { console.warn('[AlexVoice] sync failed:', e); });
    }
    voiceStartedAt = 0;
    try {
      window.__voiceLastUserLine = '';
    } catch (eVu) {}

    active = false;
    processing = false;
    if (limitTimer) { clearTimeout(limitTimer); limitTimer = null; }
    clearNoSpeechNudgeTimer();
    silenceNudgePending = false;
    stopVAD();
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.onstop = null;
      mediaRecorder.stop();
    }
    mediaRecorder = null;
    if (micStream) { micStream.getTracks().forEach(function (t) { t.stop(); }); micStream = null; }
    if (audioContext) { audioContext.close().catch(function(){}); audioContext = null; analyser = null; }
    disposeCurrentPlayback();
    speechSynthesis.cancel();
    setOrbState('idle');
    setStatus('Tap to start voice chat');
    setTranscript('');
    setTypeUiEnabled(false);
    var tin = document.getElementById('alex-type-input');
    if (tin) tin.value = '';
    var btn = document.getElementById('alex-btn');
    if (btn) { btn.textContent = 'GO LIVE WITH ALEX'; btn.classList.remove('live'); btn.disabled = false; }
    if (window.__alex_overlay_mode) {
      var bridge = document.getElementById('alex-voice-overlay-close-bridge');
      if (bridge) bridge.click();
    }
  }

  window.stopAlexVoiceSession = function () { stopAlex(false); };
})();
