// Clipboard API is unavailable on ordinary HTTP origins. Keep a fallback for
// internal deployments that are accessed by IP address without HTTPS.
export async function copyToClipboard(value) {
  const text = String(value ?? '')
  if (!text) return false

  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (_) {
      // Permission denied or browser policy: try the legacy selection path.
    }
  }

  const input = document.createElement('textarea')
  const previousFocus = document.activeElement
  const selection = window.getSelection()
  const savedRanges = []
  if (selection) {
    for (let i = 0; i < selection.rangeCount; i++) savedRanges.push(selection.getRangeAt(i))
  }
  input.value = text
  input.readOnly = true
  input.style.position = 'fixed'
  input.style.left = '-9999px'
  document.body.appendChild(input)
  try {
    input.focus()
    input.select()
    return document.execCommand('copy')
  } catch (_) {
    return false
  } finally {
    input.remove()
    selection?.removeAllRanges()
    savedRanges.forEach(range => selection?.addRange(range))
    previousFocus?.focus?.()
  }
}
