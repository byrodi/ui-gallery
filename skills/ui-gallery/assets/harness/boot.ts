// Order matters: the fake transport must exist before any app module runs,
// because API clients often capture fetch or invoke at import time.
import './fake-backend.ts';
// The app's real entry point, through the @app alias in vite.config.mjs.
// Import its global CSS here too if the entry does not.
import '@app/main.tsx';
import './steps.ts';
