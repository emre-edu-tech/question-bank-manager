// Quiz-taking logic: per-question flow with lives.
// On load: POST /start to create an attempt. Each choice click answers that
// question immediately via POST /answer. Last question or game over triggers
// POST /finish automatically. Vanilla JS only, no dependencies.
(function () {
  // Tailwind classes used for dynamic states (kept as literals so the
  // Tailwind content scanner picks them up):
  // border-blue-600 bg-blue-100 border-green-600 bg-green-100 text-green-900
  // border-red-600 bg-red-100 text-red-900 border-gray-200 bg-gray-50
  // border-yellow-400 bg-yellow-100 bg-green-100 bg-red-100
  // opacity-60 pointer-events-none

  function init() {
    var container = document.getElementById("quiz-container");
    var scoreBanner = document.getElementById("score-banner");
    var scoreText = document.getElementById("score-text");
    var gameoverBanner = document.getElementById("gameover-banner");
    var livesHearts = document.getElementById("lives-hearts");
    var livesText = document.getElementById("lives-text");
    var errorBox = document.getElementById("quiz-error");
    if (!container) {
      return;
    }
    var slug = container.getAttribute("data-slug");
    var cards = Array.prototype.slice.call(
      container.querySelectorAll(".question-card")
    );
    var attemptId = null;
    var maxLives = 3;
    var answeredCount = 0;
    var finished = false;
    var quizStartTime = Date.now();
    var firstInteractionMs = {}; // question_id -> ms since quiz start
    var lastInteractionMs = 0;

    function showError(message) {
      if (errorBox) {
        errorBox.textContent = message;
        errorBox.classList.remove("hidden");
      }
    }

    function hideError() {
      if (errorBox) {
        errorBox.classList.add("hidden");
      }
    }

    function updateLives(lives) {
      if (livesHearts) {
        var full = "";
        var empty = "";
        for (var i = 0; i < lives; i++) {
          full += "❤️";
        }
        for (var j = 0; j < maxLives - lives; j++) {
          empty += "🤍";
        }
        livesHearts.textContent = full + empty;
      }
      if (livesText) {
        livesText.textContent =
          lives === 1 ? "1 canın kaldı" : lives + " canın kaldı";
      }
    }

    function lockCard(card) {
      var labels = card.querySelectorAll(".choice-label");
      labels.forEach(function (label) {
        label.classList.add("pointer-events-none");
      });
      var inputs = card.querySelectorAll(".choice-input");
      inputs.forEach(function (input) {
        input.disabled = true;
      });
      card.setAttribute("data-answered", "true");
    }

    function unlockCard(card) {
      var labels = card.querySelectorAll(".choice-label");
      labels.forEach(function (label) {
        label.classList.remove("pointer-events-none");
      });
      var inputs = card.querySelectorAll(".choice-input");
      inputs.forEach(function (input) {
        input.disabled = false;
        input.checked = false;
      });
      card.removeAttribute("data-answered");
    }

    function lockAllUnanswered() {
      cards.forEach(function (card) {
        if (!card.getAttribute("data-answered")) {
          lockCard(card);
          var inputs = card.querySelectorAll(".choice-input");
          inputs.forEach(function (input) {
            input.disabled = true;
          });
        }
      });
    }

    function paintAnswer(
      card,
      selected,
      correctChoice,
      isCorrect,
      xpAwarded,
      speedBonus
    ) {
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
        if (choice === correctChoice) {
          label.classList.add(
            "border-green-600",
            "bg-green-100",
            "text-green-900"
          );
        } else if (choice === selected && !isCorrect) {
          label.classList.add("border-red-600", "bg-red-100", "text-red-900");
        } else {
          label.classList.add("border-gray-200", "bg-gray-50", "opacity-60");
        }
      });
      var feedback = card.querySelector(".answer-feedback");
      if (feedback) {
        feedback.classList.remove("hidden");
        if (isCorrect) {
          feedback.textContent = "✅ Doğru!";
          if (speedBonus > 0) {
            feedback.textContent +=
              " +" + xpAwarded + " XP (+" + speedBonus + " hız bonusu!)";
          }
          feedback.classList.add("bg-green-100", "text-green-900");
          feedback.classList.remove("bg-red-100", "text-red-900");
        } else {
          feedback.textContent = "❌ Yanlış! Doğru cevap işaretlendi.";
          feedback.classList.add("bg-red-100", "text-red-900");
          feedback.classList.remove("bg-green-100", "text-green-900");
        }
      }
    }

    function showSummary(data) {
      if (scoreBanner && scoreText) {
        scoreText.textContent = data.score + " / " + data.total + " doğru";
        scoreBanner.classList.remove("hidden");
        var xpText = document.getElementById("xp-text");
        if (xpText && typeof data.xp_earned !== "undefined") {
          xpText.textContent =
            "+" +
            data.xp_earned +
            " Deneyim Puanı kazandın! Toplam: " +
            data.total_xp +
            " Deneyim Puanı — Seviye " +
            data.level_number +
            " (" +
            data.level_name +
            ")";
        }
        scoreBanner.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }

    function finishAttempt() {
      if (finished || attemptId === null) {
        return;
      }
      finished = true;
      fetch("/quizzes/" + encodeURIComponent(slug) + "/finish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ attempt_id: attemptId }),
      })
        .then(function (resp) {
          if (!resp.ok) {
            throw new Error("finish failed: " + resp.status);
          }
          return resp.json();
        })
        .then(function (data) {
          if (typeof data.lives_remaining !== "undefined") {
            updateLives(data.lives_remaining);
          }
          showSummary(data);
        })
        .catch(function () {
          finished = false;
          showError(
            "Sonuçlar alınırken bir hata oluştu. Lütfen sayfayı yenileyip tekrar dene."
          );
        });
    }

    function answerCard(card, selected) {
      if (
        finished ||
        attemptId === null ||
        card.getAttribute("data-answered")
      ) {
        return;
      }
      // Disable this question's inputs immediately (prevent double-answer).
      lockCard(card);
      hideError();
      var qid = card.getAttribute("data-question-id");

      // Elapsed time since this question was first interacted with, minus
      // the previous question's interaction time (0 for the first question).
      var firstMs = firstInteractionMs[qid];
      if (typeof firstMs === "undefined") {
        firstMs = Date.now() - quizStartTime;
        firstInteractionMs[qid] = firstMs;
      }
      var timeTakenSeconds = Math.max(0, (firstMs - lastInteractionMs) / 1000);
      lastInteractionMs = firstMs;

      fetch("/quizzes/" + encodeURIComponent(slug) + "/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          attempt_id: attemptId,
          question_id: parseInt(qid, 10),
          selected_choice: selected,
          time_taken_seconds: timeTakenSeconds,
        }),
      })
        .then(function (resp) {
          if (!resp.ok) {
            throw new Error("answer failed: " + resp.status);
          }
          return resp.json();
        })
        .then(function (data) {
          answeredCount += 1;
          paintAnswer(
            card,
            selected,
            data.correct_choice,
            data.is_correct,
            data.xp_awarded,
            data.speed_bonus
          );
          if (typeof data.lives_remaining !== "undefined") {
            updateLives(data.lives_remaining);
          }
          if (data.game_over) {
            lockAllUnanswered();
            if (gameoverBanner) {
              gameoverBanner.classList.remove("hidden");
              gameoverBanner.scrollIntoView({
                behavior: "smooth",
                block: "center",
              });
            }
            finishAttempt();
          } else if (answeredCount >= cards.length) {
            finishAttempt();
          }
        })
        .catch(function () {
          unlockCard(card);
          showError(
            "Cevap gönderilirken bir hata oluştu. Lütfen tekrar dene."
          );
        });
    }

    // Record the first interaction time per question (for speed bonus).
    cards.forEach(function (card) {
      var qid = card.getAttribute("data-question-id");
      var inputs = card.querySelectorAll(".choice-input");
      inputs.forEach(function (input) {
        input.addEventListener("change", function () {
          if (!(qid in firstInteractionMs)) {
            firstInteractionMs[qid] = Date.now() - quizStartTime;
          }
        });
      });
    });

    cards.forEach(function (card) {
      var inputs = card.querySelectorAll(".choice-input");
      inputs.forEach(function (input) {
        input.addEventListener("change", function () {
          if (finished || card.getAttribute("data-answered")) {
            return;
          }
          answerCard(card, input.value);
        });
      });
    });

    // Start the attempt on page load.
    fetch("/quizzes/" + encodeURIComponent(slug) + "/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    })
      .then(function (resp) {
        if (!resp.ok) {
          throw new Error("start failed: " + resp.status);
        }
        return resp.json();
      })
      .then(function (data) {
        attemptId = data.attempt_id;
        if (typeof data.lives_remaining !== "undefined") {
          maxLives = data.lives_remaining;
          updateLives(data.lives_remaining);
        }
      })
      .catch(function () {
        lockAllUnanswered();
        showError(
          "Quiz başlatılamadı. Lütfen sayfayı yenileyip tekrar dene."
        );
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
