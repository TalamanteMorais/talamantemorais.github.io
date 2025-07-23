// ======================== CARROSSEL AUTOMÁTICO TEMÁTICO ========================
document.addEventListener("DOMContentLoaded", function () {
  const track = document.querySelector(".carousel-track");
  const items = document.querySelectorAll(".carousel-item");
  const totalItems = items.length;
  let index = 0;
  let intervalo;

  function iniciarCarrossel() {
    intervalo = setInterval(() => {
      index = (index + 1) % totalItems;
      track.style.transform = `translateX(-${index * 100}%)`;
    }, 4000); // Tempo de transição: 4 segundos
  }

  function pausarCarrossel() {
    clearInterval(intervalo);
  }

  const carouselContainer = document.querySelector(".carousel-container");
  if (carouselContainer && track && items.length > 0) {
    iniciarCarrossel();

    carouselContainer.addEventListener("mouseenter", pausarCarrossel);

    carouselContainer.addEventListener("mouseleave", () => {
      pausarCarrossel();
      iniciarCarrossel(); // reinicia corretamente
    });
  }
});
