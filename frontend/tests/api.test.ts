import {afterEach,describe,expect,it,vi} from "vitest";
import {api,initials,percent} from "../src/lib/api";

afterEach(()=>vi.unstubAllGlobals());
describe("analytics interface",()=>{
  it("formats real probabilities",()=>{expect(percent(0.462)).toBe("46.2%");expect(initials("Manchester City")).toBe("M");});
  it("reports an unavailable backend",async()=>{vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:false,json:async()=>({detail:"No deployed model"})}));await expect(api("/predict")).rejects.toThrow("No deployed model");});
  it("passes real fixture lists including an empty list",async()=>{vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:true,json:async()=>[]}));expect(await api("/fixtures/upcoming")).toEqual([]);});
});
