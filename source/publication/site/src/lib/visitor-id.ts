export const VISITOR_ID_STORAGE_KEY = "deep20bench.visitor-id.v1";

const visitorIdPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

const generateVisitorId = (): string => {
  let id: string | undefined;
  try {
    id = window.crypto?.randomUUID?.();
  } catch {
    // Fall through when crypto is unavailable or denied.
  }
  // This ID is not a security token. Ordinary randomness is a supported fallback.
  id ??= "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, character => {
    const random = Math.floor(Math.random() * 16);
    return (character === "x" ? random : (random & 3) | 8).toString(16);
  });

  return id;
};

/** Read on demand; create and persist only when no valid ID is stored. */
export const createVisitorIdReader = (): (() => string) => {
  let fallbackId: string | undefined;
  return () => {
    let storage: Storage;
    try {
      storage = window.localStorage;
      const stored = storage.getItem(VISITOR_ID_STORAGE_KEY);
      if (stored && visitorIdPattern.test(stored)) {
        fallbackId = undefined;
        return stored;
      }
    } catch {
      // Retain one page-session ID while storage cannot be read.
      return fallbackId ??= generateVisitorId();
    }

    const id = fallbackId ?? generateVisitorId();
    try {
      storage.setItem(VISITOR_ID_STORAGE_KEY, id);
      fallbackId = undefined;
    } catch {
      // Retain the ID if a browser allows reads but denies writes.
      fallbackId = id;
    }
    return id;
  };
};
