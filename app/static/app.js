(() => {
  const contextEl = document.getElementById("context");
  const pokeBtn = document.getElementById("poke");
  const statusEl = document.getElementById("status");
  const statusTextEl = document.getElementById("status-text");
  const resultEl = document.getElementById("result");
  const messageEl = document.getElementById("message");

  let currentConcern = null;

  async function postJson(path, body) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      const detail =
        payload && typeof payload.detail === "string"
          ? payload.detail
          : `Request failed with HTTP ${response.status}.`;
      throw new Error(detail);
    }

    return payload;
  }

  function setBusy(busy, text = "Poking holes…") {
    statusTextEl.textContent = text;
    statusEl.hidden = !busy;
    pokeBtn.disabled = busy;
  }

  function showMessage(kind, text) {
    messageEl.className = `message ${kind}`;
    messageEl.textContent = text;
    messageEl.hidden = false;
  }

  function hideMessage() {
    messageEl.hidden = true;
    messageEl.textContent = "";
    messageEl.className = "message";
  }

  function clearResult() {
    currentConcern = null;
    resultEl.replaceChildren();
    resultEl.hidden = true;
  }

  function makeText(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = text ?? "";
    return el;
  }

  function makeMeta(label, value, extraClass = "") {
    const wrapper = document.createElement("div");
    wrapper.className = "meta";

    const labelEl = makeText("span", "meta-label", label);
    const valueEl = makeText("p", `meta-value ${extraClass}`.trim(), value);

    wrapper.append(labelEl, valueEl);
    return wrapper;
  }

  function renderClear() {
    clearResult();

    const card = document.createElement("article");
    card.className = "state-card";
    card.append(
      makeText("h2", "", "✓ No hole worth stopping for. Carry on."),
      makeText(
        "p",
        "",
        "Nothing in this context currently justifies stopping your momentum."
      )
    );

    resultEl.appendChild(card);
    resultEl.hidden = false;
  }

  function renderConcern(concern) {
    clearResult();
    currentConcern = { ...concern };

    const card = document.createElement("article");
    card.className = "card";

    const kicker = makeText("p", "card-kicker", "Missing Question");
    const question = makeText("h2", "question", concern.question);

    const severity = String(concern.severity || "low").toLowerCase();
    const grid = document.createElement("div");
    grid.className = "meta-grid";
    grid.append(
      makeMeta("Assumption", concern.assumption),
      makeMeta("Severity", severity, `severity-${severity}`),
      makeMeta("Why now", concern.why_now),
      makeMeta("What could break", concern.failure_if_ignored),
      makeMeta("Evidence", concern.evidence)
    );

    const actions = document.createElement("div");
    actions.className = "card-actions";

    const patchBtn = makeText("button", "secondary", "Did I patch the hole?");
    patchBtn.type = "button";
    patchBtn.addEventListener("click", () => showPatchPanel(card));

    actions.appendChild(patchBtn);
    card.append(kicker, question, grid, actions);

    resultEl.appendChild(card);
    resultEl.hidden = false;
  }

  function showPatchPanel(card) {
    const existing = card.querySelector(".patch-panel");
    if (existing) {
      existing.querySelector("textarea")?.focus();
      return;
    }

    const panel = document.createElement("div");
    panel.className = "patch-panel";

    const label = makeText("label", "", "How did you address it?");
    label.htmlFor = "resolution";

    const textarea = document.createElement("textarea");
    textarea.id = "resolution";
    textarea.className = "resolution-input";
    textarea.placeholder =
      "Describe the change, evidence, decision, test, fallback, or constraint that addresses the concern.";

    const submit = makeText("button", "primary", "Evaluate patch");
    submit.type = "button";
    submit.addEventListener("click", async () => {
      const resolution = textarea.value.trim();
      if (!resolution) {
        showMessage("error", "Tell me how you addressed the issue first.");
        textarea.focus();
        return;
      }

      hideMessage();
      submit.disabled = true;
      setBusy(true, "Evaluating patch…");

      try {
        const evaluation = await postJson("/evaluate_patch", {
          original_concern: currentConcern,
          resolution,
          updated_context: contextEl.value,
        });

        renderPatchResult(evaluation, card, textarea);
      } catch (error) {
        showMessage("error", error.message);
      } finally {
        submit.disabled = false;
        setBusy(false);
      }
    });

    panel.append(label, textarea, submit);
    card.appendChild(panel);
    textarea.focus();
  }

  function renderPatchResult(evaluation, card, textarea) {
    const oldResult = card.querySelector(".patch-result");
    if (oldResult) oldResult.remove();

    const box = document.createElement("div");
    box.className = "patch-result";

    if (evaluation.result === "PATCHED") {
      showMessage("success", "✓ Hole patched. Carry on.");

      const success = document.createElement("div");
      success.className = "remaining-question";
      success.style.borderLeftColor = "var(--success)";
      success.append(
        makeText("strong", "", "✓ Hole patched. Carry on."),
        makeText("p", "", evaluation.explanation)
      );
      box.appendChild(success);

      const panel = card.querySelector(".patch-panel");
      if (panel) {
        panel.querySelector("button").disabled = true;
        panel.querySelector("textarea").disabled = true;
      }
    } else {
      const kind =
        evaluation.result === "PARTIALLY_PATCHED" ? "warning" : "error";
      const heading =
        evaluation.result === "PARTIALLY_PATCHED"
          ? "⚠ Partial patch."
          : "🚫 Original risk remains.";

      showMessage(kind, heading);

      const remaining = document.createElement("div");
      remaining.className = "remaining-question";
      remaining.append(
        makeText("strong", "", heading),
        makeText("p", "", evaluation.explanation),
        makeText("p", "", evaluation.remaining_question || "")
      );
      box.appendChild(remaining);

      textarea.focus();
    }

    card.appendChild(box);
  }

  async function analyze() {
    const context = contextEl.value.trim();
    if (!context) {
      showMessage("error", "Give me something to poke holes in first.");
      contextEl.focus();
      return;
    }

    hideMessage();
    clearResult();
    setBusy(true, "Poking holes…");

    try {
      const response = await postJson("/analyze_context", {
        context,
        mode: "manual",
      });

      if (response.status === "CLEAR") {
        renderClear();
      } else {
        renderConcern(response);
      }
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setBusy(false);
    }
  }

  pokeBtn.addEventListener("click", analyze);

  contextEl.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      analyze();
    }
  });
})();
