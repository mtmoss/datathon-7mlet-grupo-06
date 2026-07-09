# Infra AWS — Componentes e Fronteiras

Detalhe de responsabilidade de cada componente e as fronteiras entre eles.
Visão completa e diagrama em [`docs/architecture-aws.md`](../../docs/architecture-aws.md).

## Fluxo de uma decisão

1. O cliente/avaliador chama a API via **API Gateway** (autentica e limita taxa).
2. **App Runner** (FastAPI) recebe o contexto, valida o contrato e decide.
3. A decisão usa o **artefato de política** (`policy-v1.json`) carregado do **S3**.
4. A decisão é gravada no **decision log** (S3) e emitida para **CloudWatch**.
5. Impressões e recompensas (atrasadas) entram por **Kinesis Data Streams**.

## Fluxo de retreino e promoção (Etapa 7)

1. Uma **ECS Scheduled Task** (agendada ou disparada por drift) lê eventos+recompensas.
2. Treina uma política candidata e registra métricas no **MLflow** (backend
   **RDS PostgreSQL**, artefatos no **S3**).
3. Se passar nos critérios, um humano aprova a promoção no **model registry**.
4. A nova versão do artefato substitui a anterior; rollback = apontar para a versão antiga.

## Fluxo do assistente (RAG, Etapa 8)

1. Pergunta do usuário → **assistente** em App Runner.
2. Recupera documentos de política em **Amazon OpenSearch** (busca vetorial sobre o S3).
3. Gera a resposta com **Amazon Bedrock** (Claude + embeddings).

## Fronteiras de segurança

| Fronteira | Controle |
|---|---|
| Internet → API | API Gateway + Cognito (autenticação) |
| Serviço → segredos | IAM Role → Secrets Manager (sem senha) |
| Serviço → dados | IAM (least privilege) |
| Serviço → banco | IAM auth no RDS |
| Rede | VPC + Security Groups quando justificado |

## Responsabilidade por componente

| Componente | Responsabilidade única |
|---|---|
| API Gateway | entrada, auth, rate limit, versão da API |
| App Runner (API) | decidir e registrar |
| ECS Task (Job) | retreinar e avaliar |
| S3 | persistir dados, artefatos e logs |
| RDS PostgreSQL | metadados do MLflow |
| Kinesis | ingestão de eventos/recompensas |
| OpenSearch | recuperação para o RAG |
| Bedrock | inferência do LLM (Claude) |
| Secrets Manager | segredos |
| CloudWatch / X-Ray | observar |
