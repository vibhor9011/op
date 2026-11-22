import { Bar, BarChart, CartesianGrid, Area, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell } from "recharts";

const AX = { fontSize: 10, fill: "#657681", fontFamily: "JetBrains Mono, monospace" };
const TT = { background: "#fbfcfa", border: "1px solid #cbd6d8", borderRadius: 2, fontSize: 11, fontFamily: "JetBrains Mono, monospace", color: "#162c3b" };

export default function TelemetryCharts({ district, day }) {
  if (!district) return null;
  const rain = district.rain_daily_mm.map((v, i) => ({ d: ["D-2", "D-1", "D0"][i], mm: v }));
  const fc = district.forecast.map((f) => ({ hour: f.hour, low: f.low * 100, band: (f.high - f.low) * 100, mid: f.mid * 100, high: f.high * 100 }));

  return (
    <div className="h-[215px] shrink-0 border-t border-line bg-panel grid grid-cols-12 min-h-0">
      <section className="col-span-5 max-md:col-span-12 border-r border-line px-3 pt-2 pb-1 flex flex-col min-w-0">
        <div className="flex items-baseline justify-between">
          <span className="lbl">Rainfall build-up · {district.name}</span>
          <span className="num text-[12px]">
            CUMULATIVE: <b>{district.rain_cumulative_mm.toFixed(1)}</b> mm
          </span>
        </div>
        <div className="flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rain} margin={{ top: 14, right: 8, left: -18, bottom: 0 }}>
              <CartesianGrid stroke="#d6dedf" vertical={false} />
              <XAxis dataKey="d" tick={AX} axisLine={{ stroke: "#cbd6d8" }} tickLine={false} />
              <YAxis tick={AX} axisLine={false} tickLine={false} unit="" />
              <Tooltip contentStyle={TT} cursor={{ fill: "#e9f0f2" }} formatter={(v) => [`${Number(v).toFixed(1)} mm`, "daily"]} />
              <Bar dataKey="mm" radius={0} isAnimationActive={false} label={{ position: "top", fill: "#27495a", fontSize: 10, fontFamily: "JetBrains Mono, monospace", formatter: (v) => v.toFixed(0) }}>
                {rain.map((_, i) => (
                  <Cell key={i} fill={i === 2 ? "#1685a0" : "#8eb5bf"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="col-span-7 max-md:hidden px-3 pt-2 pb-1 flex flex-col min-w-0">
        <div className="flex items-baseline justify-between">
          <span className="lbl">Flood risk index · 0–72 h · P10–P90 band</span>
          <span className="num text-[12px]">
            D+{day}: <b>{(district.p_mid * 100).toFixed(0)}%</b> ({(district.p_low * 100).toFixed(0)}–{(district.p_high * 100).toFixed(0)})
          </span>
        </div>
        <div className="flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={fc} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid stroke="#d6dedf" vertical={false} />
              <XAxis dataKey="hour" type="number" domain={[0, 72]} ticks={[0, 12, 24, 36, 48, 60, 72]} tickFormatter={(h) => `${h}h`} tick={AX} axisLine={{ stroke: "#cbd6d8" }} tickLine={false} />
              <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={AX} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={TT}
                formatter={(v, k, p) => {
                  if (k === "mid") return [`${Number(v).toFixed(0)}% (${p.payload.low.toFixed(0)}–${p.payload.high.toFixed(0)})`, "P50 (P10–P90)"];
                  return null;
                }}
                itemSorter={() => 0}
                labelFormatter={(h) => `+${h} h`}
              />
              <Area dataKey="low" stackId="b" stroke="none" fill="transparent" isAnimationActive={false} legendType="none" tooltipType="none" />
              <Area dataKey="band" stackId="b" stroke="none" fill="#1685a0" fillOpacity={0.18} isAnimationActive={false} tooltipType="none" />
              <ReferenceLine x={day * 24} stroke="#657681" strokeDasharray="3 3" label={{ value: `D+${day}`, fill: "#657681", fontSize: 10, position: "insideTopRight" }} />
              <Line dataKey="mid" stroke="#c77a17" strokeWidth={1.8} dot={false} isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}
