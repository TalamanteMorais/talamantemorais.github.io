// ======================== CARROSSEL AUTOMÁTICO TEMÁTICO ========================
document.addEventListener("DOMContentLoaded", function () {
  const track = document.querySelector(".carousel-track");
  const items = document.querySelectorAll(".carousel-item");
  const carouselContainer = document.querySelector(".carousel-container");
  const prevBtn = document.querySelector(".prev-btn");
  const nextBtn = document.querySelector(".next-btn");

  const totalItems = items.length;
  let index = 0;
  let intervalo;
// Ajusta dinamicamente a largura da trilha e dos itens com base no total de itens
if (track && items.length > 0) {
  track.style.width = `${totalItems * 100}%`;
  items.forEach(item => {
    item.style.width = `${100 / totalItems}%`;
  });
  track.setAttribute("aria-live", "polite");
}

function atualizarSlide() {
  if (track) {
    track.style.transform = `translateX(-${index * (100 / totalItems)}%)`;
  }
}
  function iniciarCarrossel() {
    intervalo = setInterval(() => {
      index = (index + 1) % totalItems;
      atualizarSlide();
    }, 4000); // 4 segundos entre slides
  }

  function pausarCarrossel() {
    clearInterval(intervalo);
  }

  if (carouselContainer && track && items.length > 0) {
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

  function reiniciarCarrossel() {
    pausarCarrossel();
    iniciarCarrossel();
  }
});
// Atualiza automaticamente o ano no rodapé
document.addEventListener("DOMContentLoaded", function () {
  const ano = new Date().getFullYear();
  const anoSpan = document.getElementById("anoAtual");
  if (anoSpan) anoSpan.textContent = ano;
});
// ======================== ENVIO DO FORMULÁRIO COM reCAPTCHA v3 ========================
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("contato-form");
  const mensagemSucesso = document.getElementById("mensagem-sucesso");

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      grecaptcha.ready(function () {

        grecaptcha.execute("6LeV_I0rAAAAAC-HV2gx4ckrF5t95NntLUJgzR6n", { action: "submit" }).then(function (token) {
          document.getElementById("recaptcha-token").value = token;
console.log("Token gerado:", token);

          const formData = new FormData(form);
          fetch(form.action, {
            method: "POST",
            body: formData
          })
            .then(response => response.text())
            .then(responseText => {
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
