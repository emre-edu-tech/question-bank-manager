// Quiz-taking logic: selection styling, validation, submit via fetch, results reveal.
// Vanilla JS only, no dependencies.
(function () {
  // Tailwind classes used for dynamic states (kept as literals so the
  // Tailwind content scanner picks them up):
  // border-blue-600 bg-blue-100 border-green-600 bg-green-100 text-green-900
  // border-red-600 bg-red-100 text-red-900 border-gray-200 bg-gray-50
  // border-yellow-400 bg-yellow-100 opacity-60 pointer-events-none

  function init() {
    var container = document.getElementById("quiz-container");
    var submitBtn = document.getElementById("submit-btn");
    var scoreBanner = document.getElementById("score-banner");
    var scoreText = document.getElementById("score-text");
    var errorBox = document.getElementById("quiz-error");
    if (!container || !submitBtn) {
      return;
    }
    var slug = container.getAttribute("data-slug");
    var cards = Array.prototype.slice.call(
      container.querySelectorAll(".question-card")
    );
    var submitted = false;

    function paintChoices(card) {
      var labels = card.querySelectorAll(".choice-label");
      labels.forEach(function (label) {
        var input = label.querySelector(".choice-input");
        var selected = input && input.checked;
        label.classList.remove(
          "border-blue-600",
          "bg-blue-100",
          "border-gray-200",
          "bg-gray-50"
        );
        if (selected) {
          label.classList.add("border-blue-600", "bg-blue-100");
        } else {
          label.classList.add("border-gray-200", "bg-gray-50");
        }
      });
    }

    cards.forEach(function (card) {
      var inputs = card.querySelectorAll(".choice-input");
      inputs.forEach(function (input) {
        input.addEventListener("change", function () {
          if (submitted) {
            return;
          }
          paintChoices(card);
          var warning = card.querySelector(".unanswered-warning");
          if (warning) {
            warning.classList.add("hidden");
          }
          card.classList.remove("border-red-400");
          if (errorBox) {
            errorBox.classList.add("hidden");
          }
        });
      });
    });

    function collectAnswers() {
      var answers = {};
      var unanswered = [];
      cards.forEach(function (card) {
        var qid = card.getAttribute("data-question-id");
        var checked = card.querySelector(".choice-input:checked");
        if (checked) {
          answers[qid] = checked.value;
        } else {
          unanswered.push(card);
        }
      });
      return { answers: answers, unanswered: unanswered };
    }

    function showUnanswered(unanswered) {
      unanswered.forEach(function (card) {
        var warning = card.querySelector(".unanswered-warning");
        if (warning) {
          warning.classList.remove("hidden");
        }
      });
      if (errorBox) {
        var n = unanswered.length;
        errorBox.textContent =
          n === 1
            ? "1 soruyu cevaplamadın. Devam etmek için yukarıdaki işaretli soruyu cevapla."
            : n + " soruyu cevaplamadın. Devam etmek için yukarıdaki işaretli soruları cevapla.";
        errorBox.classList.remove("hidden");
      }
      if (unanswered[0] && unanswered[0].scrollIntoView) {
        unanswered[0].scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }

    function lockQuiz() {
      submitted = true;
      submitBtn.disabled = true;
      cards.forEach(function (card) {
        var labels = card.querySelectorAll(".choice-label");
        labels.forEach(function (label) {
          label.classList.add("pointer-events-none");
        });
        var inputs = card.querySelectorAll(".choice-input");
        inputs.forEach(function (input) {
          input.disabled = true;
        });
      });
    }

    function revealResults(data) {
      if (scoreBanner && scoreText) {
        scoreText.textContent = data.score + " / " + data.total + " doğru";
        scoreBanner.classList.remove("hidden");
        scoreBanner.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      var byId = {};
      (data.results || []).forEach(function (r) {
        byId[String(r.question_id)] = r;
      });
      cards.forEach(function (card) {
        var qid = card.getAttribute("data-question-id");
        var result = byId[String(qid)];
        if (!result) {
          return;
        }
        var labels = card.querySelectorAll(".choice-label");
        labels.forEach(function (label) {
          var choice = label.getAttribute("data-choice");
          label.classList.remove(
            "border-blue-600",
            "bg-blue-100",
            "border-gray-200",
            "bg-gray-50",
            "hover:border-blue-400",
            "hover:bg-blue-50"
          );
          if (choice === result.correct_choice) {
            label.classList.add(
              "border-green-600",
              "bg-green-100",
              "text-green-900"
            );
          } else if (choice === result.selected && !result.is_correct) {
            label.classList.add(
              "border-red-600",
              "bg-red-100",
              "text-red-900"
            );
          } else {
            label.classList.add(
              "border-gray-200",
              "bg-gray-50",
              "opacity-60"
            );
          }
        });
      });
    }

    submitBtn.addEventListener("click", function () {
      if (submitted || submitBtn.disabled) {
        return;
      }
      var collected = collectAnswers();
      if (collected.unanswered.length > 0) {
        showUnanswered(collected.unanswered);
        return;
      }
      if (errorBox) {
        errorBox.classList.add("hidden");
      }
      submitted = true;
      submitBtn.disabled = true;
      var originalText = submitBtn.textContent;
      submitBtn.textContent = "Kontrol ediliyor...";

      fetch("/quizzes/" + encodeURIComponent(slug) + "/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collected.answers),
      })
        .then(function (resp) {
          if (!resp.ok) {
            throw new Error("submit failed: " + resp.status);
          }
          return resp.json();
        })
        .then(function (data) {
          lockQuiz();
          submitBtn.textContent = "Gönderildi ✓";
          revealResults(data);
        })
        .catch(function () {
          submitted = false;
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
          if (errorBox) {
            errorBox.textContent =
              "Cevaplar gönderilirken bir hata oluştu. Lütfen tekrar dene.";
            errorBox.classList.remove("hidden");
          }
        });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
