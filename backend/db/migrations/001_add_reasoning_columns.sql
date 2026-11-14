-- Run once in the Supabase SQL editor.
-- Lets the cache store Claude's reasoning so cache hits show the same
-- explanation as a fresh analysis. Existing rows keep NULL reasoning.
ALTER TABLE analyses
  ADD COLUMN IF NOT EXISTS bias_reasoning text,
  ADD COLUMN IF NOT EXISTS tone_reasoning text;
