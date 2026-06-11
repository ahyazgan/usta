# Usta — Mobile

AI maintenance assistant for car owners. Expo (React Native) + TypeScript + expo-router.

## Install

```bash
npm install
```

## Run

```bash
npx expo start
```

Then press `a` (Android), `i` (iOS), or `w` (web), or scan the QR code with Expo Go.

## Notes

- **Dark theme by default.** The "Gece Garajı" (Night Garage) palette is the only theme; `userInterfaceStyle` is set to `dark`. Design tokens live in `lib/theme.ts`.
- **No hardcoded strings.** Every user-facing string MUST come from `locales/tr.json` / `locales/en.json` through the `t()` helper in `lib/i18n.ts`. `tr.json` and `en.json` keep identical key sets. Default locale falls back to Turkish.
- **Backend.** `lib/api.ts` is a type-safe skeleton client. Set `EXPO_PUBLIC_API_URL` to point at the backend; it defaults to `http://localhost:8080`. The app runs without a backend.
