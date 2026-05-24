// NO-LOGIN MODE: Firebase auth completely bypassed
// A fake auth object is exported so existing imports don't break

export const auth = {
  currentUser: null,
  onAuthStateChanged: () => () => {},
} as any;

export const db = null as any;
