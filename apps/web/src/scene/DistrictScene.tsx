import { useState } from 'react'
import type { SiteId } from '../features/sites'
import districtPlate from '../assets/district-night.webp'

type Props = { selected: SiteId; layer: 'night' | 'systems'; onSelect: (id: SiteId) => void }
type Block = { x: number; y: number; w: number; h: number; z: number; tone?: number }

const blocks: Block[] = [
  { x: 491, y: 91, w: 80, h: 35, z: 20 }, { x: 598, y: 80, w: 48, h: 68, z: 28 },
  { x: 684, y: 82, w: 90, h: 39, z: 23 }, { x: 800, y: 76, w: 72, h: 58, z: 31 },
  { x: 913, y: 98, w: 48, h: 67, z: 20 }, { x: 1018, y: 92, w: 65, h: 44, z: 18 },
  { x: 446, y: 178, w: 51, h: 80, z: 22 }, { x: 530, y: 180, w: 97, h: 48, z: 27 },
  { x: 665, y: 176, w: 61, h: 75, z: 25 }, { x: 766, y: 183, w: 88, h: 53, z: 34 },
  { x: 889, y: 190, w: 73, h: 71, z: 19 }, { x: 1004, y: 183, w: 80, h: 44, z: 28 },
  { x: 445, y: 323, w: 75, h: 44, z: 24 }, { x: 555, y: 309, w: 82, h: 68, z: 31 },
  { x: 888, y: 320, w: 90, h: 49, z: 27 }, { x: 1017, y: 314, w: 61, h: 76, z: 29 },
  { x: 449, y: 437, w: 65, h: 48, z: 25 }, { x: 544, y: 438, w: 94, h: 37, z: 18 },
  { x: 854, y: 462, w: 113, h: 46, z: 31 }, { x: 1007, y: 451, w: 72, h: 59, z: 22 },
  { x: 457, y: 572, w: 75, h: 58, z: 23 }, { x: 565, y: 568, w: 55, h: 71, z: 24 },
  { x: 671, y: 577, w: 93, h: 42, z: 28 }, { x: 803, y: 564, w: 68, h: 65, z: 20 },
  { x: 909, y: 571, w: 73, h: 56, z: 29 }, { x: 1010, y: 558, w: 83, h: 71, z: 26 },
]

function BlockShape({ x, y, w, h, z, tone = 0 }: Block) {
  const roof = tone ? '#172a34' : '#1a2c37'
  return <g className="district-block">
    <path d={'M' + x + ' ' + y + 'h' + w + 'v' + h + 'h-' + w + 'z'} fill={roof} stroke="#40545b" strokeWidth="1.2" />
    <path d={'M' + x + ' ' + (y + h) + 'l' + z + ' ' + z * .36 + 'h' + w + 'l-' + z + ' -' + z * .36 + 'z'} fill="#0c1922" stroke="#293b44" strokeWidth="1" />
    <path d={'M' + (x + w) + ' ' + y + 'l' + z + ' ' + z * .36 + 'v' + h + 'l-' + z + ' -' + z * .36 + 'z'} fill="#101f28" stroke="#293b44" strokeWidth="1" />
    <path d={'M' + (x + 7) + ' ' + (y + 7) + 'h' + (w - 14) + 'v' + (h - 14) + 'h-' + (w - 14)} fill="none" stroke="#2e444e" strokeWidth=".7" />
    {w > 70 && <path d={'M' + (x + 17) + ' ' + (y + h / 2) + 'h' + (w - 34)} stroke="#51605a" strokeWidth="1" opacity=".55" />}
    {[0, 1, 2].map(i => <rect key={i} x={x + 10 + i * (w - 20) / 3} y={y + h + 4 + i * 1.4} width="7" height="2" fill="#c58a4b" opacity={i === 1 ? .55 : .24} />)}
  </g>
}

const fallbackPositions: Record<SiteId, { x: number; y: number; label: string }> = {
  school: { x: 751, y: 400, label: '01 / SCHOOL' },
  clinic: { x: 854, y: 215, label: '02 / CLINIC' },
  business: { x: 582, y: 349, label: '03 / BUSINESS' },
  residential: { x: 729, y: 602, label: '04 / RESIDENTIAL' },
}
const platePositions: typeof fallbackPositions = {
  school: { x: 748, y: 345, label: '01 / SCHOOL' },
  clinic: { x: 965, y: 167, label: '02 / CLINIC' },
  business: { x: 976, y: 453, label: '03 / BUSINESS' },
  residential: { x: 820, y: 615, label: '04 / RESIDENTIAL' },
}

export function DistrictScene({ selected, layer, onSelect }: Props) {
  const [plateFailed, setPlateFailed] = useState(false)
  const sitePositions = plateFailed ? fallbackPositions : platePositions
  const focus = sitePositions[selected]
  const labelLeft = focus.x > 850
  const labelX = labelLeft ? focus.x - 254 : focus.x + 59
  return <div className={'scene scene--' + layer + (plateFailed ? '' : ' scene--plate')}>
    {!plateFailed && <img className="scene-plate" src={districtPlate} alt="" onError={() => setPlateFailed(true)} />}
    <svg viewBox="0 0 1200 800" role="img" aria-label="Original synthetic bird's-eye district composition with selectable facility sites" preserveAspectRatio="xMidYMid slice">
      <defs>
        <radialGradient id="ground"><stop stopColor="#18303a" /><stop offset=".58" stopColor="#101e27" /><stop offset="1" stopColor="#080f17" /></radialGradient>
        <radialGradient id="light"><stop stopColor="#d89a55" stopOpacity=".33" /><stop offset="1" stopColor="#d89a55" stopOpacity="0" /></radialGradient>
        <radialGradient id="streetLight"><stop stopColor="#f2ae54" stopOpacity=".68" /><stop offset=".22" stopColor="#e69d4d" stopOpacity=".2" /><stop offset="1" stopColor="#d89a55" stopOpacity="0" /></radialGradient>
        <pattern id="grain" width="27" height="27" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".65" fill="#a8c1bc" opacity=".16" /></pattern>
        <pattern id="solar" width="14" height="10" patternUnits="userSpaceOnUse"><rect x="1" y="1" width="11" height="7" fill="#192d36" stroke="#536e71" strokeWidth=".6" /></pattern>
      </defs>
      <g className="vector-fallback">
      <rect width="1200" height="800" fill="url(#ground)" />
      <rect width="1200" height="800" fill="url(#grain)" />
      <g opacity=".25" fill="none" stroke="#48616a" strokeWidth="1">
        <path d="M 260 40 C 360 110 345 215 280 280 S 242 470 355 548 S 409 700 346 800" />
        <path d="M 290 40 C 390 110 370 215 309 280 S 270 470 382 548 S 438 700 378 800" />
        <path d="M 320 40 C 422 110 397 215 337 280 S 302 470 408 548 S 466 700 410 800" />
        <path d="M 1120 0 C 1070 143 1150 240 1090 347 S 1145 537 1104 800" />
        <path d="M 1150 0 C 1100 143 1180 240 1120 347 S 1175 537 1134 800" />
      </g>
      <g className="roads">
        <path d="M425 0v800 M1107 0v800 M0 276h1200 M0 536h1200" stroke="#34454a" strokeWidth="30" opacity=".35" />
        <path d="M425 0v800 M1107 0v800 M0 276h1200 M0 536h1200" stroke="#718076" strokeWidth="1.4" opacity=".43" />
        <path d="M425 0v800 M1107 0v800 M0 276h1200 M0 536h1200" stroke="#718076" strokeWidth="1" strokeDasharray="3 25" opacity=".53" />
      </g>
      <g className="streetlights">
        {[[468,278],[635,278],[864,278],[1064,278],[468,535],[645,535],[839,535],[1060,535],[1107,400],[426,389]].map(([x,y],i) =>
          <g key={i}><circle cx={x} cy={y} r="33" fill="url(#streetLight)" /><circle cx={x} cy={y} r="2.4" fill="#edb370" /></g>)}
      </g>
      <g opacity=".38">
        <circle cx="817" cy="402" r="188" fill="url(#light)" />
        <circle cx="602" cy="345" r="86" fill="url(#light)" />
        <circle cx="917" cy="207" r="75" fill="url(#light)" />
      </g>
      <g className="tree-field" fill="#142c31" stroke="#355047" strokeWidth=".6">
        {Array.from({ length: 48 }, (_, i) => {
          const x = 463 + (i * 71) % 617
          const y = 127 + (i * 113) % 520
          return <circle key={i} cx={x} cy={y} r={2.5 + i % 4} opacity=".72" />
        })}
      </g>
      {blocks.map((block, index) => <BlockShape key={index} {...block} tone={index % 3} />)}
      <g className="campus">
        <rect x="650" y="313" width="190" height="157" fill="#192d33" stroke="#4b625d" strokeWidth="1.5" />
        <path d="M650 439h190 M671 313v157 M817 313v157" stroke="#35534f" strokeWidth="1" />
        <path d="M656 321h35v107h-35z" fill="#203f3c" stroke="#477169" opacity=".74" />
        <path d="M665 324v101 M657 373h32" stroke="#7b9a79" opacity=".33" />
        <path d="M660 340h28 M660 359h28 M660 390h28 M660 410h28" stroke="#a0b8a0" opacity=".25" />
        <path d="M690 341h106v68H690z" fill="#223942" stroke="#9d916e" strokeWidth="1.6" />
        <path d="M690 409l21 11h106l-21-11z" fill="#0f222b" stroke="#47575b" />
        <path d="M796 341l21 11v68l-21-11z" fill="#142933" stroke="#47575b" />
        <path d="M700 350h85v50h-85z" fill="url(#solar)" opacity=".9" />
        <path d="M704 404h78" stroke="#f2ae54" strokeWidth="2" opacity=".7" />
        <rect x="702" y="414" width="90" height="11" fill="#18272d" stroke="#725c43" strokeWidth=".7" />
        {[0,1,2,3,4,5,6].map(i => <rect key={i} x={706+i*12} y="417" width="7" height="3" fill="#dfaa68" opacity={i%3===0?.95:.52} />)}
        <path d="M687 446h111v14H687z" fill="#1b343a" stroke="#5c7164" strokeWidth=".8" />
        <path d="M690 453h105 M743 447v12" stroke="#789489" strokeWidth=".6" opacity=".7" />
        <circle cx="743" cy="453" r="5" fill="none" stroke="#789489" strokeWidth=".6" />
        <path d="M682 431h112" stroke="#ba8a54" strokeWidth="2" opacity=".65" />
        <path d="M688 438h68 M767 438h25" stroke="#dcaa68" strokeWidth="2" opacity=".7" />
        <rect x="676" y="333" width="9" height="7" fill="#d4a267" opacity=".75" />
        <rect x="756" y="431" width="10" height="9" fill="#b57945" />
        <path d="M660 323h177v143H660z" fill="none" stroke="#be9e6c" strokeWidth=".7" strokeDasharray="3 6" opacity=".65" />
      </g>
      </g>
      {layer === 'systems' && selected === 'school' && <g className="system-overlay" fill="none" stroke="#70d4c4" strokeWidth="2">
        <path d={'M' + (focus.x - 10) + ' ' + (focus.y - 20) + 'v55h30'} strokeDasharray="5 6" />
        <circle cx={focus.x - 10} cy={focus.y - 20} r="7" fill="#70d4c4" fillOpacity=".12" />
        <circle cx={focus.x + 20} cy={focus.y + 35} r="7" fill="#70d4c4" fillOpacity=".12" />
        <text x={focus.x + 96} y={focus.y + 26} fill="#70d4c4" stroke="none" fontSize="11" letterSpacing="2">PV / BATTERY · SCHEMATIC</text>
      </g>}
      {layer === 'systems' && selected !== 'school' && <g className="system-overlay" fill="none" stroke="#70d4c4" strokeWidth="1">
        <circle cx={focus.x} cy={focus.y} r="48" strokeDasharray="3 6" opacity=".6" />
        <text x={Math.min(focus.x + 52, 885)} y={focus.y + 48} fill="#70d4c4" stroke="none" fontSize="10" letterSpacing="1.3">EQUIPMENT GEOMETRY PENDING</text>
      </g>}
      <g className="site-markers" fill="none">
        {(Object.keys(sitePositions) as SiteId[]).map(id => {
          const p = sitePositions[id]
          const isSelected = selected === id
          return <g key={id} className={'marker ' + (isSelected ? 'active' : '')} role="button" tabIndex={0} aria-label={'Select ' + id + ' on map'} onClick={() => onSelect(id)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(id) } }} style={{ cursor: 'pointer' }}>
            <circle cx={p.x} cy={p.y} r={isSelected ? 38 : 24} stroke={isSelected ? '#f2ae54' : '#9cb5ad'} strokeWidth={isSelected ? 1.5 : 1} opacity={isSelected ? .78 : .45} strokeDasharray={isSelected ? 'none' : '3 5'} />
            <circle cx={p.x} cy={p.y} r="4" fill={isSelected ? '#f2ae54' : '#8eaba9'} />
            <circle cx={p.x} cy={p.y} r="18" fill="transparent" />
          </g>
        })}
      </g>
      <g className="focus-label">
        <path d={labelLeft ? 'M' + (focus.x - 31) + ' ' + (focus.y - 28) + 'l-28 -25h-134' : 'M' + (focus.x + 31) + ' ' + (focus.y - 28) + 'l28 -25h134'} fill="none" stroke="#f2ae54" strokeWidth="1" />
        <rect x={labelX} y={focus.y - 75} width="195" height="22" fill="#0c1820" stroke="#775d42" />
        <text x={labelX + 10} y={focus.y - 60} fill="#f2ae54" fontSize="11" letterSpacing="1.5">{focus.label}</text>
      </g>
      <path d="M0 18h1182v764H18V18" fill="none" stroke="#607875" strokeWidth=".7" opacity=".25" />
    </svg>
    <div className="scene-coordinates">DISTRICT 01 / 42.8746°N — 74.5698°E</div>
  </div>
}
