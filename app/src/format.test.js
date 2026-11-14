// Tests for format.js. Run from app/:  node --test src/format.test.js
import { test } from "node:test";
import assert from "node:assert/strict";
import { formatDuration, formatSigned, yesNo } from "./format.js";

test("formatDuration: minutes only", () => {
  assert.equal(formatDuration(0.5), "30 min");
  assert.equal(formatDuration(0), "0 min");
});

test("formatDuration: hours and minutes", () => {
  assert.equal(formatDuration(1), "1 h");
  assert.equal(formatDuration(1.5), "1 h 30 min");
  assert.equal(formatDuration(23.25), "23 h 15 min");
});

test("formatDuration: days, hours, minutes", () => {
  assert.equal(formatDuration(24), "1 d");
  assert.equal(formatDuration(25.25), "1 d 1 h 15 min");
  assert.equal(formatDuration(168.5177), "7 d 31 min");
});

test("formatDuration: rounds up into the next hour instead of showing 60 min", () => {
  assert.equal(formatDuration(0.9999), "1 h");
});

test("formatDuration: null means no event in the data", () => {
  assert.equal(formatDuration(null), "none");
});

test("formatSigned: always shows the sign, zero has none", () => {
  assert.equal(formatSigned(1.7364), "+1.74");
  assert.equal(formatSigned(-1.2189), "-1.22");
  assert.equal(formatSigned(0), "0.00");
});

test("formatSigned: a tiny negative that rounds to zero shows no sign", () => {
  assert.equal(formatSigned(-0.001), "0.00");
  assert.equal(formatSigned(0.001), "0.00");
});

test("formatSigned: digits argument", () => {
  assert.equal(formatSigned(2.95591, 1), "+3.0");
});

test("yesNo", () => {
  assert.equal(yesNo(true), "Yes");
  assert.equal(yesNo(false), "No");
});
