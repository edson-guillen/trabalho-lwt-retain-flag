const mqtt = require("mqtt");

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function randomSuffix() {
  return Math.random().toString(16).slice(2, 8);
}

function connectClient(name, brokerUrl, options = {}) {
  return new Promise((resolve, reject) => {
    const client = mqtt.connect(brokerUrl, {
      reconnectPeriod: 0,
      connectTimeout: 5_000,
      ...options,
    });

    const timer = setTimeout(() => {
      client.end(true);
      reject(new Error(`Timeout conectando cliente ${name}`));
    }, 8_000);

    const onConnect = () => {
      clearTimeout(timer);
      cleanup();
      console.log(`[${name}] conectado`);
      resolve(client);
    };

    const onError = (error) => {
      clearTimeout(timer);
      cleanup();
      client.end(true);
      reject(error);
    };

    const cleanup = () => {
      client.off("connect", onConnect);
      client.off("error", onError);
    };

    client.once("connect", onConnect);
    client.once("error", onError);
  });
}

function subscribe(client, topic, options = { qos: 1 }) {
  return new Promise((resolve, reject) => {
    client.subscribe(topic, options, (error, granted) => {
      if (error) {
        reject(error);
        return;
      }

      resolve(granted);
    });
  });
}

function publish(client, topic, payload, options = { qos: 1, retain: false }) {
  return new Promise((resolve, reject) => {
    client.publish(topic, payload, options, (error) => {
      if (error) {
        reject(error);
        return;
      }

      resolve();
    });
  });
}

function waitForMessage(client, matcher, timeoutMs = 5_000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error("Timeout aguardando mensagem MQTT"));
    }, timeoutMs);

    const onMessage = (topic, payload, packet) => {
      const message = {
        topic,
        payload: payload.toString(),
        packet,
      };

      if (!matcher(message)) {
        return;
      }

      clearTimeout(timer);
      cleanup();
      resolve(message);
    };

    const cleanup = () => {
      client.off("message", onMessage);
    };

    client.on("message", onMessage);
  });
}

async function closeClient(client, force = false) {
  if (!client) {
    return;
  }

  await new Promise((resolve) => {
    client.end(force, resolve);
  });
}

module.exports = {
  closeClient,
  connectClient,
  publish,
  randomSuffix,
  sleep,
  subscribe,
  waitForMessage,
};
