import { Suspense, lazy } from "react";
import { ArrowUpRight } from "lucide-react";
import { evidence } from "../data/evidence";
import { MUSIC } from "../infrastructure/music";
const RadiationChart = lazy(() => import("./RadiationChart"));
const FACTS: Record<string, string> = {
  moxie: "MOXIE demonstrated making oxygen from Martian carbon dioxide.",
  "osdr-plants":
    "Space experiments help scientists understand how light affects seedlings.",
  "csa-food":
    "Astronaut food needs careful planning, storage, and preparation.",
  "radlab-iss":
    "Radiation varies in space. Measurements help scientists study exposure.",
  "donki-flare":
    "NASA records solar flares. This mission uses an archived example.",
  "jezero-image":
    "Jezero?s ancient delta helps scientists choose places to investigate.",
};
export default function ScienceLibrary({ focusId }: { focusId?: string }) {
  return (
    <>
      <p>
        Archived sources, not live space weather. Real observations and
        fictional game rules are kept separate.
      </p>
      {[...evidence]
        .sort((a, b) => Number(b.id === focusId) - Number(a.id === focusId))
        .map((item) => (
          <article className="evidence-card" key={item.id}>
            <span className="eyebrow">
              {
                {
                  observation: "OBSERVED DATA",
                  educational: "EDUCATIONAL SOURCE",
                  research: "RESEARCH FINDING",
                  imagery: "MARS IMAGERY",
                }[item.kind]
              }{" "}
              · {item.provider}
            </span>
            <h3>{item.title}</h3>
            <p>{FACTS[item.id]}</p>
            <details>
              <summary>Explore the evidence & original source</summary>
              <p>{item.summary}</p>
              <p className="science-note">Source context: {item.context}</p>
              {item.id === "radlab-iss" && (
                <Suspense fallback={<p>Loading archived observations…</p>}>
                  <RadiationChart />
                </Suspense>
              )}
              {item.id === "jezero-image" && (
                <figure className="mars-photo">
                  <img
                    src="/assets/jezero-delta.jpg"
                    alt="Perseverance view across Jezero Crater toward a raised remnant of an ancient delta."
                    loading="lazy"
                    width="640"
                    height="466"
                  />
                  <figcaption>PIA24485 · NASA/JPL-Caltech/ASU/MSSS</figcaption>
                </figure>
              )}
              <dl>
                <dt>Original record</dt>
                <dd>{item.recordId}</dd>
                <dt>Date / retrieved</dt>
                <dd>
                  {item.observedAt} / {item.retrievedAt}
                </dd>
              </dl>
              {item.id === "donki-flare" && (
                <p className="data-reading">
                  X3.9 class · peak 06:54 UTC · 10 May 2024
                </p>
              )}
              <p>
                <strong>Game adaptation:</strong> {item.gameUse}
              </p>
              <p className="science-note">{item.limitations}</p>
              <p className="credit">Credit: {item.credit}</p>
              <a href={item.sourceUrl} target="_blank" rel="noreferrer">
                Open original source <ArrowUpRight size={14} />
              </a>
              {item.id === "osdr-plants" && (
                <a
                  href={item.originalFields.publicationUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  Read the research paper <ArrowUpRight size={14} />
                </a>
              )}
            </details>
          </article>
        ))}
      <p className="music-credit">
        Background music:{" "}
        <a href={MUSIC.source} target="_blank" rel="noreferrer">
          {MUSIC.title}
        </a>{" "}
        by {MUSIC.artist}, released under{" "}
        <a href={MUSIC.license} target="_blank" rel="noreferrer">
          CC BY 4.0
        </a>
        . www.scottbuckley.com.au. Transcoded to 128 kbps MP3 for the game.
      </p>
      <p className="science-note">
        The 3D terrain and models are original procedural illustrations, not
        NASA terrain data. The science library uses archived evidence; all
        resource rates and exposure limits in your mission are game rules.
      </p>
      <p className="science-note">
        Earth and Mars globe textures: Solar System Scope / INOVE, CC BY 4.0;
        resized to 1K Earth / 2K Mars. Terrain, facilities, astronaut models and
        landing vehicle are illustrative project assets. They are not measured
        NASA terrain or certified spacecraft designs.
      </p>
      <a
        href="https://www.solarsystemscope.com/textures/"
        target="_blank"
        rel="noreferrer"
      >
        Globe texture source
      </a>{" "}
      ?{" "}
      <a
        href="https://creativecommons.org/licenses/by/4.0/"
        target="_blank"
        rel="noreferrer"
      >
        CC BY 4.0
      </a>
    </>
  );
}
