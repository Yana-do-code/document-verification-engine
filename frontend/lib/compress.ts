export interface CompressResult {
  file: File;
  originalSize: number;
  compressedSize: number;
}

/**
 * Compresses an image file client-side using the Canvas API.
 * - Resizes to maxWidth if wider (preserving aspect ratio)
 * - Re-encodes as JPEG at the given quality
 * - PDFs are returned unchanged (cannot be compressed in-browser)
 */
export async function compressFile(
  file: File,
  maxWidth = 1600,
  quality = 0.85
): Promise<CompressResult> {
  // PDFs cannot be compressed in the browser — pass through as-is
  if (file.type === "application/pdf") {
    return { file, originalSize: file.size, compressedSize: file.size };
  }

  return new Promise((resolve) => {
    const img = new window.Image();
    const url = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(url);

      let { width, height } = img;
      if (width > maxWidth) {
        height = Math.round((height * maxWidth) / width);
        width = maxWidth;
      }

      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        resolve({ file, originalSize: file.size, compressedSize: file.size });
        return;
      }

      ctx.drawImage(img, 0, 0, width, height);

      canvas.toBlob(
        (blob) => {
          if (!blob || blob.size >= file.size) {
            // Compression made it bigger (or failed) — use original
            resolve({ file, originalSize: file.size, compressedSize: file.size });
            return;
          }
          const compressed = new File(
            [blob],
            file.name.replace(/\.[^.]+$/, ".jpg"),
            { type: "image/jpeg", lastModified: Date.now() }
          );
          resolve({
            file: compressed,
            originalSize: file.size,
            compressedSize: blob.size,
          });
        },
        "image/jpeg",
        quality
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve({ file, originalSize: file.size, compressedSize: file.size });
    };

    img.src = url;
  });
}

export function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.round(bytes / 1024)} KB`;
}
