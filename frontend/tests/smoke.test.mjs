import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("landing page keeps dashboard call-to-action", () => {
  const page = readFileSync("app/page.tsx", "utf8");

  assert.match(page, /Enter Dashboard/);
  assert.match(page, /href="\/feed"/);
});
