// scripts.js – Funções básicas do site Talamante Morais

// Atualiza automaticamente o ano no rodapé, se não estiver em inline no HTML
window.addEventListener("DOMContentLoaded", function () {
  var anoAtual = document.getElementById('anoAtual');
  if (anoAtual) {
    anoAtual.textContent = new Date().getFullYear();
  }
});

// Exibe mensagem de sucesso após envio do formulário se houver parâmetro na URL
(function () {
  var params = new URLSearchParams(window.location.search);
  if (params.get('sucesso') === 'true') {
    var msg = document.getElementById('mensagem-sucesso');
    if (msg) msg.style.display = 'block';
  }
})();
