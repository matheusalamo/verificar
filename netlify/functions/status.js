const fs = require("fs");

const DB_PATH = "/tmp/verificacoes.json";

function lerDB() {
  try {
    return JSON.parse(fs.readFileSync(DB_PATH, "utf-8"));
  } catch {
    return {};
  }
}

exports.handler = async (event) => {
  try {
    if (event.httpMethod !== "POST") {
      return { statusCode: 405, body: "Método não permitido" };
    }

    const data = JSON.parse(event.body);
    const telefone = String(data.telefone || "").replace(/[\s\-\(\)]/g, "");

    if (!telefone || !/^\d+$/.test(telefone)) {
      return { statusCode: 400, body: JSON.stringify({ status: "erro", message: "Telefone inválido" }) };
    }

    const db = lerDB();
    const record = db[telefone];

    if (!record) {
      return {
        statusCode: 200,
        body: JSON.stringify({ status: "nao_encontrado", message: "Nenhum registro encontrado para este telefone." }),
      };
    }

    const mensagens = {
      aprovado: "✅ Verificado!",
      reprovado: "❌ Reprovado.",
      banido: "🚫 Banido (menor de 13 anos).",
    };

    return {
      statusCode: 200,
      body: JSON.stringify({
        status: record.status,
        nome: record.nome,
        created_at: record.created_at,
        message: mensagens[record.status] || "⏳ Pendente de aprovação.",
      }),
    };
  } catch (err) {
    console.error("Erro:", err);
    return { statusCode: 500, body: JSON.stringify({ status: "erro", message: "Erro interno do servidor" }) };
  }
};
