# Trabalho MQTT: Last Will e Retain Flag

## Correcao do erro anterior

Erro visto no fluxo antigo:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

Causa real: `docker compose up -d` dependia do Docker Desktop ligado. Sem daemon, o broker local nao sobe.

Correcao aplicada neste repositorio:

- projeto refeito em `Python`
- demo principal nao depende mais de Docker
- o script sobe um broker MQTT local embutido em `127.0.0.1:18883`
- se quiser, ainda da para apontar para broker externo com `BROKER_URL`

## Objetivo

Demonstrar, na pratica:

- `Last Will and Testament (LWT)`
- `Retain Flag`

Entregar tambem:

- quando usar cada recurso
- impactos em sistema IoT real
- codigo funcional

## Conceitos

### 1. Last Will and Testament (LWT)

`LWT` e mensagem cadastrada no momento da conexao. Se cliente cair sem enviar `DISCONNECT`, o broker publica automaticamente a mensagem de ultima vontade.

Exemplo:

- sensor conecta
- registra `will` com status `offline`
- processo trava ou rede cai
- broker publica `offline` para assinantes

### Quando usar LWT

Use `LWT` quando sistema precisa detectar falha inesperada:

- sensor pode perder energia
- gateway pode cair da rede
- atuador critico nao pode desaparecer silenciosamente
- dashboard precisa refletir disponibilidade real

### Impactos do LWT em IoT real

Beneficios:

- detecta indisponibilidade sem polling constante
- melhora observabilidade do parque IoT
- acelera alarmes e automacoes de contingencia
- reduz tempo de reacao operacional

Cuidados:

- nao substitui heartbeat
- deteccao depende de `keepalive` e timeout do broker
- configuracao ruim pode gerar falso positivo

## 2. Retain Flag

Quando publica com `retain=true`, broker guarda ultima mensagem do topico e entrega imediatamente para novo assinante.

Exemplo:

- sensor publica ultima temperatura com `retain=true`
- dashboard conecta depois
- dashboard recebe ultimo valor sem esperar nova leitura

### Quando usar Retain Flag

Use `retain` quando cliente novo precisa do ultimo estado logo ao entrar:

- ultima temperatura
- estado atual de rele/lampada
- configuracao vigente
- ultimo status de dispositivo

### Impactos do Retain Flag em IoT real

Beneficios:

- novo cliente sincroniza rapido
- interface nao fica vazia
- reinicio de app/gateway recupera ultimo estado
- sistema distribui estado conhecido com menos atraso

Cuidados:

- dado antigo pode parecer atual
- precisa timestamp no payload
- precisa limpar mensagem retida quando estado nao vale mais

## Diferenca pratica

`LWT`:

- foco em falha inesperada
- broker publica em nome do cliente que caiu
- ajuda monitoramento e disponibilidade

`Retain`:

- foco em ultimo estado conhecido
- broker guarda e reapresenta ultima mensagem
- ajuda sincronizacao de novos clientes

## Estrutura

```text
.
|-- embedded_broker.py
|-- lwt_demo.py
|-- main.py
|-- mqtt_client.py
|-- pyproject.toml
|-- requirements.txt
`-- retain_demo.py
```

## Requisitos

Opcao recomendada:

- `uv` instalado
- com `uv`, o proprio comando pode baixar/runtime Python gerenciado

Opcao alternativa:

- Python `3.11`, `3.12` ou `3.13`
- `pip`

## Como executar

### Jeito mais simples com `uv`

1. Sincronize dependencias:

```powershell
uv sync --python 3.12
```

2. Rode demo completa:

```powershell
uv run python main.py
```

### Jeito com Python + pip

1. Instale dependencias:

```powershell
python -m pip install -r requirements.txt
```

2. Rode:

```powershell
python main.py
```

## Variaveis opcionais

- `BROKER_URL`: usa broker externo em vez do broker local embutido
- `BROKER_HOST`: altera host do broker local embutido
- `BROKER_PORT`: altera porta do broker local embutido
- `TOPIC_BASE`: altera raiz dos topicos da demo

Exemplo com broker externo:

```powershell
$env:BROKER_URL="mqtt://broker.emqx.io:1883"
$env:TOPIC_BASE="trabalho/aula/python"
uv run python main.py
```

## O que a demo faz

### Demo 1: LWT

- sobe cliente monitor
- sobe dispositivo com `will`
- publica `online`
- fecha socket do dispositivo sem `DISCONNECT`
- broker publica `offline`

### Demo 2: Retain Flag

- publica leitura com `retain=true`
- conecta assinante depois
- assinante recebe ultima leitura imediatamente
- demo limpa mensagem retida no final

## Saida esperada

```text
=== DEMO LWT ===
[monitor] inscrito em trabalho/python/lwt-retain/lwt/status
[device] status online publicado
[device] simulando falha brusca
[monitor] LWT recebido: {"deviceId": "sensor-temp-01", "status": "offline", ...}

=== DEMO RETAIN FLAG ===
[publisher] mensagem retida publicada
[late-subscriber] recebeu ao conectar: {"deviceId": "sensor-temp-01", "temperature": 23.7, ...}
[late-subscriber] flag retain no pacote: True
```

## Conclusao

Em IoT real:

- `LWT` responde pergunta "dispositivo caiu?"
- `Retain` responde pergunta "qual ultimo estado conhecido?"

Juntos, melhoram confiabilidade, observabilidade e sincronizacao.
