/*
  Carregador do reCAPTCHA v3 em arquivo externo.
  Motivo: a Content-Security-Policy do site não permite script embutido (inline).
  Carrega o reCAPTCHA apenas nos domínios oficiais cadastrados.
*/
(() => {
  const dominiosOficiais = new Set(["talamante-adv.com.br", "www.talamante-adv.com.br"]);
  const dominioOficial = dominiosOficiais.has(window.location.hostname);

  document.documentElement.dataset.recaptchaMode = dominioOficial ? "official" : "preview";
  if (!dominioOficial) return;

  const recaptchaScript = document.createElement("script");
  recaptchaScript.src = "https://www.google.com/recaptcha/api.js?render=6Ld0yF8sAAAAAN5JXxfuWIV3K2nhA9p-r4VWKGKo";
  recaptchaScript.defer = true;
  recaptchaScript.dataset.recaptchaV3 = "1";
  document.head.appendChild(recaptchaScript);
})();
