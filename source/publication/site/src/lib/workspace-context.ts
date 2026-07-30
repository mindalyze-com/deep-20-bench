import {
  inject,
  type ComputedRef,
  type InjectionKey,
  type Ref,
} from "vue";

import type {
  PublicRunSummary,
  PublicSubjectSummary,
  RunDocument,
  SubjectDocument,
} from "./types";

export interface RunWorkspaceContext {
  document: Readonly<Ref<RunDocument | null>>;
  run: ComputedRef<PublicRunSummary | null>;
  subjects: ComputedRef<PublicSubjectSummary[]>;
  loading: Readonly<Ref<boolean>>;
}

export interface SubjectWorkspaceContext {
  document: Readonly<Ref<SubjectDocument | null>>;
  subject: ComputedRef<PublicSubjectSummary | null>;
  loading: Readonly<Ref<boolean>>;
}

export const runWorkspaceKey: InjectionKey<RunWorkspaceContext> =
  Symbol("run-workspace");
export const subjectWorkspaceKey: InjectionKey<SubjectWorkspaceContext> =
  Symbol("subject-workspace");

export const useRunWorkspace = (): RunWorkspaceContext => {
  const context = inject(runWorkspaceKey);
  if (context === undefined) {
    throw new Error("Run workspace context is unavailable.");
  }
  return context;
};

export const useSubjectWorkspace = (): SubjectWorkspaceContext => {
  const context = inject(subjectWorkspaceKey);
  if (context === undefined) {
    throw new Error("Subject workspace context is unavailable.");
  }
  return context;
};
