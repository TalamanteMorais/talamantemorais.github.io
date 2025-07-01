document.addEventListener("DOMContentLoaded", () => {
  // ======================== ATUALIZAÇÃO DE ANO ========================
  const ano = new Date().getFullYear();
  const anoSpan = document.getElementById("anoAtual");
  if (anoSpan) anoSpan.textContent = ano;

  // ======================== CARROSSEL ========================
  const track = document.querySelector(".carousel-track");
  const items = document.querySelectorAll(".carousel-item");
  const carouselContainer = document.querySelector(".carousel-container");
  const prevBtn = document.querySelector(".prev-btn");
  const nextBtn = document.querySelector(".next-btn");

  const totalItems = items.length;
  let index = 0;
  let intervalo;

  if (track && items.length > 0) {
    track.style.width = `${totalItems * 100}%`;
    items.forEach(item => {
      item.style.width = `${100 / totalItems}%`;
    });
    track.setAttribute("aria-live", "polite");

    const atualizarSlide = () => {
      track.style.transform = `translateX(-${index * (100 / totalItems)}%)`;
    };

    const iniciarCarrossel = () => {
      intervalo = setInterval(() => {
        index = (index + 1) % totalItems;
        atualizarSlide();
      }, 4000);
    };

    const pausarCarrossel = () => clearInterval(intervalo);

    const reiniciarCarrossel = () => {
      pausarCarrossel();
      iniciarCarrossel();
    };

    iniciarCarrossel();

    carouselContainer.addEventListener("mouseenter", pausarCarrossel);
    carouselContainer.addEventListener("mouseleave", iniciarCarrossel);

    if (prevBtn && nextBtn) {
      prevBtn.addEventListener("click", () => {
        index = (index - 1 + totalItems) % totalItems;
        atualizarSlide();
        reiniciarCarrossel();
      });

      nextBtn.addEventListener("click", () => {
        index = (index + 1) % totalItems;
        atualizarSlide();
        reiniciarCarrossel();
      });
    }
  }

  // ======================== FORMULÁRIO COM reCAPTCHA v3 ========================
  const form = document.getElementById("contato-form");
  const mensagemSucesso = document.getElementById("mensagem-sucesso");

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();

      grecaptcha.ready(() => {
        grecaptcha.execute("6LdZFnQrAAAAABafHl6mffcrhuI8cbfsoGTm9cfL", { action: "submit" })
          .then((token) => {
            document.getElementById("recaptcha-token").value = token;

            const formData = new FormData(form);

            fetch(form.action, {
              method: "POST",
              body: formData
            })
              .then(response => response.text())
              .then(() => {
                if (mensagemSucesso) {
                  mensagemSucesso.style.display = "block";
                  form.reset();
                  setTimeout(() => {
                    mensagemSucesso.style.display = "none";
                  }, 6000);
                }
              })
              .catch(error => {
                console.error("Erro ao enviar:", error);
              });
          });
      });
    });
  }
});
