import { effectScope, nextTick, ref } from "vue";
import { describe, expect, it, vi } from "vitest";

import { useKeyedPublicationLoad } from "@/lib/use-keyed-publication-load";

interface Deferred<Value> {
  promise: Promise<Value>;
  resolve: (value: Value) => void;
}

const deferred = <Value>(): Deferred<Value> => {
  let resolve = (_value: Value): void => undefined;
  const promise = new Promise<Value>((promiseResolve) => {
    resolve = promiseResolve;
  });
  return { promise, resolve };
};

describe("useKeyedPublicationLoad", () => {
  it("waits until every publication key part is available", async () => {
    const executionId = ref("");
    const targetId = ref("");
    const load = vi.fn(async (run: string, target: string) => `${run}/${target}`);
    const scope = effectScope();
    const state = scope.run(() =>
      useKeyedPublicationLoad({
        parameters: (): [string, string] => [
          executionId.value,
          targetId.value,
        ],
        load,
        fallbackError: "load failed",
      }),
    );
    if (state === undefined) throw new Error("load state was not created");

    await nextTick();
    expect(load).not.toHaveBeenCalled();

    executionId.value = "run-1";
    await nextTick();
    expect(load).not.toHaveBeenCalled();

    targetId.value = "subject-1";
    await nextTick();
    await nextTick();
    expect(load).toHaveBeenCalledOnce();
    expect(state.document.value).toBe("run-1/subject-1");
    scope.stop();
  });

  it("ignores a stale response after the requested key changes", async () => {
    const first = deferred<string>();
    const second = deferred<string>();
    const key = ref("first");
    const scope = effectScope();
    const state = scope.run(() =>
      useKeyedPublicationLoad({
        parameters: (): [string] => [key.value],
        load: (requested) =>
          requested === "first" ? first.promise : second.promise,
        fallbackError: "load failed",
      }),
    );
    if (state === undefined) throw new Error("load state was not created");

    key.value = "second";
    await nextTick();
    second.resolve("current");
    await second.promise;
    await nextTick();
    expect(state.document.value).toBe("current");
    expect(state.loading.value).toBe(false);

    first.resolve("stale");
    await first.promise;
    await nextTick();
    expect(state.document.value).toBe("current");
    expect(state.error.value).toBeNull();
    scope.stop();
  });
});
