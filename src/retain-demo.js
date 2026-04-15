const {
  closeClient,
  connectClient,
  publish,
  randomSuffix,
  sleep,
  subscribe,
  waitForMessage,
} = require("./utils");

async function runRetainDemo(options = {}) {
  const brokerUrl = options.brokerUrl || "mqtt://localhost:1883";
  const topic = options.topic || "trabalho/mqtt/retain/last-reading";
  const retainedPayload = JSON.stringify({
    deviceId: "sensor-temp-01",
    temperature: 23.7,
    unit: "C",
    source: "retained_message",
    at: new Date().toISOString(),
  });

  console.log("\n=== DEMO RETAIN FLAG ===");
  console.log("Objetivo: novo inscrito receber ultimo estado imediatamente.");

  let publisher;
  let lateSubscriber;

  try {
    publisher = await connectClient(`publisher-${randomSuffix()}`, brokerUrl);

    await publish(publisher, topic, retainedPayload, { qos: 1, retain: true });
    console.log(`[publisher] mensagem retida publicada: ${retainedPayload}`);

    await sleep(1_000);

    lateSubscriber = await connectClient(`late-subscriber-${randomSuffix()}`, brokerUrl);

    const retainedPromise = waitForMessage(
      lateSubscriber,
      (message) => message.topic === topic,
      5_000
    );

    await subscribe(lateSubscriber, topic, { qos: 1 });
    console.log(`[late-subscriber] inscrito em ${topic}`);

    const retainedMessage = await retainedPromise;
    console.log(`[late-subscriber] recebeu ao conectar: ${retainedMessage.payload}`);
    console.log(`[late-subscriber] flag retain no pacote: ${retainedMessage.packet.retain}`);
    console.log("Resultado: cliente novo inicia com ultimo valor conhecido.");

    await publish(publisher, topic, "", { qos: 1, retain: true });
    console.log("[publisher] mensagem retida limpa para nao poluir prox execucao");
  } finally {
    await closeClient(lateSubscriber);
    await closeClient(publisher);
  }
}

if (require.main === module) {
  runRetainDemo().catch((error) => {
    console.error("Falha na demo Retain:", error.message);
    process.exitCode = 1;
  });
}

module.exports = {
  runRetainDemo,
};
