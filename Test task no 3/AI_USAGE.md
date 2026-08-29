# AI Usage

This document describes how AI was used during development and inside the final product.

## 1. AI inside the product

The pipeline uses a local LLM (Ollama) only for one task: generating a short human-readable summary of a CVE that has already been selected and prioritized by deterministic code.

The model never decides:

- whether a CVE is relevant to the monitored stack;
- its priority;
- whether it should be sent.

Those decisions are made entirely by code.

If the model fails, returns an invalid response or produces an unexpected format, the pipeline automatically falls back to a template-based summary built directly from the NVD description.

A detailed description of the validation logic and real examples of model failures can be found in `report.md`.

---

## 2. AI used during development

I used Claude as a development assistant while building this project.

### What I used it for:

- brainstorming the overall architecture;
- generating an initial implementation of the pipeline;
- debugging runtime issues;
- improving prompts for the local LLM;
- reviewing documentation and reports.

### Where it helped:

AI significantly sped up routine work.

For example, it suggested implementing:

- NVD pagination (the first version processed only the first 2000 CVEs);
- validation of LLM responses before sending them;
- automatic fallback summaries when the model fails.

These ideas improved the reliability of the pipeline.

### Where it was wrong

AI also made several incorrect assumptions that had to be verified and corrected.

**Example 1 - Ollama performance**

At first, AI suggested that my computer simply did not have a GPU because the model constantly timed out.

We first tried increasing the timeout and switching to a smaller model, but the problem still remained.

The real reason turned out to be different: Kali Linux was running inside VirtualBox, where the host GPU is not available to Ollama by default. After identifying the actual cause, 
I switched to llama3.2:1b and increased the timeout, which significantly reduced the number of failed requests.

**Example 2 - documentation**

The first version of the report was generated in English, while only `README.md` and `AI_USAGE.md` are required to be in English. I rewrote the report in Russian.

**Example 3 - response validation**

The initial validation checked only whether the words `WHAT:`, `IMPACT:` and `ACTION:` appeared somewhere in the model output.

During testing I noticed that the model sometimes added extra introductory text before the actual answer. The response still passed validation, although it wasn't formatted exactly as intended.

This issue is documented as a known limitation in `report.md`.

---

## Don't forget
AI is just a tool. Every suggestion it makes should be read carefully, verified, and tested in practice. Even if an answer sounds convincing, it does not necessarily mean it is correct. 
That is why I verified every non-trivial solution using logs, documentation, and real program runs instead of taking the model's output at face value.
