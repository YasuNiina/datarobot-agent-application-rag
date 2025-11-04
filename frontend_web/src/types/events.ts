import { type CustomEvent } from '@ag-ui/core';
import { type ProgressStep } from './progress';

export interface ProgressStartCustomEvent extends CustomEvent {
  name: 'progress-start';
  value: {
    id: string;
    steps: ProgressStep[];
  };
}

export interface ProgressDoneCustomEvent extends CustomEvent {
  name: 'progress-done';
  value: { id: string; step: number };
}

export interface ProgressErrorCustomEvent extends CustomEvent {
  name: 'progress-error';
  value: { id: string; step: number; message: string };
}

export function isProgressStart(event: CustomEvent): event is ProgressStartCustomEvent {
  return event.name === 'progress-start';
}

export function isProgressDone(event: CustomEvent): event is ProgressDoneCustomEvent {
  return event.name === 'progress-done';
}

export function isProgressError(event: CustomEvent): event is ProgressErrorCustomEvent {
  return event.name === 'progress-error';
}
