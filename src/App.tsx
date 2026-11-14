import {
  Component,
  Suspense,
  lazy,
  useEffect,
  useId,
  useRef,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import {
  X,
  Compass,
  Footprints,
  FlaskConical,
  CircleHelp,
  BatteryCharging,
  Wind,
  Droplets,
  Wheat,
  ShieldCheck,
  Settings2,
  Radio,
  MapPin,
  ArrowRight,
  Volume2,
  VolumeX,
} from "lucide-react";
import { BUILDINGS, type BuildingName } from "./content/buildings";
import {
  TASKS,
  EVENTS,
  commitTurn,
  defaultPlan,
  initialMission,
  previewTurn,
  taskError,
  earthHint,
  type Task,
  type Plan,
} from "./domain/mission";
import {
  advanceGuide,
  initialGuide,
  guidance,
  canCommitGuide,
  outcomeLines,
  TARGETS,
  TARGET_TASKS,
  type GuideAction,
  type TargetId,
} from "./domain/guidance";
import { loadSession, saveSession } from "./infrastructure/session";
import ScienceLibrary from "./components/ScienceLibrary";
import { MUSIC, useBackgroundMusic } from "./infrastructure/music";
const Outpost = lazy(() => import("./scenes/Outpost"));
class SceneBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}
function Dialog({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  useEffect(() => {
    const before = document.activeElement as HTMLElement;
    ref.current?.showModal();
    return () => before?.focus();
  }, []);
  return (
    <dialog
      ref={ref}
      aria-labelledby={id}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="dialog-heading">
        <h2 id={id}>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
const BENEFITS: Record<Task, string> = {
  research: "+1 research · 4 energy",
  fieldSample:
    "+1 research +1 sample · 4 energy · 2 extra water · extra exposure",
  shelter: "75% less exposure · 2 energy · no research",
  upgradeShield: "Lasting protection · 5 energy · no research",
  askEarth: "Advice next turn · 2 energy · no research",
  rest: "0 task energy · no research",
};
export default function App() {
  const music = useBackgroundMusic();
  const [session, setSession] = useState(loadSession);
  const { mission, plan, guide } = session;
  const [cameraMode, setCameraMode] = useState<"orbit" | "walk">("walk");
  const [selected, setSelected] = useState<TargetId | null>(null);
  const [near, setNear] = useState<TargetId | null>(null);
  const [chooser, setChooser] = useState(false);
  const [dialog, setDialog] = useState<
    "plan" | "sources" | "help" | "settings" | "reset" | "debrief" | null
  >(null);
  const [quality, setQuality] = useState<"high" | "low">(() =>
    window.matchMedia("(pointer: coarse)").matches ? "low" : "high",
  );
  const [map, setMap] = useState(
    () => new URLSearchParams(location.search).get("view") === "map",
  );
  const [storageMessage, setStorageMessage] = useState(session.message);
  const [worldNotice, setWorldNotice] = useState("");
  const mapActive = useRef(map);
  useEffect(() => {
    mapActive.current = map;
  }, [map]);
  const [focus, setFocus] = useState<{
    target: TargetId;
    serial: number;
  } | null>(null);
  const [recenter, setRecenter] = useState(0);
  const [idle, setIdle] = useState(false);
  const [recent, setRecent] = useState(false);
  const movement = useRef<[number, number]>([0, 0]);
  const view = previewTurn(mission, plan);
  const story = guidance(guide, mission);
  const finished = mission.status !== "playing";
  const cinematic = guide.node === "cinematic";
  const canCommit = canCommitGuide(guide, mission);
  const event = EVENTS[Math.min(mission.turn - 1, 5)];
  useEffect(() => {
    const warning = saveSession(mission, plan, guide);
    if (warning) setStorageMessage(warning);
  }, [mission, plan, guide]);
  useEffect(() => {
    movement.current = [0, 0];
  }, [dialog, cameraMode, cinematic]);
  useEffect(() => {
    let timer: number;
    const active = () => {
      setIdle(false);
      clearTimeout(timer);
      timer = window.setTimeout(() => setIdle(true), 25000);
    };
    active();
    window.addEventListener("pointerdown", active);
    window.addEventListener("keydown", active);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("pointerdown", active);
      window.removeEventListener("keydown", active);
    };
  }, [guide.node]);
  const act = useCallback(
    (action: GuideAction) =>
      setSession((s) => ({
        ...s,
        guide: advanceGuide(s.guide, action, s.mission, s.plan),
      })),
    [],
  );
  const select = useCallback((target: TargetId) => {
    setChooser(false);
    if (target === "maya" || target === "alex") {
      setSession((s) => ({
        ...s,
        guide: advanceGuide(
          s.guide,
          { type: "talk", person: target },
          s.mission,
          s.plan,
        ),
      }));
      setSelected(target);
      return;
    }
    setSelected(target);
    setSession((s) => ({
      ...s,
      guide: advanceGuide(
        s.guide,
        { type: "select", target },
        s.mission,
        s.plan,
      ),
    }));
  }, []);
  const arrive = useCallback(() => {
    act({ type: "arrive" });
    setCameraMode("walk");
  }, [act]);
  function configure(change: Partial<Plan>) {
    if (!finished)
      setSession((s) => ({ ...s, plan: { ...s.plan, ...change } }));
  }
  function chooseTask(task: Task) {
    if (!taskError(mission, task)) configure({ task });
  }
  function confirmChoice(at: TargetId) {
    act({ type: "choose", at });
    setSelected(null);
  }
  function commit() {
    if (!canCommit || view.errors.length) return;
    const expected = mission.turn;
    setSession((s) => {
      if (s.mission.turn !== expected || !canCommitGuide(s.guide, s.mission))
        return s;
      const next = commitTurn(s.mission, s.plan, expected);
      if (next === s.mission) return s;
      return {
        ...s,
        mission: next,
        plan: {
          oxygenOn: false,
          greenhouseOn: next.growthProgress === 1,
          task: "rest",
        },
        guide: advanceGuide(s.guide, { type: "commit" }, next, s.plan),
      };
    });
    setDialog(null);
    setSelected(null);
  }
  function restart(enabled = true) {
    setSession({
      mission: initialMission(),
      plan: defaultPlan(),
      guide: initialGuide(enabled),
      message: "",
    });
    setSelected(null);
    setDialog(null);
    setChooser(false);
    setRecenter((r) => r + 1);
  }
  function pointTo(target: TargetId) {
    setSelected(null);
    setChooser(false);
    if (map) {
      select(target);
      return;
    }
    setCameraMode("orbit");
    setFocus((f) => ({ target, serial: (f?.serial ?? 0) + 1 }));
  }
  function objective() {
    if (cinematic) {
      arrive();
      return;
    }
    if (guide.node === "outcome") {
      act({ type: "continue" });
      setSelected(null);
      return;
    }
    if (guide.node === "nova") {
      act({ type: "ready" });
      setSelected(null);
      return;
    }
    if (guide.node === "debrief") {
      setDialog("debrief");
      return;
    }
    if (guide.node === "water") {
      select("Life support");
      return;
    }
    if (guide.node === "route") {
      select("rover");
      return;
    }
    if (guide.node === "sample") {
      pointTo("sample");
      return;
    }
    if (story.target) {
      pointTo(story.target);
      return;
    }
    setDialog("plan");
  }
  const resources = [
    ["Energy", mission.energy, view.after.energy, "E", BatteryCharging],
    ["Oxygen", mission.oxygen, view.after.oxygen, "u", Wind],
    ["Water", mission.water, view.after.water, "u", Droplets],
    ["Food", mission.food, view.after.food, "packs", Wheat],
    ["Exposure", mission.exposure, view.after.exposure, "pts", ShieldCheck],
  ] as const;
  const forecast = (
    <div className="forecast" aria-label="Live resource forecast">
      {resources
        .filter(([label]) => dialog === "plan" || guide.learned.includes(label))
        .map(([label, before, after, unit, Icon]) => (
          <div
            className={
              (label === "Exposure" ? after > 12 : after <= 0) ? "danger" : ""
            }
            key={label}
          >
            <Icon size={18} />
            <span>
              {label}
              <strong>
                {before} <span>→</span> {after}
              </strong>
              <small>
                {label === "Exposure"
                  ? "12 = safety limit"
                  : `${unit} after this turn`}
              </small>
            </span>
          </div>
        ))}
    </div>
  );
  const oxygenControls = (
    <fieldset className="allocation">
      <legend>Oxygen production</legend>
      <div className="choice-row">
        <button
          aria-pressed={plan.oxygenOn}
          onClick={() => configure({ oxygenOn: true })}
        >
          Produce oxygen <small>4 energy · +12 oxygen</small>
        </button>
        <button
          aria-pressed={!plan.oxygenOn}
          onClick={() => configure({ oxygenOn: false })}
        >
          Use stored oxygen <small>0 energy · reserve −12</small>
        </button>
      </div>
    </fieldset>
  );
  const foodControls = (
    <fieldset className="allocation">
      <legend>Greenhouse lights</legend>
      <div className="choice-row">
        <button
          aria-pressed={plan.greenhouseOn}
          onClick={() => configure({ greenhouseOn: true })}
        >
          Power growing lights <small>3 energy · 1 water</small>
        </button>
        <button
          aria-pressed={!plan.greenhouseOn}
          onClick={() => configure({ greenhouseOn: false })}
        >
          Pause growing <small>0 energy · growth resets</small>
        </button>
      </div>
      <small>
        {mission.growthProgress}/2 powered turns complete. Two consecutive turns
        yield two meals.
      </small>
    </fieldset>
  );
  const taskButtons = (tasks: Task[]) =>
    tasks.map((task) => {
      const t = TASKS.find((t) => t.id === task)!;
      const error = taskError(mission, task);
      return (
        <button
          key={task}
          className={`command ${plan.task === task ? "chosen" : ""}`}
          aria-pressed={plan.task === task}
          disabled={!!error || finished}
          onClick={() => chooseTask(task)}
        >
          <span>
            <strong>{t.title}</strong>
            <small>{error || BENEFITS[task]}</small>
          </span>
        </button>
      );
    });
  const budget = (
    <div className="energy-budget" aria-label="Energy allocation">
      <span>
        Stored {mission.energy} + sunlight {view.generation}
      </span>
      <strong>
        {view.available} available · {view.cost} planned · {view.after.energy}{" "}
        left
      </strong>
      <div style={{ display: "flex" }}>
        {[
          ["Base", 4],
          ["Oxygen", plan.oxygenOn ? 4 : 0],
          ["Growing", plan.greenhouseOn ? 3 : 0],
          ["Crew", TASKS.find((t) => t.id === plan.task)!.cost],
        ].map(
          ([label, cost]) =>
            Number(cost) > 0 && (
              <span key={label} style={{ flex: Number(cost) }}>
                {label} {cost}
              </span>
            ),
        )}
      </div>
      {view.spilledEnergy > 0 && (
        <small>
          Battery capacity: 20. {view.spilledEnergy} incoming energy cannot be
          stored.
        </small>
      )}
    </div>
  );
  const flat = (
    <div className="flat-map" aria-label="Lightweight mission map">
      <div className="flat-path" />
      {Object.entries(TARGETS).map(([id, t]) => (
        <button
          key={id}
          style={{
            left: `${((t.position[0] + 38) / 90) * 100}%`,
            top: `${((t.position[2] + 40) / 80) * 100}%`,
          }}
          className={story.target === id ? "selected" : ""}
          onClick={() => select(id as TargetId)}
        >
          {id === story.target ? "◆" : "⌖"} {t.name}
        </button>
      ))}
      <span className="flat-caption">
        Accessible mission map · Tap a destination to interact
      </span>
    </div>
  );
  const crewLine =
    selected === "maya"
      ? guide.node === "alex"
        ? "Welcome, Commander! Find Alex by the landing area."
        : "Explore carefully. Our science goal is three research objectives and one sample."
      : selected === "alex"
        ? guide.node === "nova"
          ? "I keep the base running. NOVA will guide your first decisions."
          : "Every system shares our energy. Check the forecast before advancing."
        : "";
  return (
    <main
      className={`game-shell guided-game mode-surface camera-${cameraMode} ${cinematic ? "arrival" : ""} ${new URLSearchParams(location.search).has("debug") ? "debug" : ""}`}
    >
      <a className="skip-link" href="#mission-toolbar">
        Skip to mission controls
      </a>
      <div className="world-stage">
        {map ? (
          flat
        ) : (
          <SceneBoundary
            fallback={
              <div className="world-error">
                <h2>The 3D view could not load.</h2>
                <button className="primary" onClick={() => setMap(true)}>
                  Open mission map
                </button>
              </div>
            }
          >
            <Suspense
              fallback={
                <div className="world-loading">
                  Preparing Mars…{" "}
                  <button onClick={() => setMap(true)}>Use mission map</button>
                </div>
              }
            >
              <Outpost
                mode="surface"
                cameraMode={cameraMode}
                selected={
                  BUILDINGS.some((b) => b.name === selected)
                    ? (selected as BuildingName)
                    : null
                }
                onSelect={select}
                onLand={arrive}
                onDescend={arrive}
                mission={mission}
                plan={plan}
                quality={quality}
                paused={!!dialog}
                onFail={() => {
                  if (!mapActive.current) {
                    setWorldNotice(
                      "The 3D view stopped. Your mission continues on the accessible map.",
                    );
                    setMap(true);
                  }
                }}
                onNear={setNear}
                movement={movement}
                recenter={recenter}
                onSample={() => select("sample")}
                onInteract={select}
                guideTarget={!cinematic ? story.target : undefined}
                focus={focus}
                cinematic={cinematic}
                onArrival={arrive}
                routePreview={["sample", "expedition"].includes(guide.node)}
              />
            </Suspense>
          </SceneBoundary>
        )}
      </div>
      <div className="world-vignette" />
      <header className="game-header">
        <a className="brand" href="#" aria-label="Mars Mission Commander home">
          <span className="brand-symbol">
            M<span>•</span>
          </span>
          <span>
            MARS<small>MISSION COMMANDER</small>
          </span>
        </a>
        <div className="expedition-label">ARES EXPEDITION / TRAINING 01</div>
        <nav aria-label="Mission navigation">
          <button
            className="icon-button"
            data-music-control
            aria-label={
              music.error
                ? "Retry background music"
                : music.playing
                  ? "Mute background music"
                  : "Play background music"
            }
            aria-pressed={music.playing}
            title={
              music.error ||
              (music.playing
                ? "Background music playing"
                : "Music starts after your first interaction")
            }
            onClick={music.toggle}
          >
            {music.playing && music.volume > 0 ? (
              <Volume2 size={20} />
            ) : (
              <VolumeX size={20} />
            )}
          </button>
          <button
            className="icon-button"
            aria-label="Mission help"
            onClick={() => setDialog("help")}
          >
            <CircleHelp size={20} />
          </button>
          <button
            className="icon-button"
            aria-label="Science library"
            onClick={() => setDialog("sources")}
          >
            <FlaskConical size={20} />
          </button>
          <button
            className="icon-button"
            aria-label="Settings"
            onClick={() => setDialog("settings")}
          >
            <Settings2 size={20} />
          </button>
        </nav>
      </header>
      {!cinematic && (
        <>
          <div className="turn-weather">
            <span>
              TURN {String(Math.min(mission.turn, 6)).padStart(2, "0")} / 06
            </span>
            <strong>
              {finished
                ? "Mission complete"
                : event === "storm"
                  ? "⚠ Solar radiation warning"
                  : event === "dust"
                    ? "Dusty skies · reduced power"
                    : "Clear Martian skies"}
            </strong>
          </div>
          <div className="resource-hud" aria-label="Mission reserves">
            {resources
              .filter(([name]) => guide.learned.includes(name))
              .map(([name, value, , unit, Icon]) => (
                <div key={name}>
                  <Icon size={18} />
                  <span>
                    <small>{name}</small>
                    <strong>
                      {value} <small>{unit}</small>
                    </strong>
                  </span>
                </div>
              ))}
          </div>
          <div className="world-controls" id="mission-toolbar" tabIndex={-1}>
            <button
              aria-pressed={cameraMode === "orbit"}
              onClick={() => setCameraMode("orbit")}
            >
              <Compass size={17} />
              Overview
            </button>
            <button
              aria-pressed={cameraMode === "walk"}
              onClick={() => {
                setCameraMode("walk");
                setRecenter((r) => r + 1);
              }}
            >
              <Footprints size={17} />
              Walk
            </button>
            <button
              aria-expanded={chooser}
              onClick={() => {
                setChooser(!chooser);
                setSelected(null);
              }}
            >
              <MapPin size={17} />
              Destinations
            </button>
            <button onClick={() => setDialog("plan")}>Plan</button>
          </div>
          {!map && cameraMode === "walk" && (
            <>
              <p className="walk-help">
                WASD / arrows · drag to look · E to interact
              </p>
              {near && (
                <button className="near-prompt" onClick={() => select(near)}>
                  E ·{" "}
                  {near === "maya" || near === "alex" ? "Talk to" : "Inspect"}{" "}
                  {TARGETS[near].name}
                </button>
              )}
              <div
                className="movement-pad"
                aria-label="Touch movement controls"
              >
                {[
                  ["↑", 0, -1, "Move forward"],
                  ["←", -1, 0, "Move left"],
                  ["↓", 0, 1, "Move backward"],
                  ["→", 1, 0, "Move right"],
                ].map(([label, x, z, name]) => (
                  <button
                    key={name}
                    aria-label={String(name)}
                    onPointerDown={(e) => {
                      e.currentTarget.setPointerCapture(e.pointerId);
                      movement.current = [Number(x), Number(z)];
                    }}
                    onPointerUp={() => (movement.current = [0, 0])}
                    onLostPointerCapture={() => (movement.current = [0, 0])}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </>
          )}
          {chooser && (
            <section className="context-sheet" aria-label="Destination chooser">
              <div className="sheet-heading">
                <h2>Where shall we go?</h2>
                <button
                  aria-label="Close destinations"
                  onClick={() => setChooser(false)}
                >
                  <X size={18} />
                </button>
              </div>
              {Object.entries(TARGETS).map(([id, t]) => (
                <button
                  className="command"
                  key={id}
                  onClick={() => {
                    if (map) select(id as TargetId);
                    else pointTo(id as TargetId);
                  }}
                >
                  {t.name} {story.target === id && "◆ Current objective"}
                </button>
              ))}
            </section>
          )}
          {selected && (
            <section
              className="context-sheet facility-guide"
              aria-label={`${TARGETS[selected].name} controls`}
            >
              <div className="sheet-heading">
                <span className="eyebrow">
                  {selected === "maya" || selected === "alex"
                    ? "CREW CONVERSATION"
                    : "PLANNING · NOTHING SPENT YET"}
                </span>
                <button
                  className="icon-button"
                  aria-label="Close facility"
                  onClick={() => setSelected(null)}
                >
                  <X size={20} />
                </button>
              </div>
              <h2>{TARGETS[selected].name}</h2>
              <p className="context-objective">{story.line}</p>
              {crewLine ? (
                <>
                  <p className="crew-dialogue">{crewLine}</p>
                  <button
                    className="primary"
                    onClick={() => {
                      setSelected(null);
                      if (guide.node === "nova") act({ type: "ready" });
                    }}
                  >
                    Continue <ArrowRight size={16} />
                  </button>
                </>
              ) : (
                <>
                  {(selected === "Power station" ||
                    selected === "Life support") && (
                    <>
                      {budget}
                      {oxygenControls}
                      {selected === "Power station" && (
                        <small>
                          Other allocations remain available in Plan.
                        </small>
                      )}
                      {selected === "Life support" && (
                        <div className="water-tank">
                          <Droplets />
                          Water {mission.water} → {view.after.water}
                          <progress
                            value={mission.water}
                            max={12}
                            aria-label="Water reserve"
                          />
                          Crew use: 1 per turn. Plants:{" "}
                          {plan.greenhouseOn ? 1 : 0}. Expedition:{" "}
                          {plan.task === "fieldSample" ? 2 : 0}.
                        </div>
                      )}
                    </>
                  )}
                  {selected === "Greenhouse" && foodControls}
                  {selected === "rover" || selected === "sample" ? (
                    <>
                      <p>{BENEFITS.fieldSample}</p>
                      {taskError(mission, "fieldSample") ? (
                        <p>{taskError(mission, "fieldSample")}</p>
                      ) : (
                        <>
                          {selected === "rover" && (
                            <>
                              <p>
                                Route: rover bay → geology stop. Marking spends
                                nothing.
                              </p>
                              <button
                                className="primary"
                                onClick={() => {
                                  act({ type: "markRoute" });
                                  setSelected(null);
                                  if (!map) pointTo("sample");
                                }}
                              >
                                Mark geology route
                              </button>
                            </>
                          )}
                          {selected === "sample" && (
                            <>
                              <p>
                                {mission.samples
                                  ? "A sample is already in our research log."
                                  : "Sample identified. Collection happens only when you advance the turn."}
                              </p>
                              <button
                                className="primary"
                                onClick={() => {
                                  configure({ task: "fieldSample" });
                                  act({ type: "collect" });
                                  setSelected(null);
                                }}
                              >
                                Plan sample collection
                              </button>
                            </>
                          )}
                        </>
                      )}
                    </>
                  ) : null}
                  {TARGET_TASKS[selected as BuildingName] && (
                    <div className="task-choices">
                      {taskButtons(TARGET_TASKS[selected as BuildingName]!)}
                    </div>
                  )}
                  {selected === "Living habitat" && (
                    <p>
                      Your crew uses 12 oxygen, 1 water, and 1 meal per turn.
                    </p>
                  )}
                  {selected === "Storage center" && (
                    <p>Stored reserves help the base through dusty weather.</p>
                  )}
                  {forecast}
                  {selected === "Life support" && guide.node === "water" ? (
                    <button
                      className="primary"
                      onClick={() => {
                        act({ type: "water" });
                        setSelected(null);
                      }}
                    >
                      Water tank checked
                    </button>
                  ) : (
                    !["rover", "sample"].includes(selected) && (
                      <button
                        className="primary"
                        onClick={() => confirmChoice(selected)}
                      >
                        Keep this plan
                      </button>
                    )
                  )}
                  {[
                    "rover",
                    "sample",
                    "Radiation shelter",
                    "Communication center",
                  ].includes(selected) && (
                    <button
                      className="text-button"
                      onClick={() => {
                        act({ type: "decline" });
                        setSelected(null);
                      }}
                    >
                      Choose another crew task instead
                    </button>
                  )}
                </>
              )}
            </section>
          )}
        </>
      )}
      <section
        className="mission-guide"
        aria-label="Mission guide"
        aria-live="polite"
      >
        <div className="guide-speaker">
          {story.speaker === "NOVA" ? (
            <img src="/assets/nova.png" alt="" />
          ) : story.speaker === "Alex" ? (
            <img src="/assets/alex.png" alt="" />
          ) : (
            <span className="maya-avatar">M</span>
          )}
          <span>
            {story.speaker}
            <small>
              {cinematic
                ? "MISSION ARRIVAL"
                : `OBJECTIVE · ${Math.min(mission.turn, 6)} / 6`}
            </small>
          </span>
          <button
            className="icon-button"
            aria-label="Recent guidance"
            aria-expanded={recent}
            onClick={() => setRecent(!recent)}
          >
            ↺
          </button>
        </div>
        <h1>{story.title}</h1>
        <p>{story.line}</p>
        {guide.node === "outcome" && (
          <ul className="outcome-lines">
            {outcomeLines(mission)
              .slice(1)
              .map((line) => (
                <li key={line}>{line}</li>
              ))}
          </ul>
        )}
        {idle && !selected && !dialog && !cinematic && (
          <p className="inactivity-hint">
            {story.target
              ? `Look for the cyan marker: ${TARGETS[story.target].name}. Use Overview to find it.`
              : "Tap the highlighted action below when you are ready."}
          </p>
        )}
        {recent && (
          <div className="recent-guidance">
            <strong>Recent guidance</strong>
            {guide.log.length ? (
              guide.log.map((line, i) => <p key={i}>{line}</p>)
            ) : (
              <p>Your mission starts here.</p>
            )}
            <button onClick={() => setRecent(false)}>
              Back to current objective
            </button>
          </div>
        )}
        <div className="guide-actions">
          <button className="primary" onClick={objective}>
            {story.action}
            <ArrowRight size={17} />
          </button>
          {story.fact && (
            <button
              className="text-button"
              onClick={() => setDialog("sources")}
            >
              Why? NASA science
            </button>
          )}
        </div>
      </section>
      {mission.revealedHintIds.length > 0 && !cinematic && (
        <button className="earth-reply" onClick={() => setDialog("help")}>
          <Radio size={15} />
          Earth reply received
        </button>
      )}
      {worldNotice && (
        <div className="world-fallback-notice" role="status">
          {worldNotice}
          <button
            aria-label="Dismiss view notice"
            onClick={() => setWorldNotice("")}
          >
            Close
          </button>
        </div>
      )}
      {storageMessage && (
        <div className="storage-alert" role="status">
          {storageMessage}
          <button
            aria-label="Dismiss saving notice"
            onClick={() => setStorageMessage("")}
          >
            ×
          </button>
        </div>
      )}
      <div id="render-stats" className="render-stats" />
      <audio
        id="background-music"
        ref={music.audioRef}
        src={MUSIC.src}
        loop
        preload="none"
        hidden
      />
      {dialog === "plan" && (
        <Dialog title="Review mission plan" onClose={() => setDialog(null)}>
          <p>Preview only. You command one crew task per turn.</p>
          {budget}
          {oxygenControls}
          {foodControls}
          <details className="crew-task-picker" open>
            <summary>Choose one crew task</summary>
            <div className="task-choices">
              {taskButtons(TASKS.map((t) => t.id))}
            </div>
          </details>
          {forecast}
          <p className="mission-score">
            Science {mission.research}/3 · Samples {mission.samples}/1 ·
            Shielding {mission.shieldLevel}/2
          </p>
          {view.errors.map((e) => (
            <p className="warning" role="alert" key={e}>
              {e}
            </p>
          ))}
          {view.warnings.map((e) => (
            <p className="warning" key={e}>
              {e}
            </p>
          ))}
          {!canCommit && !finished && (
            <p className="science-note">
              Complete your current world objective before advancing.
            </p>
          )}
          <button
            className="primary full"
            disabled={!canCommit || view.errors.length > 0}
            onClick={commit}
          >
            Advance turn {mission.turn}
          </button>
          <details>
            <summary>Show the full calculation</summary>
            <p>{view.explanation}</p>
            <p>
              Exposure added: {view.exposureAdded}. Oxygen overflow:{" "}
              {view.oxygenOverflow}. Harvest: {view.harvest} meals.
            </p>
            <p>Resource units and safety limits are training game rules.</p>
          </details>
        </Dialog>
      )}
      {dialog === "sources" && (
        <Dialog title="NASA science & sources" onClose={() => setDialog(null)}>
          <ScienceLibrary focusId={story.fact} />
        </Dialog>
      )}
      {dialog === "help" && (
        <Dialog title="Your mission companion" onClose={() => setDialog(null)}>
          <p>
            Keep the crew safe through six turns. Complete three research
            objectives and collect one sample.
          </p>
          <p>Walk with WASD or arrows. Drag to look. Press E near a marker.</p>
          <p>On touch screens, use the movement pad and tap world markers.</p>
          <p>
            Overview shows your next destination. Every choice has a live
            preview.
          </p>
          {mission.revealedHintIds.map((id) => (
            <p className="earth-message" key={id}>
              {earthHint(Number(id.replace("turn-", "")))}
            </p>
          ))}
          <button
            onClick={() => {
              setDialog(null);
              setRecent(true);
            }}
          >
            Replay recent guidance
          </button>
          <details>
            <summary>Training rules</summary>
            <p>
              One turn is a planning step, not a measured sol. Resource rates
              are fictional training rules; original NASA evidence is available
              in the science library.
            </p>
          </details>
        </Dialog>
      )}
      {dialog === "settings" && (
        <Dialog title="Mission settings" onClose={() => setDialog(null)}>
          <fieldset className="music-settings" data-music-control>
            <legend>Background music</legend>
            <label className="setting-check">
              <input
                type="checkbox"
                checked={music.enabled}
                onChange={(e) => music.setEnabled(e.target.checked)}
              />
              Music enabled
            </label>
            <label className="music-volume" htmlFor="background-music-volume">
              Music volume <output>{Math.round(music.volume * 100)}%</output>
              <input
                id="background-music-volume"
                type="range"
                min="0"
                max="100"
                step="1"
                value={Math.round(music.volume * 100)}
                onChange={(e) => music.setVolume(Number(e.target.value) / 100)}
              />
            </label>
            <p className="science-note">
              {music.error ||
                "Starts after your first tap or keypress. Pauses while the game tab is hidden."}
            </p>
            <p className="music-credit">
              <a href={MUSIC.source} target="_blank" rel="noreferrer">
                {MUSIC.title}
              </a>{" "}
              by {MUSIC.artist}
              <br />
              Released under{" "}
              <a href={MUSIC.license} target="_blank" rel="noreferrer">
                CC BY 4.0
              </a>{" "}
              · www.scottbuckley.com.au
            </p>
          </fieldset>
          <fieldset>
            <legend>Visual quality</legend>
            <button
              aria-pressed={quality === "high"}
              onClick={() => setQuality("high")}
            >
              High · soft shadows
            </button>
            <button
              aria-pressed={quality === "low"}
              onClick={() => setQuality("low")}
            >
              Low · lighter rendering
            </button>
          </fieldset>
          <button onClick={() => setMap(!map)}>
            {map ? "Return to 3D world" : "Use accessible mission map"}
          </button>
          <label className="setting-check">
            <input
              type="checkbox"
              checked={guide.enabled}
              onChange={(e) => {
                const enabled = e.target.checked;
                setSession((s) => ({
                  ...s,
                  guide: enabled
                    ? {
                        ...s.guide,
                        enabled: true,
                        node:
                          s.mission.status === "playing" ? "review" : "debrief",
                      }
                    : {
                        ...s.guide,
                        enabled: false,
                        node:
                          s.mission.status === "playing" ? "free" : "debrief",
                        learned: [
                          "Energy",
                          "Oxygen",
                          "Water",
                          "Food",
                          "Exposure",
                        ],
                      },
                }));
              }}
            />
            Guided objectives
          </label>
          <p className="science-note">
            Reduced-motion preferences skip the arrival animation and soften
            world effects.
          </p>
          <button className="text-button" onClick={() => setDialog("reset")}>
            Restart mission
          </button>
        </Dialog>
      )}
      {dialog === "reset" && (
        <Dialog title="Start a new expedition?" onClose={() => setDialog(null)}>
          <p>This replaces your saved mission.</p>
          <button className="primary" onClick={() => restart()}>
            Replay guided mission
          </button>
          <button onClick={() => restart(false)}>Start without guidance</button>
        </Dialog>
      )}
      {dialog === "debrief" && (
        <Dialog
          title={
            mission.status === "success"
              ? "Mission accomplished, Commander."
              : mission.status === "rescue"
                ? "The crew needed a rescue."
                : "Your crew returned safely."
          }
          onClose={() => setDialog(null)}
        >
          <div className="debrief-cards">
            <article>
              <ShieldCheck />
              <h3>Crew</h3>
              <strong>
                {mission.status === "rescue" ? "Rescue" : "Safe return"}
              </strong>
              <p>{mission.exposure} exposure / 12 limit</p>
            </article>
            <article>
              <FlaskConical />
              <h3>Science</h3>
              <strong>{mission.research} / 3</strong>
              <p>{mission.samples} / 1 sample</p>
            </article>
            <article>
              <Wheat />
              <h3>Reserves</h3>
              <strong>{mission.food} meals</strong>
              <p>
                {mission.oxygen} oxygen · {mission.water} water
              </p>
            </article>
          </div>
          <h3>Your choices mattered</h3>
          <p>
            {mission.history.some((h) => h.after.food - h.before.food === 1)
              ? "Your greenhouse harvested meals. Keeping plants lit cost both water and energy."
              : "You saved energy by pausing plants. Food reserves could not last forever."}
          </p>
          <p>
            {mission.history.some((h) => h.plan.task === "shelter")
              ? "Sheltering traded a research opportunity for less radiation exposure."
              : "Your crew used its tasks elsewhere, accepting the radiation forecast."}
          </p>
          <details>
            <summary>Review your six-turn story</summary>
            <ol className="timeline">
              {mission.history.map((h) => (
                <li key={h.turn}>
                  <strong>
                    Turn {h.turn} ·{" "}
                    {TASKS.find((t) => t.id === h.plan.task)?.title}
                  </strong>
                  <p>{h.explanation}</p>
                  <small>
                    Energy {h.before.energy} → {h.after.energy} · Water{" "}
                    {h.before.water} → {h.after.water} · Exposure{" "}
                    {h.before.exposure} → {h.after.exposure}
                  </small>
                </li>
              ))}
            </ol>
          </details>
          <button className="primary" onClick={() => restart()}>
            Replay guided mission
          </button>
          <button onClick={() => restart(false)}>Try your own strategy</button>
        </Dialog>
      )}
    </main>
  );
}
