(() => {
  const contextEl = document.getElementById("context");
  const pokeBtn = document.getElementById("poke");
  const statusEl = document.getElementById("status");
  const statusTextEl = document.getElementById("status-text");
  const resultEl = document.getElementById("result");
  const messageEl = document.getElementById("message");
  const bootLogEl = document.getElementById("boot-log");
  const runtimeStateEl = document.getElementById("runtime-state");
  const yearEl = document.getElementById("system-year");

  const POKE_LABEL = "[ POKE HOLES ] ── ONE QUESTION. HIGHEST LEVERAGE.";
  const LOADING_MESSAGES = [
    "SCANNING FOR FATAL FLAWS",
    "LOCATING YOUR BLIND SPOTS",
    "CONSULTING THE VOID",
    "IDENTIFYING WRONG ASSUMPTIONS",
    "PREPARING UNCOMFORTABLE TRUTH",
  ];
  const BOOT_LINES = [
    "INITIALIZING ADVERSARIAL SUBSYSTEM...",
    "LOADING ASSUMPTION DATABASE... OK",
    "CALIBRATING SARCASM THRESHOLD... OK",
    "COURAGE COMPUTER v4.1.9 READY.",
    "> AWAITING INPUT_",
  ];

  let currentConcern = null;
  let loadingInterval = null;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  yearEl.textContent = `[${new Date().getFullYear()}.SYS]`;

  function boot() {
    if (!bootLogEl) return;
    if (reduceMotion) {
      BOOT_LINES.forEach((line) => bootLogEl.appendChild(makeText("p", "", line)));
      return;
    }

    let index = 0;
    const next = () => {
      if (index >= BOOT_LINES.length) return;
      bootLogEl.appendChild(makeText("p", "", BOOT_LINES[index]));
      index += 1;
      window.setTimeout(next, 180 + Math.random() * 170);
    };
    window.setTimeout(next, 240);
  }

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

  function setBusy(busy, text = "SCANNING FOR FATAL FLAWS") {
    pokeBtn.disabled = busy;
    contextEl.disabled = busy;
    statusEl.hidden = !busy;

    if (loadingInterval) {
      window.clearInterval(loadingInterval);
      loadingInterval = null;
    }

    if (busy) {
      runtimeStateEl.textContent = "PROCESSING...";
      let index = 0;
      statusTextEl.textContent = `${text}...`;
      pokeBtn.textContent = `${text}...`;

      loadingInterval = window.setInterval(() => {
        index = (index + 1) % LOADING_MESSAGES.length;
        const message = LOADING_MESSAGES[index];
        statusTextEl.textContent = `${message}...`;
        pokeBtn.textContent = `${message}...`;
      }, 620);
    } else {
      pokeBtn.textContent = POKE_LABEL;
      runtimeStateEl.textContent = resultEl.hidden ? "AWAITING INPUT" : "QUERY COMPLETE";
    }
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
    runtimeStateEl.textContent = "AWAITING INPUT";
  }

  function makeText(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = text ?? "";
    return el;
  }

  function makeMeta(label, value) {
    const wrapper = document.createElement("div");
    wrapper.className = "meta";
    wrapper.append(
      makeText("span", "meta-label", label),
      makeText("p", "meta-value", value)
    );
    return wrapper;
  }

  function typeQuestion(element, text, onDone) {
    const finalText = `“${text}”`;
    if (reduceMotion) {
      element.textContent = finalText;
      onDone();
      return;
    }

    let index = 0;
    element.textContent = "";
    element.classList.add("typing-cursor");
    const timer = window.setInterval(() => {
      index += 1;
      element.textContent = finalText.slice(0, index);
      if (index >= finalText.length) {
        window.clearInterval(timer);
        element.classList.remove("typing-cursor");
        onDone();
      }
    }, 18);
  }

  function createOutputHeader(filename, severity = "") {
    const header = document.createElement("div");
    header.className = "output-header";
    header.appendChild(makeText("span", "", `OUTPUT ── ${filename}`));

    if (severity) {
      const sev = String(severity).toLowerCase();
      header.appendChild(
        makeText("span", `severity-${sev}`, `SEVERITY: ${sev.toUpperCase()}`)
      );
    }
    return header;
  }

  function renderClear() {
    clearResult();
    const card = document.createElement("article");
    card.className = "state-card";
    card.append(
      makeText("h2", "", "✓ NO HOLE WORTH STOPPING FOR. CARRY ON."),
      makeText(
        "p",
        "",
        "Nothing in this context currently justifies interrupting your momentum. Suspicious. Enjoy it while it lasts."
      ),
      makeText("p", "twit", "YOU TWIT.")
    );
    resultEl.appendChild(card);
    resultEl.hidden = false;
    runtimeStateEl.textContent = "QUERY COMPLETE";
  }

  function renderConcern(concern) {
    clearResult();
    currentConcern = { ...concern };

    const card = document.createElement("article");
    card.className = "output-card";
    card.appendChild(createOutputHeader("CRITICAL_VECTOR_IDENTIFIED.TXT", concern.severity));

    const body = document.createElement("div");
    body.className = "output-body";
    body.appendChild(makeText("p", "output-label", "> THE QUESTION YOU HAVEN'T ASKED:"));

    const question = makeText("h2", "question", "");
    body.appendChild(question);

    const details = document.createElement("div");
    details.className = "details";
    details.append(
      makeMeta("ASSUMPTION", concern.assumption),
      makeMeta("WHY NOW", concern.why_now),
      makeMeta("WHAT COULD BREAK", concern.failure_if_ignored),
      makeMeta("EVIDENCE", concern.evidence)
    );

    const actions = document.createElement("div");
    actions.className = "card-actions";

    const resetBtn = makeText("button", "secondary", "< RESET_QUERY.EXE");
    resetBtn.type = "button";
    resetBtn.addEventListener("click", resetQuery);

    const followBtn = makeText("button", "secondary", "FOLLOW UP");
    followBtn.type = "button";
    followBtn.addEventListener("click", () => showFollowUpPanel(card));

    const patchBtn = makeText("button", "primary", "I'VE PATCHED IT!");
    patchBtn.type = "button";
    patchBtn.addEventListener("click", () => showPatchPanel(card));

    actions.append(
      resetBtn,
      followBtn,
      patchBtn,
      makeText("span", "twit", "YOU TWIT.")
    );

    details.appendChild(actions);
    body.appendChild(details);
    card.appendChild(body);
    resultEl.appendChild(card);
    resultEl.hidden = false;
    runtimeStateEl.textContent = "QUERY COMPLETE";

    typeQuestion(question, concern.question, () => {
      details.classList.add("visible");
    });
  }

  function showFollowUpPanel(card) {
    const existing = card.querySelector(".follow-up-panel");
    if (existing) {
      existing.querySelector("textarea")?.focus();
      return;
    }

    const body = card.querySelector(".output-body");
    const panel = document.createElement("div");
    panel.className = "patch-panel follow-up-panel";

    const label = makeText("label", "", "> CHALLENGE_SCOPE.TXT");
    label.htmlFor = "follow-up";

    const textarea = document.createElement("textarea");
    textarea.id = "follow-up";
    textarea.className = "resolution-input";
    textarea.placeholder =
      "> add context, push back, or explain why this concern may not belong in scope_";

    const submit = makeText("button", "secondary", "[ CHECK RELEVANCE ]");
    submit.type = "button";
    submit.addEventListener("click", async () => {
      const followUp = textarea.value.trim();
      if (!followUp) {
        showMessage("error", "FOLLOW-UP REJECTED: give the machine some context first.");
        textarea.focus();
        return;
      }

      hideMessage();
      submit.disabled = true;
      setBusy(true, "CHECKING WHETHER I OVERREACHED");

      try {
        const evaluation = await postJson("/follow_up", {
          original_concern: currentConcern,
          follow_up: followUp,
          updated_context: contextEl.value,
        });
        renderFollowUpResult(evaluation, card, textarea);
      } catch (error) {
        showMessage("error", error.message);
      } finally {
        submit.disabled = false;
        setBusy(false);
      }
    });

    panel.append(label, textarea, submit);
    body.appendChild(panel);
    textarea.focus();
  }

  function renderFollowUpResult(evaluation, card, textarea) {
    const oldResult = card.querySelector(".follow-up-result");
    if (oldResult) oldResult.remove();

    const box = document.createElement("div");
    box.className = "patch-result follow-up-result";
    const result = document.createElement("div");
    result.className = "remaining-question";

    if (evaluation.result === "OUT_OF_SCOPE") {
      showMessage("success", "✓ OUT OF SCOPE. DROPPING IT.");
      result.style.borderLeftColor = "var(--success)";
      result.append(
        makeText("strong", "", "✓ OUT OF SCOPE. DROPPING IT."),
        makeText("p", "", evaluation.explanation)
      );

      const buttons = card.querySelectorAll(".card-actions button");
      buttons.forEach((button) => {
        if (button.textContent !== "< RESET_QUERY.EXE") button.disabled = true;
      });
      const panel = card.querySelector(".follow-up-panel");
      if (panel) {
        panel.querySelector("button").disabled = true;
        panel.querySelector("textarea").disabled = true;
      }
    } else if (evaluation.result === "NEEDS_CONTEXT") {
      showMessage("warning", "? NEEDS CONTEXT. ONE MORE THING.");
      result.append(
        makeText("strong", "", "? NEEDS CONTEXT. ONE MORE THING."),
        makeText("p", "", evaluation.explanation),
        makeText("p", "", evaluation.follow_up_question || "")
      );
      textarea.focus();
    } else {
      showMessage("warning", "⚠ CONCERN STILL APPLIES.");
      result.append(
        makeText("strong", "", "⚠ CONCERN STILL APPLIES."),
        makeText("p", "", evaluation.explanation),
        makeText("p", "", evaluation.follow_up_question || "")
      );
    }

    box.appendChild(result);
    card.querySelector(".output-body").appendChild(box);
  }

  function showPatchPanel(card) {
    const existing = card.querySelector(".patch-panel:not(.follow-up-panel)");
    if (existing) {
      existing.querySelector("textarea")?.focus();
      return;
    }

    const body = card.querySelector(".output-body");
    const panel = document.createElement("div");
    panel.className = "patch-panel";

    const label = makeText("label", "", "> DESCRIBE_PATCH.TXT");
    label.htmlFor = "resolution";

    const textarea = document.createElement("textarea");
    textarea.id = "resolution";
    textarea.className = "resolution-input";
    textarea.placeholder =
      "> tell the machine what changed, what you tested, or what evidence closes the hole_";

    const submit = makeText("button", "primary", "[ EVALUATE PATCH ]");
    submit.type = "button";
    submit.addEventListener("click", async () => {
      const resolution = textarea.value.trim();
      if (!resolution) {
        showMessage("error", "PATCH REJECTED: you have to actually type something, you twit.");
        textarea.focus();
        return;
      }

      hideMessage();
      submit.disabled = true;
      setBusy(true, "EVALUATING YOUR EXCUSE");

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
    body.appendChild(panel);
    textarea.focus();
  }

  function renderPatchResult(evaluation, card, textarea) {
    const oldResult = card.querySelector(".patch-result:not(.follow-up-result)");
    if (oldResult) oldResult.remove();

    const box = document.createElement("div");
    box.className = "patch-result";

    if (evaluation.result === "PATCHED") {
      showMessage("success", "✓ HOLE PATCHED. CARRY ON.");
      const success = document.createElement("div");
      success.className = "remaining-question";
      success.style.borderLeftColor = "var(--success)";
      success.append(
        makeText("strong", "", "✓ HOLE PATCHED. CARRY ON."),
        makeText("p", "", evaluation.explanation),
        makeText("p", "twit", "YOU TWIT.")
      );
      box.appendChild(success);

      const panel = card.querySelector(".patch-panel:not(.follow-up-panel)");
      if (panel) {
        panel.querySelector("button").disabled = true;
        panel.querySelector("textarea").disabled = true;
      }
    } else {
      const kind = evaluation.result === "PARTIALLY_PATCHED" ? "warning" : "error";
      const heading =
        evaluation.result === "PARTIALLY_PATCHED"
          ? "⚠ PARTIAL PATCH. NICE TRY."
          : "🚫 STILL OPEN. SIT WITH IT.";

      showMessage(kind, heading);
      const remaining = document.createElement("div");
      remaining.className = "remaining-question";
      remaining.append(
        makeText("strong", "", heading),
        makeText("p", "", evaluation.explanation),
        makeText("p", "", evaluation.remaining_question || ""),
        makeText("p", "twit", "YOU TWIT.")
      );
      box.appendChild(remaining);
      textarea.focus();
    }

    if (evaluation.suggestion) {
      const suggestion = document.createElement("div");
      suggestion.className = "remaining-question";
      suggestion.append(
        makeText("strong", "", "> MAY I SUGGEST..."),
        makeText("p", "", evaluation.suggestion),
        makeText("p", "", "Optional. This does not affect the patch verdict.")
      );
      box.appendChild(suggestion);
    }

    card.querySelector(".output-body").appendChild(box);
  }

  async function analyze() {
    const context = contextEl.value.trim();
    if (!context) {
      showMessage("error", "INPUT ERROR: give me something to poke holes in first.");
      contextEl.focus();
      return;
    }

    hideMessage();
    clearResult();
    setBusy(true, LOADING_MESSAGES[0]);

    try {
      const response = await postJson("/analyze_context", {
        context,
        mode: "manual",
      });

      if (response.status === "CLEAR") renderClear();
      else renderConcern(response);
    } catch (error) {
      showMessage("error", error.message);
    } finally {
      setBusy(false);
    }
  }

  function resetQuery() {
    hideMessage();
    clearResult();
    contextEl.disabled = false;
    contextEl.focus();
  }

  pokeBtn.addEventListener("click", analyze);
  contextEl.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      analyze();
    }
  });

  boot();
})();