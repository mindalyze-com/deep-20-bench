import { effectScope, nextTick, ref } from "vue";
import { describe, expect, it } from "vitest";

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
