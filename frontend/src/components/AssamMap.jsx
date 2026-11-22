import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { getRiskColor } from "../design/tokens.js";
import { Layers, Eye, EyeOff, ZoomIn, Sliders, ShieldCheck } from "lucide-react";

export default function AssamMap({
  dash,
  extent,
  selectedId,
  onSelect,
  layers,
  sarOpacity = 0.75,
  onSarOpacityChange = null
}) {
  const elRef = useRef(null);
  const mapRef = useRef(null);
  const riskRef = useRef(null);
  const unRef = useRef(null);
  const sarRef = useRef(null);
  const robustMarkerRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    const el = elRef.current;
    if (!el) return;

    // Initialize Leaflet map with dark styling and Canvas acceleration for 60fps
    const map = L.map(el, {
      center: [26.45, 92.85],
      zoom: 7,
      preferCanvas: true,
      zoomControl: false,
      attributionControl: true,
      maxBounds: [[23.5, 89.0], [29.0, 96.5]],
      minZoom: 6,
      maxZoom: 12
    });

    L.control.zoom({ position: "topright" }).addTo(map);

    // Dark tiles as an enhancement; falls back gracefully to dark canvas if offline
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: "&copy; OpenStreetMap &copy; CARTO",
      subdomains: "abcd",
      maxZoom: 12,
      errorTileUrl: "" // Silent offline fallback
    }).addTo(map);

    riskRef.current = L.layerGroup().addTo(map);
    sarRef.current = L.layerGroup().addTo(map);
    unRef.current = L.layerGroup().addTo(map);
    robustMarkerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    const ro = new ResizeObserver(() => map.invalidateSize());
    ro.observe(el);

    return () => {
      ro.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update Choropleth, Districts, and Labels
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !dash || !dash.districts) return;

    const byId = Object.fromEntries(dash.districts.map((d) => [d.id, d]));
    riskRef.current.clearLayers();
    unRef.current.clearLayers();
    robustMarkerRef.current.clearLayers();

    if (dash.geojson && dash.geojson.features) {
      dash.geojson.features.forEach((feat) => {
        const zid = feat.properties?.geometry_id || feat.properties?.id;
        const d = byId[zid];
        if (!d) return;

        const isSelected = d.id === selectedId;
        const fillColor = layers.risk ? getRiskColor(d.priority) : "#182542";
        const fillOpacity = layers.risk ? (isSelected ? 0.85 : 0.65) : 0.2;

        const poly = L.geoJSON(feat, {
          style: {
            color: isSelected ? "#00f0ff" : "#334155",
            weight: isSelected ? 2.5 : 1.1,
            fillColor,
            fillOpacity,
            dashArray: isSelected ? "" : ""
          }
        });

        poly.on("click", () => onSelectRef.current(d.id));

        // Rich Tooltip
        const tipContent = `
          <div style="font-family:'JetBrains Mono',monospace; min-width:160px; line-height:1.4;">
            <div style="display:flex; justify-content:space-between; align-items:baseline; border-bottom:1px solid #334155; padding-bottom:3px; margin-bottom:4px;">
              <b style="font-size:12px; color:#f8fafc;">${d.name}</b>
              <span style="font-size:10px; color:#00f0ff; font-weight:bold;">#${d.rank}</span>
            </div>
            <div style="font-size:10px; color:#94a3b8;">
              Exceedance: <b style="color:#f8fafc;">${(d.p_mid * 100).toFixed(1)}%</b><br/>
              80% CQR: [${(d.p_low * 100).toFixed(1)}% – ${(d.p_high * 100).toFixed(1)}%]<br/>
              Priority Score: <b style="color:#00f0ff;">${d.priority.toFixed(4)}</b><br/>
              Tier: <b style="color:${getRiskColor(d.priority)};">${d.tier}</b>
              ${d.robust ? '<br/><span style="color:#00f0ff; font-weight:bold;">★ ROBUST TOP-TIER</span>' : ""}
            </div>
          </div>
        `;
        poly.bindTooltip(tipContent, { className: "og-tip", sticky: true });
        riskRef.current.addLayer(poly);

        // District label & centroid calculation
        const boundsCenter = poly.getBounds().getCenter();
        const centerPoint = d.centroid && d.centroid.length === 2 ? d.centroid : [boundsCenter.lat, boundsCenter.lng];

        if (centerPoint && !isNaN(centerPoint[0]) && !isNaN(centerPoint[1])) {
          const labelHtml = `
            <div style="transform:translate(-50%,-50%); text-align:center; white-space:nowrap; pointer-events:none;">
              <div style="font-family:'Inter Variable',sans-serif; font-size:9px; font-weight:700; color:#f8fafc; text-shadow:0 1px 3px #000, 0 0 6px #000;">
                ${d.name}
              </div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:9px; font-weight:bold; color:#00f0ff; text-shadow:0 1px 3px #000;">
                ${(d.p_mid * 100).toFixed(0)}%
              </div>
            </div>
          `;
          const labelMarker = L.marker(centerPoint, {
            interactive: false,
            icon: L.divIcon({ className: "", iconSize: [0, 0], html: labelHtml })
          });
          riskRef.current.addLayer(labelMarker);

          // Pulsing Marker on Robust Districts
          if (d.robust && d.rank <= 5) {
            const pulseHtml = `
              <div style="transform:translate(-50%,-50%); pointer-events:none;">
                <div style="width:18px; height:18px; border:2px solid #00f0ff; border-radius:50%; animation:ping 2s cubic-bezier(0, 0, 0.2, 1) infinite; opacity:0.75;"></div>
                <div style="width:6px; height:6px; background:#00f0ff; border-radius:50%; position:absolute; top:6px; left:6px;"></div>
              </div>
            `;
            const pulseMarker = L.marker(centerPoint, {
              interactive: false,
              icon: L.divIcon({ className: "", iconSize: [0, 0], html: pulseHtml })
            });
            robustMarkerRef.current.addLayer(pulseMarker);
          }

          // Uncertainty Layer (conformal band width visualizer)
          if (layers.uncertainty) {
            const bandWidth = d.p_high - d.p_low;
            const radiusMeters = 8000 + bandWidth * 80000;
            const uncCircle = L.circle(centerPoint, {
              radius: radiusMeters,
              color: "#38bdf8",
              weight: 1.2,
              dashArray: "3 5",
              fill: true,
              fillColor: "#38bdf8",
              fillOpacity: 0.08,
              interactive: false
            });
            unRef.current.addLayer(uncCircle);
          }
        }
      });
    }
  }, [dash, selectedId, layers.risk, layers.uncertainty]);

  // Sentinel-1 SAR Flood Inundation Layer
  useEffect(() => {
    if (!sarRef.current) return;
    sarRef.current.clearLayers();

    if (layers.extent && extent && extent.features) {
      const sarLayer = L.geoJSON(extent, {
        style: {
          color: "#00e5ff",
          weight: 1.5,
          fillColor: "#00e5ff",
          fillOpacity: sarOpacity
        }
      });
      sarLayer.bindTooltip(
        "<b>Sentinel-1 SAR Flood Inundation Footprint</b><br/><span style='font-family:monospace;font-size:9px;'>30m microwave radar thresholded water</span>",
        { className: "og-tip", sticky: true }
      );
      sarRef.current.addLayer(sarLayer);
    }
  }, [extent, layers.extent, sarOpacity]);

  const fitToTopDistricts = () => {
    const map = mapRef.current;
    if (!map || !dash || !dash.districts) return;

    // Check direct centroids first
    const directCentroids = dash.districts
      .filter((d) => d.rank <= 5 && d.centroid && d.centroid.length === 2)
      .map((d) => d.centroid);

    if (directCentroids.length > 0) {
      map.fitBounds(L.latLngBounds(directCentroids), { padding: [40, 40], maxZoom: 9 });
      return;
    }

    // Fallback to computing bounding box from GeoJSON features for top 5 ranked districts
    if (dash.geojson && dash.geojson.features) {
      const topIds = new Set(dash.districts.filter((d) => d.rank <= 5).map((d) => d.id));
      const topFeatures = dash.geojson.features.filter((f) => {
        const zid = f.properties?.geometry_id || f.properties?.id;
        return topIds.has(zid);
      });
      if (topFeatures.length > 0) {
        const bounds = L.geoJSON({ type: "FeatureCollection", features: topFeatures }).getBounds();
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 9 });
      }
    }
  };

  return (
    <div className="relative w-full h-full bg-canvas select-none">
      {/* Leaflet Map Div */}
      <div ref={elRef} className="w-full h-full" tabIndex={0} aria-label="Assam Basin Hazard Choropleth Map" />

      {/* Map Overlay Controls (Top-Left) */}
      <div className="absolute top-4 left-4 z-[400] flex flex-col gap-2 font-mono text-[11px]">
        {/* Fit to Top Zones Button */}
        <button
          onClick={fitToTopDistricts}
          className="px-3 py-1.5 rounded border border-line bg-panel/90 backdrop-blur text-ink hover:text-cyan hover:border-cyan/40 transition-colors flex items-center gap-1.5 shadow-lg"
          title="Zoom to Top 5 Priority Districts"
        >
          <ZoomIn className="w-3.5 h-3.5 text-cyan" />
          <span>Focus Top 5</span>
        </button>

        {/* SAR Opacity Slider (When SAR Extent Active) */}
        {layers.extent && extent && (
          <div className="p-2.5 rounded border border-line bg-panel/90 backdrop-blur shadow-lg flex flex-col gap-1 w-44">
            <div className="flex justify-between items-center text-[10px] text-dim">
              <span className="uppercase text-cyan font-bold">SAR Opacity</span>
              <span>{(sarOpacity * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min={0.1}
              max={1.0}
              step={0.05}
              value={sarOpacity}
              onChange={(e) => onSarOpacityChange && onSarOpacityChange(Number(e.target.value))}
              className="w-full h-1 bg-line rounded cursor-pointer accent-cyan"
            />
          </div>
        )}
      </div>

      {/* Map Legend (Bottom-Right) */}
      <div className="absolute bottom-4 right-4 z-[400] p-3 rounded border border-line bg-panel/90 backdrop-blur-md shadow-2xl font-mono text-[10px] space-y-1.5 pointer-events-none">
        <div className="font-bold uppercase tracking-wider text-dim text-[9px] border-b border-line pb-1 mb-1.5">
          Priority Risk Legend
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded" style={{ background: getRiskColor(0.09) }} />
          <span>Severe (&ge; 0.08)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded" style={{ background: getRiskColor(0.06) }} />
          <span>Warning (0.05 – 0.08)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded" style={{ background: getRiskColor(0.03) }} />
          <span>Watch (0.02 – 0.05)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded" style={{ background: getRiskColor(0.01) }} />
          <span>Normal (&lt; 0.02)</span>
        </div>
        {layers.extent && extent && (
          <div className="flex items-center gap-2 pt-1 border-t border-line/60">
            <span className="w-3 h-3 rounded bg-sar opacity-80" />
            <span className="text-cyan font-bold">Sentinel-1 SAR Flood</span>
          </div>
        )}
      </div>
    </div>
  );
}
