const RTL_REGEX = /[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]/;

/**
 * Returns true when `text` contains at least one Arabic-script character
 * (covers Urdu, Arabic, Persian). Used per-message to set dir="rtl"
 * and lang="ur" on the bubble so code-switched threads render correctly.
 */
export function isRtl(text: string): boolean {
  return RTL_REGEX.test(text);
}
