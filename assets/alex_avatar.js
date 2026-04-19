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
    if (window.__alexAvatarBootedTargets[targetId]) {
      log('already booted for target', targetId);
      return;
    }
    window.__alexAvatarBootedTargets[targetId] = true;
    var canvasId = targetId + '-avatar-canvas';
    injectStyleOnce(targetId, canvasId);

    waitForOrb(targetId).then(function (orb) {
      if (document.getElementById(canvasId)) return;
      var canvas = document.createElement('canvas');
      canvas.id = canvasId;
      orb.appendChild(canvas);

      loadThreeModules()
        .then(function (mods) { return initScene(mods, canvas, orb); })
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

  function initScene(mods, canvas, orb) {
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
      greetT: -1,            // >=0 while a "hi" wave is playing
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
          // Full body framing: show the whole character with tiny padding.
          // Bias camera aim slightly up from body center so the face lands in the
          // upper third of the canvas (shoulders visible); the character's lower
          // legs run off the bottom of the frame / fade into the transcript wall.
          headY = postCenter.y + postSize.y * 0.10;
          frameHeight = postSize.y * 1.05;
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

      // Trigger a welcome wave once the avatar is on-screen.
      rig.greetT = 0;

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
              // Wave when we transition INTO ai-speaking from idle (likely greeting/opening line).
              if (cls[i] === 'ai-speaking' && rig.prevState === 'idle') {
                rig.greetT = 0;
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
      spine:        zero(), neck:         zero()
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
        var dt = Math.min(0.05, clock.getDelta());
        rig.t += dt;

        // Idle breathing: subtle vertical bob + head sway.
        if (rig.root) {
          var breath = Math.sin(rig.t * 1.6) * 0.006;
          rig.root.position.y = rig.restY + breath;
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

        // ── Arm + torso gestures ────────────────────────────────────────────
        // Compute target deltas per-bone for the current state.
        var t = rig.t;
        var tgt = {
          leftArm: zero(), leftForeArm: zero(), leftHand: zero(),
          rightArm: zero(), rightForeArm: zero(), rightHand: zero(),
          spine: zero(), neck: zero()
        };

        // Gesture deltas are ADDITIVE to the rest rotation, so small values keep
        // motion subtle. With rest.leftArm.x = +1.25 (arm hanging down), negative
        // X delta lifts the arm forward; positive Y splays outward.
        if (rig.targetState === 'thinking') {
          // Quiet head-tilt + a faint hand-up, as if mulling something over.
          tgt.rightArm      = { x: -0.35, y:  0.15, z:  0.10 };
          tgt.rightForeArm  = { x:  0.80, y:  0.25, z:  0.00 };
          tgt.rightHand     = { x:  0.15, y:  0.00, z:  0.00 };
          tgt.neck          = { x:  0.04, y:  0.06, z:  0.00 };
        } else if (rig.targetState === 'ai-speaking') {
          // Teaching gestures: both arms gesture forward (negative X delta lifts
          // them toward horizontal) with alternating side-to-side splay (Y).
          // Scale with loudness so louder speech = bigger hand-talking.
          var l = rig.loudness;
          var amp = 0.35 + 0.65 * l;
          var s1 = Math.sin(t * 1.8);
          var s2 = Math.sin(t * 1.3 + 1.0);
          var s3 = Math.sin(t * 2.1 + 0.6);
          // Upper arms: lift 20–60° forward from rest, alternate left/right.
          tgt.leftArm   = { x: -0.20 - 0.30 * amp * (0.6 + 0.4 * s1),
                            y:  0.10 * s2 * amp, z:  0.00 };
          tgt.rightArm  = { x: -0.20 - 0.30 * amp * (0.6 + 0.4 * s2),
                            y: -0.10 * s1 * amp, z:  0.00 };
          // Forearms: open outward when speaking emphatically.
          tgt.leftForeArm  = { x:  0.40 + 0.40 * amp, y:  0.30 * s3 * amp, z:  0.00 };
          tgt.rightForeArm = { x:  0.40 + 0.40 * amp, y: -0.30 * s1 * amp, z:  0.00 };
          tgt.leftHand  = { x:  0.05 * s2, y:  0.05 * s3, z:  0.00 };
          tgt.rightHand = { x:  0.05 * s3, y: -0.05 * s2, z:  0.00 };
          tgt.spine     = { x:  0.00, y:  0.05 * Math.sin(t * 0.7), z: 0.00 };
        } else if (rig.targetState === 'user-speaking') {
          // Attentive listening — very small sway, arms stay at rest.
          tgt.spine = { x: 0.00, y: 0.03 * Math.sin(t * 0.6), z: 0.00 };
        } else {
          // Idle — arms drift with breath, tiny side-to-side sway only.
          tgt.leftArm  = { x:  0.00, y:  0.02 * Math.sin(t * 0.6),       z: 0.00 };
          tgt.rightArm = { x:  0.00, y: -0.02 * Math.sin(t * 0.6 + 0.3), z: 0.00 };
        }

        // Wave gesture: plays for ~2.2s from rig.greetT=0. Right hand raises
        // up and out, forearm waves left-right. Overrides the right-side gesture
        // targets while active.
        if (rig.greetT >= 0) {
          rig.greetT += dt;
          var wd = rig.greetT;
          var env;
          if (wd < 0.45)       env = wd / 0.45;
          else if (wd < 1.80)  env = 1.0;
          else if (wd < 2.25)  env = 1.0 - (wd - 1.80) / 0.45;
          else { env = 0; rig.greetT = -1; }
          if (env > 0) {
            // Raise the right upper arm up and outward:
            //   -1.05 X delta brings arm from rest (hanging, x=+1.25) up to ~+0.20
            //   +0.40 Y splays it outward from the torso
            tgt.rightArm = {
              x: -1.05 * env,
              y:  0.40 * env,
              z:  0.00
            };
            // Forearm bent up so hand is overhead, oscillating for the wave.
            tgt.rightForeArm = {
              x:  0.80 * env,
              y:  0.15 * env + 0.55 * Math.sin(wd * 10.0) * env,
              z:  0.00
            };
            tgt.rightHand = {
              x: 0.00,
              y: 0.35 * Math.sin(wd * 10.0) * env,
              z: 0.00
            };
            if (rig.head) {
              rig.head.rotation.z = (rig.head.rotation.z || 0) + 0.08 * env;
            }
          }
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
  // Manual wave trigger — useful for testing + welcome moments.
  window.AlexAvatar.wave = function () {
    try { if (window.AlexAvatar.__rig) window.AlexAvatar.__rig.greetT = 0; } catch (e) {}
  };
})();
