import { getStore } from "@netlify/blobs";

export default async (req) => {
  if (req.method !== "POST") {
    return new Response("Método não permitido", { status: 405 });
  }

  try {
    const data = await req.json();
    const telefone = String(data.telefone || "").replace(/[\s\-\(\)]/g, "");

    if (!telefone || !/^\d+$/.test(telefone)) {
      return Response.json({ status: "erro", message: "Telefone inválido" }, { status: 400 });
    }

    const store = getStore("verificacoes");
    const record = await store.get(telefone, { type: "json" });

    if (!record) {
      return Response.json({
        status: "nao_encontrado",
        message: "Nenhum registro encontrado para este telefone.",
      });
    }

    const mensagens = {
      aprovado: "✅ Verificado!",
      reprovado: "❌ Reprovado.",
      banido: "🚫 Banido (menor de 13 anos).",
    };

    return Response.json({
      status: record.status,
      nome: record.nome,
      created_at: record.created_at,
      message: mensagens[record.status] || "⏳ Pendente de aprovação.",
    });
  } catch (err) {
    return Response.json({ status: "erro", message: "Erro interno do servidor" }, { status: 500 });
  }
};
