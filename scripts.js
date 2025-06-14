// scripts.js – Funções básicas do site Talamante Morais

// Atualiza automaticamente o ano no rodapé, se não estiver em inline no HTML
window.addEventListener("DOMContentLoaded", function () {
  var anoAtual = document.getElementById('anoAtual');
  if (anoAtual) {
    anoAtual.textContent = new Date().getFullYear();
  }
});

// Exibe alerta visual após envio do formulário via Google Apps Script
document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('form');
  if (form) {
    form.addEventListener('submit', function () {
      setTimeout(() => {
        alert("✅ Mensagem enviada com sucesso!\n\nObrigado pelo contato. Retornaremos em breve.");
      }, 300);
    });
  }
});
