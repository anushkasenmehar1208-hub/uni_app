/**
 * Alex 3D Avatar — realistic talking head overlay on top of #alex-orb.
 * Zero-touch integration with alex_voice.js:
 *   - State:     MutationObserver on #alex-orb className  →  avatar anim state
 *   - Lip-sync:  patched HTMLMediaElement.prototype.play  →  Web Audio analyser  →  jaw/viseme morphs
 *   - Fallback:  if WebGL / GLB unavailable, the original orb animation stays visible underneath.
 *
 * Tech: Three.js r160 + GLTFLoader + Ready Player Me (.glb, ARKit + Oculus Visemes morph targets).
 */
(function () {
  'use strict';

  // ── Config ─────────────────────────────────────────────────────────────────
  var AVATAR_URL =
    (window.ALEX_AVATAR_URL && typeof window.ALEX_AVATAR_URL === 'string')
      ? window.ALEX_AVATAR_URL
      // Default: free Ready Player Me preset, realistic young man, with visemes for lip-sync.
      : 'https://models.readyplayer.me/64bfa15f0e72c63d7c3934a6.glb?morphTargets=ARKit,Oculus%20Visemes&textureAtlas=1024';

  var THREE_CDN = 'https://unpkg.com/three@0.160.0/build/three.module.js';
  var GLTF_CDN  = 'https://unpkg.com/three@0.160.0/examples/jsm/loaders/GLTFLoader.js';

  // Debug switch: window.ALEX_AVATAR_DEBUG = true to enable console logs.
  function log() {
    if (window.ALEX_AVATAR_DEBUG) {
      try { console.log.apply(console, ['[AlexAvatar]'].concat([].slice.call(arguments))); } catch (e) {}
    }
  }
  function warn() {
    try { console.warn.apply(console, ['[AlexAvatar]'].concat([].slice.call(arguments))); } catch (e) {}
  }

  // Prevent double-init if the boot script re-injects us on a new voice session.
  if (window.__alexAvatarBooted) {
    log('already booted, skipping');
    return;
  }
  window.__alexAvatarBooted = true;

  // ── WebGL capability check ────────────────────────────────────────────────
  function hasWebGL() {
    try {
      var c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl') || c.getContext('experimental-webgl')));
    } catch (e) { return false; }
  }

  if (!hasWebGL()) {
    warn('WebGL unavailable — falling back to original orb.');
    return;
  }

  // ── Lip-sync shared analyser (patched once, used by avatar) ───────────────
  var sharedAudioCtx = null;
  var sharedAnalyser = null;
  var sharedData = null;
  var patchedAudios = new WeakSet();

  function ensureAudioCtx() {
    if (sharedAudioCtx) return sharedAudioCtx;
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return null;
      sharedAudioCtx = new Ctx();
      sharedAnalyser = sharedAudioCtx.createAnalyser();
      sharedAnalyser.fftSize = 512;
      sharedAnalyser.smoothingTimeConstant = 0.55;
      sharedAnalyser.connect(sharedAudioCtx.destination);
      sharedData = new Uint8Array(sharedAnalyser.frequencyBinCount);
    } catch (e) {
      warn('AudioContext init failed', e);
      sharedAudioCtx = null;
    }
    return sharedAudioCtx;
  }

  function connectAudioElement(audioEl) {
    if (!audioEl || patchedAudios.has(audioEl)) return;
    var ctx = ensureAudioCtx();
    if (!ctx) return;
    try {
      // Resume if suspended (Safari/autoplay policy safety net).
      if (ctx.state === 'suspended') { ctx.resume().catch(function () {}); }
      var src = ctx.createMediaElementSource(audioEl);
      src.connect(sharedAnalyser);
      patchedAudios.add(audioEl);
      log('connected audio element to analyser');
    } catch (e) {
      // createMediaElementSource throws if already connected elsewhere — safe to ignore.
      log('connect skipped:', e && e.message);
    }
  }

  // Patch play() once — every <audio> created anywhere on the page is auto-connected.
  (function patchAudioPlay() {
    try {
      var proto = window.HTMLMediaElement && window.HTMLMediaElement.prototype;
      if (!proto || proto.__alexAvatarPatched) return;
      var origPlay = proto.play;
      proto.play = function () {
        try { connectAudioElement(this); } catch (e) {}
        return origPlay.apply(this, arguments);
      };
      proto.__alexAvatarPatched = true;
      log('HTMLMediaElement.play patched');
    } catch (e) { warn('play patch failed', e); }
  })();

  // Returns 0..1 rough loudness in a voice-ish band (roughly 200Hz–3kHz).
  function sampleLoudness() {
    if (!sharedAnalyser || !sharedData) return 0;
    try {
      sharedAnalyser.getByteFrequencyData(sharedData);
      // AnalyserNode bins cover 0..sampleRate/2 across frequencyBinCount bins.
      // We'll read a middle slice (skip rumble + hiss) and average.
      var start = 4, end = Math.min(sharedData.length, 64);
      var sum = 0, count = 0;
      for (var i = start; i < end; i++) { sum += sharedData[i]; count++; }
      var avg = count ? sum / count : 0;
      return Math.min(1, avg / 180); // 180 picked so normal speech reaches ~0.7–1.0
    } catch (e) { return 0; }
  }

  // ── Dynamic ES module loader for Three.js ─────────────────────────────────
  function loadThreeModules() {
    // Use dynamic import via a Blob so we can pin versions without build step.
    // We return a Promise resolving to { THREE, GLTFLoader }.
    var importMapId = '_alex_avatar_importmap';
    if (!document.getElementById(importMapId)) {
      try {
        var im = document.createElement('script');
        im.type = 'importmap';
        im.id = importMapId;
        im.textContent = JSON.stringify({
          imports: {
            'three': THREE_CDN,
            'three/addons/': 'https://unpkg.com/three@0.160.0/examples/jsm/'
          }
        });
        // Importmaps must be inserted before any module that uses them.
        (document.head || document.documentElement).appendChild(im);
      } catch (e) { warn('importmap insert failed', e); }
    }

    return new Promise(function (resolve, reject) {
      var bootId = '_alex_avatar_bootmod';
      if (document.getElementById(bootId)) {
        // Already loading — wait for the global.
        var check = 0;
        (function wait() {
          if (window.__alexAvatarTHREE) return resolve(window.__alexAvatarTHREE);
          if (++check > 200) return reject(new Error('THREE load timeout'));
          setTimeout(wait, 50);
        })();
        return;
      }
      var boot = document.createElement('script');
      boot.id = bootId;
      boot.type = 'module';
      boot.textContent = [
        "import * as THREE from 'three';",
        "import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';",
        "window.__alexAvatarTHREE = { THREE: THREE, GLTFLoader: GLTFLoader };",
        "window.dispatchEvent(new Event('alex-avatar-three-ready'));"
      ].join('\n');
      boot.onerror = function (e) { reject(new Error('three module load error')); };
      window.addEventListener('alex-avatar-three-ready', function once() {
        window.removeEventListener('alex-avatar-three-ready', once);
        if (window.__alexAvatarTHREE) resolve(window.__alexAvatarTHREE);
        else reject(new Error('THREE global missing after load'));
      });
      (document.head || document.documentElement).appendChild(boot);
      // Safety timeout.
      setTimeout(function () {
        if (!window.__alexAvatarTHREE) reject(new Error('THREE load timeout'));
      }, 15000);
    });
  }

  // ── DOM helpers ───────────────────────────────────────────────────────────
  function waitForOrb(timeoutMs) {
    return new Promise(function (resolve, reject) {
      var existing = document.getElementById('alex-orb');
      if (existing) return resolve(existing);
      var obs = new MutationObserver(function () {
        var el = document.getElementById('alex-orb');
        if (el) { obs.disconnect(); resolve(el); }
      });
      obs.observe(document.documentElement, { childList: true, subtree: true });
      setTimeout(function () { obs.disconnect(); reject(new Error('orb not found')); }, timeoutMs || 20000);
    });
  }

  function injectStyleOnce() {
    if (document.getElementById('alex-avatar-styles')) return;
    var st = document.createElement('style');
    st.id = 'alex-avatar-styles';
    st.textContent = [
      // Let the canvas extend outside the 220px orb bounds so avatar can be bigger.
      '#alex-orb { overflow: visible !important; }',
      // Avatar canvas sits centered over the orb; pointer-events off so buttons still work.
      '#alex-avatar-canvas {',
      '  position: absolute;',
      '  top: 50%; left: 50%;',
      '  transform: translate(-50%, -50%);',
      '  width: 380px; height: 380px;',
      '  max-width: 92vw; max-height: 92vw;',
      '  pointer-events: none;',
      '  border-radius: 50%;',
      '  opacity: 0;',
      '  transition: opacity .6s ease;',
      '  z-index: 2;',
      '}',
      '#alex-avatar-canvas.alex-avatar-ready { opacity: 1; }',
      // Once avatar is ready, fade the old orb core/rings so they act as soft halo only.
      '#alex-orb.alex-avatar-active .orb-core { opacity: .25; }',
      '#alex-orb.alex-avatar-active.ai-speaking .orb-core,',
      '#alex-orb.alex-avatar-active.user-speaking .orb-core { opacity: .55; }',
      '@media (max-width: 520px) {',
      '  #alex-avatar-canvas { width: 300px; height: 300px; }',
      '}'
    ].join('\n');
    document.head.appendChild(st);
  }

  // ── Main boot ─────────────────────────────────────────────────────────────
  function boot() {
    injectStyleOnce();

    waitForOrb().then(function (orb) {
      var canvas = document.createElement('canvas');
      canvas.id = 'alex-avatar-canvas';
      orb.appendChild(canvas);

      loadThreeModules()
        .then(function (mods) { return initScene(mods, canvas, orb); })
        .catch(function (err) {
          warn('3D init failed, keeping orb fallback:', err && err.message);
          try { canvas.remove(); } catch (e) {}
        });
    }).catch(function (err) {
      warn('could not find #alex-orb:', err && err.message);
    });
  }

  function initScene(mods, canvas, orb) {
    var THREE = mods.THREE;
    var GLTFLoader = mods.GLTFLoader;

    var scene = new THREE.Scene();
    scene.background = null; // transparent

    var camera = new THREE.PerspectiveCamera(28, 1, 0.1, 50);
    // Head-and-shoulders framing: camera at eye level, ~2.2m back, looking at face height.
    camera.position.set(0, 1.58, 2.4);
    camera.lookAt(0, 1.58, 0);

    var renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    sizeToCanvas();

    // Flattering three-point lighting for skin.
    var key = new THREE.DirectionalLight(0xffffff, 2.4);
    key.position.set(1.2, 2.2, 2.5);
    scene.add(key);
    var fill = new THREE.DirectionalLight(0x88aaff, 0.7);
    fill.position.set(-2.0, 1.2, 1.5);
    scene.add(fill);
    var rim = new THREE.DirectionalLight(0xffffff, 1.1);
    rim.position.set(0.2, 2.0, -2.0);
    scene.add(rim);
    scene.add(new THREE.AmbientLight(0xffffff, 0.35));

    // State container.
    var rig = {
      root: null,
      head: null,
      morphMeshes: [],       // meshes with morphTargetDictionary
      jawOpenKeys: [],       // preferred morph target names per mesh for jaw
      viseme: {},            // mesh → index of best "aa/open" viseme
      currentState: 'idle',
      targetState: 'idle',
      loudness: 0,
      t: 0
    };

    function sizeToCanvas() {
      // Use CSS pixel size — canvas has fixed ratio via CSS, but DPR-aware drawing buffer.
      var rect = canvas.getBoundingClientRect();
      var w = Math.max(64, rect.width | 0);
      var h = Math.max(64, rect.height | 0);
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    window.addEventListener('resize', sizeToCanvas);

    // Load avatar.
    var loader = new GLTFLoader();
    loader.load(
      AVATAR_URL,
      function onLoaded(gltf) {
        var avatar = gltf.scene;
        avatar.traverse(function (node) {
          if (node.isMesh) {
            node.castShadow = false;
            node.receiveShadow = false;
            if (node.morphTargetDictionary && node.morphTargetInfluences) {
              rig.morphMeshes.push(node);
              // Pick best available jaw/open morph by priority.
              var dict = node.morphTargetDictionary;
              var priorities = [
                'jawOpen',        // ARKit
                'mouthOpen',
                'viseme_aa',      // Oculus Visemes
                'viseme_O',
                'viseme_E',
                'viseme_U'
              ];
              for (var i = 0; i < priorities.length; i++) {
                if (priorities[i] in dict) {
                  rig.viseme[node.uuid] = dict[priorities[i]];
                  break;
                }
              }
            }
          }
          if (node.isBone || node.type === 'Bone') {
            var nm = (node.name || '').toLowerCase();
            if (!rig.head && (nm === 'head' || nm.indexOf('head') !== -1)) {
              rig.head = node;
            }
          }
        });

        rig.root = avatar;
        scene.add(avatar);
        log('avatar loaded — morph meshes:', rig.morphMeshes.length, 'head bone:', !!rig.head);

        canvas.classList.add('alex-avatar-ready');
        orb.classList.add('alex-avatar-active');

        startObservers();
        startLoop();
      },
      undefined,
      function onErr(err) {
        warn('GLB load failed:', err);
        try { canvas.remove(); } catch (e) {}
      }
    );

    function startObservers() {
      rig.currentState = (orb.className || 'idle').trim().split(/\s+/)[0] || 'idle';
      rig.targetState = rig.currentState;
      var obs = new MutationObserver(function () {
        var cls = (orb.className || '').trim().split(/\s+/);
        // Pick the first known state class.
        var known = ['idle', 'ai-speaking', 'user-speaking', 'thinking'];
        for (var i = 0; i < cls.length; i++) {
          if (known.indexOf(cls[i]) !== -1) {
            rig.targetState = cls[i];
            return;
          }
        }
        rig.targetState = 'idle';
      });
      obs.observe(orb, { attributes: true, attributeFilter: ['class'] });
    }

    var clock = new THREE.Clock();
    function startLoop() {
      renderer.setAnimationLoop(function () {
        var dt = Math.min(0.05, clock.getDelta());
        rig.t += dt;

        // Idle breathing: subtle vertical bob + head sway.
        if (rig.root) {
          var breath = Math.sin(rig.t * 1.6) * 0.006;
          rig.root.position.y = breath;
        }
        if (rig.head) {
          var swayX = Math.sin(rig.t * 0.6) * 0.04;
          var swayY = Math.sin(rig.t * 0.4 + 1.2) * 0.03;
          // Only add gentle sway when not actively speaking loudly (don't fight lipsync/head nod).
          rig.head.rotation.y = swayX;
          rig.head.rotation.x = swayY;

          if (rig.targetState === 'thinking') {
            rig.head.rotation.y = Math.sin(rig.t * 1.5) * 0.12;
            rig.head.rotation.x = -0.05 + Math.sin(rig.t * 2.3) * 0.04;
          } else if (rig.targetState === 'user-speaking') {
            // Listening: small attentive nod.
            rig.head.rotation.x = -0.02 + Math.sin(rig.t * 0.9) * 0.02;
          } else if (rig.targetState === 'ai-speaking') {
            // Speaking: livelier movement driven partly by audio loudness.
            var l = rig.loudness;
            rig.head.rotation.y = swayX + Math.sin(rig.t * 2.1) * 0.04 * l;
            rig.head.rotation.x = swayY + Math.sin(rig.t * 2.8) * 0.03 * l;
          }
        }

        // Lip-sync: drive jaw morph from loudness, but only while speaking.
        var targetMouth = 0;
        if (rig.targetState === 'ai-speaking') {
          rig.loudness = rig.loudness * 0.55 + sampleLoudness() * 0.45;
          targetMouth = Math.min(0.85, rig.loudness * 1.1);
        } else {
          rig.loudness *= 0.9;
        }
        for (var i = 0; i < rig.morphMeshes.length; i++) {
          var m = rig.morphMeshes[i];
          var idx = rig.viseme[m.uuid];
          if (idx == null) continue;
          var cur = m.morphTargetInfluences[idx] || 0;
          m.morphTargetInfluences[idx] = cur + (targetMouth - cur) * 0.35;
        }

        renderer.render(scene, camera);
      });
    }
  }

  // Kick off when DOM is ready (handles both before/after DOMContentLoaded).
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }

  // Expose a tiny debug API.
  window.AlexAvatar = {
    version: '0.1.0',
    isBooted: function () { return !!window.__alexAvatarBooted; }
  };
})();
