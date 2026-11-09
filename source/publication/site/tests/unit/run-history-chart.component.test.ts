// @vitest-environment jsdom
import { mount } from "@vue/test-utils";
import { afterEach, expect, test, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { nextTick } from "vue";
import RunHistoryChart from "../../src/components/RunHistoryChart.vue";
import { groupHistoryMarkers, historyDifference, type HistoryChartRun } from "../../src/lib/run-history-chart";

afterEach(() => vi.unstubAllGlobals());
const run = (id: string, x: number, latest = false): HistoryChartRun => ({
  executionId: `BX-${id}`, modelId: "M-0001", modelName: "Synthetic model",
  completedAt: `2026-10-${id.padStart(2,"0")}T12:00:00Z`, latest,
  x, xDisplay: x.toFixed(2), lower:x-1, upper:x+1,
});
const render = async (items: HistoryChartRun[], mode: "dot"|"scatter" = "dot") => {
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  const router = createRouter({history:createMemoryHistory(),routes:[
    {path:"/",component:{template:"<div />"}},
    {path:"/runs/:executionId/",name:"run",component:{template:"<div />"}},
  ]});
  await router.push("/");
  await router.isReady();
  return {router,wrapper:mount(RunHistoryChart,{props:{items,xLabel:"Question score",mode},global:{plugins:[router]}})};
};

test("four dates retain every value, one latest row and separate links for coincident runs", async () => {
  const items = [run("04",20,true),run("03",10),run("02",10),run("01",11)];
  const {wrapper} = await render(items);
  expect(wrapper.findAll(".latest-point")).toHaveLength(1);
  expect(wrapper.findAll(".history-model-label")).toHaveLength(1);
  expect(wrapper.findAll(".history-values li")).toHaveLength(3);
  await wrapper.get('[aria-label^="2 overlapping earlier runs"]').trigger("click");
  const choices = wrapper.get('[role="dialog"]');
  expect(choices.findAll("a").map(link=>link.attributes("href"))).toEqual(["/runs/BX-03/","/runs/BX-02/"]);
  expect(choices.text()).toContain("10.00");
  expect(choices.text()).not.toContain("10.50");
  await choices.get("button").trigger("click");
  expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
  wrapper.unmount();
});

test("a single earlier marker opens its exact execution and keyboard focus reveals its interval", async () => {
  const {wrapper,router} = await render([run("04",20,true),run("01",10)]);
  const earlier = wrapper.get(".earlier-point");
  expect(wrapper.findAll(".historical.shown")).toHaveLength(0);
  document.body.append(wrapper.element);
  (earlier.element as SVGElement).focus();
  await nextTick();
  await wrapper.get(".history-plot").trigger("pointerleave");
  expect(wrapper.findAll(".historical.shown")).toHaveLength(1);
  expect(wrapper.get('[role="tooltip"]').text()).toContain("1 Oct 2026");
  await earlier.trigger("keydown",{key:"Enter"});
  await router.isReady();
  await vi.waitFor(()=>expect(router.currentRoute.value.params.executionId).toBe("BX-01"));
  wrapper.unmount();
});

test("an older low score cannot reorder latest model rows; scatter axes also include old outliers", async () => {
  const alpha = run("04",20,true);
  const beta = {...run("03",15,true),modelId:"M-0002",modelName:"Second model"};
  const {wrapper} = await render([alpha,beta,run("01",1)]);
  expect(wrapper.findAll(".history-model-label").map(label=>label.text())).toEqual(["Synthetic model","Second model"]);
  wrapper.unmount();
  const scatter = await render([{...alpha,y:20,yDisplay:"20"},{...run("01",1000),y:40,yDisplay:"40"}],"scatter");
  const point = scatter.wrapper.get(".earlier-point circle");
  expect(Number(point.attributes("cx"))).toBeGreaterThan(62);
  expect(Number(point.attributes("cx"))).toBeLessThan(900);
  expect(Number(point.attributes("cy"))).toBeGreaterThan(28);
  scatter.wrapper.unmount();
});

test("a touch selection shows dated details before navigating", async () => {
  const {wrapper,router} = await render([run("04",20,true),run("01",10)]);
  await wrapper.get(".earlier-point").trigger("click",{pointerType:"touch"});
  expect(router.currentRoute.value.path).toBe("/");
  const dialog = wrapper.get('[role="dialog"]');
  expect(dialog.text()).toContain("1 Oct 2026");
  expect(dialog.get("a").attributes("href")).toBe("/runs/BX-01/");
  wrapper.unmount();
});

test("overlap grouping anchors to a recorded point without averaging and keeps sub-cent differences", () => {
  const first = run("01",10), second = run("02",10.01);
  const groups = groupHistoryMarkers([{run:first,x:100,y:50},{run:second,x:104,y:50}]);
  expect(groups).toEqual([{x:100,y:50,members:[first,second]}]);
  expect(first.x).toBe(10);
  expect(second.x).toBe(10.01);
  expect(historyDifference(0.0046,0.0015,"episode-cost")).toBe("+$0.0031");
});
