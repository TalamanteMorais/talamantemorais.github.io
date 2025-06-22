// scripts.js – Funcionalidades aprimoradas do site Talamante Morais

window.addEventListener("DOMContentLoaded", function () {
  // ======================== RODAPÉ – Ano automático ========================
  const anoAtual = document.getElementById("anoAtual");
  if (anoAtual) {
    anoAtual.textContent = new Date().getFullYear();
  }

  // ======================== MENU – Scroll suave para âncoras ========================
  const linksMenu = document.querySelectorAll("nav a[href^='#']");
  linksMenu.forEach((link) => {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const id = this.getAttribute("href").substring(1);
      const target = document.getElementById(id);
      if (target) {
        target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  // ======================== MENU – Destacar link ativo conforme rolagem ========================
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll("nav a[href^='#']");

  function destacarMenu() {
    const scrollPos = Math.round(window.scrollY || window.pageYOffset);

    sections.forEach((section) => {
      const top = section.offsetTop - 100;
      const height = section.offsetHeight;
      const id = section.getAttribute("id");

      if (scrollPos >= top && scrollPos < top + height) {
        navLinks.forEach((link) => {
          link.classList.remove("active");
          if (link.getAttribute("href").substring(1) === id) {
            link.classList.add("active");
          }
        });
      }
    });
  }

  window.addEventListener("scroll", destacarMenu);
  destacarMenu();

  // ======================== FORMULÁRIO – Validação e envio ========================
  const form = document.querySelector("form");
  if (form) {
    form.addEventListener("submit", function (e) {
      const nome = form.querySelector('input[name="nome"]');
      const email = form.querySelector('input[name="email"]');
      const mensagem = form.querySelector('textarea[name="mensagem"]');
      const botaoEnviar = form.querySelector('button[type="submit"]');

      const msgCamposObrigatorios = "Por favor, preencha todos os campos obrigatórios.";
      const msgEmailInvalido = "Por favor, informe um e-mail válido.";

      if (!nome.value.trim() || !email.value.trim() || !mensagem.value.trim()) {
        e.preventDefault();
        alert(msgCamposObrigatorios);
        return;
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email.value.trim())) {
        e.preventDefault();
        alert(msgEmailInvalido);
        return;
      }

      botaoEnviar.disabled = true;
      botaoEnviar.textContent = "Enviando...";
    });
  }

  // ======================== FORMULÁRIO – Mensagem de sucesso com fade-out ========================
  const params = new URLSearchParams(window.location.search);
  if (params.get("sucesso") === "true") {
    const mensagem = document.getElementById("mensagem-sucesso");
    if (mensagem) {
      mensagem.style.display = "block";
      mensagem.style.opacity = 0;
      mensagem.style.transition = "opacity 0.8s ease-in-out";
      mensagem.setAttribute("tabindex", "-1");
      mensagem.focus();

      setTimeout(() => {
        mensagem.style.opacity = 1;
      }, 100);

      setTimeout(() => {
        mensagem.style.opacity = 0;
      }, 6000);

      setTimeout(() => {
        if (mensagem.parentNode) {
          mensagem.parentNode.removeChild(mensagem);
        }
      }, 6800);
    }
  }

// ======================== INÍCIO: Execução do reCAPTCHA v3 ========================
if (typeof grecaptcha !== "undefined") {
  grecaptcha.ready(function () {
    grecaptcha.execute('6LdEyWYrAAAAALdfXa6R6BprCQbpPW7KxuySJr43', { action: 'submit' }).then(function (token) {
      const tokenField = document.getElementById('recaptcha-token');
      if (tokenField) {
        tokenField.value = token;
      }
    });
  });
}
// ======================== FIM: Execução do reCAPTCHA v3 ========================

});
