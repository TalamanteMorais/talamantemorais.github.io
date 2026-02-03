/*
  INSTRUÇÕES GERAIS DE MANUTENÇÃO E ATUALIZAÇÃO
  Script geral de funcionalidades do site.
  As seções estão organizadas por blocos funcionais comentados.
*/

document.addEventListener("DOMContentLoaded", function () {

  /* ======================== VÍDEO INSTITUCIONAL (ARQUIVO LOCAL) ======================== */
  /* Exibição por play do usuário via <video>, sem autoplay e sem integração automática com YouTube */

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
        goToSlide(i, true);

        if (!isHovered) {
          setTimeout(() => { if (!isHovered) iniciarCarrossel(); }, 3000);
        }
      });
      dotsWrap.appendChild(b);
    }
  }

  if (carouselContainer && track && totalItems > 0) {
    iniciarCarrossel();

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
        goToSlide(indexSlide - 1, true);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goToSlide(indexSlide + 1, true);
      }
    });
  }

  atualizarTransform();

  /* ======================== FORMULÁRIO + reCAPTCHA ======================== */
  const form = document.getElementById("contato-form");

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const nomeEl = document.getElementById("nome");
      const emailEl = document.getElementById("email");
      const mensagemEl = document.getElementById("mensagem");
      const botao = form.querySelector("button[type='submit']");
      const mensagemSucesso = document.getElementById("mensagem-sucesso");

      const exibirMensagem = (texto) => {
        if (mensagemSucesso) {
          mensagemSucesso.style.display = "block";
          mensagemSucesso.innerText = texto;

          setTimeout(() => {
            mensagemSucesso.style.display = "none";
            mensagemSucesso.innerText = "";
          }, 5000);
        } else {
          alert(texto);
        }
      };

      if (!nomeEl || !emailEl || !mensagemEl || !botao) {
        console.error("Formulário: campos obrigatórios ou botão submit não encontrados.");
        exibirMensagem("Não foi possível enviar no momento. Atualize a página e tente novamente.");
        return;
      }

      const nome = nomeEl.value.trim();
      const email = emailEl.value.trim();
      const mensagem = mensagemEl.value.trim();
      const honeypot = form.querySelector('input[name="honeypot"]');

      if (!nome || !email || !mensagem) {
        exibirMensagem("Por favor, preencha todos os campos obrigatórios.");
        return;
      }

      if (honeypot && honeypot.value) {
        return;
      }

      botao.disabled = true;
      botao.innerText = "Enviando...";

      const tokenField = document.getElementById("g-recaptcha-response");
      if (!tokenField) {
        console.error("reCAPTCHA: campo hidden g-recaptcha-response não encontrado.");
        exibirMensagem("Erro ao carregar o reCAPTCHA. Atualize a página e tente novamente.");
        botao.innerText = "Enviar";
        botao.disabled = false;
        return;
      }

      const siteKey = "6LcIlF8sAAAAAOPXstdnTTRCUa6eK6W3AI40TpvL";

      const falhaRecaptcha = () => {
        console.error("reCAPTCHA: grecaptcha não definido.");
        exibirMensagem("Erro ao validar o reCAPTCHA. Atualize a página e tente novamente.");
        botao.innerText = "Enviar";
        botao.disabled = false;
      };

      const executarRecaptcha = () => {
        grecaptcha.ready(function () {
          grecaptcha.execute(siteKey, { action: "contato" }).then(function (token) {
            tokenField.value = token;

            const formData = new FormData(form);
            formData.set("g-recaptcha-response", token);
fetch(form.action, {
              method: "POST",
              body: formData,
              mode: "no-cors"
            })
              .then(() => {
                exibirMensagem("Mensagem enviada com sucesso.");
                form.reset();
              })
              .catch((error) => {
                console.error("Envio do formulário: erro:", error);
                exibirMensagem("Ocorreu um erro ao enviar sua mensagem. Tente novamente.");
              })
              .finally(() => {
                botao.innerText = "Enviar";
                botao.disabled = false;
              });
          });
        });
      };

      const carregarRecaptchaSeNecessario = (onReady) => {
        if (typeof grecaptcha !== "undefined" && grecaptcha && typeof grecaptcha.ready === "function") {
          onReady();
          return;
        }

        const existing =
          document.querySelector('script[data-recaptcha-v3="1"]') ||
          document.querySelector('script[src*="recaptcha/api.js?render="]');

        const esperarGrecaptcha = (tentativasRestantes) => {
          if (typeof grecaptcha !== "undefined" && grecaptcha && typeof grecaptcha.ready === "function") {
            onReady();
            return;
          }
          if (tentativasRestantes <= 0) {
            falhaRecaptcha();
            return;
          }
          setTimeout(() => esperarGrecaptcha(tentativasRestantes - 1), 50);
        };

        if (existing) {
          existing.addEventListener("load", () => esperarGrecaptcha(60), { once: true });
          existing.addEventListener("error", falhaRecaptcha, { once: true });
          esperarGrecaptcha(2);
          return;
        }

        const s = document.createElement("script");
        s.src = "https://www.google.com/recaptcha/api.js?render=" + encodeURIComponent(siteKey);
        s.defer = true;
        s.setAttribute("data-recaptcha-v3", "1");
        s.addEventListener("load", () => esperarGrecaptcha(60), { once: true });
        s.addEventListener("error", falhaRecaptcha, { once: true });
        document.head.appendChild(s);

        esperarGrecaptcha(2);
      };

      carregarRecaptchaSeNecessario(executarRecaptcha);
    });
  }

  /* ======================== LISTA DE LINKS — PUBLICAÇÕES JURÍDICAS (JSON) ======================== */
  const linksPublicacoesEl = document.getElementById("links-publicacoes");

  if (linksPublicacoesEl) {
    const jsonUrl = linksPublicacoesEl.getAttribute("data-json") || "links-publicacoes.json";
    fetch(jsonUrl, {
      cache: "no-store",
      credentials: "omit",
      referrerPolicy: "no-referrer"
    })
      .then((res) => {
        if (!res.ok) throw new Error("Falha ao carregar JSON de links.");
        return res.json();
      })
      .then((links) => {
        if (!Array.isArray(links)) return;

        const validos = links.filter((item) =>
          item &&
          typeof item === "object" &&
          typeof item.title === "string" &&
          item.title.trim() &&
          typeof item.url === "string" &&
          item.url.trim()
        );

        if (validos.length === 0) return;

        linksPublicacoesEl.innerHTML = "";

        validos.forEach((item) => {
          const li = document.createElement("li");
          const a = document.createElement("a");

          a.href = item.url.trim();
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          a.textContent = item.title.trim();

          li.appendChild(a);
          linksPublicacoesEl.appendChild(li);
        });
      })
      .catch((err) => {
        console.error(err);
      });
  }

  /* ======================== RODAPÉ — ANO AUTOMÁTICO ======================== */
  const anoEl = document.getElementById("ano");
  if (anoEl) anoEl.textContent = new Date().getFullYear();

});
