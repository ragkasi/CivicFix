"use client";

import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import type { ReportDetail } from "@/lib/api";

const TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";
const DEFAULT_CENTER: [number, number] = [-82.9988, 39.9612]; // Columbus, OH
const DEFAULT_ZOOM = 11;

function pinColor(severity: string | null | undefined): string {
  switch (severity) {
    case "critical": return "#ef4444";
    case "high":     return "#f97316";
    case "medium":   return "#f59e0b";
    case "low":      return "#22c55e";
    default:         return "#6b7280";
  }
}

const CATEGORY_LABELS: Record<string, string> = {
  pothole: "Pothole", streetlight: "Streetlight", flooding: "Flooding",
  sidewalk_damage: "Sidewalk Damage", trash_overflow: "Trash Overflow",
  damaged_sign: "Damaged Sign", road_hazard: "Road Hazard",
  graffiti: "Graffiti", snow_or_ice: "Snow/Ice", other: "Other",
};

interface ReportMapProps {
  reports: ReportDetail[];
  height?: string;
}

export default function ReportMap({ reports, height = "100%" }: ReportMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);

  // Initialise the map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current || !TOKEN) return;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/streets-v12",
      accessToken: TOKEN,
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");
    mapRef.current = map;

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      map.remove();
      mapRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Add / refresh markers whenever reports change
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    function addMarkers() {
      // Clear previous markers
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];

      if (reports.length === 0) return;

      const bounds = new mapboxgl.LngLatBounds();

      reports.forEach((report) => {
        const popup = new mapboxgl.Popup({ closeButton: false, offset: 25, maxWidth: "220px" })
          .setHTML(`
            <div style="font-size:13px;line-height:1.5">
              <div style="font-weight:600;margin-bottom:2px">
                ${CATEGORY_LABELS[report.category ?? ""] ?? "Report"}
              </div>
              <div>Status: <strong>${report.status}</strong></div>
              ${report.severity ? `<div>Severity: ${report.severity}</div>` : ""}
              ${report.address ? `<div style="color:#555">${report.address}</div>` : ""}
              <a href="/admin/reports/${report.id}"
                 style="color:#2563eb;text-decoration:underline;display:block;margin-top:4px">
                View details →
              </a>
            </div>
          `);

        const marker = new mapboxgl.Marker({ color: pinColor(report.severity) })
          .setLngLat([report.longitude, report.latitude])
          .setPopup(popup)
          .addTo(map!);

        markersRef.current.push(marker);
        bounds.extend([report.longitude, report.latitude]);
      });

      // Fit map to show all markers
      map!.fitBounds(bounds, { padding: 60, maxZoom: 14, duration: 500 });
    }

    if (map.loaded()) {
      addMarkers();
    } else {
      map.once("load", addMarkers);
    }
  }, [reports]);

  if (!TOKEN) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center bg-gray-100 rounded-lg"
      >
        <div className="text-center px-6">
          <p className="text-gray-500 font-medium">Map unavailable</p>
          <p className="text-sm text-gray-400 mt-1">
            Set <code className="bg-gray-200 px-1 rounded">NEXT_PUBLIC_MAPBOX_TOKEN</code> in{" "}
            <code className="bg-gray-200 px-1 rounded">frontend/.env.local</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ height }} className="w-full rounded-lg overflow-hidden" />
  );
}
