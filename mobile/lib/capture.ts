/**
 * Image capture helper — enforces the AI cost rule client-side by resizing
 * every captured frame so the long edge is ≤ 1024px and compressing to
 * JPEG quality 0.7 before it ever leaves the device.
 */
import * as ImageManipulator from 'expo-image-manipulator';

/** Long-edge cap (px) applied before upload to bound token/transfer cost. */
export const MAX_LONG_EDGE = 1024;
/** JPEG compression quality applied to the captured frame. */
export const JPEG_QUALITY = 0.7;

export interface EncodedImage {
  /** Base64-encoded JPEG payload (no data URI prefix). */
  base64: string;
  mediaType: 'image/jpeg';
}

/**
 * Resize + compress a captured photo and return its base64 JPEG payload.
 *
 * Aspect ratio is preserved by constraining only the long edge: when the
 * supplied photo is wider than tall we pass a single `width`, otherwise a
 * single `height` — expo-image-manipulator scales the other dimension
 * proportionally. The first pass reads the photo's true dimensions so we
 * know which edge is longer.
 */
export async function captureAndEncode(photoUri: string): Promise<EncodedImage> {
  // First pass: no-op manipulation just to read the source dimensions.
  const probe = await ImageManipulator.manipulateAsync(photoUri, [], {
    format: ImageManipulator.SaveFormat.JPEG,
  });

  const landscape = probe.width >= probe.height;
  const longEdge = landscape ? probe.width : probe.height;

  // Only resize when the frame actually exceeds the cap; otherwise just
  // re-encode at the target quality without upscaling.
  const resize = landscape
    ? { width: MAX_LONG_EDGE }
    : { height: MAX_LONG_EDGE };
  const actions = longEdge > MAX_LONG_EDGE ? [{ resize }] : [];

  const result = await ImageManipulator.manipulateAsync(photoUri, actions, {
    compress: JPEG_QUALITY,
    format: ImageManipulator.SaveFormat.JPEG,
    base64: true,
  });

  if (!result.base64) {
    throw new Error('Image encoding failed: no base64 output');
  }

  return { base64: result.base64, mediaType: 'image/jpeg' };
}

export default captureAndEncode;
