"use client";

import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";

const TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";
const DEFAULT_CENTER: [number, number] = [-82.9988, 39.9612]; // Columbus, OH

interface LocationPickerProps {
  onLocationSelect: (lat: number, lng: number) => void;
  initialLat?: number;
  initialLng?: number;
}

export default function LocationPicker({
  onLocationSelect,
  initialLat,
  initialLng,
}: LocationPickerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);

  // Keep a ref to the callback so the map event handler never captures a stale closure
  const onSelectRef = useRef(onLocationSelect);
  useEffect(() => {
    onSelectRef.current = onLocationSelect;
  }, [onLocationSelect]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current || !TOKEN) return;

    const center: [number, number] =
      initialLng !== undefined && initialLat !== undefined
        ? [initialLng, initialLat]
        : DEFAULT_CENTER;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/streets-v12",
      accessToken: TOKEN,
      center,
      zoom: initialLat !== undefined ? 14 : 11,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");
    mapRef.current = map;

    // Place initial marker if coordinates exist
    if (initialLat !== undefined && initialLng !== undefined) {
      const marker = new mapboxgl.Marker({ draggable: true, color: "#2563eb" })
        .setLngLat([initialLng, initialLat])
        .addTo(map);

      marker.on("dragend", () => {
        const pos = marker.getLngLat();
        onSelectRef.current(pos.lat, pos.lng);
      });

      markerRef.current = marker;
    }

    // Click to place / move marker
    map.on("click", (e) => {
      const { lat, lng } = e.lngLat;

      if (markerRef.current) {
        markerRef.current.setLngLat([lng, lat]);
      } else {
        const marker = new mapboxgl.Marker({ draggable: true, color: "#2563eb" })
          .setLngLat([lng, lat])
          .addTo(map);

        marker.on("dragend", () => {
          const pos = marker.getLngLat();
          onSelectRef.current(pos.lat, pos.lng);
        });

        markerRef.current = marker;
      }

      onSelectRef.current(lat, lng);
    });

    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!TOKEN) {
    return (
      <div className="flex items-center justify-center h-48 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-sm text-gray-400 text-center px-4">
          Map picker unavailable —{" "}
          <code className="bg-gray-200 px-1 rounded">NEXT_PUBLIC_MAPBOX_TOKEN</code> not set.
          Enter coordinates manually below.
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div
        ref={containerRef}
        className="w-full h-56 rounded-lg overflow-hidden border border-gray-300"
      />
      <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-white bg-opacity-90 px-3 py-1 rounded-full text-xs text-gray-600 shadow-sm pointer-events-none whitespace-nowrap">
        Click map to set location · Drag marker to adjust
      </div>
    </div>
  );
}
