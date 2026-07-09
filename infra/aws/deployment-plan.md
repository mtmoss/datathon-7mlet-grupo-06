# Plano de Deploy — AWS

Passos para provisionar a arquitetura-alvo. **Ilustrativo**: o datathon não exige
recursos pagos ativos; serve para mostrar que o caminho é viável em AWS.

## Pré-requisitos

- AWS CLI (`aws`) e uma conta com permissões.
- Imagem do serviço publicada (Dockerfile do projeto) no **Amazon ECR**.

## Provisionamento (esboço `aws` CLI)

```bash
# 1. registry de container + push da imagem
aws ecr create-repository --repository-name offerexp-api
# (docker build + docker push para o ECR)

# 2. armazenamento (datasets, artefatos, logs)
aws s3 mb s3://offerexp-data

# 3. banco do MLflow
aws rds create-db-instance --db-instance-identifier pg-offerexp \
  --engine postgres --db-instance-class db.t3.micro --allocated-storage 20

# 4. segredos
aws secretsmanager create-secret --name offerexp/rds --secret-string '{"conn":"..."}'

# 5. servico (App Runner) a partir da imagem no ECR, com IAM Role
aws apprunner create-service --service-name offerexp-api \
  --source-configuration '{"ImageRepository":{"ImageIdentifier":"<ecr-uri>:v1","ImageRepositoryType":"ECR","ImageConfiguration":{"Port":"8000"}}}'

# 6. observabilidade: logs e metricas ja vao para o CloudWatch automaticamente
```

(Kinesis, OpenSearch e Bedrock seguem o mesmo padrão; omitidos por brevidade.
Bedrock exige apenas habilitar o acesso ao modelo Claude na conta.)

## CI/CD (já temos a base)

O `.github/workflows/ci.yaml` roda ruff + pytest. Para o deploy, o passo de CD
seria: ao dar merge na `main` → build/push da imagem para o **ECR** → App Runner
faz o rollout da nova versão. Promoção de política controlada pela Etapa 7.

## Gestão de segredos

- Todos os segredos no **Secrets Manager**; a aplicação lê via **IAM Role**.
- Nada de chave em código, imagem ou variável de ambiente em texto.
- `.env.example` ↔ secrets do Secrets Manager (mapeamento 1:1).

## Rollback

- App Runner mantém versões da imagem: voltar é fazer deploy da anterior.
- Política: apontar o artefato para a versão anterior (`policy-v(N-1).json`).

## Custo qualitativo (resumo)

| Bloco | Custo ocioso | Sob carga |
|---|---|---|
| Compute (App Runner) | baixo | baixo-médio |
| Dados (S3 + RDS) | baixo fixo | baixo |
| Eventos (Kinesis) | baixo | médio |
| IA/RAG (OpenSearch + Bedrock) | médio (OpenSearch cobra ocioso) | médio (Bedrock por token) |
| Observabilidade | baixo | por GB de log |

Detalhe de ROI e TCO no vídeo/pitch (Etapa 8).
