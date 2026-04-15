const { runLwtDemo } = require("./lwt-demo");
const { runRetainDemo } = require("./retain-demo");

async function main() {
  const brokerUrl = process.env.BROKER_URL || "mqtt://localhost:1883";
  const topicBase =
    process.env.TOPIC_BASE || `trabalho/mqtt/lwt-retain/${Date.now()}`;

  console.log("Broker alvo:", brokerUrl);
  console.log("Suba broker com: npm run broker:up");
  console.log("Base topicos:", topicBase);

  await runLwtDemo({
    brokerUrl,
    topic: `${topicBase}/lwt/status`,
  });
  await runRetainDemo({
    brokerUrl,
    topic: `${topicBase}/retain/last-reading`,
  });

  console.log("\nDemo completa.");
}

main().catch((error) => {
  console.error("Falha geral:", error.message);
  process.exitCode = 1;
});
