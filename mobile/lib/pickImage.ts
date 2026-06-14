/**
 * Gallery image picker helper.
 *
 * Lets the user analyze a photo they already took (e.g. snapped the warning
 * light or part earlier, while the engine was hot, then analyze later) instead
 * of only live capture. Returns the picked image URI, or null if the user
 * cancelled. The returned URI is fed through the same `captureAndEncode`
 * resize/compress path as live capture, so the cost rule still holds.
 */
import * as ImagePicker from 'expo-image-picker';

export type PickResult =
  | { status: 'picked'; uri: string }
  | { status: 'cancelled' }
  | { status: 'denied' };

/**
 * Request gallery permission (if needed) and open the picker.
 * No editing/cropping — we want the original framing so the 3x3 location
 * read stays meaningful.
 */
export async function pickFromGallery(): Promise<PickResult> {
  const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!perm.granted) return { status: 'denied' };

  const res = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    quality: 1, // captureAndEncode re-compresses to JPEG 0.7 ≤1024px
    allowsMultipleSelection: false,
  });

  if (res.canceled || res.assets.length === 0) return { status: 'cancelled' };
  return { status: 'picked', uri: res.assets[0].uri };
}

export default pickFromGallery;
