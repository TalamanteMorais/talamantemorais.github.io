// ======================== SCRIPT GERAL DO SITE ========================
document.addEventListener("DOMContentLoaded", function () {
  // ======================== CARROSSEL AUTOMÁTICO TEMÁTICO ========================
  const track = document.querySelector(".carousel-track");
  const items = document.querySelectorAll(".carousel-item");
  const carouselContainer = document.querySelector(".carousel-container");
  const totalItems = items.length;
  let indexSlide = 0;
  let intervaloSlide;

  function iniciarCarrossel() {
    if (!track || totalItems === 0) return;
    pararCarrossel(); // evita múltiplos intervals
    intervaloSlide = setInterval(() => {
      indexSlide = (indexSlide + 1) % totalItems;
      track.style.transform = `translateX(-${indexSlide * 100}%)`;
    }, 4000);
  }

  function pararCarrossel() {
    if (intervaloSlide) {
      clearInterval(intervaloSlide);
      intervaloSlide = null;
    }
  }

  if (carouselContainer && track && totalItems > 0) {
    // Respeita prefers-reduced-motion: desliga autoplay se o usuário preferir menos movimento
    const reduzMovimento = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduzMovimento) iniciarCarrossel();

    carouselContainer.addEventListener("mouseenter", pararCarrossel);
    carouselContainer.addEventListener("mouseleave", () => {
      if (!reduzMovimento) iniciarCarrossel();
    });

    // Pausa quando a aba fica oculta e retoma quando volta
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) pararCarrossel();
      else if (!reduzMovimento) iniciarCarrossel();
    });
  }

  // ======================== ROTAÇÃO DE FUNDO COM FADE ========================
  ;(() => {
    const bgFades = document.querySelectorAll('.bg-fade');
    if (!bgFades.length) return;

    const imagens = ['img/card_1.png', 'img/card_2.png', 'img/card_3.png'];
    let indexFundo = 0;

    // Pré-carrega as imagens para evitar flicker na troca
    imagens.forEach(src => { const pic = new Image(); pic.src = src; });

    // Define a primeira imagem com gradiente em todos
    bgFades.forEach(el => {
      el.style.backgroundImage =
        `linear-gradient(rgba(0,0,0,.45), rgba(0,0,0,.45)), url('${imagens[0]}')`;
    });

    setInterval(() => {
      indexFundo = (indexFundo + 1) % imagens.length;

      // fade-out
      bgFades.forEach(el => { el.style.opacity = 0; });

      setTimeout(() => {
        // troca imagem + fade-in
        bgFades.forEach(el => {
          el.style.backgroundImage =
            `linear-gradient(rgba(0,0,0,.45), rgba(0,0,0,.45)), url('${imagens[indexFundo]}')`;
          el.style.opacity = 1;
        });
      }, 600); // mantenha igual ao transition do CSS (.bg-fade)
    }, 4000);
  })();

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
      if (typeof grecaptcha === "undefined" || !grecaptcha.ready) {
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

