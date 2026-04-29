"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { api } from "@/lib/api";

interface FormState {
  description: string;
  latitude: string;
  longitude: string;
  address: string;
  contact_email: string;
  contact_phone: string;
}

const INITIAL: FormState = {
  description: "",
  latitude: "",
  longitude: "",
  address: "",
  contact_email: "",
  contact_phone: "",
};

export default function NewReportPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);

  const [form, setForm] = useState<FormState>(INITIAL);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  function handleImageChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  }

  function removeImage() {
    setImageFile(null);
    setImagePreview(null);
    if (fileRef.current) fileRef.current.value = "";
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const lat = parseFloat(form.latitude);
    const lng = parseFloat(form.longitude);

    if (form.description.trim().length < 10) {
      setError("Description must be at least 10 characters.");
      return;
    }
    if (isNaN(lat) || isNaN(lng)) {
      setError("Please enter valid latitude and longitude values.");
      return;
    }

    setSubmitting(true);

    try {
      // Step 1: upload image if provided
      let imagePath: string | undefined;
      if (imageFile) {
        const upload = await api.upload.image(imageFile);
        imagePath = upload.storage_path;
      }

      // Step 2: create report
      const response = await api.reports.create({
        description: form.description.trim(),
        latitude: lat,
        longitude: lng,
        address: form.address.trim() || undefined,
        image_path: imagePath,
        contact_email: form.contact_email.trim() || undefined,
        contact_phone: form.contact_phone.trim() || undefined,
      });

      // Step 3: redirect to tracking page
      router.push(`/track/${response.tracking_token}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/"
            className="text-sm text-blue-600 hover:underline mb-4 inline-block"
          >
            &larr; Back to home
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Report an Issue</h1>
          <p className="text-gray-500 mt-1">
            Describe the problem and where it is. We&apos;ll route it to the
            right city department.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl border border-gray-200 p-6 space-y-5"
        >
          {/* Description */}
          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              id="description"
              name="description"
              rows={4}
              required
              minLength={10}
              maxLength={2000}
              placeholder="Describe the issue in detail — what you see, any safety concerns, how long it has been there..."
              value={form.description}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">
              {form.description.length}/2000 characters (minimum 10)
            </p>
          </div>

          {/* Image upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Photo (optional)
            </label>
            {imagePreview ? (
              <div className="relative">
                <Image
                  src={imagePreview}
                  alt="Preview"
                  width={400}
                  height={200}
                  className="w-full h-48 object-cover rounded-lg border border-gray-200"
                />
                <button
                  type="button"
                  onClick={removeImage}
                  className="absolute top-2 right-2 bg-white border border-gray-300 rounded-full px-2 py-0.5 text-xs text-gray-600 hover:bg-gray-50"
                >
                  Remove
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 transition-colors">
                <span className="text-gray-400 text-sm">
                  Click to upload a photo (JPEG, PNG, WebP — max 10 MB)
                </span>
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleImageChange}
                  className="hidden"
                />
              </label>
            )}
          </div>

          {/* Location */}
          <div>
            <p className="block text-sm font-medium text-gray-700 mb-2">
              Location <span className="text-red-500">*</span>
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label
                  htmlFor="latitude"
                  className="block text-xs text-gray-500 mb-1"
                >
                  Latitude
                </label>
                <input
                  id="latitude"
                  name="latitude"
                  type="number"
                  step="any"
                  required
                  min={-90}
                  max={90}
                  placeholder="e.g. 39.999"
                  value={form.latitude}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label
                  htmlFor="longitude"
                  className="block text-xs text-gray-500 mb-1"
                >
                  Longitude
                </label>
                <input
                  id="longitude"
                  name="longitude"
                  type="number"
                  step="any"
                  required
                  min={-180}
                  max={180}
                  placeholder="e.g. -83.012"
                  value={form.longitude}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Map picker coming in Phase 3b — enter coordinates manually for now.
            </p>
          </div>

          {/* Address */}
          <div>
            <label
              htmlFor="address"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Street address (optional)
            </label>
            <input
              id="address"
              name="address"
              type="text"
              placeholder="e.g. 123 Oak Street"
              value={form.address}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Contact */}
          <div className="space-y-3 pt-1">
            <p className="text-sm font-medium text-gray-700">
              Contact info (optional — for status updates)
            </p>
            <input
              name="contact_email"
              type="email"
              placeholder="Email address"
              value={form.contact_email}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              name="contact_phone"
              type="tel"
              placeholder="Phone number"
              value={form.contact_phone}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 px-4 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? "Submitting..." : "Submit Report"}
          </button>
        </form>
      </div>
    </main>
  );
}
