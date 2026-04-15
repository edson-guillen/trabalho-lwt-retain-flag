const {
  closeClient,
  connectClient,
  publish,
  randomSuffix,
  sleep,
  subscribe,
  waitForMessage,
} = require("./utils");

async function runLwtDemo(options = {}) {
  const brokerUrl = options.brokerUrl || "mqtt://localhost:1883";
  const topic = options.topic || "trabalho/mqtt/lwt/status";
  const deviceId = options.deviceId || "sensor-temp-01";
  const offlinePayload = JSON.stringify({
    deviceId,
    status: "offline",
    source: "LWT",
    reason: "unexpected_disconnect",
    at: new Date().toISOString(),
  });
  const onlinePayload = JSON.stringify({
    deviceId,
    status: "online",
    source: "publisher",
    at: new Date().toISOString(),
  });

  console.log("\n=== DEMO LWT ===");
  console.log("Objetivo: broker avisar queda inesperada do dispositivo.");

  let monitor;
  let device;

  try {
    monitor = await connectClient(`monitor-${randomSuffix()}`, brokerUrl);
    await subscribe(monitor, topic, { qos: 1 });
    console.log(`[monitor] inscrito em ${topic}`);

    const offlinePromise = waitForMessage(
      monitor,
      (message) =>
        message.topic === topic && message.payload.includes('"status":"offline"'),
      10_000
    );

    device = await connectClient(deviceId, brokerUrl, {
      clientId: deviceId,
      keepalive: 2,
      will: {
        topic,
        payload: offlinePayload,
        qos: 1,
        retain: false,
      },
    });

    await publish(device, topic, onlinePayload, { qos: 1, retain: false });
    console.log(`[device] status online publicado: ${onlinePayload}`);

    await sleep(1_500);
    console.log("[device] simulando falha brusca");

    if (!device.stream || typeof device.stream.destroy !== "function") {
      throw new Error("Cliente MQTT sem stream destrutivel para demo de falha");
    }

    device.stream.destroy(new Error("Simulated device crash"));

    const offlineMessage = await offlinePromise;
    console.log(`[monitor] LWT recebido: ${offlineMessage.payload}`);
    console.log("Resultado: outros clientes descobrem queda sem polling.");
  } finally {
    await closeClient(device, true);
    await closeClient(monitor, true);
  }
}

if (require.main === module) {
  runLwtDemo().catch((error) => {
    console.error("Falha na demo LWT:", error.message);
    process.exitCode = 1;
  });
}

module.exports = {
  runLwtDemo,
};
