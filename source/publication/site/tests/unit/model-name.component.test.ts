// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, test } from "vitest";

import ModelName from "../../src/components/ModelName.vue";

describe("ModelName", () => {
  test("renders a reasoning suffix as accessible output", () => {
    const wrapper = mount(ModelName, {
      props: { name: "Synthetic Model (extra-high)" },
    });

    expect(wrapper.get(".model-name-label").text()).toBe("Synthetic Model");
    expect(wrapper.get(".model-name-effort").text()).toBe("Extra high");
    expect(wrapper.get(".model-name-effort").attributes("aria-label")).toBe(
      "Reasoning effort: Extra high",
    );
  });

  test("does not add an empty effort badge", () => {
    const wrapper = mount(ModelName, {
      props: { name: "Synthetic Model", compact: true, dark: true },
    });

    expect(wrapper.text()).toBe("Synthetic Model");
    expect(wrapper.find(".model-name-effort").exists()).toBe(false);
    expect(wrapper.classes()).toEqual(
      expect.arrayContaining(["model-name", "compact", "dark"]),
    );
  });
});
