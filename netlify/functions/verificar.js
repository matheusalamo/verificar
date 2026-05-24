import { readFile, writeFile, mkdir } from "node:fs/promises";
import { join } from "node:path";

const DB_PATH = "/tmp/verificacoes.json";
const WEBHOOK_URL = process.env.WEBHOOK_URL || "";
const DISCORD_TOKEN = process.env.DISCORD_TOKEN || "";
const GUILD_ID = process.env.GUILD_ID || "";

async function lerDB() {
  try {
    const data = await readFile(DB_PATH, "utf-8");
    return JSON.parse(data);
  } catch {
    return {};
  }
}

async function salvarDB(data) {
  await mkdir("/tmp", { recursive: true });
  await writeFile(DB_PATH, JSON.stringify(data, null, 2));
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

export default async (req) => {
  if (req.method !== "POST") {
    return new Response("Método não permitido", { status: 405 });
  }

  try {
    const data = await req.json();
    const telefone = String(data.telefone || "").replace(/[\s\-\(\)]/g, "");
    const nome = (data.nome || "").trim();
    const idade = parseInt(data.idade);
    const discordId = parseInt(data.discord_id);

    if (!telefone || telefone.length < 10 || !/^\d+$/.test(telefone)) {
      return Response.json({ status: "erro", message: "Telefone inválido" }, { status: 400 });
    }
    if (!nome || nome.length < 2) {
      return Response.json({ status: "erro", message: "Nome inválido" }, { status: 400 });
    }
    if (isNaN(idade) || idade < 1 || idade > 150) {
      return Response.json({ status: "erro", message: "Idade inválida" }, { status: 400 });
    }
    if (isNaN(discordId) || discordId < 1000) {
      return Response.json({ status: "erro", message: "ID do Discord inválido" }, { status: 400 });
    }

    const db = await lerDB();

    if (db[telefone] && db[telefone].status === "aprovado") {
      return Response.json({ status: "ja_verificado", message: "Este telefone já foi verificado." });
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

    await salvarDB(db);
    await enviarWebhook(nome, idade, telefone, discordId);

    return Response.json({
      status: "pendente",
      message: "Dados enviados para verificação. Aguarde aprovação.",
    });
  } catch (err) {
    console.error("Erro:", err);
    return Response.json({ status: "erro", message: "Erro interno do servidor" }, { status: 500 });
  }
};
