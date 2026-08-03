const fs = require("node:fs");

const secrets = {
  PAINEL_USUARIO: process.env.PAINEL_USUARIO,
  PAINEL_SENHA: process.env.PAINEL_SENHA
};

if (!secrets.PAINEL_USUARIO || !secrets.PAINEL_SENHA) {
  throw new Error("Segredos do painel ausentes.");
}

fs.writeFileSync(
  "/tmp/painel-secrets.json",
  JSON.stringify(secrets),
  { encoding: "utf8", mode: 0o600 }
);
