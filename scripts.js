// scripts.js – Funcionalidades aprimoradas do site Talamante Morais

window.addEventListener("DOMContentLoaded", function () {
  // Atualiza automaticamente o ano no rodapé
  const anoAtual = document.getElementById('anoAtual');
  if (anoAtual) {
    anoAtual.textContent = new Date().getFullYear();
  }

  // Scroll suave para links do menu que apontam para âncoras internas
  const linksMenu = document.querySelectorAll("nav a[href^='#']");
  linksMenu.forEach(link => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const id = this.getAttribute("href").substring(1);
      const target = document.getElementById(id);
      if (target) {
        target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  // Destacar link ativo do menu conforme a seção visível na tela
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll("nav a[href^='#']");
  function destacarMenu() {
    let scrollPos = window.scrollY || window.pageYOffset;
    sections.forEach(section => {
      const top = section.offsetTop - 100;
      const height = section.offsetHeight;
      const id = section.getAttribute('id');
      if (scrollPos >= top && scrollPos < top + height) {
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href').substring(1) === id) {
            link.classList.add('active');
          }
        });
      }
    });
  }
  window.addEventListener('scroll', destacarMenu);
  destacarMenu();

  // Validação simples e bloqueio de múltiplos envios no formulário
  const form = document.querySelector("form");
  if (form) {
    form.addEventListener("submit", function (e) {
      const nome = form.querySelector('input[name="nome"]');
      const email = form.querySelector('input[name="email"]');
      const mensagem = form.querySelector('textarea[name="mensagem"]');
      const botaoEnviar = form.querySelector('button[type="submit"]');

      if (!nome.value.trim() || !email.value.trim() || !mensagem.value.trim()) {
        e.preventDefault();
        alert("Por favor, preencha todos os campos obrigatórios.");
        return;
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email.value.trim())) {
        e.preventDefault();
        alert("Por favor, informe um e-mail válido.");
        return;
      }

      botaoEnviar.disabled = true;
      botaoEnviar.textContent = "Enviando...";
    });
  }

  // Exibe mensagem de sucesso com fade após envio
  const params = new URLSearchParams(window.location.search);
  if (params.get("sucesso") === "true") {
    const mensagem = document.getElementById("mensagem-sucesso");
    if (mensagem) {
      mensagem.style.display = "block";
      mensagem.style.opacity = 0;
      mensagem.style.transition = "opacity 0.8s ease-in-out";
      setTimeout(() => {
        mensagem.style.opacity = 1;
      }, 100);
      setTimeout(() => {
        mensagem.style.opacity = 0;
      }, 6000);
      setTimeout(() => {
        if (mensagem.parentNode) mensagem.parentNode.removeChild(mensagem);
      }, 6800);
    }
  }
});
