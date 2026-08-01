import { ref, type Ref } from "vue";

import { getRepeatAverages } from "@/lib/api";
import type { PublicRepeatAverage } from "@/lib/types";

interface RepeatAverageState {
  averages: Ref<PublicRepeatAverage[] | null>;
  loading: Ref<boolean>;
  error: Ref<string | null>;
  load: () => Promise<void>;
}

export const useRepeatAverages = (): RepeatAverageState => {
  const averages = ref<PublicRepeatAverage[] | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const load = async (): Promise<void> => {
    if (loading.value || averages.value !== null) return;
    loading.value = true;
    error.value = null;
    try {
      averages.value = (await getRepeatAverages()).averages;
    } catch {
      error.value = "Repeat averages could not be loaded. Try the switch again.";
    } finally {
      loading.value = false;
    }
  };

  return { averages, loading, error, load };
};
