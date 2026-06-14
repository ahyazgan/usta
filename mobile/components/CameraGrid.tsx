/**
 * 3x3 alignment grid overlay for the camera preview.
 *
 * Two jobs: (1) help the user center the part/light in the frame, and
 * (2) give a visual anchor for the AI's `konum_tarifi` output, which is
 * expressed as a cell of this same 3x3 grid. Purely decorative — sits on
 * top of <CameraView> and ignores touches so the capture button stays live.
 */
import { StyleSheet, View } from 'react-native';

import { theme } from '@/lib/theme';

/** Faint rule color for the grid lines (low opacity so it never distracts). */
const LINE = 'rgba(242, 243, 245, 0.28)';

export function CameraGrid() {
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      {/* Two vertical thirds */}
      <View style={[styles.vLine, { left: '33.33%' }]} />
      <View style={[styles.vLine, { left: '66.66%' }]} />
      {/* Two horizontal thirds */}
      <View style={[styles.hLine, { top: '33.33%' }]} />
      <View style={[styles.hLine, { top: '66.66%' }]} />
      {/* Center focus box — the "aim here" target */}
      <View style={styles.centerWrap}>
        <View style={styles.centerBox} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  vLine: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: StyleSheet.hairlineWidth,
    backgroundColor: LINE,
  },
  hLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: StyleSheet.hairlineWidth,
    backgroundColor: LINE,
  },
  centerWrap: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerBox: {
    width: '34%',
    aspectRatio: 1,
    borderWidth: 2,
    borderColor: theme.colors.accent,
    borderRadius: theme.radius.sm,
    opacity: 0.65,
  },
});

export default CameraGrid;
