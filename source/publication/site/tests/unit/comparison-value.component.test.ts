// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { expect, test } from "vitest";
import ComparisonValue from "../../src/components/ComparisonValue.vue";
import { scalar } from "../../src/lib/comparison";

test("solved-rate differences use percentage points while the rate remains a percentage", async () => {
  const wrapper = mount(ComparisonValue, { props: {
    value: scalar("0.8"), baseline: scalar("0.8333333333333333333333333333"), format: "percent",
  } });
  expect(wrapper.get("strong").text()).toBe("80%");
  expect(wrapper.get(".comparison-delta").text()).toContain("−3.3");
  expect(wrapper.get("abbr").attributes("title")).toBe("percentage points");
  expect(wrapper.get("abbr [aria-hidden]").text()).toBe("pp");
  expect(wrapper.get("abbr .visually-hidden").text()).toBe("percentage points");
  await wrapper.setProps({ value: scalar("1"), baseline: scalar("0.8") });
  expect(wrapper.get(".comparison-delta").text()).toContain("+20.0");
  await wrapper.setProps({ baseline: null });
  expect(wrapper.find(".comparison-delta").exists()).toBe(false);
  wrapper.unmount();
});

test("question differences retain question units", () => {
  const wrapper = mount(ComparisonValue, { props: {
    value: scalar("11"), baseline: scalar("9"), format: "questions", digits: 0,
  } });
  expect(wrapper.get(".comparison-delta").text()).toBe("+2 vs reference");
  expect(wrapper.find("abbr").exists()).toBe(false);
  wrapper.unmount();
});
