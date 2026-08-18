import { readonly, ref, type Ref } from "vue";

export interface PublicationLoadState {
  loading: Readonly<Ref<boolean>>;
  error: Readonly<Ref<string | null>>;
  reload: () => Promise<void>;
}

const defaultError = "Publication data could not be loaded.";

export const usePublicationLoad = (
  task: () => Promise<void>,
  fallbackError = defaultError,
): PublicationLoadState => {
  const loading = ref(true);
  const error = ref<string | null>(null);

  const reload = async (): Promise<void> => {
    loading.value = true;
    error.value = null;
    try {
      await task();
    } catch (reason: unknown) {
      error.value = reason instanceof Error ? reason.message : fallbackError;
    } finally {
      loading.value = false;
    }
  };

  void reload();
  return { loading: readonly(loading), error: readonly(error), reload };
};
