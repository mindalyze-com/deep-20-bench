import { shallowRef, watch, type ShallowRef } from "vue";

interface KeyedPublicationLoadOptions<
  Parameters extends readonly string[],
  Document,
> {
  parameters: () => Parameters;
  load: (...parameters: Parameters) => Promise<Document>;
  fallbackError: string;
  clearBeforeLoad?: boolean;
  onBeforeLoad?: () => void;
  onLoaded?: (document: Document) => void;
  onSettled?: () => void;
}

export interface KeyedPublicationLoadState<Document> {
  document: ShallowRef<Document | null>;
  loading: ShallowRef<boolean>;
  error: ShallowRef<string | null>;
  reload: () => Promise<void>;
}

export const useKeyedPublicationLoad = <
  Parameters extends readonly string[],
  Document,
>(
  options: KeyedPublicationLoadOptions<Parameters, Document>,
): KeyedPublicationLoadState<Document> => {
  const document = shallowRef<Document | null>(null);
  const loading = shallowRef(true);
  const error = shallowRef<string | null>(null);

  const isCurrent = (requested: Parameters): boolean => {
    const current = options.parameters();
    return (
      current.length === requested.length &&
      current.every((value, index) => value === requested[index])
    );
  };

  const reload = async (): Promise<void> => {
    const requested = [...options.parameters()] as unknown as Parameters;
    loading.value = true;
    error.value = null;
    if (options.clearBeforeLoad === true) document.value = null;
    options.onBeforeLoad?.();
    try {
      const loaded = await options.load(...requested);
      if (!isCurrent(requested)) return;
      document.value = loaded;
      options.onLoaded?.(loaded);
    } catch (cause: unknown) {
      if (!isCurrent(requested)) return;
      document.value = null;
      error.value =
        cause instanceof Error ? cause.message : options.fallbackError;
    } finally {
      if (isCurrent(requested)) {
        loading.value = false;
        options.onSettled?.();
      }
    }
  };

  watch(options.parameters, () => void reload(), { immediate: true });
  return { document, loading, error, reload };
};
