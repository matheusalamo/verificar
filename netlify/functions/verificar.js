const fs = require("fs");
const path = require("path");

const DB_PATH = "/tmp/verificacoes.json";
const WEBHOOK_URL = process.env.WEBHOOK_URL || "";
const DISCORD_TOKEN = process.env.DISCORD_TOKEN || "";
const GUILD_ID = process.env.GUILD_ID || "";

function lerDB() {
  try {
    return JSON.parse(fs.readFileSync(DB_PATH, "utf-8"));
  } catch {
    return {};
  }
}

function salvarDB(data) {
  try { fs.mkdirSync("/tmp", { recursive: true }); } catch {}
  fs.writeFileSync(DB_PATH, JSON.stringify(data, null, 2));
}

async function enviarWebhook(nome, idade, telefone, discordId) {
  if (!WEBHOOK_URL) return;
  const embed = {
    title: "Nova verificação recebida",
    color: idade >= 13 ? 0x5865f2 : 0xed4245,
    fields: [
      { name: "Nome", value: nome, inline: true },
      { name: "Idade", value: String(idade), inline: true },
      { name: "Telefone", value: telefone, inline: true },
      { name: "Discord ID", value: `<@${discordId}> (\`${discordId}\`)`, inline: false },
      { name: "Status", value: idade < 13 ? "🚫 Banido (menor de 13)" : "⏳ Pendente", inline: false },
    ],
    footer: { text: `Origem: Web • ID: ${discordId}` },
  };
  await fetch(WEBHOOK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ embeds: [embed] }),
  });
}

async function banirMembro(discordId) {
  if (!DISCORD_TOKEN || !GUILD_ID) return;
  await fetch(`https://discord.com/api/v10/guilds/${GUILD_ID}/bans/${discordId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bot ${DISCORD_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ delete_message_days: 0, reason: "Menor de 13 anos - verificação automática" }),
  });
}

exports.handler = async (event) => {
  try {
    if (event.httpMethod !== "POST") {
      return { statusCode: 405, body: "Método não permitido" };
    }

    const data = JSON.parse(event.body);
    const telefone = String(data.telefone || "").replace(/[\s\-\(\)]/g, "");
    const nome = (data.nome || "").trim();
    const idade = parseInt(data.idade);
    const discordId = parseInt(data.discord_id);

    if (!telefone || telefone.length < 10 || !/^\d+$/.test(telefone)) {
      return { statusCode: 400, body: JSON.stringify({ status: "erro", message: "Telefone inválido" }) };
    }
    if (!nome || nome.length < 2) {
      return { statusCode: 400, body: JSON.stringify({ status: "erro", message: "Nome inválido" }) };
    }
    if (isNaN(idade) || idade < 1 || idade > 150) {
      return { statusCode: 400, body: JSON.stringify({ status: "erro", message: "Idade inválida" }) };
    }
    if (isNaN(discordId) || discordId < 1000) {
      return { statusCode: 400, body: JSON.stringify({ status: "erro", message: "ID do Discord inválido" }) };
    }

    const db = lerDB();

    if (db[telefone] && db[telefone].status === "aprovado") {
      return { statusCode: 200, body: JSON.stringify({ status: "ja_verificado", message: "Este telefone já foi verificado." }) };
    }

    if (idade < 13) {
      await banirMembro(discordId);
    }

    db[telefone] = {
      nome,
      idade,
      telefone,
      discord_id: discordId,
      status: idade < 13 ? "banido" : "pendente",
      origem: "web",
      created_at: new Date().toISOString(),
    };

    salvarDB(db);
    await enviarWebhook(nome, idade, telefone, discordId);

    return {
      statusCode: 200,
      body: JSON.stringify({ status: "pendente", message: "Dados enviados para verificação. Aguarde aprovação." }),
    };
  } catch (err) {
    console.error("Erro:", err);
    return { statusCode: 500, body: JSON.stringify({ status: "erro", message: "Erro interno do servidor" }) };
  }
};
