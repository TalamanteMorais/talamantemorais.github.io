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
    carouselContainer.addEventListener("mouseleave", function () {
      iniciarCarrossel(); // reinicia corretamente sem pausar duplamente
    });
  }
});

// ======================== ENVIO DO FORMULÁRIO COM reCAPTCHA v3 ========================
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("contato-form");

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const nome = document.getElementById("nome").value.trim();
      const email = document.getElementById("email").value.trim();
      const mensagem = document.getElementById("mensagem").value.trim();
      const botao = form.querySelector("button[type='submit']");
      const mensagemSucesso = document.getElementById("mensagem-sucesso");

      if (!nome || !email || !mensagem) {
        alert("Por favor, preencha todos os campos obrigatórios.");
        return;
      }

      botao.disabled = true;
      botao.innerText = "Enviando...";

      grecaptcha.ready(function () {
        grecaptcha.execute('6LdEyWYrAAAAALdfXa6R6BprCQbpPW7KxuySJr43', { action: 'submit' }).then(function (token) {
          if (!token || token.trim() === "") {
            alert("Erro ao validar o reCAPTCHA. Atualize a página e tente novamente.");
            botao.disabled = false;
            botao.innerText = "Enviar";
            return;
          }

          fetch("https://script.google.com/macros/s/AKfycbzvgpuIDGGkpm6hj4WaV7TNVcIJe6BTbIqfjL2ItxrqW2z80ZwyU0Ik3arvIF6R-6Hg/exec", {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
              nome: nome,
              email: email,
              mensagem: mensagem,
              "g-recaptcha-response": token
            })
          })
          .then(response => response.text())
          .then(data => {
            if (data.includes("OK")) {
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
              form.reset();
            } else {
              alert("⚠️ Erro ao enviar: " + data);
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
});
