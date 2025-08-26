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
let isHovered = false; // flag de hover
let lastStart = 0;     // proteção contra reinício em sequência
const RESTART_GAP_MS = 300;

// Controle fino de cadência para evitar “saltos” em cliques/toques rápidos
const AUTO_INTERVAL_MS = 4000;   // intervalo do autoplay
const SLIDE_MIN_GAP_MS = 900;    // tempo mínimo entre trocas
let lastMoveAt = 0;              // último momento de troca
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

  const now = Date.now();
  if (now - lastMoveAt < SLIDE_MIN_GAP_MS) return; // evita trocas muito rápidas
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

// Botões Prev/Next — retoma autoplay ~3s após interação
if (prevBtn) prevBtn.addEventListener("click", () => {
  pararCarrossel();
  goToSlide(indexSlide - 1);
  if (!isHovered) {
    setTimeout(() => { if (!isHovered) iniciarCarrossel(); }, 3000);
  }
});
if (nextBtn) nextBtn.addEventListener("click", () => {
  pararCarrossel();
  goToSlide(indexSlide + 1);
  if (!isHovered) {
    setTimeout(() => { if (!isHovered) iniciarCarrossel(); }, 3000);
  }
});

// Paginação (bolinhas) — retoma autoplay ~3s após clique
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

  // Evita pausar imediatamente no carregamento se o cursor já estiver sobre o carrossel
  let interactionsReady = false;
  setTimeout(() => { interactionsReady = true; }, 800);

  // Hover/Toque pausa/retoma + Swipe (arrasto horizontal)
  carouselContainer.addEventListener("mouseenter", () => {
    if (!interactionsReady) return; // só passa a pausar após o pequeno delay
    isHovered = true;
    pararCarrossel();
  });
  carouselContainer.addEventListener("mouseleave", () => {
    isHovered = false;
    iniciarCarrossel();
  });

  // Dados de swipe
  let swipe = {
    dragging: false,
    startX: 0,
    deltaX: 0,
    width: 0,
    threshold: 0
  };

  // Início do toque/arrasto
  carouselContainer.addEventListener("pointerdown", (e) => {
    isHovered = true;
    pararCarrossel();

    swipe.dragging = true;
    swipe.startX = e.clientX;
    swipe.width = carouselContainer.clientWidth || 1;
    swipe.threshold = Math.max(40, swipe.width * 0.12); // ~12% da largura (mín. 40px)
    swipe.deltaX = 0;

    // desliga a transição para mover “na mão”
    track.style.transition = "none";

    try { carouselContainer.setPointerCapture(e.pointerId); } catch (_) {}
  });

  // Movimento do arrasto
  carouselContainer.addEventListener("pointermove", (e) => {
    if (!swipe.dragging) return;

    swipe.deltaX = e.clientX - swipe.startX;
    const deltaPct = (swipe.deltaX / swipe.width) * 100;

    // aplica o deslocamento relativo ao slide atual
    track.style.transform = `translateX(calc(${-indexSlide * 100}% + ${deltaPct}%))`;
  });

  // Fim/cancelamento do arrasto
  function finalizarSwipe(commit) {
    // restaura a transição padrão
    track.style.transition = "";

    if (commit && Math.abs(swipe.deltaX) > swipe.threshold) {
      if (swipe.deltaX < 0) {
        goToSlide(indexSlide + 1); // arrasto p/ esquerda -> próximo
      } else {
        goToSlide(indexSlide - 1); // arrasto p/ direita -> anterior
      }
    } else {
      // volta para a posição do slide atual
      atualizarTransform();
    }

    swipe.dragging = false;
    swipe.startX = 0;
    swipe.deltaX = 0;
    isHovered = false;
    iniciarCarrossel();
  }

  // Pausa quando a aba fica oculta e retoma quando volta (evita reiniciar se estiver em hover)
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      pararCarrossel();
    } else if (!isHovered) {
      iniciarCarrossel();
    }
  });

  // Pausa enquanto o foco estiver dentro do carrossel; retoma ao sair
  carouselContainer.addEventListener("focusin", pararCarrossel);
  carouselContainer.addEventListener("focusout", () => {
    if (!isHovered) iniciarCarrossel();
  });

  // Pausa quando o carrossel sai do viewport; retoma quando volta (economia de recursos)
  if ('IntersectionObserver' in window) {
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

  // Navegação por teclado (← →)

// Navegação por teclado (← →)
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

  // Estado inicial
  atualizarTransform();

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

// (removido: inicialização duplicada — já iniciamos/pausamos o carrossel no bloco principal)

