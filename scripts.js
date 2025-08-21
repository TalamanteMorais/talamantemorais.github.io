// ======================== SCRIPT GERAL DO SITE ========================
document.addEventListener("DOMContentLoaded", function () {
// ======================== CARROSSEL AUTOMÁTICO TEMÁTICO ========================
  const track = document.querySelector(".carousel-track");
  const items = document.querySelectorAll(".carousel-item");
  const carouselContainer = document.querySelector(".carousel-container");
  const prevBtn = document.querySelector(".carousel-prev");
  const nextBtn = document.querySelector(".carousel-next");
  const dotsWrap = document.querySelector(".carousel-dots");

  const totalItems = items.length;
  let indexSlide = 0;
  let intervaloSlide;

  function atualizarTransform() {
    if (!track) return;
    track.style.transform = `translateX(-${indexSlide * 100}%)`;
    // Atualiza bullets
    if (dotsWrap && dotsWrap.children.length === totalItems) {
      [...dotsWrap.children].forEach((btn, i) => {
        if (i === indexSlide) btn.setAttribute("aria-current", "true");
        else btn.removeAttribute("aria-current");
      });
    }
  }

  function goToSlide(n) {
    if (!totalItems) return;
    indexSlide = (n + totalItems) % totalItems;
    atualizarTransform();
  }

  // Respeita prefers-reduced-motion: sem autoplay
  const reduzMovimento = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function iniciarCarrossel() {
    if (!track || totalItems === 0) return;
    pararCarrossel();
    if (reduzMovimento) return;
    intervaloSlide = setInterval(() => {
      goToSlide(indexSlide + 1);
    }, 4000);
  }

  function pararCarrossel() {
    if (intervaloSlide) {
      clearInterval(intervaloSlide);
      intervaloSlide = null;
    }
  }

  // Botões Prev/Next
  if (prevBtn) prevBtn.addEventListener("click", () => goToSlide(indexSlide - 1));
  if (nextBtn) nextBtn.addEventListener("click", () => goToSlide(indexSlide + 1));

  // Paginação (bullets)
  if (dotsWrap && totalItems > 1) {
    dotsWrap.innerHTML = "";
    for (let i = 0; i < totalItems; i++) {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", `Ir para o slide ${i + 1}`);
      b.setAttribute("aria-controls", "carousel-track");
      b.addEventListener("click", () => goToSlide(i));
      dotsWrap.appendChild(b);
    }
  }

  if (carouselContainer && track && totalItems > 0) {
    if (!reduzMovimento) iniciarCarrossel();

    // Hover pausa/retoma
    carouselContainer.addEventListener("mouseenter", pararCarrossel);
    carouselContainer.addEventListener("mouseleave", () => {
      if (!reduzMovimento) iniciarCarrossel();
    });

    // Pausa quando a aba fica oculta e retoma quando volta
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) pararCarrossel();
      else if (!reduzMovimento) iniciarCarrossel();
    });

    // Pausa enquanto o foco estiver dentro do carrossel; retoma ao sair
    carouselContainer.addEventListener("focusin", pararCarrossel);
    carouselContainer.addEventListener("focusout", () => {
      if (!reduzMovimento) iniciarCarrossel();
    });

    // Navegação por teclado (← →)
    carouselContainer.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goToSlide(indexSlide - 1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goToSlide(indexSlide + 1);
      }
    });

    // Estado inicial
    atualizarTransform();
  } // fecha if (carouselContainer && track && totalItems > 0)

/* (removido: bloco duplicado) */

  // ======================== ENVIO DO FORMULÁRIO COM reCAPTCHA v3 ========================
  const form = document.getElementById("contato-form");

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const nome = document.getElementById("nome").value.trim();
      const email = document.getElementById("email").value.trim();
      const mensagem = document.getElementById("mensagem").value.trim();
      const botao = form.querySelector("button[type='submit']");
      const mensagemSucesso = document.getElementById("mensagem-sucesso");

      // Honeypot opcional (campo oculto no HTML). Se existir e vier preenchido, aborta silenciosamente.
      const honey = form.querySelector('input[name="honeypot"]');
      if (honey && honey.value) return;

      if (!nome || !email || !mensagem) {
        alert("Por favor, preencha todos os campos obrigatórios.");
        return;
      }

      botao.disabled = true;
      botao.innerText = "Enviando...";
      // Guarda para reCAPTCHA ausente
      if (typeof grecaptcha === "undefined" || typeof grecaptcha.ready !== "function") {
        alert("Erro ao carregar o reCAPTCHA. Atualize a página e tente novamente.");
        botao.disabled = false;
        botao.innerText = "Enviar";
        return;
      }

      grecaptcha.ready(function () {
       grecaptcha.execute('6LdEyWYrAAAAALdfXa6R6BprCQbpPW7KxuySJr43', { action: 'submit' })
          .then(function (token) {
            if (!token || token.trim() === "") {
              alert("Erro ao validar o reCAPTCHA. Atualize a página e tente novamente.");
              botao.disabled = false;
              botao.innerText = "Enviar";
              return;
            }

            fetch("https://script.google.com/macros/s/AKfycbzvgpuIDGGkpm6hj4WaV7TNVcIJe6BTbIqfjL2ItxrqW2z80ZwyU0Ik3arvIF6R-6Hg/exec", {
              method: "POST",
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
                  mensagemSucesso.innerText = "✅ Mensagem enviada com sucesso!";
                  setTimeout(() => {
                    mensagemSucesso.style.display = "none";
                    mensagemSucesso.innerText = "";
                  }, 5000);
                } else {
                  alert("✅ Mensagem enviada com sucesso!");
                }
              } else {
                // Retorno não confirmou sucesso
                alert("⚠️ Não foi possível confirmar o envio. Tente novamente.");
                }
            })
            .catch(error => {
              alert("❌ Ocorreu um erro. Tente novamente.");
              console.error("Erro:", error);
            })
            .finally(() => {
              botao.disabled = false;
              botao.innerText = "Enviar";
            });
          });
      });
    });
  }

  // Atualiza o ano do rodapé
  const anoEl = document.getElementById("anoAtual");
  if (anoEl) anoEl.textContent = new Date().getFullYear();
});

