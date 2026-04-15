# Trabalho MQTT: Last Will e Retain Flag

## Objetivo

Demonstrar, na pratica, o funcionamento de dois recursos importantes do MQTT:

- `Last Will and Testament (LWT)`
- `Retain Flag`

O projeto inclui:

- explicacao conceitual
- quando usar cada recurso
- impactos em um sistema IoT real
- codigo funcional para demonstrar ambos

## Conceitos

### 1. Last Will and Testament (LWT)

O `LWT` e uma mensagem cadastrada pelo cliente no momento da conexao com o broker. Se esse cliente cair de forma inesperada, o broker publica automaticamente a mensagem definida no `will`.

Exemplo pratico:

- um sensor conecta no broker
- esse sensor registra que, se cair sem avisar, o broker deve publicar `"offline"`
- se a energia acabar, a rede cair ou o processo travar, o broker dispara esse aviso para os assinantes

### Quando usar LWT

Use `LWT` quando o sistema precisa detectar falhas inesperadas de dispositivos ou servicos, por exemplo:

- sensores que podem perder energia
- gateways que podem sair da rede
- atuadores criticos que nao podem sumir silenciosamente
- monitoramento de disponibilidade de dispositivos

### Impactos do LWT em IoT real

Impactos positivos:

- permite detectar falhas sem depender de polling constante
- melhora observabilidade do ecossistema IoT
- acelera reacao a indisponibilidade de dispositivos
- ajuda dashboards, supervisao e automacoes a refletirem o estado real do sistema

Cuidados:

- o `LWT` nao substitui heartbeat ou telemetria periodica
- a deteccao depende da sessao MQTT e do timeout/keepalive
- mensagens mal planejadas podem gerar alarmes demais

## 2. Retain Flag

Quando uma mensagem e publicada com `retain=true`, o broker guarda a ultima mensagem daquele topico. Assim, qualquer novo assinante que entrar depois recebe esse valor imediatamente, sem esperar a proxima publicacao.

Exemplo pratico:

- um sensor publica a ultima temperatura com `retain=true`
- um dashboard conecta depois
- ao se inscrever no topico, ele recebe instantaneamente a ultima leitura retida

### Quando usar Retain Flag

Use `retain` quando novos clientes precisam conhecer o ultimo estado conhecido assim que entram no sistema:

- ultimo valor de sensor
- estado atual de um rele ou lampada
- configuracao vigente
- status atual de um dispositivo

### Impactos do Retain Flag em IoT real

Impactos positivos:

- reduz tempo para sincronizar novos clientes
- evita interfaces vazias aguardando nova mensagem
- facilita reinicio de dashboards, gateways e apps
- melhora consistencia do ultimo estado conhecido

Cuidados:

- mensagem antiga pode parecer estado atual se nao houver timestamp
- uso incorreto pode propagar informacao obsoleta
- e preciso limpar a mensagem retida quando ela nao fizer mais sentido

## Diferenca pratica entre LWT e Retain

`LWT`:

- serve para avisar falha inesperada
- o broker publica em nome do cliente desconectado
- foco em disponibilidade e monitoramento

`Retain`:

- serve para guardar o ultimo valor do topico
- o broker entrega esse ultimo valor para novos assinantes
- foco em sincronizacao de estado

## Estrutura do projeto

```text
.
|-- compose.yml
|-- mosquitto/
|   `-- mosquitto.conf
|-- src/
|   |-- demo.js
|   |-- lwt-demo.js
|   |-- retain-demo.js
|   `-- utils.js
`-- README.md
```

## Requisitos

- Node.js instalado
- Docker Desktop instalado e em execucao

## Como executar

1. Instale dependencias:

```bash
npm install
```

2. Suba o broker MQTT local:

```bash
npm run broker:up
```

3. Execute a demonstracao completa:

```bash
npm run demo
```

4. Para parar o broker:

```bash
npm run broker:down
```

## Variaveis opcionais

O projeto aceita configuracao por variavel de ambiente:

- `BROKER_URL`: altera o broker alvo
- `TOPIC_BASE`: altera a raiz dos topicos usados na demonstracao

Exemplo:

```bash
BROKER_URL=mqtt://localhost:1883 TOPIC_BASE=trabalho/aula npm run demo
```

PowerShell:

```powershell
$env:BROKER_URL="mqtt://localhost:1883"
$env:TOPIC_BASE="trabalho/aula"
npm run demo
```

## O que a demo faz

### Demo 1: LWT

- cria um cliente monitor
- cria um dispositivo com mensagem `will`
- publica status `online`
- derruba a conexao do dispositivo de forma brusca
- o broker publica automaticamente a mensagem `offline`

### Demo 2: Retain Flag

- publica uma leitura com `retain=true`
- conecta um assinante depois da publicacao
- esse assinante recebe imediatamente a ultima mensagem retida
- ao final, a mensagem retida e limpa para nao interferir na proxima execucao

## Exemplo de saida esperada

```text
=== DEMO LWT ===
[monitor] inscrito em trabalho/mqtt/lwt/status
[device] status online publicado
[device] simulando falha brusca
[monitor] LWT recebido: {"deviceId":"sensor-temp-01","status":"offline",...}

=== DEMO RETAIN FLAG ===
[publisher] mensagem retida publicada
[late-subscriber] recebeu ao conectar: {"deviceId":"sensor-temp-01","temperature":23.7,...}
[late-subscriber] flag retain no pacote: true
```

## Conclusao

Em um sistema IoT real, `LWT` e `Retain Flag` atendem problemas diferentes e complementares:

- `LWT` ajuda a detectar falhas inesperadas
- `Retain` ajuda novos clientes a iniciarem com o ultimo estado conhecido

Usados corretamente, os dois melhoram confiabilidade, observabilidade e sincronizacao do sistema.
