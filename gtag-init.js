/*
  INSTRUÇÕES GERAIS DE MANUTENÇÃO E ATUALIZAÇÃO
  Script de inicialização do Google Analytics.
  Não alterar o ID de medição sem atualização institucional.
*/

/* INICIALIZAÇÃO DO DATALAYER */

window.dataLayer = window.dataLayer || [];
function gtag(){ dataLayer.push(arguments); }
gtag('js', new Date());

/* CONFIGURAÇÃO DO GOOGLE ANALYTICS */

gtag('config', 'G-ZKCPTG7K1T', {
  anonymize_ip: true,
  allow_google_signals: false,
  allow_ad_personalization_signals: false
});
