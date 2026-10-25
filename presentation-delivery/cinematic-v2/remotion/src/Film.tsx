import "@fontsource/manrope/400.css";
import "@fontsource/manrope/600.css";
import "@fontsource/manrope/700.css";
import "@fontsource/ibm-plex-mono/400.css";
import { Audio, Video } from "@remotion/media";
import {
  AbsoluteFill,
  Img,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";

const c = {
  bg: "#061117",
  amber: "#d8a55e",
  white: "#f1efe9",
  cyan: "#8bcec6",
  red: "#d4876a",
  muted: "#abc0bf",
};
const mono: React.CSSProperties = {
  fontFamily: "IBM Plex Mono, monospace",
  letterSpacing: "0.12em",
};
const sans: React.CSSProperties = {
  fontFamily: "Manrope, Arial, sans-serif",
  fontWeight: 600,
  letterSpacing: "-0.055em",
};
const clamp = (x: number) => Math.min(1, Math.max(0, x));
const into = (f: number, a: number, d: number) => {
  const t = clamp((f - a) / d);
  return t * t * (3 - 2 * t);
};
const Scene = ({ children }: { children: React.ReactNode }) => (
  <AbsoluteFill
    style={{ background: c.bg, color: c.white, overflow: "hidden" }}
  >
    {children}
  </AbsoluteFill>
);
const Clip = ({ name }: { name: string }) => (
  <Video
    src={staticFile("film/" + name + ".mp4")}
    muted
    objectFit="cover"
    style={{ width: "100%", height: "100%" }}
  />
);
const Still = ({ name, scale = 1 }: { name: string; scale?: number }) => (
  <Img
    src={staticFile("film/" + name + ".png")}
    style={{
      width: "100%",
      height: "100%",
      objectFit: "cover",
      transform: `scale(${scale})`,
    }}
  />
);
const Dark = ({ alpha = 0.3 }: { alpha?: number }) => (
  <AbsoluteFill style={{ background: `rgba(2,10,14,${alpha})` }} />
);
const Header = ({ index }: { index: string }) => (
  <>
    <div
      style={{
        position: "absolute",
        left: 80,
        right: 80,
        top: 90,
        height: 2,
        background: c.amber,
      }}
    />
    <div
      style={{
        position: "absolute",
        top: 49,
        right: 80,
        fontSize: 21,
        ...mono,
      }}
    >
      LASTLIGHT <span style={{ color: c.amber }}>/ {index}</span>
    </div>
  </>
);
const Foot = () => (
  <div
    style={{
      position: "absolute",
      left: 80,
      bottom: 38,
      fontSize: 17,
      color: c.muted,
      ...mono,
    }}
  >
    SYNTHETIC SCHOOL SCENARIO / PHYSICS-VERIFIED
  </div>
);
const Enter = ({
  children,
  at = 0,
  style,
}: {
  children: React.ReactNode;
  at?: number;
  style: React.CSSProperties;
}) => {
  const f = useCurrentFrame(),
    p = into(f, at, 18);
  return (
    <div
      style={{
        ...style,
        opacity: p,
        transform: `translateY(${(1 - p) * 38}px)`,
      }}
    >
      {children}
    </div>
  );
};

const Hook = () => {
  const f = useCurrentFrame(),
    p = into(f, 9, 26);
  return (
    <Scene>
      <Clip name="01-district-approach" />
      <AbsoluteFill style={{ background: `rgba(0,5,8,${0.82 - 0.48 * p})` }} />
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 175,
          fontSize: 145,
          lineHeight: 1,
          ...sans,
          opacity: p,
          transform: `translateY(${(1 - p) * 65}px)`,
        }}
      >
        WHAT IF THE
        <br />
        <span style={{ color: c.amber }}>POWER FAILS?</span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          bottom: 80,
          fontSize: 22,
          ...mono,
          color: c.amber,
        }}
      >
        A NIGHTTIME SCHOOL / ONE QUESTION
      </div>
    </Scene>
  );
};

const Intro = () => {
  const f = useCurrentFrame();
  return (
    <Scene>
      <Sequence durationInFrames={93}>
        <AbsoluteFill>
          <Clip name="02-school-hero" />
        </AbsoluteFill>
      </Sequence>
      <Sequence from={93} durationInFrames={33}>
        <AbsoluteFill>
          <Clip name="03-equipment" />
        </AbsoluteFill>
      </Sequence>
      <Sequence from={126} durationInFrames={72}>
        <AbsoluteFill style={{ background: c.bg }}>
          <div
            style={{
              position: "absolute",
              left: 760,
              top: 235,
              width: 1080,
              height: 610,
              overflow: "hidden",
              border: "1px solid #587472",
            }}
          >
            <Clip name="03-roof-detail" />
          </div>
        </AbsoluteFill>
      </Sequence>
      <Sequence from={198} durationInFrames={42}>
        <AbsoluteFill>
          <Clip name="04-school-orbit" />
        </AbsoluteFill>
      </Sequence>
      <Dark alpha={0.18} />
      <Header index="THE DIGITAL TWIN" />
      {f < 126 && (
        <Enter
          at={8}
          style={{
            position: "absolute",
            left: 80,
            top: 150,
            fontSize: 79,
            lineHeight: 1.04,
            ...sans,
          }}
        >
          A BUILDING.
          <br />A BACKUP SYSTEM.
          <br />
          <span style={{ color: c.amber }}>A DIGITAL TWIN.</span>
        </Enter>
      )}
      {f >= 126 && f < 198 && (
        <div style={{ position: "absolute", left: 80, top: 270 }}>
          <div style={{ fontSize: 21, color: c.amber, ...mono }}>INSPECT THE SYSTEM</div>
          <div style={{ fontSize: 61, lineHeight: 1.26, marginTop: 35, ...sans }}>
            ROOFTOP PV.
            <br />BATTERY.
            <br />INVERTER.
          </div>
          <div style={{ fontSize: 21, marginTop: 40, color: c.muted, ...mono }}>
            PHYSICAL MODEL / NIGHT SCENARIO
          </div>
        </div>
      )}
      <Foot />
    </Scene>
  );
};

const Blackout = () => {
  const f = useCurrentFrame(),
    cut = into(f, 58, 10);
  return (
    <Scene>
      <Still name="05-before-blackout-ui" />
      {f >= 58 && f < 204 && (
        <AbsoluteFill style={{ opacity: cut }}>
          <Clip name="05-blackout" />
        </AbsoluteFill>
      )}
      {f >= 204 && (
        <AbsoluteFill>
          <Still name="05-blackout-ui" />
        </AbsoluteFill>
      )}
      <Dark alpha={0.14} />
      <AbsoluteFill
        style={{
          background: "#000",
          opacity: 0.86 * (into(f, 66, 3) - into(f, 80, 15)),
        }}
      />
      <Header index="THE BLACKOUT" />
      <Enter
        at={78}
        style={{
          position: "absolute",
          left: 80,
          top: 175,
          fontSize: 101,
          lineHeight: 1.02,
          ...sans,
        }}
      >
        GRID
        <br />
        <span style={{ color: c.amber }}>DISCONNECTED.</span>
      </Enter>
      <Enter
        at={103}
        style={{
          position: "absolute",
          left: 80,
          top: 480,
          fontSize: 31,
          ...mono,
          color: c.cyan,
        }}
      >
        CRITICAL SYSTEMS REMAIN ACTIVE.
      </Enter>
      <Foot />
    </Scene>
  );
};

const Failure = () => {
  const f = useCurrentFrame(),
    p = into(f, 10, 137),
    hit = into(f, 151, 12);
  const secs = Math.round(32832 * p);
  const stamp =
    f < 150
      ? `${String(Math.floor(secs / 3600)).padStart(2, "0")}:${String(Math.floor((secs % 3600) / 60)).padStart(2, "0")}:${String(secs % 60).padStart(2, "0")}`
      : "09:07:12";
  return (
    <Scene>
      <Still name="06-first-failure-ui" />
      <Dark alpha={0.7} />
      <Header index="FIRST FAILURE" />
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 135,
          fontSize: 25,
          ...mono,
          color: c.amber,
        }}
      >
        PHYSICS TRACE / 24 kWh BASELINE
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 235,
          fontSize: 76,
          ...sans,
        }}
      >
        THE CLOCK RUNS OUT.
      </div>
      <div
        style={{
          position: "absolute",
          left: 70,
          top: 420,
          fontSize: 238,
          lineHeight: 1,
          ...sans,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {stamp}
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 730,
          fontSize: 72,
          ...sans,
          color: c.red,
          opacity: hit,
        }}
      >
        CRITICAL POWER LOST.
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          right: 80,
          bottom: 150,
          height: 4,
          background: "#4f686a",
        }}
      >
        <div style={{ height: 4, width: `${p * 76}%`, background: c.amber }} />
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          bottom: 107,
          fontSize: 20,
          ...mono,
        }}
      >
        00:00:00
      </div>
      <div
        style={{
          position: "absolute",
          right: 80,
          bottom: 107,
          fontSize: 20,
          ...mono,
        }}
      >
        12-HOUR TEST WINDOW
      </div>
      <Foot />
    </Scene>
  );
};

const Compare = () => {
  const f = useCurrentFrame(),
    p = into(f, 29, 18),
    q = into(f, 123, 18);
  return (
    <Scene>
      <Still name="07-upgrade-ui" />
      <Dark alpha={0.8} />
      <Header index="ENGINEERING RESPONSE" />
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 180,
          fontSize: 80,
          ...sans,
        }}
      >
        MAKE THE SYSTEM <span style={{ color: c.amber }}>LAST.</span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 380,
          width: 800,
          height: 380,
          padding: "40px 50px",
          boxSizing: "border-box",
          borderTop: `4px solid ${c.red}`,
          background: "rgba(8,24,29,.95)",
          opacity: p,
          transform: `translateX(${(1 - p) * -40}px)`,
        }}
      >
        <div style={{ fontSize: 22, ...mono, color: c.red }}>
          BASELINE / PHYSICS VERIFIED
        </div>
        <div style={{ fontSize: 118, ...sans, marginTop: 20 }}>
          24 <span style={{ fontSize: 55 }}>kWh</span>
        </div>
        <div style={{ fontSize: 35, ...sans, color: c.red }}>
          FAILS AT 09:07:12
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          right: 80,
          top: 380,
          width: 800,
          height: 380,
          padding: "40px 50px",
          boxSizing: "border-box",
          borderTop: `4px solid ${c.cyan}`,
          background: "rgba(8,29,30,.95)",
          opacity: q,
          transform: `translateX(${(1 - q) * 40}px)`,
        }}
      >
        <div style={{ fontSize: 22, ...mono, color: c.cyan }}>
          UPGRADED / PHYSICS VERIFIED
        </div>
        <div style={{ fontSize: 118, ...sans, marginTop: 20 }}>
          36 <span style={{ fontSize: 55 }}>kWh</span>
        </div>
        <div style={{ fontSize: 35, ...sans, color: c.cyan }}>
          PASSES THE 12-HOUR TEST
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          bottom: 106,
          fontSize: 22,
          ...mono,
          color: c.muted,
        }}
      >
        SAME SCHOOL / SAME OUTAGE / TESTED CAPACITY CHANGED
      </div>
      <Foot />
    </Scene>
  );
};

const Search = () => {
  const f = useCurrentFrame(),
    hero = into(f, 163, 20);
  const rows: [number, string, boolean][] = [
    [24, "FAILED", false],
    [30, "FAILED", false],
    [32, "SUSTAINED", true],
    [36, "SUSTAINED", true],
  ];
  return (
    <Scene>
      <Still name="08-capacity-search-ui" />
      <Dark alpha={0.84} />
      <Header index="THE DECISION" />
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 180,
          fontSize: 82,
          ...sans,
        }}
      >
        FOUR DESIGNS. <span style={{ color: c.amber }}>ONE DECISION.</span>
      </div>
      <div style={{ position: "absolute", left: 80, top: 365, width: 900 }}>
        {rows.map(([v, label, pass], i) => {
          const p = into(f, 41 + i * 30, 13);
          return (
            <div
              key={v}
              style={{
                height: 103,
                display: "flex",
                alignItems: "center",
                borderBottom: "1px solid #567075",
                padding: "0 14px",
                opacity: p,
                transform: `translateX(${(1 - p) * -35}px)`,
                background:
                  v === 32 && hero ? "rgba(139,206,198,.15)" : "transparent",
              }}
            >
              <span style={{ width: 260, fontSize: 42, ...sans }}>{v} kWh</span>
              <span
                style={{ fontSize: 26, ...mono, color: pass ? c.cyan : c.red }}
              >
                {label}
              </span>
              <span
                style={{
                  marginLeft: "auto",
                  fontSize: 38,
                  color: pass ? c.cyan : c.red,
                }}
              >
                {pass ? "✓" : "×"}
              </span>
            </div>
          );
        })}
      </div>
      <div
        style={{
          position: "absolute",
          right: 72,
          top: 430,
          width: 770,
          opacity: hero,
          transform: `scale(${0.89 + 0.11 * hero})`,
        }}
      >
        <div style={{ fontSize: 192, lineHeight: 1, ...sans, color: c.cyan }}>
          32<span style={{ fontSize: 64 }}> kWh</span>
        </div>
        <div style={{ fontSize: 31, ...mono, lineHeight: 1.5 }}>
          SMALLEST PASSING
          <br />
          TESTED CAPACITY.
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          bottom: 108,
          fontSize: 22,
          ...mono,
          color: c.muted,
        }}
      >
        FOUR OFFICIAL PHYSICS RUNS / EXCLUSIVE 12-HOUR WINDOW
      </div>
      <Foot />
    </Scene>
  );
};

const Frontier = () => {
  const f = useCurrentFrame(),
    p = into(f, 8, 36),
    x = 868 + Math.min(1, Math.max(0, (f - 44) / 123)) * 845;
  return (
    <Scene>
      <Header index="FAILURE FRONTIER" />
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 235,
          width: 650,
          fontSize: 71,
          lineHeight: 1.05,
          ...sans,
        }}
      >
        273 PHYSICS-
        <br />
        VERIFIED
        <br />
        <span style={{ color: c.cyan }}>SCENARIOS.</span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 605,
          fontSize: 23,
          lineHeight: 1.6,
          ...mono,
          color: c.muted,
        }}
      >
        CHARGE × OUTAGE DURATION
        <br />
        <span style={{ color: c.cyan }}>SUSTAINED</span> /{" "}
        <span style={{ color: c.red }}>FAILURE OBSERVED</span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 790,
          top: 255,
          width: 1050,
          height: 700,
          overflow: "hidden",
          border: "1px solid #52706d",
          clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`,
        }}
      >
        <Img
          src={staticFile("film/09-frontier-grid.png")}
          style={{ width: "100%", height: "100%", objectFit: "fill" }}
        />
      </div>
      <div
        style={{
          position: "absolute",
          left: x,
          top: 355,
          width: 3,
          height: 500,
          background: "rgba(255,255,255,.55)",
          boxShadow: "0 0 12px white",
          opacity: into(f, 44, 15) * (1 - into(f, 177, 10)),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 80,
          bottom: 103,
          fontSize: 20,
          ...mono,
        }}
      >
        13 PHYSICAL RUNS / 273 CLASSIFIED CELLS
      </div>
      <Foot />
    </Scene>
  );
};

const Report = () => {
  const f = useCurrentFrame(),
    p = into(f, 9, 20);
  return (
    <Scene>
      <Still name="10-report-ui" />
      <Dark alpha={0.73} />
      <Header index="EVIDENCE REPORT" />
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 170,
          fontSize: 103,
          lineHeight: 1.03,
          ...sans,
        }}
      >
        EVERY RESULT.
        <br />
        <span style={{ color: c.amber }}>VERIFIABLE.</span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 475,
          width: 1200,
          padding: "28px 42px",
          boxSizing: "border-box",
          background: "rgba(5,22,27,.97)",
          borderLeft: `4px solid ${c.cyan}`,
          fontSize: 25,
          lineHeight: 1.8,
          ...mono,
          opacity: p,
          transform: `translateX(${(1 - p) * -45}px)`,
        }}
      >
        <div style={{ color: c.cyan }}>{"{"}</div>
        <div>
          {" "}
          <span style={{ color: c.amber }}>"physics_source"</span>: "Live local
          Physics API",
        </div>
        <div>
          {" "}
          <span style={{ color: c.amber }}>"model_version"</span>:
          "lastlight-dispatch-1.0.0",
        </div>
        <div>
          {" "}
          <span style={{ color: c.amber }}>"schema_version"</span>: "1.0.0"
        </div>
        <div style={{ color: c.cyan }}>{"}"}</div>
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          bottom: 105,
          fontSize: 21,
          ...mono,
        }}
      >
        ACTUAL JSON REPORT FIELDS / INPUTS + TRACE + RESULTS
      </div>
      <Foot />
    </Scene>
  );
};

const Brand = () => {
  const f = useCurrentFrame(),
    p = into(f, 5, 16),
    q = into(f, 24, 16),
    fade = 1 - into(f, 73, 16);
  return (
    <Scene>
      <Still name="02-school-hero-ui" scale={1.08} />
      <Dark alpha={0.94} />
      <AbsoluteFill style={{ opacity: fade }}>
        <div
          style={{
            position: "absolute",
            left: 80,
            top: 313,
            width: 7,
            height: 360,
            background: c.amber,
            transform: `scaleY(${p})`,
            transformOrigin: "top",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 125,
            top: 255,
            fontSize: 183,
            ...sans,
            opacity: p,
          }}
        >
          LASTLIGHT<span style={{ color: c.amber }}>.</span>
        </div>
        <div
          style={{
            position: "absolute",
            left: 134,
            top: 515,
            fontSize: 62,
            lineHeight: 1.35,
            ...sans,
            opacity: q,
          }}
        >
          KNOW THE FAILURE
          <br />
          BEFORE IT HAPPENS.
        </div>
        <div
          style={{
            position: "absolute",
            left: 134,
            bottom: 106,
            fontSize: 23,
            ...mono,
            color: c.cyan,
            opacity: q,
          }}
        >
          CURSED / LOGOS HACKATHON 2026
        </div>
      </AbsoluteFill>
    </Scene>
  );
};

export const LastlightFilm: React.FC = () => (
  <Scene>
    <Sequence durationInFrames={120}>
      <Hook />
    </Sequence>
    <Sequence from={120} durationInFrames={240}>
      <Intro />
    </Sequence>
    <Sequence from={360} durationInFrames={270}>
      <Blackout />
    </Sequence>
    <Sequence from={630} durationInFrames={270}>
      <Failure />
    </Sequence>
    <Sequence from={900} durationInFrames={270}>
      <Compare />
    </Sequence>
    <Sequence from={1170} durationInFrames={270}>
      <Search />
    </Sequence>
    <Sequence from={1440} durationInFrames={210}>
      <Frontier />
    </Sequence>
    <Sequence from={1650} durationInFrames={120}>
      <Report />
    </Sequence>
    <Sequence from={1770} durationInFrames={90}>
      <Brand />
    </Sequence>
    <Audio src={staticFile("film/original-full.wav")} />
  </Scene>
);
