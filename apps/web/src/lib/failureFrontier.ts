// The ML team owns this contract. Unknown payloads cannot be shown as verified analysis.
export type FailureFrontierState =
  | { status: 'pending'; payload: null }
  | { status: 'verified'; payload: unknown; modelVersion: string }

export const failureFrontier: FailureFrontierState = { status: 'pending', payload: null }
