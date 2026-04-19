/**
 * Alex 3D Avatar — realistic talking head overlay on top of a target orb.
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
  // Resolve default avatar URL relative to THIS script's location so the same file
  // works both inside the Reflex app (/alex_avatar.js → /models/…) and when the
  // script is served from /assets/ (e.g. static test harness).
  var AVATAR_SCRIPT_SRC =
    (document.currentScript && document.currentScript.src) ||
    (function () {
      var scripts = document.getElementsByTagName('script');
      for (var i = scripts.length - 1; i >= 0; i--) {
        var s = scripts[i].src || '';
        if (/alex_avatar\.js(\?|$)/.test(s)) return s;
      }
      return '';
    })();
  var AVATAR_URL_BASE = AVATAR_SCRIPT_SRC.replace(/[^/?#]*(\?.*)?(#.*)?$/, '');
  // Default avatar: full-body Ready Player Me character (dressed, with hair + ARKit/Oculus visemes).
  var LOCAL_AVATAR_URL = AVATAR_URL_BASE + 'models/alex_body.glb';
  // Fallback CDN copy — used only if the local file is missing.
  var REMOTE_AVATAR_URL =
    'https://raw.githubusercontent.com/wass08/r3f-virtual-girlfriend-frontend/main/public/models/64f1a714fe61576b46f27ca2.glb';
  var AVATAR_URL =
    (window.ALEX_AVATAR_URL && typeof window.ALEX_AVATAR_URL === 'string')
      ? window.ALEX_AVATAR_URL
      : LOCAL_AVATAR_URL;
  var AVATAR_URL_FALLBACK = REMOTE_AVATAR_URL;

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

  window.__alexAvatarBootedTargets = window.__alexAvatarBootedTargets || {};

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
        "import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';",
        "import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';",
        "import { OrbitControls } from 'three/addons/controls/OrbitControls.js';",
        "window.__alexAvatarTHREE = { THREE: THREE, GLTFLoader: GLTFLoader, KTX2Loader: KTX2Loader, MeshoptDecoder: MeshoptDecoder, OrbitControls: OrbitControls };",
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
  function waitForOrb(targetId, timeoutMs) {
    return new Promise(function (resolve, reject) {
      var existing = document.getElementById(targetId);
      if (existing) return resolve(existing);
      var obs = new MutationObserver(function () {
        var el = document.getElementById(targetId);
        if (el) { obs.disconnect(); resolve(el); }
      });
      obs.observe(document.documentElement, { childList: true, subtree: true });
      setTimeout(function () { obs.disconnect(); reject(new Error('orb not found')); }, timeoutMs || 20000);
    });
  }

  function injectStyleOnce(targetId, canvasId) {
    var styleId = 'alex-avatar-styles-' + targetId;
    if (document.getElementById(styleId)) return;
    var st = document.createElement('style');
    st.id = styleId;
    st.textContent = [
      // Let the canvas extend well outside the 220px orb bounds so the full body can show.
      '#' + targetId + ' { overflow: visible !important; }',
      // Portrait-aspect canvas centered on the orb so the avatar reads as a person standing.
      // Bottom ~25% fades to transparent so the character's legs visually merge into the
      // transcript "wall" that sits below the orb.
      '#' + canvasId + ' {',
      '  position: absolute;',
      '  left: 50%;',
      '  top: 50%;',
      '  transform: translate(-50%, -58%);',
      '  width: 320px; height: 520px;',
      '  max-width: 92vw;',
      '  pointer-events: auto;',
      '  cursor: grab;',
      '  opacity: 0;',
      '  transition: opacity .6s ease;',
      '  z-index: 2;',
      '  touch-action: none;',
      // Hard-ish fade at the waist so the bottom half of the body tucks neatly behind
      // the wall below, rather than bleeding onto the transcript text.
      '  -webkit-mask-image: linear-gradient(to bottom, black 0%, black 68%, rgba(0,0,0,0.35) 82%, transparent 92%);',
      '          mask-image: linear-gradient(to bottom, black 0%, black 68%, rgba(0,0,0,0.35) 82%, transparent 92%);',
      '}',
      '#' + canvasId + ':active { cursor: grabbing; }',
      '#' + canvasId + '.alex-avatar-ready { opacity: 1; }',
      // Once avatar is ready, strongly dim the old orb core so only a soft halo remains around the avatar.
      '#' + targetId + '.alex-avatar-active .orb-core { opacity: .15; }',
      '#' + targetId + '.alex-avatar-active.ai-speaking .orb-core,',
      '#' + targetId + '.alex-avatar-active.user-speaking .orb-core { opacity: .30; }',
      '@media (max-width: 520px) {',
      '  #' + canvasId + ' { width: 280px; height: 460px; }',
      '}'
    ].join('\n');
    document.head.appendChild(st);
  }

  // ── Main boot ─────────────────────────────────────────────────────────────
  function boot(targetId) {
    targetId = targetId || 'alex-orb';
    var canvasId = targetId + '-avatar-canvas';

    // Re-entrant-safe: if a previous boot ran but the canvas was removed from the
    // DOM (Reflex closes and reopens the voice overlay → destroys the old orb element),
    // clear the stale flag so we re-initialise into the fresh orb.
    if (window.__alexAvatarBootedTargets[targetId]) {
      if (document.getElementById(canvasId)) {
        log('already booted and canvas present for', targetId);
        return;
      }
      log('canvas missing — orb was re-created; re-initialising', targetId);
      window.__alexAvatarBootedTargets[targetId] = false;
    }

    window.__alexAvatarBootedTargets[targetId] = true;
    injectStyleOnce(targetId, canvasId);

    waitForOrb(targetId).then(function (orb) {
      // Guard: canvas might have been injected by a racing call.
      if (document.getElementById(canvasId)) return;
      var canvas = document.createElement('canvas');
      canvas.id = canvasId;
      orb.appendChild(canvas);

      loadThreeModules()
        .then(function (mods) { return initScene(mods, canvas, orb, targetId); })
        .catch(function (err) {
          warn('3D init failed, keeping orb fallback:', err && err.message);
          try { canvas.remove(); } catch (e) {}
          delete window.__alexAvatarBootedTargets[targetId];
        });
    }).catch(function (err) {
      warn('could not find #' + targetId + ':', err && err.message);
      delete window.__alexAvatarBootedTargets[targetId];
    });
  }

  // Watch the whole document for the orb element being (re-)added to the DOM.
  // Reflex's SPA navigation and show_voice_overlay toggling recreates #alex-orb
  // without reloading the page, so this observer ensures the avatar re-mounts.
  (function installPersistentObserver() {
    var obsTargetId = window.ALEX_AVATAR_TARGET_ID || 'alex-orb';
    var docObs = new MutationObserver(function () {
      var orb = document.getElementById(obsTargetId);
      if (!orb) return;
      var canvasId = obsTargetId + '-avatar-canvas';
      // Only act when the orb exists but canvas is absent (fresh mount).
      if (!document.getElementById(canvasId)) {
        log('persistent observer: orb re-appeared, triggering boot');
        boot(obsTargetId);
      }
    });
    docObs.observe(document.documentElement, { childList: true, subtree: true });
  })();

  function initScene(mods, canvas, orb, targetId) {
    targetId = targetId || 'alex-orb';
    var THREE = mods.THREE;
    var GLTFLoader = mods.GLTFLoader;
    var KTX2Loader = mods.KTX2Loader;
    var MeshoptDecoder = mods.MeshoptDecoder;
    var OrbitControls = mods.OrbitControls;

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
      bones: {},             // named bones: leftArm, rightArm, leftForeArm, rightForeArm, leftHand, rightHand, spine, spine1, spine2, neck
      rest: {},              // captured rest-pose rotations (Euler copies) per bone key
      morphMeshes: [],       // meshes with morphTargetDictionary
      jawOpenKeys: [],       // preferred morph target names per mesh for jaw
      viseme: {},            // mesh → index of best "aa/open" viseme
      currentState: 'idle',
      targetState: 'idle',
      prevState: 'idle',
      stateEnteredAt: 0,     // rig.t when the current target state began
      teachT: -1,            // >=0 while an "open-palms teaching" emphasis gesture is playing
      teachNext: 3.5,        // rig.t at which the next teaching gesture should auto-fire (while ai-speaking)
      loudness: 0,
      t: 0,
      restY: 0               // avatar.position.y after auto-centering; breathing anim adds on top
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

    // Load avatar — try local GLB first, then remote fallback if local is missing.
    var loader = new GLTFLoader();
    // facecap.glb uses KTX2 compressed textures and meshopt-compressed buffers; wire the decoders.
    try {
      if (KTX2Loader) {
        var ktx2 = new KTX2Loader()
          .setTranscoderPath(AVATAR_URL_BASE + 'basis/')
          .detectSupport(renderer);
        loader.setKTX2Loader(ktx2);
      }
      if (MeshoptDecoder) {
        loader.setMeshoptDecoder(MeshoptDecoder);
      }
    } catch (e) {
      warn('KTX2/Meshopt setup skipped:', e && e.message);
    }

    function loadWithFallback(urls, idx) {
      idx = idx || 0;
      if (idx >= urls.length) {
        warn('All GLB sources failed — keeping orb fallback.');
        try { canvas.remove(); } catch (e) {}
        return;
      }
      var url = urls[idx];
      log('loading GLB:', url);
      loader.load(url, onLoaded, undefined, function onErr(err) {
        warn('GLB load failed (' + url + '):', err && (err.message || err));
        loadWithFallback(urls, idx + 1);
      });
    }

    function onLoaded(gltf) {
      var avatar = gltf.scene;
      avatar.traverse(function (node) {
        if (node.isMesh) {
          node.castShadow = false;
          node.receiveShadow = false;
          node.frustumCulled = false;
          // ── Retint the shirt to solid black ─────────────────────────────
          // The RPM avatar ships with a dark-blue polo + printed "Alex" logo
          // baked into `Wolf3D_Outfit_Top`. Replace the albedo/roughness/
          // metalness texture maps with a plain black matte fabric so the
          // outfit matches the reference photo (black button-up). The mesh
          // geometry (polo silhouette + short sleeves) is fixed in the GLB
          // so the wearing style stays polo — but the color and the logo
          // removal match the target look.
          try {
            var mats = Array.isArray(node.material) ? node.material : [node.material];
            for (var mi = 0; mi < mats.length; mi++) {
              var mat = mats[mi];
              if (mat && mat.name === 'Wolf3D_Outfit_Top') {
                if (mat.map)          { mat.map.dispose();          mat.map = null; }
                if (mat.roughnessMap) { mat.roughnessMap.dispose(); mat.roughnessMap = null; }
                if (mat.metalnessMap) { mat.metalnessMap.dispose(); mat.metalnessMap = null; }
                if (mat.normalMap)    { mat.normalMap.dispose();    mat.normalMap = null; }
                if (mat.color && mat.color.set) mat.color.set(0x0b0b0d);
                mat.roughness = 0.55;
                mat.metalness = 0.02;
                mat.needsUpdate = true;
              }
            }
          } catch (e) { warn('shirt retint failed', e); }
          if (node.morphTargetDictionary && node.morphTargetInfluences) {
            rig.morphMeshes.push(node);
            // Pick best available jaw/open morph by priority.
            var dict = node.morphTargetDictionary;
            var priorities = [
              'jawOpen',        // ARKit (facecap + RPM ARKit)
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
          if (!rig.head && (nm === 'head' || nm === 'mixamorig:head')) {
            rig.head = node;
          }
          // RPM / Mixamo bone map — capture the upper body bones we need for posing
          // and gesture animation. Names vary (`LeftArm`, `mixamorig:LeftArm`, `arm_l`),
          // so we test suffixes.
          function pick(key, tests) {
            if (rig.bones[key]) return;
            for (var ti = 0; ti < tests.length; ti++) {
              if (nm === tests[ti] || nm.indexOf(tests[ti]) !== -1) {
                rig.bones[key] = node;
                return;
              }
            }
          }
          pick('leftShoulder',  ['leftshoulder']);
          pick('rightShoulder', ['rightshoulder']);
          pick('leftArm',       ['leftarm']);
          pick('rightArm',      ['rightarm']);
          pick('leftForeArm',   ['leftforearm']);
          pick('rightForeArm',  ['rightforearm']);
          pick('leftHand',      ['lefthand']);
          pick('rightHand',     ['righthand']);
          pick('neck',          ['neck']);
          pick('spine2',        ['spine2']);
          pick('spine1',        ['spine1']);
          pick('spine',         ['spine']);
          pick('hips',          ['hips']);
        }
      });

      rig.root = avatar;
      scene.add(avatar);

      // ── Apply natural rest pose (fix RPM's default T-pose) ──────────────
      // Verified empirically against the Wolf3D/RPM bind pose: the arm bone's
      // local +X axis rotates it from "straight out to the side" down toward
      // the body's side. +1.25 rad ≈ 72° of drop per arm puts hands alongside
      // the thighs; a tiny +Y splay keeps the arms from clipping the hips.
      (function applyRestPose() {
        function setRot(key, x, y, z) {
          var b = rig.bones[key];
          if (!b) return;
          b.rotation.set(x, y, z);
        }
        // Upper arms: the main "bring T-pose arms down" rotation.
        setRot('leftArm',       1.25,  0.10,  0.00);
        setRot('rightArm',      1.25, -0.10,  0.00);
        // Forearms: a subtle relaxed bend so hands sit just in front of the
        // thighs instead of locked flat.
        setRot('leftForeArm',   0.20, -0.10,  0.00);
        setRot('rightForeArm',  0.20,  0.10,  0.00);
        // Hands: neutral (the avatar's bind hand shape is already relaxed).
        setRot('leftHand',      0.00,  0.00,  0.00);
        setRot('rightHand',     0.00,  0.00,  0.00);

        // Record rest rotations so animations can modulate AROUND them rather
        // than overwriting (otherwise the arms snap back to T-pose).
        Object.keys(rig.bones).forEach(function (k) {
          var b = rig.bones[k];
          if (!b) return;
          rig.rest[k] = { x: b.rotation.x, y: b.rotation.y, z: b.rotation.z };
        });
        // Head + neck rest capture — CRITICAL. RPM avatars ship with a small
        // non-zero head bind rotation (chin-down a few degrees) and any
        // absolute overwrite on rig.head.rotation in the render loop would
        // snap the neck to a broken angle. Record the bind values here so
        // all head animation can be applied as a delta on top of them.
        if (rig.head) {
          rig.rest.head = {
            x: rig.head.rotation.x,
            y: rig.head.rotation.y,
            z: rig.head.rotation.z
          };
        }
      })();

      // Auto-frame: normalize the avatar to a known scale, then frame the face tightly.
      // Handles full-body rigs (RPM, lots of bones) and head-only scans (facecap, no bones).
      try {
        // Collect visible meshes, ignoring bones/skeletons/helpers. For skinned meshes the
        // geometry's local bbox is more trustworthy than setFromObject (which inflates for
        // bone extents).
        var meshes = [];
        var boneCount = 0;
        avatar.traverse(function (n) {
          if (n.isMesh && n.visible !== false) meshes.push(n);
          if (n.isBone || n.type === 'Bone') boneCount++;
        });

        avatar.updateWorldMatrix(true, true);
        function worldBBoxUnion(list) {
          var b = new THREE.Box3();
          list.forEach(function (m) {
            if (!m.geometry) return;
            if (!m.geometry.boundingBox) m.geometry.computeBoundingBox();
            var gbb = m.geometry.boundingBox && m.geometry.boundingBox.clone();
            if (!gbb) return;
            gbb.applyMatrix4(m.matrixWorld);
            b.union(gbb);
          });
          return b;
        }
        var fullBox = worldBBoxUnion(meshes);
        if (fullBox.isEmpty()) fullBox.setFromObject(avatar);
        var size = fullBox.getSize(new THREE.Vector3());
        var center = fullBox.getCenter(new THREE.Vector3());

        // Normalize: scale avatar so its largest axis is 1 unit, center at origin.
        var maxDim = Math.max(size.x, size.y, size.z) || 1;
        var scale = 1.0 / maxDim;
        avatar.scale.multiplyScalar(scale);
        avatar.position.x -= center.x * scale;
        avatar.position.y -= center.y * scale;
        avatar.position.z -= center.z * scale;
        avatar.updateWorldMatrix(true, true);

        // Full-body rigs have many bones (skeleton hierarchy). A T-pose full-body's arm
        // span can be wide (~1.0m) so aspectTall alone is unreliable — bone count is the
        // stronger signal. Head-only scans typically have 0–2 bones.
        var aspectTall = size.y / Math.max(size.x, size.z);
        var isFullBody = boneCount >= 20 || (boneCount > 5 && aspectTall > 1.5);

        // Re-measure the avatar AFTER normalization so framing is based on actual world
        // coordinates (not assumptions about where it landed — the RPM scene root may not
        // re-center exactly to origin depending on its internal transforms).
        var postBox = worldBBoxUnion(meshes);
        if (postBox.isEmpty()) postBox.setFromObject(avatar);
        var postSize = postBox.getSize(new THREE.Vector3());
        var postCenter = postBox.getCenter(new THREE.Vector3());

        // Find the face mesh (one with visemes) and compute its bbox post-normalization.
        var faceMesh = null;
        for (var fi = 0; fi < rig.morphMeshes.length; fi++) {
          if (rig.viseme[rig.morphMeshes[fi].uuid] != null) { faceMesh = rig.morphMeshes[fi]; break; }
        }
        if (!faceMesh && rig.morphMeshes.length) faceMesh = rig.morphMeshes[0];
        var faceBox = faceMesh ? worldBBoxUnion([faceMesh]) : postBox.clone();
        if (faceBox.isEmpty()) faceBox = postBox.clone();
        var faceCenter = faceBox.getCenter(new THREE.Vector3());
        var faceSize = faceBox.getSize(new THREE.Vector3());

        var headY, frameHeight;
        if (isFullBody) {
          // Full body framing: prefer to aim at the ACTUAL face mesh center so the
          // camera's gaze is horizontal with the eyes (no perspective foreshortening
          // that would make the character look like they're craning their neck).
          // faceCenter.y was measured above from the face mesh's world bbox.
          // Fallback: 82% up from the body's vertical span (upper chest/face line).
          var faceYBias = postBox.min.y + postSize.y * 0.82;
          headY = (faceCenter && isFinite(faceCenter.y))
            ? faceCenter.y
            : faceYBias;
          // Frame a touch taller than the full body so the shoulders sit in
          // the upper third and the legs fade into the wall below.
          frameHeight = postSize.y * 1.15;
        } else {
          // Head/face scan — frame the face with a bit of padding.
          headY = faceCenter.y;
          frameHeight = Math.max(faceSize.x * 1.35, faceSize.y * 1.15);
        }

        var fov = camera.fov * Math.PI / 180;
        var dist = (frameHeight / 2) / Math.tan(fov / 2) * 1.15;
        camera.position.set(0, headY, dist);
        camera.lookAt(0, headY, 0);
        camera.near = Math.max(0.001, dist * 0.02);
        camera.far = dist * 20;
        camera.updateProjectionMatrix();

        // Remember the post-normalization Y so the idle breathing anim can modulate
        // around it rather than overwriting the centering back to ~0.
        rig.restY = avatar.position.y;

        // Stash framing info on rig so OrbitControls can use the same focal point.
        rig.focus = new THREE.Vector3(0, headY, 0);
        rig.focusDist = dist;

        log('auto-framed — bones:', boneCount, 'aspectTall:', aspectTall.toFixed(2),
            'isFullBody:', isFullBody, 'headY:', headY.toFixed(3),
            'frameHeight:', frameHeight.toFixed(3), 'dist:', dist.toFixed(3));
      } catch (e) {
        warn('auto-frame failed, using defaults:', e && e.message);
      }

      // ── OrbitControls — let the user rotate the character ─────────────────
      // Constrained: no zoom/pan, limited yaw (±55°) and pitch (near horizontal).
      try {
        if (OrbitControls) {
          var controls = new OrbitControls(camera, canvas);
          controls.target.copy(rig.focus || new THREE.Vector3(0, 1.5, 0));
          controls.enableDamping = true;
          controls.dampingFactor = 0.08;
          controls.enableZoom = false;
          controls.enablePan = false;
          controls.rotateSpeed = 0.6;
          // Vertical limits: ~70°–100° polar (just above & below eye line)
          controls.minPolarAngle = Math.PI * 0.38;
          controls.maxPolarAngle = Math.PI * 0.56;
          // Horizontal limits: ±55° around the front
          controls.minAzimuthAngle = -Math.PI * 0.30;
          controls.maxAzimuthAngle =  Math.PI * 0.30;
          controls.update();
          rig.controls = controls;
          try { window.AlexAvatar.__controls = controls; } catch (e) {}
        }
      } catch (e) {
        warn('OrbitControls init failed:', e && e.message);
      }

      // Expose rig for debugging (window.AlexAvatar.__rig).
      try { window.AlexAvatar = window.AlexAvatar || {}; window.AlexAvatar.__rig = rig; window.AlexAvatar.__camera = camera; } catch (e) {}
      log('avatar loaded — morph meshes:', rig.morphMeshes.length, 'head bone:', !!rig.head,
          'arm bones:', !!(rig.bones.leftArm && rig.bones.rightArm));

      canvas.classList.add('alex-avatar-ready');
      orb.classList.add('alex-avatar-active');

      startObservers();
      startLoop();
    }

    var urls = [AVATAR_URL];
    if (AVATAR_URL_FALLBACK && AVATAR_URL_FALLBACK !== AVATAR_URL) urls.push(AVATAR_URL_FALLBACK);
    loadWithFallback(urls);

    function startObservers() {
      rig.currentState = (orb.className || 'idle').trim().split(/\s+/)[0] || 'idle';
      rig.targetState = rig.currentState;
      rig.prevState = rig.currentState;
      var obs = new MutationObserver(function () {
        var cls = (orb.className || '').trim().split(/\s+/);
        // Pick the first known state class.
        var known = ['idle', 'ai-speaking', 'user-speaking', 'thinking'];
        for (var i = 0; i < cls.length; i++) {
          if (known.indexOf(cls[i]) !== -1) {
            if (rig.targetState !== cls[i]) {
              rig.prevState = rig.targetState;
              rig.targetState = cls[i];
              rig.stateEnteredAt = rig.t;
              // Whenever we enter ai-speaking, push the first auto-teaching
              // gesture a few seconds out; also clear any stuck in-flight
              // teach timer.
              if (cls[i] === 'ai-speaking') {
                rig.teachT = -1;
                rig.teachNext = rig.t + 4.5;
              } else {
                // Leaving ai-speaking: cancel any pending/in-flight teach.
                rig.teachT = -1;
              }
            }
            return;
          }
        }
        rig.targetState = 'idle';
      });
      obs.observe(orb, { attributes: true, attributeFilter: ['class'] });
    }

    // ── Gesture helpers ───────────────────────────────────────────────────
    // Each gesture function returns a DELTA euler {x,y,z} that gets ADDED to the
    // rest rotation of the bone. Keeping them additive means transitions between
    // gestures just blend with gravity-like smoothing (lerp below).
    function zero() { return { x: 0, y: 0, z: 0 }; }

    // How the loop applies gestures: we compute target-state per-bone deltas,
    // then lerp the current applied delta toward them every frame. That gives
    // smooth hand-off between idle/speaking/waving without the arms popping.
    var applied = {
      leftArm:      zero(), leftForeArm:  zero(), leftHand:  zero(),
      rightArm:     zero(), rightForeArm: zero(), rightHand: zero(),
      spine:        zero(), spine1:       zero(), neck: zero()
    };
    function lerpApply(key, tx, ty, tz, k) {
      var a = applied[key];
      a.x += (tx - a.x) * k;
      a.y += (ty - a.y) * k;
      a.z += (tz - a.z) * k;
      var b = rig.bones[key];
      var r = rig.rest[key];
      if (b && r) b.rotation.set(r.x + a.x, r.y + a.y, r.z + a.z);
    }

    var clock = new THREE.Clock();
    function startLoop() {
      renderer.setAnimationLoop(function () {
        // If the canvas was removed from the DOM (Reflex closed the voice overlay),
        // stop the render loop and clear the boot flag so the next open re-inits cleanly.
        if (!canvas.isConnected) {
          renderer.setAnimationLoop(null);
          try { renderer.dispose(); } catch (e) {}
          delete window.__alexAvatarBootedTargets[targetId];
          log('canvas detached — render loop stopped, boot flag cleared');
          return;
        }

        var dt = Math.min(0.05, clock.getDelta());
        rig.t += dt;

        // Idle breathing: subtle vertical bob + head sway.
        if (rig.root) {
          var breath = Math.sin(rig.t * 1.6) * 0.006;
          rig.root.position.y = rig.restY + breath;
        }
        if (rig.head && rig.rest.head) {
          // Apply head animation ADDITIVELY around the captured rest rotation.
          // Overwriting .x/.y directly (as earlier revisions did) would discard
          // the avatar's bind-pose head tilt and produce a broken-neck look.
          var rh = rig.rest.head;
          var swayY = Math.sin(rig.t * 0.6) * 0.04;       // subtle left/right head shake
          var swayX = Math.sin(rig.t * 0.4 + 1.2) * 0.025; // very subtle up/down nod
          var headDX = swayX;
          var headDY = swayY;
          var headDZ = 0;

          if (rig.targetState === 'thinking') {
            headDY = Math.sin(rig.t * 1.5) * 0.12;
            headDX = -0.05 + Math.sin(rig.t * 2.3) * 0.04;
          } else if (rig.targetState === 'user-speaking') {
            // Listening: small attentive nod (slight chin-down + tiny oscillation).
            headDX = -0.02 + Math.sin(rig.t * 0.9) * 0.02;
            headDY = swayY * 0.5;
          } else if (rig.targetState === 'ai-speaking') {
            // Speaking: livelier movement, scaled with audio loudness.
            var l = rig.loudness;
            headDY = swayY + Math.sin(rig.t * 2.1) * 0.04 * l;
            headDX = swayX + Math.sin(rig.t * 2.8) * 0.03 * l;
          }
          rig.head.rotation.x = rh.x + headDX;
          rig.head.rotation.y = rh.y + headDY;
          rig.head.rotation.z = rh.z + headDZ;
        }

        // ── Arm + torso gestures ────────────────────────────────────────────
        // Compute target deltas per-bone for the current state.
        var t = rig.t;
        var tgt = {
          leftArm: zero(), leftForeArm: zero(), leftHand: zero(),
          rightArm: zero(), rightForeArm: zero(), rightHand: zero(),
          spine: zero(), spine1: zero(), neck: zero()
        };

        // Gesture deltas are ADDITIVE to the rest rotation. All per-state deltas
        // are intentionally TINY here — the RPM forearm/upper-arm bone axes are
        // non-obvious (large X deltas produce elbow-out "akimbo" poses instead
        // of natural forward arm swings), so we keep the arms at rest and let
        // the torso + head carry the expressive motion. This reads as a calm,
        // grounded presenter rather than a flailing cartoon.
        if (rig.targetState === 'thinking') {
          // Contemplative: head tilts + tiny neck adjustment, arms stay at rest.
          tgt.neck      = { x:  0.03, y:  0.05, z:  0.00 };
          tgt.spine     = { x:  0.00, y:  0.02, z:  0.00 };
          // Very subtle shoulder "hold" — barely perceptible, keeps arms still.
          tgt.leftArm   = { x:  0.00, y:  0.01, z:  0.00 };
          tgt.rightArm  = { x:  0.00, y: -0.01, z:  0.00 };
        } else if (rig.targetState === 'ai-speaking') {
          // Speaking: torso + shoulder sway plus a gentle forearm "teaching
          // gesture" — forearms breathe up and down subtly (small X delta),
          // scaled with loudness, to mimic a standing presenter emphasising
          // points with their hands. Magnitudes are tuned to stay BELOW the
          // akimbo threshold (empirically ~0.7 delta on forearm X = elbow-out
          // on this RPM rig; we stay at or under 0.30).
          var l = rig.loudness;
          var amp = 0.4 + 0.6 * l;                         // 0.4 silent → 1.0 peak
          var swayYaw  = Math.sin(t * 0.9) * 0.05 * amp;   // torso yaw
          var swayRoll = Math.sin(t * 1.4) * 0.02 * amp;   // shoulder rock
          tgt.spine    = { x: 0.00, y: swayYaw,         z: swayRoll };
          tgt.spine1   = { x: 0.00, y: swayYaw * 0.4,   z: swayRoll * 0.3 };
          // Shoulder counter-sway (Y = gentle inward/outward) — keeps arms alive.
          tgt.leftArm  = { x: 0.00, y:  0.03 * Math.sin(t * 1.1) * amp,       z: 0.00 };
          tgt.rightArm = { x: 0.00, y: -0.03 * Math.sin(t * 1.1 + 0.4) * amp, z: 0.00 };
          // "Hand talking" — forearm X breathes between rest and ~+0.25.
          // Both forearms move together in a gentle rise-and-fall; the wrists
          // end up hovering slightly forward, like a teacher framing an idea.
          // Bias the range to positive only so we never curl BEHIND rest.
          var handLift = (0.14 + 0.11 * Math.sin(t * 2.2)) * amp;     // 0.03 .. 0.25
          var handLiftR = (0.14 + 0.11 * Math.sin(t * 2.2 + 0.6)) * amp;
          tgt.leftForeArm  = { x: handLift,  y: 0.00, z: 0.00 };
          tgt.rightForeArm = { x: handLiftR, y: 0.00, z: 0.00 };

          // ── Open-palms "teaching" emphasis (fires occasionally) ─────────
          // Every 6–10 seconds while speaking, raise both arms outward with
          // slight elbow bend — the classic "here's the thing, look at this"
          // professor gesture (matches reference image 1: cartoon prof with
          // hands raised, palms up). Auto-scheduled via rig.teachNext so the
          // gesture comes and goes naturally without repeating mechanically.
          if (rig.teachT < 0 && t >= rig.teachNext) {
            rig.teachT = 0;
          }
          if (rig.teachT >= 0) {
            rig.teachT += dt;
            var tt = rig.teachT;
            var tenv;
            if      (tt < 0.45) tenv = tt / 0.45;                       // ease in
            else if (tt < 1.55) tenv = 1.0;                             // hold
            else if (tt < 2.05) tenv = 1.0 - (tt - 1.55) / 0.50;        // ease out
            else { tenv = 0; rig.teachT = -1; rig.teachNext = t + 6.0 + Math.random() * 4.0; }
            if (tenv > 0) {
              // Empirically probed "welcoming palms-up" professor pose.
              // Three bone rotations combine to avoid the akimbo/T-pose
              // failure modes and produce the image-1 reference look:
              //   1. Upper-arm X delta -0.80 → lift arms roughly to
              //      horizontal (rest=1.25 → 0.45 at full envelope).
              //   2. Upper-arm Z delta ±0.60 → swing the raised arms
              //      FORWARD out of the T-pose plane, so when the elbow
              //      bends the hand travels up/forward, not sideways
              //      into akimbo.
              //   3. Forearm X delta -1.30 → NEGATIVE-direction elbow
              //      bend (rest=0.20 → -1.10 at full envelope). This is
              //      the critical piece: bending the elbow the "other"
              //      way is what turns the palms upward and extends the
              //      hands outward in a welcoming "here's the thing"
              //      posture instead of folding them to the chest/hips.
              tgt.leftArm  = { x: -0.80 * tenv, y:  0.00, z:  0.60 * tenv };
              tgt.rightArm = { x: -0.80 * tenv, y:  0.00, z: -0.60 * tenv };
              tgt.leftForeArm  = { x: -1.30 * tenv, y: 0.00, z: 0.00 };
              tgt.rightForeArm = { x: -1.30 * tenv, y: 0.00, z: 0.00 };
            }
          }
        } else if (rig.targetState === 'user-speaking') {
          // Listening: small attentive spine sway + head nod handled above.
          tgt.spine = { x: 0.00, y: 0.02 * Math.sin(t * 0.6), z: 0.00 };
        } else {
          // Idle — the breath bob (on rig.root.position.y) does most of the
          // work. Arms get a barely-there Y drift so they don't look frozen.
          tgt.leftArm  = { x: 0.00, y:  0.015 * Math.sin(t * 0.55),       z: 0.00 };
          tgt.rightArm = { x: 0.00, y: -0.015 * Math.sin(t * 0.55 + 0.3), z: 0.00 };
        }

        // Smooth-apply every bone delta.
        var k = Math.min(1, dt * 6.0);        // ~6Hz follow rate
        Object.keys(tgt).forEach(function (key) {
          var v = tgt[key];
          lerpApply(key, v.x, v.y, v.z, k);
        });

        // Lip-sync: drive jaw morph from loudness, but only while speaking.
        // Subtle range — real humans barely open their jaw while talking. Cap ≈0.28 keeps
        // the mouth natural instead of cartoon-wide.
        var targetMouth = 0;
        if (rig.targetState === 'ai-speaking') {
          rig.loudness = rig.loudness * 0.55 + sampleLoudness() * 0.45;
          targetMouth = Math.min(0.28, rig.loudness * 0.38);
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

        if (rig.controls) {
          try { rig.controls.update(); } catch (e) {}
        }
        renderer.render(scene, camera);
      });
    }
  }

  window.AlexAvatarMount = boot;

  function bootDefaultAvatar() {
    boot(window.ALEX_AVATAR_TARGET_ID || 'alex-orb');
  }

  // Kick off when DOM is ready (handles both before/after DOMContentLoaded).
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootDefaultAvatar, { once: true });
  } else {
    bootDefaultAvatar();
  }

  // Expose a tiny debug API.
  window.AlexAvatar = window.AlexAvatar || {};
  window.AlexAvatar.version = '0.3.0';
  window.AlexAvatar.isBooted = function (targetId) {
    var key = targetId || window.ALEX_AVATAR_TARGET_ID || 'alex-orb';
    return !!(window.__alexAvatarBootedTargets && window.__alexAvatarBootedTargets[key]);
  };
  // No-op stubs kept so older call sites (AlexAvatar.wave(), .nod()) don't throw.
  window.AlexAvatar.wave = function () {};
  window.AlexAvatar.nod  = function () {};
})();
