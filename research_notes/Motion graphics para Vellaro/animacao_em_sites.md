# Motion design and animation on websites (2025–2026), applied to Vellaro Design

Research context: the notes target a dark, minimal one-page static site (Netlify, no build step) with a scroll-driven Three.js cabinet build (sketch to finished piece), an SVG logo drawn stroke by stroke, Lenis smooth scroll, crossfading fixed captions, and optional scroll-synced Web Audio narration. Research date: 31 Oct 2026.

**Method caveat:** In this session WebFetch could not reach webkit.org or developer.mozilla.org (network allowlist), so all findings come from web search results and snippets. Primary docs (WebKit blog, MDN compat tables, threejs.org release notes) could not be opened directly. Several findings below rest on secondary or third-party blogs, and are marked as such. Items drawn from background knowledge with no source found this session are placed under "Inferences" or "Gaps" and labeled.

## 1. Go-to techniques and libraries for scroll-driven and 3D motion (2025–2026), with browser support

### Takeaway
GSAP (ScrollTrigger, SplitText, DrawSVG, MorphSVG and the other formerly paid plugins) is now free to use, including commercially, after Webflow acquired it. That makes GSAP + Lenis + Three.js the default stack for a no-build static site. Native CSS scroll-driven animations reached Chrome/Edge 115 and Safari 26 (Sept 2025), but Firefox stable still had them behind a flag as of mid-2026, so they suit progressive enhancement of small UI motion, not the core 3D narrative. Same-document View Transitions are Baseline since Firefox 144 (Oct 2025). Cross-document (MPA) View Transitions work in Chromium and Safari 18.2+, and are an Interop 2026 target for Firefox.

### Cited Findings
**GSAP**
- After Webflow's support/acquisition, "all of the previously paid plugins in GSAP are now accessible to everyone". SplitText got a major overhaul with new options and a smaller bundle. — [Codrops: 5 Creative Demos Using Free GSAP Plugins](https://tympanus.net/codrops/?p=93244)
- Third-party summaries list ScrollTrigger, SplitText, Flip, MorphSVG and DrawSVG as free for commercial use, with no Club GSAP membership, license key or auth token required. These are secondary sources; the original announcement post was not retrieved. — [gsap-plugins skill page](https://skills.cat/skills/greensock/gsap-skills/gsap-plugins); [GSAP's Webflow page](https://gsap.com/resources/Webflow/) (official, confirms the whole plugin ecosystem is available)

**Native CSS scroll-driven animations (`animation-timeline`, `scroll()`, `view()`)**
- Chrome's documentation support table lists Chrome/Edge 115, Safari 26, and Firefox only in Technology Preview / behind a flag. It describes `scroll()` (an anonymous scroll-progress timeline) and view-progress timelines tied to an element's progress through the scrollport. — [Chrome for Developers: Scroll-driven animations](https://developer.chrome.com/docs/css-ui/scroll-driven-animations?hl=en)
- WebKit's "Features in Safari 26.0" post (via search snippet and aggregator) says Safari 26.0 supports `animation-timeline`, `animation-range`, `animation-range-start` and `animation-range-end`, which were added after the WWDC25 beta. A secondary Japanese summary says WKWebView did not yet support scroll-driven animations at that time (bug filed). This matters for in-app browsers (Instagram, WhatsApp links) on iOS. — [WebKit features in Safari 26.0 (via scour.ing)](https://scour.ing/p/https://webkit.org/blog/17333/webkit-features-in-safari-26-0); [techfeed summary](https://techfeed.io/entries/68c88678d0e17253abf951b2)
- **Firefox status: sources conflict.** One blog claims Firefox shipped in v133 (Nov 2024). A more specific source says that as of Firefox 152 (June 2026) the feature is still behind `layout.css.scroll-driven-animations.enabled` in stable (on by default in Nightly), and is an Interop 2026 priority. The flagged status agrees with Chrome's table and the Mozilla Connect thread, so treat Firefox as unsupported in stable. — [Coder Cops (claims shipped)](https://blog.codercops.com/blog/css-view-transitions-scroll-animations-2026); contradicted by [Build MVP Fast (still flagged at Fx 152)](https://www.buildmvpfast.com/blog/css-scroll-driven-animations-replace-js-2026) and [Mozilla Connect thread](https://connect.mozilla.org/t5/ideas/implement-css-scroll-driven-animations-animation-timeline/idc-p/119840)

**View Transitions API**
- Same-document view transitions became **Baseline Newly available on 16 Oct 2025** with Firefox 144. This covers `document.startViewTransition()`, `view-transition-name`, `view-transition-class`, `view-transition-name: match-element` and `:active-view-transition`, and was part of the Interop 2025 focus area. — [web.dev: Same-document view transitions are now Baseline Newly available](https://web.dev/blog/same-document-view-transitions-are-now-baseline-newly-available)
- Cross-document view transitions (`@view-transition { navigation: auto }`, no JS) are documented by Chrome for MPAs. A Chrome docs snapshot lists Safari 18.2 as the first Safari version and Firefox as unsupported. Mozilla/Jake Archibald state they are part of Interop 2026, which makes Firefox a 2026 target, not a shipped feature. — [Chrome for Developers: Cross-document view transitions](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document?authuser=0); [Simon Willison on Jake Archibald's Mozilla Hacks post](https://simonwillison.net/b/9293)

**Lenis**
- Lenis wraps the browser's native scroll, so `position: sticky`, anchor links and accessibility features keep working. It has a `respectReducedMotion` option (default true): when on, smoothing is disabled and programmatic scrolls are instant. It exposes a `prefersReducedMotion` getter. Known limitation: smoothing stops over iframes, because iframes don't forward wheel events. — [Lenis README (GitHub)](https://github.com/darkroomengineering/lenis/blob/main/README.md)
- Built-in reduced-motion handling arrived in Lenis **1.3.26**. For older versions, check `matchMedia('(prefers-reduced-motion: reduce)')` and don't instantiate Lenis. — [Motion docs: Lenis](https://motion.dev/docs/lenis)

**Three.js / WebGPU**
- Third-party sources say `WebGPURenderer` falls back automatically to WebGL 2, and that `forceWebGL: true` lets you test the fallback. They disagree on maturity: one calls it still "experimental" (v0.170), another says it has been the recommended renderer since r171 (Sept 2025). They advise a WebGL2 fallback for the ~5–10% tail (Linux Firefox, older iPhones) and testing in iOS/Android in-app webviews. — [Build MVP Fast: Three.js WebGL→WebGPU migration](https://www.buildmvpfast.com/blog/threejs-webgl-to-webgpu-renderer-migration-2026); [Utsubo: WebGPU + Three.js Migration Guide 2026](https://www.utsubo.com/blog/webgpu-threejs-migration-guide)
- Safari 26 is reported (via secondary summary) to officially support WebGPU, including WGSL and compute shaders. — [techfeed summary of WebKit Safari 26.0 post](https://techfeed.io/entries/68c88678d0e17253abf951b2)

### Inferences
- **Recommended stack for Vellaro (no build step):** load GSAP core + ScrollTrigger (+ SplitText, DrawSVG if useful) from a pinned CDN version (cdnjs / jsDelivr) or self-host in `/vendor`. Drive the Three.js build timeline with one ScrollTrigger `scrub` timeline (`gsap.ticker` driving `lenis.raf`) instead of hand-rolled scroll math. This is the documented Lenis + GSAP integration pattern, which centralizes the cabinet stages, caption crossfades and narration cue points on one timeline.
- **The SVG logo stroke-draw** can stay as CSS `stroke-dashoffset` or move to GSAP DrawSVG (now free). The value is easier sequencing and a reduced-motion branch, not visual difference.
- **Native CSS scroll-driven animations** fit small, decorative, non-critical effects (a progress hairline, caption reveal, image clip reveals) wrapped in `@supports (animation-timeline: scroll())`. Firefox stable and iOS in-app webviews then simply get static content. Don't put the cabinet build on them: it lives in WebGL anyway.
- **WebGPU is not worth migrating to** for a single cabinet model. WebGLRenderer is universal and the scene is not compute-bound. Revisit only if adding heavy material/finish shaders.
- **Libraries not verified this session (background knowledge, unsourced):** React Three Fiber requires a React/JSX build, so it's a poor fit for no-build. Spline exports are convenient but ship a heavy runtime and less control over loading. Rive is strong for small interactive vector state machines (e.g., an animated icon or configurator toggle) via a CDN runtime. Lottie suits After Effects–authored vector loops. Theatre.js is a keyframe editor for Three.js camera/object choreography, but its development pace in 2025–26 should be checked before adopting.

### Gaps
- Could not open MDN or caniuse to confirm exact current versions for `animation-timeline`, cross-document view transitions in Firefox, or `view-transition-name: auto` in Safari 26 (webkit.org and MDN were blocked in this session).
- Original Webflow/GSAP "GSAP is free" announcement (date, exact license terms) not retrieved; only secondary confirmation plus GSAP's Webflow page.
- No sourced 2025–26 status found for Spline, Rive, Lottie or Theatre.js (pricing, runtime size, maintenance).
- Three.js official release notes on WebGPURenderer status not retrieved; third-party claims conflict.

## 2. Performance on mobile: WebGL/3D on phones, Core Web Vitals, INP, lazy loading, fallbacks

### Takeaway
The consistent rules of thumb are: cap devicePixelRatio (about 1.5 on mobile, at most 2 on desktop), keep draw calls low (under about 50 on mobile), turn off shadows, MSAA and heavy post-processing on phones, dispose of GPU resources, and pause rendering when hidden or off-screen. Treat these numbers as heuristics: official Three.js guidance wasn't retrieved, and the sources are community guides.

### Cited Findings
- Draw-call budget: under 100 per frame generally, with InstancedMesh for repeated objects. — [three best practices (skills.cat)](https://skills.cat/skills/emalorenzo/three-agent-skills/three-best-practices)
- A stricter target of under 50 draw calls on mobile vs under 200 on desktop. Cap DPR to 1 on low-end devices; code patterns use `Math.min(window.devicePixelRatio, 1.5)` on mobile and a cap of 2 on desktop. — [mobile optimization skill (openskillindex)](https://openskillindex.com/skills/majiayu000-claude-skill-registry-dev-performance-mobile-optimization); [performance basics (smithery)](https://smithery.ai/skills/feliperyba/dev-performance-performance-basics)
- Turn off shadows, antialiasing and heavy post-processing on phones. Avoid allocating objects in the render loop; `dispose()` geometries, materials and textures; use frustum culling; pause or reduce work when the tab is hidden. Target at least 30 fps on mobile and 60 fps on desktop. — [threejs-graphics-optimizer (skillselion)](https://skillselion.com/skills/ovachiever/droid-tings/threejs-graphics-optimizer); [performance basics (smithery)](https://smithery.ai/skills/feliperyba/dev-performance-performance-basics)
- Test the WebGL fallback in iOS/Android in-app webviews (Instagram, X), because desktop results don't predict them. — [Build MVP Fast](https://www.buildmvpfast.com/blog/threejs-webgl-to-webgpu-renderer-migration-2026)
- Lenis keeps scroll on the main thread even with reduced motion. Any heavy main-thread work (per-frame JS, raycasting, layout reads) therefore competes with scroll and input. — [Lenis README](https://github.com/darkroomengineering/lenis/blob/main/README.md)

### Inferences
- **Concrete budget for the cabinet scene:**
  - Renderer: `renderer.setPixelRatio(Math.min(devicePixelRatio, isMobile ? 1.5 : 2))`.
  - Geometry: merge static cabinet parts per material. Aim for one model of fewer than 30 draw calls.
  - Textures: KTX2/Basis textures at 1K on mobile and 2K max on desktop.
  - Lighting: bake ambient occlusion or lighting into textures or a small HDRI instead of real-time shadows.
  - Loading: compress glTF with Draco or Meshopt. The decoders load from CDN without a build step.
- **Render on demand, not continuously.** With a scrubbed timeline, render only when scroll progress or the camera changes. Stop the loop via IntersectionObserver when the canvas is out of view, and on `visibilitychange`. This saves battery and reduces jank on phones.
- **Core Web Vitals (background knowledge, not sourced this session):**
  - LCP: a WebGL canvas usually isn't the LCP element. The LCP will be the hero text or poster image, so ship a static poster (a rendered PNG/AVIF of the sketch frame) as real HTML and fade the canvas in over it once ready.
  - CLS: reserve the canvas box so it doesn't shift layout.
  - INP: keep `pointermove`/scroll handlers light and defer the Three.js and audio bundle (`type="module"`, dynamic `import()` after first paint or on idle).
  - Audio: never decode narration audio before the user opts in.
- **Fallback ladder:**
  1. Full WebGL.
  2. Low tier (DPR 1, no post-processing, fewer frames) when the device is detected as weak (`navigator.hardwareConcurrency`, `deviceMemory`, or measured frame time over the first second).
  3. Image-sequence or static stages (pre-rendered sketch → frame → finished cabinet) for no-WebGL, reduced motion, or Save-Data.

### Gaps
- No official threejs.org or web.dev numbers retrieved on DPR caps, draw calls or texture budgets; all figures are community heuristics.
- No sourced data found on how WebGL hero scenes affect field CWV (CrUX) or INP specifically.
- Texture memory budgets for iOS Safari (per-tab GPU memory limits) not found.

## 3. Accessibility: prefers-reduced-motion, vestibular safety, scroll-jacking, WCAG 2.2 and autoplay audio

### Takeaway
Honor `prefers-reduced-motion` both in CSS (WCAG technique C39) and JS (SCR40). Lenis already does this by default from v1.3.26. Never autoplay the narration; keep it opt-in with an always-visible pause/mute control (SC 1.4.2). Also offer an on-page motion toggle, because the OS setting isn't enough on its own.

### Cited Findings
- **SC 2.3.3 Animation from Interactions (Level AAA, added in WCAG 2.1, retained in 2.2):** motion animation triggered by interaction can be disabled unless essential. People with vestibular disorders need control over interaction-triggered movement. Sufficient techniques: CSS `prefers-reduced-motion` (C39) and checking it in JavaScript to prevent motion (SCR40). — [W3C Understanding SC 2.3.3](https://w3c.github.io/wcag/understanding/animation-from-interactions.html); [W3C WCAG 2.1 Understanding 2.3.3](https://w3.org/WAI/WCAG21/Understanding/animation-from-interactions)
- The exception covers animation "essential to the functionality or the information being conveyed". — [TestParty WCAG animation guide](https://testparty.ai/blog/wcag-animation-interactions-guide)
- Guidance varies on whether reduced motion means "no motion" or "gentler motion". Subtle fades and opacity changes are usually acceptable under reduced motion. — [Passiro: animation & motion](https://passiro.com/web-accessibility/designers/animation-motion); [a11y-motion-animation (openskillindex)](https://openskillindex.com/skills/intense-visions-harness-engineering-a11y-motion-animation-2a3d1d)
- Provide an easy on-page way to turn off or reduce interaction-triggered animation when system preferences aren't available. — [Silktide](https://silktide.com/?p=39935)
- **SC 2.2.2 Pause, Stop, Hide (Level A):** Hidde de Vries discusses whether `prefers-reduced-motion` alone can satisfy it, and on 1.4.2 asks whether browsers' global mute counts as the mechanism. The question is left open, so the safe reading is to provide your own control. — [hidde.blog: Meeting 2.2.2 with prefers-reduced-motion](https://hidde.blog/meeting-2-22-pause-stop-hide-with-prefers-reduced-motion/)
- **SC 1.4.2 Audio Control** sits under "Distinguishable" in the WCAG 2.2 map. — [Intopia WCAG 2.2 map (PDF)](https://intopia.digital/wp-content/uploads/2023/10/Intopia-WCAG-2.2-Map-Portrait-Mode.pdf)
- Lenis disables smoothing under reduced motion and preserves native scroll semantics: sticky positioning, anchors and assistive-tech behavior. — [Lenis README](https://github.com/darkroomengineering/lenis/blob/main/README.md)

### Inferences
- **Reduced-motion branch for Vellaro:**
  - Lenis is off (automatic in 1.3.26+; verify the site's pinned version).
  - The cabinet doesn't fly or rotate. Show discrete stages that crossfade (sketch → structure → finished), still keyed to scroll, so the story survives without camera motion. That treats the narrative as the "information conveyed", while large camera moves aren't essential.
  - The logo appears without the stroke draw, or with a quick fade.
  - Captions use opacity only.
- **Narration:**
  - Must be strictly opt-in, started by a user gesture (browsers' autoplay policies also require this for Web Audio).
  - Needs a persistent, keyboard-focusable pause/mute button with `aria-pressed`.
  - The captions already double as a transcript. Make sure the caption text matches the narration, so deaf and muted users get the same content.
- **Avoid true scroll-jacking:**
  - Keep the scroll distance proportional and never block or snap the user's scroll.
  - Make sure keyboard (Space, PgDn, arrow keys) and screen-reader navigation reach every caption. Fixed, crossfading captions should be real DOM text, not canvas text, with only the active one exposed (others `aria-hidden` or `visibility: hidden`).
- Add a small "Motion: on/off" toggle stored in localStorage that forces the reduced-motion branch. This covers users who don't know about the OS setting (Silktide's recommendation).
- **Vestibular triggers to avoid (background knowledge, unsourced this session):** large-scale zooms, parallax with strong depth differentials, spinning, and camera motion decoupled from scroll direction. A slow, scroll-locked camera orbit of under about 30° per viewport is lower risk.

### Gaps
- The WCAG 2.2 Understanding pages for 1.4.2 Audio Control and 2.2.2 Pause, Stop, Hide were not opened. The 1.4.2 rule (audio playing automatically for more than 3 seconds needs pause/stop or independent volume control) is from background knowledge and should be verified at w3.org/WAI/WCAG22/Understanding/audio-control.
- No authoritative source found on scroll-jacking specifically (e.g., NN/g research); not retrieved this session.

## 4. Award-winning reference sites (furniture, interior, architecture, luxury), 2024–2026

### Takeaway
Awwwards' architecture and luxury categories have a steady stream of 2026 Sites of the Day (e.g., Belgrade Arbor, LPAS, Illoca, Studio X), but no furniture-brand SOTD for 2025–26 turned up in search. The best furniture precedents found are older: Moooi (Build in Amsterdam, SOTD 2020–22) and Kvell (Locomotive, SOTD 2017). Motion details per site could not be verified because the pages couldn't be opened.

### Cited Findings
- **2026 Awwwards SOTD in architecture** (from the architecture category listing):
  - Belgrade Arbor (Square43 Studio, 17 Oct 2026)
  - LPAS (Studio Naam, 10 Oct 2026)
  - Sobha Privy Collection (Vide Infra, 23 Sep 2026)
  - Illoca (Unseen Studio, 4 Sep 2026)
  - Kononenko Architectural Bureau (23 Aug 2026)
  - AIR (Vide Infra, 27 May 2026)

  Some listing metadata is inconsistent; verify on the site. — [Awwwards: Best Architectural Design Websites](https://www.awwwards.com/websites/architecture/)
- **Studio X**, a commercial interior design studio (Hong Kong/Singapore), was SOTD on 17 Apr 2026. — [Awwwards: Studio X SOTD](https://www.awwwards.com/sites/studio-x)
- **Elite Interior Design** has an Awwwards SOTD page (date not shown in snippet). — [Awwwards: Elite Interior Design](https://www.awwwards.com/sites/elite-interior-design)
- The Awwwards luxury category is a curated browsing list for luxury brands. — [Awwwards: Best Luxury websites](https://www.awwwards.com/websites/luxury/)
- **Moooi** (furniture/design brand) has Site of the Day wins by Build in Amsterdam, dated 2020–2022. — [Awwwards: Build in Amsterdam favorites](https://www.awwwards.com/buildinamsterdam/collections/build-in-amsterdam-personal-favorites/); [Moooi "Beauty Blooms" inspiration](https://www.awwwards.com/inspiration/thumbnail-moooi-beauty-blooms)
- **Kvell** (Scandinavian furniture brand) won Awwwards SOTD per Locomotive's case study (circa 2017). — [Locomotive: Kvell case study](https://2022.locomotive.ca/en/work/kvell)
- Furniture element showcases on Awwwards: Henge (design furniture), Besen furniture company, and Format Furniture (fullscreen footer). — [Henge](https://www.awwwards.com/inspiration/henge-design-furniture); [Besen](https://www.awwwards.com/inspiration/about-besen-furniture-company); [Format Furniture footer](https://www.awwwards.com/inspiration/fullscreen-footer-8)
- **Relevant Codrops technique write-ups (2025–26):**
  - ToyFight's INK Games site: layered 3D, scroll-driven animation and a single shared WebGL canvas (Nov 2025). — [Codrops Nov 2025 archive](https://tympanus.net/codrops/2025/11/)
  - "WebGL Scroll Sync" demo (Apr 2025). — [Codrops: Edan Kwan hub](https://tympanus.net/codrops/hub/author/edan_kwan)
  - Building Aether 1: a product site centered on sound (Aug 2025). — [Codrops: Building Aether 1](https://tympanus.net/codrops/2025/08/06/building-aether-1-sound-without-boundaries/)

### Inferences
- **Common traits** of architecture/interior SOTDs and luxury product sites (inferred from category patterns, not verified per site): restraint, large type, slow eased image reveals (clip-path/mask), a single persistent WebGL canvas behind DOM content, and audio as an opt-in layer. Vellaro's concept (sketch → built piece, narrated) is closer to the product-storytelling of the Aether 1 case study than to typical furniture e-commerce sites, which is a differentiator.
- **"Single shared WebGL canvas"** (ToyFight/INK Games) is the pattern Vellaro already uses. Keep one renderer and swap scenes or stages, rather than creating multiple canvases.

### Gaps
- No 2025–2026 Awwwards/FWA/CSSDA winner that is specifically a **furniture brand** was found. FWA and CSS Design Awards were not searched for lack of tool budget.
- Per-site motion analysis (what each winner does on scroll, durations, easing) could not be verified because the pages couldn't be fetched. Look at Belgrade Arbor, Illoca (Unseen Studio), LPAS and Studio X directly before citing their techniques.
- No Brazilian luxury furniture site references found (e.g., Etel, Jader Almeida, Sergio Rodrigues heritage brands); not searched.

## 5. Ideas to evolve the Vellaro site: worth it vs. gimmicky

### Takeaway
The highest-value additions extend the existing "craft made visible" narrative:
- an exploded-view / joinery stage in the same scroll timeline;
- a light wood/finish swatch switcher on the finished cabinet;
- a cross-document View Transition into case-study pages if the site grows past one page;
- a reduced-motion/narration control bar.

Custom cursors, heavy sound beds and full configurators are mostly cost without payoff for a small team and a bespoke (not catalog) business.

### Cited Findings
- GSAP's now-free Flip, MorphSVG, DrawSVG and SplitText enable these effects without licensing cost. — [Codrops: free GSAP plugins demos](https://tympanus.net/codrops/?p=93244)
- Same-document View Transitions (Baseline Oct 2025) can animate in-page state changes, e.g., swapping a finish swatch or opening a detail panel, with `startViewTransition()` and `view-transition-name`. — [web.dev](https://web.dev/blog/same-document-view-transitions-are-now-baseline-newly-available)
- Cross-document View Transitions need no JS and fit static multi-page sites (Chromium, Safari 18.2+; Firefox is an Interop 2026 target), so they degrade to normal navigation elsewhere. — [Chrome for Developers: cross-document](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document?authuser=0); [Simon Willison / Mozilla Hacks](https://simonwillison.net/b/9293)
- Sound-led product storytelling is a recognized 2025 award-winning pattern. — [Codrops: Building Aether 1](https://tympanus.net/codrops/2025/08/06/building-aether-1-sound-without-boundaries/)
- Mobile budgets: fewer than about 50 draw calls, DPR cap, no shadows or post-processing on phones. These constrain how rich a configurator can be on mobile. — [openskillindex mobile optimization](https://openskillindex.com/skills/majiayu000-claude-skill-registry-dev-performance-mobile-optimization)

### Inferences
**Worth it (fits the brand, small-team feasible, no build step)**
1. **Exploded view / joinery stage.** Between "structure" and "finished", let the cabinet separate along its axes for a few hundred pixels of scroll. Show dovetails, hinges and the inner finish, with a caption naming the joinery and the wood species.
   - It's the strongest proof of bespoke craft, and it's cheap: the same glTF nodes animated along local offsets on the existing GSAP timeline.
   - Reduced-motion variant: a static exploded still image.
2. **Finish/material switcher (light configurator).** Offer 3–5 swatches (e.g., freijó, imbuia, cumaru, lacquer black, brass hardware) on the finished cabinet.
   - Implementation: swap `material.map`/`roughnessMap` from preloaded KTX2 textures, with a short crossfade (shader lerp or GSAP on a uniform) and `aria-pressed` buttons.
   - Don't build a full parametric configurator (dimensions, pricing). For a bespoke workshop, the CTA should be "talk to the workshop", and a full configurator implies a catalog and pricing that bespoke work doesn't have.
3. **Scroll progress and chapter markers.** A thin hairline plus chapter labels (Sketch · Structure · Joinery · Finish · Atelier), built with CSS `animation-timeline: scroll()` inside `@supports`, with a GSAP fallback. This helps orientation in a long scroll story and mitigates the scroll-jacking feel.
4. **Motion & sound control bar.** A fixed, minimal control: "Narration ▶/❚❚" and "Motion on/off". It doubles as WCAG 1.4.2 / 2.2.2 / 2.3.3 hygiene.
5. **Text reveals with the now-free SplitText**, applied sparingly: line or word mask reveals on section titles only, with opacity-only under reduced motion. Avoid per-character effects on body copy (readability and screen-reader issues).
6. **Cross-document View Transitions** if case-study or project pages are added later. A single CSS rule gives a crossfade or shared-element morph of the hero image between static pages, with no SPA router or build needed. Firefox and older Safari users get normal navigation.

**Maybe (only with clear restraint)**
- **Ambient sound bed / foley** (chisel, plane, wood knock) tied to build stages under the narration. It's atmospheric for a workshop brand, but must be opt-in, low volume and pausable. It also adds file weight and mixing work; decide only after measuring how many users enable narration.
- **Subtle pointer parallax** on the finished cabinet (a few degrees of tilt following the cursor on desktop only, disabled on touch and under reduced motion). Fine as a quiet touch; skip it on mobile.

**Gimmicky / not worth it for Vellaro**
- **Custom cursors** (blob/magnetic followers): they add a per-frame main-thread loop and can hurt INP. They're meaningless on touch, which is likely most traffic for a Brazilian consumer audience, and clash with a minimal luxury tone.
- **Heavy post-processing** (bloom, chromatic aberration, film grain via EffectComposer): expensive on phones and stylistically off-brand for natural wood.
- **Spline / R3F rewrites:** these mean a runtime or build pipeline the team doesn't need. The existing vanilla Three.js + GSAP setup is the right altitude.
- **Preloader-gated experiences** (full-screen % loaders before any content): they hurt LCP and bounce. Show the static poster and copy immediately and progressively enhance into 3D.
- **WebGPU migration:** no visible benefit for one cabinet model.

### Gaps
- No sourced UX data on whether configurators or exploded views improve lead conversion for bespoke furniture; recommendations are judgment-based.
- No measurement of current Vellaro bundle size or field Core Web Vitals available to prioritize these changes; run Lighthouse/PageSpeed Insights on the Netlify URL before deciding.
- Rive/Lottie use cases (e.g., animated swatch icons) not evaluated against sources this session.
