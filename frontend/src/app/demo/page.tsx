"use client";

import { useEffect, useRef, useState } from "react";

import {
  GuideWorkflowError,
  runQuietPresenceDemo,
  type GuideDemoResult,
} from "./guide-client";
import styles from "./page.module.css";

const defaultKnowledge = `# Northwind Release 2.4.0

Release 2.4.0 targets production on August 5, 2026.
The change request is approved, the build succeeded, and automated tests passed.
Security review is still in progress.
Deployment remains blocked until every required approval is complete.`;

const releaseSteps = [
  { name: "Change request", owner: "Alex Morgan", status: "Approved", tone: "success" },
  { name: "Build", owner: "CI System", status: "Succeeded", tone: "success" },
  { name: "Automated tests", owner: "CI System", status: "Passed", tone: "success" },
  { name: "Security review", owner: "Riley Chen", status: "In progress", tone: "active" },
  { name: "Quality review", owner: "Jamie Lee", status: "Pending", tone: "neutral" },
  { name: "Release notes", owner: "Taylor Kim", status: "Pending", tone: "neutral" },
  { name: "Deploy", owner: "Release Manager", status: "Blocked", tone: "danger" },
] as const;

const navigation = ["Home", "Overview", "Work", "Code", "Builds", "Releases", "Deployments"];
type Theme = "light" | "dark";
type GuideState = "expanded" | "collapsed";

export default function QuietPresenceDemo() {
  const [theme, setTheme] = useState<Theme>("light");
  const [guideState, setGuideState] = useState<GuideState>("expanded");
  const [mobileGuideOpen, setMobileGuideOpen] = useState(true);
  const [focusOpen, setFocusOpen] = useState(false);
  const [audience, setAudience] = useState("PRODUCT_LEADER");
  const [depth, setDepth] = useState("CONCISE");
  const [result, setResult] = useState<GuideDemoResult | null>(null);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [captionsOn, setCaptionsOn] = useState(true);
  const [consentAcknowledged, setConsentAcknowledged] = useState(false);
  const [error, setError] = useState("");
  const [hydrated, setHydrated] = useState(false);
  const focusButtonRef = useRef<HTMLButtonElement>(null);
  const launcherRef = useRef<HTMLButtonElement>(null);
  const activeRunRef = useRef<{ controller: AbortController; id: number } | null>(null);
  const nextRunIdRef = useRef(0);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      setHydrated(true);
      if (window.innerWidth > 720 && window.innerHeight <= 760) setGuideState("collapsed");
    });
    return () => {
      cancelAnimationFrame(frame);
      activeRunRef.current?.controller.abort();
      activeRunRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!focusOpen) return;
    const dialog = document.getElementById("narratwin-focus-stage");
    const origin = focusButtonRef.current;
    const focusable = () => dialog?.querySelectorAll<HTMLElement>(
      'button:not(:disabled), input:not(:disabled), select:not(:disabled), [href], [tabindex]:not([tabindex="-1"])',
    );
    focusable()?.[0]?.focus();
    const containFocus = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setFocusOpen(false);
        return;
      }
      if (event.key !== "Tab") return;
      const current = focusable();
      if (!current?.length) return;
      const first = current[0];
      const last = current[current.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", containFocus);
    return () => {
      window.removeEventListener("keydown", containFocus);
      requestAnimationFrame(() => origin?.focus());
    };
  }, [focusOpen]);

  async function runDemo() {
    activeRunRef.current?.controller.abort();
    const controller = new AbortController();
    const runId = ++nextRunIdRef.current;
    activeRunRef.current = { controller, id: runId };
    setIsRunning(true);
    setError("");
    setSourcesOpen(false);
    try {
      const nextResult = await runQuietPresenceDemo({
        projectName: "Northwind release workspace",
        knowledgeDocument: defaultKnowledge,
        audience,
        depth,
        targetLanguage: "en",
        glossaryTerms: ["Northwind", "Release 2.4.0"],
        syntheticAvatarConsent: consentAcknowledged,
      }, fetch, controller.signal);
      if (activeRunRef.current?.id === runId && !controller.signal.aborted) setResult(nextResult);
    } catch (caught) {
      if (activeRunRef.current?.id === runId && !controller.signal.aborted) {
        setResult(null);
        setError(
          caught instanceof GuideWorkflowError
            ? caught.message
            : "The local NarraTwin demo could not complete safely. Try again.",
        );
      }
    } finally {
      if (activeRunRef.current?.id === runId) {
        activeRunRef.current = null;
        setIsRunning(false);
      }
    }
  }

  const stopPresentation = () => {
    activeRunRef.current?.controller.abort();
    activeRunRef.current = null;
    setIsRunning(false);
    setResult(null);
    setSourcesOpen(false);
    setError("");
  };
  const toggleTheme = () => setTheme(theme === "light" ? "dark" : "light");
  const returnToHost = () => {
    setMobileGuideOpen(false);
    requestAnimationFrame(() => launcherRef.current?.focus());
  };
  const minimizeGuide = () => {
    setGuideState("collapsed");
    returnToHost();
  };
  const openGuide = () => {
    setGuideState("expanded");
    setMobileGuideOpen(true);
  };
  const explanation = result?.explanation ??
    "Run the grounded local demo to validate this release explanation against approved project evidence.";
  const presenterState = isRunning ? "Grounding evidence" : result ? "Explaining verified source" : "Context ready";

  const guideProps: GuideContentProps = {
    audience,
    captionsOn,
    consentAcknowledged,
    depth,
    error,
    explanation,
    isRunning,
    hydrated,
    presenterState,
    result,
    sourcesOpen,
    onAudienceChange: setAudience,
    onCaptionsToggle: () => setCaptionsOn(!captionsOn),
    onConsentChange: setConsentAcknowledged,
    onDepthChange: setDepth,
    onRun: runDemo,
    onSourcesToggle: () => setSourcesOpen(!sourcesOpen),
    onStop: stopPresentation,
  };

  return (
    <main
      className={styles.demo}
      data-theme={theme}
      data-mobile-guide={mobileGuideOpen ? "open" : "closed"}
      data-hydrated={hydrated}
      aria-busy={isRunning}
    >
      <div className={styles.backgroundLayer} inert={focusOpen} aria-hidden={focusOpen || undefined}>
        <HostTopbar theme={theme} onThemeToggle={toggleTheme} />
        <div className={styles.shell}>
          <HostSidebar />
          <HostWorkspace />
        </div>

        <button
          ref={launcherRef}
          type="button"
          className={styles.mobileGuideLauncher}
          aria-label="Open NarraTwin guide"
          onClick={openGuide}
        >
          <NarraMark />
          <span><strong>Open NarraTwin guide</strong><small>Security review · context ready</small></span>
          <Icon name="arrow" />
        </button>

        <aside
          className={styles.guideRibbon}
          aria-label="NarraTwin project guide"
          data-guide-state={guideState}
        >
          <div className={styles.mobileGuideTopbar}>
            <button type="button" aria-label="Back to project" onClick={returnToHost}>
              <Icon name="back" /> Back to project
            </button>
            <ThemeButton theme={theme} onClick={toggleTheme} />
          </div>

          {guideState === "collapsed" ? (
            <CollapsedRibbon presenterState={presenterState} onExpand={() => setGuideState("expanded")} />
          ) : (
            <>
              <RibbonPresenter presenterState={presenterState} />
              <GuideContent {...guideProps} />
              <RibbonControls
                captionsOn={captionsOn}
                focusButtonRef={focusButtonRef}
                isRunning={isRunning}
                onCaptionsToggle={guideProps.onCaptionsToggle}
                onFocus={() => setFocusOpen(true)}
                onMinimize={minimizeGuide}
                onStop={stopPresentation}
              />
            </>
          )}
        </aside>
      </div>

      <FocusStage
        {...guideProps}
        open={focusOpen}
        onClose={() => setFocusOpen(false)}
      />
    </main>
  );
}

function HostTopbar({ theme, onThemeToggle }: { theme: Theme; onThemeToggle: () => void }) {
  return (
    <header className={styles.topbar}>
      <div className={styles.brand} aria-label="Northwind project"><BrandMark /><span>Northwind</span></div>
      <div className={styles.breadcrumbs} aria-label="Breadcrumb">
        <span>Release workflow</span><Icon name="chevron" /><strong>Release 2.4.0</strong>
      </div>
      <div className={styles.search} aria-label="Search Northwind preview">
        <Icon name="search" /><span>Search Northwind</span><small>Preview only</small>
      </div>
      <div className={styles.topActions}>
        <ThemeButton theme={theme} onClick={onThemeToggle} />
        <span className={styles.notification} aria-hidden="true"><Icon name="bell" /></span>
        <span className={styles.userAvatar} role="img" aria-label="Maya Patel">MP</span>
      </div>
    </header>
  );
}

function ThemeButton({ theme, onClick }: { theme: Theme; onClick: () => void }) {
  return (
    <button
      type="button"
      className={styles.iconButton}
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
      onClick={onClick}
    >
      <Icon name={theme === "light" ? "moon" : "sun"} />
    </button>
  );
}

function HostSidebar() {
  return (
    <nav className={styles.sidebar} aria-label="Northwind navigation">
      <div className={styles.navGroup}>
        {navigation.map((item) => (
          <span className={item === "Releases" ? styles.navCurrent : styles.navItem} key={item}>
            <Icon name={item === "Releases" ? "release" : "grid"} /><span>{item}</span>
          </span>
        ))}
      </div>
      <div className={styles.sidebarFooter}>
        <span className={styles.navItem}><Icon name="settings" /><span>Settings</span></span>
        <span className={styles.internetState}><Icon name="globe" /><span>Internet</span><strong>Off</strong></span>
      </div>
    </nav>
  );
}

function HostWorkspace() {
  return (
    <section className={styles.hostWorkspace} aria-labelledby="release-title">
      <div className={styles.releaseHeader}>
        <div>
          <p className={styles.mobileBreadcrumb}>Release workflow / Release 2.4.0</p>
          <div className={styles.titleRow}>
            <h1 id="release-title">Release 2.4.0</h1><span className={styles.progressBadge}>In progress</span>
          </div>
        </div>
        <span className={styles.projectMode}><Icon name="shield" /> Guided locally</span>
      </div>
      <dl className={styles.releaseMeta}>
        <div><dt>Target</dt><dd>Production</dd></div>
        <div><dt>Release window</dt><dd>Aug 5, 2026 · 09:00–11:00</dd></div>
        <div><dt>Created by</dt><dd>Maya Patel</dd></div>
        <div><dt>Last updated</dt><dd>2 Aug 2026 · 10:21</dd></div>
      </dl>
      <nav className={styles.tabs} aria-label="Release sections">
        <span>Overview</span><span className={styles.activeTab}>Approvals</span><span>Artifacts</span>
        <span>Changes</span><span>History</span>
      </nav>
      <div className={styles.releaseTable} role="table" aria-label="Release approval steps">
        <div className={styles.tableHead} role="row">
          <span role="columnheader">Step</span><span role="columnheader">Owner</span>
          <span role="columnheader">Status</span><span role="columnheader">Updated</span>
        </div>
        {releaseSteps.map((step, index) => (
          <div
            className={`${styles.tableRow} ${step.tone === "active" ? styles.contextRow : ""}`}
            role="row"
            aria-current={step.tone === "active" ? "step" : undefined}
            key={step.name}
          >
            <span role="cell" className={styles.stepName}>
              <StatusGlyph tone={step.tone} /><span className={styles.stepNumber}>{index + 1}</span>{step.name}
            </span>
            <span role="cell" className={styles.owner}>{step.owner}</span>
            <span role="cell" className={styles[`tone_${step.tone}`]}>{step.status}</span>
            <span role="cell" className={styles.updated}>{index < 4 ? `2 Aug 09:${12 + index * 8}` : "—"}</span>
          </div>
        ))}
      </div>
      <div className={styles.hostNote}>
        <Icon name="shield" />
        <p><strong>Selected context:</strong> Security review is the first incomplete approval blocking deployment.</p>
      </div>
    </section>
  );
}

type GuideContentProps = {
  audience: string;
  captionsOn: boolean;
  consentAcknowledged: boolean;
  depth: string;
  error: string;
  explanation: string;
  hydrated: boolean;
  isRunning: boolean;
  presenterState: string;
  result: GuideDemoResult | null;
  sourcesOpen: boolean;
  onAudienceChange: (value: string) => void;
  onCaptionsToggle: () => void;
  onConsentChange: (value: boolean) => void;
  onDepthChange: (value: string) => void;
  onRun: () => void;
  onSourcesToggle: () => void;
  onStop: () => void;
};

function RibbonPresenter({ presenterState }: { presenterState: string }) {
  return (
    <section className={styles.ribbonPresenter} aria-label="Synthetic presenter status">
      <div className={styles.presenterFrame}>
        <PresenterPortrait />
        <span className={styles.presenterDisclosure}>Fictional synthetic still · no real-person reference</span>
      </div>
      <div className={styles.guideIdentity}>
        <NarraMark /><span><strong>NarraTwin</strong><small>AI project guide</small></span>
      </div>
      <span className={styles.presenterState}><i />{presenterState}</span>
    </section>
  );
}

function GuideContent(props: GuideContentProps) {
  return (
    <section className={styles.guideContent} aria-label="Grounded project explanation">
      <div className={styles.guideNarrative}>
        <p className={styles.contextLabel}>
          <Icon name="spark" /> {props.result ? "Verified project source" : "Simulated host context"}
        </p>
        <h2>Why is deployment blocked?</h2>
        <p className={styles.explanation} aria-live="polite">{props.explanation}</p>
        {props.result && props.captionsOn ? (
          <p className={styles.translation} lang={props.result.targetLanguage} data-testid="translated-captions">
            {props.result.translatedExplanation}
          </p>
        ) : null}
        {props.error ? <p className={styles.error} role="alert">{props.error}</p> : null}
      </div>

      <div className={styles.guideActions}>
        <div className={styles.runSettings} aria-label="Demo settings">
          <label><span>Audience</span>
            <select value={props.audience} onChange={(event) => props.onAudienceChange(event.currentTarget.value)}>
              <option value="PRODUCT_LEADER">Product leader</option><option value="RECRUITER">Recruiter</option>
              <option value="ENGINEER">Engineer</option>
            </select>
          </label>
          <label><span>Depth</span>
            <select value={props.depth} onChange={(event) => props.onDepthChange(event.currentTarget.value)}>
              <option value="CONCISE">Concise</option><option value="STANDARD">Standard</option>
            </select>
          </label>
        </div>
        <ConsentControl
          checked={props.consentAcknowledged}
          disabled={!props.hydrated}
          onChange={props.onConsentChange}
        />
        <button
          className={styles.runButton}
          type="button"
          disabled={!props.hydrated || !props.consentAcknowledged || props.isRunning}
          onClick={props.onRun}
        >
          <Icon name="play" />{props.isRunning ? "Grounding approved evidence…" : "Run grounded demo"}
        </button>
      </div>

      <EvidencePanel result={props.result} sourcesOpen={props.sourcesOpen} onToggle={props.onSourcesToggle} />
      <CapabilityBoundary />
    </section>
  );
}

function ConsentControl({
  checked,
  disabled,
  onChange,
}: {
  checked: boolean;
  disabled: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className={styles.consentControl}>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.currentTarget.checked)}
      />
      <span>I consent to create a local synthetic presenter preview for this run.</span>
    </label>
  );
}

function EvidencePanel({
  result,
  sourcesOpen,
  onToggle,
}: {
  result: GuideDemoResult | null;
  sourcesOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <section className={styles.evidencePanel} aria-label="Grounding evidence">
      <div className={styles.evidenceTitle}>
        <span><Icon name="source" /><strong>{result ? "Verified project source" : "Simulated host context"}</strong></span>
        <em>{result ? "Verified" : "Pending"}</em>
      </div>
      <p>Security review · release approval step 4</p>
      <button type="button" aria-expanded={sourcesOpen} disabled={!result} onClick={onToggle}>
        Verified sources {result ? `· ${result.sources.length}` : "· pending"}<Icon name="chevron" />
      </button>
      {sourcesOpen && result ? (
        <div className={styles.sources}>
          {result.sources.map((source) => (
            <article key={source.contextRefId}>
              <span>[{source.citationIndex}]</span><div><strong>{source.filename}</strong><p>{source.excerpt}</p></div>
            </article>
          ))}
        </div>
      ) : null}
      {result ? (
        <div className={styles.proofBar}>
          <span><Icon name="check" />Passed evaluation · {result.evaluation.unsupportedClaimCount} unsupported claims</span>
          <span><Icon name="offline" />No external provider calls</span>
          <span>
            Local providers · {result.providerPosture.translation} / {result.providerPosture.voice} / {result.providerPosture.avatar}
          </span>
        </div>
      ) : null}
    </section>
  );
}

function CapabilityBoundary() {
  return (
    <section className={styles.capabilityBoundary} aria-label="Current capability boundary">
      <span><Icon name="offline" /><strong>External web disabled by policy</strong></span>
      <button type="button" disabled>Ask next · planned</button>
      <p>Q&amp;A and governed web search are not enabled in this UI foundation.</p>
      <small>Local mock · no external provider calls, real media, or cloned identity</small>
    </section>
  );
}

function RibbonControls({
  captionsOn,
  focusButtonRef,
  isRunning,
  onCaptionsToggle,
  onFocus,
  onMinimize,
  onStop,
}: {
  captionsOn: boolean;
  focusButtonRef: React.RefObject<HTMLButtonElement | null>;
  isRunning: boolean;
  onCaptionsToggle: () => void;
  onFocus: () => void;
  onMinimize: () => void;
  onStop: () => void;
}) {
  return (
    <div className={styles.ribbonControls}>
      <button ref={focusButtonRef} type="button" aria-label="Expand focus" onClick={onFocus}><Icon name="expand" /><span>Focus</span></button>
      <button type="button" aria-label="Minimize guide" onClick={onMinimize}><Icon name="minus" /><span>Minimize</span></button>
      <button type="button" aria-label={`Captions ${captionsOn ? "on" : "off"}`} aria-pressed={captionsOn} onClick={onCaptionsToggle}>
        <Icon name="captions" /><span>Captions {captionsOn ? "on" : "off"}</span>
      </button>
      <button type="button" aria-label={isRunning ? "Stop" : "Clear"} onClick={onStop}>
        <Icon name="stop" /><span>{isRunning ? "Stop" : "Clear"}</span>
      </button>
    </div>
  );
}

function CollapsedRibbon({ presenterState, onExpand }: { presenterState: string; onExpand: () => void }) {
  return (
    <div className={styles.collapsedRibbon}>
      <div className={styles.guideIdentity}><NarraMark /><span><strong>NarraTwin</strong><small>{presenterState}</small></span></div>
      <span className={styles.collapsedContext}><Icon name="spark" />Security review · Why is deployment blocked?</span>
      <span className={styles.collapsedBoundary}><Icon name="offline" />Local mock · web off</span>
      <button type="button" aria-label="Expand guide" onClick={onExpand}><Icon name="arrowUp" />Expand guide</button>
    </div>
  );
}

function FocusStage(props: GuideContentProps & {
  open: boolean;
  onClose: () => void;
}) {
  return (
    <section
      id="narratwin-focus-stage"
      className={styles.focusStage}
      role="dialog"
      aria-modal="true"
      aria-label="NarraTwin focus stage"
      hidden={!props.open}
    >
      <header>
        <div className={styles.guideIdentity}><NarraMark /><span><strong>NarraTwin</strong><small>Focused project walkthrough</small></span></div>
        <button id="narratwin-focus-close" type="button" aria-label="Close focus stage" onClick={props.onClose}>
          <Icon name="close" /> Close
        </button>
      </header>
      <div className={styles.focusLayout}>
        <div className={styles.focusPresenter}>
          <PresenterPortrait fullLength />
          <p>Fictional synthetic still · no real-person reference</p>
          <span><i />{props.open ? props.presenterState : "Focus stage ready"}</span>
        </div>
        <div className={styles.focusNarrative}>
          <p className={styles.contextLabel}>
            <Icon name="spark" /> {props.result ? "Verified project source" : "Simulated host context"}
          </p>
          <h2>Why is deployment blocked?</h2>
          <p className={styles.focusExplanation} aria-live="polite">
            {props.open ? props.explanation : "Open the focus stage for the current grounded explanation."}
          </p>
          {props.open && props.result && props.captionsOn ? (
            <p className={styles.translation} lang={props.result.targetLanguage} data-testid="focus-translated-captions">
              {props.result.translatedExplanation}
            </p>
          ) : null}
          <EvidencePanel
            result={props.open ? props.result : null}
            sourcesOpen={props.open && props.sourcesOpen}
            onToggle={props.onSourcesToggle}
          />
          <CapabilityBoundary />
          <ConsentControl
            checked={props.consentAcknowledged}
            disabled={!props.hydrated}
            onChange={props.onConsentChange}
          />
          <div className={styles.focusActions}>
            <button
              type="button"
              className={styles.runButton}
              disabled={!props.hydrated || !props.consentAcknowledged || props.isRunning}
              onClick={props.onRun}
            >
              <Icon name="play" />{props.isRunning ? "Grounding approved evidence…" : "Run grounded demo"}
            </button>
            <button type="button" disabled={!props.result && !props.isRunning} onClick={props.onStop}>
              <Icon name="stop" />Stop
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

type IconName = "arrow" | "arrowUp" | "back" | "bell" | "captions" | "check" | "chevron" |
  "close" | "expand" | "globe" | "grid" | "minus" | "moon" | "offline" | "play" |
  "release" | "search" | "settings" | "shield" | "source" | "spark" | "stop" | "sun";

function Icon({ name }: { name: IconName }) {
  const paths: Record<IconName, React.ReactNode> = {
    arrow: <path d="M5 12h14m-5-5 5 5-5 5"/>,
    arrowUp: <path d="m7 14 5-5 5 5"/>,
    back: <path d="m15 18-6-6 6-6"/>,
    bell: <><path d="M6 9a6 6 0 0 1 12 0c0 7 3 7 3 7H3s3 0 3-7"/><path d="M10 20h4"/></>,
    captions: <><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M8 10h3M8 14h3M14 10h2M14 14h2"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    chevron: <path d="m9 6 6 6-6 6"/>,
    close: <path d="M6 6l12 12M18 6 6 18"/>,
    expand: <path d="M8 3H3v5m13-5h5v5M8 21H3v-5m13 5h5v-5"/>,
    globe: <><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/></>,
    grid: <><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/></>,
    minus: <path d="M5 12h14"/>,
    moon: <path d="M20 15.5A8 8 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z"/>,
    offline: <><path d="M5 5 19 19M8.5 8.5A7 7 0 0 0 5 12M15.5 8.5A7 7 0 0 1 19 12M9 16a4 4 0 0 1 6 0M12 20h.01"/></>,
    play: <path d="m8 5 11 7-11 7Z"/>,
    release: <><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 9h8M8 13h8M8 17h5"/></>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4 4"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19 13.5v-3l-2-.7-.8-2 1-1.9-2.1-2.1-1.9 1-.2-.1-1.8-.7-.7-2h-3l-.7 2-2 .8-1.9-1L.8 5.9l1 1.9-.8 2v3l2 .7.8 2-1 1.9 2.1 2.1 1.9-1 2 .8.7 2h3l.7-2 2-.8 1.9 1 2.1-2.1-1-1.9Z"/></>,
    shield: <><path d="M12 3 20 6v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6Z"/><path d="m8 12 3 3 5-6"/></>,
    source: <><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></>,
    spark: <><path d="m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6Z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8Z"/></>,
    stop: <rect x="7" y="7" width="10" height="10" rx="1"/>,
    sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></>,
  };
  return <svg className={styles.icon} aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

function StatusGlyph({ tone }: { tone: (typeof releaseSteps)[number]["tone"] }) {
  return <span className={`${styles.statusGlyph} ${styles[`status_${tone}`]}`}>{tone === "success" ? "✓" : tone === "danger" ? "!" : ""}</span>;
}

function BrandMark() {
  return <span className={styles.brandMark} aria-hidden="true"><i/><i/><i/></span>;
}

function NarraMark() {
  return <span className={styles.narraMark} aria-hidden="true"><i/><i/><i/></span>;
}

function PresenterPortrait({ fullLength = false }: { fullLength?: boolean }) {
  return (
    <div
      className={`${styles.portrait} ${fullLength ? styles.portraitFull : ""}`}
      role="img"
      aria-label="Photorealistic fictional synthetic adult Indian woman presenter; still image, generated without a real-person reference"
      data-image-src="/demo/narratwin-synthetic-presenter.webp"
    />
  );
}
