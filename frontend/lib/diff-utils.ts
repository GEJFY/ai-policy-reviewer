/**
 * Simple line-based diff utility (no external dependencies).
 * Compares original and revised text line by line and returns
 * diff hunks with context lines.
 */

export type DiffLineType = 'same' | 'removed' | 'added' | 'separator'

export interface DiffLine {
  type: DiffLineType
  content: string
  lineNumber?: number
}

/**
 * Compute a simple line-based diff between two texts.
 * Returns diff lines with context (surrounding unchanged lines).
 */
export function computeDiff(
  original: string,
  revised: string,
  contextLines = 3
): DiffLine[] {
  const origLines = original.split('\n')
  const revLines = revised.split('\n')

  // Build a simple LCS-based diff
  const rawDiff = buildRawDiff(origLines, revLines)

  // Add context: only show changed lines + surrounding context
  return addContext(rawDiff, contextLines)
}

interface RawDiffLine {
  type: 'same' | 'removed' | 'added'
  content: string
  origLine?: number
  revLine?: number
}

function buildRawDiff(origLines: string[], revLines: string[]): RawDiffLine[] {
  // Use a simple O(NM) approach that's fine for document-sized texts
  const m = origLines.length
  const n = revLines.length

  // Build LCS table
  const dp: number[][] = Array.from({ length: m + 1 }, () =>
    new Array(n + 1).fill(0)
  )
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (origLines[i - 1] === revLines[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }

  // Backtrack to produce diff
  const result: RawDiffLine[] = []
  let i = m
  let j = n
  const stack: RawDiffLine[] = []

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && origLines[i - 1] === revLines[j - 1]) {
      stack.push({ type: 'same', content: origLines[i - 1], origLine: i, revLine: j })
      i--
      j--
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      stack.push({ type: 'added', content: revLines[j - 1], revLine: j })
      j--
    } else {
      stack.push({ type: 'removed', content: origLines[i - 1], origLine: i })
      i--
    }
  }

  // Reverse since we built it backwards
  while (stack.length > 0) {
    result.push(stack.pop()!)
  }

  return result
}

function addContext(rawDiff: RawDiffLine[], contextLines: number): DiffLine[] {
  // Find indices of changed lines
  const changedIndices = new Set<number>()
  rawDiff.forEach((line, idx) => {
    if (line.type !== 'same') {
      changedIndices.add(idx)
    }
  })

  if (changedIndices.size === 0) {
    return [{ type: 'same', content: '(変更なし)' }]
  }

  // Expand context around changed lines
  const visibleIndices = new Set<number>()
  changedIndices.forEach((idx) => {
    for (let c = Math.max(0, idx - contextLines); c <= Math.min(rawDiff.length - 1, idx + contextLines); c++) {
      visibleIndices.add(c)
    }
  })

  const result: DiffLine[] = []
  let lastIdx = -1

  const sortedIndices = Array.from(visibleIndices).sort((a, b) => a - b)
  for (const idx of sortedIndices) {
    if (lastIdx >= 0 && idx - lastIdx > 1) {
      result.push({ type: 'separator', content: '...' })
    }
    const line = rawDiff[idx]
    result.push({
      type: line.type,
      content: line.content,
      lineNumber: line.origLine || line.revLine,
    })
    lastIdx = idx
  }

  return result
}
