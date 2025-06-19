// scripts.js – Funções básicas do site Talamante Morais

// Atualiza automaticamente o ano no rodapé, se não estiver em inline no HTML
window.addEventListener("DOMContentLoaded", function () {
  var anoAtual = document.getElementById('anoAtual');
  if (anoAtual) {
    anoAtual.textContent = new Date().getFullYear();
  }
});

// Exibe mensagem embutida na página após envio bem-sucedido do formulário
document.addEventListener("DOMContentLoaded", function () {
  const params = new URLSearchParams(window.location.search);
  if (params.get("sucesso") === "true") {
    const mensagem = document.getElementById("mensagem-sucesso");
    if (mensagem) {
      mensagem.style.display = "block";
      setTimeout(() => {
        mensagem.style.opacity = 1;
        mensagem.style.transition = "opacity 0.8s ease-in-out";
      }, 100);
      // Opcional: esconder automaticamente após 6 segundos
      setTimeout(() => {
        mensagem.style.opacity = 0;
      }, 6000);
    }
  }
});
