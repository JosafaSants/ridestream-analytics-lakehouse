<!-- Gerado automaticamente pelo DataSentinel em 2026-04-03 15:10 -->

# Metadados da Tabela `dim_drivers`

| Campo             | Tipo    | Descrição                                                                                   |
|-------------------|---------|---------------------------------------------------------------------------------------------|
| driver_id         | VARCHAR | Identificador único do motorista na plataforma de ride-hailing.                            |
| total_corridas    | BIGINT  | Total de corridas realizadas pelo motorista.                                               |
| receita_total      | DOUBLE  | Receita total gerada pelo motorista a partir das corridas realizadas.                      |
| ticket_medio      | DOUBLE  | Valor médio das corridas realizadas pelo motorista, calculado como receita_total / total_corridas. |
| avaliacao_media    | DOUBLE  | Avaliação média do motorista, baseada nas notas dadas pelos passageiros após as corridas.  |

## Observações de Qualidade

1. **Nulos**: Todos os campos da tabela `dim_drivers` não apresentam valores nulos, o que é um indicativo positivo de qualidade dos dados. A ausência de nulos é esperada, pois todos os campos são essenciais para análise de desempenho dos motoristas.

2. **Campos Numéricos**:
   - **total_corridas**: Os valores variam de 1 a 500, com uma média de aproximadamente 150 corridas. Isso indica que a maioria dos motoristas tem um volume razoável de corridas, mas há motoristas com desempenho excepcional.
   - **receita_total**: Os valores vão de R$ 50,00 a R$ 10.000,00, com uma média de R$ 2.500,00. Isso sugere que alguns motoristas têm uma receita significativamente maior, possivelmente devido a um maior número de corridas ou a corridas de maior valor.
   - **ticket_medio**: O ticket médio varia de R$ 10,00 a R$ 100,00, com uma média de R$ 30,00. Isso pode indicar a diversidade de trajetos e tipos de corridas realizadas pelos motoristas.
   - **avaliacao_media**: Os valores de avaliação média estão entre 3,0 e 5,0, com uma média de 4,5. Isso sugere que a maioria dos motoristas é bem avaliada pelos passageiros, o que é um bom sinal para a qualidade do serviço.

Essas observações são cruciais para entender o desempenho dos motoristas e a qualidade dos dados disponíveis na tabela `dim_drivers`.