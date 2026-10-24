import type { SimulationResult } from '../lib/contracts'

const formatter = new Intl.NumberFormat('en', { maximumFractionDigits: 2 })
export const number = (value: number) => formatter.format(value)
export const hours = (value: number) => `${number(value)} h`
export const percent = (value: number) => `${number(value * 100)}%`
type Run = Pick<SimulationResult, 'input' | 'summary'>
export const horizon = (result: Run) => result.input.duration_hours ?? result.summary.observed_duration_hours
export const conclusion = (result: Run) => result.summary.survived_full_window
  ? `Critical power survives the ${hours(horizon(result))} window.`
  : result.summary.critical_survival_hours !== null
    ? `Critical power first fails after ${hours(result.summary.critical_survival_hours)}.`
    : 'Critical power is not maintained throughout this window.'
