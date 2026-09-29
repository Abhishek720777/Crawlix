import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Home.css";

const MODES = [
  { k: "E-Commerce & Pricing", d: "Track prices, stock and seller changes across storefronts.", f: ["price", "sku", "stock", "rating"] },
  { k: "News & Sentiment", d: "Pull headlines, authors and tone from publishers at scale.", f: ["headline", "author", "published", "sentiment"] },
  { k: "Schema.org / JSON-LD", d: "Ingest structured data that sites already publish.", f: ["@type", "name", "offers", "address"] },
  { k: "Generic Web Content", d: "Point custom CSS selectors at anything else.", f: ["title", "h1", "links", "meta"] },
];

const STAGES = [
  { t: "Define the job", d: "Add target URLs, set depth and page limits, pick a crawler type and queue priority, then add your CSS selectors." },
  { t: "Queue it on Redis", d: "Your job is split into tasks and pushed to a Redis broker, ordered by priority." },
  { t: "Workers fan out", d: "Celery workers running in separate Docker containers pick up tasks and crawl in parallel." },
  { t: "Records land", d: "Each page becomes a structured record you can filter, sort and export as JSON or CSV." },
  { t: "Report writes itself", d: "When the job ends, Crawlix summarizes it: metrics, top domains and HTTP status breakdown." },
];

const ROWS = [
  ["shop.northwind.io/p/4412", "Trail runner GTX", "₹8,499", "200", "e-com"],
  ["daily-ledger.com/2026/09/rates", "RBI holds repo rate", "+0.42", "200", "news"],
  ["shop.northwind.io/p/4413", "Merino base layer", "₹3,299", "200", "e-com"],
  ["cafe-tulsi.in/menu", "Restaurant · Indiranagar", "4.6★", "200", "jsonld"],
  ["daily-ledger.com/2026/09/oil", "Crude slips on supply", "-0.18", "301", "news"],
  ["cafe-tulsi.in/about", "Restaurant · Koramangala", "4.4★", "200", "jsonld"],
];

const seed = () => [
  { id: "worker-01", cpu: 62, ram: 48, act: 7, done: 1842 },
  { id: "worker-02", cpu: 35, ram: 41, act: 4, done: 1610 },
  { id: "worker-03", cpu: 88, ram: 71, act: 9, done: 2097 },
  { id: "worker-04", cpu: 12, ram: 29, act: 1, done: 903 },
  { id: "worker-05", cpu: 54, ram: 56, act: 6, done: 1388 },
];

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

export default function Home() {
  const nav = useNavigate();
  const root = useRef(null);
  const pin = useRef(null);
  const [stage, setStage] = useState(0);
  const [mode, setMode] = useState(0);
  const [filter, setFilter] = useState("all");
  const [nodes, setNodes] = useState(seed);
  const [pages, setPages] = useState(128440);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let raf = 0;
    const tick = () => {
      raf = 0;
      const vh = window.innerHeight;
      const el = root.current;
      if (!el) return;
      el.style.setProperty("--sy", window.scrollY);
      el.querySelectorAll("[data-speed]").forEach((n) => {
        const r = n.parentElement.getBoundingClientRect();
        const off = (r.top + r.height / 2 - vh / 2) * -parseFloat(n.dataset.speed);
        const rot = n.dataset.rot ? `rotate(${off * parseFloat(n.dataset.rot)}deg)` : "";
        n.style.transform = still ? "none" : `translate3d(0,${off}px,0) ${rot}`;
      });
      if (pin.current) {
        const r = pin.current.getBoundingClientRect();
        const p = clamp(-r.top / (r.height - vh), 0, 1);
        el.style.setProperty("--p", p);
        setStage(Math.min(STAGES.length - 1, Math.floor(p * STAGES.length)));
      }
      el.querySelectorAll(".rv").forEach((n) => {
        const r = n.getBoundingClientRect();
        if (r.top < vh * 0.88) n.classList.add("in");
      });
    };
    const on = () => !raf && (raf = requestAnimationFrame(tick));
    tick();
    window.addEventListener("scroll", on, { passive: true });
    window.addEventListener("resize", on);
    return () => {
      window.removeEventListener("scroll", on);
      window.removeEventListener("resize", on);
      cancelAnimationFrame(raf);
    };
  }, []);

  useEffect(() => {
    const t = setInterval(() => {
      setNodes((ns) =>
        ns.map((n) => ({
          ...n,
          cpu: clamp(n.cpu + Math.round((Math.random() - 0.5) * 24), 6, 97),
          ram: clamp(n.ram + Math.round((Math.random() - 0.5) * 8), 20, 90),
          act: clamp(n.act + Math.round((Math.random() - 0.5) * 4), 0, 12),
          done: n.done + Math.floor(Math.random() * 6),
        }))
      );
      setPages((p) => p + Math.floor(Math.random() * 40 + 10));
    }, 1300);
    return () => clearInterval(t);
  }, []);

  const rows = ROWS.filter((r) => filter === "all" || r[4] === filter);
  const go = (p) => () => nav(p);

  return (
    <div
      className="cx"
      ref={root}
      onMouseMove={(e) =>
        setMouse({ x: e.clientX / window.innerWidth - 0.5, y: e.clientY / window.innerHeight - 0.5 })
      }
    >
      <header className="cx-nav">
        <a className="cx-logo" href="#top">
          <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">
            <circle cx="16" cy="16" r="4" fill="currentColor" />
            <g stroke="currentColor" strokeWidth="2" fill="none">
              <path d="M16 12V3M16 20v9M12 16H3M20 16h9M13 13 6 6M19 19l7 7M19 13l7-7M13 19l-7 7" />
            </g>
          </svg>
          Crawlix
        </a>
        <nav>
          <a href="#how">How it works</a>
          <a href="#mesh">Node Mesh</a>
          <a href="#data">Data</a>
          <a href="#modes">Modes</a>
        </nav>
        <div className="cx-navbtn">
          <button className="btn ghost" onClick={go("/login")}>Log in</button>
          <button className="btn solid" onClick={go("/register")}>Start crawling</button>
        </div>
      </header>

      {/* HERO */}
      <section className="hero" id="top">
        <div className="hero-web" aria-hidden="true">
          <svg data-speed="0.05" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice" style={{ translate: `${mouse.x * -14}px ${mouse.y * -14}px` }}>
            {[[180,160,520,300],[520,300,860,180],[520,300,640,560],[640,560,1010,520],[860,180,1010,520],[180,160,240,520],[240,520,640,560],[860,180,1100,330],[1010,520,1100,330]].map((l, i) => (
              <line key={i} x1={l[0]} y1={l[1]} x2={l[2]} y2={l[3]} className="wire" style={{ animationDelay: `${i * 0.25}s` }} />
            ))}
            {[[180,160],[520,300],[860,180],[640,560],[1010,520],[240,520],[1100,330]].map((c, i) => (
              <circle key={i} cx={c[0]} cy={c[1]} r={i % 3 === 0 ? 9 : 6} className="pt" style={{ animationDelay: `${i * 0.4}s` }} />
            ))}
          </svg>
          <span data-speed="0.18" className="blob b1" />
          <span data-speed="-0.12" className="blob b2" />
        </div>

        <div className="hero-copy">
          <p className="pill"><i /> {pages.toLocaleString()} pages crawled while you read this</p>
          <h1>
            <span className="ln"><b>Crawl the</b></span>
            <span className="ln"><b>whole web,</b></span>
            <span className="ln"><b>without a single</b></span>
            <span className="ln"><b className="strike">bottleneck.</b></span>
          </h1>
          <p className="sub">
            Crawlix spreads your scraping jobs across a mesh of Celery workers, turns pages into clean records,
            and writes the intelligence report when the crawl is done.
          </p>
          <div className="cta-row">
            <button className="btn solid big" onClick={go("/register")}>Create free account</button>
            <button className="btn ghost big" onClick={go("/login")}>I already have one</button>
          </div>
        </div>

        <div className="hero-card" data-speed="-0.06" style={{ translate: `${mouse.x * 18}px ${mouse.y * 12}px` }}>
          <div className="hc-top"><span className="dot live" /> job #2291 · running</div>
          <div className="hc-url">https://shop.northwind.io</div>
          <div className="hc-bar"><span /></div>
          <div className="hc-stats"><div><b>depth 3</b>max</div><div><b>500</b>pages</div><div><b>high</b>priority</div></div>
          <code>{"{ price: '.pdp-price', title: 'h1' }"}</code>
        </div>
      </section>

      {/* MARQUEE */}
      <div className="marq" aria-hidden="true">
        <div>
          {[0, 1].map((n) => (
            <span key={n}>
              Celery workers · Redis broker · Docker nodes · CSS selectors · JSON-LD · Live heartbeats · JSON &amp; CSV export · Intelligence reports ·{" "}
            </span>
          ))}
        </div>
      </div>

      {/* PINNED PIPELINE */}
      <section className="pin" id="how" ref={pin}>
        <div className="pin-in">
          <div className="pin-l">
            <h2>From URL to insight in five moves</h2>
            <div className="stages">
              {STAGES.map((s, i) => (
                <div key={s.t} className={`stg ${i === stage ? "on" : ""} ${i < stage ? "past" : ""}`}>
                  <span className="n">{i + 1}</span>
                  <div><h3>{s.t}</h3><p>{s.d}</p></div>
                </div>
              ))}
            </div>
          </div>
          <div className="pin-r" aria-hidden="true">
            <div className="rail"><span style={{ height: "calc(var(--p) * 100%)" }} /></div>
            <div className="pipe">
              <div className={`pn ${stage >= 0 ? "lit" : ""}`}>Job</div>
              <div className={`pn ${stage >= 1 ? "lit" : ""}`}>Redis</div>
              <div className="fan">
                {[0, 1, 2].map((i) => <div key={i} className={`pn sm ${stage >= 2 ? "lit" : ""}`}>W{i + 1}</div>)}
              </div>
              <div className={`pn ${stage >= 3 ? "lit" : ""}`}>Records</div>
              <div className={`pn ${stage >= 4 ? "lit" : ""}`}>Report</div>
            </div>
          </div>
        </div>
      </section>

      {/* NODE MESH */}
      <section className="sec mesh" id="mesh">
        <div className="sec-h rv">
          <h2>Watch every worker breathe</h2>
          <p>The Node Mesh shows each Celery node's CPU, RAM, active and completed tasks, plus its heartbeat, refreshed live.</p>
        </div>
        <div className="mesh-wrap">
          <div className="para-bg" data-speed="0.14" data-rot="0.01" />
          <div className="panel rv">
            <div className="p-head"><span className="dot live" /> Node Mesh <em>{nodes.length} nodes online</em></div>
            {nodes.map((n) => (
              <div className="node" key={n.id}>
                <div className="nid"><span className={`dot ${n.cpu > 85 ? "hot" : "live"}`} />{n.id}</div>
                <div className="meter"><label>CPU {n.cpu}%</label><i><s style={{ width: n.cpu + "%" }} className={n.cpu > 85 ? "hot" : ""} /></i></div>
                <div className="meter"><label>RAM {n.ram}%</label><i><s style={{ width: n.ram + "%" }} /></i></div>
                <div className="tk"><b>{n.act}</b> active</div>
                <div className="tk"><b>{n.done.toLocaleString()}</b> done</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DATA EXPLORER */}
      <section className="sec data" id="data">
        <div className="data-grid">
          <div className="rv">
            <h2>Every record, filterable and exportable</h2>
            <p>Search the extracted data in the Data Explorer, narrow it by crawl type, then download the lot as JSON or CSV.</p>
            <div className="chips">
              {["all", "e-com", "news", "jsonld"].map((f) => (
                <button key={f} className={`chip ${filter === f ? "on" : ""}`} onClick={() => setFilter(f)}>{f}</button>
              ))}
            </div>
            <div className="cta-row"><span className="tag">Export .json</span><span className="tag">Export .csv</span></div>
          </div>
          <div className="panel table rv" data-speed="0.04">
            <div className="tr th"><span>Source</span><span>Extracted</span><span>Value</span><span>HTTP</span></div>
            {rows.map((r) => (
              <div className="tr" key={r[0]}>
                <span className="u">{r[0]}</span><span>{r[1]}</span><span>{r[2]}</span>
                <span className={r[3] === "200" ? "ok" : "warn"}>{r[3]}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* REPORT */}
      <section className="sec report">
        <div className="rep-stack">
          <div className="rcard r1 rv" data-speed="0.1">
            <h4>Job summary</h4>
            <p>4,812 pages fetched in 6m 41s across 5 workers. 97.3% returned a usable record.</p>
          </div>
          <div className="rcard r2 rv" data-speed="-0.05">
            <h4>Top domains</h4>
            {[["northwind.io", 74], ["daily-ledger.com", 52], ["cafe-tulsi.in", 31]].map((d) => (
              <div className="hb" key={d[0]}><span>{d[0]}</span><i><s style={{ "--w": d[1] + "%" }} /></i></div>
            ))}
          </div>
          <div className="rcard r3 rv" data-speed="0.16">
            <h4>HTTP statuses</h4>
            <div className="st"><b>200</b> 4,682 <b>301</b> 96 <b>404</b> 34</div>
          </div>
        </div>
        <div className="rv rep-copy">
          <h2>The report arrives before you ask for it</h2>
          <p>When a job completes, Crawlix generates an Intelligence Report with summaries, headline metrics, top domains and the most common HTTP statuses.</p>
        </div>
      </section>

      {/* MODES */}
      <section className="sec modes" id="modes">
        <div className="sec-h rv"><h2>Four crawl modes, one job form</h2></div>
        <div className="modes-grid rv">
          <div className="tabs">
            {MODES.map((m, i) => (
              <button key={m.k} className={i === mode ? "on" : ""} onClick={() => setMode(i)}>{m.k}</button>
            ))}
          </div>
          <div className="mode-body" key={mode}>
            <p>{MODES[mode].d}</p>
            <div className="fields">{MODES[mode].f.map((f) => <span key={f}>{f}</span>)}</div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="final">
        <div className="fweb" data-speed="0.12" aria-hidden="true" />
        <h2 className="rv">Your first crawl is one form away.</h2>
        <div className="cta-row rv">
          <button className="btn solid big" onClick={go("/register")}>Create free account</button>
          <button className="btn ghost big" onClick={go("/login")}>Log in</button>
        </div>
      </section>

      <footer className="cx-foot">
        <span>© 2026 Crawlix</span>
        <span>Distributed scraping and intelligence.</span>
      </footer>
    </div>
  );
}
