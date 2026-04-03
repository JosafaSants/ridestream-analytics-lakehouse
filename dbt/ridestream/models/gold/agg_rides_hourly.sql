-- Modelo: agg_rides_hourly
-- Camada: Gold
-- Descrição: Volume de corridas concluídas por hora do dia
-- Responde: em que horário o app tem mais demanda?
-- Fonte: Silver layer diretamente para capturar todos os status

{{
    config(
        materialized='table',
        tags=['gold', 'agregacao', 'demanda']
    )
}}

with corridas_silver as (
    select *
    from read_parquet(
        'C:/Users/JosafaBarbosadosSant/ridestream-analytics-lakehouse/data/silver/ride_events/**/*.parquet',
        hive_partitioning = true
    )
),

-- Extrai a hora do timestamp e conta corridas por hora
corridas_por_hora as (
    select
        hour(timestamp) as hora_do_dia,
        count(*) as total_corridas,
        count(case when status = 'completed' then 1 end) as corridas_concluidas,
        count(case when status = 'cancelled' then 1 end) as corridas_canceladas
    from corridas_silver
    where timestamp is not null
    group by hour(timestamp)
    order by hora_do_dia
)

select * from corridas_por_hora
