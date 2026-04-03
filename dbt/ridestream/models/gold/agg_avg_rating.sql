-- Modelo: agg_avg_rating
-- Camada: Gold
-- Descrição: Avaliação média por motorista
-- Responde: quais motoristas têm melhor desempenho na visão do passageiro?
-- Fonte: fct_rides_completed (só corridas concluídas têm avaliação)

{{
    config(
        materialized='table',
        tags=['gold', 'agregacao', 'qualidade']
    )
}}

-- Usa ref() para depender do modelo fct_rides_completed
-- O dbt garante que este modelo só roda depois que aquele estiver pronto
with base as (
    select
        driver_id,
        avaliacao
    from {{ ref('fct_rides_completed') }}
    where avaliacao is not null
),

ranking_motoristas as (
    select
        driver_id,
        count(*) as total_avaliacoes,
        round(avg(avaliacao), 2) as avaliacao_media,
        min(avaliacao) as pior_avaliacao,
        max(avaliacao) as melhor_avaliacao
    from base
    group by driver_id
    order by avaliacao_media desc
)

select * from ranking_motoristas
