/*
  INSTRUÇÕES GERAIS DE MANUTENÇÃO E ATUALIZAÇÃO
  Script geral de funcionalidades do site.
  As seções estão organizadas por blocos funcionais comentados.
*/



document.addEventListener("DOMContentLoaded", function () {

/* ======================== ÚLTIMO VÍDEO DO YOUTUBE ======================== */
(function () {

  const iframeUltimo = document.getElementById("ultimo-video-youtube");
  if (!iframeUltimo) return;
  const RSS_URL =
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCifA0MpzCwCYfiuQY4E6S9A";

  fetch(RSS_URL)
    .then(r => r.text())
    .then(str => {
      const xml = new window.DOMParser().parseFromString(str, "text/xml");
      const entry = xml.querySelector("entry > id");

      if (!entry) {
        iframeUltimo.src =
          "https://www.youtube-nocookie.com/embed/fy2a2YcozUE";
        return;
      }

      const fullId = entry.textContent.trim();
      const videoId = fullId.replace("yt:video:", "");

      iframeUltimo.src =
        "https://www.youtube-nocookie.com/embed/" + videoId;
      iframeUltimo.title =
        "Último vídeo publicado — carregamento automático";
    })
    .catch(() => {
      iframeUltimo.src =
        "https://www.youtube-nocookie.com/embed/fy2a2YcozUE";
    });
})();

  /* ======================== CARROSSEL ======================== */
  const track = document.querySelector(".carousel-track");
  const items = document.querySelectorAll(".carousel-item");
  const carouselContainer = document.querySelector(".carousel-container");

  if (track && !track.id) track.id = "carousel-track";

  items.forEach((el) => {
    el.addEventListener("dragstart", (e) => e.preventDefault());
  });

  const prevBtn = document.querySelector(".carousel-prev");
  const nextBtn = document.querySelector(".carousel-next");
  const dotsWrap = document.querySelector(".carousel-dots");

  const totalItems = items.length;
  let indexSlide = 0;
  let intervaloSlide;
  let isHovered = false;
  let lastStart = 0;
  const RESTART_GAP_MS = 300;

  const AUTO_INTERVAL_MS = 4000;
  const SLIDE_MIN_GAP_MS = 900;
  let lastMoveAt = 0;

  function atualizarTransform() {
    if (!track) return;
    track.style.transform = `translate3d(-${indexSlide * 100}%, 0, 0)`;

    if (dotsWrap && dotsWrap.children.length === totalItems) {
      [...dotsWrap.children].forEach((btn, i) => {
        if (i === indexSlide) btn.setAttribute("aria-current", "true");
        else btn.removeAttribute("aria-current");
      });
    }
  }
function goToSlide(n, manual = false) {
  if (!totalItems) return;

  const now = Date.now();
  if (!manual && now - lastMoveAt < SLIDE_MIN_GAP_MS) return;
  lastMoveAt = now;

  indexSlide = ((n % totalItems) + totalItems) % totalItems;
  atualizarTransform();
}

  function iniciarCarrossel() {
    if (!track || totalItems <= 1 || isHovered) return;

    const now = Date.now();
    if (now - lastStart < RESTART_GAP_MS) return;
    lastStart = now;

    pararCarrossel();
    intervaloSlide = setInterval(() => {
      goToSlide(indexSlide + 1);
    }, AUTO_INTERVAL_MS);
  }

  function pararCarrossel() {
    if (intervaloSlide) {
      clearInterval(intervaloSlide);
      intervaloSlide = null;
    }
  }
if (prevBtn) {
  prevBtn.addEventListener("pointerdown", (e) => {
    e.stopPropagation();
  });
  prevBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    pararCarrossel();
    goToSlide(indexSlide - 1, true);

    if (!isHovered) {
      setTimeout(() => { if (!isHovered) iniciarCarrossel(); }, 3000);
    }
  });
}
if (nextBtn) {
  nextBtn.addEventListener("pointerdown", (e) => {
    e.stopPropagation();
  });
  nextBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    pararCarrossel();
    goToSlide(indexSlide + 1, true);
    if (!isHovered) {
      setTimeout(() => { if (!isHovered) iniciarCarrossel(); }, 3000);
    }
  });
}
  if (dotsWrap && totalItems > 1) {
    dotsWrap.innerHTML = "";
    for (let i = 0; i < totalItems; i++) {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", `Ir para o slide ${i + 1}`);
      b.setAttribute("aria-controls", "carousel-track");
      b.addEventListener("click", () => {
        pararCarrossel();
        goToSlide(i);
        if (!isHovered) {
          setTimeout(() => { if (!isHovered) iniciarCarrossel(); }, 3000);
        }
      });
      dotsWrap.appendChild(b);
    }
  }

  if (carouselContainer && track && totalItems > 0) {
    iniciarCarrossel();

    let interactionsReady = false;
    setTimeout(() => { interactionsReady = true; }, 800);

    carouselContainer.addEventListener("mouseenter", () => {
      if (!interactionsReady) return;
      isHovered = true;
      pararCarrossel();
    });

    carouselContainer.addEventListener("mouseleave", () => {
      isHovered = false;
      iniciarCarrossel();
    });

    let swipe = {
      dragging: false,
      startX: 0,
      deltaX: 0,
      width: 0,
      threshold: 0
    };

    carouselContainer.addEventListener("pointerdown", (e) => {
      isHovered = true;
      pararCarrossel();

      swipe.dragging = true;
      swipe.startX = e.clientX;
      swipe.width = carouselContainer.clientWidth || 1;
      swipe.threshold = Math.max(40, swipe.width * 0.12);
      swipe.deltaX = 0;

      track.style.transition = "none";

      try { carouselContainer.setPointerCapture(e.pointerId); } catch (_) { }
    });

    carouselContainer.addEventListener("pointermove", (e) => {
      if (!swipe.dragging) return;

      swipe.deltaX = e.clientX - swipe.startX;
      const deltaPct = (swipe.deltaX / swipe.width) * 100;

      track.style.transform =
        `translate3d(calc(${-indexSlide * 100}% + ${deltaPct}%), 0, 0)`;
    });

    function finalizarSwipe(commit) {
      track.style.transition = "";

      if (commit && Math.abs(swipe.deltaX) > swipe.threshold) {
        if (swipe.deltaX < 0) {
          goToSlide(indexSlide + 1);
        } else {
          goToSlide(indexSlide - 1);
        }
      } else {
        atualizarTransform();
      }

      swipe.dragging = false;
      swipe.startX = 0;
      swipe.deltaX = 0;
      isHovered = false;
      iniciarCarrossel();
    }

    carouselContainer.addEventListener("pointerup", () => finalizarSwipe(true));
    carouselContainer.addEventListener("pointercancel", () => finalizarSwipe(false));
    carouselContainer.addEventListener("pointerleave", () => {
      if (swipe.dragging) finalizarSwipe(false);
    });

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) pararCarrossel();
      else if (!isHovered) iniciarCarrossel();
    });

    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => {
        const entry = entries[0];
        if (!entry) return;

        if (entry.isIntersecting) {
          if (!isHovered) iniciarCarrossel();
        } else {
          pararCarrossel();
        }
      }, { root: null, threshold: 0.25 });

      io.observe(carouselContainer);
    }
  }

  if (carouselContainer) {
    carouselContainer.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goToSlide(indexSlide - 1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goToSlide(indexSlide + 1);
      }
    });
  }

  atualizarTransform();

  /* ======================== FORMULÁRIO + reCAPTCHA ======================== */
  const form = document.getElementById("contato-form");

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const nome = document.getElementById("nome").value.trim();
      const email = document.getElementById("email").value.trim();
      const mensagem = document.getElementById("mensagem").value.trim();
      const botao = form.querySelector("button[type='submit']");
      const mensagemSucesso = document.getElementById("mensagem-sucesso");

      const honey = form.querySelector('input[name="honeypot"]');
      if (honey && honey.value) return;

      if (!nome || !email || !mensagem) {
        alert("Por favor, preencha todos os campos obrigatórios.");
        return;
      }

      botao.disabled = true;
      botao.innerText = "Enviando...";

      if (typeof grecaptcha === "undefined" ||
        typeof grecaptcha.ready !== "function") {
        alert("Erro ao carregar o reCAPTCHA. Atualize a página e tente novamente.");
        botao.disabled = false;
        botao.innerText = "Enviar";
        return;
      }

      grecaptcha.ready(function () {
        grecaptcha.execute('6LdEyWYrAAAAALdfXa6R6BprCQbpPW7KxuySJr43',
          { action: "submit" })
          .then(function (token) {
            if (!token || token.trim() === "") {
              alert("Erro ao validar o reCAPTCHA. Atualize a página e tente novamente.");
              botao.disabled = false;
              botao.innerText = "Enviar";
              return;
            }
fetch("https://script.google.com/macros/s/AKfycbzvgpuIDGGkpm6hj4WaV7TNVcIJe6BTbIqfjL2ItxrqW2z80ZwyU0Ik3arvIF6R-6Hg/exec", {
  method: "POST",
  credentials: "omit",
  referrerPolicy: "no-referrer",
  cache: "no-store",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({
    nome: nome,
    email: email,
    mensagem: mensagem,
    "g-recaptcha-response": token
  })
})
              .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.text();
              })
              .then(data => {
                const texto = String(data || "").toUpperCase();

                if (texto.includes("OK") || texto.includes("SUCCESS")) {
                  if (mensagemSucesso) {
                    mensagemSucesso.style.display = "block";
                    mensagemSucesso.innerText = "Mensagem enviada com sucesso.";

                    setTimeout(() => {
                      mensagemSucesso.style.display = "none";
                      mensagemSucesso.innerText = "";
                    }, 5000);
                  } else {
                    alert("Mensagem enviada com sucesso.");
                  }
                } else {
                  alert("Não foi possível confirmar o envio. Tente novamente.");
                }
              })
              .catch(error => {
                alert("Ocorreu um erro ao enviar sua mensagem. Tente novamente.");
                console.error("Erro:", error);
              })
              .finally(() => {
                botao.innerText = "Enviar";
                botao.disabled = false;
              });
          });
      });
    });
  }

  /* ======================== RODAPÉ — ANO AUTOMÁTICO ======================== */
  const anoEl = document.getElementById("ano");
  if (anoEl) anoEl.textContent = new Date().getFullYear();

});
